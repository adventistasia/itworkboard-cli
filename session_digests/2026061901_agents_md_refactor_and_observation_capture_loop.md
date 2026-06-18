---
lorespec: "0.1"
id: "2026061901"
date: "2026-06-19"
source: "opencode"
topic: "AGENTS.md refactor, @workboard agent, and observation capture loop for the workboard CLI"
tags: [agents-md, progressive-disclosure, opencode-agent, observation-capture, corrections-loop, aix]
classification:
  type: strategy
  secondary_type: technical
  domains: [agent-instructions, cli-design, observability]
  value: high
trails: [workboard-cli-evolution, observation-capture-strategy]
---

## Session Arc

### Started

The user asked what the AGENTS.md should focus on now that the workboard CLI has been shipped — the file was still describing a non-existent build-plan project.

### Pivots

- **Build-plan to maintenance** — Recognizing the AGENTS.md still described an orchestrator flow for a project that was already delivered, the entire file needed to shift from "how to build" to "how to maintain and evolve."
- **Progressive disclosure** — Rather than just updating inline, the agent-md-refactor skill was loaded, leading to a full split of AGENTS.md into a 38-line root with 5 linked files under `docs/agent-instructions/`.
- **Agent creation** — Shift from refactoring documentation to building a new OpenCode agent (`@workboard`) that acts as a proxy to the CLI tool.
- **Improvement via observation** — The user asked what signals to watch for in user interactions. This triggered a deep exploration of the AIX self-learning correction loop and how to apply it to a CLI tool.
- **Three-dimension capture schema** — Realized the CLI-level capture (commands, errors, timing) is incomplete. The agent layer must capture context (conversation) and outcome (was the need met?) to close the loop.
- **Implementation** — Moved from design to code: 50-line zero-dep observation module, hooks in cli.py, gap callback in graph_client.py, aggregation script, agent capture instructions.

### Ended

A fully built observation capture system across two layers (CLI + agent), with a weekly aggregation script and committed changes. The loop is instrumented but the cadence (weekly review + fix cycle) is still human-driven.

## ARTIFACTS

### A1 — Progressive disclosure AGENTS.md

- **Location:** `AGENTS.md` (root)
- **Linked files:** `docs/agent-instructions/{architecture,field-mapping,agent-intents,testing,maintenance}.md`
- **Summary:** Replaced an 80-line build-plan document with a 38-line root containing only essentials (project description, commands, non-negotiables, links). Five categorized files under `docs/agent-instructions/` hold detailed guidance. The `.claude/` directory was initially used but renamed to `docs/agent-instructions/` when the user noted they don't use Claude.
- **Source:** User request after CLI delivery. Refactored via agent-md-refactor skill.

### A2 — @workboard OpenCode agent

- **Location:** `.opencode/agents/workboard.md`
- **Summary:** A primary-mode agent that acts as a proxy between users and the `workboard` CLI. Knows all 13 commands, the WorkBoard schema (17+ fields, stage mapping, 9 lists), 6 approved agent intents, error codes, and common workflow patterns. Read-only, edit denied, bash allowed. Later updated with observation capture instructions.

### A3 — CLI observation capture module

- **Location:** `src/workboard_cli/observations.py`
- **Summary:** ~50 lines, zero dependencies, on-by-default. Captures invocations, errors, crashes, and slow Graph requests (>3s). Writes JSONL events to `~/.local/share/workboard/observations/` with session summary counters. Silent on failure. Opt-out via `WORKBOARD_OBS_DISABLE=1`. Wired via three hooks in `cli.py` (callback, error_exit, excepthook) and a gap callback in `GraphClient.__init__`.

### A4 — Weekly aggregation script

- **Location:** `scripts/analyze-observations.py`
- **Summary:** Reads JSONL from observation logs for the past N days (default 7). Groups by event type, ranks by frequency, outputs a markdown report with top error codes, slowest endpoints, and crash types. Designed to be run weekly to identify the top 3 gaps for the next improvement cycle.

