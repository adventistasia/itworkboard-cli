# Admin permissions request template

## Request

Grant the WorkBoard CLI read-only access needed to query the IT Workboard SharePoint site and primary WorkBoard list.

## Target

- Site: `https://southernasiapacific.sharepoint.com/sites/ITWorkboard`
- Primary list: `WorkBoard`

## Purpose

The CLI will allow approved users and AI agents to query WorkBoard data through controlled commands and structured outputs.

## Requested access

Preferred approach:

- Least-privilege read access to the target site/list.
- If application permissions are used, prefer selected permissions scoped to the site or list where possible.
- No write permissions for first version.

## Needed operations

- Resolve site metadata.
- List SharePoint lists on the target site.
- Read WorkBoard list schema/columns.
- Read WorkBoard list items and fields.
- Read related supporting lists if required for lookup resolution.

## Not requested

- Write access.
- Schema modification access.
- Tenant-wide SharePoint read access unless no narrower approach is approved.
- Access to unrelated sites.

## Operational safeguards

- CLI will not print tokens or secrets.
- CLI outputs will include source metadata and retrieval timestamps.
- Agent-facing interface will support only approved query intents.
