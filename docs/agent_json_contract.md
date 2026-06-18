# Agent JSON contract

## Intended audience

AI agents that call `workboard agent query --intent <name>`. This is the **only** agent-facing interface. Free-form SharePoint browsing is not exposed.

## Approved intents

| Intent | Required params | Description |
|---|---|---|
| `open_items` | none | Items whose stage maps to an open alias |
| `overdue_items` | none | Items with `DateDue` before today and not closed |
| `blocked_items` | none | Items whose stage maps to a blocked alias |
| `items_by_owner` | `--owner <value>` | Items owned by a person (case-insensitive substring match on display name or email) |
| `recently_updated_items` | `--days <n>` | Items modified within the last N days |
| `manager_summary` | none | Aggregated counts: total, by stage, overdue, blocked, by owner |

## Success envelope

```json
{
  "status": "ok",
  "intent": "open_items",
  "source": {
    "system": "sharepoint",
    "siteUrl": "https://southernasiapacific.sharepoint.com/sites/ITWorkboard",
    "listName": "WorkBoard",
    "listId": "57f6d985-7e30-4895-914e-60e73d39e1e0"
  },
  "retrievedAt": "2026-06-18T12:00:00Z",
  "filters": {},
  "result": {
    "count": 0,
    "items": []
  },
  "warnings": [],
  "errors": []
}
```

### Envelope fields

| Field | Type | Description |
|---|---|---|
| `status` | string | `"ok"` or `"error"` |
| `intent` | string | The requested intent name |
| `source.system` | string | Always `"sharepoint"` |
| `source.siteUrl` | string | The SharePoint site URL |
| `source.listName` | string | The primary list name |
| `source.listId` | string | The Graph list ID (omitted if not resolvable) |
| `retrievedAt` | string | ISO 8601 timestamp of data retrieval |
| `filters` | object | Key-value pairs of applied filters (may be empty) |
| `result.count` | integer | Number of items in the result |
| `result.items` | array | Array of WorkItem objects |
| `warnings` | array | Non-blocking warnings (e.g. missing fields) |
| `errors` | array | Blocking errors (should be empty if status is `"ok"`) |

## WorkItem object

```json
{
  "id": "123",
  "title": "Example work item",
  "stage": "Open",
  "deliveryOwner": {
    "displayName": "Example Person",
    "email": "person@example.org"
  },
  "why": "Business justification",
  "dueDate": "2026-06-30",
  "dateCommitted": "2026-06-01",
  "dateStart": "2026-05-15",
  "dateClosed": null,
  "createdDate": "2026-05-01T00:00:00Z",
  "modifiedDate": "2026-06-10T00:00:00Z",
  "stageCategory": "open",
  "sourceUrl": "https://southernasiapacific.sharepoint.com/sites/ITWorkboard/Lists/WorkBoard/DispForm.aspx?ID=123",
  "raw": {},
  "warnings": []
}
```

### WorkItem fields

| Field | From config | Nullable | Notes |
|---|---|---|---|
| `id` | `ID` | no | SharePoint item ID as string |
| `title` | `Title` | no | Display title |
| `stage` | `Stage` | yes | Raw SharePoint value |
| `deliveryOwner` | `DeliveryOwner` | yes | Object with `displayName` and optional `email` |
| `why` | `Why` | yes | Business justification |
| `dueDate` | `DateDue` | yes | ISO date string or null |
| `dateCommitted` | `DateCommitted` | yes | ISO date string or null |
| `dateStart` | `DateStart` | yes | ISO date string or null |
| `dateClosed` | `DateClosed` | yes | ISO date string or null |
| `createdDate` | `Created` | no | ISO 8601 datetime |
| `modifiedDate` | `Modified` | no | ISO 8601 datetime |
| `stageCategory` | computed | no | Derived from stage aliases: `"open"`, `"closed"`, `"blocked"`, or `"unknown"` |
| `sourceUrl` | computed | yes | Direct link to the SharePoint list item |
| `raw` | config | — | Raw SharePoint fields if `include_raw_fields` is true |
| `warnings` | computed | — | List of warning strings for this item |

## Error envelope

```json
{
  "status": "error",
  "intent": "unsupported_intent",
  "source": {
    "system": "sharepoint",
    "siteUrl": "https://southernasiapacific.sharepoint.com/sites/ITWorkboard",
    "listName": "WorkBoard"
  },
  "retrievedAt": "2026-06-18T12:00:00Z",
  "filters": {},
  "result": null,
  "warnings": [],
  "errors": [
    {
      "code": "unsupported_intent",
      "message": "The requested intent is not approved for agent use.",
      "action": "Use one of: open_items, overdue_items, blocked_items, items_by_owner, recently_updated_items, manager_summary"
    }
  ]
}
```

## Refusal rules

1. **Unsupported intent**: Return error envelope with `unsupported_intent`. Do not attempt to approximate.
2. **Missing required parameter**: Return error envelope with `validation_error` listing the missing parameter.
3. **Free-form query**: If the agent asks for something that is not one of the 6 approved intents, refuse. Do not fabricate parameters.
4. **Write request**: Return error envelope with `permission_denied` and message "This CLI is read-only."

## Summary envelope (manager_summary only)

For `manager_summary` intent, `result` contains:

```json
{
  "count": 42,
  "totalItems": 42,
  "byStageCategory": {
    "open": 25,
    "closed": 10,
    "blocked": 5,
    "unknown": 2
  },
  "overdueCount": 3,
  "blockedCount": 5,
  "byOwner": {
    "Person A": { "open": 8, "overdue": 1 },
    "Person B": { "open": 5, "overdue": 0 }
  }
}
```
