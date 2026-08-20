import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from workboard_cli.cli import app
from workboard_cli.schema_drift import (
    WORK_RELATED_LISTS,
    diff_schemas,
    establish_baseline,
    export_all_schemas,
    load_baseline,
)

runner = CliRunner()

MOCK_COLUMNS = [
    {"name": "Title", "displayName": "Title", "type": "text", "required": True, "lookup": None},
    {"name": "Stage", "displayName": "Stage", "type": "choice", "required": False, "lookup": None},
    {"name": "DeliveryOwner", "displayName": "Delivery Owner", "type": "lookup", "required": False, "lookup": "list-id-1"},
]


def test_work_related_lists():
    assert len(WORK_RELATED_LISTS) == 6
    assert "WorkBoard" in WORK_RELATED_LISTS
    assert "Users" in WORK_RELATED_LISTS


def test_export_all_schemas():
    client = MagicMock()
    mock_lists = [{"id": "id-1", "displayName": "WorkBoard", "name": "WorkBoard"}]
    client.get_all.return_value = mock_lists
    with patch("workboard_cli.schema_drift.get_lists", return_value=mock_lists), \
         patch("workboard_cli.schema_drift.find_list", side_effect=lambda lists, name: {"id": f"id-{name}"} if name == "WorkBoard" else None), \
         patch("workboard_cli.schema_drift.build_schema_columns", return_value={"columns": MOCK_COLUMNS, "column_count": 3, "list_id": "id-1"}):
        result = export_all_schemas(client, "site-id")
    assert "WorkBoard" in result
    assert result["WorkBoard"] is not None
    assert result["Deliverables"] is None


def test_diff_schemas_identical():
    schemas = {"WorkBoard": {"columns": MOCK_COLUMNS, "column_count": 3}}
    result = diff_schemas(schemas, schemas)
    assert result == []


