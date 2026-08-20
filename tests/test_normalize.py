from workboard_cli.normalize import (
    _build_source_url,
    _coerce_cycle_time,
    _expand_work_intake,
    _extract_long_form_text,
    _get_stage_category,
    _parse_date,
    _parse_person,
    _parse_rel_project,
    _parse_work_brief,
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
        "who": "Who",
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
    "stage_aliases": {
        "open": ["Open", "In Progress", "New", "Definition", "Delivery"],
        "closed": ["Closed", "Done", "Completed", "Cancelled", "Canceled", "Tabled"],
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


def test_stage_category_tabled():
    assert _get_stage_category("Tabled", SAMPLE_CONFIG["stage_aliases"]) == "closed"


def test_stage_category_canceled():
    assert _get_stage_category("Canceled", SAMPLE_CONFIG["stage_aliases"]) == "closed"


def test_stage_category_cancelled_regression():
    assert _get_stage_category("Cancelled", SAMPLE_CONFIG["stage_aliases"]) == "closed"


def test_stage_category_definition():
    assert _get_stage_category("Definition", SAMPLE_CONFIG["stage_aliases"]) == "open"


def test_stage_category_delivery():
    assert _get_stage_category("Delivery", SAMPLE_CONFIG["stage_aliases"]) == "open"


def test_stage_category_new_regression():
    assert _get_stage_category("New", SAMPLE_CONFIG["stage_aliases"]) == "open"


def test_normalize_item_tabled_stage():
    item = {"id": 1, "fields": {"Title": "Tabled Item", "Stage": "Tabled"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["stageCategory"] == "closed"
    assert result["stage"] == "Tabled"


def test_coerce_cycle_time_valid():
    w = []
    result = _coerce_cycle_time("8", w)
    assert result == {"cycleTimeDays": 8, "cycleTimeAnomaly": False}
    assert len(w) == 0


def test_coerce_cycle_time_anomalous():
    w = []
    result = _coerce_cycle_time("-46,113", w)
    assert result == {"cycleTimeDays": None, "cycleTimeAnomaly": True}
    assert len(w) == 1
    assert "-46,113" in w[0]


def test_coerce_cycle_time_not_a_number():
    w = []
    result = _coerce_cycle_time("not a number", w)
    assert result == {"cycleTimeDays": None, "cycleTimeAnomaly": True}


def test_coerce_cycle_time_none():
    w = []
    result = _coerce_cycle_time(None, w)
    assert result == {"cycleTimeDays": None, "cycleTimeAnomaly": False}
    assert len(w) == 0


def test_coerce_cycle_time_negative():
    w = []
    result = _coerce_cycle_time("-5", w)
    assert result == {"cycleTimeDays": None, "cycleTimeAnomaly": True}


def test_normalize_item_cycle_time():
    item = {"id": 1, "fields": {"Title": "Test", "CycleTime": "-46,216"}}
    cfg = {**SAMPLE_CONFIG, "output": {"include_raw_fields": True}}
    result = normalize_item(item, cfg)
    assert result["cycleTimeDays"] is None
    assert result["cycleTimeAnomaly"] is True
    assert any("CycleTime" in w for w in result["warnings"])
    assert result["raw"]["CycleTime"] == "-46,216"


def test_normalize_item_cycle_time_valid():
    item = {"id": 1, "fields": {"Title": "Test", "CycleTime": "8"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["cycleTimeDays"] == 8
    assert result["cycleTimeAnomaly"] is False


def test_parse_rel_project_valid():
    w = []
    result = _parse_rel_project('{"id":3,"text":"Retirement System"}', w)
    assert result == {"id": 3, "text": "Retirement System"}
    assert len(w) == 0


def test_parse_rel_project_malformed():
    w = []
    result = _parse_rel_project("not json", w)
    assert result is None
    assert len(w) == 1
    assert "not valid JSON" in w[0]


def test_parse_rel_project_none():
    w = []
    result = _parse_rel_project(None, w)
    assert result is None
    assert len(w) == 0


def test_normalize_item_rel_project():
    item = {"id": 1, "fields": {"Title": "Test", "RelProject": '{"id":3,"text":"Retirement System"}'}}
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["relProject"] == {"id": 3, "text": "Retirement System"}


def test_normalize_item_rel_project_malformed():
    cfg = {**SAMPLE_CONFIG, "output": {"include_raw_fields": True}}
    item = {"id": 1, "fields": {"Title": "Test", "RelProject": "not json"}}
    result = normalize_item(item, cfg)
    assert result["relProject"] is None
    assert result["raw"]["RelProject"] == "not json"
    assert any("RelProject" in w for w in result["warnings"])


def test_parse_work_brief_valid():
    html = '<div><a href="/&#58;w&#58;/r/sites/itdocumentcontrol/Shared%20Documents/Workboard/01%20Develop.docx?d=w08f&amp;csf=1&amp;web=1&amp;e=Lzq60F">01 Develop.docx</a></div>'
    site = "https://southernasiapacific.sharepoint.com/sites/ITWorkboard"
    w = []
    result = _parse_work_brief(html, site, w)
    assert len(result) == 1
    assert result[0]["text"] == "01 Develop.docx"
    assert "southernasiapacific.sharepoint.com" in result[0]["url"]
    assert "&csf=1" in result[0]["url"]


def test_parse_work_brief_no_links():
    assert _parse_work_brief("<div>Just text</div>", "https://example.com", []) == []


def test_parse_work_brief_none():
    assert _parse_work_brief(None, "https://example.com", []) == []


def test_extract_long_form_text():
    html = '<div class="ExternalClass1ED5E4D75D7D4844945CC8352F57DB4C"><p>Outcome&#58; Finalized</p></div>'
    result = _extract_long_form_text(html)
    assert result == "Outcome: Finalized"


def test_extract_long_form_text_collapses_whitespace():
    html = "<p>  Hello   world  </p>"
    result = _extract_long_form_text(html)
    assert result == "Hello world"


def test_expand_work_intake_string():
    result = _expand_work_intake("House 143 AP Installation")
    assert result == [{"lookupId": None, "lookupValue": "House 143 AP Installation"}]


def test_expand_work_intake_none():
    assert _expand_work_intake(None) is None


def test_expand_work_intake_list():
    raw = [{"LookupId": 1, "LookupValue": "Item A"}, {"LookupId": 2, "LookupValue": "Item B"}]
    result = _expand_work_intake(raw)
    assert len(result) == 2
    assert result[0]["lookupId"] == 1
    assert result[1]["lookupValue"] == "Item B"


def test_normalize_item_description_priority_status():
    item = {
        "id": 1,
        "fields": {"Title": "Test", "Description": "Some desc", "PriorityStatus": "High"},
    }
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["description"] == "Some desc"
    assert result["priorityStatus"] == "High"


def test_normalize_item_description_absent():
    item = {"id": 1, "fields": {"Title": "Test"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["description"] is None
    assert result["priorityStatus"] is None


def test_normalize_item_delivery_owner_string():
    item = {"id": 1, "fields": {"Title": "Test", "DeliveryOwner": "Dennis Arquillano"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["deliveryOwner"] == {"displayName": "Dennis Arquillano", "email": None, "id": None}


def test_normalize_item_work_intake_string():
    item = {"id": 1, "fields": {"Title": "Test", "WorkIntake": "House 143 AP Installation"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["workIntake"] == [{"lookupId": None, "lookupValue": "House 143 AP Installation"}]


def test_normalize_item_work_intake_none():
    item = {"id": 1, "fields": {"Title": "Test"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["workIntake"] is None
