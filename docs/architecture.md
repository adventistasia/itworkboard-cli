# Architecture — IT WorkBoard CLI

## Status

Accepted (2026-06-18). Architecture decisions are binding for builder subagents (T03–T10).

## Context

The WorkBoard CLI is a read-only boundary between SharePoint WorkBoard data and AI agents. It must be more deterministic and safer than letting agents browse SharePoint directly.

## Decisions

### 1. Language and runtime

**Python 3.11+** with Typer CLI framework. MSAL for auth, `requests` for HTTP, Pydantic v2+ for validation, `pyyaml` for config, `pytest` for tests, `ruff` for linting.

Rationale: Team familiarity, existing discovery spike already uses this stack, lightweight dependency footprint.

### 2. Module boundaries

| Module | Responsibility |
|---|---|
| `cli.py` | Typer app, command groups, global options, help text |
| `auth.py` | MSAL device code flow — token acquisition only, no Graph logic |
| `graph_client.py` | `requests` wrapper — HTTP to Microsoft Graph, pagination, error translation |
| `sharepoint.py` | Site resolution, list enumeration, item CRUD (read-only), column discovery |
| `schema.py` | SharePoint column metadata → structured schema export |
| `normalize.py` | Raw SharePoint fields → Pydantic `WorkItem` model using config-driven mapping |
| `queries.py` | In-memory filter/sort over `WorkItem` list — open, overdue, by-owner, blocked, recent |
| `summaries.py` | `WorkItem[]` → aggregated markdown summary (counts, groupings, dates) |
| `output.py` | `WorkItem[]` → JSON envelope or markdown rendering, handles both agent and human paths |
| `config.py` | YAML + env var loading, deep merge defaults with overrides, validation |
| `errors.py` | Structured `WorkboardError` hierarchy with code, message, action fields |

### 3. Data flow

```
CLI input → cli.py routes command
         → config.py loads config (defaults + local override + env vars)
         → auth.py acquires token via MSAL device code flow
         → graph_client.py wraps Graph API calls with pagination
         → sharepoint.py resolves site/lists/items
         → schema.py (if export command) outputs raw schema JSON
         → normalize.py maps SharePoint fields → WorkItem using config
         → queries.py filters WorkItem list by intent
         → summaries.py (if summary command) aggregates markdown
         → output.py wraps WorkItem[] in JSON envelope or renders markdown
```

All commands pass through this pipeline. No command skips the normalize → output path for agent outputs.

### 4. Error taxonomy

All errors are structured as `WorkboardError` with three fields:

| Error code | Meaning |
|---|---|
| `auth_error` | Token acquisition failed (user cancelled, wrong tenant, expired) |
| `permission_denied` | Authenticated but Graph returned 403 |
| `resource_not_found` | Site, list, or item not found (404) |
| `validation_error` | Invalid CLI arguments or config |
| `unsupported_intent` | Agent requested an unapproved intent |
| `graph_api_error` | Graph returned unexpected error (5xx, 429) |
| `config_error` | Config file missing, malformed, or missing required fields |
| `network_error` | Connection refused, DNS failure, timeout |

### 5. Permission model

- **Auth flow**: MSAL device code flow (delegated user auth)
- **Graph scope**: `Sites.Read.All` (least privilege for reading SharePoint lists across a known site)
- **No app-only flow** in v1 — all requests are on behalf of an authenticated user
- **No write scopes** requested or used

### 6. Logging

- Standard `logging` module with `WARNING` default level
- `--verbose` flag sets `INFO`; `--debug` sets `DEBUG`
- No secrets, tokens, or Graph response bodies logged at INFO/WARNING
- DEBUG may log sanitized request/response details (token redacted)

### 7. Agent security boundary

The `agent query --intent <name>` command is the **only** agent-facing entry point. It:
1. Validates the intent against an allowlist of 6 approved intents
2. Returns a safe error for unapproved intents
3. Always includes `source` and `retrievedAt` metadata
4. Exposes no free-form SharePoint browsing capability

## Module dependency graph

```
cli.py
  ├── config.py (config loading)
  ├── auth.py (token acquisition)
  ├── sharepoint.py (site/list ops, uses graph_client)
  ├── schema.py (schema export, uses graph_client)
  ├── queries.py (in-memory filtering)
  ├── summaries.py (aggregation)
  ├── output.py (JSON/markdown rendering)
  └── errors.py (structured errors)

graph_client.py ← auth.py (gets token)
sharepoint.py ← graph_client.py
schema.py ← graph_client.py
normalize.py ← config.py (field mapping)
queries.py ← normalize.py (WorkItem[])
summaries.py ← queries.py (WorkItem[])
output.py ← errors.py (WorkboardError)
```

## Open questions

- Whether to cache tokens to disk (MSAL token cache is not yet wired)
- Whether `by-owner` should match display name, email, or both
