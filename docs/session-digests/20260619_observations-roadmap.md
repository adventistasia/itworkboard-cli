# Session Digest — 2026-06-19

## Summary

Explored the workboard CLI's observations subsystem and produced a phased roadmap for turning telemetry into a self-improving closed loop.

## Key Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Keep observations as an in-process CLI subcommand, not a separate `workboard-obs-cli` tool | Capture layer is tightly coupled to workboard CLI's lifecycle. A separate tool would duplicate wiring for little gain. Extract shared analysis library later if pattern proves useful across tools. |
| D2 | Roadmap lives in `docs/roadmaps/` | Follows existing docs structure, distinct from `docs/solutions/` (past learnings) and `docs/agent-instructions/` (agent guidance) |
| D3 | Start with Phase 1 quick wins before Phase 2 automation | 80/20 rule — `observations stats` and slow-query warnings ship fast and validate the loop before building clustering/auto-PR |

## Artifacts Created

- `docs/roadmaps/observations-self-improvement.md` — three-phase implementation roadmap

## Key Findings

1. **Observations is not a CLI command** — it's an invisible telemetry layer with 4 event types (`invocation`, `error`, `crash`, `interaction_gap`) plus agent-level capture with 7 trigger types
2. **Current JSONL data** shows 100 events from recent sessions — mostly `invocation` (89) and `unsupported_intent` errors (4), no crashes or slow-gap events
3. **CE skill sequence** for implementation: brainstorm → agent-native-architecture → plan → work → code-review → compound
4. **AIX research** identified the 7-component correction loop; our capture covers components 1-5, missing automated diagnosis→fix and meta-evaluation

## Next Steps

- Phase 1.1: Add `workboard observations stats --days N` CLI command
- Phase 1.2: Surface slow Graph calls as stderr warnings
- Phase 1.3: Add keyword clustering for unsupported intent errors

## Open Questions

- What should the promotion threshold be? (Default: 5 in 7 days, configurable)
- How to handle false positives from fat-finger typos vs genuine feature requests?
- Should the analysis library be extracted early if other CLIs adopt the pattern?
