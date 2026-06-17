# Technical Task Brief: T04 Microsoft Graph auth and client

## Task Summary

Implement authentication and a safe Microsoft Graph client wrapper for read-only operations.

## Objective

Enable the CLI to acquire tokens, call Microsoft Graph, handle paging/errors, and avoid exposing secrets or tokens.

## Context

The CLI needs Graph access to resolve SharePoint sites, list lists, list columns, and list items. Auth may be delegated for local users or app-based for agent/tool execution.

## Intent

Centralize Graph behavior so SharePoint commands stay simple, testable, and safe.

## Expected Behavior

Commands should support:

```bash
workboard auth login
workboard auth status
```

Graph wrapper should support:

- GET requests.
- Query parameters.
- Pagination through `@odata.nextLink`.
- Retry/backoff for throttling where practical.
- Actionable error messages.
- Secret/token redaction.

## Current / Actual Behavior

CLI scaffold exists.

## Relevant Files or Areas

- `src/workboard_cli/auth.py`
- `src/workboard_cli/graph_client.py`
- `src/workboard_cli/errors.py`
- `tests/test_graph_client.py`
- `tests/test_auth.py`

## In Scope

- MSAL token acquisition pattern.
- Config/env var loading for tenant ID, client ID, scopes, and auth mode.
- Token cache support if safe for the target environment.
- GET request wrapper.
- Pagination.
- Redaction.
- Mocked tests.

## Out of Scope

- SharePoint-specific business logic.
- Write requests.
- Secret creation or tenant admin setup.

## Constraints

- Do not print access tokens.
- Do not store client secrets in source-controlled config.
- Prefer least privilege.
- Make auth mode explicit.

## Implementation Guidance

Support one auth mode first, then make the design extensible:

- Local delegated mode: public client auth suitable for a human operator.
- Future service mode: confidential client or managed identity, if hosting is later required.

## Autonomy / Approval Boundary

The builder may decide between direct HTTP calls and SDK use. Keep the chosen approach documented.

## Acceptance Criteria

- Auth command exists and fails safely without config.
- Graph GET wrapper can be tested with mocked responses.
- Pagination is implemented and tested.
- Throttling/error responses become actionable CLI errors.
- Tokens and secrets are redacted from logs and exceptions.

## Tests Expected

- Token redaction test.
- Pagination test.
- 401/403 error mapping tests.
- 429 retry or clear failure test.
- Missing configuration test.

## Risks / Watchouts

- MSAL flows differ for public and confidential clients.
- Conditional Access may require interactive flows or admin decisions.
- App-only access may require admin consent and selected permissions.

## Do Not Change

- No SharePoint data writes.
- No broad permission assumptions without documentation.

## Assumptions

- First implementation may use delegated auth for local CLI usability.

## Completion Standard

Auth/client work is complete when SharePoint modules can use a single safe Graph client to make authenticated GET calls.
