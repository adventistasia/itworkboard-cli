"""Tests for config loading — three-tier precedence and validation."""

import os
from io import StringIO
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from workboard_cli.config import _deep_merge, load_config
from workboard_cli.errors import WorkboardError

# Shared defaults fixture — single source of truth for all mock-based tests.
DEFAULTS_DICT = {
    "tenant_id": "default-tenant",
    "client_id": "default-client",
    "site_url": "https://default.sharepoint.com",
    "primary_list_name": "DefaultBoard",
    "fields": {"id": "ID"},
    "stage_aliases": {},
    "output": {},
    "query_defaults": {},
}


# --- _deep_merge unit tests ---


def test_deep_merge_flat():
    base = {"a": 1, "b": 2}
    overlay = {"b": 3, "c": 4}
    result = _deep_merge(base, overlay)
    assert result == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_nested():
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    overlay = {"a": {"y": 99}}
    result = _deep_merge(base, overlay)
    assert result == {"a": {"x": 1, "y": 99}, "b": 3}


def test_deep_merge_empty_overlay():
    base = {"a": 1}
    result = _deep_merge(base, {})
    assert result == {"a": 1}


# --- load_config tests ---


def _run_with_mocks(defaults_dict, local_paths=None, env_vars=None, open_side_effect=None):
    """Run load_config with controlled mocks. Returns the config dict."""
    defaults_data = yaml.dump(defaults_dict)
    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", local_paths or []),
        patch.dict(os.environ, env_vars or {}, clear=True),
    ):
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        if open_side_effect:
            m = mock_open()
            m.side_effect = open_side_effect
        else:
            m = mock_open(read_data=defaults_data)
        with patch("builtins.open", m):
            return load_config()


def test_load_config_defaults_only():
    """Defaults file provides tenant_id and client_id — no local, no env."""
    cfg = _run_with_mocks(DEFAULTS_DICT)
    assert cfg["tenant_id"] == "default-tenant"
    assert cfg["client_id"] == "default-client"
    assert cfg["site_url"] == "https://default.sharepoint.com"


def test_load_config_local_overlay():
    """Local overlay overrides defaults via deep merge."""
    local = {"tenant_id": "local-tenant", "client_id": "local-client"}
    local_path = Path("config/local.yaml")
    defaults_data = yaml.dump(DEFAULTS_DICT)
    local_data = yaml.dump(local)

    def open_by_path(path, *args, **kwargs):
        if str(path) == "config/workboard.defaults.yaml":
            return StringIO(defaults_data)
        return StringIO(local_data)

    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", [local_path]),
        patch.dict(os.environ, {}, clear=True),
        patch("builtins.open", side_effect=open_by_path),
        patch.object(type(local_path), "exists", return_value=True),
    ):
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        cfg = load_config()

    assert cfg["tenant_id"] == "local-tenant"
    assert cfg["client_id"] == "local-client"
    assert cfg["site_url"] == "https://default.sharepoint.com"  # not overridden


def test_load_config_env_var_highest_precedence():
    """Env vars override both defaults and local."""
    env = {"WORKBOARD_TENANT_ID": "env-tenant", "WORKBOARD_CLIENT_ID": "env-client"}
    cfg = _run_with_mocks(DEFAULTS_DICT, env_vars=env)
    assert cfg["tenant_id"] == "env-tenant"
    assert cfg["client_id"] == "env-client"


def test_load_config_missing_defaults_file():
    """Missing defaults file raises config_error."""
    with patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults:
        mock_defaults.exists.return_value = False
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        with pytest.raises(WorkboardError) as exc_info:
            load_config()
    assert exc_info.value.code == "config_error"


def test_load_config_empty_tenant_id_raises():
    """Defaults with empty tenant_id raises config_error."""
    bad_defaults = {**DEFAULTS_DICT, "tenant_id": ""}
    with pytest.raises(WorkboardError) as exc_info:
        _run_with_mocks(bad_defaults)
    assert exc_info.value.code == "config_error"
    assert "Missing credentials" in exc_info.value.message


def test_load_config_env_partial_override():
    """Only WORKBOARD_TENANT_ID set — client_id falls through to defaults."""
    env = {"WORKBOARD_TENANT_ID": "env-tenant"}
    os.environ.pop("WORKBOARD_CLIENT_ID", None)
    cfg = _run_with_mocks(DEFAULTS_DICT, env_vars=env)
    assert cfg["tenant_id"] == "env-tenant"
    assert cfg["client_id"] == "default-client"  # from defaults


def test_load_config_missing_local_file_falls_through():
    """Local path that doesn't exist is skipped — defaults remain."""
    fake_path = Path("config/nonexistent.yaml")
    local_paths = [fake_path]

    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", local_paths),
        patch.dict(os.environ, {}, clear=True),
    ):
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        with patch.object(type(fake_path), "exists", return_value=False):
            m = mock_open(read_data=yaml.dump(DEFAULTS_DICT))
            with patch("builtins.open", m):
                cfg = load_config()

    assert cfg["tenant_id"] == "default-tenant"
    assert cfg["client_id"] == "default-client"


def test_load_config_real_defaults_file():
    """Smoke test: the real committed defaults file loads and has required keys."""
    with (
        patch("workboard_cli.config.LOCAL_PATHS", []),
        patch.dict(os.environ, {}, clear=True),
    ):
        cfg = load_config()

    assert cfg["tenant_id"], "tenant_id must not be empty in defaults"
    assert cfg["client_id"], "client_id must not be empty in defaults"
    assert cfg["site_url"], "site_url must not be empty in defaults"
    assert cfg["primary_list_name"], "primary_list_name must not be empty in defaults"
    assert isinstance(cfg["fields"], dict)
    assert isinstance(cfg["stage_aliases"], dict)
