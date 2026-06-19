---
title: feat: Add session_id correlation across observation streams
date: 2026-06-19
topic: correlation-id-observation-streams
type: feat
---

# feat: Add session_id correlation across observation streams

## Summary

Generate a session-scoped UUID (`session_id`) once per CLI process and stamp it on every CLI observation event, agent observation entry, session counters file, and stdout JSON envelope. The CLI reads `WORKBOARD_SESSION_ID` from the environment when set (caller-owned), otherwise auto-generates via `uuid.uuid4()`. This creates a deterministic join key between the two JSONL streams (`workboard-observations.jsonl` and `workboard-agent-observations.jsonl`) and the CLI output, enabling cross-stream correlation for analysis and the observations self-improvement roadmap.

## Problem Frame

The workboard CLI captures two independent observation streams that cannot be correlated today. CLI events (invocation, error, crash, interaction_gap) land in `workboard-observations.jsonl` keyed only by `ts` + `ms`. Agent observations (intent_mismatch, error, warning, etc.) land in a separate file `workboard-agent-observations.jsonl` keyed only by `ts`. Neither file carries a session-level identifier, so joining "what the CLI did" with "what happened in the conversation" requires brittle guesswork. The observations roadmap depends on session-unique counting for gap deduplication and cross-session behavioral analysis — neither is possible without a join key.

## Requirements

- R1. A `session_id` (UUID v4 string) is generated once per CLI process.
- R2. The CLI respects the `WORKBOARD_SESSION_ID` environment variable when set, falling back to auto-generation.
- R3. Every CLI observation event written by `capture()` includes `session_id`.
- R4. The session counters file (`workboard-counters.json`) includes `session_id` in the session summary object.
- R5. Every stdout JSON envelope from `output.py` (`build_envelope`, `build_summary_envelope`, `build_error_envelope`) includes `session_id`.
- R6. The agent observation instructions are updated to include `session_id` in every agent observation entry.
- R7. No existing observation data is backfilled — the change applies to new observations only.
- R8. All changes are tested with the existing test patterns (pytest, CliRunner, responses library).

## Key Technical Decisions

- **KTD1. Single-generation point in observations.py.** The `session_id` is generated at module import time in `observations.py`, matching the existing singleton-like pattern (`_events`, `_counters`, `_start`). Captures are stamped inline in `capture()`, the session counters in `_flush()`. No per-call-site changes needed.
- **KTD2. Public getter for cross-module access.** `observations.get_session_id()` exposes the value so `output.py` can include it in envelopes without passing it as a parameter everywhere.
- **KTD3. Environment variable override.** `WORKBOARD_SESSION_ID` is checked before auto-generation, matching the existing `WORKBOARD_OBS_DISABLE` and `WORKBOARD_OBS_DIR` pattern. This lets an outer loop (openCode, CI, orchestration framework) own the session ID across multiple CLI invocations.
- **KTD4. Agent reads session_id from CLI stdout.** The agent does not need to pre-set the env var. After the first CLI invocation, it extracts `session_id` from a stdout envelope and includes it in all subsequent agent observations. This is the simplest path — agent observations always fire after CLI interaction per the trigger list.

## Implementation Units

### U1. Add session_id generation and stamping to observations.py

**Goal:** Generate a session-scoped UUID per process and stamp it on every CLI observation event.

**Requirements:** R1, R2, R3, R4

**Dependencies:** None

**Files:**
- `src/workboard_cli/observations.py` (modify)
- `tests/test_observations.py` (create)

**Approach:**
- Add `import uuid` and `import os` at the top of the module.
- Add module-level `_session_id: str` initialized as:
  ```
  _session_id = os.environ.get("WORKBOARD_SESSION_ID") or str(uuid.uuid4())
  ```
  placed after `_start` to match the existing pattern.
- Add public accessor `def get_session_id() -> str: return _session_id`.
- In `capture()`, add `data["session_id"] = _session_id` alongside the existing `event`, `ts`, `ms` stamps.
- In `_flush()`, add `"session_id": _session_id` to the session counters dict.

**Patterns to follow:**
- Module-level mutable state pattern already used for `_events`, `_counters`, `_start` (observations.py:12-15)
- Environment variable fallback pattern: `WORKBOARD_OBS_DIR` (observations.py:28-30), `WORKBOARD_OBS_DISABLE` (observations.py:16)

**Test scenarios:**
- Session_id is present on every captured event — call `capture("test")`, inspect the JSON event string for `"session_id":`
- All events from a single process share the same `session_id` — capture two events, parse both, assert IDs match
- `WORKBOARD_SESSION_ID` env var override — set env var, reimport module (or monkeypatch), verify captured session_id matches the override
- `get_session_id()` returns the same value as stamped on events
- Session counters file includes `session_id` with matching value
- Observations disabled (`WORKBOARD_OBS_DISABLE=1`) — capture is no-op, no errors from session_id code path

**Verification:** `pytest tests/test_observations.py` passes. Manual: run `workboard query open`, check stdout envelope contains `session_id`, check JSONL files at observation dir.

### U2. Add session_id to stdout JSON envelopes

