from unittest.mock import MagicMock

from workboard_cli.schema import _get_column_type, build_schema_columns, export_schema


def test_column_type_text():
    col = {"text": {"textType": "plain"}}
    assert _get_column_type(col) == "text"


def test_column_type_number():
    col = {"number": {}}
    assert _get_column_type(col) == "number"


def test_column_type_choice():
    col = {"choice": {}}
    assert _get_column_type(col) == "choice"


def test_column_type_person():
    col = {"personOrGroup": {}}
    assert _get_column_type(col) == "personOrGroup"


def test_column_type_lookup():
    col = {"lookup": {"listId": "abc"}}
    assert _get_column_type(col) == "lookup"


def test_build_schema_columns():
    client = MagicMock()
    client.get_all.return_value = [
        {"name": "Title", "displayName": "Title", "text": {"textType": "plain"}, "required": True},
        {"name": "Stage", "displayName": "Stage", "choice": {}},
    ]
    result = build_schema_columns(client, "site-1", "list-1")
    assert result["column_count"] == 2
    assert result["list_id"] == "list-1"
    assert len(result["columns"]) == 2
    assert result["columns"][0]["name"] == "Title"
    assert result["columns"][0]["type"] == "text"


def test_export_schema_writes_count(tmp_path):
    client = MagicMock()
    client.get_all.return_value = [
        {"name": "Title", "displayName": "Title", "text": {}},
    ]
    out_path = str(tmp_path / "schema.json")
    result = export_schema(client, "site-1", "list-1", out_path)
    assert result == out_path
    import json
    with open(out_path) as f:
        data = json.load(f)
    assert "columns" in data
    assert data["count"] == 1
