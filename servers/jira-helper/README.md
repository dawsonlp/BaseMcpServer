# Jira Helper MCP Server

A Jira and Confluence integration MCP server providing 32 tools for issue management, search, time tracking, workflow visualization, file operations, and Confluence page management.

**Version:** 2.0.0

## Architecture

Flat module structure following the mcp-commons pattern:

```
src/
├── main.py              # Entry point (stdio/sse/streamable-http)
├── config.py            # YAML configuration loading
├── tool_config.py       # Tool registration (32 tools → mcp-commons)
├── jira_client.py       # Client factory with connection caching
├── exceptions.py        # Simplified exception hierarchy (7 classes)
└── tools/               # Tool implementations
    ├── issues.py        # Issue CRUD, transitions, assignments
    ├── search.py        # JQL search, project tickets, validation
    ├── comments.py      # Comments, transition queries
    ├── links.py         # Issue links, epic-story links
    ├── time_tracking.py # Work logs, time estimates
    ├── workflow.py      # Workflow graph generation (matplotlib)
    ├── confluence.py    # Spaces, pages, search, create, update
    └── files.py         # Attachments: upload, list, delete
```

## Setup

### Prerequisites
- Python 3.13+
- Jira and/or Confluence instance with API access

### Configuration

Copy the example config and edit with your instance details:

```bash
cp config.yaml.example ~/.config/mcp-manager/servers/jira-helper/config.yaml
```

The config file supports multiple Jira and Confluence instances:

```yaml
server:
  name: jira-helper-server
  log_level: INFO

default_jira_instance: primary

instances:
  primary:
    jira:
      url: https://your-domain.atlassian.net
      username: your-email@example.com
      api_token: your-jira-api-token
    confluence:
      url: https://your-domain.atlassian.net/wiki
      username: your-email@example.com
      api_token: your-confluence-api-token
```

### Installation

```bash
mcp-manager install local jira-helper --source servers/jira-helper --force
```

## Available Tools (32)

### Core Jira Operations (13)
| Tool | Description |
|------|-------------|
| `list_jira_projects` | List all projects in the Jira instance |
| `get_issue_details` | Get issue details by key |
| `get_full_issue_details` | Get comprehensive issue details with comments, links, attachments |
| `create_jira_ticket` | Create a new issue |
| `update_jira_issue` | Update issue fields |
| `transition_jira_issue` | Transition issue through workflow |
| `get_issue_transitions` | Get available transitions |
| `change_issue_assignee` | Change assignee |
| `list_project_tickets` | List project issues with filters |
| `get_custom_field_mappings` | Get custom field ID/name mappings |
| `generate_project_workflow_graph` | Generate workflow visualization |
| `list_jira_instances` | List configured instances |

### Search (3)
| Tool | Description |
|------|-------------|
| `search_jira_issues` | Execute JQL search |
| `list_project_tickets` | Filter project issues |
| `validate_jql_query` | Validate JQL syntax |

### Issue Links (4)
| Tool | Description |
|------|-------------|
| `create_issue_link` | Link two issues |
| `create_epic_story_link` | Create epic-story link |
| `get_issue_links` | Get issue links |
| `create_issue_with_links` | Create issue with links |

### Time Tracking (4)
| Tool | Description |
|------|-------------|
| `log_work` | Log work time |
| `get_work_logs` | Get work logs |
| `get_time_tracking_info` | Get time tracking info |
| `update_time_estimates` | Update estimates |

### File Operations (3)
| Tool | Description |
|------|-------------|
| `upload_file_to_jira` | Upload attachment |
| `list_issue_attachments` | List attachments |
| `delete_issue_attachment` | Delete attachment |

### Confluence (6)
| Tool | Description |
|------|-------------|
| `list_confluence_spaces` | List spaces |
| `list_confluence_pages` | List pages in space |
| `get_confluence_page` | Get page details |
| `search_confluence_pages` | Search pages |
| `create_confluence_page` | Create page |
| `update_confluence_page` | Update page |

## Development

```bash
cd servers/jira-helper
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Transport Modes

```bash
# stdio (default, used by mcp-manager)
jira-helper stdio

# SSE (HTTP server)
jira-helper sse

# Streamable HTTP
jira-helper streamable-http

# Help
jira-helper help