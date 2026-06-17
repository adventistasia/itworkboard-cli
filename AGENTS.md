# IT WorkBoard CLI — Agent instructions

This is a build-plan package, not implemented code. There is no `src/`, `tests/`, or `pyproject.toml` yet — those get created during execution. The work follows an orchestrator flow: builder subagent → auditor subagent → gate.

## How to work here

- Read `00_orchestrator_master_prompt.md` first (your role, boundaries, stop conditions).
- Follow the decomposed sequence in `decomposed_orchestrator_instruction.md`: T01 → A01 → T02 → A02 → T03+T04+T05 → A03 → T06+T07+T08+T09+T10 → A04.
- Pass each audit gate before the next phase. Do not proceed on a failed gate.
- Each `briefs/tNN_*.md` is a task for a builder subagent. Each `audit_briefs/aNN_*.md` is the matching audit for an auditor subagent.
- Use `contracts/` as the source of truth for command shapes, agent JSON envelope, and normalization config.

## Session memory

- **Read `MEMORY.md` first thing** — the State table tells you where we are, the Decisions section avoids re-litigating settled choices.
- **Append to the Session Log at the end** — note what was done, any decisions made, and suggested next steps. Do not overwrite or edit past entries.

## Non-negotiable

- Read-only CLI. No SharePoint writes, no schema changes.
- No secrets in source, logs, or output. No hard-coded tokens.
- Agent outputs must include `source` (system, siteUrl, listName, listId) and `retrievedAt` fields.
- Unknown schema fields must be discovered and documented, never silently guessed.
- Approved agent intents only: `open_items`, `overdue_items`, `blocked_items`, `items_by_owner`, `recently_updated_items`, `manager_summary`.

## Target

- Site: `https://southernasiapacific.sharepoint.com/sites/ITWorkboard`
- Primary list: `WorkBoard` at `https://southernasiapacific.sharepoint.com/sites/ITWorkboard/Lists/WorkBoard`

## Default stack (from `readme.md` and `templates/starter_pyproject.toml`)

| Area | Choice |
|---|---|
| Language | Python 3.11+ |
| CLI framework | Typer (entrypoint: `workboard_cli.cli:app`) |
| Auth | MSAL |
| HTTP | `requests` or Microsoft Graph SDK |
| Validation | Pydantic v2+ |
| Testing | pytest |
| Linting | ruff (`line-length = 100`) |
| Config | YAML (`pyyaml`) |
| Package install | `pip install -e .` |

## Package layout (from orchestrator prompt and starter pyproject.toml)

```
src/workboard_cli/
  cli.py          # Typer app, command groups
  auth.py         # MSAL auth
  graph_client.py # Graph API wrapper
  sharepoint.py   # SharePoint list operations
  schema.py       # Schema export
  normalize.py    # Field normalization
  queries.py      # Query logic
  summaries.py    # Markdown summaries
  output.py       # JSON/markdown output formatting
  config.py       # Config loading
  errors.py       # Structured errors
config/
  workboard.example.yaml
tests/
```

## Verification commands (will exist after implementation)

```bash
pytest                            # run all tests
ruff check .                      # lint
python -m workboard_cli --help    # CLI smoke test
pip install -e .                  # editable install
```

## Source references

`sources.md` links to current Microsoft Graph docs. Use those over copied examples if discrepancies arise.
