---
title: check_auth() false negatives from in-memory-only cache check
date: 2026-06-19
category: logic-errors
module: workboard_cli
problem_type: logic_error
component: authentication
symptoms:
  - "workboard auth status returns authenticated: false even when valid MSAL disk cache exists"
  - "Other commands like site info and query work fine despite auth status reporting false"
root_cause: logic_error
resolution_type: code_fix
severity: medium
tags: [auth, msal, token-cache, sharepoint]
---

# check_auth() false negatives from in-memory-only cache check

## Problem

`workboard auth status` always returned `{"authenticated": false}` in a fresh Python process, even when the user had previously authenticated and a valid MSAL token cache existed on disk. This misled users and agents into thinking they needed to re-authenticate.

## Symptoms

- `workboard auth status` reports `authenticated: false` immediately after a successful login
- All other commands (e.g., `workboard site info`) work correctly because they call `get_token()` which loads the MSAL disk cache
- Only observable in fresh processes — running `auth status` after another command reports correctly because the other command populates the in-memory cache

## What Didn't Work

Initial investigation confirmed the CLI was correctly authenticated for real operations. The discrepancy was entirely in the `auth status` reporting path.

## Solution

Updated `check_auth()` in `src/workboard_cli/auth.py:95` to replicate the same silent token acquisition logic that `get_token()` already performed, rather than only checking an in-memory dictionary.

**Before:**
```python
def check_auth():
    return bool(TOKEN_CACHE.get("token"))
```

**After:**
```python
def check_auth():
    if TOKEN_CACHE.get("token"):
        return True

    cfg = load_config()
    authority = f"https://login.microsoftonline.com/{cfg['tenant_id']}"
    cache = msal.SerializableTokenCache()
    cache.deserialize(_load_msal_cache())
    app = msal.PublicClientApplication(cfg["client_id"], authority=authority, token_cache=cache)

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(
            scopes=["https://graph.microsoft.com/Sites.Read.All"],
            account=accounts[0],
        )
        if result and "access_token" in result:
            TOKEN_CACHE["token"] = result["access_token"]
            if cache.has_state_changed:
                _save_msal_cache(cache.serialize())
            return True

    return False
```

## Why This Works

`get_token()` (used by all real commands) follows a three-layer resolution: in-memory cache → MSAL disk cache → silent renewal. `check_auth()` only checked the first layer. The fix adds the second and third layers — loading the MSAL `SerializableTokenCache` from disk and attempting `acquire_token_silent()` — so `auth status` reflects the same reality as every other command.

The `TOKEN_CACHE` population side effect (`TOKEN_CACHE["token"] = result["access_token"]`) means that running `auth status` first doesn't just report correctly — it also warms the in-memory cache for subsequent commands.

## Prevention

- Auth status checks should never be shallower than the authentication path used by real operations. If `get_token()` goes to disk, `check_auth()` must go to disk too.
- The next time a similar "status" or "health" check is added, verify it exercises the same credential resolution path as production commands.

## Related Issues

- Commit: `6d31859` — fix: check_auth() now consults MSAL disk cache before reporting false
