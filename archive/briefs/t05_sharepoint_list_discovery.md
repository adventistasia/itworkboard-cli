# Technical Task Brief: T05 SharePoint list discovery commands

## Task Summary

Implement read-only SharePoint discovery and item retrieval commands.

## Objective

Enable the CLI to resolve the IT Workboard site, discover lists, export WorkBoard schema, and retrieve WorkBoard items.

## Context

Target site: `https://southernasiapacific.sharepoint.com/sites/ITWorkboard`

Primary list: `WorkBoard`

## Intent

Turn the discovery spike into reusable CLI functionality.

## Expected Behavior

Commands:

```bash
workboard site info --format json
workboard lists discover --format json
workboard schema export --list WorkBoard --output workboard_schema.json
workboard items list --list WorkBoard --limit 10 --format json
workboard items get <id> --list WorkBoard --format json
```

## Current / Actual Behavior

Graph auth/client exists or is in progress.

## Relevant Files or Areas

- `src/workboard_cli/sharepoint.py`
- `src/workboard_cli/schema.py`
- `src/workboard_cli/cli.py`
- `tests/test_sharepoint.py`
- `tests/fixtures/graph/`

## In Scope

- Site resolution from configured URL.
- List discovery.
- WorkBoard list identification.
- Column/schema export.
- List item retrieval with `fields` expansion.
- Optional field selection if supported by config.
- Pagination for lists and items.
- Source metadata in outputs.

## Out of Scope

- Normalized WorkItem mapping.
- Manager summaries.
- Write operations.

## Constraints

- Use read-only Graph calls only.
- No hard-coded field assumptions beyond locating the list by name or URL.
- Return clear 403/404 messages.

## Implementation Guidance

Add data classes or Pydantic models for `SiteInfo`, `SharePointList`, `ColumnInfo`, and raw `ListItem`. Keep raw item retrieval separate from normalized query logic.

## Autonomy / Approval Boundary

The builder may add helper functions, but must not add broad natural-language query behavior here.

## Acceptance Criteria

- Site info command returns site ID/name/web URL.
- List discovery returns list IDs, names, URLs, hidden flag if available, and templates.
- Schema export writes a JSON file with field names, display names, types, lookup hints, and required flags when available.
- Item listing retrieves expanded fields and includes item ID/source URL where available.
- Commands are covered by mocked tests.

## Tests Expected

- Site resolution mock test.
- List discovery mock test.
- Schema export file test.
- Item list pagination test.
- WorkBoard not found test.

## Risks / Watchouts

- Internal field names may not match display names.
- List lookups may need extra Graph calls.
- SharePoint may paginate or throttle.

## Do Not Change

- SharePoint data or schemas.

## Assumptions

- The configured account or app has read access to the target site/list.

## Completion Standard

Discovery commands are complete when a user can export evidence needed for configuration and normalization.
