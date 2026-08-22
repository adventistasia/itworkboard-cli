---
title: Normalized WorkBoard Item Capture - Plan
date: 2026-08-21
type: feat
topic: normalized-item-capture
artifact_contract: ce-unified-plan/v1
artifact_readiness: requirements-only
product_contract_source: ce-brainstorm
execution: code
source_issue: https://github.com/adventistasia/itworkboard-cli/issues/6
source_observed: 2026-08-21
contract_decisions_observed: 2026-08-22
repository_revision: ee1e67e
---

# Normalized WorkBoard Item Capture - Plan

## Goal Capsule

- **Objective:** Define the product contract for stable, item-level capture from `workboard items get <ID>` so automation can consume canonical WorkBoard meaning without repeatedly parsing SharePoint-specific field shapes.
- **Product authority:** This plan owns the requirements and acceptance boundary for normalized capture of a single WorkBoard item through the authoritative WorkItem contract. Additive WorkItem fields will propagate to existing surfaces that already serialize WorkItem, but changing list, query, or intent behavior remains outside active scope, as do new acceptance or closure state and SharePoint writes.
- **Open blockers:** None. Q1 was settled on 2026-08-21 and reaffirmed with the complete contract decision pass on 2026-08-22; Q2-Q7 were session-settled on 2026-08-22.

---

## Product Contract

### Summary

Provide a stable normalized representation of one WorkBoard item while preserving raw source fidelity, source metadata, and existing contract meanings.
Use WorkItem as the single authoritative normalized item contract and extend it additively for missing capture semantics.
For successful retrievals from the configured primary WorkBoard list, `items get` automatically preserves the unchanged raw Graph item at `result.item` and adds WorkItem at `result.workItem`; successful custom-list retrievals remain raw-only.

### Problem Frame

The single-item command currently returns the Graph item directly under the result envelope and does not invoke the repository's normalization path (`src/workboard_cli/cli.py:313-341`).
The separate WorkItem projection already normalizes several fields, but it uses `relProject`, lower-camel date names, and a mix of raw and extracted long-form values; it does not surface `Scope` or `Requirements` (`src/workboard_cli/normalize.py:142-214`; `docs/agent_json_contract.md:64-142`).
As a result, downstream capture and wiki automation must understand both SharePoint field conventions and repository-specific partial normalization before it can treat a work item as a durable operational record.

This matters because a WorkBoard item is the primary operational record even when it has no linked project.
Parsing raw HTML and lookup blobs independently in every consumer makes linked-project, authority, acceptance-evidence, and closure-date capture less reliable.

### Evidence and Decision Status

