---
title: Write Capability for WorkBoard CLI - Plan
date: 2026-09-06
type: feat
topic: write-capability
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

# Write Capability for WorkBoard CLI - Plan

## Goal Capsule

- **Objective:** Users can create and update work items in the SharePoint WorkBoard list through the CLI and agent interface, with field validation, read-only field protection, and full parity with the existing normalized schema.
- **Means:** Extend the existing read-only CLI with write methods in the Graph client, a dedicated write-preparation module, new `items create` and `items update` commands, and corresponding agent intents. Auth scope extends to `Sites.ReadWrite.All`. (KTD1, KTD2, KTD3, KTD4, KTD5)
- **Authority hierarchy:** This plan owns the write-surface requirements and implementation units. Existing read behavior is unchanged. The SharePoint list remains the sole source of truth.
- **Stop conditions:** All implementation units complete, tests pass, documentation updated, and `ruff check .` clean.

---

## Product Contract

### Summary

Add `workboard items create` and `workboard items update` commands that write fields to the SharePoint WorkBoard list via Microsoft Graph API. Expose all normalized schema fields (except read-only system fields) through both CLI flags and agent intents. Validate inputs before write. Fail on update with no fields specified.

### Problem Frame

The CLI is read-only today (`Sites.Read.All`). Users and agents cannot create or update work items without opening SharePoint directly. This limits automation and forces context-switching for routine work tracking.

Adding write capability closes the loop: query, create, and update all from the terminal or agent interface.

### Requirements

**Write Surface**

- R1. The CLI provides `workboard items create` with `--title` required and all normalized-schema fields as optional flags.
- R2. The CLI provides `workboard items update <item_id>` with all normalized-schema fields as optional flags. The command fails with an error if no field flags are provided.
- R3. `date_closed` is available only on `items update`, not on `items create`.
- R4. Both commands return the standard JSON envelope with the created or updated item.
- R5. Both commands accept `--list` (default: WorkBoard) and `--format` (default: json) options.

**Validation**

- R6. `title` is required for create; the command fails with an actionable error when missing.
- R7. Date fields (`date_due`, `date_start`, `date_committed`, `date_closed`) validate YYYY-MM-DD format.
- R8. `stage` values are validated against the configured stage aliases.
- R9. Read-only fields (`ID`, `Created`, `Modified`, `Author`, `Editor`, `CycleTime`) are silently skipped when provided.

**Auth and Permissions**

- R10. Auth scope extends from `Sites.Read.All` to `Sites.ReadWrite.All`. Existing tokens with only read scope fall through to device-flow re-authentication.
- R11. Error handling for 403 (permission denied) provides an actionable message pointing to admin-granted write access.

**Agent Interface**

- R12. `create_item` agent intent requires `--title` and accepts optional field params.
- R13. `update_item` agent intent requires `--item-id` and at least one field param.

**Non-goals**

- R14. Delete capability is out of scope.
- R15. Confirmation prompts before write are out of scope; writes are immediate.
- R16. Azure AD `Sites.Selected` site-scoping is an admin task, not a CLI concern.
- R17. `workboard config validate` verifies that all mapped fields are writable in the target SharePoint list, not just present.
- R18. Write operations are logged locally to `~/.config/workboard/write_log.jsonl` with timestamp, command, item_id, and changed fields for audit trail.

### Success Criteria

- A user can run `workboard items create --title "Test Item" --stage "Open"` and see the created item in the JSON envelope.
- A user can run `workboard items update 42 --stage "In Progress"` and see the updated item.
- `workboard items update 42` (no fields) returns an error with an actionable message.
- `workboard agent query --intent create_item --title "Agent Item"` creates an item.
- All existing read commands continue to work unchanged.
- `ruff check .` and `pytest` pass clean.

### Scope Boundaries

- **In scope:** Auth scope change, Graph client write methods, field preparation with validation, CLI create/update commands, agent intents, tests, documentation.
- **Deferred to follow-up work:** Delete command, bulk create/update, field-level permissions, concurrency control, optimistic locking.

---

## Planning Contract

### Key Technical Decisions

