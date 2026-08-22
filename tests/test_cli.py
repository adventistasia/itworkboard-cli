import importlib
import json
from contextlib import ExitStack
from unittest.mock import patch

from typer.testing import CliRunner

from workboard_cli import observations as obs
from workboard_cli.cli import app

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


def test_agent_query_new_items():
    with _mock_query_patches():
        result = runner.invoke(app, ["agent", "query", "--intent", "new_items", "--days", "7"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert envelope["intent"] == "new_items"


def test_agent_query_new_items_missing_days():
    result = runner.invoke(app, ["agent", "query", "--intent", "new_items"])
    assert result.exit_code == 1


def test_agent_query_recently_completed_items():
    with _mock_query_patches():
        result = runner.invoke(app, ["agent", "query", "--intent", "recently_completed_items", "--days", "30"])
    assert result.exit_code == 0


def test_agent_query_cycle_time_stats():
    with _mock_query_patches():
        result = runner.invoke(app, ["agent", "query", "--intent", "cycle_time_stats"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert envelope["intent"] == "cycle_time_stats"


def test_agent_query_items_by_project():
    with _mock_query_patches():
        result = runner.invoke(app, ["agent", "query", "--intent", "items_by_project", "--project", "Test"])
    assert result.exit_code == 0


def test_agent_query_items_by_stage():
    with _mock_query_patches():
        result = runner.invoke(app, ["agent", "query", "--intent", "items_by_stage", "--stage", "Open"])
    assert result.exit_code == 0


def test_agent_query_items_by_decision_authority():
    with _mock_query_patches():
        result = runner.invoke(app, ["agent", "query", "--intent", "items_by_decision_authority", "--person", "Alice"])
    assert result.exit_code == 0


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


_VALID_GUID = "918af52d-8dec-44c4-818a-cebf3c9b7767"
_VALID_GUID2 = "c626c5b9-2fbb-4004-89a2-7660ea1906c0"


def test_config_set_tenant_id(tmp_path):
    target = tmp_path / "local.yaml"
    with patch("workboard_cli.config.LOCAL_PATHS", [target]):
        result = runner.invoke(app, ["config", "set", "--tenant-id", _VALID_GUID])
    assert result.exit_code == 0
    assert "tenant_id" in result.stdout
    assert target.exists()


def test_config_set_client_id(tmp_path):
    target = tmp_path / "local.yaml"
    with patch("workboard_cli.config.LOCAL_PATHS", [target]):
        result = runner.invoke(app, ["config", "set", "--client-id", _VALID_GUID2])
    assert result.exit_code == 0
    assert "client_id" in result.stdout
    assert target.exists()


def test_config_set_both_keys(tmp_path):
    target = tmp_path / "local.yaml"
    with patch("workboard_cli.config.LOCAL_PATHS", [target]):
        result = runner.invoke(
            app, ["config", "set", "--tenant-id", _VALID_GUID, "--client-id", _VALID_GUID2]
        )
    assert result.exit_code == 0
    import yaml

    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["tenant_id"] == _VALID_GUID
    assert data["client_id"] == _VALID_GUID2


def test_config_set_no_flags():
    result = runner.invoke(app, ["config", "set"])
    assert result.exit_code == 1
    assert "config_error" in result.stdout


def test_config_set_invalid_guid(tmp_path):
    target = tmp_path / "local.yaml"
    with patch("workboard_cli.config.LOCAL_PATHS", [target]):
        result = runner.invoke(app, ["config", "set", "--tenant-id", "not-a-guid"])
    assert result.exit_code == 1
    assert "config_error" in result.stdout
    assert not target.exists()


def test_config_set_preserves_existing_keys(tmp_path):
    import yaml

    target = tmp_path / "local.yaml"
    target.write_text(
        yaml.dump({"tenant_id": "old-tenant", "site_url": "https://example.com"}),
        encoding="utf-8",
    )
    with patch("workboard_cli.config.LOCAL_PATHS", [target]):
        result = runner.invoke(app, ["config", "set", "--client-id", _VALID_GUID2])
    assert result.exit_code == 0
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert data["tenant_id"] == "old-tenant"
    assert data["site_url"] == "https://example.com"
    assert data["client_id"] == _VALID_GUID2


def test_config_help_lists_set():
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0
    assert "set" in result.stdout


# --- U-3: Automatic dual capture for primary items get ---


_PRIMARY_CFG = {
    "site_url": "https://test.sharepoint.com",
    "primary_list_name": "WorkBoard",
    "fields": {
        "title": "Title",
        "stage": "Stage",
        "delivery_owner": "DeliveryOwner",
        "why": "Why",
        "scope": "Scope",
        "requirements": "Requirements",
        "schedule": "Schedule",
        "acceptance_criteria": "AcceptanceCriteria",
        "deliverables": "Deliverables",
        "decision_authority": "DecisionAuthority",
        "acceptance_authority": "AcceptanceAuthority",
        "work_intake": "WorkIntake",
        "rel_project": "RelProject",
        "rel_work_brief": "RelWorkBrief",
        "description": "Description",
        "priority_status": "PriorityStatus",
        "date_due": "DateDue",
        "date_committed": "DateCommitted",
        "date_start": "DateStart",
        "date_closed": "DateClosed",
        "cycle_time": "CycleTime",
        "created": "Created",
        "modified": "Modified",
    },
    "stage_aliases": {"open": ["Open"], "closed": ["Closed"], "blocked": ["Blocked"]},
    "output": {"include_raw_fields": False},
}

_PRIMARY_LISTS = [
    {"id": "primary-list-id", "displayName": "WorkBoard", "name": "WorkBoard"},
    {"id": "other-list-id", "displayName": "CustomList", "name": "CustomList"},
]

_PRIMARY_ITEM = {
    "id": 42,
    "webUrl": "https://test.sharepoint.com/sites/Test/Lists/TestBoard/DispForm.aspx?ID=42",
    "fields": {
        "Title": "Primary Item",
        "Stage": "Open",
        "Created": "2026-05-01T00:00:00Z",
        "Modified": "2026-06-10T00:00:00Z",
        "DateDue": "2026-06-30",
    },
}

_CUSTOM_ITEM = {
    "id": 99,
    "webUrl": "https://test.sharepoint.com/sites/Test/Lists/CustomList/DispForm.aspx?ID=99",
    "fields": {
        "Title": "Custom Item",
        "Stage": "Done",
        "Created": "2026-04-01T00:00:00Z",
        "Modified": "2026-05-01T00:00:00Z",
    },
}


def _mock_items_get_patches(cfg=_PRIMARY_CFG, target_list=None, lists=None, item=None):
    """Return an ExitStack with mocked _get_client and the Graph functions for items_get."""
    stack = ExitStack()
    stack.enter_context(patch("workboard_cli.cli._get_client", return_value=(cfg, _MOCK_CLIENT)))
    if lists is None:
        lists = _PRIMARY_LISTS
    if target_list is None:
        target_list = _PRIMARY_LISTS[0]
    stack.enter_context(patch("workboard_cli.cli.get_site", return_value={"id": "site-id"}))
    stack.enter_context(patch("workboard_cli.cli.get_lists", return_value=lists))
    stack.enter_context(patch("workboard_cli.cli.get_list_item", return_value=item or _PRIMARY_ITEM))
    return stack


def test_items_get_primary_returns_unchanged_raw_and_work_item():
    """AE1 -- Primary list get returns result.item unchanged plus result.workItem."""
    with _mock_items_get_patches():
        result = runner.invoke(app, ["items", "get", "42"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert envelope["status"] == "ok"
    assert envelope["result"]["item"] == _PRIMARY_ITEM
    assert "workItem" in envelope["result"]
    wi = envelope["result"]["workItem"]
    assert wi["id"] == "42"
    assert wi["title"] == "Primary Item"
    assert wi["stage"] == "Open"


def test_items_get_primary_preserves_top_level_metadata_and_session_id():
    """AE1/R3 -- status, source, retrievedAt, sessionId preserved."""
    with _mock_items_get_patches():
        result = runner.invoke(app, ["items", "get", "42"])
    envelope = json.loads(result.stdout)
    assert envelope["status"] == "ok"
    assert "source" in envelope
    assert envelope["source"]["system"] == "sharepoint"
    assert "retrievedAt" in envelope
    assert "sessionId" in envelope
    assert len(envelope["sessionId"]) == 36
    wi = envelope["result"]["workItem"]
    assert "sessionId" not in wi


def test_items_get_omitted_list_uses_configured_primary():
    """AE1 -- Omitted --list defaults to configured primary."""
    with _mock_items_get_patches():
        result = runner.invoke(app, ["items", "get", "42"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert "workItem" in envelope["result"]


def test_items_get_custom_list_remains_raw_only():
    """AE2 -- Non-primary list get omits result.workItem."""
    with _mock_items_get_patches(item=_CUSTOM_ITEM):
        result = runner.invoke(app, ["items", "get", "99", "--list", "CustomList"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert envelope["result"]["item"] == _CUSTOM_ITEM
    assert "workItem" not in envelope["result"]


def test_items_get_not_found_preserves_structured_error():
    """AE12 -- Not-found item returns structured error, no partial result."""
    from workboard_cli.errors import WorkboardError
    with _mock_items_get_patches(), patch(
        "workboard_cli.cli.get_list_item",
        side_effect=WorkboardError("resource_not_found", "Item not found.", "Check the ID."),
    ):
        result = runner.invoke(app, ["items", "get", "999999"])
    assert result.exit_code == 1
    envelope = json.loads(result.stdout)
    assert envelope["status"] == "error"
    assert envelope["error"]["code"] == "resource_not_found"
    assert "item" not in envelope.get("result", {})
    assert "workItem" not in envelope.get("result", {})


# --- U-4: Cross-surface compatibility and agent boundary guards ---


_U4_CFG = {
    "site_url": "https://test.sharepoint.com",
    "primary_list_name": "WorkBoard",
    "fields": {
        "title": "Title",
        "stage": "Stage",
        "delivery_owner": "DeliveryOwner",
        "why": "Why",
        "scope": "Scope",
        "requirements": "Requirements",
        "schedule": "Schedule",
        "acceptance_criteria": "AcceptanceCriteria",
        "deliverables": "Deliverables",
        "decision_authority": "DecisionAuthority",
        "acceptance_authority": "AcceptanceAuthority",
        "work_intake": "WorkIntake",
        "rel_project": "RelProject",
        "rel_work_brief": "RelWorkBrief",
        "description": "Description",
        "priority_status": "PriorityStatus",
        "date_due": "DateDue",
        "date_committed": "DateCommitted",
        "date_start": "DateStart",
        "date_closed": "DateClosed",
        "cycle_time": "CycleTime",
        "created": "Created",
        "modified": "Modified",
    },
    "stage_aliases": {"open": ["Open"], "closed": ["Closed"], "blocked": ["Blocked"]},
    "output": {"include_raw_fields": False},
}

_U4_RAW_ITEMS = [
    {
        "id": 1,
        "fields": {
            "Title": "Open Item",
            "Stage": "Open",
            "DeliveryOwner": {"displayName": "Alice"},
            "Scope": "<p>Scope A</p>",
            "Requirements": "<p>Reqs A</p>",
            "Created": "2026-05-01T00:00:00Z",
            "Modified": "2026-06-01T00:00:00Z",
        },
    },
    {
        "id": 2,
        "fields": {
            "Title": "Closed Item",
            "Stage": "Closed",
            "DeliveryOwner": {"displayName": "Bob"},
            "Scope": "<p>Scope B</p>",
            "Requirements": "<p>Reqs B</p>",
            "Created": "2026-04-01T00:00:00Z",
            "Modified": "2026-05-15T00:00:00Z",
        },
    },
]


def test_items_list_normalized_inherits_additive_work_item_fields():
    """AE17 -- items list --normalize inherits scopeText and requirementsText."""
    with ExitStack() as stack:
        stack.enter_context(patch("workboard_cli.cli._get_client", return_value=(_U4_CFG, _MOCK_CLIENT)))
        stack.enter_context(patch("workboard_cli.cli.get_site", return_value={"id": "site-id"}))
        stack.enter_context(patch("workboard_cli.cli.get_lists", return_value=[
            {"id": "primary-list-id", "displayName": "WorkBoard", "name": "WorkBoard"},
        ]))
        stack.enter_context(patch("workboard_cli.cli.get_list_items", return_value=_U4_RAW_ITEMS))
        result = runner.invoke(app, ["items", "list", "--normalize"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert envelope["result"]["count"] == 2
    for item in envelope["result"]["items"]:
        assert "scopeText" in item
        assert "requirementsText" in item


def test_query_open_inherits_additive_fields_without_filter_change():
    """AE17 -- query open inherits additive fields; filter unchanged."""
    with ExitStack() as stack:
        stack.enter_context(patch("workboard_cli.cli._get_client", return_value=(_U4_CFG, _MOCK_CLIENT)))
        stack.enter_context(patch("workboard_cli.cli._fetch_items", return_value=(_U4_RAW_ITEMS, _U4_CFG, {"id": "test-list-id", "name": "WorkBoard"})))
        result = runner.invoke(app, ["query", "open"])
    assert result.exit_code == 0
    envelope = json.loads(result.stdout)
    assert envelope["result"]["count"] == 1
    item = envelope["result"]["items"][0]
    assert "scopeText" in item
    assert "requirementsText" in item
    assert item["title"] == "Open Item"


def test_execute_intent_inherits_additive_fields_without_routing_change():
    """AE17 -- execute_intent inherits additive fields; routing unchanged."""
    from workboard_cli.agent import execute_intent
    envelope = execute_intent("open_items", _U4_RAW_ITEMS, _U4_CFG)
    assert envelope["result"]["count"] == 1
    item = envelope["result"]["items"][0]
    assert "scopeText" in item
    assert "requirementsText" in item
    assert item["scopeText"] == "Scope A"
    assert item["requirementsText"] == "Reqs A"


def test_manager_summary_aggregates_are_unchanged_by_additive_fields():
    """AE17 -- Summary counts and groupings unchanged by additive fields."""
    from workboard_cli.agent import execute_intent
    envelope = execute_intent("manager_summary", _U4_RAW_ITEMS, _U4_CFG)
    assert envelope["result"]["totalItems"] == 2
    assert envelope["result"]["byStageCategory"]["open"] == 1
    assert envelope["result"]["byStageCategory"]["closed"] == 1


def test_items_get_is_not_an_approved_intent():
    """AE16 -- items_get spellings are absent from APPROVED_INTENTS."""
    from workboard_cli.agent import APPROVED_INTENTS
    single_item_spellings = ["get_item", "items_get", "get_item_by_id", "single_item"]
    for spelling in single_item_spellings:
        assert spelling not in APPROVED_INTENTS, f"Single-item intent '{spelling}' should not be approved"
    assert "open_items" in APPROVED_INTENTS
    assert "manager_summary" in APPROVED_INTENTS
