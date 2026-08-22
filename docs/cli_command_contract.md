# CLI command contract

The binary is `workboard`. Install via `pip install .` and run `workboard --help`.

## Global options

| Option | Env var | Default |
|---|---|---|
| `--config PATH` | — | `config/workboard.defaults.yaml` merged with local overrides |
| `--site-url URL` | `WORKBOARD_SITE_URL` | From config |
| `--format json|markdown` | — | `json` |
| `--verbose` | — | Off |
| `--debug` | — | Off |

## Command tree

### `workboard auth login`

Acquire a token via MSAL device code flow. Prints the browser URL and code, waits for user to authenticate, caches the token in memory for the session.

### `workboard auth status`

Check whether a valid token exists. Returns `{"status": "ok", "authenticated": true}` or `{"status": "ok", "authenticated": false}`.

### `workboard site info`

Resolve and display SharePoint site details.

```json
{
  "status": "ok",
  "source": {
    "system": "sharepoint",
    "siteUrl": "https://southernasiapacific.sharepoint.com/sites/ITWorkboard"
  },
  "result": {
    "id": "southernasiapacific.sharepoint.com,abc-def",
    "displayName": "IT Workboard",
    "webUrl": "https://southernasiapacific.sharepoint.com/sites/ITWorkboard"
  }
}
```

### `workboard lists discover`

Enumerate all lists on the target site.

Output format (JSON):

```json
{
  "status": "ok",
  "source": { "system": "sharepoint", "siteUrl": "..." },
  "retrievedAt": "2026-06-18T00:00:00Z",
  "result": {
    "count": 9,
    "lists": [
      { "id": "...", "displayName": "Work Board", "name": "WorkBoard" }
    ]
  }
}
```

### `workboard schema export --list <name> --output <path>`

Export column schema for a SharePoint list to a JSON file. Prints the path on success.

### `workboard schema drift --baseline <path>`

Detect schema drift against a baseline for work-related lists (WorkBoard, Deliverables, Tasks, WorkIntake, WorkReview, Users). On first run (no baseline), writes the baseline and exits 0. On subsequent runs, prints a drift report and exits 6 if any entry has high severity. Options:
- `--baseline PATH` (default: `discovery/workboard_schema.baseline.json`)
- `--output PATH` (optional, default: stdout)

### `workboard config validate --config <path> --schema <path>`

Validate that the normalization config field names exist in the exported schema. Reports mismatches with field-level detail.

### `workboard items list --list <name> --limit <n>`

List items from a SharePoint list. Default limit is 10.

### `workboard items get <id> --list <name>`

Get a single item by its SharePoint item ID.

**Primary WorkBoard list** — when the resolved list matches the configured primary list, the response includes both the unchanged raw Graph item and the authoritative WorkItem:

```json
{
  "status": "ok",
  "source": {
    "system": "sharepoint",
    "siteUrl": "...",
    "listName": "WorkBoard",
    "listId": "..."
  },
  "retrievedAt": "2026-08-21T00:00:00Z",
  "sessionId": "...",
  "result": {
    "item": { "..." },
    "workItem": {
      "id": "123",
      "title": "...",
      "scopeText": "...",
      "requirementsText": "...",
      "...": "..."
    }
  }
}
```

`result.item` is the unchanged raw Graph item. `result.workItem` is the normalized WorkItem (see `docs/agent_json_contract.md`). No opt-in flag is required.

**Custom or non-WorkBoard list** — the response includes only the raw item:

```json
{
  "status": "ok",
  "result": {
    "item": { "..." }
  }
}
```

**Not found** — returns the existing structured resource-not-found error without any partial `result.item` or `result.workItem`.

`items get` is a general read-only CLI command and is **not** an approved agent-facing interface. Official AI-agent access remains `workboard agent query --intent <name>`.

### `workboard query open`

Return items whose stage/status maps to an open alias.

### `workboard query overdue`

Return items whose `DateDue` is before today and whose stage is not closed.

### `workboard query by-owner --owner "<name>"`

Return items owned by the given person. Matching is case-insensitive substring.

### `workboard query blocked`

Return items whose stage/status maps to a blocked alias.

### `workboard query recently-updated --days <n>`

Return items modified within the last N days.

### `workboard summary manager`

Return a markdown summary with counts, overdue counts, blocked counts, and owner groupings.

### `workboard agent query --intent <name>`

The only agent-facing entry point. Validates intent against the approved list:
- `open_items`
- `overdue_items`
- `blocked_items`
- `items_by_owner` (requires `--owner`)
- `recently_updated_items` (requires `--days`)
- `manager_summary`
- `new_items` (requires `--days`)
- `recently_completed_items` (requires `--days`)
- `cycle_time_stats` (optional `--group-by owner|stage`, default `owner`)
- `items_by_project` (requires `--project`)
- `items_by_stage` (requires `--stage`)
- `items_by_decision_authority` (requires `--person`)

Returns the standard JSON agent envelope. See `docs/agent_json_contract.md`.

## Error output shape

```json
{
  "status": "error",
  "error": {
    "code": "permission_denied",
    "message": "Read access to the WorkBoard list was denied.",
    "action": "Ask an administrator to grant read access to the app or user."
  }
}
```

| Field | Required | Type | Description |
|---|---|---|---|
| `status` | yes | string | Always `"error"` |
| `error.code` | yes | string | Machine-readable error code from the taxonomy |
| `error.message` | yes | string | Human-readable description |
| `error.action` | yes | string | Suggested next step for the user |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | CLI usage or validation error |
| 2 | Authentication error |
| 3 | API / Graph error |
| 4 | Config error |
| 5 | Network error |
| 6 | Schema drift detected (high severity) |
