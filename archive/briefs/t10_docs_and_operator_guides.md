# Technical Task Brief: T10 Documentation and operator guides

## Task Summary

Create the documentation required for installation, configuration, administration, team usage, manager usage, and agent integration.

## Objective

Make the CLI usable by someone who did not build it.

## Context

The final CLI will support WorkBoard discovery, querying, summaries, and agent-safe JSON output.

## Intent

Close the gap between working code and usable tool.

## Expected Behavior

Documentation should include:

```text
README.md
docs/admin_permissions.md
docs/configuration.md
docs/manager_usage.md
docs/agent_usage.md
docs/troubleshooting.md
docs/security_model.md
```

## Current / Actual Behavior

Implementation is mostly complete.

## Relevant Files or Areas

- `README.md`
- `docs/`
- `config/workboard.example.yaml`

## In Scope

- Install instructions.
- Required Python version.
- Auth/config setup.
- Required Graph permissions.
- Site/list target defaults.
- Schema export workflow.
- Config mapping workflow.
- Command examples.
- Agent usage examples.
- Troubleshooting.
- Known limitations.

## Out of Scope

- End-user training deck.
- Hosted service runbook.
- Write-back process documentation.

## Constraints

- Do not include secrets.
- Do not include sensitive sample WorkBoard data.
- Keep docs specific enough for the IT Workboard target.

## Implementation Guidance

Use concrete commands. Separate admin setup from normal user usage.

Target defaults:

```text
Site: https://southernasiapacific.sharepoint.com/sites/ITWorkboard
Primary list: WorkBoard
```

## Autonomy / Approval Boundary

The builder may add additional docs if they improve operational adoption.

## Acceptance Criteria

- A new user can install and run `workboard --help`.
- An admin can understand required permissions.
- A manager can run a summary command.
- An AI-agent orchestrator can understand approved intents.
- Known limitations are listed.

## Tests Expected

- Docs command examples should match actual CLI commands.
- Links and filenames should be checked for consistency.

## Risks / Watchouts

- Docs becoming generic and not tied to this WorkBoard use case.
- Permission setup being vague.

## Do Not Change

- CLI behavior unless documentation exposes a mismatch that must be fixed.

## Assumptions

- The organization will decide final authentication mode.

## Completion Standard

Docs are complete when the final audit can install, configure, test, and use the CLI from the documentation alone.
