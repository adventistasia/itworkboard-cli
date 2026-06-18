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
        "created": "Created",
        "modified": "Modified",
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
