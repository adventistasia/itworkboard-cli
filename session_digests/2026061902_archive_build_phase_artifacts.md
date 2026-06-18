---
lorespec: "0.1"
id: "2026061902"
date: "2026-06-19"
source: "opencode"
topic: "Archive build-phase artifacts and transition to maintenance mode"
tags: [archive, maintenance, build-phase, cleanup, project-transition]
classification:
  type: reflective
  secondary_type: operational
  domains: [project-management, maintenance]
  value: medium
trails: [project-transition, build-phase-artifacts]
---

## Session Arc

### Started
User requested archiving of files used during the CLI building phase now that the project has shifted to maintenance.

### Pivots
- User rejected initial broad proposal — most proposed items (scripts/, build/, templates/) were still needed. Narrowed to orchestrator/build-prompt files only.
- Iterative refinement: user added briefs/, audit_briefs/, contracts/, samples/, discovery/, prerequisites/ to archive one by one.
- sources.md recognized as a reference doc, not a build artifact — renamed and moved to docs/.
- manifest.json identified as a pure build orchestrator artifact and archived.

### Ended
Clean project root with build-phase planning/execution artifacts consolidated under archive/. Remaining docs (MEMORY.md, STRATEGY.md, session_digests/) flagged for content updates.

## Knowledge Objects

### DECISIONS

#### D1: Archive only orchestrator/build-prompt files, not broader project files
- **Issue**: Which files are build-phase artifacts vs maintenance-phase essentials?
- **Positions**: (1) Archive scripts/, build/, templates/ as build artifacts. (2) Keep them — build outputs and utility scripts remain useful during maintenance.
- **Arguments**: User confirmed that scripts/, build/, templates/ serve ongoing maintenance needs — build artifacts include compiled output and helper scripts, not just planning docs.
- **Warrant**: A file's creation context (build phase) doesn't determine its ongoing value. Utility and reference files retain value regardless of when they were created.
- **Qualifier**: settled
- **Status**: settled

#### D2: Rename sources.md to docs/graph-api-references.md
- **Issue**: What to do with a build-phase reference doc listing Graph API links?
- **Positions**: (1) Archive it with other build artifacts. (2) Keep it in docs/ with an updated name.
- **Arguments**: The content is a durable reference of official Microsoft Graph API documentation links — useful for future maintenance. Only the title and intro were build-phase language.
- **Warrant**: Reference documents should be organized by content topic (Graph API references), not by originating phase (build sources).
- **Qualifier**: always
- **Status**: settled

#### D3: Archive manifest.json, keep MEMORY.md and session_digests/ for content updates
- **Issue**: What to do with remaining build-phase metadata files?
- **Positions**: (1) Archive all three. (2) Archive manifest.json only, update the others.
- **Arguments**: manifest.json is a pure orchestrator execution artifact referencing now-archived briefs. MEMORY.md and session_digests/ contain durable decisions and records that should be refactored into maintenance-relevant docs rather than archived away.
- **Warrant**: The cost of updating a doc is lower than the cost of losing decision history. MEMORY.md captures architecture decisions that remain in effect; session records preserve context.
- **Qualifier**: tentatively
- **Status**: settled

### INSIGHTS

#### I1: Build-phase artifacts cluster into two categories — planning/execution (archive-worthy) and reference/utility (keep-worthy)
Planning artifacts: orchestrator prompts, task briefs, audit docs, design contracts, discovery outputs, sample outputs, completion reports. Keep-worthy: build outputs, scripts, templates, strategy docs, reference docs, source code, tests. The line is drawn by whether the file informs future work vs only describes completed work.

#### I2: sources.md was misclassified as a build artifact by initial analysis
The title and intro used build-phase language, but the core content (Graph API reference URLs) is a durable maintenance resource. The correct action was relocate and rename, not archive.

### PATTERNS

#### P1: Post-delivery artifact triage
**Scope**: Universal
**Steps**:
1. List all non-source-code files in the project root and docs/ directories.
2. Classify each as: (a) planning/execution artifact, (b) durable reference, or (c) active maintenance file.
3. Archive (a) items under archive/ organized by original path.
4. Relocate and rename (b) items into docs/ with content-topic names.
5. Flag (c) items that need content updates to remove build-phase language.
6. Verify nothing in archive/ is referenced by source code, CI config, or agent instructions.

## Connections
- P1 —[instance_of]→ I1
- D1 —[informed_by]→ I1
- D2 —[informed_by]→ I2
- D2 —[instance_of]→ P1
