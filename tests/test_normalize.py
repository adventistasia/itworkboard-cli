from workboard_cli.normalize import (
    _build_source_url,
    _get_stage_category,
    _parse_date,
    _parse_person,
    normalize_item,
)

SAMPLE_CONFIG = {
    "site_url": "https://southernasiapacific.sharepoint.com/sites/ITWorkboard",
    "primary_list_name": "WorkBoard",
    "fields": {
        "id": "ID",
        "title": "Title",
        "stage": "Stage",
        "delivery_owner": "DeliveryOwner",
        "why": "Why",
        "date_due": "DateDue",
        "date_committed": "DateCommitted",
        "date_start": "DateStart",
        "date_closed": "DateClosed",
        "created": "Created",
        "modified": "Modified",
    },
    "stage_aliases": {
        "open": ["Open", "In Progress", "New"],
        "closed": ["Closed", "Done", "Completed", "Cancelled"],
        "blocked": ["Blocked", "On Hold"],
    },
    "output": {"include_raw_fields": False},
}

SAMPLE_ITEM = {
    "id": 42,
    "fields": {
        "ID": 42,
        "Title": "Test Item",
        "Stage": "Open",
        "DeliveryOwner": {
            "displayName": "John Doe",
            "email": "john@example.org",
        },
        "Why": "Business reason",
        "DateDue": "2026-06-30",
        "DateCommitted": "2026-06-01",
        "DateStart": "2026-05-15",
        "DateClosed": None,
        "Created": "2026-05-01T00:00:00Z",
        "Modified": "2026-06-10T12:00:00Z",
    },
}


def test_normalize_basic():
    result = normalize_item(SAMPLE_ITEM, SAMPLE_CONFIG)
    assert result["id"] == "42"
    assert result["title"] == "Test Item"
    assert result["stage"] == "Open"
    assert result["deliveryOwner"]["displayName"] == "John Doe"
    assert result["deliveryOwner"]["email"] == "john@example.org"
    assert result["why"] == "Business reason"
    assert result["dueDate"] == "2026-06-30"
    assert result["stageCategory"] == "open"


def test_normalize_missing_field():
    item = {"id": 1, "fields": {"Title": "Test"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    warnings = result["warnings"]
    assert len(warnings) > 0
    assert any("Stage" in w for w in warnings)


def test_normalize_stage_category():
    config = SAMPLE_CONFIG.copy()
    assert _get_stage_category("Open", config["stage_aliases"]) == "open"
    assert _get_stage_category("Blocked", config["stage_aliases"]) == "blocked"
    assert _get_stage_category("Done", config["stage_aliases"]) == "closed"
    assert _get_stage_category(None, config["stage_aliases"]) == "unknown"
    assert _get_stage_category("UnknownStatus", config["stage_aliases"]) == "unknown"


def test_parse_person_dict():
    result = _parse_person({"displayName": "Alice", "email": "alice@test.com"})
    assert result["displayName"] == "Alice"
    assert result["email"] == "alice@test.com"


def test_parse_person_string():
    result = _parse_person("Bob")
    assert result["displayName"] == "Bob"
    assert result["email"] is None


def test_parse_person_none():
    assert _parse_person(None) is None


def test_parse_date():
    assert "2026-06-30" in _parse_date("2026-06-30")
    assert _parse_date(None) is None


def test_build_source_url():
    url = _build_source_url("https://sharepoint.com/sites/Test", "WorkBoard", "42")
    assert "DispForm.aspx?ID=42" in url


def test_normalize_raw_fields():
    cfg = {**SAMPLE_CONFIG, "output": {"include_raw_fields": True}}
    result = normalize_item(SAMPLE_ITEM, cfg)
    assert "raw" in result
    assert result["raw"]["Title"] == "Test Item"
