# Agent Intents

## The agent pipeline

```
workboard agent query --intent <name> [--owner "Name"] [--days N]
  → agent.py: validate_intent(intent)
  → agent.py: execute_intent(name, params)
    → sharepoint.get_list_items() or queries module
    → output.build_envelope() / build_summary_envelope()
  → stdout: JSON
```

## Adding a new intent

1. Define the filter function in `queries.py` (if query) or `summaries.py` (if summary).
2. Add the intent name to `APPROVED_INTENTS` in `agent.py`.
3. Add the intent handler in `execute_intent()` in `agent.py` — map intent name to function call.
4. Add tests in `tests/test_agent.py` for validation + execution.
5. Add a CLI test in `tests/test_cli.py` for the new intent flag combination.
6. Update the intent list in `docs/agent_usage.md` and `docs/agent_json_contract.md`.

## Intent validation rules

- Intent names are lowercase, snake_case.
- Unknown intents return `unsupported_intent` error — no fallback, no partial match.
- Intent parameters (`owner`, `days`) are validated at the same time.
- All intents go through `validate_intent()` before any Graph call.

## Output envelope (agent query)

```json
{
  "status": "success",
  "source": {
    "system": "SharePoint",
    "siteUrl": "https://...",
    "listName": "WorkBoard",
    "listId": "57f6d985-..."
  },
  "retrievedAt": "2026-06-18T12:00:00Z",
  "filters": { "intent": "open_items" },
  "result": { "items": [...], "count": 5 },
  "warnings": [{"field": "stage", "message": "Unknown value 'Foo'"}],
  "errors": []
}
```

## Summary envelope

```json
{
  "status": "success",
  "source": { "...": "..." },
  "retrievedAt": "...",
  "result": {
    "total_items": 30,
    "overdue_count": 5,
    "blocked_count": 3,
    "by_stage": { "open": 10, "in_progress": 12, "blocked": 3, "done": 5 },
    "by_owner": { "Alice": 8, "Bob": 7 },
    "markdown": "# Manager Summary\n\n..."
  }
}
```

## Refusal rules

- Any intent not in `APPROVED_INTENTS` → `unsupported_intent` error.
- Any attempt to write (create, update, delete) → refused — CLI is read-only.
- No free-form Graph queries — all access is through predefined intents.
