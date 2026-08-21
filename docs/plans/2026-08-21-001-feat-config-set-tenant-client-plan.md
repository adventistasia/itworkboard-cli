---
title: "feat: Add config set command for tenant ID and client ID"
date: 2026-08-21
type: feat
topic: config-set-tenant-client
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

# Add `workboard config set` Command for Tenant ID and Client ID

## Goal Capsule

- **Objective:** Add a `workboard config set` CLI command that writes `tenant_id` and/or `client_id` into `config/local.yaml`, so users never hand-edit YAML.
- **Origin:** GitHub Issue [#11](https://github.com/adventistasia/itworkboard-cli/issues/11).
- **Execution profile:** Small bounded feature. Single Typer command + one config-module helper + tests. Complements the Issue #12 defaults (this command is the override path).

## Problem Frame

Onboarding currently requires copying `config/local.example.yaml` to `config/local.yaml` and hand-editing GUIDs — wrong path and YAML syntax errors are common. Even though Issue #12 baked team defaults into `config/workboard.defaults.yaml`, users still need a supported way to override tenant/client IDs (their own test tenant, a different app registration). A CLI command removes the file-editing step entirely.

## Scope

**In scope:**
- `workboard config set --tenant-id <guid> [--client-id <guid>]` (at least one flag required)
- Create `config/local.yaml` (and `config/` dir) if missing
- Update only the given keys; preserve all other settings in the file
- Strict GUID-format validation before any write
- Plain-text confirmation after success
- Tests for validation, create, update, and preserve-other-keys

**Out of scope:**
- Setting env vars, site URL, list name, or other config keys (future work; command shape is extensible)
- Two-subcommand variant (`set-tenant` / `set-client`) — single command with flags satisfies the acceptance criteria
- Any change to the config loading chain in `src/workboard_cli/config.py` — precedence (defaults → local → env) stays as-is

## Requirements (from Issue #11 acceptance criteria)

| ID | Requirement |
|---|---|
| R1 | `workboard config set` accepts `--tenant-id` and/or `--client-id` flags |
| R2 | Creates `config/local.yaml` if missing |
| R3 | Updates existing values without overwriting other config |
| R4 | Validates input is a valid GUID format before writing |
| R5 | Prints confirmation message after success |
| R6 | Tests added |

## Implementation Units

### U1. Add `update_local_config()` + GUID validator to `src/workboard_cli/config.py`

**Goal:** A testable module-level function owns all local-file read/modify/write logic; the CLI command stays thin.

**Files:**
- `src/workboard_cli/config.py` (modify)
- `tests/test_config.py` (modify)

**Approach:**
- Add module-level `GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")` and `def is_valid_guid(value: str) -> bool`.
- Add `def update_local_config(overrides: dict, path: Path | None = None) -> Path`:
  - Resolve target path: explicit `path` arg if given, else `LOCAL_PATHS[0]` (`config/local.yaml`).
  - Validate every value in `overrides` with `is_valid_guid`; raise `WorkboardError("config_error", ..., action=...)` naming the offending key on failure.
  - `data = yaml.safe_load(file) or {}` if the file exists, else `{}`.
  - `data.update(overrides)` — preserves all other keys.
  - `path.parent.mkdir(parents=True, exist_ok=True)`; write with `yaml.safe_dump(data, sort_keys=False, default_flow_style=False)`.
  - Return the resolved `Path` for the confirmation message.
- No change to `load_config()` or `_deep_merge`.

**Test scenarios (tests/test_config.py):**
- `is_valid_guid` accepts canonical hyphenated GUIDs, both upper- and lower-case hex.
- `is_valid_guid` rejects: wrong segment lengths, missing dashes, non-hex characters, braces, `uuid.UUID`-style compact forms (e.g. 32 hex chars without dashes), empty string, None.
- `update_local_config` creates the file (incl. parent dir) when missing — file exists after call, contains only the override key(s).
- `update_local_config` updates one key and preserves others when the file exists (load-update-dump round-trip).
- `update_local_config` with both keys updates both.
- `update_local_config` raises `WorkboardError` with code `config_error` for an invalid GUID, and the file is NOT written.
- Written YAML round-trips: `yaml.safe_load` of the result equals the expected dict.
- Explicit `path` argument overrides `LOCAL_PATHS[0]`.

**Verification:** `pytest tests/test_config.py` green.

---

### U2. Add `config set` command to `src/workboard_cli/cli.py`

**Goal:** `workboard config set` command wired into the existing `config_app` Typer app, following the `config validate` command's error pattern.

**Files:**
- `src/workboard_cli/cli.py` (modify)
- `tests/test_cli.py` (modify)

**Approach:**
- `@config_app.command("set")` with `tenant_id: str | None = typer.Option(None, "--tenant-id", ...)` and `client_id: str | None = typer.Option(None, "--client-id", ...)`.
- Build `overrides = {}`, add non-None flags.
- If `overrides` is empty: `raise WorkboardError("config_error", "Provide at least one of --tenant-id or --client-id.", "Example: workboard config set --tenant-id 918af52d-8dec-44c4-818a-cebf3c9b7767")`.
- Call `update_local_config(overrides)` (import from `workboard_cli.config`), wrap in the existing `try / except WorkboardError → _error_exit(e)` pattern used by `config_validate`.
- Print plain-text confirmation, e.g. `print(f"Updated {path}")` plus one line naming the keys set; add a hint line that `WORKBOARD_TENANT_ID`/`WORKBOARD_CLIENT_ID` env vars take precedence if set.

**Test scenarios (tests/test_cli.py):**
- `config set --tenant-id <valid>` → exit 0, confirmation contains `config/local.yaml` and `tenant_id`.
- `config set --client-id <valid>` → exit 0, confirmation mentions `client_id`.
- `config set --tenant-id <valid> --client-id <valid>` → exit 0, both set (verify via written file content when LOCAL_PATHS is patched to a tmp path).
- `config set` (no flags) → exit 1, stdout contains `config_error`.
- `config set --tenant-id not-a-guid` → exit 1, stdout contains `config_error` and the offending key name.
- `config set --tenant-id <valid>` writes to the patched `config.LOCAL_PATHS[0]` tmp file; existing other keys in that file survive.
- `config --help` still exits 0 and lists `set`.

**Verification:** `pytest tests/test_cli.py` green; full suite `pytest` green; `ruff check .` exits 0.

---

### U3. Document the command in README.md setup section

**Goal:** Onboarding docs mention the command so new users discover it.

**Files:**
- `README.md` (modify)

**Approach:**
- One short line in the Setup section after the auth instructions: "Override tenant/client IDs with `workboard config set --tenant-id <guid> --client-id <guid>`."

**Test expectation: none — documentation only.**

## Decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Single `config set` command with optional flags, not `set-tenant`/`set-client` subcommands | Matches Issue #11 acceptance criteria; one command is extensible to more keys later; avoids command-name drift |
| D2 | GUID validation by strict regex (canonical hyphenated form, case-insensitive), not `uuid.UUID()` | `uuid.UUID()` accepts non-canonical forms (compact, braces); the issue asks for "valid GUID format" — strict form rejects typos like missing dashes before they hit the file |
| D3 | Write target is `LOCAL_PATHS[0]` (`config/local.yaml`) with parent-dir creation | Issue says "instead of manually editing config/local.yaml"; reuses the existing constant so config location stays in one place |
| D4 | Logic lives in `config.py` (`update_local_config`), CLI command stays thin | YAML I/O is config-module concern; unit-testable without CliRunner (matches how `load_config`/`_deep_merge` are tested in `tests/test_config.py`) |
| D5 | Load-modify-dump with `yaml.safe_dump(sort_keys=False, default_flow_style=False)` | Preserves unknown/other keys and key order; `safe_dump` is the same loader family already used everywhere |
| D6 | Plain-text confirmation (not JSON envelope) | Human-facing config action like `auth login`/`schema export`; GUIDs are team identifiers, not secrets, so echoing them is fine |
| D7 | CLI tests patch `workboard_cli.config.LOCAL_PATHS` to a tmp file | Consistent with existing `tests/test_config.py` patch style; avoids cwd-sensitive relative-path issues in CliRunner |
| D8 | No change to config load precedence | Env vars still win over the file — that is existing documented behavior and must not silently change; confirmation hints at it |

## Verification Contract

- `pytest` passes all tests (existing + new)
- `ruff check .` exits 0
- Manual: `workboard config set --tenant-id 918af52d-8dec-44c4-818a-cebf3c9b7767` → prints confirmation; `config/local.yaml` still contains its other keys
- Manual: `workboard config set --tenant-id nope` → exit 1 with `config_error` and no file write

## Definition of Done

1. `workboard config set` accepts `--tenant-id` and/or `--client-id` (at least one required)
2. Missing `config/local.yaml` (and `config/`) is created on write
3. Existing keys in `config/local.yaml` are preserved
4. Non-GUID input is rejected before any write, with a clear error naming the key
5. Success prints a confirmation naming the file and keys set
6. Tests cover U1 and U2 scenarios above; `pytest` and `ruff check .` green
7. README setup section mentions the command