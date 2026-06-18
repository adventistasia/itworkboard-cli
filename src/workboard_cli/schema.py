import json

from workboard_cli.sharepoint import get_list_columns


def export_schema(client, site_id, list_id, output_path):
    columns = get_list_columns(client, site_id, list_id)
    structured = []
    for col in columns:
        structured.append({
            "name": col.get("name"),
            "displayName": col.get("displayName"),
            "type": _get_column_type(col),
            "required": col.get("required", False),
            "lookup": _get_lookup_hint(col),
        })
    output = {"columns": structured, "count": len(structured)}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)
    return output_path


def _get_column_type(col):
    if "boolean" in col:
        return "boolean"
    if "text" in col:
        return "text"
    if "number" in col:
        return "number"
    if "dateTime" in col:
        return "datetime"
    if "lookup" in col:
        return "lookup"
    if "choice" in col:
        return "choice"
    if "personOrGroup" in col:
        return "personOrGroup"
    if "url" in col:
        return "url"
    return "unknown"


def _get_lookup_hint(col):
    if "lookup" in col:
        return col["lookup"].get("listId")
    return None
