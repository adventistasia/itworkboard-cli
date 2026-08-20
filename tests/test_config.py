"""Tests for config loading — three-tier precedence and validation."""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from workboard_cli.config import _deep_merge, load_config
from workboard_cli.errors import WorkboardError

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


def test_load_config_defaults_only():
    """Defaults file provides tenant_id and client_id — no local, no env."""
    defaults = {
        "tenant_id": "default-tenant",
        "client_id": "default-client",
        "site_url": "https://test.sharepoint.com",
        "primary_list_name": "TestBoard",
        "fields": {},
        "stage_aliases": {},
        "output": {},
        "query_defaults": {},
    }
    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", []),
        patch.dict(os.environ, {}, clear=True),
    ):
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        m = mock_open(read_data=yaml.dump(defaults))
        with patch("builtins.open", m):
            cfg = load_config()

    assert cfg["tenant_id"] == "default-tenant"
    assert cfg["client_id"] == "default-client"
    assert cfg["site_url"] == "https://test.sharepoint.com"


def test_load_config_local_overlay():
    """Local overlay overrides defaults via deep merge."""
    defaults = {
        "tenant_id": "default-tenant",
        "client_id": "default-client",
        "site_url": "https://default.sharepoint.com",
        "primary_list_name": "DefaultBoard",
        "fields": {"id": "ID"},
        "stage_aliases": {},
        "output": {},
        "query_defaults": {},
    }
    local = {
        "tenant_id": "local-tenant",
        "client_id": "local-client",
    }
    local_path = Path("config/local.yaml")

    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", [local_path]),
        patch.dict(os.environ, {}, clear=True),
    ):
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"

        # First open = defaults, second open = local
        defaults_data = yaml.dump(defaults)
        local_data = yaml.dump(local)
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_open(read_data=defaults_data)()
            return mock_open(read_data=local_data)()

        m = mock_open()
        m.side_effect = side_effect
        with patch("builtins.open", m), patch.object(type(local_path), "exists", return_value=True):
            cfg = load_config()

    assert cfg["tenant_id"] == "local-tenant"
    assert cfg["client_id"] == "local-client"
    assert cfg["site_url"] == "https://default.sharepoint.com"  # not overridden


def test_load_config_env_var_highest_precedence():
    """Env vars override both defaults and local."""
    defaults = {
        "tenant_id": "default-tenant",
        "client_id": "default-client",
        "site_url": "https://default.sharepoint.com",
        "primary_list_name": "DefaultBoard",
        "fields": {},
        "stage_aliases": {},
        "output": {},
        "query_defaults": {},
    }
    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", []),
        patch.dict(os.environ, {"WORKBOARD_TENANT_ID": "env-tenant", "WORKBOARD_CLIENT_ID": "env-client"}, clear=False),
    ):
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        m = mock_open(read_data=yaml.dump(defaults))
        with patch("builtins.open", m):
            cfg = load_config()

    assert cfg["tenant_id"] == "env-tenant"
    assert cfg["client_id"] == "env-client"


def test_load_config_missing_defaults_file():
    """Missing defaults file raises config_error."""
    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
    ):
        mock_defaults.exists.return_value = False
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        with pytest.raises(WorkboardError) as exc_info:
            load_config()
    assert exc_info.value.code == "config_error"


def test_load_config_empty_tenant_id_raises():
    """Defaults with empty tenant_id raises config_error."""
    defaults = {
        "tenant_id": "",
        "client_id": "some-client",
        "site_url": "https://test.sharepoint.com",
        "primary_list_name": "TestBoard",
        "fields": {},
        "stage_aliases": {},
        "output": {},
        "query_defaults": {},
    }
    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", []),
        patch.dict(os.environ, {}, clear=True),
    ):
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        m = mock_open(read_data=yaml.dump(defaults))
        with patch("builtins.open", m), pytest.raises(WorkboardError) as exc_info:
            load_config()
    assert exc_info.value.code == "config_error"
    assert "Missing credentials" in exc_info.value.message


def test_load_config_env_partial_override():
    """Only WORKBOARD_TENANT_ID set — client_id falls through to defaults."""
    defaults = {
        "tenant_id": "default-tenant",
        "client_id": "default-client",
        "site_url": "https://default.sharepoint.com",
        "primary_list_name": "DefaultBoard",
        "fields": {},
        "stage_aliases": {},
        "output": {},
        "query_defaults": {},
    }
    with (
        patch("workboard_cli.config.DEFAULTS_PATH") as mock_defaults,
        patch("workboard_cli.config.LOCAL_PATHS", []),
        patch.dict(os.environ, {"WORKBOARD_TENANT_ID": "env-tenant"}, clear=False),
    ):
        # Ensure CLIENT_ID is not set
        os.environ.pop("WORKBOARD_CLIENT_ID", None)
        mock_defaults.exists.return_value = True
        mock_defaults.__str__ = lambda self: "config/workboard.defaults.yaml"
        m = mock_open(read_data=yaml.dump(defaults))
        with patch("builtins.open", m):
            cfg = load_config()

    assert cfg["tenant_id"] == "env-tenant"
    assert cfg["client_id"] == "default-client"  # from defaults
