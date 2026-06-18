# Technical Task Brief: T07 Operational query commands and summaries

## Task Summary

Implement practical read-only query commands and manager summaries over normalized WorkBoard items.

## Objective

Make the CLI useful to team members and workboard managers without requiring them to manually inspect raw SharePoint data.

## Context

Normalized WorkItem support exists or is in progress.

## Intent

Deliver the user-facing value: the WorkBoard can now be queried consistently by humans and AI agents.

## Expected Behavior

Commands:

```bash
workboard query open --format json
workboard query overdue --format json
workboard query by-owner --owner "<name>" --format json
workboard query blocked --format json
workboard query recently-updated --days 7 --format json
workboard summary manager --format markdown
```

## Current / Actual Behavior

Raw items and normalized WorkItems are available.

## Relevant Files or Areas

- `src/workboard_cli/queries.py`
- `src/workboard_cli/summaries.py`
- `src/workboard_cli/output.py`
- `tests/test_queries.py`
- `tests/test_summaries.py`

## In Scope

- Open items query.
- Overdue items query.
- By-owner query.
- Blocked items query.
- Recently updated query.
- Sorting and limiting results.
- Markdown manager summary.
- JSON output with source metadata.

## Out of Scope

- AI-written recommendations that are not grounded in WorkBoard data.
- Write-back status updates.
- Complex natural language parsing.

## Constraints

- Query definitions must be transparent and documented.
- Do not hide warnings from normalized data.
- If required fields are unmapped, fail clearly rather than returning misleading results.

## Implementation Guidance

Use explicit query functions that accept a list of WorkItems and return a typed result object. Keep formatting separate from filtering.

## Autonomy / Approval Boundary

The builder may add useful filters if they do not expand scope or rely on unverified fields.

## Acceptance Criteria

- All required query commands work on fixture data.
- Queries fail clearly when required mappings are missing.
- Manager summary includes counts, overdue items, blocked items, recently updated items, and source timestamp.
- Outputs are deterministic and testable.

## Tests Expected

- Open item filter test.
- Overdue calculation test.
- By-owner matching test.
- Blocked item test.
- Recently updated date-window test.
- Manager summary snapshot test.

## Risks / Watchouts

- Status values may be custom and need config aliases.
- Due date timezone handling can create false overdue results.
- Owner matching may need display name and email support.

## Do Not Change

- SharePoint data.
- Normalization contract without updating tests.

## Assumptions

- Config can define status aliases such as open, done, blocked, cancelled.

## Completion Standard

Query commands are complete when a manager can run a summary and receive a useful, sourced markdown report.
