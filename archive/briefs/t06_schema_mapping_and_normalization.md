# Technical Task Brief: T06 Schema mapping and normalization

## Task Summary

Implement configurable mapping from raw SharePoint fields into a normalized WorkItem model.

## Objective

Allow the CLI to produce stable work item objects even if SharePoint field names differ from expected labels.

## Context

The WorkBoard schema is discovered at runtime. The CLI must not assume exact column names for status, owner, priority, due date, or blocker fields.

## Intent

Create a durable boundary between volatile SharePoint list configuration and stable agent-facing outputs.

## Expected Behavior

Add config support:

```bash
workboard config validate --config config/workboard.yaml
workboard items list --normalize --config config/workboard.yaml --format json
```

Normalized WorkItem fields should include:

```text
id
title
status
priority
owner
requester
department
project
dueDate
createdDate
modifiedDate
blockedReason
sourceUrl
rawFields
warnings
```

## Current / Actual Behavior

Raw SharePoint item retrieval exists.

## Relevant Files or Areas

- `src/workboard_cli/config.py`
- `src/workboard_cli/normalize.py`
- `config/workboard.example.yaml`
- `tests/test_normalize.py`
- `tests/test_config.py`

## In Scope

- YAML configuration loader.
- Mapping validation against exported schema.
- Normalization of raw items.
- Missing field warnings.
- Date parsing.
- Person/lookup field handling where practical.
- Tests with fixtures.

## Out of Scope

- Mutating SharePoint fields.
- Auto-mapping without human review.
- Complex workflow inference.

## Constraints

- Keep raw fields available when requested.
- Include warnings when a mapped field is missing.
- Do not drop unknown fields silently unless output mode excludes raw fields intentionally.

## Implementation Guidance

Use `contracts/normalization_config_contract.yaml` as the template. Treat config as required for normalized queries unless safe defaults are explicitly discovered and validated.

## Autonomy / Approval Boundary

The builder may add optional mapping suggestions, but they must be marked as suggestions and not silently applied to production config.

## Acceptance Criteria

- Config can be validated against schema export.
- Raw items can be normalized into WorkItem objects.
- Missing/invalid mappings generate warnings.
- Normalized output follows the agent JSON contract.
- Tests cover missing fields, lookup fields, dates, and optional raw output.

## Tests Expected

- Valid config test.
- Missing mapped field test.
- Person field normalization test.
- Date parsing test.
- Raw fields inclusion/exclusion test.

## Risks / Watchouts

- SharePoint person fields may have nested structures.
- Lookup values may need ID and display value handling.
- Some fields may be multi-value.

## Do Not Change

- SharePoint schema.
- Raw discovery exports.

## Assumptions

- A human can review and adjust `workboard.yaml` after schema export.

## Completion Standard

Normalization is complete when agent-facing commands can rely on a stable WorkItem model.