def test_diff_schemas_list_added():
    baseline = {"WorkBoard": {"columns": [], "column_count": 0}}
    current = {"WorkBoard": {"columns": [], "column_count": 0}, "Deliverables": {"columns": [], "column_count": 0}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["changeType"] == "list_added"
    assert result[0]["severity"] == "high"


def test_diff_schemas_list_removed():
    baseline = {"WorkBoard": {"columns": [], "column_count": 0}, "Deliverables": {"columns": [], "column_count": 0}}
    current = {"WorkBoard": {"columns": [], "column_count": 0}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["changeType"] == "list_removed"
    assert result[0]["severity"] == "high"


def test_diff_schemas_column_added():
    baseline = {"WorkBoard": {"columns": [{"name": "Title", "type": "text"}], "column_count": 1}}
    current = {"WorkBoard": {"columns": [{"name": "Title", "type": "text"}, {"name": "NewCol", "type": "text"}], "column_count": 2}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["changeType"] == "column_added"
    assert result[0]["severity"] == "low"


def test_diff_schemas_column_removed():
    baseline = {"WorkBoard": {"columns": [{"name": "Title", "type": "text"}, {"name": "OldCol", "type": "text"}], "column_count": 2}}
    current = {"WorkBoard": {"columns": [{"name": "Title", "type": "text"}], "column_count": 1}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["changeType"] == "column_removed"
    assert result[0]["severity"] == "low"


def test_diff_schemas_type_changed_known():
    baseline = {"WorkBoard": {"columns": [{"name": "Col1", "type": "text"}], "column_count": 1}}
    current = {"WorkBoard": {"columns": [{"name": "Col1", "type": "choice"}], "column_count": 1}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["changeType"] == "column_type_changed"
    assert result[0]["severity"] == "medium"


def test_diff_schemas_type_changed_unknown():
    baseline = {"WorkBoard": {"columns": [{"name": "Col1", "type": "unknown"}], "column_count": 1}}
    current = {"WorkBoard": {"columns": [{"name": "Col1", "type": "text"}], "column_count": 1}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["severity"] == "low"


def test_diff_schemas_type_changed_none():
    baseline = {"WorkBoard": {"columns": [{"name": "Col1"}], "column_count": 1}}
    current = {"WorkBoard": {"columns": [{"name": "Col1", "type": "text"}], "column_count": 1}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["severity"] == "high"


def test_diff_schemas_lookup_target_changed():
    baseline = {"WorkBoard": {"columns": [{"name": "Owner", "type": "lookup", "lookup": "list-a"}], "column_count": 1}}
    current = {"WorkBoard": {"columns": [{"name": "Owner", "type": "lookup", "lookup": "list-b"}], "column_count": 1}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["changeType"] == "column_lookup_target_changed"
    assert result[0]["severity"] == "high"


def test_diff_schemas_display_name_changed():
    baseline = {"WorkBoard": {"columns": [{"name": "Col1", "displayName": "Old Name"}], "column_count": 1}}
    current = {"WorkBoard": {"columns": [{"name": "Col1", "displayName": "New Name"}], "column_count": 1}}
    result = diff_schemas(baseline, current)
    assert len(result) == 1
    assert result[0]["changeType"] == "column_display_name_changed"
    assert result[0]["severity"] == "low"


def test_diff_schemas_both_none_no_entry():
    baseline = {"WorkBoard": None}
    current = {"WorkBoard": None}
    result = diff_schemas(baseline, current)
    assert result == []


def test_load_baseline_missing():
    assert load_baseline("nonexistent/path.json") is None


def test_establish_baseline(tmp_path):
    path = str(tmp_path / "baseline.json")
    schemas = {"WorkBoard": {"columns": [], "column_count": 0}}
    result = establish_baseline(path, schemas)
    assert result["baseline_established"] is True
    assert Path(path).exists()
    loaded = load_baseline(path)
    assert loaded == schemas


def test_cli_schema_drift_first_run(tmp_path):
    baseline_path = str(tmp_path / "baseline.json")
    mock_cfg = {"site_url": "https://test.sharepoint.com", "primary_list_name": "TestBoard", "fields": {}}
    mock_site = {"id": "site-123"}
    mock_schemas = {"WorkBoard": {"columns": [], "column_count": 0, "list_id": "id-1"}}

    with patch("workboard_cli.cli._get_client", return_value=(mock_cfg, MagicMock())), \
         patch("workboard_cli.cli.get_site", return_value=mock_site), \
         patch("workboard_cli.schema_drift.export_all_schemas", return_value=mock_schemas), \
         patch("workboard_cli.schema_drift.load_baseline", return_value=None), \
         patch("workboard_cli.schema_drift.establish_baseline", return_value={"status": "ok", "baseline_established": True, "lists": ["WorkBoard"]}):
        result = runner.invoke(app, ["schema", "drift", "--baseline", baseline_path])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["baseline_established"] is True
    assert "source" in data
    assert "retrievedAt" in data
    assert "sessionId" in data


def test_cli_schema_drift_high_severity_exits_6(tmp_path):
    baseline_path = str(tmp_path / "baseline.json")
    mock_cfg = {"site_url": "https://test.sharepoint.com", "primary_list_name": "TestBoard", "fields": {}}
    mock_site = {"id": "site-123"}
    existing = {"WorkBoard": {"columns": [], "column_count": 0}}
    current = {"WorkBoard": {"columns": [], "column_count": 0}, "Deliverables": {"columns": [], "column_count": 0}}

    with patch("workboard_cli.cli._get_client", return_value=(mock_cfg, MagicMock())), \
         patch("workboard_cli.cli.get_site", return_value=mock_site), \
         patch("workboard_cli.schema_drift.export_all_schemas", return_value=current), \
         patch("workboard_cli.schema_drift.load_baseline", return_value=existing):
        result = runner.invoke(app, ["schema", "drift", "--baseline", baseline_path])
    assert result.exit_code == 6
    data = json.loads(result.stdout)
    assert data["summary"]["high"] >= 1


def test_cli_schema_drift_output_flag(tmp_path):
    baseline_path = str(tmp_path / "baseline.json")
    output_path = str(tmp_path / "out" / "drift.json")
    mock_cfg = {"site_url": "https://test.sharepoint.com", "primary_list_name": "TestBoard", "fields": {}}
    mock_site = {"id": "site-123"}
    existing = {"WorkBoard": {"columns": [], "column_count": 0}}
    current = {"WorkBoard": {"columns": [], "column_count": 0}}

    with patch("workboard_cli.cli._get_client", return_value=(mock_cfg, MagicMock())), \
         patch("workboard_cli.cli.get_site", return_value=mock_site), \
         patch("workboard_cli.schema_drift.export_all_schemas", return_value=current), \
         patch("workboard_cli.schema_drift.load_baseline", return_value=existing):
        result = runner.invoke(app, ["schema", "drift", "--baseline", baseline_path, "--output", output_path])
    assert result.exit_code == 0
    assert not result.stdout.strip(), "--output should suppress stdout"
    out_file = Path(output_path)
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["status"] == "ok"
    assert "drift" in data
