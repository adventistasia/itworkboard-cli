---
title: "feat: Embed default tenant ID and client ID in CLI"
date: 2026-08-20
type: feat
topic: embed-default-credentials
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-plan-bootstrap
execution: code
---

# Embed Default Tenant ID and Client ID in CLI

## Goal Capsule

- **Objective:** Ship the CLI with default `tenant_id` and `client_id` values baked into the committed defaults config, so users can run commands without any config setup or environment variables.
- **Origin:** GitHub Issue [#12](https://github.com/adventistasia/itworkboard-cli/issues/12).
- **Execution profile:** Configuration change + documentation update. No code logic changes needed — the existing config loading chain already supports this.

## Problem Frame

Today, every new user must either:
1. Copy `config/workboard.example.yaml` to `config/local.yaml` and fill in tenant/client IDs, or
2. Set `WORKBOARD_TENANT_ID` and `WORKBOARD_CLIENT_ID` environment variables

before the CLI works. The tenant and app registration are fixed for our team — these are identifiers (not secrets), and requiring manual entry adds onboarding friction with no security benefit.

## Scope

**In scope:**
- Add default `tenant_id` and `client_id` to `config/workboard.defaults.yaml`
- Update README.md setup instructions and agent install prompt
- Add tests verifying defaults work and overrides still take precedence

**Out of scope (deferred to Issue #11):**
- `workboard config set` CLI command for setting tenant/client IDs interactively
- Any code changes to `config.py` — the existing loading chain already handles defaults-to-overlay-to-env-var precedence

## Config Loading Chain (existing, no changes needed)

```
config/workboard.defaults.yaml  (committed — WHERE defaults go)
        ↓ deep merge
config/local.yaml               (gitignored — user overrides)
        ↓ env var override
WORKBOARD_TENANT_ID / WORKBOARD_CLIENT_ID
        ↓ validation
error if still missing
```

Adding `tenant_id` and `client_id` to the defaults file means the chain produces valid credentials without step 2 or 3. Local overrides and env vars continue to take precedence per the existing `_deep_merge` and `os.environ.get` logic.

## Implementation Units

### U1. Add default credentials to `config/workboard.defaults.yaml`

**Goal:** The committed defaults file contains real `tenant_id` and `client_id` values so the CLI works out of the box.

**Files:**
- `config/workboard.defaults.yaml` (modify)

**Approach:**
- Add `tenant_id` and `client_id` keys to `config/workboard.defaults.yaml`, at the top of the file alongside `site_url` and `primary_list_name` (which are already defaults)
- Use the same values currently in `config/local.yaml` (these are the team's fixed Azure AD identifiers)
- Add a comment noting these are team defaults and can be overridden via `config/local.yaml` or env vars

**Test scenarios:**
- `load_config()` with no `local.yaml` and no env vars returns `tenant_id` and `client_id` from defaults (no `config_error` raised)
- `load_config()` with `local.yaml` present returns the local values, not the defaults (override precedence)
- `load_config()` with env vars set returns the env var values, not defaults (env var precedence)

**Verification:** `pytest tests/` green; manual: delete/rename `config/local.yaml`, run `workboard auth status` — should not fail with `config_error` (will fail at auth step, not config load).

---

### U2. Update README.md setup instructions and agent install prompt

**Goal:** Documentation reflects that the CLI works out of the box without manual config.

**Files:**
- `README.md` (modify)

**Approach:**
- Simplify the **Setup** section: remove the manual copy-and-fill step. Replace with: "The CLI ships with default credentials. Just authenticate: `workboard auth login`"
- Update the **Agent install prompt** section: remove the steps about copying example config and asking for tenant/client IDs. The agent can skip straight to `workboard auth login`
- Add a note that users can override defaults via `config/local.yaml` or env vars if needed

**Test expectation: none — documentation only.**

---

### U3. Add config-loading tests

**Goal:** Automated tests verify that defaults work, local overrides take precedence, and env vars take highest precedence.

**Files:**
- `tests/test_config.py` (create)

**Approach:**
- Create `tests/test_config.py` with tests for the `load_config` function
- Test the three-tier precedence: defaults → local overlay → env vars
- Test the error path: no defaults file raises `config_error`
- Test the missing-credentials path: defaults without tenant_id/client_id raises `config_error` (this is the current behavior — ensures we don't accidentally remove the validation)

**Test scenarios:**
- `load_config()` with defaults only (no local, no env) → returns `tenant_id` and `client_id` from defaults
- `load_config()` with local.yaml overlay → returns local values (deep merge works)
- `load_config()` with env vars → returns env var values (highest precedence)
- `load_config()` with local.yaml pointing to a nonexistent file → falls through to defaults
- `load_config()` with defaults file missing → raises `WorkboardError("config_error", ...)`
- `load_config()` with defaults having empty tenant_id → raises `WorkboardError("config_error", ...)` (validation still fires)

**Verification:** `pytest tests/test_config.py` green; full suite `pytest` still passes.

## Verification Contract

- `pytest` passes all tests (existing + new)
- `ruff check .` exits 0
- `workboard auth status` (with no `local.yaml`, no env vars) loads config without `config_error`
- `workboard auth login` (with no `local.yaml`) proceeds to device flow using default credentials

## Definition of Done

1. `config/workboard.defaults.yaml` contains `tenant_id` and `client_id` with real team values
2. CLI works without `config/local.yaml` or environment variables for config loading
3. `config/local.yaml` and env vars still override defaults
4. README.md reflects simplified setup
5. Tests verify three-tier config precedence
6. No code changes to `config.py` — existing loading chain handles it
7. `ruff check .` clean
8. `pytest` green (all 170 existing + new tests)
