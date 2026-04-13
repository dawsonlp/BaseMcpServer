# Requirements: Cline-Safe Output Layer

**Date:** 2026-04-13
**Priority:** High
**Origin:** [Bug Report -- Protocol Delimiter Collision](../../docs/miscellaneous/BUG_REPORT_CLINE_PROTOCOL_DELIMITER_COLLISION.md)
**Design:** [Design -- Cline-Safe Output Layer](architecture/cline-safe-output.md)

---

## Background

When Jira ticket or Confluence page content contains XML-style tags that collide with Cline's
internal context-injection markers, the tool response is silently truncated by the Cline parser.
The AI receives no result, retries the call repeatedly, and the session degrades.

The failure is data-dependent and intermittent. The user cannot predict when it will occur, and
when it does the session appears broken rather than returning an obvious error.

The root cause is user-generated content returned unsanitized in tool responses. The fix is to
sanitize user-authored string fields at the point of extraction from the Jira/Confluence API,
without altering structural metadata fields controlled by Jira.

---

## Requirements

### REQ-1: Output Sanitization (P1)

All user-authored string content returned in tool responses must be sanitized so that angle
bracket sequences cannot be interpreted as protocol markup by the consuming client.

**What counts as user-authored content:** Jira issue summaries, descriptions, and comment bodies.
Confluence page titles and page body content. Linked issue summaries when embedded in a response.

**What is not sanitized:** Structural metadata fields whose values are controlled by Jira --
status, assignee, reporter, priority, issue type, project key, issue key, dates, labels,
component names, attachment filenames, and similar.

**Acceptance criteria:**
- When a Jira ticket description contains `<environment_details>`, no tool response includes
  the literal string `<environment_details>` in any user-authored field.
- The sanitization applies uniformly: list-view responses and detail responses both sanitize
  user-authored fields.
- The sanitized output remains human-readable (HTML entity escaping is acceptable).
- No structural metadata field is altered.

### REQ-2: Default max_results Reduction (P2)

Default result counts for list-returning tools must be reduced. The current defaults of 50 are
too large for comfortable AI context window operation.

**Acceptance criteria:**
- `search_jira_issues` defaults to `max_results=20` (was 50).
- `list_project_tickets` defaults to `max_results=20` (was 50, delegates to search_jira_issues).
- `list_confluence_pages` defaults to `limit=20` (was 25).
- `search_confluence_pages` defaults to `limit=20` (was 25).
- Callers passing explicit `max_results` or `limit` values continue to work unchanged.
- The change is documented in the changelog as a behavior change, not a bug fix.

### REQ-3: Field Truncation in List Responses (P2)

In list-view responses, long user-authored text fields are capped at a reasonable length. Full
content remains available via the existing detail tools.

**Acceptance criteria:**
- `summary` is capped at 200 characters in list-view responses (the `_extract_issue()` helper
  used by `search_jira_issues` and `list_project_tickets`).
- Truncated fields display a visible indicator (ellipsis suffix).
- Detail tools (`get_issue_details`, `get_full_issue_details`, `get_confluence_page`) return
  full, untruncated content.
- Description is not returned in list-view responses. This is already the case; no change is
  required for description in list views.

### REQ-4: Plain Text Format Option (Deferred)

An optional compact text output mode for list-returning tools is deferred to the next release.

The parameter name `output_format` is reserved for this future feature. This parameter must not
be introduced with a different contract in the current release.

---

## Constraints

- No breaking changes to existing tool interfaces. Callers that pass explicit `max_results` or
  `limit` values must continue to work.
- No changes to mcp-commons.
- No changes to `src/tool_config.py` or tool registration.
- No changes to tool function signatures.
- Sanitization applies to output only. Input parameters passed by the caller to create or update
  tools are not altered.
- Implementation gate applies: checklist before code.

---

## Post-Ship Documentation Updates

The following documentation must be updated after the implementation ships:

**`docs/user/cline-compatibility.md`** -- Add a section covering:
- The protocol delimiter collision risk class and what triggers it.
- The sanitization protection now in place and what it covers.
- The Confluence body entity-escaping limitation (get_confluence_page returns body with `<`
  replaced by `&lt;`; verbatim HTML round-trip is not supported).

**`docs/developer/adding-features.md`** -- Add guidance that:
- New tools returning user-authored content must call `sanitize_string()` on those fields.
- Structural metadata fields from Jira do not require sanitization.
- Reference the design document for the field classification table.