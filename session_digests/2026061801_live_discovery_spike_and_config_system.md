---
lorespec: "0.1"
id: "2026061801"
date: "2026-06-18"
source: "opencode"
topic: "Live SharePoint discovery spike and config system architecture"
tags: [sharepoint, graph-api, msal, config, discovery, azure-ad, python]
classification:
  type: technical
  secondary_type: strategy
  domains: [sharepoint-integration, cli-tooling, python-engineering]
  value: high
trails: [workboard-cli-discovery, workboard-cli-config]
---

## Session Arc

### Started
User was going through the Azure AD app registration checklist (prerequisites/azure_app_reg_checklist.md) and reached step 5 — "Run discovery" via `python -m workboard_cli.discovery_spike` — but the module didn't exist yet because prior T01 work was rolled back for using mock data.

### Pivots
- **Mock data → live data**: Previous session's T01 was rolled back because builder output used mock data instead of real SharePoint discovery. This session started fresh with actual credentials.
- **Env vars → config files**: User asked where to store credentials. Evolved from "just env vars" to a config file approach with gitignored local credentials.
- **Single config → split config**: User suggested separating credentials from field defaults, leading to a two-file architecture (defaults.yaml committed + local.yaml gitignored).
- **Naming evolution**: `config/workboard.yaml` → `config/secrets.yaml` → `config/local.yaml`, each refining the semantic purpose.
- **4 env vars**: Expanded from 2 (TENANT_ID, CLIENT_ID) to 4 (adding SITE_URL, LIST_NAME) and documented them in the defaults file header.
- **ID exposure → amend commit**: After committing, user flagged that tenant/client IDs were in the checklist file. Amended the commit to replace them with placeholders.

### Ended
All changes committed (amended): discovery spike code, config system, real discovery data (5 output files), updated MEMORY.md and checklist. No remote configured — commit is local-only on `main`.

---

## ARTIFACTS

### A1 — Discovery spike Python package

**Location**: `src/workboard_cli/`

Three modules that form the read-only SharePoint discovery pipeline:

- **`auth.py`** — MSAL PublicClientApplication device code flow. Calls `initiate_device_flow` with `Sites.Read.All` scope, prints verification URI and user code, then acquires token. Falls back to `config.py` for credentials if not passed directly.
- **`graph_client.py`** — Lightweight wrapper around `requests.Session`. Two methods: `get()` for single requests and `get_all()` for paginated results (follows `@odata.nextLink`). Raises `RuntimeError` with status code and response body on errors.
- **`discovery_spike.py`** — Orchestrator that runs 5 steps: resolve site, enumerate lists, find WorkBoard by name, export column schema (43 columns), retrieve sample items (30 items). Writes results to `discovery/` as JSON + markdown report. Parses `site_url` from config to derive hostname and path for Graph API.

Config-driven: list name, site URL, and credentials all come from `load_config()` instead of hard-coded constants.

**Evolution**: Previous T01 scaffold was rolled back for using mock data. This version runs against real SharePoint and produced verified output.

### A2 — Config system

**Location**: `src/workboard_cli/config.py`, `config/`

Two-layer config with env var override:

```
config/workboard.defaults.yaml  (committed — team defaults)
config/local.yaml               (gitignored — local overrides)
env vars                        (highest precedence)
```

**Default config** (`config/workboard.defaults.yaml`):
- `site_url`, `primary_list_name`
- 26 field mappings (normalized names → SharePoint internal field names)
- Stage aliases for open/closed/blocked
- Output settings, query defaults

**Local override** (`config/local.yaml`): Only `tenant_id` and `client_id` in current state. Can override any key from defaults.

