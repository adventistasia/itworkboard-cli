---
lorespec: "0.1"
id: "2026061802"
date: "2026-06-18"
source: "opencode"
topic: "Full CLI delivery from architecture through implementation, tests, docs, and code review"
tags: [sharepoint, graph-api, msal, typer, python, orchestrator, code-review, architecture, cli]
classification:
  type: technical
  secondary_type: strategy
  domains: [sharepoint-integration, cli-tooling, python-engineering, delivery-governance]
  value: high
trails: [workboard-cli-architecture, workboard-cli-implementation, workboard-cli-code-review]
---

## Session Arc

### Started
User had completed the discovery spike (session 2026061801) and asked to "work on the next task". MEMORY.md showed the orchestrator was at T02 (architecture and contracts).

### Pivots
- **Discovery → architecture**: Shifted from exploring SharePoint schema to designing the module boundaries, error taxonomy, permission model, and data flow before any implementation code.
- **Architecture → implementation**: After A02 audit passed, moved into building the CLI scaffold (T03), auth/Graph client (T04), and SharePoint discovery commands (T05) as a batch.
- **Implementation → normalization/queries/agent**: After A03 audit passed, built the config-driven normalization pipeline, query filters, manager summaries, JSON output envelopes, and the agent intent dispatch layer (T06–T08).
- **Build → test/doc/CI**: After all modules were implemented, created comprehensive unit tests (69 total), GitHub Actions CI workflow, and 8 documentation files covering admin, config, manager, agent, troubleshooting, security, and testing (T09–T10).
- **Delivery → audit → code review**: After A04 final acceptance audit passed (PASS verdict), user loaded the ce-code-review skill. Ran a full project code review that found 8 issues (1 P1, 4 P2, 3 P3), applied 5 fixes, and committed them.

### Ended
Orchestrator delivery complete. All 10 tasks and 4 audits passed. Code review applied 5 fixes (config.py error handling, lazy import fix, URL encoding, verbose wiring, unused variable cleanup). 69 tests pass, ruff clean. Completion report saved at `orchestrator_completion_report.md`.

## ARTIFACTS

### A1 — Architecture and contracts documentation

**Location**: `docs/architecture.md`, `docs/cli_command_contract.md`, `docs/agent_json_contract.md`

Three documents produced before any implementation code:

- **`docs/architecture.md`** — Architecture Decision Record covering: language/runtime (Python 3.11+, Typer), 11 module boundaries with single-responsibility descriptions, data flow from CLI input through normalize→query→output, 8-code error taxonomy (auth_error, permission_denied, resource_not_found, validation_error, unsupported_intent, graph_api_error, config_error, network_error), permission model (Sites.Read.All, device code only, no app-only), logging rules, agent security boundary, and module dependency graph.
- **`docs/cli_command_contract.md`** — 13 CLI commands with shapes, exit codes (0-5), global options, error output format.
- **`docs/agent_json_contract.md`** — Success/error JSON envelopes, WorkItem model with 11 fields, 6 approved agent intents, refusal rules, manager summary envelope shape.

**Evolution**: Contracts existed as brief `contracts/` files from earlier work; docs version refined and expanded with concrete examples.

### A2 — CLI implementation (11 source modules)

**Location**: `src/workboard_cli/` (11 modules)

- **`errors.py`** — `WorkboardError` with code, message, action fields and `to_dict()` serialization.
- **`auth.py`** — MSAL device code flow with in-memory token cache, silent token refresh via `SerializableTokenCache`, `check_auth()`, secret key redaction.
- **`graph_client.py`** — `GraphClient` with exponential backoff on 429, error translation (401→auth_error, 403→permission_denied, 404→resource_not_found, 5xx→graph_api_error), pagination via `@odata.nextLink`.
- **`config.py`** — Two-layer config loading (defaults.yaml + local.yaml) with deep merge, 4 env var overrides (TENANT_ID, CLIENT_ID, SITE_URL, LIST_NAME). After code review: raises `WorkboardError` instead of `ValueError`/`FileNotFoundError`.
- **`sharepoint.py`** — Site resolution, list enumeration, list lookup by display/internal name, column discovery, item retrieval with field expansion.
- **`schema.py`** — Column type detection (9 types) and structured schema export to JSON.
- **`normalize.py`** — Config-driven `normalize_item()` maps raw SharePoint fields → WorkItem dict with: stage category derivation from aliases, date-only string preservation, person field parsing (dict/string/none), source URL construction, warning collection for missing fields.
- **`queries.py`** — 5 filter functions: `filter_open`, `filter_overdue`, `filter_blocked`, `filter_by_owner` (case-insensitive substring on displayName or email), `filter_recently_updated`.
- **`summaries.py`** — `build_summary()` with counts by stage category and owner, overdue/blocked counts. `render_markdown_summary()` produces a formatted markdown report.
- **`output.py`** — 3 envelope builders (`build_envelope`, `build_summary_envelope`, `build_error_envelope`) matching the agent JSON contract (status, intent, source, retrievedAt, filters, result, warnings, errors).
- **`agent.py`** — Intent validation against 6 approved intents, parameter requirement checks, intent dispatch to query functions or summary builder.
- **`cli.py`** — 9 Typer command groups (auth, site, lists, schema, items, query, summary, agent, config), 15+ commands, agent intent validation before any Graph call (moved per code review finding), `--normalize` flag on items list, `--verbose` logging (wired per code review finding).

