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
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for server environments
    import matplotlib.pyplot as plt
    import networkx as nx
    import io
    GRAPH_SUPPORT = True
    logger.info("Graph libraries loaded: matplotlib %s, networkx %s", 
                matplotlib.__version__, nx.__version__)
except ImportError as e:
    # Since matplotlib and networkx are now required dependencies,
    # log as error rather than warning if they're missing
    logger.error(f"Required graph libraries not available: {e}")
    GRAPH_SUPPORT = False


class MatplotlibGenerator(GraphGenerator):
    """Graph generator implementation using matplotlib and NetworkX."""

    def __init__(self):
        # Dependencies are now required and checked at module level
        pass

    def is_available(self) -> bool:
        """Check if graph generation is available."""
        return GRAPH_SUPPORT

    async def generate_dot_graph(self, workflow: WorkflowGraph) -> str:
        """Generate a graph structure description in DOT-like format."""
        if not self.is_available():
            raise JiraGraphLibraryNotAvailable(["matplotlib", "networkx"])

        try:
            # Create NetworkX graph for analysis
            graph = self._create_networkx_graph(workflow)
            
            # Generate DOT-style text representation
            dot_lines = [
                f'digraph "{workflow.project_key}_{workflow.issue_type}_workflow" {{',
                '    rankdir=LR;',
                '    node [shape=box, style=rounded];',
                ''
            ]

            # Add nodes with networkx-analyzed properties
            for node_id in graph.nodes():
                node_data = graph.nodes[node_id]
                color = node_data.get('color', '#9E9E9E')
                label = node_data.get('label', node_id)
                dot_lines.append(f'    "{node_id}" [label="{label}", fillcolor="{color}", style="filled,rounded"];')

            dot_lines.append('')

            # Add edges
            for source, target, edge_data in graph.edges(data=True):
                label = edge_data.get('label', '')
                dot_lines.append(f'    "{source}" -> "{target}" [label="{label}"];')

            dot_lines.append('}')
            
            # Add graph statistics
            dot_lines.extend([
                '',
                f'// Graph Statistics (NetworkX Analysis):',
                f'// Nodes: {graph.number_of_nodes()}',
                f'// Edges: {graph.number_of_edges()}',
                f'// Layout: {"spring" if graph.number_of_nodes() <= 10 else "hierarchical"}'
            ])

            return '\n'.join(dot_lines)

        except Exception as e:
            logger.error(f"Failed to generate DOT graph: {str(e)}")
            raise JiraGraphGenerationError(f"DOT generation failed: {str(e)}")

    async def generate_visual_graph(self, workflow: WorkflowGraph, format: str = "svg") -> str:
        """Generate a visual graph in SVG or PNG format (base64 encoded)."""
        if not self.is_available():
            raise JiraGraphLibraryNotAvailable(["matplotlib", "networkx"])

        # Create NetworkX graph
        graph = self._create_networkx_graph(workflow)
        
        if graph.number_of_nodes() == 0:
            raise JiraGraphGenerationError("Cannot generate workflow graph: No workflow nodes available. This indicates the workflow data could not be retrieved from Jira.")
        
        # Generate matplotlib visualization
        return self._render_matplotlib_graph(graph, workflow, format)

    def _create_networkx_graph(self, workflow: WorkflowGraph) -> nx.DiGraph:
        """Convert WorkflowGraph to NetworkX DiGraph."""
        graph = nx.DiGraph()
        
        # Add nodes with attributes
        for node in workflow.nodes:
            graph.add_node(
                node.id,
                label=node.name,
                color=node.color,
                category=node.category
            )
        
        # Add edges with attributes
        for edge in workflow.edges:
            graph.add_edge(
                edge.from_node,
                edge.to_node,
                label=edge.label
            )
        
        return graph

    def _render_matplotlib_graph(self, graph: nx.DiGraph, workflow: WorkflowGraph, format: str) -> str:
        """Render NetworkX graph using matplotlib."""
        # Create figure with appropriate size
        plt.figure(figsize=(14, 10))
        plt.clf()
        
        # Choose layout based on graph size and structure
        pos = self._choose_layout(graph)
        
        # Extract node colors and sizes
        node_colors = [graph.nodes[node].get('color', '#9E9E9E') for node in graph.nodes()]
        node_sizes = [2500 for _ in graph.nodes()]  # Consistent size
        
        # Draw nodes
        nx.draw_networkx_nodes(
            graph, pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9,
            linewidths=2,
            edgecolors='black'
        )
        
        # Draw edges with arrows
        nx.draw_networkx_edges(
            graph, pos,
            edge_color='#333333',
            arrows=True,
            arrowsize=25,
            arrowstyle='->',
            width=2.5,
            alpha=0.8,
            connectionstyle="arc3,rad=0.1"
        )
        
        # Draw node labels
        nx.draw_networkx_labels(
            graph, pos,
            labels={node: graph.nodes[node].get('label', node) for node in graph.nodes()},
            font_size=11,
            font_weight='bold',
            font_color='white',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7)
        )
        
        # Draw edge labels
        edge_labels = nx.get_edge_attributes(graph, 'label')
        if edge_labels:
            nx.draw_networkx_edge_labels(
                graph, pos,
                edge_labels,
                font_size=9,
                font_color='#333333',
                bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8)
            )
        
        # Add title and styling
        title = f'{workflow.project_key} - {workflow.issue_type} Workflow'
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Remove axis
        plt.axis('off')
        plt.tight_layout()
        
        # Export to base64
        return self._export_to_base64(format)

    def _choose_layout(self, graph: nx.DiGraph) -> dict:
        """Choose appropriate layout algorithm based on graph characteristics."""
        node_count = graph.number_of_nodes()
        
        if node_count <= 3:
            # Small graphs: simple circular layout
            return nx.circular_layout(graph, scale=2)
        elif node_count <= 8:
            # Medium graphs: spring layout with good spacing
            return nx.spring_layout(graph, k=3, iterations=50, seed=42)
        else:
            # Large graphs: try hierarchical if possible, otherwise spring
            try:
                return nx.nx_agraph.graphviz_layout(graph, prog='dot')
            except:
                # Fallback to spring layout with more space
                return nx.spring_layout(graph, k=4, iterations=100, seed=42)

    def _export_to_base64(self, format: str) -> str:
        """Export matplotlib figure to base64 encoded string."""
        buffer = io.BytesIO()
        
        if format.lower() == 'png':
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150,
                       facecolor='white', edgecolor='none', pad_inches=0.5)
        else:
            plt.savefig(buffer, format='svg', bbox_inches='tight', dpi=150,
                       facecolor='white', edgecolor='none', pad_inches=0.5)
        
        buffer.seek(0)
        image_data = buffer.read()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_data).decode('utf-8')

    def _format_workflow_as_text(self, workflow: WorkflowGraph) -> str:
        """Enhanced text representation when visual generation fails."""
        lines = [f"=== Workflow: {workflow.project_key} - {workflow.issue_type} ===", ""]
        
        # Add summary statistics
        lines.append(f"📊 Summary:")
        lines.append(f"   Nodes: {len(workflow.nodes)}")
        lines.append(f"   Transitions: {len(workflow.edges)}")
        lines.append("")
        
        # Add nodes with categories
        lines.append("🔸 Workflow States:")
        for node in workflow.nodes:
            lines.append(f"   • {node.name} ({node.category}) - {node.color}")
        
        lines.append("")
        
        # Add transitions
        lines.append("🔀 Available Transitions:")
        for edge in workflow.edges:
            lines.append(f"   {edge.from_node} --[{edge.label}]--> {edge.to_node}")
        
        lines.extend(["", "💡 Note: Visual graph unavailable, showing text representation"])
        
        return "\n".join(lines)


