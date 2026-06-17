# Technical Task Brief: T02 Architecture and contracts

## Task Summary

Design the CLI architecture and contracts based on discovery output.

## Objective

Produce architecture decisions, command contracts, JSON output contracts, error-handling rules, and configuration conventions before implementation expands.

## Context

The CLI will be the controlled boundary between SharePoint WorkBoard data and AI agents. It must be safer and more deterministic than letting agents browse SharePoint directly.

## Intent

Prevent downstream build drift. Builders should know exactly what commands to implement, what outputs look like, what errors mean, and how schema mapping works.

## Expected Behavior

Produce or update:

```text
docs/architecture.md
docs/cli_command_contract.md
docs/agent_json_contract.md
config/workboard.example.yaml
```

## Current / Actual Behavior

Discovery output exists or must be explicitly marked as missing.

## Relevant Files or Areas

- CLI entrypoint
- Auth module
- Graph client module
- SharePoint discovery module
- Normalization/config module
- Output formatting module
- Query command module

## In Scope

- Architecture decision record.
- Module boundaries.
- Command list.
- JSON envelope contract.
- Markdown summary rules.
- Error categories.
- Logging rules.
- Configuration schema.
- Permission model.

## Out of Scope

- Full implementation of all commands.
- SharePoint writes.
- Hosted API service.

## Constraints

- Read-only first version.
- Configurable schema mapping.
- No hard-coded secrets.
- Agent outputs must be stable and machine-readable.
- Human outputs must be concise and source-aware.

## Implementation Guidance

Prefer simple, explicit architecture:

```text
cli.py -> command routing
auth.py -> token acquisition only
graph_client.py -> HTTP/Graph wrapper
sharepoint.py -> site/list/item operations
schema.py -> schema export and lookup metadata
normalize.py -> SharePoint fields to WorkItem model
queries.py -> operational filters and sorting
summaries.py -> markdown summaries
output.py -> JSON and markdown envelopes
config.py -> configuration loading and validation
```

## Autonomy / Approval Boundary

The builder may choose libraries within the default stack. Changing language/runtime requires an explicit architecture note explaining why.

## Acceptance Criteria

- Commands are named and scoped.
- JSON output envelope is defined.
- WorkItem normalized model is defined.
- Config file structure is defined.
- Permission strategy is documented.
- Error taxonomy is documented.
- Audit can verify that agents cannot get arbitrary SharePoint access through the CLI.

## Tests Expected

- Contract tests for JSON envelope shape.
- Config validation tests.
- Error mapping tests.

## Risks / Watchouts

- Overengineering natural-language query support before structured commands exist.
- Hard-coding discovered field names in code rather than config.
- Failing to include source metadata.

## Do Not Change

- Discovery evidence.
- SharePoint data.

## Assumptions

- Python remains acceptable unless a strong reason emerges.

## Completion Standard

Architecture is complete when implementation agents can build modules and commands without inventing contracts.
