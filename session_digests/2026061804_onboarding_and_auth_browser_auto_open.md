---
lorespec: "0.1"
id: "2026061804"
date: "2026-06-18"
source: "opencode"
topic: "CLI onboarding, device code auth debugging, and auto-open browser fix"
tags: [onboarding, auth, device-code, webbrowser, stdout-buffering, workboard-cli]
classification:
  type: technical
  secondary_type: drafting
  domains: [cli-development, microsoft-auth, sharepoint]
  value: medium
trails: [workboard-cli-auth, workboard-cli-onboarding]
---

## Session Arc

### Started
User requested onboarding to the workboard-cli: install, configure auth, verify connectivity, run a test query.

### Pivots
- **Auth stall (device code not printed)**: Running `workboard auth login` produced no output — no URL, no code. Root cause was Python stdout buffering in the subprocess environment. Fixed with `$env:PYTHONUNBUFFERED=1`.
- **UX friction → code change**: After successful auth, user expressed dissatisfaction that the browser didn't open automatically. This triggered the `webbrowser.open()` addition to the device flow.
- **Commit**: Changes were committed with a single conventional commit.

### Ended
CLI installed and authenticated, browser auto-open added, all changes committed.

## Artifacts

### A1 — Browser auto-open on device code auth

- **File**: `src/workboard_cli/auth.py` (commit `b0e0af5`)
- **Summary**: Added `webbrowser.open(flow['verification_uri'])` immediately after printing the device code URL and code in `get_token()`. When `workboard auth login` triggers device flow, the default browser now opens to `https://login.microsoft.com/device` automatically. The user only needs to enter the code shown in the terminal.
- **Also changed**: `docs/onboarding_agent.md` (updated instructions) and `readme.md` (added agent install prompt).
- **Evolution**: Previously only `print()` statements showed the URL and code. Now the browser opens as well.

## Solutions

### S1 — Force unbuffered stdout for device code visibility

- **Problem**: Running `workboard auth login` in the shell tool produced no visible output because `acquire_token_by_device_flow()` is a blocking call and Python buffers stdout when it detects a pipe/subprocess context.
- **Fix**: Set `$env:PYTHONUNBUFFERED = "1"` before invoking the CLI. This forces stdout to flush immediately, so the URL and code print before the blocking auth call.
- **Why it works**: Python's `print()` normally flushes on newline only when connected to a TTY. `PYTHONUNBUFFERED=1` disables I/O buffering globally.
- **Caveats**: Only needed in subprocess/pipe environments (shell tools, CI). Interactive terminal use has no buffering issue.

## Insights

### I1 — Python buffers stdout in subprocess environments

Python's default line-buffering applies to stdout only when connected to a TTY. When a CLI is driven through a shell tool (pipe/subprocess), stdout becomes fully buffered. A `print()` before a long blocking call will not appear until the buffer fills or the process exits. Confidence: high.

### I2 — Target tenant and client_id are live and functional

The configured Azure AD tenant (`918af52d-8dec-44c4-818a-cebf3c9b7767`) and client ID (`c626c5b9-2fbb-4004-89a2-7660ea1906c0`) successfully completed device code auth against the target SharePoint site. The site returned correct metadata and 30 items were retrieved. Confidence: high.

## Patterns

### P1 — Unbuffer stdout before blocking auth flows in automated environments

**Scope**: Universal (applies to any CLI tool with device-code or OAuth flows driven through subprocess/CI).

When automating a CLI that uses a device code flow (or any flow that prints a URL/code then blocks for user action), always force unbuffered Python output so the URL and code are visible before the blocking call:

```
$env:PYTHONUNBUFFERED = "1"   # Windows PowerShell
export PYTHONUNBUFFERED=1      # Linux/macOS
```

This applies whenever the CLI is invoked through a shell tool, CI runner, or any non-TTY context.

## Connections

- **S1** —[led_to]→ **A1** (fixing the buffering issue enabled the user to see output, which led to the UX request)
- **I1** —[informed_by]→ **S1** (the buffering observation was the root cause analysis)
- **S1** —[instance_of]→ **P1** (specific fix is an example of the general pattern)
- **A1** —[depends_on]→ **S1** (A1's webbrowser.open would not have been visible without S1's fix first)
- **S1** —[related_to]→ **workboard-cli-onboarding trail** (part of the onboarding setup sequence)

## Trail Updates

- **workboard-cli-auth**: Extended with the `webbrowser.open()` pattern. Device flow now opens browser automatically.
- **workboard-cli-onboarding**: Extended with the PYTHONUNBUFFERED workaround for shell-tool-driven auth.
