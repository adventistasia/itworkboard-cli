# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Observations (telemetry)

### session_id
A process-scoped UUID v4 that correlates entries across the two observation streams (CLI events and agent observations). Generated once per process at module import time. Distinct from an HTTP session or user session — it identifies a single CLI invocation + any agent conversation it spawns.
*Avoid:* session, sessionId, correlation_id

### observation_stream
One of two parallel JSONL event logs in the observation directory: the CLI event stream (`workboard-observations.jsonl`, written by `capture()`) and the agent observation stream (`workboard-agent-observations.jsonl`, written by the AI agent). Together they form a bifurcated capture of what the CLI did and what happened in the conversation. Correlatable via `session_id`.

## Compound engineering pipeline

### LFG-ship pipeline
The end-to-end autonomous shipping pipeline: plan enrichment, implementation, simplification, code review with fix cycle, commit/push/PR, then a merge-ready loop that ends in a ready verdict (never an auto-merge). Phase-composable — the operator may switch from plain LFG to lfg-ship mid-flight by adding the merge-ready loop.

### Plan enrichment gate
The rule that a plan must be `implementation-ready` (not `requirements-only`) before an implementation agent is dispatched. Requirements-only plans are promoted first by a planning skill; bypassing the gate makes implementation agents stall or improvise.

### Merge-ready loop
The review-fix cycle that drives a PR to a ready verdict: primary reviewer (Copilot), a judge agent that rules on each finding, fixes applied, then a re-review round until the judge says ready. The judge's verdict decides what gets fixed — a finding declined as a false positive is not fixed.

### Cross-family judge
A judge agent drawn from a different model family than the fixer. The family contrast is what makes the judge independent — a judge from the same family tends to replicate the fixer's blind spots.
