from workboard_cli.normalize import (
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
        "scope": "Scope",
        "requirements": "Requirements",
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
    """Required field absence warns; optional field absence is silent."""
    item = {"id": 1, "fields": {"Title": "Test"}}
    result = normalize_item(item, SAMPLE_CONFIG)
    warnings = result["warnings"]
    assert len(warnings) > 0
    assert any("Created" in w for w in warnings), "Required field 'Created' should warn"
    assert any("Modified" in w for w in warnings), "Required field 'Modified' should warn"
    stage_warnings = [w for w in warnings if "Stage" in w]
    assert len(stage_warnings) == 0, "Optional field 'Stage' should not warn"


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

# --- U-1: Category sentinels, diagnostics, and field-state policy ---

DOCUMENTED_KEYS = [
    "id", "title", "stage", "deliveryOwner", "decisionAuthority",
    "acceptanceAuthority", "why", "dueDate", "dateCommitted", "dateStart",
    "dateClosed", "createdDate", "modifiedDate", "stageCategory",
    "cycleTimeDays", "cycleTimeAnomaly", "relProject", "workBriefLinks",
    "whyText", "scheduleText", "scopeText", "requirementsText",
    "acceptanceCriteriaText", "deliverablesText",
    "workIntake", "description", "priorityStatus", "sourceUrl", "raw",
    "warnings",
]


def test_normalize_item_optional_absence_uses_category_sentinels_without_warning():
    """AE14 -- Supply only required source values; optional fields use sentinels silently."""
    item = {
        "id": 7,
        "fields": {
            "Title": "Minimal Item",
            "Created": "2026-01-01T00:00:00Z",
            "Modified": "2026-01-02T00:00:00Z",
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=7",
    }
    result = normalize_item(item, SAMPLE_CONFIG)

    for key in DOCUMENTED_KEYS:
        assert key in result, f"Documented key '{key}' missing from WorkItem"

    assert result["id"] == "7"
    assert result["title"] == "Minimal Item"
    assert result["stage"] is None
    assert result["deliveryOwner"] is None
    assert result["decisionAuthority"] is None
    assert result["acceptanceAuthority"] is None
    assert result["why"] is None
    assert result["dueDate"] is None
    assert result["dateCommitted"] is None
    assert result["dateStart"] is None
    assert result["dateClosed"] is None
    assert result["relProject"] is None
    assert result["workBriefLinks"] == []
    assert result["whyText"] == ""
    assert result["scheduleText"] == ""
    assert result["scopeText"] == ""
    assert result["requirementsText"] == ""
    assert result["acceptanceCriteriaText"] == ""
    assert result["deliverablesText"] == ""
    assert result["workIntake"] is None
    assert result["description"] is None
    assert result["priorityStatus"] is None
    assert result["raw"] == {}
    assert result["warnings"] == []


def test_normalize_item_unavailable_mapping_and_required_absence_warn():
    """AE15 -- Required field absence emits warnings."""
    item = {
        "id": 8,
        "fields": {
            "Title": "Warning Item",
            "Stage": "Open",
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=8",
    }
    result = normalize_item(item, SAMPLE_CONFIG)
    warnings = result["warnings"]
    assert len(warnings) >= 2
    assert any("Created" in w for w in warnings), "Required field 'Created' absence should warn"
    assert any("Modified" in w for w in warnings), "Required field 'Modified' absence should warn"


def test_normalize_item_malformed_project_date_person_and_lookup_warn():
    """AE4/AE15 -- Malformed project, date, person, and work-intake produce sentinels and warnings."""
    item = {
        "id": 9,
        "fields": {
            "Title": "Malformed",
            "Created": "2026-01-01T00:00:00Z",
            "Modified": "2026-01-02T00:00:00Z",
            "RelProject": "not-valid-json",
            "DateDue": "not-a-date",
            "DeliveryOwner": 12345,
            "DecisionAuthority": True,
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=9",
    }
    cfg = {**SAMPLE_CONFIG, "output": {"include_raw_fields": True}}
    result = normalize_item(item, cfg)

    assert result["relProject"] is None
    assert any("RelProject" in w for w in result["warnings"])

    assert result["dueDate"] is None

    assert result["deliveryOwner"] is None
    assert any("person" in w.lower() for w in result["warnings"]), "Malformed person should warn"

    assert result["decisionAuthority"] is None
    # Both DeliveryOwner (int) and DecisionAuthority (bool) are malformed person values
    person_warnings = [w for w in result["warnings"] if "person" in w.lower()]
    assert len(person_warnings) >= 2, f"Expected 2+ person warnings, got {len(person_warnings)}"

    assert result["raw"]["RelProject"] == "not-valid-json"


def test_normalize_item_legacy_person_string_is_valid_without_warning():
    """AE7 -- Legacy person-name string normalizes without warning."""
    item = {
        "id": 10,
        "fields": {
            "Title": "Legacy Person",
            "DeliveryOwner": "Example Person",
            "Created": "2026-01-01T00:00:00Z",
            "Modified": "2026-01-02T00:00:00Z",
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=10",
    }
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["deliveryOwner"] == {
        "displayName": "Example Person",
        "email": None,
        "id": None,
    }
    delivery_warnings = [w for w in result["warnings"] if "DeliveryOwner" in w]
    assert delivery_warnings == [], f"Legacy person string should not warn: {delivery_warnings}"


def test_parse_work_brief_filters_invalid_entries_and_warns():
    """AE11/R16 -- Invalid work-brief anchors are omitted with warnings; valid siblings survive."""
    html = (
        '<a href="https://valid.example.com/doc.pdf">Valid Doc</a>'
        '<a href="/relative/path">Relative Link</a>'
        '<a href="ftp://invalid.example.com/file">FTP Link</a>'
        '<a href="https://valid2.example.com/page"></a>'
        '<a href="https://valid3.example.com/other">Valid 3</a>'
    )
    w = []
    result = _parse_work_brief(html, "https://sharepoint.com/sites/Test", w)
    assert len(result) == 3
    assert result[0]["text"] == "Valid Doc"
    assert result[0]["url"] == "https://valid.example.com/doc.pdf"
    assert result[1]["text"] == "Relative Link"
    assert result[1]["url"] == "https://sharepoint.com/relative/path"
    assert result[2]["text"] == "Valid 3"
    assert result[2]["url"] == "https://valid3.example.com/other"
    assert len(w) >= 1


def test_parse_work_brief_missing_or_empty_is_silent_empty_array():
    """AE11 -- Missing or empty RelWorkBrief yields [] with no warning."""
    assert _parse_work_brief(None, "https://example.com", []) == []
    w = []
    assert _parse_work_brief("", "https://example.com", w) == []
    assert w == []


def test_source_url_uses_validated_graph_item_web_url():
    """AE10/AE15 -- sourceUrl comes from raw item.webUrl, validated as absolute HTTP(S)."""
    item = {
        "id": 42,
        "fields": {"Title": "URL Test", "Created": "2026-01-01T00:00:00Z", "Modified": "2026-01-02T00:00:00Z"},
        "webUrl": "https://sharepoint.com/sites/Test/Lists/TestBoard/DispForm.aspx?ID=42",
    }
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["sourceUrl"] == "https://sharepoint.com/sites/Test/Lists/TestBoard/DispForm.aspx?ID=42"

    item_no_url = {
        "id": 43,
        "fields": {"Title": "No URL", "Created": "2026-01-01T00:00:00Z", "Modified": "2026-01-02T00:00:00Z"},
    }
    result2 = normalize_item(item_no_url, SAMPLE_CONFIG)
    assert result2["sourceUrl"] is None
    assert any("webUrl" in w for w in result2["warnings"])

    item_relative = {
        "id": 44,
        "fields": {"Title": "Relative URL", "Created": "2026-01-01T00:00:00Z", "Modified": "2026-01-02T00:00:00Z"},
        "webUrl": "/relative/path",
    }
    result3 = normalize_item(item_relative, SAMPLE_CONFIG)
    assert result3["sourceUrl"] is None
    assert any("webUrl" in w for w in result3["warnings"])


# --- U-2: Complete WorkItem capture projection ---


def test_normalize_item_adds_html_free_scope_and_requirements_text():
    """AE5/AE6 -- Scope and Requirements become HTML-free text; no aliases."""
    item = {
        "id": 20,
        "fields": {
            "Title": "Scope Test",
            "Created": "2026-01-01T00:00:00Z",
            "Modified": "2026-01-02T00:00:00Z",
            "Scope": "<p>Deploy to <b>three</b> regions by Q3.</p>",
            "Requirements": "<div>Must support &#58; unicode &#38; entities</div>",
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=20",
    }
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["scopeText"] == "Deploy to three regions by Q3."
    assert result["requirementsText"] == "Must support : unicode & entities"
    assert "scope" not in result
    assert "requirements" not in result
    assert "Scope" not in result
    assert "Requirements" not in result


def test_normalize_item_emits_only_canonical_project_date_and_link_names():
    """AE3/AE8/AE10 -- Only canonical names exist; prohibited aliases are absent."""
    item = {
        "id": 21,
        "fields": {
            "Title": "Canonical Test",
            "Created": "2026-01-01T00:00:00Z",
            "Modified": "2026-01-02T00:00:00Z",
            "DateDue": "2026-06-30",
            "DateCommitted": "2026-06-01",
            "DateStart": "2026-05-15",
            "DateClosed": "2026-07-01",
            "RelProject": '{"id":3,"text":"Retirement System"}',
            "RelWorkBrief": '<a href="https://example.com/doc">Doc</a>',
        },
        "webUrl": "https://sharepoint.com/sites/Test/Lists/TestBoard/DispForm.aspx?ID=21",
    }
    cfg = {**SAMPLE_CONFIG, "output": {"include_raw_fields": True}}
    result = normalize_item(item, cfg)
    assert result["relProject"] == {"id": 3, "text": "Retirement System"}
    assert result["dueDate"] == "2026-06-30"
    assert result["dateCommitted"] == "2026-06-01"
    assert result["dateStart"] == "2026-05-15"
    assert result["dateClosed"] == "2026-07-01"
    assert result["createdDate"] is not None
    assert result["modifiedDate"] is not None
    assert len(result["workBriefLinks"]) == 1
    assert result["sourceUrl"] == "https://sharepoint.com/sites/Test/Lists/TestBoard/DispForm.aspx?ID=21"

    prohibited = [
        "linkedProject", "due_date", "date_committed", "date_start",
        "date_closed", "created_date", "modified_date", "relatedLinks",
    ]
    for key in prohibited:
        assert key not in result, f"Prohibited alias '{key}' found in WorkItem"


def test_normalize_item_keeps_acceptance_and_deliverables_as_text_without_state():
    """AE9/AE13 -- Acceptance criteria and deliverables are text-only; no invented state."""
    item = {
        "id": 22,
        "fields": {
            "Title": "State Test",
            "Created": "2026-01-01T00:00:00Z",
            "Modified": "2026-01-02T00:00:00Z",
            "AcceptanceCriteria": "<p>All tests pass</p>",
            "Deliverables": "<ul><li>Doc A</li><li>Doc B</li></ul>",
            "DecisionAuthority": "Alice Smith",
            "AcceptanceAuthority": "Bob Jones",
            "DateDue": "2026-06-30",
            "DateClosed": "2026-07-01",
            "Stage": "Done",
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=22",
    }
    result = normalize_item(item, SAMPLE_CONFIG)
    assert result["acceptanceCriteriaText"] == "All tests pass"
    assert result["deliverablesText"] == "Doc ADoc B"
    state_keys = ["accepted", "complete", "closed", "isAccepted", "isComplete", "isClosed"]
    for key in state_keys:
        assert key not in result, f"Invented state key '{key}' found in WorkItem"


def test_normalize_item_raw_option_preserves_original_long_form_markup():
    """AE6 -- Raw fields preserve HTML markup while normalized text is plain."""
    item = {
        "id": 23,
        "fields": {
            "Title": "Raw Markup",
            "Created": "2026-01-01T00:00:00Z",
            "Modified": "2026-01-02T00:00:00Z",
            "Scope": "<p>Scope <b>bold</b></p>",
            "Requirements": "<div>Req <i>italic</i></div>",
            "AcceptanceCriteria": "<span>AC text</span>",
            "Deliverables": "<em>Del text</em>",
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=23",
    }
    cfg = {**SAMPLE_CONFIG, "output": {"include_raw_fields": True}}
    result = normalize_item(item, cfg)
    assert result["raw"]["Scope"] == "<p>Scope <b>bold</b></p>"
    assert result["raw"]["Requirements"] == "<div>Req <i>italic</i></div>"
    assert result["raw"]["AcceptanceCriteria"] == "<span>AC text</span>"
    assert result["raw"]["Deliverables"] == "<em>Del text</em>"
    assert result["scopeText"] == "Scope bold"
    assert result["requirementsText"] == "Req italic"
    assert result["acceptanceCriteriaText"] == "AC text"
    assert result["deliverablesText"] == "Del text"


def test_normalize_item_additive_keys_preserve_existing_values():
    """AE17 -- Only scopeText and requirementsText are added; all pre-existing values unchanged."""
    item = {
        "id": 24,
        "fields": {
            "Title": "Compatibility",
            "Stage": "Open",
            "DeliveryOwner": {"displayName": "Carol", "email": "carol@test.com"},
            "Why": "Business case",
            "DateDue": "2026-09-01",
            "DateCommitted": "2026-08-01",
            "DateStart": "2026-07-15",
            "DateClosed": None,
            "Created": "2026-06-01T00:00:00Z",
            "Modified": "2026-06-15T00:00:00Z",
            "RelProject": '{"id":5,"text":"New System"}',
            "CycleTime": "12",
            "Description": "A description",
            "PriorityStatus": "High",
            "Scope": "<p>Scope content</p>",
            "Requirements": "<p>Requirements content</p>",
        },
        "webUrl": "https://example.com/sites/Test/Lists/Test/DispForm.aspx?ID=24",
    }
    cfg = {**SAMPLE_CONFIG, "output": {"include_raw_fields": True}}
    result = normalize_item(item, cfg)

    assert result["id"] == "24"
    assert result["title"] == "Compatibility"
    assert result["stage"] == "Open"
    assert result["deliveryOwner"]["displayName"] == "Carol"
    assert result["why"] == "Business case"
    assert result["dueDate"] == "2026-09-01"
    assert result["dateCommitted"] == "2026-08-01"
    assert result["dateStart"] == "2026-07-15"
    assert result["dateClosed"] is None
    assert result["relProject"] == {"id": 5, "text": "New System"}
    assert result["cycleTimeDays"] == 12
    assert result["cycleTimeAnomaly"] is False
    assert result["description"] == "A description"
    assert result["priorityStatus"] == "High"
    assert result["scopeText"] == "Scope content"
    assert result["requirementsText"] == "Requirements content"
