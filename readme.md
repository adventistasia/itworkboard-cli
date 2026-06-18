# IT WorkBoard CLI

Read-only CLI for querying the Adventist Asia IT WorkBoard in SharePoint. Provides deterministic JSON for AI agents and markdown summaries for managers.

## Quick start

```bash
pip install .
workboard --help
```

## Setup

1. Copy `config/workboard.example.yaml` to `config/local.yaml`
2. Fill in your Azure AD `tenant_id` and `client_id`
3. Authenticate: `workboard auth login`

## Commands

```bash
workboard auth login                          # Device code authentication
workboard auth status                         # Check auth status
workboard site info                           # Resolve SharePoint site
workboard lists discover                      # List all lists
workboard schema export --list WorkBoard      # Export column schema
workboard items list --limit 10               # List items from WorkBoard
workboard items get <id>                      # Get single item
workboard query open                          # Open items
workboard query overdue                       # Overdue items
workboard query blocked                       # Blocked items
workboard query by-owner --owner "<name>"     # Items by owner
workboard query recently-updated --days 7     # Recently updated
workboard summary manager                     # Manager summary
workboard agent query --intent open_items     # Agent-safe query
workboard config validate                     # Validate config mapping
```

## Configuration

Default config: `config/workboard.defaults.yaml` (committed). Override via `config/local.yaml` (gitignored) or environment variables:

- `WORKBOARD_TENANT_ID`
- `WORKBOARD_CLIENT_ID`
- `WORKBOARD_SITE_URL`
- `WORKBOARD_LIST_NAME`

## Development

```bash
pip install -e ".[dev]"   # Editable install with dev dependencies (pytest, ruff)
pytest                    # Run tests
ruff check .              # Lint
```

## Documentation

See `docs/` for detailed guides:

- [`configuration.md`](docs/configuration.md) — Config file format and field mapping
- [`manager_usage.md`](docs/manager_usage.md) — Daily summary and manager workflows
- [`agent_usage.md`](docs/agent_usage.md) — AI agent JSON interface
- [`testing.md`](docs/testing.md) — Running tests
- [`troubleshooting.md`](docs/troubleshooting.md) — Common issues
- [`security_model.md`](docs/security_model.md) — Auth and permissions
- [`architecture.md`](docs/architecture.md) — Module design and data flow

## Target

- Site: `https://southernasiapacific.sharepoint.com/sites/ITWorkboard`
- List: `WorkBoard` at `/Lists/WorkBoard`

## Architecture

See `docs/architecture.md`. The CLI uses Typer, MSAL device code flow, and Microsoft Graph API (Sites.Read.All). All agent outputs include `source` and `retrievedAt` metadata.
