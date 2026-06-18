from datetime import datetime, timezone, timedelta

from workboard_cli.summaries import build_summary, render_markdown_summary

NOW = datetime.now(timezone.utc)

SAMPLE_ITEMS = [
    {
        "id": "1",
        "title": "Open Item",
        "stageCategory": "open",
        "dueDate": (NOW + timedelta(days=5)).isoformat(),
        "deliveryOwner": {"displayName": "Alice"},
        "modifiedDate": NOW.isoformat(),
    },
    {
        "id": "2",
        "title": "Overdue Open",
        "stageCategory": "open",
        "dueDate": (NOW - timedelta(days=1)).isoformat(),
        "deliveryOwner": {"displayName": "Bob"},
        "modifiedDate": NOW.isoformat(),
    },
    {
        "id": "3",
        "title": "Blocked",
        "stageCategory": "blocked",
        "dueDate": (NOW + timedelta(days=10)).isoformat(),
        "deliveryOwner": {"displayName": "Alice"},
        "modifiedDate": NOW.isoformat(),
    },
    {
        "id": "4",
        "title": "Closed",
        "stageCategory": "closed",
        "dueDate": (NOW - timedelta(days=30)).isoformat(),
        "deliveryOwner": None,
        "modifiedDate": (NOW - timedelta(days=60)).isoformat(),
    },
]


def test_build_summary_counts():
    summary = build_summary(SAMPLE_ITEMS)
    assert summary["totalItems"] == 4
    assert summary["byStageCategory"]["open"] == 2
    assert summary["byStageCategory"]["blocked"] == 1
    assert summary["byStageCategory"]["closed"] == 1
    assert summary["overdueCount"] == 1
    assert summary["blockedCount"] == 1


def test_build_summary_by_owner():
    summary = build_summary(SAMPLE_ITEMS)
    assert "Alice" in summary["byOwner"]
    assert "Bob" in summary["byOwner"]
    assert "Unknown" not in summary["byOwner"]


def test_render_markdown_summary():
    summary = build_summary(SAMPLE_ITEMS)
    md = render_markdown_summary(summary, "https://sharepoint.com", NOW.isoformat())
    assert "# WorkBoard Manager Summary" in md
    assert "## By Stage" in md
    assert "## By Owner" in md
    assert "Alice" in md
    assert "Bob" in md