| Status | Evidence | Contract consequence |
|---|---|---|
| Confirmed repository fact | The product is a read-only, agent-oriented JSON boundary over SharePoint (`STRATEGY.md:7-35`; `AGENTS.md:19-25`). | The feature must remain read-only, keep SharePoint authoritative, and retain source metadata. |
| Confirmed repository fact | `items get` returns the fetched Graph item without normalizing it (`src/workboard_cli/cli.py:313-341`; `src/workboard_cli/sharepoint.py:43-50`). | The reported raw-only gap is verified on clean `main` at revision `ee1e67e`. |
| Confirmed repository fact | The current WorkItem uses `relProject`, `dueDate`, `dateCommitted`, `dateStart`, and `dateClosed`; it extracts text for selected HTML fields and omits `Scope` and `Requirements` (`src/workboard_cli/normalize.py:180-209`; `docs/agent_json_contract.md:111-142`). | The issue's example spellings and field coverage do not match the current projection exactly. |
| Confirmed repository fact | Repository configuration maps `Scope` and `Requirements`, and discovery recorded them as WorkBoard fields (`config/workboard.defaults.yaml:18-44`; `MEMORY.md:34-40`). | Their semantic inclusion is grounded, but their live value and empty-value shapes were not re-discovered in this brainstorm. |
| Confirmed repository fact | Existing WorkItem evolution is additive-only (`docs/plans/2026-08-19-001-feat-cli-evolution-sharepoint-shape-plan.md:26-45`, especially AE8; `docs/plans/2026-08-19-001-feat-cli-evolution-sharepoint-shape-plan.md:565-575`). | Any change to WorkItem must preserve existing keys, types, and meanings. |
| Confirmed repository fact | The current contract says `workboard agent query` is the only agent-facing interface (`docs/agent_json_contract.md:1-6`; `src/workboard_cli/agent.py:22-44`). | `items get` remains a general automation-friendly CLI command and does not expand `APPROVED_INTENTS`. |
| Issue-requested behavior | GitHub issue #6 asks for stable normalized single-item output, raw-field availability, canonical capture fields, and machine-readable linked-project data. | The outcome is delivered through existing WorkItem conventions rather than new aliases copied from the issue examples. |
| Session-settled decision | Adopt WorkItem as the single authoritative normalized item contract and reject a second curated schema. (session-settled: 2026-08-21; reaffirmed: 2026-08-22) | Extend WorkItem additively, expose it at `result.workItem` beside unchanged raw `result.item` for primary WorkBoard retrievals, and propagate additive fields to existing normalized WorkItem surfaces. |
| Session-settled decision | Primary WorkBoard retrievals keep raw data at `result.item` and add WorkItem at `result.workItem` automatically; custom-list retrievals remain raw-only. (session-settled: 2026-08-22) | No opt-in flag is introduced, and existing envelope metadata and not-found behavior remain unchanged. |
| Session-settled decision | WorkItem names remain lower-camelCase, keep only `relProject`, and add `scopeText` and `requirementsText` without aliases. Operational dates remain `dueDate`, `dateStart`, `dateCommitted`, and `dateClosed`. (session-settled: 2026-08-22) | Issue-example casing, `linkedProject`, `scope`, `requirements`, and alternative date aliases are excluded. |
| Session-settled decision | Documented WorkItem keys are always present with category-specific absence sentinels; exceptional absence and malformed content also emit warnings. (session-settled: 2026-08-22) | Raw `result.item` remains the audit source, and malformed content never becomes authoritative normalized output. |
| Session-settled decision | Keep only `sourceUrl` and `workBriefLinks` for link capture; do not introduce `relatedLinks` or a generic taxonomy. (session-settled: 2026-08-22) | Other long-form links remain follow-up, and invalid work-brief entries are warned and omitted from WorkItem. |
| Session-settled decision | `items get` remains outside the approved agent interface. (session-settled: 2026-08-22) | Official AI-agent access remains validated `agent query` intents; conflicting OpenCode routing is deferred contract drift. |
| Assumption | Primary direct consumers are AI agents and downstream capture/wiki automation; delivery leads and managers benefit indirectly from more reliable records. | No usage telemetry or user interview evidence was provided, so success is stated behaviorally rather than as an adoption metric. |

### Actors

- A1. **Automation consumer:** An AI agent or capture process that needs a stable, machine-readable representation of one WorkBoard item.
- A2. **Operator or reviewer:** A person who needs normalized output to remain traceable to the exact SharePoint source values.
- A3. **SharePoint WorkBoard:** The authoritative source system; it supplies item data but is never mutated by this workflow.

### Desired Outcome and Value

An A1 consumer can capture the operational meaning of one item without custom parsing for every raw HTML, lookup, person, or date field.
An A2 reviewer can trace normalized values back to the raw item and see warnings where normalization is incomplete.
The organization gains a reusable item-level contract that does not assume every item belongs to a project and does not manufacture acceptance or closure state absent from SharePoint.

### Candidate Directions

1. **Rejected — curated item-capture projection.** A purpose-built second normalized schema would isolate single-item capture but duplicate WorkItem semantics, documentation, and tests, creating an avoidable drift surface.
2. **Selected — extend the existing WorkItem contract.** (session-settled: 2026-08-21; reaffirmed: 2026-08-22) Add the missing capture semantics to WorkItem and expose that authoritative representation alongside the unchanged raw Graph item. Reusing `normalize.py`, the documented WorkItem contract, and existing normalization tests reduces semantic and documentation drift; additive fields will also propagate to existing normalized list, query, and intent surfaces.

Q1 is settled in favor of direction 2. A raw-only documentation change is not viable because it would leave every downstream consumer responsible for the parsing problem described by the issue.
Q2-Q7 settle the contract within direction 2: fixed response locations, existing WorkItem naming and date conventions, explicit absence and warning semantics, the existing focused link fields, and no expansion of the approved agent interface.

### Requirements

