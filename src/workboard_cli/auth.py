import json
import webbrowser
from pathlib import Path

import msal

from workboard_cli.config import load_config
from workboard_cli.errors import WorkboardError

TOKEN_CACHE: dict = {}

CACHE_DIR = Path.home() / ".config" / "workboard"
CACHE_FILE = CACHE_DIR / "msal_token_cache.json"

SECRET_KEYS = {"access_token", "refresh_token", "client_secret", "secret"}


def _redact(obj):
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k.lower() in SECRET_KEYS else _redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _load_msal_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_msal_cache(cache_state):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_state, f)


def get_token(tenant_id=None, client_id=None, force=False):
    if not tenant_id or not client_id:
        cfg = load_config()
        tenant_id = cfg["tenant_id"]
        client_id = cfg["client_id"]

    if not force and TOKEN_CACHE.get("token"):
        return TOKEN_CACHE["token"]

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    cache = msal.SerializableTokenCache()
    cache.deserialize(_load_msal_cache())
    app = msal.PublicClientApplication(client_id, authority=authority, token_cache=cache)

    accounts = app.get_accounts()
    if accounts and not force:
        result = app.acquire_token_silent(
            scopes=["https://graph.microsoft.com/Sites.Read.All"],
            account=accounts[0],
        )
        if result and "access_token" in result:
            TOKEN_CACHE["token"] = result["access_token"]
            if cache.has_state_changed:
                _save_msal_cache(cache.serialize())
            return result["access_token"]

    scopes = ["https://graph.microsoft.com/Sites.Read.All"]
    flow = app.initiate_device_flow(scopes=scopes)
    if "user_code" not in flow:
        raise WorkboardError(
            "auth_error",
            f"Device flow initiation failed: {flow.get('error_description', flow)}",
        )

    print(f"Open: {flow['verification_uri']}")
    print(f"Code: {flow['user_code']}")
    webbrowser.open(flow['verification_uri'])

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        error_desc = result.get("error_description", str(result))
        raise WorkboardError(
            "auth_error",
            f"Authentication failed: {error_desc}",
            "Try again or check your tenant ID and client ID.",
        )

    TOKEN_CACHE["token"] = result["access_token"]
    if cache.has_state_changed:
        _save_msal_cache(cache.serialize())
    return result["access_token"]


def check_auth():
    return bool(TOKEN_CACHE.get("token"))
