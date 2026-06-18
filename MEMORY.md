# Memory Log

Ground truth for what's happened and what's next. New sessions read this first, append at the end.

## State

| Field | Value |
|---|---|
| Current phase | Discovery complete — ready for architecture phase |
| Last task | Session 3 — Real discovery spike completed & A01 passed |
| Next task | T02 — Architecture and contracts |
| Blockers | None |
| Completed | Azure AD app registration created, discovery spike code scaffolded & live, A01 audit passed, config file system created |

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
