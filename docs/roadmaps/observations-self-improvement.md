# Observations Self-Improvement — Implementation Roadmap

Turn CLI telemetry into a closed loop where usage patterns drive CLI improvements automatically.

## Status

Draft (2026-06-19). Start with Phase 1 before moving to Phase 2.

## Current State

- **Capture layer**: Done. `observations.py` captures 4 event types (`invocation`, `error`, `crash`, `interaction_gap`) to JSONL at `~/.local/share/workboard/observations/`. All events carry a process-scoped `session_id` for cross-stream correlation ([design pattern](design-patterns/session-id-correlation.md)).
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

## Using CE Skills

Compound Engineering skills ([docs](https://every.to/guides/compound-engineering), [plugin repo](https://github.com/EveryInc/compound-engineering-plugin)) provide structured workflows for each stage of this roadmap. Load the relevant skill when the trigger condition is met — each one resolves what to do next, then hands off to the next skill in the chain.

### Skill Reference Table

| Skill | Phase(s) | Trigger — load this when… | What it produces |
|---|---|---|---|
| **ce-ideate** | All | You need ideas for what to work on next, or want to explore surprising directions before picking one. | Ranked ideation artifact in `docs/ideation/` — candidate directions with rejection rationale, survivors, and basis citations. |
| **ce-brainstorm** | 1, 2, 3 | You have an idea or candidate direction and need to resolve scope, success criteria, and product decisions before planning. | Requirements document in `docs/brainstorms/` — user-facing behavior, scope boundaries, acceptance criteria, trade-offs. |
| **ce-agent-native-architecture** | 2, 3 | You're designing a system where agents read, write, or act autonomously — auto-PR drafting, session-context injection, or cross-session behavior updates. | Architecture decisions for agent-native features: which agents exist, their permissions, handoff protocols, observability, and safety boundaries. |
| **ce-plan** | 1, 2, 3 | You have clear requirements (from brainstorm or direct knowledge) and need to decompose the work into implementable units with files, dependencies, risks, and test scenarios. | Implementation plan in `docs/plans/` — implementation units with U-IDs, approach, file lists, test scenarios, verification criteria. |
| **ce-work** | 1, 2 | You have a plan (or a well-defined bare-prompt task) and want to execute — implement, test, and commit. | Implemented code, passing tests, incremental commits on a feature branch. |
| **ce-code-review** | 1, 2, 3 | Before opening a PR, or after a batch of implementation is complete. Loads 6-14 reviewer personas against the diff. | Structured review report with severity-gated findings (P0-P3), deduplicated, validated, and optionally auto-fixed. |
| **ce-commit-push-pr** | 1, 2 | You have committed work on a branch and want to open a PR with a value-first description. | PR on GitHub with an adaptive description scaled to change depth. |
| **ce-compound** | 1, 2, 3 | A non-trivial problem has just been solved — a bug found deep in a module, a surprising edge case, a hard-won lesson. | Learning doc in `docs/solutions/<category>/` with YAML frontmatter, root cause, solution, and prevention. |
| **ce-compound-refresh** | 1, 2, 3 | An older `docs/solutions/` doc may be stale, contradicted by new learnings, or overlapping with a new solution. | Refreshed, consolidated, or archived learning docs — duplicates merged, drift corrected. |
| **ce-optimize** | 2, 3 | You have a measurable knob (threshold, cutoff, weight) and want to find its best value through parallel experiments. | Experiment log — baseline, batch results, winning configuration with delta. |
| **ce-debug** | 1, 2, 3 | Observation capture stops working, the analysis script crashes, auto-PR drafts malformed content, embedding routing returns wrong intents. | Debug summary with causal chain, confirmed root cause, test-first fix, and prevention recommendations. |
| **ce-simplify-code** | 1, 2, 3 | After implementing a cluster of related changes (especially clustering logic, promotion pipelines, or embedding routing) when the diff is ≥30 lines. | Simplified code — deduplicated utilities, consolidated abstractions, dead code removed. Behavior verified via tests. |
| **ce-strategy** | All | The roadmap itself needs updating — a phase scope changes, a new track emerges, or you're aligning work with product direction. | Updated `STRATEGY.md` — target problem, approach, persona, metrics, and tracks of work. |
| **ce-sessions** | All | Before starting a new phase (or resuming after a break) — check if prior sessions already tried the approach or hit dead ends. | Structured digest of prior agent sessions: what was tried, what didn't work, key decisions. |
| **ce-demo-reel** | 1, 2 | Shipping CLI changes — capture visual proof of the `observations stats` output or slow-query warning in the PR description. | GIF, terminal recording, or screenshot embedded in the PR description showing before/after behavior. |

### Recommended Flow Per Phase

```
Phase 1 (Quick Wins):
  ce-ideate → ce-brainstorm → ce-plan → ce-work → ce-code-review → ce-commit-push-pr → ce-compound
  ├── ce-debug (if pipeline breaks)
  ├── ce-simplify-code (after clustering logic lands)
  └── ce-demo-reel (for CLI output evidence in PR)

Phase 2 (Closed Loop):
  ce-ideate → ce-brainstorm → ce-agent-native-architecture → ce-plan → ce-work → ce-code-review → ce-compound
  ├── ce-optimize (tune promotion threshold & similarity cutoff)
  ├── ce-debug (if auto-PR drafts are malformed)
  ├── ce-simplify-code (after promotion pipeline stabilizes)
  └── ce-compound-refresh (consolidate older learnings with new ones)

Phase 3 (Advanced):
  ce-brainstorm → ce-agent-native-architecture → ce-plan → ce-work → ce-code-review → ce-compound
  ├── ce-optimize (tune embedding similarity, confidence cutoffs)
  ├── ce-debug (embedding routing issues, outcome inference failures)
  └── ce-simplify-code (embedding classification code)
```

### When to Skip Skills

- **ce-brainstorm**: Skip when requirements are already clear (well-scoped tickets, existing spec). Go straight to `ce-plan`.
- **ce-agent-native-architecture**: Skip for pure CLI work that doesn't involve agent autonomy. Only load when agents make decisions or write drafts.
- **ce-optimize**: Skip when default threshold values work well enough. Only invest in systematic tuning when false positives or misses cost real time.
- **ce-compound**: Skip for trivial fixes (typos, one-line config changes). The bar: "Would future me or a teammate benefit from searching for this?"
- **ce-sessions**: Skip when working on a well-understood problem with no reason to believe prior attempts exist.

### Pro Tip: Plan U-IDs Stabilize Cross-Skill Traceability

When `ce-plan` creates implementation units with stable U-IDs (`U1`, `U2`, …), reference them when spawning `ce-work`, when reviewing with `ce-code-review` (pass `plan:<path>`), and when compounding via `ce-compound`. The IDs survive reordering and splitting, giving you unambiguous traceability from requirements → implementation → review → learning.`
