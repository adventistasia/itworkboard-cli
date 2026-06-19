# Memory Log

Ground truth for what's happened and what's next. New sessions read this first, append at the end.

## State

| Field | Value |
|---|---|
| Current phase | **DELIVERY COMPLETE** |
| Last task | Session 4 — All 10 tasks + 4 audits passed |
| Next task | None — orchestrator delivery finished |
| Blockers | None |
| Completed | Discovery spike, architecture/contracts, CLI scaffold, auth/Graph client, SharePoint discovery, normalization, queries/summaries, agent interface, tests/CI, docs |

## Decisions

- **Memory approach**: Single `MEMORY.md` log at repo root, no extra tooling (2026-06-17)
- **CE setup**: All recommended tools installed (agent-browser, jq, ffmpeg, vhs, silicon, ast-grep CLI+skill)
- **AGENTS.md scope**: Compact, repo-specific guidance only. Orchestrator-driven flow, non-negotiables, target, stack, package layout.

## Session Log

### 2026-06-18 — Session 3: Real discovery spike completed

**Done:**
- Human completed Azure AD app registration and shared credentials
- Created `pyproject.toml` from starter template
- Created `src/workboard_cli/auth.py` — MSAL device code flow auth
- Created `src/workboard_cli/graph_client.py` — Graph API wrapper with pagination
- Created `src/workboard_cli/discovery_spike.py` — discovery orchestrator
- Installed package (`pip install -e .`)
- Ran live discovery against real SharePoint — **all 5 output files generated**

**Discovery findings:**
- Site resolved: `southernasiapacific.sharepoint.com/sites/ITWorkboard`
- 9 lists found: Users, Deliverables, **Work Board** (display name has space, internal name likely `WorkBoard`), EventLog, WorkIntake, Web Template Extensions, Hosted App Configs, Work Review, Documents
- WorkBoard list id: `57f6d985-7e30-4895-914e-60e73d39e1e0`
- 43 columns discovered, 30 sample items retrieved
- Key fields: `DeliveryOwner` [indexed], `WorkIntake` [indexed], `RelProject`, `RelWorkBrief`, `Stage`, `Title`, `Why`, `Who`, `Schedule`, `DateDue`, `DateCommitted`, `DateStart`, `DateClosed`, `Scope`, `CycleTime`, `AcceptanceCriteria`, `DecisionAuthority`, `AcceptanceAuthority`, `Requirements`, `Deliverables`, `_ColorTag`
- Standard fields: `AuthorLookupId`, `EditorLookupId`, `Created`, `Modified`, `ContentType`, `LinkTitle`

**Decisions:**
- Discovery spike code is clean enough to keep and reuse — no rollback needed
- Display name is "Work Board" (with space); queries should match on internal name `WorkBoard`
- Config stored in `config/workboard.yaml` (gitignored), template at `config/workboard.example.yaml` (committed), env var overrides supported

**Next:**
1. A01 audit — passed (see audit evaluation above)
2. Proceed to T02 — architecture and contracts

### 2026-06-18 — Session 4: T02 Architecture and contracts completed

**Done:**
- Created `docs/architecture.md` — ADR, module boundaries, data flow, error taxonomy (8 codes), permission model (Sites.Read.All, device code only), logging rules, agent security boundary
- Created `docs/cli_command_contract.md` — all 13 commands documented with shapes, exit codes, global options, error output format
- Created `docs/agent_json_contract.md` — success/error envelopes, WorkItem model with all fields, 6 approved intents, refusal rules, summary envelope shape
- Updated `config/workboard.example.yaml` — user-facing example matching discovery-derived field mapping

**Key decisions:**
- Module boundaries match the AGENTS.md layout with no deviations
- Token cache not yet wired (deferred — T03+ will add it)
- `by-owner` matching is case-insensitive substring on display name or email (to be confirmed in T07)
- No app-only flow in v1 — delegated user auth only

**Next:**
1. A02 audit — PASS
2. T03+T04+T05 — Completed (see below)
3. Run A03 audit — `audit_briefs/a03_implementation_audit.md`

**A02 audit verdict: PASS**
- All 6 pass criteria met
- No scope issues, no quality issues
- Architecture is ready for implementation agents