**Source fidelity and compatibility**

- R1. Every successful `items get` request for the configured primary WorkBoard list must preserve the unchanged raw Graph item at `result.item` and automatically add the authoritative WorkItem at `result.workItem` without an opt-in flag.
- R2. WorkItem must remain the single authoritative normalized item contract, with missing capture semantics added without changing current keys, types, or meanings; additive fields propagate to existing normalized list, query, and intent surfaces without changing their behavior.
- R3. The command must remain read-only against SharePoint, require no SharePoint schema change, and preserve `status`, `source`, `retrievedAt`, and `sessionId`.

**Canonical names and item capture**

- R4. WorkItem properties must use lower-camelCase, with missing HTML-free long-form capture added only as `scopeText` and `requirementsText`; parallel `scope` and `requirements` aliases must not be emitted.
- R5. `relProject` must remain the sole normalized project association with shape `{id: int, text: string} | null`; `linkedProject` and other project aliases must not be emitted.
- R6. Documented WorkItem keys must never be omitted, and genuine absence must use `""` for canonical text, `null` for nullable scalar, object, person, project, date, and `sourceUrl` values, and `[]` for link arrays without a warning.

**Human-readable text and links**

- R7. WorkItem long-form text fields, including `scopeText` and `requirementsText`, must be HTML-free while the unchanged raw Graph item retains the original source content for audit.
- R8. Link capture must use only `sourceUrl: string | null` for the item display URL and `workBriefLinks: Array<{url: string, text: string}>` for decoded absolute HTTP(S) links from `RelWorkBrief` anchors; `relatedLinks` and generic link taxonomies must not be introduced.

**State integrity and diagnostics**

- R9. Acceptance and closure information must reflect source data only. The contract must not invent accepted, complete, closed, or similar state from dates, stage text, authorities, criteria, or deliverables.
- R10. Required absent values, demonstrably unavailable configured mappings, and malformed or un-normalizable values must use the category sentinel plus a normalization warning; malformed content must never become authoritative normalized output, and raw `result.item` remains the audit source.
- R11. An item that does not exist must continue to produce the repository's structured not-found error behavior rather than a partial normalized item (`src/workboard_cli/graph_client.py:22-40`; `src/workboard_cli/cli.py:73-78`).

**Command and compatibility edge cases**

- R12. Every successful `items get` request for a non-WorkBoard or custom list must retain the existing raw-only `result.item` and omit `result.workItem`.
- R13. Canonical operational dates must remain only `dueDate`, `dateStart`, `dateCommitted`, and `dateClosed`; no SharePoint-style or alternative aliases may be added, and existing `createdDate` and `modifiedDate` remain unchanged.
- R14. `items get` must remain a general read-only CLI command with automation-friendly JSON, must not become an approved agent-facing interface, and must not add or change `APPROVED_INTENTS`; official AI-agent access remains `workboard agent query --intent <name>`.
- R15. A valid legacy person-name string must normalize to `{displayName: <source name>, email: null, id: null}` without a warning.
- R16. `workBriefLinks` must always be an array: missing or empty source yields `[]` without warning, while invalid entries are omitted with a normalization warning and remain auditable in raw fields.

### Success Criteria

- Primary WorkBoard retrievals return unchanged raw data at `result.item` plus WorkItem at `result.workItem` automatically, while successful custom-list retrievals remain raw-only.
- WorkItem remains the only normalized item contract, uses the settled names and date keys, and contains every documented key with the settled category sentinel.
- Reviewers can audit normalized values against unchanged raw content, and every exceptional absence or malformed value produces a warning without becoming authoritative output.
- Link capture remains limited to `sourceUrl` and `workBriefLinks`, with stable empty-array and invalid-entry behavior.
- No acceptance or closure state is invented, and `items get` does not expand the approved agent interface.
- Existing normalized WorkItem surfaces receive additive fields without changing list, query, summary, or intent behavior.
- A planner can trace every expected behavior to an R-ID and AE-ID without inventing product-contract choices.

### Acceptance Examples

