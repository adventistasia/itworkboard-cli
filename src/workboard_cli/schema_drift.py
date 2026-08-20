import json
from pathlib import Path

from workboard_cli.schema import build_schema_columns
from workboard_cli.sharepoint import find_list, get_lists

# The six work-related lists whose schemas we track for drift.
WORK_RELATED_LISTS = ["WorkBoard", "Deliverables", "Tasks", "WorkIntake", "WorkReview", "Users"]


def export_all_schemas(client, site_id):
    lists_data = get_lists(client, site_id)
    schemas = {}
    for name in WORK_RELATED_LISTS:
        target = find_list(lists_data, name)
        if target is None:
            schemas[name] = None
        else:
            schemas[name] = build_schema_columns(client, site_id, target["id"])
    return schemas


def load_baseline(baseline_path):
    p = Path(baseline_path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def establish_baseline(baseline_path, current_schemas):
    p = Path(baseline_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(current_schemas, f, indent=2, default=str)
    return {"status": "ok", "baseline_established": True, "lists": list(current_schemas.keys())}


def diff_schemas(baseline, current):
    entries = []
    all_lists = sorted(set(list(baseline.keys()) + list(current.keys())))

    for list_name in all_lists:
        b_slot = baseline.get(list_name)
        c_slot = current.get(list_name)

        if b_slot is None and c_slot is None:
            continue
        if b_slot is None and c_slot is not None:
            entries.append({
                "list": list_name,
                "changeType": "list_added",
                "severity": "high",
                "column": None,
                "note": f"List '{list_name}' added to site.",
            })
            continue
        if b_slot is not None and c_slot is None:
            entries.append({
                "list": list_name,
                "changeType": "list_removed",
                "severity": "high",
                "column": None,
                "note": f"List '{list_name}' removed from site.",
            })
            continue

        b_cols = {c["name"]: c for c in b_slot.get("columns", [])}
        c_cols = {c["name"]: c for c in c_slot.get("columns", [])}
        all_cols = sorted(set(list(b_cols.keys()) + list(c_cols.keys())))

        for col_name in all_cols:
            b_col = b_cols.get(col_name)
            c_col = c_cols.get(col_name)

            if b_col is None and c_col is not None:
                entries.append({
                    "list": list_name,
                    "changeType": "column_added",
                    "severity": "low",
                    "column": col_name,
                    "note": f"Column '{col_name}' added to '{list_name}'.",
                })
                continue
            if b_col is not None and c_col is None:
                entries.append({
                    "list": list_name,
                    "changeType": "column_removed",
                    "severity": "low",
                    "column": col_name,
                    "note": f"Column '{col_name}' removed from '{list_name}'.",
                })
                continue

            b_type = b_col.get("type")
            c_type = c_col.get("type")
            if b_type != c_type:
                if b_type == "unknown" or c_type == "unknown":
                    sev = "low"
                elif b_type is None or c_type is None:
                    sev = "high"
                else:
                    sev = "medium"
                entries.append({
                    "list": list_name,
                    "changeType": "column_type_changed",
                    "severity": sev,
                    "column": col_name,
                    "note": f"Column '{col_name}' type changed from '{b_type}' to '{c_type}' in '{list_name}'.",
                })

            b_display = b_col.get("displayName")
            c_display = c_col.get("displayName")
            if b_display != c_display:
                entries.append({
                    "list": list_name,
                    "changeType": "column_display_name_changed",
                    "severity": "low",
                    "column": col_name,
                    "note": f"Column '{col_name}' display name changed from '{b_display}' to '{c_display}' in '{list_name}'.",
                })

            b_lookup = b_col.get("lookup")
            c_lookup = c_col.get("lookup")
            if b_lookup != c_lookup:
                entries.append({
                    "list": list_name,
                    "changeType": "column_lookup_target_changed",
                    "severity": "high",
                    "column": col_name,
                    "note": f"Column '{col_name}' lookup target changed in '{list_name}'.",
                })

    return entries
