from workboard_cli.sharepoint import find_list, parse_site_url


def test_parse_site_url():
    host, path = parse_site_url("https://southernasiapacific.sharepoint.com/sites/ITWorkboard")
    assert host == "southernasiapacific.sharepoint.com"
    assert path == "/sites/ITWorkboard"


def test_find_list_by_display_name():
    lists = [
        {"displayName": "Work Board", "name": "WorkBoard"},
        {"displayName": "Documents", "name": "Documents"},
    ]
    result = find_list(lists, "Work Board")
    assert result is not None
    assert result["name"] == "WorkBoard"


def test_find_list_by_internal_name():
    lists = [
        {"displayName": "Work Board", "name": "WorkBoard"},
    ]
    result = find_list(lists, "WorkBoard")
    assert result is not None
    assert result["displayName"] == "Work Board"


def test_find_list_not_found():
    result = find_list([], "Nonexistent")
    assert result is None
