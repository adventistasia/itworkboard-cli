import time

import requests

from workboard_cli.errors import WorkboardError


class GraphClient:
    BASE = "https://graph.microsoft.com/v1.0"
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })

    def _handle_response(self, resp, path):
        if resp.status_code == 401:
            raise WorkboardError(
                "auth_error",
                "Token expired or invalid. Run 'workboard auth login' to re-authenticate.",
                "Re-authenticate with 'workboard auth login'.",
            )
        if resp.status_code == 403:
            raise WorkboardError(
                "permission_denied",
                f"Access denied to {path}. Your account may not have sufficient permissions.",
                "Ask an administrator to grant read access to the target SharePoint site.",
            )
        if resp.status_code == 404:
            raise WorkboardError(
                "resource_not_found",
                f"Resource not found: {path}",
                "Verify the site URL and list name in your config.",
            )
        if resp.status_code == 429:
            raise WorkboardError(
                "graph_api_error",
                "Rate limited by Microsoft Graph. Try again later.",
                "Wait and retry.",
            )
        if resp.status_code >= 400:
            raise WorkboardError(
                "graph_api_error",
                f"Graph error {resp.status_code}: {resp.text[:500]}",
            )

    def get(self, path, params=None):
        url = f"{self.BASE}{path}"
        for attempt in range(self.MAX_RETRIES):
            resp = self.session.get(url, params=params)
            if resp.status_code == 429 and attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY * (attempt + 1))
                continue
            self._handle_response(resp, path)
            return resp.json()

    def get_all(self, path, params=None):
        items = []
        url = f"{self.BASE}{path}"
        while url:
            resp = self.session.get(url, params=params)
            params = None
            self._handle_response(resp, path)
            data = resp.json()
            items.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
        return items