**Goal:** Every output envelope carries `session_id` so the agent can read it from any CLI response.

**Requirements:** R5

**Dependencies:** U1 (needs `observations.get_session_id()`)

**Files:**
- `src/workboard_cli/output.py` (modify)
- `tests/test_output.py` (modify)

**Approach:**
- Import `get_session_id` from `workboard_cli.observations` in `output.py`.
- In `build_envelope()`, add `"sessionId": get_session_id()` to the returned dict.
- In `build_summary_envelope()`, add the same.
- In `build_error_envelope()`, add the same.
- Key name is `"sessionId"` (camelCase) to match the existing JSON envelope convention (`retrievedAt`, `listId`, etc.).

**Patterns to follow:**
- Import from `workboard_cli.observations` is already established in `cli.py` (line 19)
- Output envelope dict shape in `output.py` — `status`, `intent`, `source`, `retrievedAt`, etc.

**Test scenarios:**
- `build_envelope()` output includes `"sessionId"` key with a non-empty string value
- `build_summary_envelope()` output includes `"sessionId"`
- `build_error_envelope()` output includes `"sessionId"`
- All three envelope types share the same `sessionId` value within a process (module-level singleton)
- `sessionId` value is a valid UUID format (36-char string with hyphens)

**Verification:** `pytest tests/test_output.py` passes.

### U3. Update agent observation capture instructions

**Goal:** The agent includes `session_id` in every agent observation entry, enabling cross-stream correlation.

**Requirements:** R6

**Dependencies:** U1 (session_id concept exists), U2 (agent reads session_id from CLI stdout)

**Files:**
- `.opencode/agents/workboard.md` (modify)

**Approach:**
- Update the agent observation schema example (line 183-192) to include `"session_id"` field.
- Add a note explaining how the agent obtains the session_id: extract it from the `sessionId` field in any CLI stdout envelope after the first invocation; store it for the conversation duration; include it in every subsequent `agent_observation` entry.
- The agent does NOT need to pre-set `WORKBOARD_SESSION_ID` — reading from stdout covers the common case.

**Test scenarios:** None — agent instruction changes are verified by human review.

**Verification:** Review the updated `.opencode/agents/workboard.md` for correctness.

### U4. Integration tests

**Goal:** Verify end-to-end that session_id flows correctly through the observation lifecycle.

**Requirements:** R1, R2, R3, R4, R5, R8

**Dependencies:** U1, U2

**Files:**
- `tests/test_observations.py` (created in U1, extend here)
- `tests/test_cli.py` (modify)

**Approach:**
- Add an integration test in `tests/test_cli.py` that uses `CliRunner` to invoke a command, then asserts the stdout envelope contains `sessionId`.
- Add a test that verifies observations written to a temp dir contain `session_id` in both JSONL events and the counters file.
- Use `monkeypatch.setenv("WORKBOARD_OBS_DIR", tmp_path)` to redirect observation output for test isolation.

**Patterns to follow:**
- `typer.testing.CliRunner` for CLI invocation tests (tests/test_cli.py)
- `monkeypatch` for env var control (used throughout test suite)
- Temp directory for observation files — avoid polluting the real observation dir

**Test scenarios:**
- CLI invocation via CliRunner produces stdout envelope with valid `sessionId`
- JSONL observation file at temp dir has `session_id` on every line
- Session counters JSON at temp dir has matching `session_id`
- Same `session_id` across stdout envelope, JSONL entries, and counters file within one process

## Scope Boundaries

- **In scope:** Three observation streams — CLI events (JSONL), agent observations (JSONL), session counters (JSON). Plus stdout envelopes for consumption.
- **In scope:** Environment variable override (`WORKBOARD_SESSION_ID`) for external orchestration.
- **Not in scope:** Backfilling `session_id` on existing observation data — the change applies to new observations only.
- **Not in scope:** A cross-stream analysis or join tool — `session_id` enables it but does not build it.
- **Not in scope:** Changes to `scripts/analyze-observations.py` — the analysis script can use `session_id` in a follow-up.
- **Not in scope:** Changes to Graph API or SharePoint interaction layer — purely a telemetry concern.

## Open Questions

- **Role of `WORKBOARD_SESSION_ID` env var in practice.** The mechanism is in place for any caller (openCode session, CI pipeline, orchestration framework) to set it. For the current agent workflow, auto-generation + stdout read is sufficient. The decision to use the env var actively is deferred to whoever implements the outer-loop session management.

## Sources / Research

- `docs/roadmaps/observations-self-improvement.md` — the observation roadmap this feature directly enables
- `docs/solutions/logic-errors/check-auth-false-negative.md` — precedent for process-boundary bugs and the "don't be shallower" principle
- `docs/solutions/design-patterns/session-id-correlation.md` — documented design pattern for the session_id approach
- `docs/session-digests/20260619_observations-roadmap.md` — D1: observations are in-process; D3: Phase 1 quick wins first
- `src/workboard_cli/observations.py` — current capture module, the single funnel point for injection
- `.opencode/agents/workboard.md` (lines 163-218) — current agent observation format and triggers
