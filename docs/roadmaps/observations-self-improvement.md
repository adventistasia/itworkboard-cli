# Observations Self-Improvement — Implementation Roadmap

Turn CLI telemetry into a closed loop where usage patterns drive CLI improvements automatically.

## Status

Draft (2026-06-19). Start with Phase 1 before moving to Phase 2.

## Current State

- **Capture layer**: Done. `observations.py` captures 4 event types (`invocation`, `error`, `crash`, `interaction_gap`) to JSONL at `~/.local/share/workboard/observations/`
- **Analysis layer**: Partial. `scripts/analyze-observations.py` reads JSONL and prints a report
- **Improvement loop**: Manual. Human reviews report, human writes fix
- **Agent capture**: Defined in `.opencode/agents/workboard.md` but not yet automated

## Phases

### Phase 1 — Quick Wins (ship these first, smallest effort)

| # | Step | What to Do | File(s) | Verification |
|---|------|-----------|---------|-------------|
| 1.1 | Add `observations stats` CLI command | Wrap `analyze-observations.py` logic into a `workboard observations stats --days N` command that outputs JSON report | `src/workboard_cli/cli.py`, new `src/workboard_cli/observations.py` additions | `workboard observations stats --days 7` prints structured report |
| 1.2 | Surface slow Graph calls as stderr warnings | When `interaction_gap` fires (>3s), emit a one-line warning to stderr: `Warning: <endpoint> took <ms>ms` | `src/workboard_cli/graph_client.py` or callback in `cli.py` | Run a slow query, see warning on stderr, JSON output on stdout intact |
| 1.3 | Add keyword clustering to analysis script | Group `unsupported_intent` errors by n-gram similarity. Report top clusters as candidate new intents/aliases | `scripts/analyze-observations.py` | Report includes "Unrecognized intent patterns" section with cluster → suggested fix |

**Phase 1 is done when**: You can run `workboard observations stats` and see actionable insight (top errors with clusters, slowest endpoints) without leaving the CLI.

### Phase 2 — The Closed Loop

| # | Step | What to Do | File(s) | Dependencies |
|---|------|-----------|---------|-------------|
| 2.1 | Threshold-based gap promotion | When error clusters exceed N occurrences (default: 5) in 7 days, generate a structured gap report with suggested fix (new intent, alias, or better error message) | `scripts/analyze-observations.py` or new `scripts/promote-gaps.py` | 1.3 |
| 2.2 | Auto-PR drafts from gap report | Agent reads gap report, creates a branch with the suggested change, opens a PR with evidence from observations. Human must approve. | CI config + agent instructions | 2.1 |
| 2.3 | Outcome trend dashboard | Rolling 7-day window chart of resolved / partial / unresolved ratios. Alert if no improvement for 3 consecutive weeks. | `scripts/outcome-trend.py` → `docs/observation-trend.md` | 2.1 |
| 2.4 | Recent failures context injection | At session start, inject last N observation errors into the agent's context so it knows what's been failing | `.opencode/agents/workboard.md` | 2.1 |

**Phase 2 is done when**: A user repeatedly types a query the CLI doesn't understand, and a PR with the fix is drafted without a human touching the code.

### Phase 3 — Advanced

| # | Step | What to Do | Rationale |
|---|------|-----------|-----------|
| 3.1 | Semantic intent routing | Replace strict `APPROVED_INTENTS` matching with embedding-based similarity. Route high-confidence fuzzy matches directly, ask for confirmation on medium-confidence ones. | Scales to 60+ intents without brittle string matching |
| 3.2 | Heuristic outcome inference | Automate the D5 heuristic: infer resolved / unresolved from user's next turn (new topic = resolved, same topic rephrase = unresolved, "never mind" = abandoned). Agent writes observation automatically. | Removes manual agent capture requirement |
| 3.3 | Schema drift auto-detection | When warnings with unknown field values exceed threshold, auto-run `schema export`, diff against config, open PR to update field mappings. | Most common silent drift problem for SharePoint CLIs |
| 3.4 | Cross-session behavioral change | Pattern extraction from multiple sessions → persistent agent instruction updates without human in loop | Autonomous self-improvement |

**Phase 3 is done when**: The system detects, diagnoses, and fixes its own gaps with only exception-flag human review.

## Guiding Principles

1. **Human approves every change.** Auto-PRs are drafts, not merges. Trust is built through transparent diffs with observation evidence attached.
2. **Noisy gaps get filtered.** Cluster by n-gram similarity, count by unique sessions, only promote clusters that appear in multiple sessions. Single-fat-finger typos do not become PRs.
3. **Privacy first.** Structured dimensions only (event type, command string, error code, timing). No full conversation capture. Opt-out via `WORKBOARD_OBS_DISABLE=1`.
4. **80/20 rule.** Phase 1 delivers the most signal for the least effort. Do not skip to Phase 2 until Phase 1 ships and generates real data.

## Key Files Reference

| Path | Role |
|------|------|
| `src/workboard_cli/observations.py` | Core capture module (CLI events) |
| `src/workboard_cli/graph_client.py` | HTTP client with `on_gap` callback |
| `src/workboard_cli/cli.py` | CLI entry point — observation hooks at `_crash_hook`, `_error_exit`, `_get_client`, `main` callback |
| `scripts/analyze-observations.py` | Current analysis script (target for clustering upgrade) |
| `.opencode/agents/workboard.md` | Agent instructions — observation capture rules (lines 163-218) |
| `docs/agent-instructions/agent-intents.md` | Intent definitions (target for new intent additions) |
| `docs/agent-instructions/maintenance.md` | Schema drift detection workflow |

## Pitfalls

- **Noisy gaps** — not every `unsupported_intent` is a feature request. Use session-unique counting, not raw count.
- **Outcome inference is ~70% accurate** — track aggregate trends, not per-interaction accuracy.
- **Auto-PRs destroy trust if they merge silently** — always require human approval, always include rollback path.
- **Cadence decay** — weekly review won't sustain. Phase 2 automation exists precisely because human cadence doesn't scale.
