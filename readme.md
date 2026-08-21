# IT WorkBoard CLI

Read-only CLI for querying the Adventist Asia IT WorkBoard in SharePoint. Provides deterministic JSON for AI agents and markdown summaries for managers.

## Quick start

```bash
pip install .
workboard --help
```

## Agent install prompt

Copy and paste the following into your AI agent to install and onboard:

```
Install workboard-cli from this repo, then onboard me.

1. Run `pip install -e .` from the repo root to install the package.
2. Verify the CLI works: run `workboard --help`.
3. Run `workboard auth login` and guide me through the device code authentication flow.
4. Once authenticated, run `workboard site info` to confirm connectivity.
5. Run a quick query to show me it works: `workboard items list --limit 5`.
6. Summarise what was installed and suggest next steps (try a query, view manager summary, or read docs/agent_usage.md).
```

## Uninstall

```bash
pip uninstall workboard-cli
```

## Setup

The CLI ships with default credentials for our team — run from the repo root with no config setup needed:

```bash
workboard auth login
```

> **Note:** Defaults are resolved relative to the working directory. Run `workboard` commands from the repo root, or set `WORKBOARD_TENANT_ID`/`WORKBOARD_CLIENT_ID` env vars for use outside the repo.

To override defaults (e.g. for a different tenant), create `config/local.yaml` or set environment variables:

- `WORKBOARD_TENANT_ID`
- `WORKBOARD_CLIENT_ID`
- `WORKBOARD_SITE_URL`
- `WORKBOARD_LIST_NAME`

Or use the CLI to set tenant/client IDs directly:

```bash
workboard config set --tenant-id <guid> --client-id <guid>
```

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
workboard config set --tenant-id <guid>       # Set tenant ID in local config
workboard config set --client-id <guid>       # Set client ID in local config
```

## Configuration

Default config: `config/workboard.defaults.yaml` (committed) — includes team Azure AD credentials, site URL, and field mappings. Override any value via `config/local.yaml` (gitignored) or environment variables:

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