### A3 — Test suite (69 tests)

**Location**: `tests/` (14 test files)

- 55 unit tests across: agent dispatch (7), CLI smoke tests (13), errors (3), graph client with mocked HTTP (6), normalize (9), output envelopes (6), queries (9), schema column types (5), sharepoint helpers (4), summaries (3), auth check (1)
- 14 CLI smoke tests (help output, version, unsupported intent refusal, unauthenticated status)
- All mock-based — no live SharePoint credentials required
- Uses `responses` library for HTTP mocking

### A4 — Documentation (8 files)

**Location**: `README.md` + `docs/`

| File | Purpose |
|------|---------|
| `README.md` | Quick start, setup, command list, development |
| `docs/admin_permissions.md` | Azure AD app registration, Sites.Read.All, admin checklist |
| `docs/configuration.md` | Config file structure, field mapping, stage aliases, schema validation workflow |
| `docs/manager_usage.md` | Daily summary, common queries, JSON output |
| `docs/agent_usage.md` | 6 approved intents, output format, restrictions, orchestrator integration |
| `docs/troubleshooting.md` | Missing credentials, auth fails, resource not found, rate limits |
| `docs/security_model.md` | Auth flow, least privilege, data protection, agent safety |
| `docs/testing.md` | Test structure, running tests, CI, linting |

### A5 — CI workflow

**Location**: `.github/workflows/ci.yml`

GitHub Actions workflow: install → ruff check → pytest, runs on push/PR to main across Python 3.11/3.12/3.13.

### A6 — Orchestrator completion report

**Location**: `orchestrator_completion_report.md`

Final delivery report with: install/config instructions, supported commands table, test results, audit results (A01–A04 all PASS), known limitations, human actions still required (Azure AD app registration, admin consent, local.yaml setup), and v2 recommendations (token persistence, app-only auth, field suggestion, live tests, long-running agent server).

### A7 — Code review applied fixes

**Location**: 5 files modified during code review Stage 5c

| Fix | File | Before | After |
|-----|------|--------|-------|
| Error type consistency | `config.py` | `ValueError`/`FileNotFoundError` for missing config | `WorkboardError("config_error", ...)` |
| Import hygiene | `cli.py` | Lazy `from workboard_cli.agent import validate_intent` inside function | Module-level import |
| URL safety | `normalize.py` | `f"Lists/{list_name}/DispForm.aspx"` | `f"Lists/{list_name.replace(' ', '%20')}/..."` |
| Verbose wiring | `cli.py` | `verbose` parameter accepted but ignored | `logging.basicConfig(level=logging.INFO)` |
| Dead variable | `summaries.py` | `total = len(items)` then unused | Removed, `len(items)` inline |

## DECISIONS

### D1 — Module boundaries match AGENTS.md layout

- **Decision**: 11 modules following the AGENTS.md spec exactly (cli.py, auth.py, graph_client.py, sharepoint.py, schema.py, normalize.py, queries.py, summaries.py, output.py, config.py, errors.py).
- **Issue**: Whether to consolidate or split modules differently.
- **Positions**: 1) Follow the spec, 2) Merge smaller modules (e.g., output into queries), 3) Split further (e.g., separate CLI from command routing).
- **Arguments**: Following the spec reduces cognitive load for future builders (the spec is the source of truth). Each module has a single responsibility and clear dependency direction.
- **Warrant**: Consistent module boundaries let multiple builders work independently without merge conflicts or unexpected coupling.
- **Qualifier**: always
- **Status**: settled