| ID | Scenario and expected outcome | Covers |
|---|---|---|
| AE1 | A successful get from the configured primary WorkBoard list returns the unchanged Graph item at `result.item` and WorkItem at `result.workItem` without a flag, while preserving `status`, `source`, `retrievedAt`, and `sessionId`. | R1, R3 |
| AE2 | A successful get from a non-WorkBoard or custom list returns only raw `result.item` and omits `result.workItem`. | R12 |
| AE3 | A valid `RelProject` value becomes only `relProject: {id: 3, text: "Retirement System"}`; no `linkedProject` alias appears. | R5 |
| AE4 | A genuinely absent project produces `relProject: null` without warning; malformed project content produces `relProject: null` plus a warning and remains in raw `result.item`. | R5, R6, R10 |
| AE5 | Populated SharePoint `Scope` and `Requirements` content becomes HTML-free `scopeText` and `requirementsText`; no parallel `scope` or `requirements` aliases appear. | R4, R7 |
| AE6 | HTML in any normalized long-form field is removed from the WorkItem text value while the original markup remains unchanged in raw `result.item`. | R7, R10 |
| AE7 | A valid legacy person string such as `"Example Person"` becomes `{displayName: "Example Person", email: null, id: null}` without warning. | R15 |
| AE8 | Operational dates appear only as `dueDate`, `dateStart`, `dateCommitted`, and `dateClosed`; `createdDate` and `modifiedDate` remain unchanged, and no aliases or inferred closure status appear. | R9, R13 |
| AE9 | Acceptance criteria and deliverables remain individually capturable as HTML-free WorkItem text while their original source remains in raw `result.item`. | R7 |
| AE10 | A valid item display URL appears only in `sourceUrl`, and valid `RelWorkBrief` anchors become decoded absolute HTTP(S) entries in `workBriefLinks`; no `relatedLinks` appears. | R8 |
| AE11 | Missing or empty `RelWorkBrief` yields `workBriefLinks: []` without warning; invalid entries are omitted with a warning and remain auditable in raw fields. | R10, R16 |
| AE12 | A request for a nonexistent item returns the existing structured resource-not-found error without a synthetic `result.item` or `result.workItem`. | R11 |
| AE13 | Criteria, deliverables, authorities, dates, or stage text without explicit acceptance or closure state do not produce invented state. | R9 |
| AE14 | A WorkItem with genuinely absent optional values still contains every documented key with `""`, `null`, or `[]` according to category and no absence warning. | R6 |
| AE15 | A required absent value, unavailable configured mapping, or malformed value uses its category sentinel, emits a normalization warning, and never presents malformed content as authoritative WorkItem data. | R10 |
| AE16 | `items get` remains outside `APPROVED_INTENTS`, and official agent calls continue through validated `workboard agent query --intent <name>`. | R14 |
| AE17 | Existing normalized list, query, and intent outputs receive the additive WorkItem fields without changes to their filtering, routing, or command behavior. | R2 |

### Scope Boundaries

**In scope**

- The settled raw-plus-WorkItem response contract for primary WorkBoard retrievals and raw-only compatibility for non-WorkBoard or custom-list retrievals.
- Additive WorkItem fields and the settled lower-camelCase names, operational dates, category sentinels, warning behavior, project association, and focused link fields.
- Raw fidelity, HTML-free normalized text, source metadata, backward compatibility, and item-not-found behavior.
- Additive field propagation to existing normalized list, query, and intent outputs without behavioral changes.

**Out of scope or follow-up**

- Fixing the command's currently ignored `--format` behavior (`src/workboard_cli/cli.py:313-341`).
- Broad hardening for malformed or unexpected Microsoft Graph payloads beyond item-level normalization warnings.
- A WorkItem v2 or general contract-versioning system; the settled decision extends the current WorkItem additively.
- `linkedProject`, `scope`, `requirements`, SharePoint-style date aliases, alternative date aliases, `relatedLinks`, or any other parallel normalized aliases.
- A generic link taxonomy or extraction of links from long-form fields other than `RelWorkBrief`; those links remain follow-up.
- Changing `items list`, query, summary, or intent behavior, or designing separate projections for them. Existing surfaces that already serialize WorkItem will inherit additive fields as a consequence of the settled contract; further behavior changes require separate approval.
- Adding an approved intent, changing `APPROVED_INTENTS`, or declaring `items get` an approved agent interface.
- Reconciling `.opencode/agents/workboard.md` routing that sends single-item requests directly to `items get`; this is separate contract drift.
- Creating acceptance or closure state not present in source data; adjacent item-level state work should be handled separately.
- Normalizing arbitrary non-WorkBoard lists selected through `--list`.
- SharePoint writes, SharePoint schema changes, new permissions, credential access, or secrets.