- KTD1. **Auth scope: `Sites.ReadWrite.All`** (session-settled: user-directed - chosen over `Sites.Selected` site-scoping: site lockdown is an admin config, not a CLI concern). Scope blast radius: `Sites.ReadWrite.All` grants write access to every SharePoint list the authenticated user can reach, not only WorkBoard. Operators needing tighter scoping should use Azure AD conditional access or `Sites.Selected`. Existing MSAL token cache handles scope increase: when cached token has only read scope, silent acquisition fails and the CLI falls back to device flow re-authentication.
- KTD2. **Field preparation in a dedicated `write.py` module** (session-settled: user-directed - chosen over extending `normalize.py`: keeps read/write concerns separate). The existing `config["fields"]` mapping already maps normalized names to SharePoint internal names, so the write module reverses this mapping without duplicating config.
- KTD3. **Fail on update with no fields** (session-settled: user-directed - chosen over silent no-op: a no-op is misleading when the user thinks they changed something). The command returns a `WorkboardError` with an actionable message.
- KTD4. **All normalized-schema fields exposed on create and update** (session-settled: user-directed - chosen over minimal subset: full parity with the read schema). Read-only fields are silently skipped rather than erroring, so agents can pass the full item dict without filtering.
- KTD5. **No confirmation prompts** (session-settled: user-directed - chosen over confirmation flow: matches the agent-friendly JSON output pattern). Writes are immediate, consistent with the existing CLI behavior for read commands.

### Assumptions

- The SharePoint list schema supports the fields being written (verified by `workboard config validate` against the exported schema, per R17).
- The Azure AD app registration permits the `Sites.ReadWrite.All` scope (admin-side configuration).
- Users re-authenticate after the scope change (MSAL handles this via device flow fallthrough).
- The existing `config["fields"]` mapping is correct and complete for write operations.

### Sequencing

1. Auth scope change (U1) - foundational, no dependencies
2. GraphClient write methods (U2) - foundational, no dependencies
3. SharePoint write helpers (U3) - depends on U2
4. Write module (U4) - depends on existing config/normalize patterns, logically precedes U5 (which consumes its output)
5. CLI commands (U5) - depends on U1, U2, U3, U4
6. Agent intents (U6) - depends on U5
7. Tests (U7) - depends on U2, U3, U4, U5, U6
8. Documentation (U8) - depends on U5, U6

U1 and U2 are independent and can be parallelized. U3, U4, U5, U6 are sequential. U7 and U8 can run after their dependencies.

---

## Implementation Units

### U1. Auth Scope Extension

- **Goal:** Change the MSAL auth scope from `Sites.Read.All` to `Sites.ReadWrite.All` so the CLI can write to SharePoint lists.
- **Dependencies:** None.
- **Files:** `src/workboard_cli/auth.py`
- **Approach:**
  1. Replace `Sites.Read.All` with `Sites.ReadWrite.All` in `get_token()` silent acquisition scope.
  2. Replace `Sites.Read.All` with `Sites.ReadWrite.All` in `get_token()` device flow initiation scope.
  3. Replace `Sites.Read.All` with `Sites.ReadWrite.All` in `check_auth()` silent acquisition scope.
  4. MSAL handles scope upgrade: when the cached token has only read scope, silent acquisition fails and the device flow runs to get the new scope. After replacing scopes, add a fallback: if `get_token()` (non-force) returns a token, verify it carries write scope before returning; if not, force device flow re-authentication. This catches cases where MSAL serves a stale read-only token from cache.
- **Patterns to follow:** Existing scope references in `src/workboard_cli/auth.py:52,59,89,95`.
- **Test scenarios:**
  - `get_token` requests `Sites.ReadWrite.All` scope in device flow.
  - `check_auth` uses `Sites.ReadWrite.All` in silent acquisition.
  - When cached token has only `Sites.Read.All`, `get_token(force=True)` initiates device flow (does not reuse stale token).
- **Verification:** `grep -n "Sites.Read" src/workboard_cli/auth.py` shows only `Sites.ReadWrite.All`.

### U2. GraphClient Write Methods

