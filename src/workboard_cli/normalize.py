import html as html_mod
import json
import re
from datetime import datetime


def _get_field(raw_fields, field_name, warnings):
    value = raw_fields.get(field_name)
    if value is None:
        lookup_id_name = f"{field_name}LookupId"
        value = raw_fields.get(lookup_id_name)
        if value is not None:
            return value
        warnings.append(f"Field '{field_name}' not found in SharePoint item.")
    return value


def _get_mapped_field(raw_fields, field_name, warnings):
    """Read a mapped field with optional-absence semantics.

    Returns the value when present, None when genuinely absent (no warning).
    Warns when the field name is configured but not found in the item
    (unavailable mapping).
    """
    if not field_name:
        return None
    value = raw_fields.get(field_name)
    if value is None:
        lookup_id_name = f"{field_name}LookupId"
        value = raw_fields.get(lookup_id_name)
        if value is not None:
            return value
        warnings.append(f"Field '{field_name}' not found in SharePoint item.")
    return value


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, str):
        if "T" not in value and " " not in value:
            return value
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))  # noqa: FURB162
            return dt.isoformat()
        except (ValueError, TypeError):
            return value
    return str(value)


def _parse_person(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return {
            "displayName": value.get("displayName") or value.get("title", ""),
            "email": value.get("email") or value.get("Email", ""),
            "id": value.get("LookupId") or value.get("id"),
        }
    if isinstance(value, str):
        return {"displayName": value, "email": None, "id": None}
    return {"displayName": str(value), "email": None, "id": None}


def _coerce_cycle_time(raw_value, warnings):
    if raw_value is None or (isinstance(raw_value, str) and raw_value.strip() == ""):
        return {"cycleTimeDays": None, "cycleTimeAnomaly": False}
    cleaned = str(raw_value).replace(",", "")
    try:
        days = int(cleaned)
    except (ValueError, TypeError):
        warnings.append(
            f"CycleTime value '{raw_value}' is anomalous (non-integer or negative)"
        )
        return {"cycleTimeDays": None, "cycleTimeAnomaly": True}
    if days < 0:
        warnings.append(
            f"CycleTime value '{raw_value}' is anomalous (non-integer or negative)"
        )
        return {"cycleTimeDays": None, "cycleTimeAnomaly": True}
    return {"cycleTimeDays": days, "cycleTimeAnomaly": False}


def _parse_rel_project(raw_value, warnings):
    if raw_value is None or (isinstance(raw_value, str) and raw_value.strip() == ""):
        return None
    try:
        parsed = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        warnings.append(f"RelProject value is not valid JSON: '{raw_value}'")
        return None
    if isinstance(parsed, dict) and isinstance(parsed.get("id"), int) and isinstance(parsed.get("text"), str):
        return {"id": parsed["id"], "text": parsed["text"]}
    warnings.append(f"RelProject value is not valid JSON: '{raw_value}'")
    return None


def _parse_work_brief(html, site_url, warnings):
    if not html:
        return []
    from urllib.parse import urljoin
    results = []
    for match in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL):
        href_raw = match.group(1)
        inner = match.group(2)
        href = html_mod.unescape(href_raw)
        text = re.sub(r'<[^>]+>', '', inner).strip()
        text = html_mod.unescape(text)
        if not text:
            warnings.append(
                f"Work brief anchor with empty text omitted: href='{href}'"
            )
            continue
        abs_url = urljoin(site_url + "/", href)
        if not abs_url.startswith("http"):
            warnings.append(
                f"Work brief anchor with non-HTTP URL omitted: href='{href}'"
            )
            continue
        results.append({"url": abs_url, "text": text})
    return results


def _extract_long_form_text(html):
    if not html:
        return ""
    decoded = html_mod.unescape(html)
    text = re.sub(r'<[^>]+>', '', decoded)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _expand_work_intake(raw_value):
    if raw_value is None or (isinstance(raw_value, str) and raw_value.strip() == ""):
        return None
    if isinstance(raw_value, str):
        return [{"lookupId": None, "lookupValue": raw_value}]
    if isinstance(raw_value, list):
        result = []
        for item in raw_value:
            if isinstance(item, dict):
                result.append({
                    "lookupId": item.get("LookupId") or item.get("lookupId"),
                    "lookupValue": item.get("LookupValue") or item.get("lookupValue", ""),
                })
        return result if result else None
    return None


def _get_stage_category(stage, stage_aliases):
    if not stage:
        return "unknown"
    stage_lower = stage.lower()
    for category, aliases in stage_aliases.items():
        for alias in aliases:
            if alias.lower() == stage_lower:
                return category
    return "unknown"


def _build_source_url(site_url, list_name, item_id):
    base = site_url.rstrip("/")
    encoded = list_name.replace(" ", "%20")
    return f"{base}/Lists/{encoded}/DispForm.aspx?ID={item_id}"


