import importlib
import json
from contextlib import ExitStack
from unittest.mock import patch

from typer.testing import CliRunner

from workboard_cli.cli import app
from workboard_cli import observations as obs

runner = CliRunner()

_MOCK_CFG = {"site_url": "https://test.sharepoint.com", "primary_list_name": "TestBoard", "fields": {}}
_MOCK_CLIENT = object()
_MOCK_TARGET = {"id": "test-list-id", "name": "TestBoard"}


def _mock_query_patches():
    stack = ExitStack()
    stack.enter_context(patch("workboard_cli.cli._get_client", return_value=(_MOCK_CFG, _MOCK_CLIENT)))
    stack.enter_context(patch("workboard_cli.cli._fetch_items", return_value=([], _MOCK_CFG, _MOCK_TARGET)))
    return stack


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Read-only CLI" in result.stdout


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "workboard-cli v" in result.stdout


def test_auth_help():
    result = runner.invoke(app, ["auth", "--help"])
    assert result.exit_code == 0


def test_site_help():
    result = runner.invoke(app, ["site", "--help"])
    assert result.exit_code == 0


def test_lists_help():
    result = runner.invoke(app, ["lists", "--help"])
    assert result.exit_code == 0


def test_schema_help():
    result = runner.invoke(app, ["schema", "--help"])
    assert result.exit_code == 0


def test_items_help():
    result = runner.invoke(app, ["items", "--help"])
    assert result.exit_code == 0


def test_query_help():
    result = runner.invoke(app, ["query", "--help"])
    assert result.exit_code == 0


def test_summary_help():
    result = runner.invoke(app, ["summary", "--help"])
    assert result.exit_code == 0


def test_agent_help():
    result = runner.invoke(app, ["agent", "--help"])
    assert result.exit_code == 0


def test_config_help():
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0


def test_agent_query_unsupported_intent():
    result = runner.invoke(app, ["agent", "query", "--intent", "browse"])
    assert result.exit_code == 1
    assert "unsupported_intent" in result.stdout


def test_auth_status_authenticated():
    with patch("workboard_cli.cli.check_auth", return_value=True):
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert '"authenticated": true' in result.stdout


def test_auth_status_not_authenticated():
    with patch("workboard_cli.cli.check_auth", return_value=False):
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert '"authenticated": false' in result.stdout


def test_query_open_includes_session_id():
    with _mock_query_patches():
        result = runner.invoke(app, ["query", "open"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert "sessionId" in envelope
    assert isinstance(envelope["sessionId"], str)
    assert len(envelope["sessionId"]) == 36


def test_cli_capture_with_mocked_query_includes_session_id():
    obs._events.clear()
    obs._counters.clear()
    with _mock_query_patches():
        result = runner.invoke(app, ["query", "open"])
    assert result.exit_code == 0
    assert len(obs._events) >= 1
    event = json.loads(obs._events[0])
    assert event["event"] == "invocation"
    assert "session_id" in event
    assert event["session_id"] == obs.get_session_id()


def test_envelope_session_id_matches_obs_session_id():
    obs._events.clear()
    obs._counters.clear()
    with _mock_query_patches():
        result = runner.invoke(app, ["query", "open"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert envelope["sessionId"] == obs.get_session_id()


def test_agent_query_unsupported_intent_includes_session_id():
    result = runner.invoke(app, ["agent", "query", "--intent", "browse"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert "sessionId" in data
    assert isinstance(data["sessionId"], str)
    assert len(data["sessionId"]) == 36


def test_query_open_includes_session_id_when_obs_disabled():
    import os
    prev_disable = os.environ.get("WORKBOARD_OBS_DISABLE")
    os.environ["WORKBOARD_OBS_DISABLE"] = "1"
    importlib.reload(obs)
    try:
        obs._events.clear()
        obs._counters.clear()
        with _mock_query_patches():
            result = runner.invoke(app, ["query", "open"])
        assert result.exit_code == 0
        envelope = json.loads(result.stdout)
        assert "sessionId" in envelope
        assert len(envelope["sessionId"]) == 36
        assert len(obs._events) == 0
    finally:
        if prev_disable:
            os.environ["WORKBOARD_OBS_DISABLE"] = prev_disable
        else:
            os.environ.pop("WORKBOARD_OBS_DISABLE", None)
        importlib.reload(obs)


def test_cross_stream_session_id_consistency(tmp_path):
    import os
    prev_dir = os.environ.get("WORKBOARD_OBS_DIR")
    os.environ["WORKBOARD_OBS_DIR"] = str(tmp_path)
    importlib.reload(obs)
    try:
        obs._events.clear()
        obs._counters.clear()
        with _mock_query_patches():
            result = runner.invoke(app, ["query", "open"])
        assert result.exit_code == 0
        envelope = json.loads(result.stdout)
        sid = envelope["sessionId"]
        assert sid == obs.get_session_id()
        assert len(obs._events) >= 1
        for line in obs._events:
            event = json.loads(line)
            assert event["session_id"] == sid
        obs._flush()
        counters_file = tmp_path / "workboard-counters.json"
        assert counters_file.exists()
        with open(counters_file) as f:
            counters = json.load(f)
        assert counters["session_id"] == sid
    finally:
        if prev_dir:
            os.environ["WORKBOARD_OBS_DIR"] = prev_dir
        else:
            os.environ.pop("WORKBOARD_OBS_DIR", None)
        importlib.reload(obs)