- **Goal:** Add `post()`, `patch()`, and `delete()` methods to `GraphClient` for creating, updating, and deleting SharePoint list items.
- **Dependencies:** None.
- **Files:** `src/workboard_cli/graph_client.py`, `tests/test_graph_client.py`
- **Approach:**
  1. Add `post(path, json=None)` - sends POST with `Content-Type: application/json`, returns `resp.json()`.
  2. Add `patch(path, json=None)` - sends PATCH with `Content-Type: application/json`, returns `resp.json()`.
  3. Add `delete(path)` - sends DELETE, returns `None` on 204 success.
  4. All three use the same retry-on-429 loop (3 attempts, linear backoff) and `_handle_response()` error handling as `get()`. Extract the retry loop into a shared `_request_with_retry(method, path, json=None)` helper to avoid duplicating the pattern across `get()`, `post()`, `patch()`, and `delete()`.
  5. Add `Content-Type: application/json` to the session headers in `__init__` so POST/PATCH don't need per-call header setup.
  6. Update `_handle_response()` for 403 errors: when called from write methods, the message should say "Ask an administrator to grant write access" instead of "read access". Pass an optional `is_write=False` parameter to `_handle_response()` from `post()`/`patch()`/`delete()` to select the correct hint.
- **Patterns to follow:** Existing `get()` method retry/error pattern in `src/workboard_cli/graph_client.py:42-66`.
- **Test scenarios:**
  - `post` sends JSON body and returns parsed response.
  - `patch` sends JSON body and returns parsed response.
  - `delete` returns None on 204.
  - All three retry on 429 with backoff.
  - All three translate 401/403/404/429/5xx to `WorkboardError`.
- **Verification:** `pytest tests/test_graph_client.py` passes.

### U3. SharePoint Write Helpers

- **Goal:** Add `create_list_item()` and `update_list_item()` functions to the sharepoint module for Graph API list-item mutations.
- **Dependencies:** U2.
- **Files:** `src/workboard_cli/sharepoint.py`
- **Approach:**
  1. Add `create_list_item(client, site_id, list_id, fields)` - POST to `/sites/{site_id}/lists/{list_id}/items` with `{"fields": fields}` body. Returns created item.
  2. Add `update_list_item(client, site_id, list_id, item_id, fields)` - PATCH to `/sites/{site_id}/lists/{list_id}/items/{item_id}` with `{"fields": fields}` body. Returns updated item.
  3. Both are thin wrappers over the Graph client's new `post()` and `patch()` methods, following the same pattern as `get_list_item()`.
- **Patterns to follow:** Existing `get_list_item()` function in `src/workboard_cli/sharepoint.py:43-50`.
- **Test scenarios:**
  - `create_list_item` POSTs to correct path with fields body.
  - `update_list_item` PATCHes to correct path with item ID and fields body.
- **Verification:** `pytest tests/test_sharepoint.py` passes.

### U4. Write Module - Field Preparation

- **Goal:** Provide `prepare_fields_for_write()` that maps user input to SharePoint field names, validates inputs, and skips read-only fields.
- **Dependencies:** None (requires config schema stability - field mapping and stage aliases).
- **Files:** `src/workboard_cli/write.py`, `tests/test_write.py`
- **Approach:**
  1. Define `READ_ONLY_FIELDS` set: `{"ID", "Created", "Modified", "Author", "Editor", "CycleTime"}`.
  2. Define `DATE_FIELDS` set: `{"date_due", "date_start", "date_committed", "date_closed"}`.
  3. `prepare_fields_for_write(input_fields, config)`:
     a. Strip read-only fields silently (no warning).
     b. Validate `title` is present for create (raise `WorkboardError` if missing).
     c. Map each normalized name to SharePoint internal name via `config["fields"]`.
     d. Validate date fields against YYYY-MM-DD regex.
     e. Validate `stage` against combined stage aliases from `config["stage_aliases"]`.
     f. Strip control characters (`\x00-\x1f` except `\t\n\r`) from free-text field values as defense-in-depth.
     g. Return `(sharepoint_fields_dict, warnings_list)`.
  4. Date validation uses `re.fullmatch(r'\d{4}-\d{2}-\d{2}', value)` for date-only fields, matching the existing `_parse_date` pattern.
  5. Stage validation collects all alias values from all categories and checks membership.
