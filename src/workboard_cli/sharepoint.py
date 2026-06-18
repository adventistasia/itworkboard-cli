from urllib.parse import urlparse


def parse_site_url(site_url):
    parsed = urlparse(site_url)
    host = parsed.netloc
    path = parsed.path.rstrip("/")
    return host, path


def get_site(client, site_url):
    host, path = parse_site_url(site_url)
    return client.get(f"/sites/{host}:{path}")


def get_lists(client, site_id):
    return client.get_all(f"/sites/{site_id}/lists")


def find_list(lists, name):
    for lst in lists:
        if lst.get("displayName") == name or lst.get("name") == name:
            return lst
    return None


def get_list_columns(client, site_id, list_id):
    return client.get_all(f"/sites/{site_id}/lists/{list_id}/columns")


def get_list_items(client, site_id, list_id, limit=None, expand="fields"):
    params = {"expand": expand}
    if limit:
        params["$top"] = limit
    return client.get_all(f"/sites/{site_id}/lists/{list_id}/items", params=params)


def get_list_item(client, site_id, list_id, item_id, expand="fields"):
    params = {"expand": expand}
    return client.get(f"/sites/{site_id}/lists/{list_id}/items/{item_id}", params=params)