### A5 — Agent-level capture instructions

- **Location:** `.opencode/agents/workboard.md` (Observation capture section)
- **Summary:** Instructs the agent to log structured observations when triggers fire (intent mismatch, error, warning, rephrase, feature request, post-processing, negative signal). Each entry captures: `criterion` (trigger type), `context` (user question + agent plan + CLI commands), and `outcome` (resolved / resolved_partial / unresolved / abandoned / unknown). Outcome is inferred from the user's next turn.

## DECISIONS

### D1 — AGENTS.md should focus on maintenance, not build

- **Issue:** The shipped CLI still had build-plan AGENTS.md
- **Positions:** (1) Update inline (2) Progressive disclosure split
- **Arguments:** Progressive disclosure won — keeps root minimal (38 lines), detailed guidance in categorized files. Prevents the single file from bloating again.
- **Warrant:** Agent instruction files that cover everything become hard to maintain and waste context. Separating by topic improves retrieval.
- **Qualifier:** always
- **Status:** settled

### D2 — Use docs/agent-instructions/ not .claude/

- **Issue:** The `.claude/` directory name is tool-specific
- **Positions:** (1) `.claude/` (2) `docs/agent-instructions/` (3) `agent-guides/`
- **Arguments:** The user explicitly said they don't use Claude. `docs/agent-instructions/` won — it lives under the existing `docs/` tree and is tool-agnostic.
- **Warrant:** Directory names should match organizational structure, not runtime tooling.
- **Qualifier:** always
- **Status:** settled

### D3 — Observation capture uses synchronous JSONL append, not SQLite

- **Issue:** What storage backend for a one-shot CLI's observation data
- **Positions:** (1) JSONL append (2) SQLite (3) In-memory buffer
- **Arguments:** JSONL won — ~5-15µs write cost, no schema, human-readable, trivial to aggregate. SQLite adds schema management, connection handling, and ~50-200µs per write for no benefit at CLI scale.
- **Warrant:** A one-shot CLI that lives seconds doesn't need a database engine for a few KB of observability data per run.
- **Qualifier:** always
- **Status:** settled

### D4 — Three-dimension capture: criterion, context, outcome

- **Issue:** What to capture from user-agent interactions
- **Positions:** (1) Just CLI errors and timing (2) Full conversation transcription (3) Structured criterion + context + outcome
- **Arguments:** Option (3) won. CLI-only capture misses intent and outcome. Full transcription is too heavy and violates privacy. The three fields map cleanly to all three levels of the AIX correction loop.
- **Warrant:** Closing the improvement loop requires knowing not just what failed, but why it was attempted and whether the user's actual need was met.
- **Qualifier:** always
- **Status:** settled

### D5 — Outcome inferred from user's next turn

- **Issue:** How to determine if the user's need was met without asking them
- **Positions:** (1) Ask explicitly (2) Infer from next message (3) Default to unknown
- **Arguments:** Inference won — explicit asking adds friction. Heuristic rules: new topic = resolved, same topic follow-up = partial, rephrase = unresolved, "never mind" = abandoned. Fallback to unknown when unsure.
- **Warrant:** User behavior patterns reliably indicate satisfaction without requiring an explicit rating. The inference is cheap and good enough for aggregate trends.
- **Qualifier:** usually
- **Status:** settled

## INSIGHTS

### I1 — Correction vs improvement

A retry is self-correction. A persistent behavioral change across sessions is self-improvement. The mechanism that turns one into the other is **pattern extraction** — recording not just what failed but why, and applying the lesson to all similar future situations.

### I2 — CLI blind spot

The CLI sees only the final command string. The conversation context (user's original question, agent's reasoning, back-and-forth, interpreted results) lives entirely upstream in the AI session. Instrumenting only the CLI layer misses intent and outcome.

### I3 — Three-dimension schema maps to AIX's three levels

