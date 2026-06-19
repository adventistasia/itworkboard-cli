import importlib
import json
import uuid

import workboard_cli.observations as obs


def _reset():
    obs._events.clear()
    obs._counters.clear()


def _reload_with_env(key, value):
    import os
    prev = os.environ.get(key)
    os.environ[key] = value
    importlib.reload(obs)
    return prev


def _restore_env(key, prev):
    import os
    if prev is None:
        os.environ.pop(key, None)
    else:
        os.environ[key] = prev
    importlib.reload(obs)


def test_get_session_id_returns_string():
    sid = obs.get_session_id()
    assert isinstance(sid, str)
    assert len(sid) == 36
    assert sid.count("-") == 4


def test_session_id_on_captured_event():
    _reset()
    obs.capture("test_capture")
    assert len(obs._events) == 1
    event = json.loads(obs._events[0])
    assert "session_id" in event
    assert event["session_id"] == obs.get_session_id()


def test_all_events_share_session_id():
    _reset()
    obs.capture("event_a", foo=1)
    obs.capture("event_b", bar=2)
    assert len(obs._events) == 2
    sid = obs.get_session_id()
    for line in obs._events:
        event = json.loads(line)
        assert event["session_id"] == sid


def test_get_session_id_matches_stamped():
    _reset()
    obs.capture("match_test")
    event = json.loads(obs._events[0])
    assert event["session_id"] == obs.get_session_id()


def test_session_id_with_env_override():
    custom_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    prev = _reload_with_env("WORKBOARD_SESSION_ID", custom_uuid)
    try:
        assert obs.get_session_id() == custom_uuid
        obs.capture("override_test")
        event = json.loads(obs._events[0])
        assert event["session_id"] == custom_uuid
    finally:
        _restore_env("WORKBOARD_SESSION_ID", prev)


def test_disabled_no_errors():
    prev = _reload_with_env("WORKBOARD_OBS_DISABLE", "1")
    try:
        obs.capture("should_not_crash")
        assert len(obs._events) == 0
    finally:
        _restore_env("WORKBOARD_OBS_DISABLE", prev)


def test_session_id_is_valid_uuid():
    sid = obs.get_session_id()
    try:
        parsed = uuid.UUID(sid)
        assert str(parsed) == sid
        assert parsed.version == 4
    except ValueError:
        assert False, f"session_id {sid!r} is not a valid UUID"


def test_session_id_with_invalid_env_override():
    prev = _reload_with_env("WORKBOARD_SESSION_ID", "not-a-uuid")
    try:
        assert obs.get_session_id() == "not-a-uuid"
        obs.capture("invalid_id_test")
        event = json.loads(obs._events[0])
        assert event["session_id"] == "not-a-uuid"
    finally:
        _restore_env("WORKBOARD_SESSION_ID", prev)


def test_session_id_with_empty_env_falls_back_to_uuid():
    prev = _reload_with_env("WORKBOARD_SESSION_ID", "")
    try:
        sid = obs.get_session_id()
        parsed = uuid.UUID(sid)
        assert parsed.version == 4
    finally:
        _restore_env("WORKBOARD_SESSION_ID", prev)


def test_session_counters_include_session_id(tmp_path):
    prev_dir = _reload_with_env("WORKBOARD_OBS_DIR", str(tmp_path))
    try:
        _reset()
        obs.capture("counter_test")
        obs._flush()
        counters_file = tmp_path / "workboard-counters.json"
        assert counters_file.exists()
        with open(counters_file) as f:
            counters = json.load(f)
        assert counters["session_id"] == obs.get_session_id()
        jsonl_file = tmp_path / "workboard-observations.jsonl"
        assert jsonl_file.exists()
        with open(jsonl_file) as f:
            line = json.loads(f.readline())
        assert line["session_id"] == obs.get_session_id()
    finally:
        _restore_env("WORKBOARD_OBS_DIR", prev_dir)
