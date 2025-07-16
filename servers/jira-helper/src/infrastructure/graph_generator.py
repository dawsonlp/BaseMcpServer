"""
Graph generation implementation for the Jira Helper.

This module implements the GraphGenerator and WorkflowAnalyzer ports using
GraphViz and NetworkX libraries for workflow visualization.
"""

import base64
import logging
import os
import tempfile
from typing import Any

from domain.exceptions import JiraGraphGenerationError, JiraGraphLibraryNotAvailable
from domain.models import WorkflowEdge, WorkflowGraph, WorkflowNode, WorkflowTransition
from domain.ports import GraphGenerator, WorkflowAnalyzer

logger = logging.getLogger(__name__)

try:
    import graphviz
    import networkx as nx
    GRAPH_SUPPORT = True
except ImportError:
    GRAPH_SUPPORT = False


class GraphvizGenerator(GraphGenerator):
    """Graph generator implementation using GraphViz."""

    def __init__(self):
        if not GRAPH_SUPPORT:
            logger.warning("GraphViz and NetworkX libraries not available")

    def is_available(self) -> bool:
        """Check if graph generation is available."""
        return GRAPH_SUPPORT

    async def generate_dot_graph(self, workflow: WorkflowGraph) -> str:
        """Generate a DOT format graph."""
        if not self.is_available():
            raise JiraGraphLibraryNotAvailable(["graphviz", "networkx"])

        try:
            dot_lines = [
                f'digraph "{workflow.project_key}_{workflow.issue_type}_workflow" {{',
                '    rankdir=LR;',
                '    node [shape=box, style=rounded];',
                ''
            ]

            # Add nodes
            for node in workflow.nodes:
                color = node.color
                dot_lines.append(f'    "{node.id}" [label="{node.name}", fillcolor="{color}", style="filled,rounded"];')

            dot_lines.append('')

            # Add edges
            for edge in workflow.edges:
                label = edge.label
                dot_lines.append(f'    "{edge.from_node}" -> "{edge.to_node}" [label="{label}"];')

            dot_lines.append('}')

            return '\n'.join(dot_lines)

        except Exception as e:
            logger.error(f"Failed to generate DOT graph: {str(e)}")
            raise JiraGraphGenerationError(f"DOT generation failed: {str(e)}")

    async def generate_visual_graph(self, workflow: WorkflowGraph, format: str = "svg") -> str:
        """Generate a visual graph in SVG or PNG format (base64 encoded)."""
        if not self.is_available():
            raise JiraGraphLibraryNotAvailable(["graphviz", "networkx"])

        try:
            # Create Graphviz graph
            dot = graphviz.Digraph(comment=f'{workflow.project_key} {workflow.issue_type} Workflow')
            dot.attr(rankdir='LR')
            dot.attr('node', shape='box', style='rounded,filled')

            # Add nodes
            for node in workflow.nodes:
                dot.node(node.id, node.name, fillcolor=node.color)

            # Add edges
            for edge in workflow.edges:
                dot.edge(edge.from_node, edge.to_node, label=edge.label)

            # Determine output format
            output_format = "png" if format.lower() == "png" else "svg"

            # Use a temporary file to render
            with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=False) as tmp_file:
                try:
                    # Render the graph
                    dot.render(tmp_file.name.replace(f'.{output_format}', ''), format=output_format, cleanup=True)

                    # Read the generated file
                    output_file = tmp_file.name
                    with open(output_file, 'rb') as f:
                        graph_bytes = f.read()

                    # Clean up
                    os.unlink(output_file)

                    # Return base64 encoded data
                    return base64.b64encode(graph_bytes).decode('utf-8')

                except Exception as render_error:
                    # Clean up temp file if it exists
                    if os.path.exists(tmp_file.name):
                        os.unlink(tmp_file.name)
                    raise render_error

        except Exception as e:
            logger.error(f"Failed to generate visual graph: {str(e)}")
            # Fallback to text representation
            return self._format_workflow_as_text(workflow)

    def _format_workflow_as_text(self, workflow: WorkflowGraph) -> str:
        """Format workflow as text when visual generation fails."""
        lines = [f"Workflow for {workflow.project_key} - {workflow.issue_type}", ""]

        lines.append("Nodes:")
        for node in workflow.nodes:
            lines.append(f"  - {node.name} ({node.category})")

        lines.append("\nTransitions:")
        for edge in workflow.edges:
            lines.append(f"  - {edge.from_node} --[{edge.label}]--> {edge.to_node}")

        return "\n".join(lines)


