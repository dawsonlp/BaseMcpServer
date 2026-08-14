# MCP Python SDK v2 Conventions

This repository uses stable `mcp>=2.0.0,<3.0.0` and direct `MCPServer`
factories. Tools and resources are registered imperatively with `add_tool()`
and `add_resource()`. Registration or validation decorators are not used. A
decorator is considered separately only for genuine cross-cutting behavior.

## Contracts

- Every public parameter has a concrete type. Optional values include `None`,
  collections declare item/value types, and existing numeric or literal domain
  limits are represented in the signature.
- Do not expose `**kwargs`. Use an explicit `dict[str, Any]` field only when the
  domain is actually open-ended.
- Repository-owned stable results use `TypedDict` or Pydantic models. Upstream
  payloads that may add fields use an open `dict[str, Any]` schema.
- Invalid arguments raise `ValueError`; operational failures raise
  `RuntimeError` or a domain-specific ordinary exception. Returned error/status
  fields describe valid domain state, not a failed invocation.
- Protocol tests use `Client(..., raise_exceptions=True)` for successful calls
  and also assert `is_error` behavior with exception conversion enabled.

## Tool behavior matrix

`RO` means the tool does not mutate user or external state. `Destructive` means
the mutation can replace or remove existing state. `Idempotent` is a behavioral
hint, not a retry guarantee. `Open` means the tool interacts with state outside
the server process. These values are the source for registered
`ToolAnnotations`.

| Server | Tool | RO | Destructive | Idempotent | Open |
| --- | --- | ---: | ---: | ---: | ---: |
| Jira | `list_jira_projects` | yes | no | yes | yes |
| Jira | `get_issue_details` | yes | no | yes | yes |
| Jira | `get_full_issue_details` | yes | no | yes | yes |
| Jira | `create_jira_ticket` | no | no | no | yes |
| Jira | `add_comment_to_jira_ticket` | no | no | no | yes |
| Jira | `transition_jira_issue` | no | yes | no | yes |
| Jira | `get_issue_transitions` | yes | no | yes | yes |
| Jira | `change_issue_assignee` | no | yes | no | yes |
| Jira | `list_project_tickets` | yes | no | yes | yes |
| Jira | `get_custom_field_mappings` | yes | no | yes | yes |
| Jira | `generate_project_workflow_graph` | no | no | yes | yes |
| Jira | `list_jira_instances` | yes | no | yes | no |
| Jira | `update_jira_issue` | no | yes | no | yes |
| Jira | `search_jira_issues` | yes | no | yes | yes |
| Jira | `validate_jql_query` | yes | no | yes | no |
| Jira | `create_issue_link` | no | no | no | yes |
| Jira | `create_epic_story_link` | no | no | no | yes |
| Jira | `get_issue_links` | yes | no | yes | yes |
| Jira | `create_issue_with_links` | no | no | no | yes |
| Jira | `log_work` | no | no | no | yes |
| Jira | `get_work_logs` | yes | no | yes | yes |
| Jira | `get_time_tracking_info` | yes | no | yes | yes |
| Jira | `update_time_estimates` | no | yes | no | yes |
| Jira | `upload_file_to_jira` | no | no | no | yes |
| Jira | `list_issue_attachments` | yes | no | yes | yes |
| Jira | `delete_issue_attachment` | no | yes | no | yes |
| Jira | `list_confluence_spaces` | yes | no | yes | yes |
| Jira | `list_confluence_pages` | yes | no | yes | yes |
| Jira | `get_confluence_page` | yes | no | yes | yes |
| Jira | `search_confluence_pages` | yes | no | yes | yes |
| Jira | `create_confluence_page` | no | no | no | yes |
| Jira | `update_confluence_page` | no | yes | no | yes |
| World Context | `get_current_datetime` | yes | no | yes | no |
| World Context | `get_stock_market_overview` | yes | no | yes | yes |
| World Context | `get_stock_quote` | yes | no | yes | yes |
| World Context | `get_news_headlines` | yes | no | yes | yes |
| World Context | `get_context_summary` | yes | no | yes | yes |
| World Context | `get_latest_tool_versions` | yes | no | yes | yes |
| World Context | `get_python_package_version` | yes | no | yes | yes |
| MCP Server Creator | `help` | yes | no | yes | no |
| MCP Server Creator | `create_mcp_server` | no | yes | no | yes |
| MCP Server Creator | `list_installed_servers` | yes | no | yes | no |
| Loadbearing YouTube | `analyze_video` | no | no | no | yes |
| Loadbearing YouTube | `get_analysis_result` | yes | no | yes | no |
| Loadbearing YouTube | `list_analysis_jobs` | yes | no | yes | no |
| Loadbearing YouTube | `get_video_transcript` | yes | no | yes | yes |
| Loadbearing YouTube | `list_analysis_providers` | yes | no | yes | no |
| Template | `echo` | yes | no | yes | no |

## Lifecycle, resources, and transport

Executors, clients, and other long-lived runtime objects belong to a server
lifespan and must shut down deterministically. Generated files are exposed as
MCP resources and replaced atomically; producing tools return a URI and notify
subscribers only after success.

Streamable HTTP defaults to loopback. A non-loopback host requires explicit,
non-empty allowed-host and allowed-origin lists passed through
`TransportSecuritySettings`. Ambiguous exposure fails before startup. Do not
add middleware for behavior already provided by the SDK.

The current Loadbearing job/polling mechanism remains intentional. MCP tasks,
prompts, elicitation, and sampling are outside this effort until a concrete use
case is approved.
