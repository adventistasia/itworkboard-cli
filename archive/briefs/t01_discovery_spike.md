# Technical Task Brief: T01 Discovery spike

## Task Summary

Build the smallest read-only discovery spike needed to understand the IT Workboard SharePoint site, list inventory, primary WorkBoard list, fields, and permission gaps.

## Objective

Produce evidence that the CLI can authenticate, resolve the target site, identify the primary WorkBoard list, export schema metadata, and retrieve a small sample of items if permissions allow.

## Context

The primary list is expected at `https://southernasiapacific.sharepoint.com/sites/ITWorkboard/Lists/WorkBoard`. Supporting lists are unknown and must be discovered rather than guessed.

## Intent

Reduce implementation risk before building query logic. The orchestrator must not hard-code field names or relationships until discovery output exists.

## Expected Behavior

The spike should produce local JSON files such as:

```text
discovery/site.json
discovery/lists.json
discovery/workboard_schema.json
discovery/workboard_sample_items.json
discovery/permission_report.md
```

## Current / Actual Behavior

No repository or CLI is assumed to exist yet.

## Relevant Files or Areas

Create temporary spike code or the initial CLI scaffold if useful. Keep outputs in a `discovery/` directory.

## In Scope

- Auth configuration notes.
- Site resolution.
- List discovery.
- WorkBoard list identification.
- Field/schema export.
- Sample item retrieval with expanded fields.
- Permission error reporting.
- Related-list candidates based on lookup fields or list names.

## Out of Scope

- Writing to SharePoint.
- Final query commands.
- UI work.
- Automated schema mapping decisions.

## Constraints

- Use read-only Graph calls only.
- Do not log tokens.
- Do not commit tenant secrets or client secrets.
- If permissions are missing, document the exact failing operation and needed permission.

## Implementation Guidance

Use Microsoft Graph endpoints for site/list/list-item discovery. The implementation may call Graph directly through HTTP or through a Microsoft Graph SDK. Prefer clear wrapper functions even in the spike, because the code may be reused.

Minimum operations:

```text
GET /sites/{hostname}:/sites/ITWorkboard
GET /sites/{site-id}/lists
GET /sites/{site-id}/lists/{list-id}/columns
GET /sites/{site-id}/lists/{list-id}/items?expand=fields&$top=10
```

## Autonomy / Approval Boundary

The builder may create local files and mock fixtures. The builder must not request write permissions or mutate SharePoint data.

## Acceptance Criteria

- Site resolution result is captured.
- List inventory is captured or permission failure is documented.
- WorkBoard list is identified by name, URL, or explicit failure evidence.
- Schema/columns are exported if accessible.
- Sample items are exported if accessible.
- A permission report explains any required Entra ID consent or SharePoint selected permission assignment.

## Tests Expected

- Test that discovery output writer redacts tokens and secrets.
- Test that Graph errors are converted into actionable messages.
- Test that paginated list results can be accumulated.

## Risks / Watchouts

- WorkBoard may have display names different from internal field names.
- Lookup fields may require additional calls to understand supporting lists.
- Large lists may require indexed filters or pagination.

## Do Not Change

- SharePoint data.
- SharePoint list schemas.
- Tenant permissions.

## Assumptions

- A human can supply app registration details or delegated auth credentials.
- The first phase may end with a permission gap rather than complete data.

## Completion Standard

Discovery is complete when the next architecture phase has enough evidence to design concrete commands, data mappings, and permission requirements.