- **Patterns to follow:** Existing field mapping in `config/workboard.defaults.yaml:15-41`, date validation in `src/workboard_cli/normalize.py:35-52`, stage alias lookup in `src/workboard_cli/normalize.py:128-135`.
- **Test scenarios:**
  - Maps `title` to `Title`, `delivery_owner` to `DeliveryOwner`, etc.
  - Skips `ID`, `Created`, `Modified`, `Author`, `Editor`, `CycleTime` silently.
  - Raises error when `title` missing on create.
  - Validates date format `2026-01-15` passes, `not-a-date` fails.
  - Validates stage "Open" passes, "InvalidStage" fails.
  - Returns warnings for unmapped fields.
  - Empty input (after read-only stripping) returns empty dict for update.
- **Verification:** `pytest tests/test_write.py` passes.

### U5. CLI Commands - Create and Update

- **Goal:** Add `workboard items create` and `workboard items update` commands with all normalized-schema fields as flags.
- **Dependencies:** U1, U2, U3, U4.
- **Files:** `src/workboard_cli/cli.py`, `tests/test_cli.py`
- **Approach:**
  1. Add `items_create` command to `items_app`:
     - `--title` (required, `typer.Option(...)`).
      - All other fields as optional `typer.Option(None)`: `--stage`, `--delivery-owner`, `--decision-authority`, `--acceptance-authority`, `--why`, `--description`, `--schedule`, `--scope`, `--requirements`, `--acceptance-criteria`, `--deliverables`, `--work-intake`, `--rel-project`, `--rel-work-brief`, `--who`, `--date-due`, `--date-start`, `--date-committed`, `--priority-status`, `--color-tag`.
     - `--list` (default "WorkBoard"), `--format` (default "json").
     - Flow: resolve site/list -> build input dict from non-None options -> `prepare_fields_for_write(input, config, require_title=True)` -> `create_list_item()` -> return envelope with created item.
  2. Add `items_update` command to `items_app`:
     - `item_id` as `typer.Argument(...)`.
     - Same optional fields as create, plus `--date-closed`.
     - Fails if no field flags provided (after `--list` and `--format` are excluded).
     - Flow: resolve site/list -> build input dict -> `prepare_fields_for_write(input, config, require_title=False)` -> check non-empty -> `update_list_item()` -> return envelope with updated item.
   3. Both follow the existing `_get_client()` / `_fetch_items()` / `_error_exit()` patterns.
   4. After successful create/update, append a JSON line to `~/.config/workboard/write_log.jsonl` with `{"timestamp": "<ISO>", "command": "create"|"update", "item_id": "<id>", "fields": [<changed field names>], "list": "<list_name>"}`.
   5. The command help text states: "Create a new work item" and "Update an existing work item".
- **Patterns to follow:** Existing `items_get` command structure in `src/workboard_cli/cli.py:245-280`, `_get_client()` helper in `src/workboard_cli/cli.py:119-122`.
- **Test scenarios:**
  - `items create --title "Test"` succeeds and returns created item in envelope.
  - `items create` (no title) fails with actionable error.
  - `items update 42 --stage "In Progress"` succeeds and returns updated item.
  - `items update 42` (no fields) fails with "provide at least one field" error.
  - `items update 999` with non-existent ID returns 404 error.
  - `items create --date-due "bad-date"` fails with date validation error.
  - `items create --stage "InvalidStage"` fails with stage validation error.
  - Both commands use `--list` and `--format` options correctly.
- **Verification:** `pytest tests/test_cli.py` passes. Manual: `workboard items create --title "Plan Test" --help`.

### U6. Agent Intents - Create and Update

- **Goal:** Add `create_item` and `update_item` to the approved agent intents with appropriate parameter validation.
- **Dependencies:** U5.
- **Files:** `src/workboard_cli/agent.py`, `tests/test_agent.py`
- **Approach:**
  1. Add `"create_item"` and `"update_item"` to `APPROVED_INTENTS` set.
  2. In `execute_intent()`, add validation:
     - `create_item` requires `params["title"]` - raise `WorkboardError` if missing.
     - `update_item` requires `params["item_id"]` and at least one other field param.
  3. Write intents require a Graph client and site/list context, unlike read intents which operate on pre-fetched items. Refactor `execute_intent()` to accept an optional `client` and `config` parameter for write intents; read intents continue using `raw_items` as before. Alternatively, handle write intents directly in the `agent_query` CLI command before calling `execute_intent()`, bypassing the read-intake path entirely.
  4. For `update_item`, skip the `_fetch_items()` call in `agent_query` and resolve the site/list directly (same pattern as `items_update`), then call the shared write logic.
  5. Return the standard JSON envelope with the created/updated item, matching the CLI command output shape.
