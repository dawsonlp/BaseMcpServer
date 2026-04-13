# Product Request to Chief Architect: Cline-Safe Output Layer for jira-helper

**From:** Larry Dawson, Product Manager
**To:** Chief Architect
**Date:** 2026-04-13
**Priority:** High
**Related Assessment:** `docs/miscellaneous/BUG_REPORT_CLINE_PROTOCOL_DELIMITER_COLLISION.md`

---

## Context

Our primary user (also myself, in practice) filed a confirmed defect against jira-helper. When Jira ticket content includes XML-style tags that collide with Cline's internal context-injection markers -- specifically `<environment_details>` -- the tool response is silently truncated by the Cline parser. The AI receives no result, retries the call repeatedly, and the session degrades.

The defect is data-dependent and intermittent, which makes it more disruptive than a consistent failure: users cannot predict when it will happen, and when it does the session appears to be broken rather than returning an obvious error.

The full assessment is in the linked document. This memo describes what I need from architecture to address it.

---

## What I Need

I need you to design and oversee the implementation of four changes to jira-helper. I am treating all four as a single release. I am not asking for a big redesign -- the scope is bounded and the server is in good shape. What I need is an intentional architectural decision about where these concerns live and how they are applied consistently across the 32 tools.

### 1. Output Sanitization (P1 -- the defect fix)

All user-generated string content returned in tool responses must be sanitized to prevent angle bracket sequences from being interpreted as protocol markup by the Cline parser or any other XML-sensitive client.

**What I need from architecture:**
- A decision on where sanitization lives. My preference is a single sanitization pass applied at the response serialization boundary rather than scattered per-tool. The server already routes all tools through `tool_config.py` and `mcp-commons` -- this seems like the right seam. I would like your assessment of whether the right place is in mcp-commons itself (benefiting all servers), in a shared utility within jira-helper, or somewhere else.
- A decision on sanitization depth: minimum viable is escaping `<` to `&lt;` in all string fields. I want to understand if there are tool responses (e.g., Confluence page body retrieval) that intentionally return HTML/markup where this transform would corrupt the output, and if so how to handle that exception.
- A clear, testable interface for the sanitization function so engineering can write a unit test that proves the fix holds for the known trigger pattern and its variants.

### 2. Default max_results Reduction (P2)

The current defaults of 50-100 results per call are too large for comfortable AI context window operation. I want the default reduced to 20 across all list-returning tools (`search_jira_issues`, `list_project_tickets`, and any others with a max_results parameter).

**What I need from architecture:**
- Confirmation this is a clean, backward-compatible change (callers who need more can pass `max_results` explicitly).
- Identification of any tools where 20 is too small to be useful as a default (e.g., `list_jira_projects` probably returns a small list anyway).
- A note in the changelog entry template so the change is documented as a behavior change, not just a bug fix.

### 3. Field Truncation in List Responses (P2)

In list-view responses (not detail responses), long text fields -- primarily `summary` and `description` -- should be capped at a reasonable length. The full content is already available via `get_issue_details` and `get_full_issue_details`, so list truncation does not lose information.

**What I need from architecture:**
- Recommended character caps for each field type. I suggest summary at 200 characters and description at 400 characters, but defer to your judgment on what produces a useful list-view response.
- A decision on whether truncation belongs alongside sanitization (same boundary) or as a separate concern. I expect they belong together, but I want your call.
- Confirmation that truncation is applied only to list-view responses and not to detail responses, so `get_full_issue_details` continues to return complete content.

### 4. Plain Text / Summary Format Option (P2)

I want an optional compact text output mode for list-returning tools. When a caller passes `format=text` (or similar), the tool should return a concise tabular or bulleted summary rather than raw JSON. This addresses both context window consumption and collision surface area (free text is less likely to contain XML-tag sequences than raw Jira field values).

**What I need from architecture:**
- A design for the format parameter: which tools support it, what the output structure looks like, and whether it is a tool-level parameter or a server-level configuration.
- An opinion on whether this is worth doing now alongside the other three changes, or whether it should be deferred to the next release. I lean toward deferring it to keep the P1 fix clean, but if it is straightforward to add I would prefer it ships together.
- If deferred, a note that the parameter name and format contract should be reserved so it can be added without a breaking change later.

---

## Constraints

- **No breaking changes to existing tool interfaces.** Callers that pass `max_results=50` or `max_results=100` explicitly must continue to work. The format parameter must be optional with the current behavior as the default.
- **Sanitization must not corrupt intentional markup.** Confluence page body content and Jira description fields in detail responses may contain legitimate HTML. The sanitization design must account for this.
- **The fix must apply uniformly.** I do not want per-tool sanitization. If we fix it in `search_jira_issues` but miss it in `list_project_tickets` or `get_full_issue_details`, we have not fixed the problem -- we have just moved it. A single boundary point is required.
- **The implementation gate applies.** Per our standard process, I expect a checklist before any code is written.

---

## What I Am Not Asking For

I am not asking for a redesign of the tool architecture, a new abstraction layer, or a change to the mcp-commons interface beyond what the sanitization placement decision requires. This is a targeted, high-confidence fix. The server is otherwise in good shape.

---

## Suggested Next Steps

1. You review this request and the linked PM assessment.
2. You confirm or correct my read of the architecture -- particularly whether the serialization boundary in `tool_config.py` / `mcp-commons` is the right seam for sanitization, or whether a different location is cleaner.
3. You produce the implementation checklist per our standard gate.
4. Engineering implements against the checklist.
5. `docs/user/cline-compatibility.md` is updated post-ship to document this class of risk and the protection now in place.

I would like the architecture response by end of week. The P1 fix is blocking the primary user from reliable use of jira-helper in sessions that touch tickets with pasted terminal output.

---

## Reference Architecture (Current State)

For convenience, the relevant parts of the current server:

- **Entry point:** `src/main.py` -- routes to `run_mcp_server()` in mcp-commons
- **Tool registration:** `src/tool_config.py` -- 32 tools registered, all routed through mcp-commons
- **Tool implementations:** `src/tools/` -- issues, search, comments, links, time_tracking, workflow, confluence, files
- **Client factory:** `src/jira_client.py` -- connection caching per instance
- **Transport:** stdio (primary), SSE, streamable-HTTP

All tool output currently passes through mcp-commons serialization. The question is whether the sanitization transform can be injected at that layer cleanly, or whether it requires a wrapper at each tool boundary.