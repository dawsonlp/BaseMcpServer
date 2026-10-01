# Adding Jira Helper Features

Use the [MCP v2 conventions](../../../../docs/developer/mcp-v2-conventions.md).
Jira Helper uses ordinary domain functions, explicit MCP adapters, a registration
map, and a server factory. Start from a concrete operation and its input/output
contract; there are no generic service/use-case/repository layers to instantiate.

## Where responsibilities live

| File | Responsibility |
| --- | --- |
| `src/tools/*.py` | Domain validation, Atlassian operations, and typed projected results |
| `src/mcp_adapters.py` | Explicit public tool signatures, MCP context, worker dispatch, safe errors, and notifications |
| `src/jira_client.py` | Lazy client construction, per-service/instance serialization, and deterministic cleanup |
| `src/runtime.py` | Lifespan state and execution using its owned registry |
| `src/tool_config.py` | Tool metadata, adapter references, behavior hints, and resource registration objects |
| `src/main.py` | Fresh server factory, lifespan composition, and transport entry points |

## Add an operation

1. Define its typed domain function in the appropriate `tools` module. For network
   operations, accept an explicit keyword-only `get_client: Callable[[], Jira]`
   (or `Confluence`) dependency. Invoke it after local validation. The adapter
   supplies an instance name resolved from the server's configuration.
2. Define stable results using `TypedDict`, including nested projected records.
   Use an open dictionary only for genuinely open upstream data. Domain functions
   do not import MCP or retrieve runtime globals.
3. Add an ordinary, explicitly typed async function in `mcp_adapters.py`. Keep
   client-facing arguments concrete and inject `ctx: Context[RuntimeState]` as a
   keyword-only parameter. Call the private `_call` execution helper with the
   service, instance, domain function, and its arguments. This helper runs the
   synchronous operation off-loop, within the owned client scope, and translates
   expected domain exceptions. Do not expose its internal `**arguments` on tools.
4. Add the adapter reference and description to `JIRA_TOOLS`, classify its behavior
   hints, and let `create_server()` register it through `add_tool()`. No tool
   decorators, import-time server, or private SDK manager access is needed.
5. Test direct domain behavior with a fake client supplier, then test the public
   tool using `Client(create_server(client_registry_factory=...))`. Exercise both
   protocol modes for behavior claimed to support both.

Use a lazy client supplier so invalid arguments fail before an external request.
It is scoped to one operation: do not retain it or return a client to background
work. Compound operations stay within that scope and reuse its client.

## Errors and partial success

Domain code raises the existing `JiraError` subclasses. Locally authored validation
and missing-configuration messages must be safe to show callers. Authentication,
permission, connection, and API messages are translated by `public_error_message()`;
raw upstream bodies and credentials must not reach the tool result.

Unexpected exceptions remain sanitized by the SDK. Test the public `is_error`
flag and explanation, not merely that a Python exception occurred. Successful
partial operations retain their result, identifiers, and failure details: an issue
created with failed links must not look like nothing happened. Check existing state
before retrying a write; cancellation does not reverse completed external effects.

## Ownership and concurrency

Each server lifespan owns a separate registry. Clients are created lazily, have
finite request timeouts, and are closed on shutdown. Operations are serialized per
service/instance; distinct instances can run independently. Worker cancellation
is not abandonment: shutdown waits for owned operations before closing clients.
A timeout is a bound on an HTTP request, not a guarantee of immediate shutdown of
an entire compound operation or graph render.

Workflow rendering runs off-loop and uses a process-wide rendering lock because
Matplotlib has shared state. It closes figures on failure and atomically replaces
artifacts. The adapter publishes updates only after success. See
[resource behavior](../architecture/mcp-resource-system.md).

## Preserve output sanitization

Apply `sanitize_string()` to user-authored content at field extraction, as existing
operations do. This compatibility behavior protects XML-sensitive consumers; it
is separate from safe error messages. Use `truncate_string()` for existing bounded
list summaries, and preserve full detail where the contract calls for it.

```python
from output_sanitizer import sanitize_string, truncate_string

summary = truncate_string(sanitize_string(issue["fields"].get("summary", "")), 200)
```

See [Cline-safe output](../architecture/cline-safe-output.md) for the existing
classification and rationale. Do not silently change escaping behavior as part
of a schema refinement.

## Verify before installation

Run `uv run --directory servers/jira-helper --locked --extra dev pytest`, build
and inspect the package, and exercise a fresh stdio subprocess. Test actual
subscription delivery when adding notifications and ASGI behavior when changing
HTTP integration. Managed installation is separate from checkout verification;
use MCP Manager when installation is requested and verify the new process.
