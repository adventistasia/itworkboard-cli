# Technical Task Brief: T09 Tests and CI readiness

## Task Summary

Build the test suite and CI-ready validation commands needed to trust the CLI.

## Objective

Ensure the CLI can be changed safely and audited without live SharePoint access for most tests.

## Context

Core CLI modules exist or are nearing completion.

## Intent

Prevent regressions and provide confidence before the CLI is handed to team members or agents.

## Expected Behavior

Developer commands should include:

```bash
pytest
ruff check .
python -m workboard_cli --help
```

If CI is available, add a simple workflow. If not, document commands.

## Current / Actual Behavior

Partial tests likely exist from earlier tasks.

## Relevant Files or Areas

- `tests/`
- `tests/fixtures/`
- `pyproject.toml`
- `.github/workflows/ci.yml` if repository uses GitHub Actions
- `docs/testing.md`

## In Scope

- Unit tests.
- CLI tests.
- Mock Graph responses.
- Contract tests.
- Error tests.
- Optional CI workflow.
- Test documentation.

## Out of Scope

- Live integration tests as a required CI gate.
- Load testing.
- Write-operation tests.

## Constraints

- Tests must not require real SharePoint credentials by default.
- Live tests, if added, must be opt-in through environment variables.
- Fixtures must not contain sensitive production data.

## Implementation Guidance

Use mocked Graph fixtures for normal CI. Create one clearly marked optional live smoke test only if useful.

## Autonomy / Approval Boundary

The builder may add CI files only if the repository context supports them.

## Acceptance Criteria

- Unit tests cover auth/client, discovery, normalization, queries, summaries, and agent interface.
- CLI smoke tests pass.
- Contract tests verify JSON shape.
- Test fixtures contain no sensitive data.
- CI or local validation command is documented.

## Tests Expected

This task is itself about tests; include a final test coverage summary in the completion response.

## Risks / Watchouts

- Mock tests can overfit to fake responses.
- Live tests can leak data or fail due to permissions.

## Do Not Change

- Production SharePoint data.

## Assumptions

- The repository supports pytest.

## Completion Standard

Test work is complete when a reviewer can run one local command and receive a meaningful pass/fail signal.
