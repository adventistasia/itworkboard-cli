import json

from workboard_cli.errors import WorkboardError


def test_error_to_dict():
    err = WorkboardError("auth_error", "Something went wrong.", "Try again.")
    d = err.to_dict()
    assert d["code"] == "auth_error"
    assert d["message"] == "Something went wrong."
    assert d["action"] == "Try again."


def test_error_to_dict_no_action():
    err = WorkboardError("auth_error", "Something went wrong.")
    d = err.to_dict()
    assert d["code"] == "auth_error"
    assert "action" not in d


def test_error_round_trip_json():
    err = WorkboardError("permission_denied", "Access denied.", "Ask admin.")
    d = err.to_dict()
    s = json.dumps(d)
    loaded = json.loads(s)
    assert loaded["code"] == "permission_denied"
