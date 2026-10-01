# Workflow Resources

Status: implemented. Jira Helper explicitly registers two public SDK file resources
from `tool_config.py`; the server factory uses `add_resource()`.

| URI | Content |
| --- | --- |
| `jira-workflow://latest/workflow.png` | PNG image, returned as binary resource content |
| `jira-workflow://latest/workflow.svg` | SVG, returned as text resource content |

`generate_project_workflow_graph` returns a typed result containing project,
issue type, instance, format, and (after successful rendering) `resource_uri` and
message. JSON mode returns workflow data directly. A no-data result includes a
message and no resource URI. Existing result fields and URIs are preserved.

## Publication and failure

The domain function performs synchronous lookup and rendering in a worker. A
process-wide lock serializes plotting across server instances. Rendering writes a
temporary file in the destination directory and atomically replaces the current
artifact. Figures and temporary files are cleaned up on failure; an existing
artifact survives a failed replacement.

Only after success does the MCP adapter call `ctx.notify_resource_updated(uri)`.
Modern clients receive updates through an acknowledged `Client.listen(...)`
subscription for that URI. Tests exercise the real subscription, resource read,
and failed-publication behavior, rather than only a notification helper mock.

A registered file that has not been generated raises `ResourceNotFoundError` via
a small `FileResource` subclass. The public protocol error is `-32602` with the
requested URI in `data`; an unknown URI is also tested as a not-found error.

## Ownership limits

These URIs intentionally mean **latest**, not a durable result belonging to one
request. The artifact paths remain relative to the configured server directory.
A later generation can replace an earlier result; atomic publication prevents
partial files but does not provide caller isolation. Separate processes do not
share the plotting lock. Per-request artifact identity, retention, and multi-user
access control are separate design requirements, not claims of this implementation.

Jira client ownership is independent of artifact storage: each server lifespan
owns and closes its own lazy clients, while the established artifact paths remain
shared. Cancellation does not undo an already published file.

See [adding features](../developer/adding-features.md) and the
[implementation plan](../../../../docs/developer/jira-helper-mcp-improvement-plan.md).
