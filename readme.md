# SharePoint WorkBoard CLI execution package

This package is designed for an orchestrator agent that can delegate implementation work to builder and auditor subagents.

The final output of completing the package should be a usable read-only CLI for querying the IT Workboard SharePoint list and exposing safe, structured outputs for AI agents.

## Target system

- SharePoint site: `https://southernasiapacific.sharepoint.com/sites/ITWorkboard`
- Primary list: `https://southernasiapacific.sharepoint.com/sites/ITWorkboard/Lists/WorkBoard`
- Primary purpose: make the IT Workboard queryable by AI agents and useful to team members and workboard managers.

## Recommended use

Use the decomposed mode. The WorkBoard schema and related lists are not yet known, so the discovery phase should run before implementation choices become final.

1. Give the orchestrator agent `00_orchestrator_master_prompt.md`.
2. Give it `manifest.json`.
3. Give it the relevant brief from `briefs/` for the current phase.
4. After each build phase, give the matching audit brief from `audit_briefs/` to an auditor subagent.
5. Do not proceed past a failed audit unless the builder fixes the issue and the auditor passes it.
6. Treat the final acceptance audit as the release gate.

## One-shot use

If the orchestrator can ingest the whole package, give it the entire folder and this instruction:

```text
Execute the work in manifest order. Use builder subagents for build tasks and auditor subagents for audit gates. Do not skip discovery. Do not write to SharePoint. The final result must be an installable, tested, documented CLI that can authenticate, discover the IT Workboard list, export schema, retrieve items, normalize fields through configuration, and provide agent-safe JSON outputs.
```

## Decomposed use

Use this sequence:

1. `briefs/t01_discovery_spike.md`
2. `audit_briefs/a01_discovery_audit.md`
3. `briefs/t02_architecture_and_contracts.md`
4. `audit_briefs/a02_architecture_and_security_audit.md`
5. `briefs/t03_cli_scaffold.md`
6. `briefs/t04_graph_auth_and_client.md`
7. `briefs/t05_sharepoint_list_discovery.md`
8. `audit_briefs/a03_implementation_audit.md`
9. `briefs/t06_schema_mapping_and_normalization.md`
10. `briefs/t07_query_commands_and_summaries.md`
11. `briefs/t08_agent_interface_and_json_contract.md`
12. `briefs/t09_tests_and_ci.md`
13. `briefs/t10_docs_and_operator_guides.md`
14. `audit_briefs/a04_final_cli_acceptance_audit.md`

## Assumed default stack

The briefs assume Python unless the orchestrator identifies a strong reason to change.

Recommended stack:

- Python 3.11+
- Typer or Click for CLI
- MSAL for authentication
- Requests or Microsoft Graph SDK for Graph calls
- Pydantic for data validation
- Pytest for tests
- Ruff for linting

## Non-negotiable boundaries

- First usable CLI is read-only.
- No SharePoint writes.
- No schema changes.
- No hard-coded secrets.
- No uncontrolled agent access to the SharePoint site.
- Output must include source metadata and retrieval timestamp.
- Missing schema details must be discovered and documented, not guessed silently.