| Workboard dimension | AIX Level 1 | AIX Level 2 | AIX Level 3 |
|---|---|---|---|
| Criterion | `category` + `text` | `trigger` | `problem_type` + `symptoms` |
| Context | `context` (one line) | `What Didn't Work` narrative | Full solution doc |
| Outcome | `status: resolved` | `fix` + `Result` | `resolution_type` + `Why This Works` |

### I4 — The seven components of a working corrections loop

From AIX: output capture, evaluation signal, root-cause diagnosis, extraction into actionable form, persistent storage, retrieval + integration, meta-evaluation. The workboard capture currently covers 1-2. The remaining 3-7 are the gap.

## PATTERNS

### P1 — Progressive disclosure for agent instructions

- **Scope:** universal
- **Problem:** Bloated AGENTS.md files waste context and are hard to maintain
- **Solution:** Split into a minimal root (essentials only) + categorized linked files by topic. Root under 50 lines. Each file self-contained.
- **Steps:** (1) Find contradictions (2) Extract essentials for root (3) Categorize remaining (4) Create file hierarchy (5) Prune vague/obsolete instructions
- **Source:** agent-md-refactor skill, applied to this repo.

### P2 — Three-level observation capture for CLI tools

- **Scope:** local (workboard-cli)
- **Problem:** No signal about how users actually interact with the tool — what they need, where they get stuck, whether their needs are met
- **Solution:** Two layers — CLI-level (commands, errors, timing via ~50-line module with hooks) and agent-level (criterion, context, outcome via structured JSONL). Weekly aggregation script ranks gaps by frequency. Top 3 = next improvement cycle.
- **Components:** (1) JSONL capture module on-by-default (2) Three hook points in CLI code (3) Gap callback for slow requests (4) Agent-level capture instructions (5) Aggregation + ranking script (6) Weekly review cadence

## OPEN_QUESTIONS

### O1 — Will the weekly review actually happen?

The capture infrastructure is built but the loop requires a human (or agent) to run the aggregation script, extract gaps, diagnose root causes, implement fixes, and meta-evaluate. Without this cadence, the observation logs accumulate but no improvement happens.

### O2 — What's the promotion threshold?

How many occurrences of a gap justify a fix? One user asking for a feature vs ten users? What's the tradeoff between fixing a gap that affected one person vs one that affected many?

## NEXT_STEPS

### N1 — Run the first weekly analysis (soon)

After observations accumulate for 7 days, run `python scripts/analyze-observations.py --days 7` and review the top 3 gaps.

### N2 — Track outcome trend over time (soon)

The north star metric: `resolved_partial` + `unresolved` counts should trend down week over week. If they don't, the loop isn't working.

### N3 — Close the remaining 5 correction loop components (someday)

The capture layer (components 1-2) is built. For true self-improvement, add: root-cause diagnosis (3), extraction into actionable form (4), retrieval on future tasks (6), and meta-evaluation (7).

## Connections

- D1 —[led_to]→ A1 (decision to refactor produced the artifact)
- D2 —[informed_by]→ A1 (directory naming choice embedded in artifact structure)
- D1 —[related_to]→ P1 (refactor was an instance of the progressive disclosure pattern)
- I2 —[informed_by]→ D4 (CLI blind spot motivated the three-dimension schema)
- I1 —[informed_by]→ AIX corrections loop concept
- I3 —[informed_by]→ AIX session on correction loop schemas
- D3 —[informed_by]→ AIX analysis of storage tradeoffs
- D5 —[related_to]→ I4 (outcome inference is the meta-evaluation component)
- A3 —[instance_of]→ P2 (CLI-level capture)
- A5 —[instance_of]→ P2 (agent-level capture)
- A4 —[instance_of]→ P2 (aggregation component)
- D4 —[led_to]→ A3, A5 (schema decision produced both capture layers)

## Trail Updates

- **workboard-cli-evolution** — Extended with: (1) Progressive disclosure AGENTS.md (2) @workboard agent (3) Observation capture system across CLI and agent layers
- **observation-capture-strategy** — Created. Documents the three-dimension schema, the two-layer architecture, the AIX-informed design, and the weekly review cadence.
