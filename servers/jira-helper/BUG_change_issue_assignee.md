# BUG: `change_issue_assignee` silently no-ops on Jira Cloud

**Severity:** High
**File:** `src/tools/issues.py:293`
**Discovered:** 2026-04-24

---

## Summary

`change_issue_assignee` always returns a fabricated success message but never actually updates the assignee field on Jira Cloud instances. The tool is completely broken for any Cloud tenant.

---

## Reproduction

Live repro against the `highspring` Jira Cloud instance, issue AG-72:

| Attempt | Input | MCP response | Actual result |
|---|---|---|---|
| 1 | `assignee="Larry Dawson"` (display name) | `"Successfully changed assignee of AG-72 to Larry Dawson"` | Assignee: Unassigned |
| 2 | `assignee="607f4e4de851ab006b4e65c5"` (accountId) | `"Successfully changed assignee of AG-72 to 607f4e..."` | Assignee: Unassigned |
| 3 | `assignee="ldawson@builtglobal.com"` (email) | `"Successfully changed assignee of AG-72 to ldawson@..."` | Assignee: Unassigned |

`get_full_issue_details` on AG-72 confirmed `"assignee": "Unassigned"` after every call. There is no caching issue on the read side.

---

## Root Cause

`src/tools/issues.py:293`:

```python
client.issue_update(key, fields={"assignee": {"name": assignee}})
```

The `{"name": ...}` shape is the deprecated **Jira Server** user identifier. Jira Cloud removed the `name` field approximately 2019 as part of GDPR compliance (users are referenced only by `accountId`). When Cloud receives this payload it silently ignores the unrecognized `name` sub-key, performs no update, and returns `200 OK` with no error body.

Because the function only checks for exceptions (and the PUT raises none), the `except` branches are never triggered and the hardcoded success message is returned unconditionally.

The Jira Server identifier, the Jira Cloud accountId, and the user's email address all fail the same way -- Cloud rejects all of them silently when wrapped in `{"name": ...}`.

---

## Proposed Fix

### Minimal fix

Replace line 293:

```python
# Before (broken on Jira Cloud)
client.issue_update(key, fields={"assignee": {"name": assignee}})

# After
client.issue_update(key, fields={"assignee": {"accountId": assignee}})
```

This unblocks callers who already know the accountId. The caller must pass the accountId directly.

### Better fix (preserves the convenient caller API)

1. Resolve the caller input (display name, email, or accountId) to a Cloud accountId before the update:

```python
def _resolve_to_account_id(client, identifier: str) -> str:
    """Resolve a display name, email, or accountId to a Jira Cloud accountId."""
    # If it already looks like an accountId (no @ or spaces), try it directly.
    # Otherwise search by query and pick the first exact match.
    users = client.user_find_by_user_string(query=identifier, maxResults=5)
    for user in users:
        if user.get("accountId") == identifier:
            return identifier
        if user.get("emailAddress", "").lower() == identifier.lower():
            return user["accountId"]
        if user.get("displayName", "").lower() == identifier.lower():
            return user["accountId"]
    raise JiraValidationError(f"Cannot resolve user identifier '{identifier}' to a Jira Cloud accountId.")
```

2. Use `accountId` in the update:

```python
account_id = _resolve_to_account_id(client, assignee)
client.issue_update(key, fields={"assignee": {"accountId": account_id}})
```

3. **Read-back verification** (belt-and-suspenders against future silent-success paths):

```python
updated = client.issue(key, fields="assignee")
actual = (updated.fields.assignee.accountId if updated.fields.assignee else None)
if actual != account_id:
    raise JiraApiError(
        f"Assignee update appeared to succeed but read-back shows '{actual}' not '{account_id}'.",
        instance_name=name,
    )
```

### Grep the rest of the codebase

Any other place in `src/tools/` that sends `{"name": ...}` for a user reference (reporter, watchers, comment authors, etc.) has the same bug. Fix them all at the same time:

```bash
grep -rn '"name":' servers/jira-helper/src/tools/
```

### Centralize the pattern

Create a shared helper so the `{"name": ...}` shape can never re-appear:

```python
def user_payload(account_id: str) -> dict:
    """Return the Cloud-compatible user reference payload."""
    return {"accountId": account_id}
```

Use `user_payload(...)` everywhere a user object needs to be sent to Jira Cloud.

---

## Impact

- **Any workflow relying on assignment is silently broken:** ownership, routing, SLA rules, notification subscriptions triggered by assignment.
- **The failure is invisible to callers:** every invocation returns a success message regardless of outcome.
- **Blast radius:** all Jira Cloud tenants since any time after Jira Cloud migrated away from `name`-based user references (circa 2019). Server tenants may still work (they still support `name`) but all active Cloud tenants are affected.

---

## Verification After Fix

Re-run the three repro cases (display name, accountId, email) on any test issue. After each call, call `get_full_issue_details` and confirm the `assignee` field shows the expected user name, not `"Unassigned"`.
