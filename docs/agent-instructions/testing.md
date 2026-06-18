# Testing

## Quick start

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
```

## Test principles

- **All tests are mock-based** — no live SharePoint access required.
- Graph API calls are mocked with the `responses` library.
- Auth tests verify behavior without real credentials.
- CLI tests verify command structure, flag parsing, and error handling.
- Unit tests cover edge cases: missing fields, null dates, empty lists.

## Test file mapping

| Test file | What it covers |
|---|---|
| `test_auth.py` | MSAL flow, token cache, `check_auth()` |
| `test_graph_client.py` | Retry/backoff, pagination, error translation (401/403/404/5xx) |
| `test_sharepoint.py` | `parse_site_url()`, `get_site()`, `get_lists()`, list/item ops |
| `test_schema.py` | Column type detection, schema export format |
| `test_normalize.py` | Field mapping, date/person parsing, stage aliases, warnings |
| `test_queries.py` | Filter logic: open, overdue, blocked, by-owner, recent |
| `test_summaries.py` | Aggregation, markdown rendering, edge cases |
| `test_output.py` | JSON envelope shape: success, error, summary variants |
| `test_agent.py` | Intent validation (approved + unknown), dispatch routing |
| `test_cli.py` | Command structure, flag parsing, error exit codes |
| `test_errors.py` | Error class fields, `to_dict()` format |

## Mocking pattern

```python
import responses

@responses.activate
def test_get_site():
    responses.get(
        "https://graph.microsoft.com/v1.0/sites/host:path",
        json={"id": "site-id", "webUrl": "https://..."},
        status=200,
    )
    client = GraphClient(access_token="fake")
    result = client.get("sites/host:path")
    assert result["id"] == "site-id"
```

## Writing a test for a new feature

1. Create mock data matching the real Graph response shape (use `discovery/` samples as reference).
2. Register the mock with `@responses.activate` and `responses.get/post`.
3. Call your function with a `GraphClient` initialized with a fake token.
4. Assert on the returned structure, not implementation internals.
5. Add edge cases: empty results, null fields, unexpected field types.

## CI expectations

The GitHub Actions workflow runs `ruff check . && pytest -q` on every push/PR to `main`. Both must pass before merge.
