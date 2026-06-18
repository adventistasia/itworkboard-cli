import os
from pathlib import Path

import yaml

from workboard_cli.errors import WorkboardError

DEFAULTS_PATH = Path("config/workboard.defaults.yaml")
LOCAL_PATHS = [
    Path("config/local.yaml"),
    Path.home() / ".config/workboard/local.yaml",
    Path.home() / ".workboard.yaml",
]


def _deep_merge(base, overlay):
    merged = base.copy()
    for k, v in overlay.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def load_config(path=None):
    if not DEFAULTS_PATH.exists():
        raise WorkboardError(
            "config_error",
            f"Defaults file not found: {DEFAULTS_PATH}",
            "Ensure config/workboard.defaults.yaml exists in the project root.",
        )

    with open(DEFAULTS_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if path:
        local_paths = [Path(path)]
    else:
        local_paths = LOCAL_PATHS

    for p in local_paths:
        if p.exists():
            with open(p, encoding="utf-8") as f:
                config = _deep_merge(config, yaml.safe_load(f) or {})
            break

    tenant_id = os.environ.get("WORKBOARD_TENANT_ID") or config.get("tenant_id")
    client_id = os.environ.get("WORKBOARD_CLIENT_ID") or config.get("client_id")
    site_url = os.environ.get("WORKBOARD_SITE_URL") or config.get("site_url")
    list_name = os.environ.get("WORKBOARD_LIST_NAME") or config.get("primary_list_name")

    if not tenant_id or not client_id:
        raise WorkboardError(
            "config_error",
            "Missing credentials: set WORKBOARD_TENANT_ID and WORKBOARD_CLIENT_ID "
            "env vars, or create config/local.yaml",
        )

    return {
        "tenant_id": tenant_id,
        "client_id": client_id,
        "site_url": site_url,
        "primary_list_name": list_name,
        "fields": config.get("fields", {}),
        "stage_aliases": config.get("stage_aliases", {}),
        "output": config.get("output", {}),
        "query_defaults": config.get("query_defaults", {}),
    }
