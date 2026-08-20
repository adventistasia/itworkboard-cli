from datetime import UTC, datetime, timedelta

from workboard_cli.queries import (
    _is_overdue,
    _owner_matches,
    compute_cycle_time_stats,
    filter_blocked,
    filter_by_decision_authority,
    filter_by_owner,
    filter_by_project,
    filter_by_stage,
    filter_new_items,
    filter_open,
    filter_overdue,
    filter_recently_completed,
    filter_recently_updated,
)

NOW = datetime.now(UTC)

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


def test_filter_new_items():
    items = [
        {"id": "1", "createdDate": (NOW - timedelta(days=3)).isoformat()},
        {"id": "2", "createdDate": (NOW - timedelta(days=10)).isoformat()},
        {"id": "3", "createdDate": None},
    ]
    result = filter_new_items(items, 7)
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_filter_new_items_excludes_unparseable():
    items = [{"id": "1", "createdDate": "not-a-date"}]
    result = filter_new_items(items, 7)
    assert len(result) == 0


def test_filter_recently_completed():
    items = [
        {"id": "1", "dateClosed": (NOW - timedelta(days=5)).isoformat()},
        {"id": "2", "dateClosed": (NOW - timedelta(days=30)).isoformat()},
        {"id": "3", "dateClosed": None},
        {"id": "4", "stageCategory": "closed", "dateClosed": (NOW - timedelta(days=2)).isoformat()},
    ]
    result = filter_recently_completed(items, 7)
    assert len(result) == 2
    assert "1" in [i["id"] for i in result]
    assert "4" in [i["id"] for i in result]


def test_filter_by_project():
    items = [
        {"id": "1", "relProject": {"id": 1, "text": "Retirement System"}},
        {"id": "2", "relProject": {"id": 2, "text": "Network Upgrade"}},
        {"id": "3", "relProject": None},
    ]
    result = filter_by_project(items, "Retirement")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_filter_by_project_case_insensitive():
    items = [
        {"id": "1", "relProject": {"id": 1, "text": "Retirement System"}},
    ]
    result = filter_by_project(items, "retirement")
    assert len(result) == 1


def test_filter_by_stage():
    items = [
        {"id": "1", "stage": "Tabled"},
        {"id": "2", "stage": "Open"},
        {"id": "3", "stage": "Tabled"},
    ]
    result = filter_by_stage(items, "Tabled")
    assert len(result) == 2


def test_filter_by_stage_case_insensitive():
    items = [{"id": "1", "stage": "Tabled"}]
    result = filter_by_stage(items, "tabled")
    assert len(result) == 1


def test_filter_by_decision_authority():
    items = [
        {"id": "1", "decisionAuthority": {"displayName": "Ryann Micua"}},
        {"id": "2", "decisionAuthority": {"displayName": "John Doe"}},
        {"id": "3", "decisionAuthority": None},
    ]
    result = filter_by_decision_authority(items, "Ryann")
    assert len(result) == 1
    assert result[0]["id"] == "1"


def test_compute_cycle_time_stats():
    items = [
        {"cycleTimeDays": 3, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Alice"}},
        {"cycleTimeDays": 5, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Alice"}},
        {"cycleTimeDays": 7, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Bob"}},
        {"cycleTimeDays": 8, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Bob"}},
        {"cycleTimeDays": 10, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Alice"}},
        {"cycleTimeDays": 12, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Bob"}},
        {"cycleTimeDays": 15, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Alice"}},
        {"cycleTimeDays": None, "cycleTimeAnomaly": True, "deliveryOwner": {"displayName": "Alice"}},
        {"cycleTimeDays": None, "cycleTimeAnomaly": True, "deliveryOwner": {"displayName": "Bob"}},
        {"cycleTimeDays": None, "cycleTimeAnomaly": False, "deliveryOwner": {"displayName": "Charlie"}},
    ]
    stats = compute_cycle_time_stats(items)
    assert stats["total_items"] == 10
    assert stats["bogus_count"] == 2
    assert stats["valid_count"] == 7
    assert "Alice" in stats["groups"]
    assert "Bob" in stats["groups"]
    assert stats["groups"]["Alice"]["count"] == 4
    assert stats["groups"]["Bob"]["count"] == 3


def test_compute_cycle_time_stats_group_by_stage():
    items = [
        {"cycleTimeDays": 3, "cycleTimeAnomaly": False, "stage": "Open"},
        {"cycleTimeDays": 5, "cycleTimeAnomaly": False, "stage": "Open"},
        {"cycleTimeDays": 7, "cycleTimeAnomaly": False, "stage": "Closed"},
    ]
    stats = compute_cycle_time_stats(items, group_by="stage")
    assert "Open" in stats["groups"]
    assert "Closed" in stats["groups"]
    assert stats["groups"]["Open"]["count"] == 2
