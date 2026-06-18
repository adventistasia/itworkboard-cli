# Agent query contract

The agent interface is intentionally constrained. Agents should call approved intents rather than free-form SharePoint search.

## Approved intents

| Intent | Required parameters | Description |
|---|---|---|
| `open_items` | none | Return open WorkBoard items. |
| `overdue_items` | none | Return items with due date before today and not closed. |
| `blocked_items` | none | Return blocked items. |
| `items_by_owner` | `owner` | Return items assigned to or owned by a person. |
| `recently_updated_items` | `days` | Return items updated within the given window. |
| `manager_summary` | none | Return counts and grouped operational summary. |

## JSON envelope

All agent-facing outputs must use this envelope:

```json
{
  "status": "ok",
  "intent": "open_items",
  "source": {
    "system": "sharepoint",
    "siteUrl": "https://southernasiapacific.sharepoint.com/sites/ITWorkboard",
    "listName": "WorkBoard",
    "listId": "optional-discovered-id"
  },
  "retrievedAt": "2026-06-17T00:00:00Z",
  "filters": {},
  "result": {
    "count": 0,
    "items": []
  },
  "warnings": [],
  "errors": []
}
```

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
  "retrievedAt": "2026-06-17T00:00:00Z",
  "filters": {},
  "result": null,
  "warnings": [],
  "errors": [
    {
      "code": "unsupported_intent",
      "message": "The requested intent is not approved for agent use.",
      "action": "Use one of the approved intents."
    }
  ]
}
```

## WorkItem object

```json
{
  "id": "123",
  "title": "Example work item",
  "status": "Open",
  "priority": "High",
  "owner": {
    "displayName": "Example Person",
    "email": "person@example.org"
  },
  "requester": null,
  "department": null,
  "project": null,
  "dueDate": "2026-06-30",
  "createdDate": "2026-06-01T00:00:00Z",
  "modifiedDate": "2026-06-10T00:00:00Z",
  "blockedReason": null,
  "sourceUrl": "https://...",
  "warnings": []
}
```

## Refusal rule

If an agent requests arbitrary SharePoint browsing, write-back, schema changes, or unsupported intent execution, return a safe error instead of trying to comply.