### Risks

| Risk | Product impact | Contract response |
|---|---|---|
| Cross-surface propagation | Additive WorkItem fields will appear in existing normalized list, query, and intent outputs even though issue #6 targets single-item capture. | Accept field propagation as a consequence of one authoritative contract, preserve additive semantics, and require separate approval for behavioral changes. |
| Sentinel ambiguity | Consumers could confuse genuine absence with exceptional absence or malformed source values. | Keep category sentinels stable and require warnings only for required, unavailable-mapping, or malformed cases. |
| Fidelity loss | HTML-to-text conversion can discard structure or link context. | Require separate raw preservation and readable text under R1 and R7. |
| False state | Consumers may interpret dates or populated criteria as accepted or closed. | Prohibit invented state under R9 and cover the edge cases in AE8 and AE13. |
| Link loss | Invalid work-brief links are omitted from WorkItem and could be missed by automation. | Emit a warning and preserve the unchanged raw source for audit. |
| Routing drift | OpenCode routing sends single-item agent requests to a command that is not an approved agent-facing interface. | Record the conflict as follow-up and keep issue #6 from changing `APPROVED_INTENTS`. |

### Dependencies and Assumptions

- The repository evidence was read from clean `main` at revision `ee1e67e` on 2026-08-21.
- The issue title, body, and current open state were read successfully on 2026-08-21 via authenticated, read-only GitHub CLI at [GitHub issue #6](https://github.com/adventistasia/itworkboard-cli/issues/6).
- The Q2-Q7 contract decision pass was supplied and session-settled on 2026-08-22; Q1 was preserved from 2026-08-21 and reaffirmed as part of the complete contract.
- SharePoint schema and sample data were not queried during this requirements update. Field existence is grounded in committed discovery records and configuration; the settled sentinel and warning rules govern current and future live value distributions (`MEMORY.md:34-40`; `config/workboard.defaults.yaml:18-44`).
- The configured primary WorkBoard list is the only list that receives `result.workItem`; successful non-WorkBoard and custom-list retrievals remain raw-only.
- Source metadata means the existing SharePoint source identity, retrieval timestamp, and CLI session identity; this plan does not introduce a new provenance system.

### Session-Settled Decisions

1. **Q1 — Projection ownership:** Adopt the existing WorkItem contract as the single authoritative normalized item contract, extend it additively, and expose it alongside the unchanged raw Graph item returned by `items get`. Do not create a second curated normalized schema. (session-settled: 2026-08-21; reaffirmed 2026-08-22 — chosen over a curated item-capture projection because `normalize.py`, WorkItem documentation, and existing tests already own normalization, reducing semantic and documentation drift.)
2. **Q2 — Raw and normalized placement:** For every successful `items get` targeting the configured primary WorkBoard list, preserve the unchanged raw Graph item at `result.item` and automatically add WorkItem at `result.workItem` without an opt-in flag. Successful non-WorkBoard and custom-list retrievals retain raw-only `result.item` and omit `result.workItem`; existing envelope metadata and not-found behavior remain unchanged. (session-settled: 2026-08-22)
3. **Q3 — Property casing and project naming:** Use lower-camelCase WorkItem properties, keep `relProject` as the sole project association with `{id: int, text: string} | null`, and add only HTML-free `scopeText` and `requirementsText`; do not emit `linkedProject`, `scope`, `requirements`, or other aliases. (session-settled: 2026-08-22)
4. **Q4 — Date names:** Keep only `dueDate`, `dateStart`, `dateCommitted`, and `dateClosed` as canonical operational dates, add no SharePoint-style or alternative aliases, and leave `createdDate` and `modifiedDate` unchanged. (session-settled: 2026-08-22)
5. **Q5 — Empty and malformed values:** Never omit documented WorkItem keys. Genuine absence uses `""` for canonical text, `null` for nullable scalar, object, person, project, date, and `sourceUrl` fields, and `[]` for link arrays without warning; required absence, unavailable configured mappings, and malformed values use the category sentinel plus a warning, never become authoritative normalized output, and remain auditable in raw `result.item`. Valid legacy person strings normalize to `{displayName, email: null, id: null}` without warning. (session-settled: 2026-08-22)
6. **Q6 — Links:** Do not introduce `relatedLinks` or a generic taxonomy. Keep `sourceUrl: string | null` and `workBriefLinks: Array<{url: string, text: string}>`; missing or empty `RelWorkBrief` yields `[]` without warning, invalid entries are omitted with a warning and remain raw-auditable, and links in other long-form fields remain follow-up. (session-settled: 2026-08-22)
7. **Q7 — Agent interface:** Keep `items get` as a general read-only CLI command with automation-friendly JSON, not an approved agent-facing interface. Do not add an approved intent or change `APPROVED_INTENTS`; official agent access remains validated `agent query`, and conflicting `.opencode/agents/workboard.md` single-item routing is separate drift to reconcile later. (session-settled: 2026-08-22)

#### Deferred to Planning

None. Q1-Q7 are session-settled, and no unresolved product-contract decisions remain.

### How This Work Fits the Strategy

This work advances the Agent Query Layer and Output & Summaries tracks by making a primary operational record available as structured JSON for automation (`STRATEGY.md:11-31`).
It keeps SharePoint as the system of record, preserves the read-only boundary, and avoids generic Graph browsing or mutation (`STRATEGY.md:33-35`; `docs/architecture.md:67-79`).
It strengthens the additive WorkItem evolution already established by the SharePoint-shape plan by making WorkItem the single authoritative normalized item contract. Existing normalized WorkItem surfaces inherit additive fields, while changes to their behavior remain outside this plan.

### Sources / Research

- [GitHub issue #6](https://github.com/adventistasia/itworkboard-cli/issues/6) — issue body and current open state read successfully on 2026-08-21 via authenticated, read-only GitHub CLI.
- GPT-5.6-sol Q2-Q7 recommendations supplied in session — contract decision pass observed and session-settled on 2026-08-22.
- `AGENTS.md:1-25` — repository purpose and non-negotiable read-only, source-metadata, approved-intent, schema-discovery, and secret-handling constraints.
- `STRATEGY.md:7-35` — target problem, structured JSON positioning, users, product tracks, and SharePoint write boundary.
- `CONCEPTS.md:1-12` — current canonical glossary; it contains no settled item-capture term to reuse or amend.
- `MEMORY.md:34-40` — discovery evidence for WorkBoard columns, including project, authority, date, scope, requirements, acceptance, and deliverable fields.
- `docs/plans/2026-08-19-001-feat-cli-evolution-sharepoint-shape-plan.md:26-45` and `docs/plans/2026-08-19-001-feat-cli-evolution-sharepoint-shape-plan.md:565-575` — prior field-shape acceptance examples and additive WorkItem compatibility constraint.
- `src/workboard_cli/cli.py:289-341` — current list normalization option and raw-only single-item command behavior.
- `src/workboard_cli/sharepoint.py:31-50` — Graph list-item retrieval shapes.
- `src/workboard_cli/normalize.py:65-105` and `src/workboard_cli/normalize.py:142-214` — current project parsing, HTML text extraction, normalized names, omissions, raw passthrough, and warnings.
- `tests/test_normalize.py:71-130`, `tests/test_normalize.py:215-280`, and `tests/test_normalize.py:300-331` — tested normalized field, raw fidelity, linked-project, HTML text, description, owner, and lookup behavior.
- `docs/agent_json_contract.md:1-6` and `docs/agent_json_contract.md:64-142` — current agent-interface boundary and documented WorkItem contract.
- `src/workboard_cli/agent.py:22-44` — approved-intent allowlist and refusal behavior preserved by Q7.
- `.opencode/agents/workboard.md:38-49` and `.opencode/agents/workboard.md:243-244` — separate routing that sends single-item requests to `items get`, recorded as follow-up contract drift.
- `docs/agent-instructions/field-mapping.md:1-49` — config-driven normalization rules and schema discovery requirements.
- `config/workboard.defaults.yaml:18-44` — committed field mapping, including currently unmapped-in-output `Scope` and `Requirements`.
- `src/workboard_cli/graph_client.py:22-40` and `tests/test_graph_client.py:40-45` — current structured not-found behavior.