### D2 — Agent intent validation before Graph calls

- **Decision**: `agent query` validates the intent against the approved list BEFORE any authentication or Graph API call.
- **Issue**: Should the CLI attempt auth/Graph calls before or after checking intent validity?
- **Positions**: 1) Validate first (fail fast for bad intents), 2) Auth first (simpler code path).
- **Arguments**: Position 1 won because: (a) unsupported intents are not recoverable, (b) auth failures for bad intents are confusing, (c) this was the root cause of a test timeout during implementation — the original code tried `_get_client()` before checking the intent, causing MSAL device code flow to hang in unit tests.
- **Warrant**: Fast-failing on invalid input is more secure and more testable than attempting expensive operations first.
- **Qualifier**: always
- **Status**: settled

### D3 — Config-driven field normalization instead of hard-coded mapping

- **Decision**: All SharePoint field mapping is driven by `config/workboard.defaults.yaml` (committed), overridable via `config/local.yaml` (gitignored) or env vars.
- **Issue**: Should the CLI discover field names and auto-map them, or rely on human-reviewed config?
- **Positions**: 1) Hard-code discovered field names (simpler), 2) Config-driven with human review (safer), 3) Auto-discover and suggest (best but complex).
- **Arguments**: Position 2 won. The WorkBoard schema has 43 columns — auto-mapping risks silently guessing wrong types. A human reviews the schema export once, validates the config, and the result is stable across runs. The `config validate` command checks field mappings against the live schema.
- **Warrant**: A wrong silent mapping (e.g., mapping a date field to a person field) is worse than requiring a one-time human review.
- **Qualifier**: always
- **Status**: settled

### D4 — No app-only auth in v1

- **Decision**: v1 supports delegated MSAL device code flow only. No app-only (client credentials) flow.
- **Issue**: Should the CLI support unattended/CI-CD auth from the start?
- **Positions**: 1) Delegated only (simpler, safer), 2) Both from v1.
- **Arguments**: Device code flow requires no client secret and no admin consent for the app itself. App-only auth requires a certificate or client secret and broader tenant permissions. Keeping v1 delegated-only reduces the attack surface and simplifies onboarding.
- **Warrant**: You cannot leak credentials you never store.
- **Qualifier**: in this case
- **Status**: settled

### D5 — `by-owner` matching is case-insensitive substring

- **Decision**: Owner queries match on case-insensitive substring of display name OR email.
- **Issue**: How should the CLI match owner names — exact, fuzzy, by email only, by display name only?
- **Positions**: 1) Exact match on display name, 2) Case-insensitive substring on display name OR email (chosen), 3) Regex matching.
- **Arguments**: Position 2 balances usability (a partial name "John" matches "John Doe" and "john@example.com") with predictability. SharePoint person fields can return either a lookup object (with displayName and email) or a string. The current implementation handles both.
- **Warrant**: Users are more likely to type part of a name than an exact string, and different context (email vs display name) shouldn't produce different results.
- **Qualifier**: usually
- **Status**: settled

## INSIGHTS

### I1 — WorkBoard stage values are more granular than standard open/closed/blocked

The SharePoint Stage column has 10 choices: New, Definition, Decision, Committed, Delivery, Closure, Closed, Blocked, Tabled, Canceled. The default stage alias config maps these to three categories (open, closed, blocked), but "Tabled" and "Definition" don't map cleanly — they fall through to "unknown". A human should review whether Tabled/Definition should map to open or have their own category.

**Source**: Discovery schema output and normalize.py `_get_stage_category()`.

### I2 — token cache is in-memory only

The `msal.SerializableTokenCache` is instantiated each call but never serialized to or loaded from disk. The in-memory `TOKEN_CACHE` dict keeps the raw token string for the session's lifetime, but the full serializable cache (which enables proper token refresh across restarts) is not wired. Verified in auth.py source.

**Source**: Code review finding #1 (P1).

### I3 — Code review found 8 issues; 5 were safely auto-fixed

Of the 8 code review findings (1 P1, 4 P2, 3 P3), 5 were auto-fixed by the review pipeline (config.py error type, lazy import, URL encoding, verbose wiring, dead variable). The remaining P1 (SerializableTokenCache not persisted) was kept as a known limitation. The P2 items (URL parsing, no server-side filter pushdown, envelope DRY, config test gap) were assessed as v2 candidates.

