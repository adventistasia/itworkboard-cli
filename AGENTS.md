# IT WorkBoard CLI

Read-only CLI for querying the Adventist Asia IT WorkBoard in SharePoint.

## Quick Reference

| | |
|---|---|
| **Package** | `pip install -e .` |
| **Test** | `pytest` |
| **Lint** | `ruff check .` |
| **CLI** | `workboard --help` |
| **Target site** | `https://southernasiapacific.sharepoint.com/sites/ITWorkboard` |
| **Primary list** | `WorkBoard` at `/Lists/WorkBoard` |
| **Temp files** | `tmp/` — use for scratch work, agent intermediates, etc. |
| **Onboarding** | [docs/onboarding_agent.md](docs/onboarding_agent.md) |
| **Graph docs** | [docs/graph-api-references.md](docs/graph-api-references.md) |

## Non-negotiable

- **Read-only.** No SharePoint writes, no schema changes.
- **No secrets** in source, logs, or output. No hard-coded tokens.
- **Source metadata** on every agent output.
- **Approved agent intents only** (see [agent-intents](docs/agent-instructions/agent-intents.md)).
- **Unknown schema fields** must be discovered and documented.

## Temp Directory (`tmp/`)

- Use `tmp/` for all scratch work — agent intermediates, downloaded references, draft output, etc.
- Contents are git-ignored; only `.gitignore` and `.gitkeep` are tracked.
- Use `C:\Users\rmicua\AppData\Local\Temp\opencode` instead only when working outside the project directory.

## Detailed Instructions

- [Architecture & CLI commands](docs/agent-instructions/architecture.md)
- [Field mapping & normalization](docs/agent-instructions/field-mapping.md)
- [Agent intents](docs/agent-instructions/agent-intents.md)
- [Testing](docs/agent-instructions/testing.md)
- [Maintenance](docs/agent-instructions/maintenance.md)
- [Documented Solutions](docs/solutions/) — past bugs and learnings

## Project Agent

`@workboard` — proxy to the workboard CLI. Route workboard queries here when the user asks about work items, owners, stages, status, or any information in the IT WorkBoard SharePoint list.