**Config loader** (`config.py`): Uses `_deep_merge()` for nested dicts (so partial local overrides don't wipe full nested structures). Searches `config/local.yaml` → `~/.config/workboard/local.yaml` → `~/.workboard.yaml`.

**4 supported env vars**: `WORKBOARD_TENANT_ID`, `WORKBOARD_CLIENT_ID`, `WORKBOARD_SITE_URL`, `WORKBOARD_LIST_NAME`.

### A3 — Discovery output data

**Location**: `discovery/`

Five files from live SharePoint:

| File | Size | Content |
|------|------|---------|
| `site.json` | 574 B | Resolved site metadata |
| `lists.json` | 9.8 KB | 9 lists: Users, Deliverables, Work Board, EventLog, WorkIntake, Web Template Extensions, Hosted App Configs, Work Review, Documents |
| `discovery/workboard_schema.json` | 19.2 KB | 43 column definitions |
| `workboard_sample_items.json` | 225 KB | 30 items with expanded fields |
| `permission_report.md` | 892 B | Full inventory report |

### A4 — Updated MEMORY.md

**Location**: `MEMORY.md`

State table updated to reflect current phase (discovery complete, A01 passed), decisions about config approach, and next step (T02 architecture and contracts). Session 3 log documents all files created, discovery findings, and decisions.

---

## DECISIONS

### D1 — Split config into defaults.yaml + local.yaml

- **Decision**: Store team-shared config (field mappings, aliases, site URL) in committed `config/workboard.defaults.yaml` and git-ignored per-user overrides (credentials, test config) in `config/local.yaml`.
- **Issue**: Where should tenant/client IDs and site-specific config live without leaking secrets into version control or duplicating configuration?
- **Positions**:
  1. Single `config.yaml` with placeholders + env vars only
  2. Two files: one committed defaults, one gitignored local overrides
  3. All config in env vars only
- **Arguments**: Position 2 won because (a) field mappings and aliases are team-shared and should be version-controlled, (b) tenant/client IDs are per-user and should never be committed, (c) env vars are good for CI but verbose for daily use.
- **Warrant**: Every developer needs the same field normalization config but different credentials. Splitting lets the team converge on one defaults file while keeping secrets local.
- **Qualifier**: always
- **Status**: settled

### D2 — Expand env vars from 2 to 4

- **Decision**: Support `WORKBOARD_SITE_URL` and `WORKBOARD_LIST_NAME` in addition to the existing `WORKBOARD_TENANT_ID` and `WORKBOARD_CLIENT_ID`.
- **Issue**: The defaults file documented 4 env vars but only 2 were wired in `config.py`.
- **Positions**: 1) Document only what exists, 2) Wire all 4 for CI/test flexibility.
- **Arguments**: Position 2 adds minimal code and makes CI/CD or test environments fully configurable without any config files. The cost is one extra `os.environ.get()` call per config key.
- **Warrant**: Env vars are the standard mechanism for CI and containerized runs; half-baked support creates friction.
- **Qualifier**: always
- **Status**: settled

### D3 — Keep sample items with embedded tenantId

- **Decision**: Keep `discovery/workboard_sample_items.json` in the commit even though the `RelWorkBrief` rich text fields contain `tenantId=918af52d-...` in Teams/SharePoint URLs.
- **Issue**: The tenant ID appears 2x in sample item data — inside SharePoint-generated URLs in the `RelWorkBrief` field. Is this a credential leak?
- **Positions**: 1) Remove the file from git to be safe, 2) Keep it — the tenant ID in SharePoint content URLs is not a credential.
- **Arguments**: Tenant IDs in SharePoint data URLs are functional identifiers, not secrets. Removing the file loses the sample data that the architecture phase depends on. The checklist (which had the IDs in plain text) was the real concern.
- **Warrant**: A tenant ID in a content URL is equivalent to a server hostname — it's a routing parameter, not an authentication secret.
- **Qualifier**: usually
- **Status**: settled

---

## INSIGHTS

### I1 — WorkBoard list has a display-name discrepancy

The list displays as "Work Board" (with a space) in SharePoint but the internal name is `WorkBoard` (no space). Queries should match on internal name to avoid ambiguity. The discovery code matches on both `displayName` and `name` fields.

**Source**: Discovery output — `lists.json` shows `displayName: "Work Board"`, `name: "WorkBoard"`.

### I2 — Device code flow requires no client secret

MSAL device code flow uses `PublicClientApplication` which does not require a client secret. Only `tenant_id` and `client_id` (application ID) are needed. This means the "secrets" file (`config/local.yaml`) contains identifiers, not actual secrets. No refresh token rotation or secret management is needed.

**Source**: Auth setup in `src/workboard_cli/auth.py`, confirmed by MSAL docs referenced in `sources.md`.

