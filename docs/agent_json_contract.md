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
| `new_items` | `--days <n>` | Items created within the last N days |
| `recently_completed_items` | `--days <n>` | Items closed (dateClosed populated) within the last N days |
| `cycle_time_stats` | `--group-by owner\|stage` (default `owner`) | Aggregate cycle time stats by owner or stage; returns summary envelope |
| `items_by_project` | `--project <value>` | Items whose relProject.text matches (case-insensitive substring) |
| `items_by_stage` | `--stage <value>` | Items whose raw stage matches (case-insensitive exact match) |
| `items_by_decision_authority` | `--person <value>` | Items whose decisionAuthority.displayName matches (case-insensitive substring) |

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
    "email": "person@example.org",
    "id": "c1520444-..."
  },
  "decisionAuthority": {
    "displayName": "Decision Maker",
    "email": "decision@example.org",
    "id": "d1234567-..."
  },
  "acceptanceAuthority": {
    "displayName": "Acceptance Holder",
    "email": "accept@example.org",
    "id": "a1234567-..."
  },
  "why": "Business justification",
  "dueDate": "2026-06-30",
  "dateCommitted": "2026-06-01",
  "dateStart": "2026-05-15",
  "dateClosed": null,
  "createdDate": "2026-05-01T00:00:00Z",
  "modifiedDate": "2026-06-10T00:00:00Z",
  "stageCategory": "open",
  "cycleTimeDays": 8,
  "cycleTimeAnomaly": false,
  "relProject": {"id": 3, "text": "Retirement System"},
  "workBriefLinks": [{"url": "https://...", "text": "Doc Name"}],
  "whyText": "Plain text from Why field",
  "scheduleText": "Plain text from Schedule field",
  "acceptanceCriteriaText": "Plain text from AcceptanceCriteria field",
  "deliverablesText": "Plain text from Deliverables field",
  "workIntake": [{"lookupId": null, "lookupValue": "Item Name"}],
  "description": "Plain text description",
  "priorityStatus": "High",
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
| `deliveryOwner` | `DeliveryOwner` | yes | Object with `displayName`, `email`, and `id` (all nullable except `displayName`) |
| `decisionAuthority` | `DecisionAuthority` | yes | Same shape as `deliveryOwner` |
| `acceptanceAuthority` | `AcceptanceAuthority` | yes | Same shape as `deliveryOwner` |
| `why` | `Why` | yes | Business justification |
| `dueDate` | `DateDue` | yes | ISO date string or null |
| `dateCommitted` | `DateCommitted` | yes | ISO date string or null |
| `dateStart` | `DateStart` | yes | ISO date string or null |
| `dateClosed` | `DateClosed` | yes | ISO date string or null |
| `createdDate` | `Created` | no | ISO 8601 datetime |
| `modifiedDate` | `Modified` | no | ISO 8601 datetime |
| `stageCategory` | computed | no | Derived from stage aliases: `"open"`, `"closed"`, `"blocked"`, or `"unknown"` |
| `cycleTimeDays` | `CycleTime` | yes | Parsed integer days, null when missing or anomalous |
| `cycleTimeAnomaly` | computed | no | `true` when CycleTime value is non-integer or negative |
| `relProject` | `RelProject` | yes | Parsed `{"id": int, "text": str}` or null |
| `workBriefLinks` | `RelWorkBrief` | no | Array of `{"url": str, "text": str}` from HTML `<a>` tags |
| `whyText` | `Why` (computed) | no | Plain-text extraction of HTML `Why` field |
| `scheduleText` | `Schedule` (computed) | no | Plain-text extraction of HTML `Schedule` field |
| `acceptanceCriteriaText` | `AcceptanceCriteria` (computed) | no | Plain-text extraction of HTML field |
| `deliverablesText` | `Deliverables` (computed) | no | Plain-text extraction of HTML field |
| `workIntake` | `WorkIntake` | yes | Array of `{"lookupId": int\|null, "lookupValue": str}` or null |
| `description` | `Description` | yes | Plain text description |
| `priorityStatus` | `PriorityStatus` | yes | Priority status string |
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
3. **Free-form query**: If the agent asks for something that is not one of the 12 approved intents, refuse. Do not fabricate parameters.
4. **Write request**: Return error envelope with `permission_denied` and message "This CLI is read-only."

## Summary envelope (manager_summary, cycle_time_stats)

For `manager_summary` and `cycle_time_stats` intents, `result` contains aggregated data.

### manager_summary result

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

### cycle_time_stats result

```json
{
  "total_items": 43,
  "valid_count": 38,
  "bogus_count": 5,
  "groups": {
    "Alice Smith": {
      "median_days": 8,
      "p95_days": 15,
      "count": 12
    },
    "Bob Jones": {
      "median_days": 5,
      "p95_days": 10,
      "count": 8
    }
  }
}
```

## Schema drift envelope (workboard schema drift)

The `workboard schema drift` command outputs two envelope shapes:

### First run (baseline established)

```json
{
  "status": "ok",
  "baseline_established": true,
  "lists": ["WorkBoard", "Deliverables", "Tasks", "WorkIntake", "WorkReview", "Users"],
  "source": {"system": "workboard-cli", "siteUrl": "https://..."},
  "retrievedAt": "2026-08-19T00:00:00Z",
  "sessionId": "..."
}
```

### Subsequent run (drift detected)

```json
{
  "status": "ok",
  "drift": [
    {
      "list": "WorkBoard",
      "changeType": "column_added",
      "severity": "low",
      "column": "NewColumn",
      "note": "Column 'NewColumn' added to 'WorkBoard'."
    }
  ],
  "summary": {"high": 0, "medium": 0, "low": 1},
  "source": {"system": "workboard-cli", "siteUrl": "https://..."},
  "retrievedAt": "2026-08-19T00:00:00Z",
  "sessionId": "..."
}
```

Exit code 6 is returned when any drift entry has severity `"high"`.
