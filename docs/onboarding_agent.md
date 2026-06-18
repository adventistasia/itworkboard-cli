# User onboarding — agent instructions

Run this flow when onboarding a new user. Execute each step sequentially. Show command output to the user and explain what each command does.

## Prerequisites

- User has Python 3.11+ installed
- User has a copy of this repo cloned

## Step 1: Install the CLI

```bash
pip install -e .
```

Verify installation:

```bash
workboard --help
```

Confirm the command groups (auth, site, lists, schema, items, query, summary, agent, config, self) are visible.

## Step 2: Authenticate

```bash
workboard auth login
```

The CLI prints a URL and a device code. Tell the user:
- "Open the URL in any browser"
- "Enter the code shown above"
- "Sign in with your Microsoft work account"
- The CLI will proceed automatically once authentication completes

Verify success:

```bash
workboard auth status
```

Expected: `{"status": "ok", "authenticated": true}`

## Step 3: Demo commands

Run each command, show the output, and briefly explain what it shows. Adapt the owner name used in `by-owner` queries to someone visible in the output of an earlier command.

### Site and list discovery

```bash
workboard site info
```

Shows the SharePoint site ID and name the CLI resolves to.

```bash
workboard lists discover
```

Enumerates all lists on the site — shows which ones exist and their IDs.

### Schema exploration

```bash
workboard schema export --list WorkBoard
```

Exports the column schema for the WorkBoard list to a JSON file. Open the file to show the user what fields are available.

### Raw items

```bash
workboard items list --limit 5
```

Shows raw list items straight from SharePoint. Note the SharePoint internal field names.

```bash
workboard items list --limit 5 --normalize
```

Same items but normalized to friendly field names using the config mapping. Compare the two outputs to show the value of normalization.

### Operational queries

```bash
workboard query open
```

Items with a stage matching "Open", "In Progress", or "New".

```bash
workboard query overdue
```

Items past their due date and still open.

```bash
workboard query blocked
```

Items with stage "Blocked" or "On Hold".

```bash
workboard query recently-updated --days 30
```

Items modified in the last 30 days.

### Manager summary

```bash
workboard summary manager
```

A markdown report with counts, groupings, and a visual health overview. This is the highest-value single command for managers.

### Agent interface

```bash
workboard agent query --intent open_items
```

The agent-focused interface. Shows the standard JSON envelope with source, retrievedAt, filters, and result. Explain that this is the command AI agents should use (not free-form query commands).

### Configuration validation

```bash
workboard config validate
```

Validates that the config field mappings exist in the schema. Useful after schema changes.

### Self-inspection

```bash
workboard self path
```

Shows where the CLI is installed on disk.

## Step 4: Summarize

After the demo, tell the user:

- The CLI is **read-only** — it queries SharePoint, never writes
- All commands accept `--format json` (default) or machine-readable output
- The `agent query` interface is the approved path for AI agents
- No secrets appear in any output
- Config is at `config/workboard.defaults.yaml` with local overrides in `config/local.yaml`
- Auth tokens are cached in `~/.config/workboard/msal_token_cache.json`
- The full command contract is documented in `docs/cli_command_contract.md`
