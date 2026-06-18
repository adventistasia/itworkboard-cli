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


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, str):
        if "T" not in value and " " not in value:
            return value
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
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
        }
    if isinstance(value, str):
        return {"displayName": value, "email": None}
    return {"displayName": str(value), "email": None}


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


def normalize_item(item, config):
    raw_fields = item.get("fields", {})
    item_id = str(item.get("id", ""))
    field_map = config.get("fields", {})
    stage_aliases = config.get("stage_aliases", {})
    site_url = config.get("site_url", "")
    list_name = config.get("primary_list_name", "WorkBoard")
    output_cfg = config.get("output", {})

    warnings = []

    stage = _get_field(raw_fields, field_map.get("stage"), warnings)
    delivery_owner_raw = _get_field(raw_fields, field_map.get("delivery_owner"), warnings)

    work_item = {
        "id": item_id,
        "title": _get_field(raw_fields, field_map.get("title"), warnings) or "",
        "stage": stage,
        "deliveryOwner": _parse_person(delivery_owner_raw),
        "why": _get_field(raw_fields, field_map.get("why"), warnings),
        "dueDate": _parse_date(_get_field(raw_fields, field_map.get("date_due"), warnings)),
        "dateCommitted": _parse_date(_get_field(raw_fields, field_map.get("date_committed"), warnings)),
        "dateStart": _parse_date(_get_field(raw_fields, field_map.get("date_start"), warnings)),
        "dateClosed": _parse_date(_get_field(raw_fields, field_map.get("date_closed"), warnings)),
        "createdDate": _parse_date(_get_field(raw_fields, field_map.get("created"), warnings)),
        "modifiedDate": _parse_date(_get_field(raw_fields, field_map.get("modified"), warnings)),
        "stageCategory": _get_stage_category(stage, stage_aliases),
        "sourceUrl": _build_source_url(site_url, list_name, item_id),
        "raw": {},
        "warnings": warnings,
    }

    if output_cfg.get("include_raw_fields", False):
        work_item["raw"] = raw_fields

    return work_item