### 2026-06-18 — Session 4: T03+T04+T05 implementation

**Done:**
- `src/workboard_cli/errors.py` — structured `WorkboardError` with code, message, action, `to_dict()`
- `src/workboard_cli/auth.py` — MSAL device code flow with token cache, silent acquisition, `check_auth()`, secret redaction
- `src/workboard_cli/graph_client.py` — `GraphClient` with retry/backoff on 429, error translation (401→auth_error, 403→permission_denied, 404→resource_not_found, 5xx→graph_api_error), pagination via `@odata.nextLink`
- `src/workboard_cli/sharepoint.py` — `parse_site_url()`, `get_site()`, `get_lists()`, `find_list()`, `get_list_columns()`, `get_list_items()`, `get_list_item()`
- `src/workboard_cli/schema.py` — `export_schema()` with structured column output (name, displayName, type, required, lookup)
- `src/workboard_cli/cli.py` — 9 command groups (auth, site, lists, schema, items, query, summary, agent, config), 5 implemented commands (login, status, site info, lists discover, schema export, items list, items get, config validate), query/summary/agent placeholders, agent intent allowlist with refusal
- `.gitignore` — Python, config, discovery output, IDE
- `config/workboard.example.yaml` — user-facing example config
- 7 test files, 33 tests passing, ruff clean

**Key decisions:**
- Added `config validate` command to meet the contract (checks field mappings against exported schema)
- Agent query intent validation happens client-side before any Graph call
- Token cache uses `msal.SerializableTokenCache` for silent token refresh

### 2026-06-18 — Session 4 continued: T06–T10 completion

**Done:**
- `src/workboard_cli/normalize.py` — config-driven `normalize_item()` → WorkItem dict with stage category, date parsing, person parsing, source URL, raw field passthrough, warnings
- `src/workboard_cli/queries.py` — `filter_open()`, `filter_overdue()`, `filter_blocked()`, `filter_by_owner()`, `filter_recently_updated()`
- `src/workboard_cli/summaries.py` — `build_summary()` + `render_markdown_summary()`
- `src/workboard_cli/output.py` — `build_envelope()`, `build_summary_envelope()`, `build_error_envelope()`
- `src/workboard_cli/agent.py` — `validate_intent()` + `execute_intent()` with 6 approved intents
- `src/workboard_cli/cli.py` — all placeholders replaced, `--normalize` flag, intent validation before Graph calls
- `.github/workflows/ci.yml` — GitHub Actions (ruff + pytest on 3.11/3.12/3.13)
- `README.md`, `docs/` — 8 doc files covering admin, config, manager, agent, troubleshooting, security, testing
- `orchestrator_completion_report.md` — final report

**Tests:** 69 passed (55 unit + 14 CLI), ruff clean

**Audit verdicts:** A01 PASS, A02 PASS, A03 PASS, A04 PASS

**State: DELIVERY COMPLETE**

### 2026-06-19 — Session 5: session_id correlation + CE pipeline run

**Done:**
- Implemented `session_id` correlation across observation streams (U1-U4):
  - `src/workboard_cli/observations.py` — uuid generation, `get_session_id()`, stamp on all events
  - `src/workboard_cli/output.py` — `sessionId` in all stdout envelopes
  - `.opencode/agents/workboard.md` — agent observation instructions updated
  - `tests/test_observations.py` (new), `tests/test_output.py`, `tests/test_cli.py` — 83 tests passing
- Full CE pipeline: ce-plan → ce-work → ce-simplify-code → ce-code-review → ce-commit-push-pr → CI autofix
- Code review: P1+P3 findings applied (UUID v4 nibble, regex hardening); deferred test gaps filed as issues #1–#4
- Created `docs/solutions/design-patterns/session-id-correlation.md` — design pattern doc
- Created `CONCEPTS.md` — domain vocabulary (session_id, observation_stream)
- PR [#5](https://github.com/adventistasia/itworkboard-cli/pull/5) open, CI passing

**Next:** Close PR #5, then **session-unique counting** in `scripts/analyze-observations.py` (Phase 1.1 of observations roadmap). Resolve agent-obs path-resolution caveat in `.opencode/agents/workboard.md` first — it's a prerequisite for Phase 2 auto-improvement.
