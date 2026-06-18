import atexit
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from workboard_cli import __version__

_events: list[str] = []
_counters: dict[str, int] = {}
_start = time.monotonic()
_disabled = os.environ.get("WORKBOARD_OBS_DISABLE") == "1"
_OBS_DIR: Path | None = None


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_dir() -> Path | None:
    global _OBS_DIR
    if _OBS_DIR is not None:
        return _OBS_DIR
    override = os.environ.get("WORKBOARD_OBS_DIR")
    if override:
        d = Path(override)
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        d = Path(xdg) / "workboard" / "observations" if xdg else \
            Path.home() / ".local" / "share" / "workboard" / "observations"
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        d = Path(tempfile.gettempdir()) / "workboard-observations"
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            return None
    _OBS_DIR = d
    return d


def capture(event: str, **data: Any) -> None:
    if _disabled:
        return
    _counters[event] = _counters.get(event, 0) + 1
    data["event"] = event
    data["ts"] = _iso()
    data["ms"] = int((time.monotonic() - _start) * 1000)
    _events.append(json.dumps(data, default=str))


def make_on_gap(threshold_ms: int = 3000) -> Callable:
    """Factory: returns a gap callback suitable for GraphClient."""
    def on_gap(endpoint: str, ms: int, status_code: int | None = None,
               error: str | None = None):
        if ms > threshold_ms:
            capture("interaction_gap", endpoint=endpoint, ms=ms,
                    status_code=status_code, error=error)
    return on_gap


def _flush() -> None:
    if _disabled or not _events:
        return
    d = _get_dir()
    if d is None:
        return
    try:
        with open(d / "workboard-observations.jsonl", "a", encoding="utf-8") as f:
            for line in _events:
                f.write(line + "\n")
        with open(d / "workboard-counters.json", "w", encoding="utf-8") as f:
            json.dump({
                "event": "session",
                "ts": _iso(),
                "duration_ms": int((time.monotonic() - _start) * 1000),
                "counts": dict(_counters),
                "version": __version__,
                "command": " ".join(sys.argv[1:]),
                "exit_code": 0,
            }, f, indent=2)
    except Exception:
        pass


atexit.register(_flush)
