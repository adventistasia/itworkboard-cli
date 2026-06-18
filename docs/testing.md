# Testing

## Quick start

```bash
pip install -e ".[dev]"
pytest -q
```

## Test structure

```
tests/
  test_cli.py              # CLI smoke tests (help, version, unsupported intent)
  test_auth.py             # Auth module tests
  test_graph_client.py     # Graph client (mocked HTTP, pagination, errors)
  test_sharepoint.py       # SharePoint helper functions
  test_schema.py           # Schema column type detection
  test_normalize.py        # WorkItem normalization
  test_queries.py          # Query filter logic
  test_summaries.py        # Manager summary building
  test_output.py           # JSON envelope formatting
  test_agent.py            # Agent intent dispatch
  test_errors.py           # Error class tests
```

## Running tests

```bash
pytest                    # All tests (no live credentials needed)
pytest -v                 # Verbose
pytest tests/test_cli.py  # Single test file
pytest -k "normalize"     # Filter by keyword
```

## Linting

```bash
ruff check .
ruff check . --fix        # Auto-fix safe issues
```

## CI

The GitHub Actions workflow in `.github/workflows/ci.yml` runs on push/PR to `main`:

1. Installs package + dev dependencies
2. Runs `ruff check .`
3. Runs `pytest -q`

## Test principles

- All tests are mock-based — no live SharePoint access required
- Graph API calls are mocked with the `responses` library
- Auth tests verify behavior without real credentials
- CLI tests verify command structure and error handling
- Unit tests cover edge cases (missing fields, null dates, empty lists)
