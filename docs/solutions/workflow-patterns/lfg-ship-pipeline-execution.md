---
title: LFG-ship pipeline execution
date: 2026-08-22
category: workflow-patterns
module: compound-engineering
problem_type: workflow_issue
component: development_workflow
severity: medium
applies_when:
  - "Running the LFG or lfg-ship pipeline on a feature plan"
  - "The source plan has artifact_readiness: requirements-only"
  - "Dispatching planning or implementation agents through Paseo"
  - "Driving a PR to merge-ready via Copilot review plus a judge"
tags:
  - lfg-ship
  - pipeline
  - plan-enrichment
  - merge-ready-loop
  - paseo
  - agent-orchestration
  - cross-family-judge
  - analysis-paralysis
---

# LFG-ship pipeline execution

## Context

A full LFG-ship run shipped normalized WorkBoard item capture to production: requirements-only plan → implementation-ready plan → implementation → code review → Copilot review → judge → merge-ready PR. PR #17 (`feat: normalized WorkBoard item capture`) is merged to `main`. The run surfaced five recurring failure modes in the pipeline: plan enrichment gating, provider fallback, agent analysis paralysis, the code-review fix cycle, and the merge-ready loop. Each was solved with a small, repeatable intervention. This doc captures those interventions so the next LFG-ship run starts from the playbook instead of rediscovering it.

## Guidance

### 1. Plan enrichment is a mandatory gate

Check `artifact_readiness` in the plan frontmatter before dispatching any implementation agent. A `requirements-only` plan must be promoted to `implementation-ready` via `ce-plan` first — implementation agents assume the plan is executable and stall or improvise on a plan that only states requirements.

- Run: `ce-plan` in pipeline mode against the plan path.
- Gate condition: the enriched plan frontmatter reads `artifact_readiness: implementation-ready`.
- The LFG pipeline correctly stopped at step 1 when it detected `requirements-only`; do not bypass the gate to save a step.

### 2. Provider fallback on agent auth failure

When the configured planning provider fails to authenticate (e.g., "Not logged in · Please run /login"), do not retry the same provider. Fall back to the planning fallback provider from orchestration preferences (`codex/gpt-5.6-sol` in this setup). The fallback produced a complete enrichment in one pass.

- Verify auth before dispatching long work: a failed agent burns the pipeline step.
- Keep the fallback decision recorded in the session so the operator can see which provider actually did the work.

### 3. Recover implementation agents from analysis paralysis

Agents dispatched with a full plan sometimes burn their context analyzing instead of writing code. Recovery: send an explicit follow-up naming the concrete starting point and instructing "stop analyzing and start implementing." This worked immediately — the agent completed all five implementation units after the nudge.

- Never trust the agent's narrative about its own state; verify with `git status` and the test suite.
- Agent responses can be truncated — always confirm actual repo state before advancing the pipeline.

### 4. Run the code-review fix cycle

`ce-code-review` returned 6 findings (NIC-01 through NIC-06: 2 P1, 2 P2, 2 P3). Apply P1/P2 fixes immediately, re-run tests, and re-review. Notable P1 fixes from this run:

- Malformed date sentinel violation: `_parse_date` must return `None` plus a warning on malformed input (`src/workboard_cli/normalize.py:30`).
- `items get` must resolve the omitted `--list` flag to the configured primary list name before primary-list detection.

P3 findings may be deferred only with explicit agreement (NIC-06, a test-only aliasing test, was deferred without blocking).

### 5. Drive the merge-ready loop with a cross-family judge

The merge-ready loop is: Copilot review → judge verdict → fix → repeat until ready. Use a judge from a different model family than the fixer — the cross-family contrast is what makes the judge independent. In this run the fixer was `mimo-v2.5` and the judge was `minimax-m3`.

- The judge correctly identified Copilot's C1 as a false positive (the `cfg` key is always populated) and C2 as a real issue (malformed date missing warning).
- Fix the real issue, then run Copilot round 2; a clean second round plus judge "ready" verdict closes the loop.

## Why This Matters

Each failure mode, left unhandled, stalls the pipeline: an unenriched plan produces improvisation, an auth failure wastes the step, analysis paralysis burns an agent's context budget, unreviewed code ships defects, and an unchallenged review either blocks on false positives or merges real defects. The five interventions above are small, cheap, and each was proven on this run. Following them turns LFG-ship from a fragile multi-agent chain into a repeatable pipeline: PR #17 went from requirements-only plan to merged in a single session with 225 tests passing and ruff clean.

## When to Apply

- Any LFG or lfg-ship invocation on a plan you did not enrich yourself.
- Any Paseo dispatch where the provider is known to be flaky or unauthenticated.
- Any implementation agent that has produced analysis but no diffs after its first turn.
- Any PR heading to merge where Copilot is the primary reviewer.
- Any session where the operator switches pipelines mid-flight (LFG → lfg-ship) — the phases compose; only the merge-ready loop is added.

## Examples

- **Gate check**: `docs/plans/2026-08-21-002-feat-normalized-item-capture-plan.md` started as `requirements-only`; after `ce-plan` enrichment its frontmatter reads `artifact_readiness: implementation-ready` (line 7).
- **Fallback**: the first planning agent on `claude/claude-opus-5` replied "Not logged in · Please run /login"; the run fell back to `codex/gpt-5.6-sol`, which produced the enrichment. (session history)
- **Paralysis recovery**: the implementation agent on `opencode-go/mimo-v2.5` was sent "stop analyzing and start implementing" with specific file targets, then completed all 5 units.
- **Judge contrast**: Copilot flagged C1 (cfg key) and C2 (date warning); `minimax-m3` declined C1 as a false positive and confirmed C2, which was then fixed and re-reviewed clean.
- **End state**: PR #17 merged via squash (`dfc08b8`), 225 tests, ruff clean, working tree clean.

## Related

- Feature plan: [docs/plans/2026-08-21-002-feat-normalized-item-capture-plan.md](../../plans/2026-08-21-002-feat-normalized-item-capture-plan.md)
- Session digest: [docs/session-digests/2026082201_normalized_item_capture_ship.md](../../session-digests/2026082201_normalized_item_capture_ship.md)
- GitHub: PR #17 (`feat: normalized WorkBoard item capture`, merged)
- Prior session context: the issue #6 brainstorm on `codex/gpt-5.6-sol` established the dual `result.item` + `result.workItem` design that the plan built on. (session history)