- **Patterns to follow:** Existing intent validation in `src/workboard_cli/agent.py:27-70`, parameter passing in `src/workboard_cli/cli.py:406-430`.
- **Test scenarios:**
  - `create_item` with `--title` creates item and returns envelope.
  - `create_item` without `--title` raises validation error.
  - `update_item` with `--item-id` and `--stage` updates item.
  - `update_item` without `--item-id` raises validation error.
  - `update_item` with only `--item-id` (no fields) raises validation error.
- **Verification:** `pytest tests/test_agent.py` passes.

### U7. Tests

- **Goal:** Comprehensive test coverage for all write functionality using mock-based tests.
- **Dependencies:** U2, U3, U4, U5, U6.
- **Files:** `tests/test_write.py` (new), `tests/test_graph_client.py` (extend), `tests/test_sharepoint.py` (extend), `tests/test_cli.py` (extend), `tests/test_agent.py` (extend)
- **Approach:**
  1. New `tests/test_write.py` covering `prepare_fields_for_write()`:
     - Field mapping correctness.
     - Read-only field stripping.
     - Required title validation.
     - Date format validation.
     - Stage alias validation.
     - Empty input handling.
  2. Extend `tests/test_graph_client.py` with `responses` mocks for POST, PATCH, DELETE.
  3. Extend `tests/test_sharepoint.py` with create/update helper tests.
  4. Extend `tests/test_cli.py` with Typer test runner for `items create` and `items update`.
  5. Extend `tests/test_agent.py` with intent validation for new intents.
- **Test scenarios:** Covered in each unit above.
- **Verification:** `pytest` passes clean. `ruff check .` passes.

### U8. Documentation Updates

- **Goal:** Update documentation to reflect new write capability, auth scope change, and agent intents.
- **Dependencies:** U5, U6.
- **Files:** `readme.md`, `docs/security_model.md`, `docs/agent_usage.md`
- **Approach:**
  1. `readme.md`: Add `items create` and `items update` to the Commands section. Update the agent install prompt to mention write capability. Update the scope note from `Sites.Read.All` to `Sites.ReadWrite.All`.
  2. `docs/security_model.md`: Update scope to `Sites.ReadWrite.All`. Revise the Agent safety section: remove the "write-back is blocked" statement, document that write intents (`create_item`, `update_item`) are now approved, and specify scope blast radius (all accessible lists, not just WorkBoard). Note that re-authentication is required after upgrade. This is a blocking gate in U8 - the security model must be updated before or alongside write-intent implementation.
  3. `docs/agent_usage.md`: Document `create_item` and `update_item` intents with parameter requirements and examples.
- **Patterns to follow:** Existing command documentation in `readme.md:47-68`, security model in `docs/security_model.md:1-25`.
- **Test expectation: none** - documentation changes, no behavioral tests.

---

## Verification Contract

| Gate | Command | Pass condition |
|---|---|---|
| Lint | `ruff check .` | Clean, no errors |
| Unit tests | `pytest` | All pass |
| Type check | N/A (not configured) | - |
| Manual smoke | `workboard items create --title "Smoke Test" --stage "Open"` | Returns JSON envelope with created item |
| Manual smoke | `workboard items update <id> --stage "In Progress"` | Returns JSON envelope with updated item |
| Manual smoke | `workboard items update <id>` | Fails with actionable error |
| Read regression | `workboard items list --limit 3` | Existing read commands unchanged |

---

## Definition of Done

- All implementation units (U1-U8) complete.
- `ruff check .` passes with no errors.
- `pytest` passes with all tests green.
- `workboard items create --title "Test" --stage "Open"` produces a valid created item.
- `workboard items update <id> --stage "Done"` produces a valid updated item.
- `workboard items update <id>` (no fields) fails with actionable error.
- `workboard agent query --intent create_item --title "Agent Test"` creates an item.
- All existing read commands work unchanged.
- Documentation reflects the new commands and scope change.
