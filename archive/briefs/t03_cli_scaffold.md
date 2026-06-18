# Technical Task Brief: T03 CLI scaffold

## Task Summary

Create the installable CLI repository scaffold.

## Objective

Set up a maintainable Python package with a working `workboard` command, test harness, linting, and placeholder commands.

## Context

This task creates the base that later tasks will fill with Graph, SharePoint, normalization, and query behavior.

## Intent

Give all builders a stable project structure and command entrypoint.

## Expected Behavior

After this task, the repository should support:

```bash
python -m pip install -e .
workboard --help
pytest
```

## Current / Actual Behavior

No scaffold is assumed unless created by the discovery spike.

## Relevant Files or Areas

- `pyproject.toml`
- `src/workboard_cli/cli.py`
- `src/workboard_cli/__init__.py`
- `tests/`
- `.gitignore`
- `README.md`

## In Scope

- Package scaffold.
- CLI root command.
- Placeholder command groups.
- Version command.
- Test and lint setup.
- Example config path convention.

## Out of Scope

- Real Graph calls.
- Real SharePoint queries.
- Full docs.

## Constraints

- Do not require live SharePoint access for basic tests.
- Keep dependencies minimal.
- Follow lowercase underscore file naming.

## Implementation Guidance

Use Typer unless a clear reason exists to use Click. Add command groups for `auth`, `site`, `lists`, `schema`, `items`, `query`, `summary`, and `agent`.

## Autonomy / Approval Boundary

The builder may add basic developer tooling. Do not add deployment infrastructure yet.

## Acceptance Criteria

- `workboard --help` works.
- Command groups are visible.
- `pytest` runs.
- The package can be installed editable.
- Placeholder commands return clear not-implemented messages where needed.

## Tests Expected

- CLI help smoke test.
- Version command test.
- Placeholder command test.

## Risks / Watchouts

- Pulling live auth into tests too early.
- Creating hidden side effects during import.

## Do Not Change

- Target SharePoint data.

## Assumptions

- Python 3.11+ is available.

## Completion Standard

The scaffold is complete when later builders can implement modules without changing the base command design.
