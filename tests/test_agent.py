import pytest

from workboard_cli.agent import APPROVED_INTENTS, execute_intent, validate_intent
from workboard_cli.errors import WorkboardError

SAMPLE_RAW_ITEMS = [
    {
        "id": 1,
        "fields": {
            "Title": "Task 1",
            "Stage": "Open",
            "DeliveryOwner": {"displayName": "Alice"},
        },
    },
    {
        "id": 2,
        "fields": {
            "Title": "Task 2",
            "Stage": "Blocked",
            "DeliveryOwner": {"displayName": "Bob"},
        },
    },
]

SAMPLE_CONFIG = {
    "site_url": "https://sharepoint.com/sites/Test",
    "primary_list_name": "WorkBoard",
    "fields": {
        "title": "Title",
        "stage": "Stage",
        "delivery_owner": "DeliveryOwner",
        "decision_authority": "DecisionAuthority",
        "acceptance_authority": "AcceptanceAuthority",
        "work_intake": "WorkIntake",
        "rel_project": "RelProject",
        "rel_work_brief": "RelWorkBrief",
        "description": "Description",
        "priority_status": "PriorityStatus",
        "cycle_time": "CycleTime",
        "schedule": "Schedule",
        "acceptance_criteria": "AcceptanceCriteria",
        "deliverables": "Deliverables",
        "created": "Created",
        "modified": "Modified",
        "date_closed": "DateClosed",
    },
    "stage_aliases": {
        "open": ["Open"],
        "closed": ["Closed"],
        "blocked": ["Blocked"],
    },
    "output": {"include_raw_fields": False},
}


def test_approved_intents():
    assert "open_items" in APPROVED_INTENTS
    assert "overdue_items" in APPROVED_INTENTS
    assert "blocked_items" in APPROVED_INTENTS
    assert "items_by_owner" in APPROVED_INTENTS
    assert "recently_updated_items" in APPROVED_INTENTS
    assert "manager_summary" in APPROVED_INTENTS


def test_validate_intent_valid():
    validate_intent("open_items")


def test_validate_intent_invalid():
    with pytest.raises(WorkboardError) as exc:
        validate_intent("browse")
    assert exc.value.code == "unsupported_intent"


def test_execute_open_items():
    envelope = execute_intent("open_items", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "open_items"
    assert envelope["result"]["count"] == 1
    assert envelope["result"]["items"][0]["title"] == "Task 1"


def test_execute_blocked_items():
    envelope = execute_intent("blocked_items", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert envelope["result"]["count"] == 1
    assert envelope["result"]["items"][0]["title"] == "Task 2"


def test_execute_manager_summary():
    envelope = execute_intent("manager_summary", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert envelope["status"] == "ok"
    assert envelope["result"]["totalItems"] == 2


def test_execute_by_owner_missing_param():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("items_by_owner", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert exc.value.code == "validation_error"


def test_execute_by_owner():
    envelope = execute_intent("items_by_owner", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG, {"owner": "Alice"})
    assert envelope["result"]["count"] == 1


def test_execute_unsupported_intent():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("bad_intent", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert exc.value.code == "unsupported_intent"


def test_new_items_in_approved_intents():
    assert "new_items" in APPROVED_INTENTS
    assert "recently_completed_items" in APPROVED_INTENTS
    assert "cycle_time_stats" in APPROVED_INTENTS
    assert "items_by_project" in APPROVED_INTENTS
    assert "items_by_stage" in APPROVED_INTENTS
    assert "items_by_decision_authority" in APPROVED_INTENTS


def test_execute_new_items():
    envelope = execute_intent("new_items", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG, {"days": 30})
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "new_items"


def test_execute_new_items_missing_days():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("new_items", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert exc.value.code == "validation_error"


def test_execute_recently_completed_items():
    envelope = execute_intent("recently_completed_items", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG, {"days": 30})
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "recently_completed_items"


def test_execute_recently_completed_items_missing_days():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("recently_completed_items", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert exc.value.code == "validation_error"


def test_execute_cycle_time_stats():
    envelope = execute_intent("cycle_time_stats", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "cycle_time_stats"
    assert "bogus_count" in envelope["result"]


def test_execute_cycle_time_stats_invalid_group_by():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("cycle_time_stats", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG, {"group_by": "month"})
    assert exc.value.code == "validation_error"


def test_execute_items_by_project():
    envelope = execute_intent("items_by_project", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG, {"project": "Test"})
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "items_by_project"


def test_execute_items_by_project_missing_param():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("items_by_project", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert exc.value.code == "validation_error"


def test_execute_items_by_stage():
    envelope = execute_intent("items_by_stage", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG, {"stage": "Open"})
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "items_by_stage"


def test_execute_items_by_stage_missing_param():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("items_by_stage", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert exc.value.code == "validation_error"


def test_execute_items_by_decision_authority():
    envelope = execute_intent("items_by_decision_authority", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG, {"person": "Alice"})
    assert envelope["status"] == "ok"
    assert envelope["intent"] == "items_by_decision_authority"


def test_execute_items_by_decision_authority_missing_param():
    with pytest.raises(WorkboardError) as exc:
        execute_intent("items_by_decision_authority", SAMPLE_RAW_ITEMS, SAMPLE_CONFIG)
    assert exc.value.code == "validation_error"
