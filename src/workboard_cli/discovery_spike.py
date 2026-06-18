import json
from pathlib import Path

from workboard_cli.auth import get_token
from workboard_cli.config import load_config
from workboard_cli.graph_client import GraphClient

DISCOVERY_DIR = Path("discovery")

SECRET_KEYS = {"access_token", "refresh_token", "client_secret", "secret"}


def _redact(obj):
    if isinstance(obj, dict):
        return {
            k: ("[REDACTED]" if k.lower() in SECRET_KEYS else _redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    return obj


def _write_json(filename, data):
    path = DISCOVERY_DIR / filename
    path.write_text(json.dumps(_redact(data), indent=2, default=str))
    print(f"  Wrote {path}")


def _write_text(filename, text):
    path = DISCOVERY_DIR / filename
    path.write_text(text)
    print(f"  Wrote {path}")


def main():
    cfg = load_config()
    site_url = cfg["site_url"]
    # e.g. https://southernasiapacific.sharepoint.com/sites/ITWorkboard
    parts = site_url.replace("https://", "").split("/", 1)
    site_host = parts[0]
    site_path = "/" + parts[1] if len(parts) > 1 else ""

    print("Authenticating via device code flow...")
    token = get_token()
    client = GraphClient(token)

    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[1/5] Resolving site...")
    site = client.get(f"/sites/{site_host}:{site_path}")
    site_id = site.get("id")
    _write_json("site.json", site)

    if not site_id:
        print("  ERROR: Could not resolve site ID")
        return

    print("\n[2/5] Enumerating all lists...")
    lists = client.get_all(f"/sites/{site_id}/lists")
    _write_json("lists.json", lists)

    list_name = cfg["primary_list_name"]
    workboard = next(
        (
            lst
            for lst in lists
            if lst.get("displayName") == list_name
            or lst.get("name") == list_name
        ),
        None,
    )
    if not workboard:
        print(f"  WARNING: {list_name} list not found by display name or internal name")
        print(f"  Available lists: {[lst.get('displayName') for lst in lists]}")
        return

    workboard_id = workboard.get("id")
    print(f"  Found {list_name} list: id={workboard_id}")

    print("\n[3/5] Exporting WorkBoard column schema...")
    columns = client.get_all(f"/sites/{site_id}/lists/{workboard_id}/columns")
    _write_json("workboard_schema.json", columns)

    print("\n[4/5] Retrieving sample items (top 10)...")
    items = client.get_all(
        f"/sites/{site_id}/lists/{workboard_id}/items",
        params={"expand": "fields", "$top": 10},
    )
    _write_json("workboard_sample_items.json", items)

    print("\n[5/5] Generating permission report...")
    lines = [
        "# Permission Report",
        "",
        "## Site",
        f"- URL: {site_url}",
        f"- ID: {site_id}",
        "- Resolved: OK",
        "",
        "## Lists discovered",
    ]
    for lst in lists:
        display = lst.get("displayName") or "(unnamed)"
        lines.append(f"- {display} (id={lst.get('id')})")

    lines.append("")
    lines.append(f"## {list_name} list: {'FOUND' if workboard else 'NOT FOUND'}")
    if workboard:
        lines.append(f"- ID: {workboard_id}")
        lines.append(f"- Columns discovered: {len(columns)}")
        lines.append(f"- Sample items: {len(items)}")

    _write_text("permission_report.md", "\n".join(lines))

    print("\nDiscovery complete. Output in discovery/")


if __name__ == "__main__":
    main()
