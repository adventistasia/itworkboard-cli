# CLI command contract

The CLI executable name should be `workboard`.

## Required commands

```bash
workboard --help
workboard --version
workboard auth login
workboard auth status
workboard site info --format json
workboard lists discover --format json
workboard schema export --list WorkBoard --output workboard_schema.json
workboard config validate --config config/workboard.yaml --schema workboard_schema.json
workboard items list --list WorkBoard --limit 10 --format json
workboard items get <id> --list WorkBoard --format json
workboard query open --format json
workboard query overdue --format json
workboard query by-owner --owner "<name>" --format json
workboard query blocked --format json
workboard query recently-updated --days 7 --format json
workboard summary manager --format markdown
workboard agent query --intent open_items --format json
```

## Optional commands

```bash
workboard relationships map --format json
workboard schema suggest-config --schema workboard_schema.json --output config/workboard.suggested.yaml
```

## Global options

```text
--config PATH
--site-url URL
--format json|markdown
--verbose
--no-cache
```

## Error behavior

Errors should be actionable and should not expose tokens or secrets.

Machine-readable error output should include:

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
