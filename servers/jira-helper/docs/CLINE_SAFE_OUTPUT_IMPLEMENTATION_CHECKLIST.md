# Implementation Checklist: Cline-Safe Output Layer

**Date:** 2026-04-13
**Requirements:** [requirements-cline-safe-output.md](requirements-cline-safe-output.md)
**Design:** [architecture/cline-safe-output.md](architecture/cline-safe-output.md)

---

## Gate

This checklist must be reviewed and accepted before any code is written. Implementation proceeds
in the order listed. Do not skip steps or reorder phases.

---

## Phase 1: output_sanitizer module

- [ ] Create `src/output_sanitizer.py`
  - [ ] Implement `sanitize_string(value: str) -> str` -- replaces `<` with `&lt;`
  - [ ] Implement `truncate_string(value: str, max_length: int, suffix: str = "...") -> str`
  - [ ] Both functions handle `None` input gracefully (return empty string)
  - [ ] Both functions handle empty string input (return empty string unchanged)
  - [ ] No imports beyond the standard library

- [ ] Create `tests/unit/test_output_sanitizer.py`
  - [ ] `sanitize_string` escapes `<` in a plain string
  - [ ] `sanitize_string` applied to `<environment_details>` produces no literal `<`
  - [ ] `sanitize_string` escapes multiple `<` in a single string
  - [ ] `sanitize_string` is idempotent (applying twice gives the same result as once)
  - [ ] `sanitize_string` does not alter strings containing no `<`
  - [ ] `sanitize_string` handles `None` without raising
  - [ ] `sanitize_string` handles empty string without raising
  - [ ] `truncate_string` truncates a string longer than max_length and appends suffix
  - [ ] `truncate_string` does not alter a string shorter than max_length
  - [ ] `truncate_string` does not alter a string exactly at max_length
  - [ ] `truncate_string` handles `None` without raising
  - [ ] `truncate_string` handles empty string without raising

---

## Phase 2: Apply sanitization to search.py

- [ ] Import `sanitize_string` and `truncate_string` from `output_sanitizer` in `search.py`
- [ ] In `_extract_issue()`, apply `sanitize_string` then `truncate_string(200)` to `summary`
- [ ] Change `max_results` default from `50` to `20` in `search_jira_issues`
- [ ] Confirm `list_project_tickets` inherits the new default (it delegates to `search_jira_issues`)

---

## Phase 3: Apply sanitization to issues.py

- [ ] Import `sanitize_string` from `output_sanitizer` in `issues.py`
- [ ] In `get_issue_details()`, apply `sanitize_string` to `summary` and `description`
- [ ] In `get_full_issue_details()`:
  - [ ] Apply `sanitize_string` to `summary`
  - [ ] Apply `sanitize_string` to `description`
  - [ ] Apply `sanitize_string` to each comment `body` in the comments list
  - [ ] Apply `sanitize_string` to each link `summary` in the links list

---

## Phase 4: Apply sanitization to confluence.py

- [ ] Import `sanitize_string` from `output_sanitizer` in `confluence.py`
- [ ] In `list_confluence_pages()`:
  - [ ] Apply `sanitize_string` to each page `title`
  - [ ] Change `limit` default from `25` to `20`
- [ ] In `get_confluence_page()`:
  - [ ] Apply `sanitize_string` to `title`
  - [ ] Apply `sanitize_string` to `body`
- [ ] In `search_confluence_pages()`:
  - [ ] Apply `sanitize_string` to each result `title`
  - [ ] Change `limit` default from `25` to `20`

---

## Phase 5: Verification

- [ ] Run existing test suite -- all tests pass with no modifications to test assertions
  ```
  pytest tests/ -v
  ```
- [ ] Manual integration check: call `search_jira_issues` against a project where at least one
  ticket description contains angle brackets -- confirm no `<` appears in any string field of
  the response
- [ ] Manual integration check: call `get_full_issue_details` on a ticket with angle brackets
  in the description -- confirm full content is returned (no truncation) and `<` is escaped
- [ ] Manual integration check: call `get_confluence_page` on a page with HTML markup in the
  body -- confirm body is returned with `<` escaped to `&lt;`
- [ ] Confirm `list_project_tickets` with no explicit `max_results` returns at most 20 results
- [ ] Confirm `search_jira_issues` with explicit `max_results=50` still returns up to 50 results

---

## Phase 6: Documentation

- [ ] Update `docs/user/cline-compatibility.md` -- add section:
  - Protocol delimiter collision risk (what triggers it, why it is intermittent)
  - Sanitization protection in place (what is covered, what is not)
  - Confluence body entity-escaping limitation
- [ ] Update `servers/jira-helper/docs/developer/adding-features.md` -- add guidance:
  - New tools returning user-authored content must import and call `sanitize_string()`
  - Structural metadata fields do not require sanitization
  - Reference the field classification table in `architecture/cline-safe-output.md`

---

## Definition of Done

- [ ] All checklist items above are marked complete
- [ ] Existing test suite passes without modification
- [ ] New unit tests in `test_output_sanitizer.py` all pass
- [ ] Manual integration checks completed against a real Jira instance
- [ ] Documentation updates committed in the same PR as the code changes
- [ ] Changelog entry added documenting the max_results default change as a behavior change