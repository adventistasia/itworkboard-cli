from typer.testing import CliRunner

from workboard_cli.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Read-only CLI" in result.stdout


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "workboard-cli v" in result.stdout


def test_auth_help():
    result = runner.invoke(app, ["auth", "--help"])
    assert result.exit_code == 0


def test_site_help():
    result = runner.invoke(app, ["site", "--help"])
    assert result.exit_code == 0


def test_lists_help():
    result = runner.invoke(app, ["lists", "--help"])
    assert result.exit_code == 0


def test_schema_help():
    result = runner.invoke(app, ["schema", "--help"])
    assert result.exit_code == 0


def test_items_help():
    result = runner.invoke(app, ["items", "--help"])
    assert result.exit_code == 0


def test_query_help():
    result = runner.invoke(app, ["query", "--help"])
    assert result.exit_code == 0


def test_summary_help():
    result = runner.invoke(app, ["summary", "--help"])
    assert result.exit_code == 0


def test_agent_help():
    result = runner.invoke(app, ["agent", "--help"])
    assert result.exit_code == 0


def test_config_help():
    result = runner.invoke(app, ["config", "--help"])
    assert result.exit_code == 0


def test_agent_query_unsupported_intent():
    result = runner.invoke(app, ["agent", "query", "--intent", "browse"])
    assert result.exit_code == 1
    assert "unsupported_intent" in result.stdout


def test_auth_status_authenticated():
    from unittest.mock import patch
    with patch("workboard_cli.cli.check_auth", return_value=True):
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert '"authenticated": true' in result.stdout


def test_auth_status_not_authenticated():
    from unittest.mock import patch
    with patch("workboard_cli.cli.check_auth", return_value=False):
        result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert '"authenticated": false' in result.stdout



