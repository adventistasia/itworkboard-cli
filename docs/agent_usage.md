# Agent usage

## For AI agent orchestrators

The `agent query` command exposes 6 approved intents. This is the **only** agent-facing interface.

## Approved intents

```bash
workboard agent query --intent open_items
workboard agent query --intent overdue_items
workboard agent query --intent blocked_items
workboard agent query --intent items_by_owner --owner "Name"
workboard agent query --intent recently_updated_items --days 7
workboard agent query --intent manager_summary
```

## Output format

All agent queries return the standard JSON envelope with `source`, `retrievedAt`, `filters`, `result`, `warnings`, and `errors` fields. See `docs/agent_json_contract.md` for the full schema.

## Agent restrictions

- **No free-form browsing**: The CLI rejects any intent not in the approved list
- **No write access**: The CLI is read-only
- **No token exposure**: Tokens and secrets never appear in output
- **Source metadata**: Every response includes `siteUrl`, `listName`, and `retrievedAt`

## Error handling

Agents should check `status` before reading `result`. A status of `"error"` includes a machine-readable `code`, human-readable `message`, and suggested `action`.

## For orchestrator developers

Treat the CLI as a constrained tool. Register `workboard agent query` as the single tool, not individual `workboard query` commands. This centralizes intent validation and refusal logic.
