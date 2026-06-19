# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Observations (telemetry)

### session_id
A process-scoped UUID v4 that correlates entries across the two observation streams (CLI events and agent observations). Generated once per process at module import time. Distinct from an HTTP session or user session — it identifies a single CLI invocation + any agent conversation it spawns.
*Avoid:* session, sessionId, correlation_id

### observation_stream
One of two parallel JSONL event logs in the observation directory: the CLI event stream (`workboard-observations.jsonl`, written by `capture()`) and the agent observation stream (`workboard-agent-observations.jsonl`, written by the AI agent). Together they form a bifurcated capture of what the CLI did and what happened in the conversation. Correlatable via `session_id`.
