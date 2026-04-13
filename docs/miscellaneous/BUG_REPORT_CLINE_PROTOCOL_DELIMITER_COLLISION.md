# PM Assessment: Bug Report -- Large MCP Response / Cline Protocol Delimiter Collision

**Assessed by:** Larry Dawson (Product Manager)
**Assessment Date:** 2026-04-13
**Original Report Date:** 2026-04-13
**Component:** jira-helper MCP server
**Report Source:** Primary user (Larry Dawson, via Cline/Claude session)

---

## Executive Summary

This bug report describes a real, confirmed defect in jira-helper. The fix is well understood, bounded in scope, and should be implemented promptly. The primary cause is a protocol delimiter collision -- not response size. All four suggested mitigations have merit and should be prioritized independently on their own value.

Severity confirmed at **Medium**. Priority: **High for the delimiter sanitization fix** (highest user impact, lowest risk to implement). The remaining mitigations are **Recommended** as good hygiene improvements.

---

## Root Cause Assessment

The report correctly identifies two potential causes. They are not equivalent:

### Cause 1: Protocol Delimiter Collision (Primary Cause -- Confirmed)

Cline injects `<environment_details>` XML-style tags into its internal context pipeline when processing MCP tool results. If the tool response payload itself contains the literal string `<environment_details>`, the Cline parser will treat it as a context injection point and truncate the tool result at that position.

Evidence supporting this as the primary cause:
- The issue is **data-dependent** -- it resolved on a subsequent attempt, which is consistent with querying a different page or set of issues where no ticket contained the offending text
- The user could see the raw JSON on screen, confirming the tool executed and returned data -- the failure was in Cline's parsing, not in transport or the server
- The triggering content was explicitly identified: a Jira ticket description containing `<environment_details>` pasted from a prior Cline session

This is a **client-side parsing vulnerability** triggered by **server-side output that is unguarded against protocol collisions**. The fix belongs in the server -- the server should not emit raw user-generated content in a form that can be mistaken for framework protocol markers.

### Cause 2: Response Size (Secondary, Independent Concern)

Large response payloads (50+ issues as raw JSON) are a real concern but are NOT the cause of the reported failure. The evidence is:
- Intermittent behavior inconsistent with a deterministic size threshold
- Resolution on retry (a size issue would not resolve by retrying the same query)

Response size is a **separate issue** worth addressing on its own merits (AI context window consumption, usability), but it should not be conflated with the delimiter collision defect.

---

## Mitigation Analysis

### Mitigation 1: Sanitize angle bracket sequences in string output fields

**Priority: P1 -- Implement immediately**

This is the direct fix for the confirmed root cause. Before serializing any string field from Jira (summary, description, comment body, custom field text, etc.) into the tool response, the server should strip or escape sequences that could be interpreted as XML/HTML markup by the Cline context parser.

Minimum viable approach: Replace `<` with a safe substitute (e.g., the HTML entity `&lt;` or simply strip `<` from text fields in list responses). This eliminates the collision class entirely.

Broader approach: Apply this to all string fields in all tool responses, not just the ones that triggered this report. Any Jira content field could contain angle bracket sequences introduced by:
- Developers pasting terminal or IDE output into tickets
- Jira templates with XML/HTML markup
- Automated tooling embedding structured data in ticket descriptions
- Future Cline protocol markers not yet observed

The fix is low-risk, the scope is well-bounded, and the failure mode without it is high-impact for the primary user.

Acceptance criteria:
- When a Jira ticket description contains `<environment_details>`, the tool response does not include the literal string `<environment_details>` in any field
- The sanitization applies to all text-carrying fields returned by all tools
- The sanitized output remains readable (entities or stripped brackets are both acceptable)

### Mitigation 2: Plain text formatting option

**Priority: P2 -- Include in the same sprint**

A `format=text` or `format=summary` option that returns a compact tabular representation instead of raw JSON addresses three problems simultaneously:
- Reduces collision surface area (structured text is less likely to contain raw XML-style tags than arbitrary field values)
- Reduces context window consumption significantly
- Improves readability when the AI relays results to the user

