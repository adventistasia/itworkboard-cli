import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer
import yaml

from workboard_cli import __version__
from workboard_cli.agent import execute_intent, validate_intent
from workboard_cli.auth import check_auth, get_token
from workboard_cli.config import load_config
from workboard_cli.errors import WorkboardError
from workboard_cli.graph_client import GraphClient
from workboard_cli.normalize import normalize_item
from workboard_cli.output import build_envelope, build_summary_envelope
from workboard_cli.queries import (
    filter_blocked,
    filter_by_owner,
    filter_open,
    filter_overdue,
    filter_recently_updated,
)
from workboard_cli.schema import export_schema as _export_schema
from workboard_cli.sharepoint import (
    find_list,
    get_list_item,
    get_list_items,
    get_lists,
    get_site,
)
from workboard_cli.summaries import build_summary, render_markdown_summary

logger = logging.getLogger("workboard_cli")

app = typer.Typer(help="Read-only CLI for querying the SharePoint IT WorkBoard")
auth_app = typer.Typer(help="Authentication commands")
site_app = typer.Typer(help="Site information commands")
lists_app = typer.Typer(help="List discovery commands")
schema_app = typer.Typer(help="Schema export commands")
items_app = typer.Typer(help="Item retrieval commands")
query_app = typer.Typer(help="Operational query commands")
summary_app = typer.Typer(help="Summary commands")
agent_app = typer.Typer(help="Agent interface commands")
config_app = typer.Typer(help="Configuration commands")
self_app = typer.Typer(help="Self-inspection commands")

app.add_typer(auth_app, name="auth")
app.add_typer(site_app, name="site")
app.add_typer(lists_app, name="lists")
app.add_typer(schema_app, name="schema")
app.add_typer(items_app, name="items")
app.add_typer(query_app, name="query")
app.add_typer(summary_app, name="summary")
app.add_typer(agent_app, name="agent")
app.add_typer(config_app, name="config")
app.add_typer(self_app, name="self")


def _error_exit(e: WorkboardError, code=1):
    msg = {"status": "error", "error": e.to_dict()}
    print(json.dumps(msg, indent=2))
    raise typer.Exit(code)


def _get_client():
    cfg = load_config()
    token = get_token()
    return cfg, GraphClient(token)


def _fetch_items(cfg, client, list_name, limit=None):
    site = get_site(client, cfg["site_url"])
    site_id = site.get("id")
    lists_data = get_lists(client, site_id)
    target = find_list(lists_data, list_name)
    if not target:
        raise WorkboardError(
            "resource_not_found",
            f"List '{list_name}' not found on site.",
            "Use 'workboard lists discover' to see available lists.",
        )
    items = get_list_items(client, site_id, target["id"], limit=limit)
    return items, cfg, target


def _build_source(site_url, list_name=None, list_id=None):
    source = {"system": "sharepoint", "siteUrl": site_url}
    if list_name:
        source["listName"] = list_name
    if list_id:
        source["listId"] = list_id
    return source


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _version_callback(value: bool):
    if value:
        print(f"workboard-cli v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True, help="Show version"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
):
    if verbose:
        logging.basicConfig(level=logging.INFO)
        logger.info("Verbose logging enabled")


@auth_app.command()
def login():
    """Authenticate via Microsoft device code flow."""
    try:
        get_token(force=True)
        print("Authentication successful.")
    except WorkboardError as e:
        _error_exit(e, 2)


@auth_app.command()
def status():
    """Check authentication status."""
    if check_auth():
        print(json.dumps({"status": "ok", "authenticated": True}))
    else:
        print(json.dumps({"status": "ok", "authenticated": False}))


