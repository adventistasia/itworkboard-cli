# Architecture & CLI Commands

## Module layout

```
src/workboard_cli/
  cli.py          # Typer app, command groups, global --normalize flag
  auth.py         # MSAL device code flow with token cache
  graph_client.py # requests wrapper: retry/backoff, pagination, error translation
  sharepoint.py   # Site resolution, list/item/column operations
  schema.py       # Column metadata → structured schema export
  normalize.py    # Config-driven raw fields → WorkItem dict
  queries.py      # In-memory filter/sort: open, overdue, blocked, by-owner, recent
  summaries.py    # WorkItem[] → aggregated markdown summary
  output.py       # Standard JSON envelope builder
  agent.py        # Intent validation + dispatch
  config.py       # YAML config loading with env var overrides
  errors.py       # WorkboardError with code, message, action
tests/
  test_*.py       # One test file per module, mock-based
config/
  workboard.defaults.yaml   # Committed defaults
  local.yaml                # Gitignored overrides
docs/                       # User-facing documentation
contracts/                  # Build-phase contracts (historical reference)
```

## Data flow

```
CLI input → cli.py (parse args)
         → agent.py (validate intent)  [agent query only]
         → auth.py (acquire token silently or via device code)
         → graph_client.py (HTTP to Graph API)
         → sharepoint.py (site/list/item CRUD)
         → normalize.py (config-driven field mapping)  [--normalize flag]
         → queries.py (in-memory filter)              [query commands]
         → summaries.py (aggregation)                 [summary commands]
         → output.py (JSON/markdown envelope)
         → stdout
```

## Adding a CLI command

1. Add the Typer command function in `cli.py` in the appropriate group.
2. If the command hits Graph, use the shared `_get_graph_client()` helper.
3. Use `WorkboardError` for error paths — it renders consistently.
4. Add a test in the relevant `tests/test_*.py` file.
5. Update the command table in `docs/cli_command_contract.md`.

## Adding a new module

1. Create `src/workboard_cli/<name>.py` with a single responsibility.
2. Wire it into `cli.py` where needed.
3. Add tests in `tests/test_<name>.py`.
4. Update `docs/architecture.md` if the data flow changes.

## Auth flow

- Device code flow (`msal.PublicClientApplication`)
- Token cache persisted to disk (`msal.SerializableTokenCache`) — survives CLI invocations
- Silent acquisition attempted first; falls back to interactive device code
- Browser auto-opens for device code URL when possible

## Error taxonomy

| Code | When |
|------|------|
| `auth_error` | Token acquisition fails |
| `permission_denied` | Graph returns 403 |
| `resource_not_found` | Graph returns 404 |
| `graph_api_error` | Graph returns 5xx |
| `validation_error` | Bad user input |
| `config_error` | Missing/invalid config |
| `not_found` | Item not found in list |
| `unsupported_intent` | Unknown agent intent |