### I3 — WorkBoard site has 9 lists and 43 columns

The IT Workboard site at `southernasiapacific.sharepoint.com/sites/ITWorkboard` contains:
- 9 lists total: Users, Deliverables, Work Board, EventLog, WorkIntake, Web Template Extensions, Hosted App Configs, Work Review, Documents
- WorkBoard list has 43 columns including indexed fields `DeliveryOwner` and `WorkIntake`
- Lookup relationships exist to Users, Deliverables, and WorkIntake lists
- 30 sample items retrieved successfully with full field expansion

**Source**: All 5 discovery output files.

---

## PATTERNS

### P1 — Two-layer config with deep-merge override

**Scope**: universal (applicable to any CLI tool with shared + per-user config)

Method for managing configuration that has both team-shared defaults and per-user overrides:

1. **Defaults file** (committed): All configuration keys with team-agreed values. Single source of truth for field mappings, normalization rules, and output settings.
2. **Local override file** (gitignored): Only the keys a developer needs to change. Uses shallow YAML — no need to repeat the full structure.
3. **Deep merge**: Local values overlay defaults using recursive dict merge, so partial overrides (e.g., changing one field mapping) don't wipe unrelated nested sections.
4. **Env var escape hatch**: Highest precedence, for CI/CD and quick overrides without file editing.
5. **Template/example file**: Committed `.example.yaml` showing what the local file should look like, serving as onboarding documentation.

Implemented in `config.py` as `_deep_merge()`.

### P2 — Config search order

**Scope**: local (workboard-cli-specific)

The config loader searches paths in order, taking the first match:
1. `config/local.yaml` (project-local override)
2. `~/.config/workboard/local.yaml` (user-level override)
3. `~/.workboard.yaml` (legacy user-level)
4. Env vars override any file-discovered value

This allows project-specific config, per-user config across projects, and CI config via env vars without collision.

---

## REFERENCES

### R1 — MSAL Python device code flow

Microsoft Authentication Library for Python's `PublicClientApplication` with `initiate_device_flow` and `acquire_token_by_device_flow`. Used for desktop/CLI auth where no redirect URI is available.

Documentation: https://learn.microsoft.com/en-us/entra/msal/python/

**Relevance**: Core auth mechanism for the CLI. No client secret needed.

### R2 — Microsoft Graph endpoints for SharePoint discovery

Used during the spike:
- `GET /sites/{hostname}:/sites/{path}` — site resolution
- `GET /sites/{site-id}/lists` — list enumeration
- `GET /sites/{site-id}/lists/{list-id}/columns` — schema export
- `GET /sites/{site-id}/lists/{list-id}/items?expand=fields&$top=10` — sample items

Documentation: https://learn.microsoft.com/en-us/graph/api/list-list (see `sources.md` for full refs)

**Relevance**: Core API surface for all read-only queries the CLI will perform.

---

## NEXT_STEPS

### N1 — Proceed to T02 (architecture and contracts)

- **What**: Use discovery data to design concrete CLI commands, data mappings, and permission requirements. Produce architecture docs and formal contracts.
- **Prompted by**: A01 audit passed — all criteria met, real discovery data ready.
- **Urgency**: now

---

## Connections

- A1 —[depends_on]→ A2 (discovery spike uses config system)
- A2 —[instance_of]→ P1, P2 (config system implements both patterns)
- A3 —[informed_by]→ A1 (discovery output produced by discovery spike)
- I1 —[informed_by]→ A3 (display name finding from discovery data)
- I2 —[informed_by]→ R1 (no-secret insight from MSAL device code docs)
- D1 —[led_to]→ A2 (split config decision produced the config system)
- D2 —[informed_by]→ D1 (env var expansion followed from config system design)
- D3 —[related_to]→ D1 (both concern what committed vs gitignored)
- N1 —[depends_on]→ A3 (architecture phase depends on real discovery data)

## Trail Updates

- **workboard-cli-discovery**: Created. Documents the live discovery spike, SharePoint site structure (9 lists, 43 columns), and key field mapping findings.
- **workboard-cli-config**: Created. Documents the two-layer config architecture (defaults.yaml + local.yaml), env var support, config search order, and the naming evolution decisions.
