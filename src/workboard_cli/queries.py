from datetime import datetime, timezone, timedelta


def _is_overdue(item):
    if item["stageCategory"] == "closed":
        return False
    due = item.get("dueDate")
    if not due:
        return False
    try:
        due_dt = datetime.fromisoformat(due)
        return due_dt.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def _is_recently_updated(item, days):
    modified = item.get("modifiedDate")
    if not modified:
        return False
    try:
        modified_dt = datetime.fromisoformat(modified)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return modified_dt.replace(tzinfo=timezone.utc) >= cutoff
    except (ValueError, TypeError):
        return False


def _owner_matches(item, owner_query):
    owner = item.get("deliveryOwner")
    if not owner:
        return False
    query_lower = owner_query.lower()
    name = (owner.get("displayName") or "").lower()
    email = (owner.get("email") or "").lower()
    return query_lower in name or query_lower in email


def filter_open(items):
    return [i for i in items if i["stageCategory"] == "open"]


def filter_overdue(items):
    return [i for i in items if _is_overdue(i)]


def filter_blocked(items):
    return [i for i in items if i["stageCategory"] == "blocked"]


def filter_by_owner(items, owner):
    return [i for i in items if _owner_matches(i, owner)]


def filter_recently_updated(items, days):
    return [i for i in items if _is_recently_updated(i, days)]
