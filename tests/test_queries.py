from datetime import datetime, timezone, timedelta

from workboard_cli.queries import (
    _is_overdue,
    _owner_matches,
    filter_blocked,
    filter_by_owner,
    filter_open,
    filter_overdue,
    filter_recently_updated,
)

NOW = datetime.now(timezone.utc)

SAMPLE_ITEMS = [
    {
        "id": "1",
        "title": "Open Item",
        "stageCategory": "open",
        "dueDate": (NOW + timedelta(days=5)).isoformat(),
        "deliveryOwner": {"displayName": "Alice", "email": "alice@test.com"},
        "modifiedDate": NOW.isoformat(),
    },
    {
        "id": "2",
        "title": "Overdue Open Item",
        "stageCategory": "open",
        "dueDate": (NOW - timedelta(days=2)).isoformat(),
        "deliveryOwner": {"displayName": "Bob", "email": "bob@test.com"},
        "modifiedDate": (NOW - timedelta(days=10)).isoformat(),
    },
    {
        "id": "3",
        "title": "Blocked Item",
        "stageCategory": "blocked",
        "dueDate": (NOW + timedelta(days=10)).isoformat(),
        "deliveryOwner": {"displayName": "Alice", "email": "alice@test.com"},
        "modifiedDate": (NOW - timedelta(days=1)).isoformat(),
    },
    {
        "id": "4",
        "title": "Closed Item",
        "stageCategory": "closed",
        "dueDate": (NOW - timedelta(days=30)).isoformat(),
        "deliveryOwner": {"displayName": "Charlie", "email": "charlie@test.com"},
        "modifiedDate": (NOW - timedelta(days=60)).isoformat(),
    },
]


def test_filter_open():
    result = filter_open(SAMPLE_ITEMS)
    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[1]["id"] == "2"


def test_filter_overdue():
    result = filter_overdue(SAMPLE_ITEMS)
    assert len(result) == 1
    assert result[0]["id"] == "2"


def test_filter_blocked():
    result = filter_blocked(SAMPLE_ITEMS)
    assert len(result) == 1
    assert result[0]["id"] == "3"


def test_filter_by_owner():
    result = filter_by_owner(SAMPLE_ITEMS, "Alice")
    assert len(result) == 2


def test_filter_by_owner_email():
    result = filter_by_owner(SAMPLE_ITEMS, "bob@test.com")
    assert len(result) == 1


def test_filter_by_owner_case_insensitive():
    result = filter_by_owner(SAMPLE_ITEMS, "alice")
    assert len(result) == 2


def test_filter_recently_updated():
    result = filter_recently_updated(SAMPLE_ITEMS, 5)
    assert len(result) == 2
    assert "1" in [i["id"] for i in result]
    assert "3" in [i["id"] for i in result]


def test_is_overdue_closed_never_overdue():
    item = {"stageCategory": "closed", "dueDate": (NOW - timedelta(days=1)).isoformat()}
    assert _is_overdue(item) is False


def test_is_overdue_no_due_date():
    item = {"stageCategory": "open", "dueDate": None}
    assert _is_overdue(item) is False


def test_owner_matches_no_owner():
    assert _owner_matches({"deliveryOwner": None}, "Alice") is False
