---
title: Session ID correlation across observation streams
date: 2026-06-19
category: design-patterns
module: observations
problem_type: design_pattern
component: tooling
severity: medium
applies_when:
  - "Any system writing two or more independent observation or event streams that must be correlated post-hoc"
  - "CLI tools with split architecture (CLI-side events + agent-side observations)"
  - "Adding correlation IDs to a module that emits structured log/event output and communicates results via stdout"
tags:
  - session-id
  - correlation
  - observations
  - telemetry
  - python
---

# Session ID correlation across observation streams

## Context

The workboard CLI writes two independent observation streams: CLI-side events (invocation, error, crash, interaction_gap) go to `workboard-observations.jsonl` keyed only by `ts` + `ms`, while agent-side observations (intent_mismatch, error, warning) go to `workboard-agent-observations.jsonl` keyed only by `ts`. Without a session-level identifier, correlating CLI events with agent observations required brittle timestamp guesswork that broke under concurrency, retries, or rapid re-runs.

## Guidance

Generate a single `session_id` at module-import time via a module-level singleton, expose it through a public getter, and stamp it on every observation event and every stdout envelope. Respect an environment variable override so an outer loop (CI, orchestration, agent) can own the session ID across multiple CLI invocations.

### 1. Singleton at import

Place the generation after other module-level state, matching the existing singleton pattern:

```python
_session_id: str = os.environ.get("WORKBOARD_SESSION_ID") or str(uuid.uuid4())
```

### 2. Public getter for cross-module access

Expose the value so other modules can include it without parameter threading:

```python
def get_session_id() -> str:
    return _session_id
```

### 3. Single injection point

Stamp `session_id` in the observation capture function — ensures every event carries it with zero per-call-site changes:

```python
def capture(event: str, **data: Any) -> None:
    data["session_id"] = _session_id
    data["event"] = event
    data["ts"] = _iso()
    data["ms"] = ...
```

### 4. Stdout envelopes

Add to every envelope builder using camelCase to match existing JSON envelope conventions:

```python
"sessionId": get_session_id()
```

### 5. Agent reads from stdout

The agent does not pre-set `WORKBOARD_SESSION_ID`. After the first CLI invocation, it extracts `sessionId` from the stdout envelope and includes it in all subsequent agent observations. This eliminates the chicken-and-egg problem and keeps the env var as optional infrastructure for advanced orchestration.

## Why This Matters

Before this change, session-correlation between CLI events and agent observations was impossible without fragile timestamp matching. A single CLI invocation that spawns an agent now produces exactly one `session_id` — logged in both observation files and echoed in every stdout envelope — enabling deterministic join across streams. The `WORKBOARD_SESSION_ID` env-var override makes it reproducible in tests and CI.

This pattern is the third use of the env-var-with-fallback pattern in the codebase (following `WORKBOARD_OBS_DISABLE` and `WORKBOARD_OBS_DIR`), making it a local convention for any future configuration.

## When to Apply

- Any system writing two or more independent observation or event streams that must be correlated post-hoc
- CLI tools that have a split architecture (CLI-side events + agent-side observations)
- Designs where the caller cannot propagate a correlation ID across process boundaries and the callee must be self-contained
- Adding correlation IDs to a module that emits structured log/event output and communicates results via stdout

## Examples

**Before:** Two JSONL files with no shared identifier. `workboard-observations.jsonl` entries had `{"ts": "...", "ms": 1234, "event": "interaction_gap"}`. Agent observations had `{"ts": "...", "event": "intent_mismatch"}`. Correlating them required matching timestamps within an arbitrary tolerance window, which failed under fast re-runs.

**After:** Every entry in both streams carries `"session_id": "a1b2c3d4-..."`. A CLI error and an agent warning from the same run have the same value. The stdout envelope also includes `"sessionId": "a1b2c3d4-..."`, so the agent never needs to manage env vars — it just extracts it from the first CLI response. The env-var override `WORKBOARD_SESSION_ID=test-run-1` makes all outputs from a CI run share the same ID.

## Related

- Feature plan: [docs/plans/2026-06-19-001-feat-correlation-id-observation-streams-plan.md](../../plans/2026-06-19-001-feat-correlation-id-observation-streams-plan.md)
- Observations roadmap: [docs/roadmaps/observations-self-improvement.md](../../roadmaps/observations-self-improvement.md)
- Residual review findings: [docs/residual-review-findings/feat-correlation-id-plan.md](../../residual-review-findings/feat-correlation-id-plan.md)
- GitHub issues: [#1](https://github.com/adventistasia/itworkboard-cli/issues/1) – [#4](https://github.com/adventistasia/itworkboard-cli/issues/4)