def _validate_source_url(item, warnings):
    """Validate the item's webUrl as the sole sourceUrl input.

    Returns the absolute HTTP(S) URL when valid, None plus a warning
    when absent, relative, or unsupported-scheme.
    """
    web_url = item.get("webUrl")
    if isinstance(web_url, str) and web_url.strip():
        if web_url.startswith(("http://", "https://")):
            return web_url
        warnings.append(
            f"sourceUrl from webUrl is not a valid absolute URL: '{web_url}'"
        )
        return None
    warnings.append("sourceUrl unavailable: item has no webUrl.")
    return None


def normalize_item(item, config):
    raw_fields = item.get("fields", {})
    item_id = str(item.get("id", ""))
    field_map = config.get("fields", {})
    stage_aliases = config.get("stage_aliases", {})
    site_url = config.get("site_url", "")
    output_cfg = config.get("output", {})

    warnings = []

    stage = _get_mapped_field(raw_fields, field_map.get("stage"), warnings)
    delivery_owner_raw = _get_mapped_field(
        raw_fields, field_map.get("delivery_owner"), warnings
    )

    cycle_time_raw = raw_fields.get(field_map.get("cycle_time"))
    if cycle_time_raw is None:
        lookup_id_name = f"{field_map.get('cycle_time')}LookupId"
        cycle_time_raw = raw_fields.get(lookup_id_name)
    ct = _coerce_cycle_time(cycle_time_raw, warnings)

    rel_project_raw = raw_fields.get(field_map.get("rel_project"))
    rel_project = _parse_rel_project(rel_project_raw, warnings)

    rel_work_brief_raw = raw_fields.get(field_map.get("rel_work_brief"))
    work_brief_links = _parse_work_brief(rel_work_brief_raw, site_url, warnings)

    why_raw = raw_fields.get(field_map.get("why"))
    schedule_raw = raw_fields.get(field_map.get("schedule"))
    scope_raw = raw_fields.get(field_map.get("scope"))
    requirements_raw = raw_fields.get(field_map.get("requirements"))
    acceptance_raw = raw_fields.get(field_map.get("acceptance_criteria"))
    deliverables_raw = raw_fields.get(field_map.get("deliverables"))

    decision_auth_raw = _get_mapped_field(
        raw_fields, field_map.get("decision_authority"), warnings
    )
    acceptance_auth_raw = _get_mapped_field(
        raw_fields, field_map.get("acceptance_authority"), warnings
    )
    work_intake_raw = raw_fields.get(field_map.get("work_intake"))

    description_raw = raw_fields.get(field_map.get("description"))
    priority_status_raw = raw_fields.get(field_map.get("priority_status"))

    source_url = _validate_source_url(item, warnings)

    work_item = {
        "id": item_id,
        "title": _get_field(raw_fields, field_map.get("title"), warnings) or "",
        "stage": stage,
        "deliveryOwner": _parse_person(delivery_owner_raw),
        "decisionAuthority": _parse_person(decision_auth_raw),
        "acceptanceAuthority": _parse_person(acceptance_auth_raw),
        "why": why_raw,
        "dueDate": _parse_date(raw_fields.get(field_map.get("date_due"))),
        "dateCommitted": _parse_date(raw_fields.get(field_map.get("date_committed"))),
        "dateStart": _parse_date(raw_fields.get(field_map.get("date_start"))),
        "dateClosed": _parse_date(raw_fields.get(field_map.get("date_closed"))),
        "createdDate": _parse_date(
            _get_field(raw_fields, field_map.get("created"), warnings)
        ),
        "modifiedDate": _parse_date(
            _get_field(raw_fields, field_map.get("modified"), warnings)
        ),
        "stageCategory": _get_stage_category(stage, stage_aliases),
        "cycleTimeDays": ct["cycleTimeDays"],
        "cycleTimeAnomaly": ct["cycleTimeAnomaly"],
        "relProject": rel_project,
        "workBriefLinks": work_brief_links,
        "whyText": _extract_long_form_text(why_raw),
        "scheduleText": _extract_long_form_text(schedule_raw),
        "scopeText": _extract_long_form_text(scope_raw),
        "requirementsText": _extract_long_form_text(requirements_raw),
        "acceptanceCriteriaText": _extract_long_form_text(acceptance_raw),
        "deliverablesText": _extract_long_form_text(deliverables_raw),
        "workIntake": _expand_work_intake(work_intake_raw),
        "description": description_raw,
        "priorityStatus": priority_status_raw,
        "sourceUrl": source_url,
        "raw": {},
        "warnings": warnings,
    }

    if output_cfg.get("include_raw_fields", False):
        work_item["raw"] = raw_fields

    return work_item
