import pytest
import responses

from workboard_cli.errors import WorkboardError
from workboard_cli.graph_client import GraphClient


@pytest.fixture
def client():
    return GraphClient("fake-token")


@responses.activate
def test_get_success(client):
    responses.get(
        "https://graph.microsoft.com/v1.0/test",
        json={"value": "ok"},
        status=200,
    )
    result = client.get("/test")
    assert result["value"] == "ok"


@responses.activate
def test_get_401(client):
    responses.get("https://graph.microsoft.com/v1.0/test", status=401)
    with pytest.raises(WorkboardError) as exc:
        client.get("/test")
    assert exc.value.code == "auth_error"


@responses.activate
def test_get_403(client):
    responses.get("https://graph.microsoft.com/v1.0/test", status=403)
    with pytest.raises(WorkboardError) as exc:
        client.get("/test")
    assert exc.value.code == "permission_denied"


@responses.activate
def test_get_404(client):
    responses.get("https://graph.microsoft.com/v1.0/test", status=404)
    with pytest.raises(WorkboardError) as exc:
        client.get("/test")
    assert exc.value.code == "resource_not_found"


@responses.activate
def test_get_429_then_retry(client):
    responses.get(
        "https://graph.microsoft.com/v1.0/test",
        status=429,
    )
    responses.get(
        "https://graph.microsoft.com/v1.0/test",
        json={"value": "retried"},
        status=200,
    )
    result = client.get("/test")
    assert result["value"] == "retried"


@responses.activate
def test_get_all_pagination(client):
    responses.get(
        "https://graph.microsoft.com/v1.0/items",
        json={
            "value": [{"id": 1}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/items?page=2",
        },
        status=200,
    )
    responses.get(
        "https://graph.microsoft.com/v1.0/items?page=2",
        json={"value": [{"id": 2}]},
        status=200,
    )
    items = client.get_all("/items")
    assert len(items) == 2
    assert items[0]["id"] == 1
    assert items[1]["id"] == 2
