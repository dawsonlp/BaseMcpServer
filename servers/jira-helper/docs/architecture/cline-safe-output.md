# Design: Cline-Safe Output Layer

**Author:** Chief Architect
**Date:** 2026-04-13
**Status:** Approved
**Related:** [Requirements -- Cline-Safe Output](../requirements-cline-safe-output.md)

---

## Problem

Jira ticket and Confluence page content is user-authored free text. When this content contains
angle bracket sequences that collide with Cline's internal protocol markers (e.g.,
`&lt;environment_details&gt;`), the Cline parser silently truncates the tool response. The AI
receives no result, retries repeatedly, and the session degrades.

The failure is data-dependent and intermittent, which makes it more disruptive than a consistent
failure. The user sees a broken session rather than an obvious error.

## Design Principle

Sanitize user-authored content at the point where it is extracted from the Jira/Confluence API
response. Structural metadata from Jira (status names, project keys, assignee display names) is
controlled vocabulary from the Jira system and does not require sanitization.

This approach keeps the sanitization concern close to the data source, makes the call sites
explicit and auditable, and avoids wrapping the tool registration or output serialization path.

## Components

### output_sanitizer (new module: `src/output_sanitizer.py`)

**Responsibility:** Provide pure functions that transform individual string values to be safe for
protocol-sensitive consumers.

**Interface:**

```
sanitize_string(value: str) -> str
```
Escapes `<` to `&lt;` in the input string. Returns the transformed string.

```
truncate_string(value: str, max_length: int, suffix: str = "...") -> str
```
Returns the string truncated to `max_length` characters with the suffix appended if truncation
occurred. Returns the original string unchanged if it is within the limit.

**Constraints:**
- Pure functions. No I/O, no logging, no dependencies beyond the standard library.
- `sanitize_string` is idempotent. The output of `&lt;` contains no `<`, so re-application
  produces the same result.
- Both functions handle empty string and `None` gracefully.

### Tool Extraction Points (existing modules, modified)

Each tool function that extracts user-authored text from Jira/Confluence API responses applies
`sanitize_string()` to those specific fields at the point of extraction.

**Fields classified as user-authored:**

| Field | Source | Present In |
|-------|--------|-----------|
| `summary` | Jira issue | `_extract_issue()`, `get_issue_details()`, `get_full_issue_details()`, link summaries |
| `description` | Jira issue | `get_issue_details()`, `get_full_issue_details()` |
| `body` (comment) | Jira comment | `get_full_issue_details()` |
| `title` | Confluence page | `get_confluence_page()`, `list_confluence_pages()`, `search_confluence_pages()` |
| `body` (page) | Confluence storage format | `get_confluence_page()` |

**Fields NOT sanitized -- Jira-controlled metadata:**

`status`, `assignee`, `reporter`, `priority`, `issue_type`, `project`, `key`, `id`, `created`,
`updated`, `labels`, `components`, `filename`, `size`, `version`, `type`, `space_key`,
`transition`, `message`

### Truncation Policy

Truncation is applied only in list-view contexts, not detail views.

| Context | summary cap | description cap | body cap |
|---------|------------|----------------|---------|
| `_extract_issue()` (list view) | 200 chars | N/A (not returned) | N/A |
| `get_issue_details()` (detail) | No cap | No cap | N/A |
| `get_full_issue_details()` (detail) | No cap | No cap | No cap |
| `get_confluence_page()` (detail) | No cap | N/A | No cap |

Sanitization is applied in all contexts. Truncation is applied only where indicated above.

## Data Flow

```
Jira/Confluence API response (raw JSON)
    |
    v
Tool function extracts fields into result dict
    |
    +--> Structural metadata fields (key, status, assignee, etc.) -- passed through unchanged
    |
    +--> User-authored fields (summary, description, comment body, page title, page body)
             |
             v
         sanitize_string()  [all contexts]
             |
             v  (list-view tools only)
         truncate_string()
             |
             v
         Placed in result dict
    |
    v
Tool returns sanitized dict
    |
    v
FastMCP serializes to JSON and sends to client
```

## Constraints and Limitations

**Input parameters are not sanitized.** `create_confluence_page`, `create_jira_ticket`,
`update_confluence_page`, and `update_jira_issue` pass user-provided content through to the
Jira/Confluence API unchanged. This is correct -- the sanitization protects the output path only.

**Confluence body content is entity-escaped.** `get_confluence_page` returns body content with
`<` replaced by `&lt;`. The AI reads this correctly. If a future use case requires verbatim HTML
round-trip through jira-helper, the caller must reverse the escaping. See
`docs/user/cline-compatibility.md` for the documented limitation.

**New tools that return user-authored content must call `sanitize_string()`.** This is a
convention, not an enforced constraint. Document this requirement in
`docs/developer/adding-features.md` so future implementors are aware.

**The `output_format` parameter name is reserved.** A future plain-text output option will use
`output_format` as the parameter name. Do not introduce a parameter named `output_format` in this
release. (Note: `get_full_issue_details` already uses `format` for its existing behavior;
`output_format` is distinct and must not be confused with it.)

## What Is Not Changed

- mcp-commons: no changes
- FastMCP: no changes
- `src/tool_config.py`: no changes
- Tool function signatures: no changes (only field extraction logic and default parameter values)
- Input parameter handling: no changes