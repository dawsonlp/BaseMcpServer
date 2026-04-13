"""Workflow operations: transitions, workflow graph generation."""

import base64
import io
import json
import logging

from jira_client import get_jira_client, resolve_instance_name
from exceptions import JiraError, JiraValidationError, JiraApiError, JiraGraphError

logger = logging.getLogger(__name__)


def generate_project_workflow_graph(
    project_key: str, issue_type: str = "Task", output_format: str = "png",
    instance_name: str = None, **kwargs
) -> dict:
    """Generate a visual workflow graph for a project and issue type."""
    if not project_key:
        raise JiraValidationError("project_key is required.")
    name = resolve_instance_name(instance_name)
    client = get_jira_client(name)

    try:
        # Get workflow data using multi-strategy approach
        workflow = _extract_workflow_data(client, project_key, issue_type)

        if output_format == "json":
            return {
                "project_key": project_key, "issue_type": issue_type,
                "instance": name, "format": "json", "workflow": workflow,
            }

        # Generate visual graph
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import networkx as nx
        except ImportError:
            raise JiraGraphError("matplotlib and networkx are required for graph generation.")

        G = nx.DiGraph()
        statuses = workflow.get("statuses", [])
        transitions = workflow.get("transitions", [])

        for s in statuses:
            G.add_node(s["name"], category=s.get("category", ""))

        for t in transitions:
            if t.get("from_status") and t.get("to_status"):
                G.add_edge(t["from_status"], t["to_status"], label=t.get("name", ""))

        if not G.nodes():
            return {
                "project_key": project_key, "issue_type": issue_type,
                "instance": name, "format": output_format,
                "message": "No workflow data available for this project/issue type.",
            }

        # Layout and draw
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

        # Color by category
        color_map = {"To Do": "#4A90D9", "In Progress": "#F6C342", "Done": "#14892C"}
        node_colors = [
            color_map.get(G.nodes[n].get("category", ""), "#C0C0C0") for n in G.nodes()
        ]

        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=2000, alpha=0.9)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_weight="bold")
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#666666", arrows=True, arrowsize=20)

        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=6)

        ax.set_title(f"Workflow: {project_key} - {issue_type}", fontsize=14, fontweight="bold")
        ax.axis("off")
        plt.tight_layout()

        buf = io.BytesIO()
        fmt = "svg" if output_format == "svg" else "png"
        fig.savefig(buf, format=fmt, dpi=150, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")

        return {
            "project_key": project_key, "issue_type": issue_type,
            "instance": name, "format": fmt,
            "image_base64": encoded,
            "message": f"Generated {fmt.upper()} workflow graph for {project_key}/{issue_type}",
        }
    except (JiraError, JiraGraphError):
        raise
    except Exception as e:
        raise JiraGraphError(f"Failed to generate workflow graph: {e}", instance_name=name)


def _extract_workflow_data(client, project_key: str, issue_type: str) -> dict:
    """Extract workflow data using multiple strategies."""
    statuses = []
    transitions = []

    # Strategy 1: Try project statuses API
    try:
        project_statuses = client.get_project_issue_statuses(project_key)
        if isinstance(project_statuses, list):
            for itype in project_statuses:
                if itype.get("name", "").lower() == issue_type.lower():
                    for s in itype.get("statuses", []):
                        category = s.get("statusCategory", {}).get("name", "") if s.get("statusCategory") else ""
                        statuses.append({
                            "name": s.get("name", ""),
                            "id": s.get("id", ""),
                            "category": category,
                        })
                    break
    except Exception:
        pass

    # Strategy 2: Try getting statuses from a sample issue
    if not statuses:
        try:
            jql = f'project = "{project_key}" AND issuetype = "{issue_type}" ORDER BY created DESC'
            result = client.jql(jql, limit=1)
            issues = result.get("issues", []) if isinstance(result, dict) else []
            if issues:
                sample_key = issues[0].get("key", "")
                if sample_key:
                    trans = client.get_issue_transitions(sample_key)
                    current = issues[0].get("fields", {}).get("status", {})
                    if current:
                        cat = current.get("statusCategory", {}).get("name", "") if current.get("statusCategory") else ""
                        statuses.append({"name": current.get("name", ""), "id": current.get("id", ""), "category": cat})
                    for t in trans:
                        to_status = t.get("to", {})
                        if to_status:
                            cat = to_status.get("statusCategory", {}).get("name", "") if to_status.get("statusCategory") else ""
                            s = {"name": to_status.get("name", ""), "id": to_status.get("id", ""), "category": cat}
                            if s not in statuses:
                                statuses.append(s)
                            transitions.append({
                                "name": t.get("name", ""),
                                "from_status": current.get("name", "") if current else "",
                                "to_status": to_status.get("name", ""),
                            })
        except Exception:
            pass

    # Generate logical transitions if we have statuses but no transitions
    if statuses and not transitions:
        transitions = _generate_logical_transitions(statuses)

    return {"statuses": statuses, "transitions": transitions}


def _generate_logical_transitions(statuses: list) -> list:
    """Generate logical transitions from status categories."""
    transitions = []
    todo = [s for s in statuses if s.get("category") == "To Do"]
    in_progress = [s for s in statuses if s.get("category") == "In Progress"]
    done = [s for s in statuses if s.get("category") == "Done"]

    # To Do -> In Progress
    for t in todo:
        for ip in in_progress[:1]:
            transitions.append({"name": "Start", "from_status": t["name"], "to_status": ip["name"]})

    # In Progress -> Done
    for ip in in_progress:
        for d in done[:1]:
            transitions.append({"name": "Complete", "from_status": ip["name"], "to_status": d["name"]})

    # In Progress -> In Progress (between substates)
    for i, ip1 in enumerate(in_progress[:-1]):
        transitions.append({"name": "Progress", "from_status": ip1["name"], "to_status": in_progress[i + 1]["name"]})

    return transitions