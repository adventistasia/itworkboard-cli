# Technical Task Brief: T08 Agent interface and JSON contract

## Task Summary

Implement a constrained AI-agent query interface over approved WorkBoard operations.

## Objective

Allow AI agents to call the CLI predictably without giving them arbitrary SharePoint access.

## Context

Operational query commands exist. The agent interface should be a thin, safe layer over those commands.

## Intent

Make AI agents useful to team members and workboard managers while preserving data boundaries and auditability.

## Expected Behavior

Command:

```bash
workboard agent query --intent open_items --format json
workboard agent query --intent overdue_items --format json
workboard agent query --intent blocked_items --format json
workboard agent query --intent items_by_owner --owner "<name>" --format json
workboard agent query --intent manager_summary --format json
```

## Current / Actual Behavior

Structured query commands exist or are in progress.

## Relevant Files or Areas

- `src/workboard_cli/agent.py`
- `src/workboard_cli/output.py`
- `contracts/agent_query_contract.md`
- `tests/test_agent_interface.py`

## In Scope

- Approved intent enum.
- Required/optional parameters per intent.
- Stable JSON envelope.
- Refusal/error output for unsupported intents.
- Source metadata and warnings.
- Contract tests.

## Out of Scope

- Free-form natural-language execution.
- Autonomous changes to WorkBoard.
- Summaries that fabricate missing data.

## Constraints

- Agents may only call approved intents.
- Output must be parseable JSON by default.
- Errors must be machine-readable.
- Include `retrievedAt`, `source`, `filters`, `items`, `warnings`, and `errors` where applicable.

## Implementation Guidance

Use `contracts/agent_query_contract.md` as the output contract. Treat this as a public API even though it is a CLI.

## Autonomy / Approval Boundary

The builder may add additional approved intents only if they map directly to existing structured queries and tests are added.

## Acceptance Criteria

- Approved intents work.
- Unsupported intent returns a safe error.
- Missing required parameter returns a safe error.
- JSON contract tests pass.
- No raw token, secret, or excessive SharePoint metadata appears in output.

## Tests Expected

- One test per approved intent.
- Unsupported intent test.
- Missing owner parameter test.
- JSON schema/snapshot tests.
- Warning propagation test.

## Risks / Watchouts

- Agents may treat warnings as success unless explicit status exists.
- Free-form query strings create ambiguity and should remain out of scope for first version.

## Do Not Change

- Underlying query definitions without updating contract tests.

## Assumptions

- Orchestrator will expose this CLI to agents as a constrained tool.

## Completion Standard

Agent interface is complete when agents can reliably call approved intents and receive deterministic JSON.