@site_app.command()
def info(
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Resolve and display SharePoint site information."""
    try:
        cfg, client = _get_client()
        site = get_site(client, cfg["site_url"])
        result = {
            "id": site.get("id"),
            "displayName": site.get("displayName"),
            "webUrl": site.get("webUrl"),
        }
        envelope = {
            "status": "ok",
            "source": _build_source(cfg["site_url"]),
            "result": result,
        }
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@lists_app.command("discover")
def lists_discover(
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Enumerate all lists on the SharePoint site."""
    try:
        cfg, client = _get_client()
        site = get_site(client, cfg["site_url"])
        site_id = site.get("id")
        lists_data = get_lists(client, site_id)
        cleaned = [
            {
                "id": lst.get("id"),
                "displayName": lst.get("displayName"),
                "name": lst.get("name"),
                "hidden": lst.get("hidden", False),
                "webUrl": f"{cfg['site_url']}/Lists/{lst.get('name', '')}",
            }
            for lst in lists_data
        ]
        envelope = {
            "status": "ok",
            "source": _build_source(cfg["site_url"]),
            "retrievedAt": _now_iso(),
            "result": {"count": len(cleaned), "lists": cleaned},
        }
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@schema_app.command("export")
def schema_export(
    list_name: str = typer.Option("WorkBoard", "--list", help="List name"),
    output: str = typer.Option("discovery/workboard_schema.json", "--output", help="Output file path"),
):
    """Export column schema for a SharePoint list to a JSON file."""
    try:
        cfg, client = _get_client()
        site = get_site(client, cfg["site_url"])
        site_id = site.get("id")
        lists_data = get_lists(client, site_id)
        target = find_list(lists_data, list_name)
        if not target:
            raise WorkboardError(
                "resource_not_found",
                f"List '{list_name}' not found on site.",
                "Use 'workboard lists discover' to see available lists.",
            )
        out_path = _export_schema(client, site_id, target["id"], output)
        print(f"Schema written to {out_path}")
    except WorkboardError as e:
        _error_exit(e)


@items_app.command("list")
def items_list(
    list_name: str = typer.Option("WorkBoard", "--list", help="List name"),
    limit: int = typer.Option(10, "--limit", help="Maximum items to retrieve"),
    normalize: bool = typer.Option(False, "--normalize", help="Normalize items using config field mapping"),
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """List items from a SharePoint list."""
    try:
        cfg, client = _get_client()
        raw_items, _, target = _fetch_items(cfg, client, list_name, limit=limit)
        items = [normalize_item(i, cfg) for i in raw_items] if normalize else raw_items
        envelope = {
            "status": "ok",
            "source": _build_source(cfg["site_url"], list_name, target["id"]),
            "retrievedAt": _now_iso(),
            "result": {"count": len(items), "items": items},
        }
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@items_app.command("get")
def items_get(
    item_id: str = typer.Argument(..., help="Item ID"),
    list_name: str = typer.Option("WorkBoard", "--list", help="List name"),
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Get a single list item by ID."""
    try:
        cfg, client = _get_client()
        site = get_site(client, cfg["site_url"])
        site_id = site.get("id")
        lists_data = get_lists(client, site_id)
        target = find_list(lists_data, list_name)
        if not target:
            raise WorkboardError(
                "resource_not_found",
                f"List '{list_name}' not found on site.",
                "Use 'workboard lists discover' to see available lists.",
            )
        item = get_list_item(client, site_id, target["id"], item_id)
        envelope = {
            "status": "ok",
            "source": _build_source(cfg["site_url"], list_name, target["id"]),
            "retrievedAt": _now_iso(),
            "result": {"item": item},
        }
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@config_app.command("validate")
def config_validate(
    config_path: str = typer.Option("config/workboard.defaults.yaml", "--config", help="Config file path"),
    schema_path: str = typer.Option("discovery/workboard_schema.json", "--schema", help="Exported schema JSON path"),
):
    """Validate that config field mappings exist in the exported schema."""
    try:
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise WorkboardError(
                "config_error",
                f"Schema file not found: {schema_path}",
                "Export the schema first with 'workboard schema export'.",
            )
        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)
        schema_names = {c["name"] for c in schema.get("columns", [])}

        config_file = Path(config_path)
        if not config_file.exists():
            raise WorkboardError(
                "config_error",
                f"Config file not found: {config_path}",
            )
        with open(config_file, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        field_mappings = config.get("fields", {}).values()

        mismatches = []
        for mapped_name in field_mappings:
            if mapped_name not in schema_names:
                mismatches.append(mapped_name)

        if mismatches:
            result = {
                "status": "error",
                "error": {
                    "code": "config_error",
                    "message": f"{len(mismatches)} field(s) in config not found in schema.",
                    "action": f"Review field names: {', '.join(mismatches)}",
                },
            }
            print(json.dumps(result, indent=2))
            raise typer.Exit(4)
        else:
            result = {
                "status": "ok",
                "message": f"All {len(field_mappings)} field mappings validated against schema.",
            }
            print(json.dumps(result, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@query_app.command("open")
def query_open(
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Return open work items."""
    try:
        cfg, client = _get_client()
        raw_items, _, target = _fetch_items(cfg, client, cfg["primary_list_name"])
        items = [normalize_item(i, cfg) for i in raw_items]
        filtered = filter_open(items)
        envelope = build_envelope(filtered, "open_items", cfg, target["id"])
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@query_app.command("overdue")
def query_overdue(
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Return overdue work items."""
    try:
        cfg, client = _get_client()
        raw_items, _, target = _fetch_items(cfg, client, cfg["primary_list_name"])
        items = [normalize_item(i, cfg) for i in raw_items]
        filtered = filter_overdue(items)
        envelope = build_envelope(filtered, "overdue_items", cfg, target["id"])
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@query_app.command("by-owner")
def query_by_owner(
    owner: str = typer.Option(..., "--owner", help="Owner name"),
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Return items owned by a person."""
    try:
        cfg, client = _get_client()
        raw_items, _, target = _fetch_items(cfg, client, cfg["primary_list_name"])
        items = [normalize_item(i, cfg) for i in raw_items]
        filtered = filter_by_owner(items, owner)
        envelope = build_envelope(filtered, "items_by_owner", cfg, target["id"], {"owner": owner})
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@query_app.command("blocked")
def query_blocked(
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Return blocked work items."""
    try:
        cfg, client = _get_client()
        raw_items, _, target = _fetch_items(cfg, client, cfg["primary_list_name"])
        items = [normalize_item(i, cfg) for i in raw_items]
        filtered = filter_blocked(items)
        envelope = build_envelope(filtered, "blocked_items", cfg, target["id"])
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@query_app.command("recently-updated")
def query_recently_updated(
    days: int = typer.Option(7, "--days", help="Number of days"),
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Return items updated within the last N days."""
    try:
        cfg, client = _get_client()
        raw_items, _, target = _fetch_items(cfg, client, cfg["primary_list_name"])
        items = [normalize_item(i, cfg) for i in raw_items]
        filtered = filter_recently_updated(items, days)
        envelope = build_envelope(filtered, "recently_updated_items", cfg, target["id"], {"days": days})
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@summary_app.command("manager")
def summary_manager(
    format: str = typer.Option("markdown", "--format", help="Output format"),
):
    """Return a manager summary with counts and groupings."""
    try:
        cfg, client = _get_client()
        raw_items, cfg, target = _fetch_items(cfg, client, cfg["primary_list_name"])
        items = [normalize_item(i, cfg) for i in raw_items]
        summary = build_summary(items)
        if format == "markdown":
            print(render_markdown_summary(summary, cfg["site_url"], _now_iso()))
        else:
            envelope = build_summary_envelope(summary, cfg, target.get("id"))
            print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)


@self_app.command("path")
def self_path():
    """Show where the CLI is installed."""
    print(Path(sys.argv[0]).resolve())


@self_app.command("install")
def self_install():
    """Add the CLI directory to the user PATH."""
    scripts_dir = Path(sys.argv[0]).resolve().parent
    path_entry = str(scripts_dir)
    env_path = os.environ.get("PATH", "")
    if path_entry in env_path.split(os.pathsep):
        print(f"Already on PATH: {path_entry}")
        return
    import subprocess
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';{path_entry}', 'User')"],
        capture_output=True, text=True, check=True
    )
    os.environ["PATH"] = env_path + os.pathsep + path_entry
    print(f"Added to PATH: {path_entry}")
    print("Restart your terminal for the change to take full effect.")


@agent_app.command("query")
def agent_query(
    intent: str = typer.Option(..., "--intent", help="Agent intent to execute"),
    owner: Optional[str] = typer.Option(None, "--owner", help="Owner filter (for items_by_owner)"),
    days: Optional[int] = typer.Option(None, "--days", help="Days filter (for recently_updated_items)"),
    format: str = typer.Option("json", "--format", help="Output format"),
):
    """Execute an approved agent intent."""
    try:
        validate_intent(intent)
        cfg, client = _get_client()
        raw_items, _, _ = _fetch_items(cfg, client, cfg["primary_list_name"])
        params = {}
        if owner:
            params["owner"] = owner
        if days:
            params["days"] = days
        envelope = execute_intent(intent, raw_items, cfg, params)
        print(json.dumps(envelope, indent=2))
    except WorkboardError as e:
        _error_exit(e)
