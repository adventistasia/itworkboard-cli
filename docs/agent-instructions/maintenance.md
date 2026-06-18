# Maintenance

## Schema drift detection

The SharePoint list schema may change over time (new columns, renamed columns, deleted columns). When a command produces unexpected warnings or missing fields:

1. Run `workboard schema export --list WorkBoard > discovery/schema_latest.json`.
2. Diff against a previous export to identify what changed.
3. Update `config/workboard.defaults.yaml` field mappings if columns were added/renamed.
4. Update `normalize.py` if parsing logic needs to handle new column types.
5. Update `docs/agent_json_contract.md` WorkItem model if a new field should be surfaced.

## Auth troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `auth_error` on login | Wrong tenant_id or client_id in config | Check `config/local.yaml` |
| `permission_denied` | MSAL token expired or user lacks Sites.Read.All | Run `workboard auth login` again |
| Browser doesn't auto-open | No default browser or headless env | Open the printed URL manually |
| Token cache stale | Cache file corrupted | Delete `~/.workboard_cache/*` and re-auth |

## Config changes

- **`config/workboard.defaults.yaml`** — committed, shared defaults. Changes here affect all users.
- **`config/local.yaml`** — gitignored, user-local overrides. Never commit.
- **Environment variables** override both: `WORKBOARD_TENANT_ID`, `WORKBOARD_CLIENT_ID`, `WORKBOARD_SITE_URL`, `WORKBOARD_LIST_NAME`.
- After config changes, run `workboard config validate` to verify mappings match the live schema.

## CI maintenance

The CI workflow runs on Ubuntu latest. If it starts failing:
- Check if `responses` library API changed (pin version in pyproject.toml if needed).
- Check if ruff rules were added in a ruff upgrade.
- Run `pytest -q` locally with `pip install -e ".[dev]"` to reproduce.

## Adding a dependency

1. Add to `dependencies` or `[project.optional-dependencies] dev` in `pyproject.toml`.
2. Lock the minimum version (e.g., `pydantic>=2` not `pydantic`).
3. Run `pip install -e ".[dev]"` to update local env.
4. Add tests for any new integration points.

## docs/ reference

User-facing docs are in `docs/`. Keep them in sync with code changes:

| Doc | When to update |
|---|---|
| `docs/configuration.md` | Field mapping, stage aliases, env vars change |
| `docs/cli_command_contract.md` | New command, changed flag, different exit code |
| `docs/agent_json_contract.md` | New intent, changed WorkItem model, new envelope field |
| `docs/architecture.md` | Module boundaries change, data flow changes |
| `docs/agent_usage.md` | Intent list changes |
| `docs/manager_usage.md` | Manager summary format changes |
| `docs/onboarding_agent.md` | Install flow or auth steps change |
| `docs/admin_permissions.md` | Required Graph permissions change |
| `docs/testing.md` | Test patterns change |
| `docs/troubleshooting.md` | New common issues discovered |
| `docs/security_model.md` | Auth flow or token handling changes |

## Background references

- `contracts/` — build-phase contracts documenting command shapes, agent JSON envelope, and normalization config. Useful for understanding the original design intent.
- `discovery/` — raw discovery outputs from the initial SharePoint schema exploration.