**Source**: Code review output.

## PATTERNS

### P1 — Intent-gated agent interface pattern

**Scope**: universal

Method for exposing CLI functionality to AI agents without granting arbitrary system access:

1. Define an allowlist of approved intents (6 in this case).
2. Validate the intent against the allowlist before any expensive or sensitive operation.
3. Each intent maps to a deterministic, testable query function.
4. Unsupported intents return a structured error with machine-readable code and suggested alternatives.
5. The agent-facing command is the only entry point — individual query commands (query open, etc.) are for human use only.

Implemented in `agent.py` as `APPROVED_INTENTS` + `validate_intent()` + `execute_intent()`.

### P2 — Two-layer config with deep-merge override

**Scope**: universal

Method for managing configuration that has both team-shared defaults and per-user overrides. See `session_digests/2026061801_live_discovery_spike_and_config_system.md` P1 for full documentation.

## REFERENCES

### R1 — MSAL Python device code flow

Microsoft Authentication Library for Python's `PublicClientApplication` with `initiate_device_flow` and `acquire_token_by_device_flow`. Used for desktop/CLI auth where no redirect URI is available.

Documentation: https://learn.microsoft.com/en-us/entra/msal/python/

**Relevance**: Core auth mechanism for the CLI. No client secret needed.

### R2 — Microsoft Graph endpoints for SharePoint operations

Used across discovery, schema export, and item retrieval:
- `GET /sites/{hostname}:/sites/{path}` — site resolution
- `GET /sites/{site-id}/lists` — list enumeration
- `GET /sites/{site-id}/lists/{list-id}/columns` — schema export
- `GET /sites/{site-id}/lists/{list-id}/items?expand=fields` — item retrieval with field expansion

Documentation: https://learn.microsoft.com/en-us/graph/api/resources/sharepoint

**Relevance**: Primary API surface for all CLI operations.

## NEXT_STEPS

### N1 — Complete Azure AD app registration before first use

- **What**: Admin must create an Azure AD app registration with Sites.Read.All delegated permission and grant admin consent.
- **Prompted by**: Orchestrator completion report; CLI cannot authenticate without this.
- **Urgency**: now

### N2 — Create config/local.yaml with tenant/client IDs

- **What**: User copies config/workboard.example.yaml to config/local.yaml and fills in tenant_id and client_id from the app registration.
- **Prompted by**: Orchestrator completion report; CLI cannot authenticate without credentials.
- **Urgency**: now

### N3 — v2: Wire token persistence across sessions

- **What**: Serialize the msal.SerializableTokenCache to a file so users don't need to re-authenticate every session.
- **Prompted by**: Code review finding #1 (P1): token cache is in-memory only.
- **Urgency**: soon

### N4 — v2: Add app-only (client credentials) auth

- **What**: Implement an app-only auth mode so the CLI can run unattended in CI/CD or long-running agent server scenarios.
- **Prompted by**: Orchestrator completion report recommendation.
- **Urgency**: soon

### N5 — v2: Server-side `$filter` pushdown for queries

- **What**: Push stage/owner/due-date filters to the Graph API via `$filter` instead of fetching all items and filtering in memory.
- **Prompted by**: Code review finding #3 (P2): every query fetches all items before filtering.
- **Urgency**: someday

## Connections

- D1 —[informed_by]→ AGENTS.md package layout spec
- D2 —[resolved]→ test timeout during T05 CLI implementation
- D3 —[instance_of]→ P2 (two-layer config pattern from 2026061801)
- D3 —[informed_by]→ A1 (architecture decision record)
- A2 —[depends_on]→ A1 (implementation followed architecture)
- A3 —[depends_on]→ A2 (tests cover implementation)
- A4 —[depends_on]→ A2 (docs describe implementation)
- A7 —[instance_of]→ ce-code-review skill
- I2 —[informed_by]→ A7 (code review found the token cache issue)
- N1 —[depends_on]→ D4 (no app-only auth means human action needed)
- N3 —[informed_by]→ I2 (in-memory token cache gap)
- N5 —[informed_by]→ code review finding #3

## Trail Updates

- **workboard-cli-architecture**: Created. Documents the module boundaries, error taxonomy, permission model, data flow, and security boundary decisions.
- **workboard-cli-implementation**: Created. Covers all 11 source modules, 69 tests, CI workflow, and documentation.
- **workboard-cli-code-review**: Created. Documents the code review findings, applied fixes, and residual risks.
