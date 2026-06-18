# Memory Log

Ground truth for what's happened and what's next. New sessions read this first, append at the end.

## State

| Field | Value |
|---|---|
| Current phase | Prerequisites — Azure AD app registration |
| Last task | Session 2 — T01 scaffolded then rolled back (mock data, not real discovery) |
| Next task | Complete Azure AD app reg checklist → run live discovery |
| Blockers | No Azure AD app registration credentials for the Desert AD tenant |
| Completed | AGENTS.md created, MEMORY.md created, CE tooling installed, blocker identified (mock data invalid), Azure AD checklist created at `prerequisites/azure_app_reg_checklist.md` |

## Decisions

- **Memory approach**: Single `MEMORY.md` log at repo root, no extra tooling (2026-06-17)
- **CE setup**: All recommended tools installed (agent-browser, jq, ffmpeg, vhs, silicon, ast-grep CLI+skill)
- **AGENTS.md scope**: Compact, repo-specific guidance only. Orchestrator-driven flow, non-negotiables, target, stack, package layout.

## Session Log

### 2026-06-18 — Session 2: Rollback + blocker identified

**Done:**
- Delegated T01 to builder — scaffold created, 26 tests passing
- Ran A01 audit — builder output used mock data, not real SharePoint discovery
- Delegated T02 to builder — architecture docs, contracts, 93 tests passing
- Ran A02 audit — passed on code quality, but built on unverified field assumptions
- **Rolled back all session work** at user's direction (mock data invalidates architecture assumptions)
- Identified blocker: no Azure AD credentials for the Desert AD tenant
- Created `prerequisites/azure_app_reg_checklist.md` for the human to complete

**Decisions:**
- No implementation work proceeds until real discovery data is captured
- All T01/T02 output was removed — clean start once credentials are available
- Discovery spike code will be rewritten from scratch after credentials exist (no reusing untested scaffold)

**Next:**
1. Human completes Azure AD app registration checklist
2. Share credentials (tenant_id, client_id) with the agent
3. Run live discovery spike against real SharePoint
4. Proceed with A01 → T02 → ... using real schema data
