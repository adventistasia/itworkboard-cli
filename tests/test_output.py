import re

from workboard_cli.output import (
    _collect_warnings,
    build_envelope,
    build_summary_envelope,
)

SAMPLE_CONFIG = {
    "site_url": "https://sharepoint.com/sites/Test",
    "primary_list_name": "WorkBoard",
}

SAMPLE_ITEMS = [
    {"id": "1", "title": "A", "warnings": ["Missing field 'Stage'"]},
    {"id": "2", "title": "B", "warnings": []},
]


def test_build_envelope():
    envelope = build_envelope(SAMPLE_ITEMS, "open_items", SAMPLE_CONFIG)
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "open_items"
    assert envelope["source"]["system"] == "sharepoint"
    assert envelope["source"]["siteUrl"] == "https://sharepoint.com/sites/Test"
    assert envelope["source"]["listName"] == "WorkBoard"
    assert envelope["result"]["count"] == 2
    assert "retrievedAt" in envelope
    _assert_valid_session_id(envelope)
    assert "filters" in envelope


def test_build_envelope_with_filters():
    envelope = build_envelope([], "items_by_owner", SAMPLE_CONFIG, filters={"owner": "Alice"})
    assert envelope["filters"] == {"owner": "Alice"}


def test_build_summary_envelope():
    summary = {"totalItems": 5}
    envelope = build_summary_envelope(summary, SAMPLE_CONFIG)
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "manager_summary"
    assert envelope["result"]["totalItems"] == 5
    _assert_valid_session_id(envelope)


def test_collect_warnings():
    warnings = _collect_warnings(SAMPLE_ITEMS)
    assert len(warnings) == 1
    assert "Missing field 'Stage'" in warnings


def test_collect_warnings_dedup():
    items = [
        {"warnings": ["Same warning"]},
        {"warnings": ["Same warning"]},
    ]
    assert len(_collect_warnings(items)) == 1


def test_all_envelopes_share_session_id():
    env1 = build_envelope([], "open_items", SAMPLE_CONFIG)
    env2 = build_summary_envelope({}, SAMPLE_CONFIG)
    sid = env1["sessionId"]
    assert isinstance(sid, str) and len(sid) == 36
    assert env2["sessionId"] == sid


def _assert_valid_session_id(envelope):
    sid = envelope["sessionId"]
    assert isinstance(sid, str) and len(sid) == 36
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", sid)
