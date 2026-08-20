import statistics
from datetime import UTC, datetime, timedelta


def _to_utc(dt: datetime) -> datetime:
    """Convert a datetime to UTC, handling both naive and aware inputs."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _is_overdue(item):
    if item["stageCategory"] == "closed":
        return False
    due = item.get("dueDate")
    if not due:
        return False
    try:
        due_dt = datetime.fromisoformat(due)
        return _to_utc(due_dt) < datetime.now(UTC)
    except (ValueError, TypeError):
        return False


def _is_recently_updated(item, days):
    modified = item.get("modifiedDate")
    if not modified:
        return False
    try:
        modified_dt = datetime.fromisoformat(modified)
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return _to_utc(modified_dt) >= cutoff
    except (ValueError, TypeError):
        return False


def _is_within_days(date_str, days):
    if not date_str:
        return False
    try:
        dt = datetime.fromisoformat(date_str)
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return _to_utc(dt) >= cutoff
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


def filter_new_items(items, days):
    return [i for i in items if _is_within_days(i.get("createdDate"), days)]


def filter_recently_completed(items, days):
    return [i for i in items if _is_within_days(i.get("dateClosed"), days)]


def filter_by_project(items, project_name):
    query_lower = project_name.lower()
    result = []
    for item in items:
        rp = item.get("relProject")
        if rp and isinstance(rp, dict):
            text = (rp.get("text") or "").lower()
            if query_lower in text:
                result.append(item)
    return result


def filter_by_stage(items, stage):
    stage_lower = stage.lower()
    return [i for i in items if (i.get("stage") or "").lower() == stage_lower]


def filter_by_decision_authority(items, person):
    query_lower = person.lower()
    result = []
    for item in items:
        da = item.get("decisionAuthority")
        if da and isinstance(da, dict):
            name = (da.get("displayName") or "").lower()
            if query_lower in name:
                result.append(item)
    return result


def compute_cycle_time_stats(items, group_by="owner"):
    valid_by_group = {}
    bogus_count = 0
    total_count = 0
    for item in items:
        total_count += 1
        if item.get("cycleTimeAnomaly"):
            bogus_count += 1
            continue
        days = item.get("cycleTimeDays")
        if days is None:
            continue
        if group_by == "owner":
            owner = item.get("deliveryOwner")
            key = (owner.get("displayName") or "Unknown") if owner else "Unknown"
        elif group_by == "stage":
            key = item.get("stage") or "Unknown"
        else:
            key = "Unknown"
        valid_by_group.setdefault(key, []).append(days)

    groups = {}
    for key, values in sorted(valid_by_group.items()):
        n = len(values)
        sorted_vals = sorted(values)
        median_val = statistics.median(sorted_vals)
        p95_idx = int(0.95 * (n - 1)) if n > 1 else 0
        groups[key] = {
            "median_days": median_val,
            "p95_days": sorted_vals[p95_idx],
            "count": n,
        }

    valid_count = sum(len(v) for v in valid_by_group.values())

    return {
        "total_items": total_count,
        "valid_count": valid_count,
        "bogus_count": bogus_count,
        "groups": groups,
    }
