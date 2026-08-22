---
lorespec: "0.1"
id: "2026082201"
date: "2026-08-22"
source: "claude"
topic: "End-to-end LFG-ship pipeline: normalized WorkBoard item capture from requirements-only plan to merge-ready PR"
tags: [lfg, paseo, compound-engineering, workboard, normalization, sharepoint, cli]
classification:
  type: technical
  secondary_type: strategy
  domains: [ai-engineering, cli-tools, sharepoint]
  value: high
trails: [workboard-cli, compound-engineering-pipeline]
---

## Session Arc

### Started
Operator invoked LFG pipeline on an existing requirements-only plan (`docs/plans/2026-08-21-002-feat-normalized-item-capture-plan.md`) for normalized WorkBoard item capture. The plan had a complete Product Contract with 16 requirements, 17 acceptance examples, and 7 session-settled decisions, but was `artifact_readiness: requirements-only`.

### Pivots
- **Plan enrichment gate**: LFG pipeline correctly stopped at step 1 because the plan was requirements-only. Operator chose to dispatch `ce-plan` to promote it to implementation-ready.
- **Claude auth failure**: First planning agent on `claude/claude-opus-5` failed ("Not logged in"). Fell back to `codex/gpt-5.6-sol` (planning fallback per orchestration preferences). Planning succeeded.
- **Implementation agent analysis paralysis**: First implementation agent on `opencode-go/mimo-v2.5` got stuck in deep analysis without writing code. Sent explicit follow-up telling it to "stop analyzing and start implementing." Agent then completed all 5 units.
- **Operator requested lfg-ship**: Mid-pipeline, operator switched from standard LFG to `lfg-ship` for the merge-ready loop (Copilot review → judge → fix cycle).
- **Code review found 6 issues**: NIC-01 through NIC-06, including 2 P1s (malformed date sentinel violation, unresolved --list primary detection). Applied fixes, verified tests.
- **Copilot review found 2 issues**: C1 (false positive — cfg key always populated), C2 (real — malformed date missing warning). Judge confirmed C2, declined C1. Fixed C2, Copilot round 2 clean, judge verdict: ready.

### Ended
PR #17 merged to main via squash. Branch deleted locally and remotely. All agents archived. Working tree clean.

## Knowledge Objects

### ARTIFACT

**A1 — Normalized Item Capture PR (#17)**
- Extends WorkItem as single authoritative normalized item contract
- Primary `items get` returns raw `result.item` + WorkItem at `result.workItem` automatically
- Added `scopeText`, `requirementsText` to WorkItem
- `_get_field(required=)` distinguishes required vs optional field warnings
- `_validate_source_url` validates webUrl as absolute HTTP(S)
- `_parse_date` returns None + warning for malformed dates
- 225 tests (was 204), ruff clean
- Files: `normalize.py`, `cli.py`, `test_normalize.py`, `test_cli.py`, `agent_json_contract.md`, `cli_command_contract.md`
- Source: `docs/plans/2026-08-21-002-feat-normalized-item-capture-plan.md`

### DECISION

**D1 — Merge `_get_field` and `_get_mapped_field` into one helper**
- **Decision**: Single `_get_field(raw_fields, field_name, warnings, *, required=False)` function
- **Issue**: Two near-identical functions with invisible behavioral distinction
- **Positions**: Keep separate (clarity) vs merge with keyword arg (reuse)
- **Arguments**: Merge eliminates duplication, `required=` makes the contract explicit at call sites
- **Warrant**: Function names should communicate their contract; `required=` is the natural distinction
- **Qualifier**: in this case
- **Status**: settled

**D2 — `_parse_date` must warn on malformed values**
- **Decision**: Add `warnings=None` parameter, append on 3 failure paths
- **Issue**: Malformed dates silently returned None without warning, violating KTD4/AE15
- **Positions**: Silent None (simpler) vs sentinel + warning (contract-compliant)
- **Arguments**: Plan requires malformed content to never be authoritative; warning is the diagnostic signal
- **Warrant**: The contract says malformed values get sentinel + warning; silent None breaks traceability
- **Qualifier**: always (contract requirement)
- **Status**: settled

**D3 — Optional field absence does NOT warn**
- **Decision**: `_get_field` only warns when `required=True` and field is absent
- **Issue**: Original code warned for all missing fields including optional ones
- **Positions**: Warn always (conservative) vs warn only for required (contract-correct)
- **Arguments**: Q5/AE14 require genuine optional absence to use sentinel with NO warning
- **Warrant**: Consumers should distinguish "field not configured" from "field configured but empty"
- **Qualifier**: always (session-settled Q5)
- **Status**: settled

### PATTERN

**P1 — LFG-Ship Pipeline Execution**
- Scope: local (this project's CE workflow)
- Steps: ce-plan enrichment → ce-work implementation → ce-simplify-code → ce-code-review → apply fixes → commit-push-pr → ce-babysit-pr (CI) → merge-ready loop (Copilot review → judge → fix cycle)
- Key insight: Plan enrichment is a gating step — requirements-only plans cannot be implemented directly
- Key insight: The merge-ready loop requires cross-family judge (minimax-m3) for genuine contrast from the fixer (mimo-v2.5)
- Key insight: Operator can switch pipelines mid-flight (LFG → lfg-ship) — the phases are composable

**P2 — Paseo Agent Dispatch for Multi-Phase Work**
- Scope: local (Paseo orchestration)
- Pattern: Dispatch agents per phase, wait for notification, verify output, continue
- Key insight: Agent responses can be truncated — always verify actual state (git status, tests) rather than trusting the response
- Key insight: Some agents get stuck in analysis paralysis — explicit "stop analyzing, start implementing" follow-ups work

### SOLUTION

**S1 — Agent Analysis Paralysis Recovery**
- What was broken: Implementation agent spent full context window analyzing without writing code
- Fix: Sent explicit follow-up with specific file targets and "stop analyzing and start implementing"
- Why it works: Removes ambiguity about what to do next; gives the agent a concrete starting point
- Caveat: The agent still needs sufficient context to implement correctly

### OPEN_QUESTION

**O1 — NIC-06: Missing list-identity aliasing test**
- The plan specifies a test for primary internal name + display-name alias invocation
- Not implemented (P3, test-only)
- Blocks: nothing (all other tests pass)

## Connections

- A1 —[instance_of]→ P1 (normalized item capture is an instance of the LFG-ship pipeline pattern)
- D1 —[informed_by]→ A1 (merge decision simplified the implementation)
- D2 —[led_to]→ C2 fix (judge identified the gap, fix applied)
- D3 —[informed_by]→ Q5 session-settled decision
- S1 —[related_to]→ P2 (recovery pattern for agent dispatch)

## Trail Updates

- **workboard-cli**: Extended with normalized item capture feature. PR #17 merged.
- **compound-engineering-pipeline**: Validated full LFG-ship flow including plan enrichment gate, code review with fix cycle, and merge-ready loop.

## Next Steps

- N1 — Implement NIC-06 test for list-identity aliasing (P3, someday)
- N2 — Reconcile `.opencode/agents/workboard.md` routing that sends single-item requests to `items get` (separate contract drift, documented in plan out-of-scope)
