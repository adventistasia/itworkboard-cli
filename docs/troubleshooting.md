# Troubleshooting

## "Missing credentials"

Set `WORKBOARD_TENANT_ID` and `WORKBOARD_CLIENT_ID` environment variables, or create `config/local.yaml`.

```bash
export WORKBOARD_TENANT_ID="your-tenant-id"
export WORKBOARD_CLIENT_ID="your-client-id"
```

## Authentication fails

- Verify the tenant ID and client ID are correct
- Complete the device code flow within the timeout window
- Admin consent may be required for the `Sites.Read.All` permission

## "List not found"

Run `workboard lists discover` to see all available lists, then check the `primary_list_name` in your config matches the internal name or display name.

## "Resource not found"

Verify the `site_url` in config matches the full SharePoint site URL.

## Rate limited

Microsoft Graph throttles at high request rates. The CLI retries once on 429 responses. Wait and try again.

## Tests fail

```bash
# Ensure dev dependencies are installed
pip install -e ".[dev]"

# Run tests with verbose output
pytest -v
```

## Known limitations

- v1 supports delegated auth only (device code flow)
- No offline/cached queries
- No write-back capability
- Owner matching is case-insensitive substring (display name or email)