class WorkflowAnalyzerImpl(WorkflowAnalyzer):
    """Workflow analyzer implementation using NetworkX."""

    def __init__(self):
        if not GRAPH_SUPPORT:
            logger.warning("NetworkX library not available for workflow analysis")

    async def analyze_workflow(self, workflow_data: dict[str, Any], project_key: str, issue_type: str) -> WorkflowGraph:
        """Analyze workflow data and create a workflow graph."""
        try:
            workflow = WorkflowGraph(project_key=project_key, issue_type=issue_type)

            # Check if we have project workflow data
            if "workflow_data" in workflow_data:
                return await self._create_workflow_from_project_data(workflow_data, workflow)
            elif "available_transitions" in workflow_data:
                return await self._create_workflow_from_transitions(workflow_data, workflow)
            else:
                # Create a minimal workflow
                return await self._create_minimal_workflow(workflow_data, workflow)

        except Exception as e:
            logger.error(f"Failed to analyze workflow: {str(e)}")
            raise JiraGraphGenerationError(f"Workflow analysis failed: {str(e)}")

    async def create_fallback_workflow(self, transitions: list[WorkflowTransition], current_status: str) -> WorkflowGraph:
        """Create a fallback workflow from available transitions."""
        try:
            workflow = WorkflowGraph(project_key="UNKNOWN", issue_type="UNKNOWN")

            # Add current status as a node
            current_node = WorkflowNode(
                id=current_status,
                name=current_status,
                category="Current",
                color=self._get_status_color("Current")
            )
            workflow.add_node(current_node)

            # Add nodes and edges from transitions
            for transition in transitions:
                # Add target status node if not exists
                if not workflow.get_node_by_id(transition.to_status):
                    target_node = WorkflowNode(
                        id=transition.to_status,
                        name=transition.to_status,
                        category="Available",
                        color=self._get_status_color("Available")
                    )
                    workflow.add_node(target_node)

                # Add transition edge
                edge = WorkflowEdge(
                    from_node=current_status,
                    to_node=transition.to_status,
                    label=transition.name
                )
                workflow.add_edge(edge)

            workflow.metadata["source"] = "fallback_transitions"
            return workflow

        except Exception as e:
            logger.error(f"Failed to create fallback workflow: {str(e)}")
            raise JiraGraphGenerationError(f"Fallback workflow creation failed: {str(e)}")

    async def _create_workflow_from_project_data(self, workflow_data: dict[str, Any], workflow: WorkflowGraph) -> WorkflowGraph:
        """Create workflow from project workflow data."""
        try:
            project_workflow = workflow_data["workflow_data"]
            issue_type = workflow_data["issue_type"]

            # Find the workflow for our issue type
            issue_type_workflows = None
            for item in project_workflow:
                if item['name'].lower() == issue_type.lower():
                    issue_type_workflows = item['statuses']
                    break

            if not issue_type_workflows:
                # Fallback to first available workflow
                if project_workflow:
                    issue_type_workflows = project_workflow[0]['statuses']

            if issue_type_workflows:
                # Add status nodes
                for status_info in issue_type_workflows:
                    status_name = status_info['name']
                    category = status_info.get('statusCategory', {}).get('name', 'Unknown')

                    node = WorkflowNode(
                        id=status_name,
                        name=status_name,
                        category=category,
                        color=self._get_status_color(category)
                    )
                    workflow.add_node(node)

                # Create logical transitions based on categories
                self._add_logical_transitions(workflow)

            workflow.metadata["source"] = "project_workflow_data"
            return workflow

        except Exception as e:
            logger.error(f"Failed to create workflow from project data: {str(e)}")
            raise

    async def _create_workflow_from_transitions(self, workflow_data: dict[str, Any], workflow: WorkflowGraph) -> WorkflowGraph:
        """Create workflow from available transitions."""
        try:
            current_status = workflow_data.get("current_status", "Unknown")
            transitions = workflow_data.get("available_transitions", [])

            # Add current status node
            current_node = WorkflowNode(
                id=current_status,
                name=current_status,
                category="Current",
                color=self._get_status_color("Current")
            )
            workflow.add_node(current_node)

            # Add nodes and edges from transitions
            for transition in transitions:
                target_status = transition['to']['name'] if 'to' in transition else "Unknown"

                # Add target node if not exists
                if not workflow.get_node_by_id(target_status):
                    target_node = WorkflowNode(
                        id=target_status,
                        name=target_status,
                        category="Available",
                        color=self._get_status_color("Available")
                    )
                    workflow.add_node(target_node)

                # Add transition edge
                edge = WorkflowEdge(
                    from_node=current_status,
                    to_node=target_status,
                    label=transition['name']
                )
                workflow.add_edge(edge)

            workflow.metadata["source"] = "available_transitions"
            return workflow

        except Exception as e:
            logger.error(f"Failed to create workflow from transitions: {str(e)}")
            raise

    async def _create_minimal_workflow(self, workflow_data: dict[str, Any], workflow: WorkflowGraph) -> WorkflowGraph:
        """Create a minimal workflow when limited data is available."""
        try:
            # Create a basic workflow with common statuses
            statuses = ["To Do", "In Progress", "Done"]

            for i, status in enumerate(statuses):
                category = "To Do" if i == 0 else "In Progress" if i == 1 else "Done"
                node = WorkflowNode(
                    id=status,
                    name=status,
                    category=category,
                    color=self._get_status_color(category)
                )
                workflow.add_node(node)

            # Add basic transitions
            for i in range(len(statuses) - 1):
                edge = WorkflowEdge(
                    from_node=statuses[i],
                    to_node=statuses[i + 1],
                    label="Progress"
                )
                workflow.add_edge(edge)

            workflow.metadata["source"] = "minimal_default"
            return workflow

        except Exception as e:
            logger.error(f"Failed to create minimal workflow: {str(e)}")
            raise

    def _add_logical_transitions(self, workflow: WorkflowGraph) -> None:
        """Add logical transitions based on status categories."""
        try:
            # Group nodes by category
            todo_nodes = [n for n in workflow.nodes if n.category == "To Do"]
            progress_nodes = [n for n in workflow.nodes if n.category == "In Progress"]
            done_nodes = [n for n in workflow.nodes if n.category == "Done"]

            # Create logical transitions
            for todo in todo_nodes:
                for progress in progress_nodes:
                    edge = WorkflowEdge(
                        from_node=todo.id,
                        to_node=progress.id,
                        label="Start Progress"
                    )
                    workflow.add_edge(edge)

            for progress in progress_nodes:
                for done in done_nodes:
                    edge = WorkflowEdge(
                        from_node=progress.id,
                        to_node=done.id,
                        label="Complete"
                    )
                    workflow.add_edge(edge)

        except Exception as e:
            logger.warning(f"Failed to add logical transitions: {str(e)}")

    def _get_status_color(self, category: str) -> str:
        """Get color for status category."""
        color_map = {
            "To Do": "#FF9800",      # Orange
            "In Progress": "#2196F3", # Blue
            "Done": "#4CAF50",       # Green
            "Current": "#9C27B0",    # Purple
            "Available": "#607D8B",  # Blue Grey
            "Unknown": "#9E9E9E"     # Grey
        }
        return color_map.get(category, "#9E9E9E")


class LoggerAdapter:
    """Simple logger adapter for the infrastructure layer."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self._logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self._logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self._logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self._logger.debug(message, extra=kwargs)
