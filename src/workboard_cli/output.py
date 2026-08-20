from datetime import UTC, datetime

from workboard_cli.observations import get_session_id


def _now_iso():
    return datetime.now(UTC).isoformat()


def _build_source(site_url, list_name=None, list_id=None):
    source = {"system": "sharepoint", "siteUrl": site_url}
    if list_name:
        source["listName"] = list_name
    if list_id:
        source["listId"] = list_id
    return source


def build_envelope(items, intent, config, list_id=None, filters=None):
    site_url = config.get("site_url", "")
    list_name = config.get("primary_list_name", "WorkBoard")
    return {
        "status": "ok",
        "intent": intent,
        "source": _build_source(site_url, list_name, list_id),
        "retrievedAt": _now_iso(),
        "sessionId": get_session_id(),
        "filters": filters or {},
        "result": {"count": len(items), "items": items},
        "warnings": _collect_warnings(items),
        "errors": [],
    }


def build_summary_envelope(summary, config, list_id=None, intent_name="manager_summary", filters=None):
    site_url = config.get("site_url", "")
    list_name = config.get("primary_list_name", "WorkBoard")
    return {
        "status": "ok",
        "intent": intent_name,
        "source": _build_source(site_url, list_name, list_id),
        "retrievedAt": _now_iso(),
        "sessionId": get_session_id(),
        "filters": filters or {},
        "result": summary,
        "warnings": [],
        "errors": [],
    }


def _collect_warnings(items):
    all_warnings = []
    for item in items:
        all_warnings.extend(item.get("warnings", []))
    return list(dict.fromkeys(all_warnings))