This is also the right long-term UX investment for list-returning tools. Raw JSON is a machine format; the AI client is the consumer, but the end user reads the AI's response. Compact text output serves both.

Note: This mitigation should be **additive** (a new format option, not a replacement for JSON), so existing integrations and clients that expect JSON are not broken.

### Mitigation 3: Reduce default max_results

**Priority: P2 -- Ship with the sanitization fix**

Defaulting to 20 results (from 50 or 100) is good practice. It:
- Reduces context window consumption per call
- Makes responses more likely to fit cleanly in AI working context
- Encourages explicit pagination for large datasets, which is clearer to the AI about what it has and has not retrieved

This is a **breaking change** if any callers depend on the current default. Check whether any documented use cases or examples specify the default behavior explicitly and update accordingly. The change is low risk because the tool accepts explicit `max_results` overrides.

### Mitigation 4: Truncate long string fields in list responses

**Priority: P2 -- Ship with the sanitization fix**

Capping summary fields at 200 characters and description fields at 300-500 characters in list responses is standard practice for list-view APIs. Full content should be retrievable via a dedicated detail endpoint (`get_issue_details` / `get_full_issue_details` already exist).

This reduces total payload size proportionally and also reduces the probability of embedded markup content surviving into the response. A 200-character truncated summary is unlikely to contain a full XML tag that was buried 800 characters into a description field.

---

## What Is NOT Recommended

**Do not implement framework-specific escaping for only `<environment_details>`.**

Escaping only the known trigger string is fragile. Cline may use other protocol markers. Future versions of Cline or other AI clients (Claude Code, Cursor, etc.) may use different delimiters. The correct posture is to treat all angle bracket sequences in user-generated content as potentially unsafe and sanitize them uniformly.

**Do not suppress the JSON format entirely.**

JSON is useful for AI processing and for debugging. The plain text option should be additive, not a replacement.

---

## Prioritization Decision

| Mitigation | Priority | Sprint | Risk |
|---|---|---|---|
| Sanitize angle brackets in all string output fields | P1 | Immediate | Low |
| Reduce default max_results to 20 | P2 | Same sprint | Low (verify no documented defaults) |
| Truncate long string fields in list responses | P2 | Same sprint | Low |
| Plain text format option | P2 | Same or next sprint | Low (additive) |

All four can and should ship together. The P1 sanitization fix is the defect fix. The P2 items are UX and robustness improvements that have independent value and are cheap to ship alongside the fix.

---

## Impact on Existing Functionality

- Sanitization is transparent to the AI: the AI reads the escaped or truncated content correctly
- Lower max_results default changes behavior only when the caller relies on the default; document the change in the changelog
- Field truncation in list responses is standard; `get_full_issue_details` remains available for full content
- Plain text format is additive; no existing behavior changes

---

## User Communication

The primary user (the reporter) should be informed that:
1. The root cause has been identified
2. A fix is in progress and will ship in the next release
3. The immediate workaround -- if the issue recurs -- is to avoid pasting Cline session output into Jira ticket descriptions, or to use `max_results=20` with explicit pagination

---

## Follow-On Consideration: Cline Compatibility Documentation

The file `docs/user/cline-compatibility.md` exists and should be updated to document:
- This class of protocol delimiter collision risk
- The fix applied and what it protects against
- Any remaining limitations or known edge cases

If this file does not yet cover this scenario, it is a gap in our user-facing documentation.

---

## Open Questions (For Engineering)

1. Does the current output serialization path go through a single point that can accept a sanitization transform, or is formatting distributed across each tool?
2. Are there tool responses that intentionally return raw HTML or XML content from Jira (e.g., wiki markup) where angle bracket stripping would corrupt the output?
3. What does the `format=structured` option already do? Is `format=text` already partially implemented?

---

## Decision

Approve all four mitigations. Implement P1 (sanitization) and P2 items in the same release. Update `docs/user/cline-compatibility.md` after shipping. Close the bug report once the sanitization fix and default max_results change are confirmed deployed and tested with the triggering data pattern.