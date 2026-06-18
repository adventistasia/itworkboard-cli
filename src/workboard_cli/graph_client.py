import requests


class GraphClient:
    BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })

    def get(self, path, params=None):
        url = f"{self.BASE}{path}"
        resp = self.session.get(url, params=params)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Graph error {resp.status_code}: {resp.text}"
            )
        return resp.json()

    def get_all(self, path, params=None):
        items = []
        url = f"{self.BASE}{path}"
        while url:
            resp = self.session.get(url, params=params)
            params = None
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Graph error {resp.status_code}: {resp.text}"
                )
            data = resp.json()
            items.extend(data.get("value", []))
            url = data.get("@odata.nextLink")
        return items