# Create alias for backward compatibility during migration
GraphvizGenerator = MatplotlibGenerator


class WorkflowAnalyzerImpl(WorkflowAnalyzer):
    """Workflow analyzer implementation using NetworkX."""

    def __init__(self):
        # No longer log warnings at init - dependencies are now required
        pass

    async def analyze_workflow(self, workflow_data: dict[str, Any], project_key: str, issue_type: str) -> WorkflowGraph:
        """Analyze workflow data and create a workflow graph."""
        workflow = WorkflowGraph(project_key=project_key, issue_type=issue_type)

        # Check for new multi-strategy workflow data format (preferred)
        if "statuses" in workflow_data and "transitions" in workflow_data:
            return await self._create_workflow_from_enhanced_data(workflow_data, workflow)
        # Legacy format support
        elif "workflow_data" in workflow_data:
            return await self._create_workflow_from_project_data(workflow_data, workflow)
        elif "available_transitions" in workflow_data:
            return await self._create_workflow_from_transitions(workflow_data, workflow)
        else:
            # NO FALLBACKS: Fail explicitly when no real workflow data is available
            raise JiraGraphGenerationError(
                f"Cannot generate workflow graph for {project_key} {issue_type}: "
                f"No workflow data available from Jira API. This indicates either: "
                f"1) Missing Jira API integration for workflow schemas, or "
                f"2) Insufficient permissions to access workflow data. "
                f"(Project: {project_key}, Issue Type: {issue_type})"
            )

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

    async def _create_workflow_from_enhanced_data(self, workflow_data: dict[str, Any], workflow: WorkflowGraph) -> WorkflowGraph:
        """Create workflow from enhanced multi-strategy workflow data format."""
        try:
            # Extract statuses and transitions from new format
            statuses = workflow_data.get("statuses", [])
            transitions = workflow_data.get("transitions", [])
            
            logger.info(f"Creating workflow from enhanced data: {len(statuses)} statuses, {len(transitions)} transitions")
            
            # Add status nodes
            for status_info in statuses:
                status_name = status_info["name"]
                category = status_info.get("statusCategory", {}).get("name", "Unknown")
                
                node = WorkflowNode(
                    id=status_name,
                    name=status_name,
                    category=category,
                    color=self._get_status_color(category)
                )
                workflow.add_node(node)
            
            # Add transitions
            for transition_info in transitions:
                from_status = transition_info["from"]
                to_status = transition_info["to"]
                transition_name = transition_info["name"]
                
                edge = WorkflowEdge(
                    from_node=from_status,
                    to_node=to_status,
                    label=transition_name
                )
                workflow.add_edge(edge)
            
            # Add comprehensive metadata about extraction strategy
            strategy_info = {
                "strategy_used": "unknown",
                "strategy_details": {},
                "data_quality": "unknown"
            }
            
            if "workflow_scheme" in workflow_data:
                strategy_info["strategy_used"] = "direct_schema_access"
                strategy_info["data_quality"] = "high"
                strategy_info["strategy_details"] = {
                    "method": "Jira REST API - Workflow Schema",
                    "permissions": "admin_level_required",
                    "description": "Direct access to project workflow scheme configuration"
                }
                workflow.metadata["source"] = "direct_schema_access"
            else:
                # Check if this looks like Strategy 2 (logical transitions)
                logical_transition_patterns = ["Start ", "Complete to ", "Move to "]
                logical_transitions = sum(1 for t in transitions if any(t["name"].startswith(pattern) for pattern in logical_transition_patterns))
                
                if logical_transitions > len(transitions) * 0.5:
                    strategy_info["strategy_used"] = "project_statuses_with_logical_transitions"
                    strategy_info["data_quality"] = "good"
                    strategy_info["strategy_details"] = {
                        "method": "Jira REST API - Project Statuses + Generated Transitions",
                        "permissions": "standard_user",
                        "description": "Real statuses with logically generated workflow transitions"
                    }
                    workflow.metadata["source"] = "project_statuses_with_logical_transitions"
                else:
                    strategy_info["strategy_used"] = "sample_issue_extraction"
                    strategy_info["data_quality"] = "limited"
                    strategy_info["strategy_details"] = {
                        "method": "Jira REST API - Sample Issue Analysis",
                        "permissions": "read_only",
                        "description": "Workflow data extracted from existing project issues"
                    }
                    workflow.metadata["source"] = "sample_issue_extraction"
            
            # Add strategy information to workflow metadata
            workflow.metadata.update(strategy_info)
            
            logger.info(f"Successfully created workflow using {strategy_info['strategy_used']}: {len(workflow.nodes)} nodes, {len(workflow.edges)} edges")
            return workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow from enhanced data: {str(e)}")
            raise JiraGraphGenerationError(f"Enhanced workflow creation failed: {str(e)}")

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


# Use standard logging pattern consistent with rest of project
logger = logging.getLogger(__name__)
