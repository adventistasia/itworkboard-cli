# Configuration

## File structure

```
config/
  workboard.defaults.yaml    # Defaults — committed, shared
  workboard.example.yaml     # User-facing example
  local.yaml                 # Local overrides — gitignored
```

## Field mapping

The `fields` section maps normalized field names to SharePoint column names:

```yaml
fields:
  title: "Title"
  stage: "Stage"
  delivery_owner: "DeliveryOwner"
  why: "Why"
  date_due: "DateDue"
  date_committed: "DateCommitted"
  date_start: "DateStart"
  date_closed: "DateClosed"
```

## Stage aliases

Maps raw SharePoint status values to stage categories:

```yaml
stage_aliases:
  open:
    - "Open"
    - "In Progress"
    - "New"
  closed:
    - "Closed"
    - "Done"
    - "Completed"
    - "Cancelled"
  blocked:
    - "Blocked"
    - "On Hold"
```

## Schema validation workflow

```bash
# 1. Export current schema
workboard schema export --list WorkBoard --output workboard_schema.json

# 2. Verify config mappings
workboard config validate --config config/local.yaml --schema workboard_schema.json
```

## Environment variable overrides

| Variable | Overrides |
|---|---|
| `WORKBOARD_TENANT_ID` | `tenant_id` |
| `WORKBOARD_CLIENT_ID` | `client_id` |
| `WORKBOARD_SITE_URL` | `site_url` |
| `WORKBOARD_LIST_NAME` | `primary_list_name` |
