# Security model

## Authentication

- **Flow**: MSAL device code flow (delegated user auth)
- **Scope**: `Sites.Read.All` (Microsoft Graph)
- **Token cache**: In-memory only, per session
- **No app-only flow** in v1

## Least privilege

- `Sites.Read.All` is the minimum scope needed to read SharePoint lists
- No write scopes (`Sites.ReadWrite.All`, `Files.ReadWrite.All`, etc.) are ever requested
- Access is on behalf of the authenticated user, not a service principal

## Data protection

- Tokens are never written to disk
- Tokens never appear in logs, error messages, or CLI output
- Secrets are redacted from debug output and exception messages
- API error responses are truncated to 500 characters

## Agent safety

- `agent query` is the only agent-facing command
- Intent validation happens before any Graph call
- Unsolicited browsing, write-back, and schema changes are blocked at the CLI layer

## Configuration safety

- Credentials go in `config/local.yaml` (gitignored) or environment variables
- `config/workboard.defaults.yaml` contains no secrets
- Config validation catches mismatched field names before runtime
