---
lorespec: "0.1"
id: "2026061902"
date: "2026-06-19"
source: "opencode"
topic: "Planned session_id correlation across workboard observation streams"
tags: [observations, telemetry, correlation, planning, ce-plan, session_id]
classification:
  type: technical
  domains: [cli-tooling, telemetry, python]
  value: high
trails: [observations-self-improvement]
---

## Session Arc

### Started
User requested brainstorm for "Correlation ID Across Observation Streams" in the workboard CLI. The existing observation system captures CLI events (JSONL) and agent observations (separate JSONL) with no shared join key.

### Pivots
- **Scope narrowing (stream choice):** User clarified session-scoped UUID per CLI process for both CLI events and agent observations — not multi-invocation, not Graph API correlation. Led to env-var vs auto-generate design.
- **Stdout envelope call-out resolved:** User challenged the "don't pollute the contract" argument and concluded session_id belongs in stdout envelopes too. The contract pollution concern was judged weak.
- **Chicken-and-egg resolved:** User suggested the CLI emits session_id on stdout before observations fire — agent reads it from the first CLI response. This eliminates the need for the agent to pre-set WORKBOARD_SESSION_ID.
- **Transition to plan:** User invoked ce-plan to produce an implementation plan from the brainstorm.

### Ended
A structured implementation plan was written to `docs/plans/2026-06-19-001-feat-correlation-id-observation-streams-plan.md` with 4 implementation units, test scenarios, and key technical decisions.

## Objects

### A1. ARTIFACT — Implementation plan for session_id correlation

**Path:** `docs/plans/2026-06-19-001-feat-correlation-id-observation-streams-plan.md`

**Summary:** A 4-unit implementation plan covering:
- U1: session_id generation and stamping in `observations.py` (env var override + uuid4 fallback)
- U2: session_id in stdout JSON envelopes via `output.py`
- U3: Agent observation instruction update in `.opencode/agents/workboard.md`
- U4: Integration tests for the full flow

### D1. DECISION — session_id scope: CLI events + agent observations + counters + stdout envelopes

- **Issue:** Which observation streams should carry session_id?
- **Positions:** CLI events only; CLI + agent + counters; all streams including stdout envelopes
- **Arguments:** stdout coupling vs convenience trade-off; the coupling concern was weaker than the convenience gain
- **Warrant:** If stdout envelopes are internal contracts (not public API), adding a field for correlation is net-positive — agent gets session_id from every response without reading JSONL files
- **Qualifier:** settled
- **Status:** settled

### D2. DECISION — Env-var driven with auto-generate fallback

- **Issue:** How should session_id be owned and communicated?
- **Positions:** CLI arg (clutters every command); CLI-owned + stdout emission (chicken-and-egg for agent); env-var driven (flexible)
- **Arguments:** Env var separates concerns — outer loop (agent/CI/orchestrator) sets WORKBOARD_SESSION_ID when it cares, CLI auto-generates otherwise. Stdout emission resolves the chicken-and-egg concern: agent reads session_id from the first CLI response before needing it.
- **Warrant:** If the agent always gets session_id from CLI stdout before recording any observation, the env var is optional infrastructure for advanced orchestration.
- **Qualifier:** always
- **Status:** settled

### D3. DECISION — Auto-generation: UUID at module import time

- **Issue:** When and how to generate the auto-fallback session_id?
- **Positions:** Lazy (first capture); eager (module import); UUID vs timestamp-based
- **Arguments:** Module-level eager generation matches existing pattern (`_start`, `_events`, `_counters` are all module-level). UUID4 is stdlib. Lazy generation would add complexity for no benefit.
- **Warrant:** If observations.py is always imported at CLI startup (which it is, via cli.py import), eager generation at import time is the simplest correct behavior.
- **Qualifier:** always
- **Status:** settled

### I1. INSIGHT — The analysis script reads both JSONL files already

The `scripts/analyze-observations.py` script globs all `*.jsonl` files in the observation directory, parsing both `workboard-observations.jsonl` and `workboard-agent-observations.jsonl`. It currently has no way to correlate events between them — `session_id` directly enables cross-stream analysis without script changes.

**Source:** `scripts/analyze-observations.py` (load_events function)

### I2. INSIGHT — No existing UUID infrastructure in the codebase

`import uuid` does not appear anywhere in `src/`. Adding `uuid.uuid4()` to observations.py introduces a new stdlib dependency (no pip install needed) but no established pattern to follow.

### I3. INSIGHT — observations.py is the single funnel point for CLI events

Every CLI observation flows through `capture(event, **data)` in `observations.py`. Adding `data["session_id"] = _session_id` there stamps every event automatically with zero per-call-site changes. This is the most efficient injection point.

### P1. PATTERN — Env-var with fallback for configuration

The codebase uses environment variable overrides with sensible fallbacks consistently:
- `WORKBOARD_OBS_DISABLE=1` disables observations
- `WORKBOARD_OBS_DIR` overrides the observation directory
- `WORKBOARD_SESSION_ID` (new) overrides the session ID

This is a local pattern to follow for the new feature.

### N1. NEXT_STEP — Implement the 4-unit plan

Begin with U1 (observations.py changes), then U2 (output.py envelopes), U3 (agent instructions), U4 (integration tests). See `docs/plans/2026-06-19-001-feat-correlation-id-observation-streams-plan.md`.

**Urgency:** now

## Connections

- D1 —[led_to]→ D2
- D2 —[led_to]→ D3
- A1 —[informed_by]→ D1
- A1 —[informed_by]→ D2
- A1 —[informed_by]→ D3
- I1 —[related_to]→ A1
- I2 —[informed_by]→ research findings
- I3 —[informed_by]→ research findings
- P1 —[instance_of]→ existing codebase patterns
- N1 —[depends_on]→ A1

## Trail Updates

- **observations-self-improvement** — Added session_id as the foundational cross-stream correlation mechanism. Enables Phase 2 roadmap items (session-unique counting, cross-session behavior analysis).
