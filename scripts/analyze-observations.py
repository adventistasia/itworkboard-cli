"""Analyze observation logs and produce a ranked gap report.

Usage:
    python scripts/analyze-observations.py [--days 7]

Outputs a markdown report to stdout grouped by event type,
sorted by frequency descending. The top entries are candidates
for the next improvement cycle.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


def find_log_dirs() -> list[Path]:
    candidates = []
    xdg = __import__("os").environ.get("XDG_DATA_HOME")
    if xdg:
        candidates.append(Path(xdg) / "workboard" / "observations")
    candidates.append(Path.home() / ".local" / "share" / "workboard" / "observations")
    candidates.append(Path.home() / "AppData" / "Local" / "workboard" / "observations")
    existing = [d for d in candidates if d.exists()]
    if not existing:
        print("No observation logs found.", file=sys.stderr)
        print(f"Looked in: {', '.join(str(d) for d in candidates)}", file=sys.stderr)
        sys.exit(1)
    return existing


def load_events(dirs: list[Path], since: datetime | None = None) -> list[dict]:
    events = []
    for d in dirs:
        for f in sorted(d.glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").strip().splitlines():
                try:
                    ev = json.loads(line)
                    if since:
                        ev_ts = datetime.fromisoformat(ev.get("ts", "")).replace(tzinfo=timezone.utc)
                        if ev_ts < since:
                            continue
                    events.append(ev)
                except (json.JSONDecodeError, ValueError):
                    continue
    return events


def report(events: list[dict]):
    total = len(events)
    if total == 0:
        print("No events found in the time window.")
        return

    by_event = Counter(ev.get("event", "unknown") for ev in events)
    sessions = [ev for ev in events if ev.get("event") == "session"]
    error_events = [ev for ev in events if ev.get("event") == "error"]
    gap_events = [ev for ev in events if ev.get("event") == "interaction_gap"]
    crash_events = [ev for ev in events if ev.get("event") == "crash"]
    invocations = [ev for ev in events if ev.get("event") == "invocation"]

    print("# Observation Report\n")
    print(f"**Period:** {events[0].get('ts', '?')[:10]} — {events[-1].get('ts', '?')[:10]}")
    print(f"**Total events:** {total}")
    print(f"**Sessions:** {len(sessions)}")
    print(f"**Invocations:** {len(invocations)}")
    print(f"**Errors:** {len(error_events)}")
    print(f"**Interaction gaps (>3s):** {len(gap_events)}")
    print(f"**Crashes:** {len(crash_events)}")
    print()

    if error_events:
        print("## Errors by Code\n")
        codes = Counter(ev.get("code", "unknown") for ev in error_events)
        commands = Counter(ev.get("command", "unknown") for ev in error_events)
        print("| Rank | Error Code | Count |")
        print("|------|-----------|-------|")
        for i, (code, count) in enumerate(codes.most_common(), 1):
            print(f"| {i} | `{code}` | {count} |")
        print()
        print("| Rank | Command | Count |")
        print("|------|---------|-------|")
        for i, (cmd, count) in enumerate(commands.most_common(5), 1):
            print(f"| {i} | `{cmd}` | {count} |")
        print()

    if gap_events:
        print("## Interaction Gaps (slow endpoints)\n")
        slow = sorted(gap_events, key=lambda e: e.get("ms", 0), reverse=True)
        print("| Endpoint | Max ms | Count |")
        print("|----------|--------|-------|")
        by_endpoint = Counter(ev.get("endpoint", "unknown") for ev in gap_events)
        for endpoint, count in by_endpoint.most_common(5):
            max_ms = max((e.get("ms", 0) for e in gap_events if e.get("endpoint") == endpoint), default=0)
            print(f"| `{endpoint}` | {max_ms} | {count} |")
        print()

    if crash_events:
        print("## Crashes\n")
        crash_types = Counter(ev.get("type", "unknown") for ev in crash_events)
        for t, count in crash_types.most_common():
            print(f"- `{t}`: {count}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Analyze workboard observation logs")
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7)")
    args = parser.parse_args()

    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    dirs = find_log_dirs()
    events = load_events(dirs, since=since)
    report(events)


if __name__ == "__main__":
    main()
