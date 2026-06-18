# IT WorkBoard CLI

Read-only CLI for querying the Adventist Asia IT WorkBoard in SharePoint. Delivers deterministic JSON for AI agents and markdown summaries for managers.

## Quick Reference

| | |
|---|---|
| **Package** | `pip install -e .` |
| **Test** | `pytest` |
| **Lint** | `ruff check .` |
| **CLI** | `workboard --help` |
| **Target site** | `https://southernasiapacific.sharepoint.com/sites/ITWorkboard` |
| **Primary list** | `WorkBoard` at `/Lists/WorkBoard` |

## Non-negotiable

- **Read-only.** No SharePoint writes, no schema changes.
- **No secrets** in source, logs, or output. No hard-coded tokens.
- **Source metadata** on every agent output: `source` (system, siteUrl, listName, listId) and `retrievedAt`.
- **Approved agent intents only:** `open_items`, `overdue_items`, `blocked_items`, `items_by_owner`, `recently_updated_items`, `manager_summary`. Unknown intents are refused.
- **Unknown schema fields** must be discovered and documented, never silently guessed.

## Detailed Instructions

- [Architecture & CLI commands](docs/agent-instructions/architecture.md) — module layout, data flow, adding commands
- [Field mapping & normalization](docs/agent-instructions/field-mapping.md) — config-driven mapping, stage aliases, adding fields
- [Agent intents](docs/agent-instructions/agent-intents.md) — query pipeline, adding intents, JSON envelope
- [Testing](docs/agent-instructions/testing.md) — mock patterns, test structure, writing tests
- [Maintenance](docs/agent-instructions/maintenance.md) — schema drift, auth troubleshooting, CI

## Project Agent

`@workboard` — proxy to the workboard CLI. Use it to run queries, check board status, look up items by owner, get manager summaries, or answer any question about the IT WorkBoard.

## User Onboarding

See [docs/onboarding_agent.md](docs/onboarding_agent.md) for installing, authenticating, and running a demo query.

## Source References

`sources.md` links to current Microsoft Graph docs. Use those over copied examples if discrepancies arise.
