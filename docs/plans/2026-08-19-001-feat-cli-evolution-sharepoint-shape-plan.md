---
title: WorkBoard CLI Evolution for SharePoint Shape - Plan
date: 2026-08-19
type: feat
topic: cli-evolution-sharepoint-shape
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: ce-brainstorm
execution: code
deepened: 2026-08-19
---

# WorkBoard CLI Evolution for SharePoint Shape - Plan

## Goal Capsule

- **Objective:** Evolve the IT WorkBoard CLI's data layer to surface what the new SharePoint shape reveals (unrecognized stages, JSON/HTML blobs, calculated fields with anomalies, unexpanded lookups), add analytics intents that depend on those improvements, and ship a schema-drift detection command that tracks changes across WorkBoard, Deliverables, Tasks, WorkIntake, WorkReview, and Users lists so future SharePoint-side changes are visible at the CLI boundary.
- **Product authority:** This plan owns one coherent work unit covering field handling, new analytics intents, and schema-drift detection across all work-related lists (WorkBoard, Deliverables, Tasks, WorkIntake, WorkReview, Users). Adjacent areas — write operations, embedding-based intent routing, web dashboard, cross-list joins — remain contextual candidates and are not active scope. Schema-drift auto-correction (closing the loop by opening PRs) is already covered by the observations self-improvement roadmap (`docs/roadmaps/observations-self-improvement.md` Phase 3.3) and is referenced as related work, not duplicated here.
- **Execution profile:** Software feature work, Python/Typer. Read-only against SharePoint.
- **Open blockers:** None.

## Plan self-containment note

This plan is self-contained: it does not depend on a separate requirements document. Requirement IDs (R#), key-decision IDs (KD#), field IDs (F#), and acceptance-example IDs (AE#) referenced throughout are defined inline — R1–R19 and R22–R24 are covered by Implementation Units U1–U14 below (see each unit's "Covers" line), F1–F6 are the field-handling goals covered by U1–U6, and AE1–AE8 are reconstructed from the unit test scenarios and enumerated in full in "Acceptance Examples" below. KD6 (stdlib-only HTML parsing, no third-party dependency) is stated at U4. R20, R21, and KD1–KD5/KD7 belong to adjacent scope this plan explicitly excludes (write operations, embedding-based intent routing, web dashboard, cross-list joins — see Goal Capsule) and are not implemented here. The deferred-to-planning questions are resolved inline at the top of the Implementation Units section.

## Acceptance Examples

- **AE1:** Item with `Stage: "Tabled"` → `stageCategory: "closed"`, raw stage preserved under `raw.Stage`. (covers U1)
- **AE2:** Item with `CycleTime: "-46,113"` → `cycleTimeDays: null`, `cycleTimeAnomaly: true`, a warning is emitted. (covers U2)
- **AE3:** Item with `RelProject: '{"id":3,"text":"Retirement System"}'` → `relProject` parsed to `{"id": 3, "text": "Retirement System"}`; malformed JSON → `relProject: null` plus a warning. (covers U3)
- **AE4:** Item with `RelWorkBrief` HTML containing an entity-encoded `href` → `workBriefLinks` with decoded, absolute URLs. (covers U4)
- **AE5:** `cycle_time_stats` returns `median_days`, `p95_days`, `count`, `bogus_count`; anomalous items are excluded from the stats and tallied under `bogus_count`. (covers U9)
- **AE6:** `workboard schema drift` on first run (no baseline present) writes the baseline and exits 0; on subsequent runs with drift present, it prints a drift report and exits 6 if any entry is high severity. (covers U13)
- **AE7:** Item with a `DeliveryOwner` lookup → `deliveryOwner` object with `displayName`, `email`, `id`. (covers U6)
- **AE8:** All existing WorkItem keys (`id`, `title`, `stage`, `deliveryOwner.displayName`, `dueDate`, `stageCategory`, `sourceUrl`, `raw`, `warnings`) remain present and unchanged in type/meaning — new fields are additive only. (covers U22/R22)

## Deferred-Question Resolutions

The five open questions raised at the requirements stage are resolved here so the implementation units below have unambiguous direction:

- **DQ1 — Parser module location.** Helpers (`_parse_rel_project`, `_parse_work_brief`, `_extract_long_form_text`, `_coerce_cycle_time`, `_expand_person_lookup`, `_expand_work_intake`) live inside `src/workboard_cli/normalize.py` rather than a new `parsers.py` module. *Rationale:* normalize.py is small (94 lines) and these helpers are normalization helpers; a separate module would split one responsibility (raw → WorkItem) across two files. If a parser is later reused by something other than normalization, it can move without breaking callers.
- **DQ2 — Config keys for parsers.** No new top-level config block is introduced. The `stage_aliases` block is extended for the five new stages (R1–R3). The new field handling (R7–R10) is automatic at normalize time based on detected shape — no per-field config needed because SharePoint stores these as plain `text` columns whose content we discover from live data. The `output.include_raw_fields` flag (already present) is reused for `raw.*` fidelity.
- **DQ3 — `cycle_time_stats` grouping filter.** Single intent with a `--group-by owner|stage` flag (default `owner`). Two separate intents would inflate the approved-intent surface from 12 to 13 without adding capability. A flag keeps the dispatch trivial and matches the pattern already used by `items_by_owner` (`--owner` filter) and `recently_updated_items` (`--days` filter).
- **DQ4 — Schema-drift baseline location.** `discovery/workboard_schema.baseline.json` (same path used by today's `schema export`). Keeps all schema-related artifacts in one place and avoids introducing a `.workboard/` dotfile directory in this release.
- **DQ5 — `workBriefLinks` URL form.** Absolute, resolved against the configured `site_url` (AE4). The `<a href>` values in the wild are relative paths like `/:w:/r/sites/itdocumentcontrol/...`; resolving them to absolute URLs makes agents usable without knowing SharePoint URL semantics.

## Sequencing & Dependencies

The implementation is grouped into four phases. Phases 2–4 can overlap partially, but each unit names its own dependencies so the order is unambiguous.

**Phase A — Field handling (foundation).** All WorkItem-shape changes land here. Units U1–U6.
**Phase B — New agent intents.** Six new intents that build on the normalized shape. Units U7–U12.
**Phase C — Schema drift detection.** Standalone command, depends on the existing `schema export` machinery. Unit U13.
**Phase D — Docs + contract surface.** WorkItem contract, CLI contract, intent list updates. Unit U14.

Sequencing diagram (mixes true data dependencies with sequencing-only/hygiene ordering — see legend):

```
Legend: ──►  data dependency (consumer needs the producer's output)
        ···► sequencing-only / review-hygiene ordering (no data dependency)

U1 stage aliases ─────┐
                      ├─► U7  new_items
U2 cycle time    ─────┼─► U9  cycle_time_stats
U3 RelProject    ─────┼─► U10 items_by_project
U4 RelWorkBrief + text──┘    (text not directly needed; HTML is)
U5 Description/PriorityStatus (no downstream dependents; standalone additive)
U6 lookup expansion ─────┬─► U12 items_by_decision_authority
                         ├···► U11 items_by_stage (no data dep on U6; sequenced after purely for review hygiene — both touch lookup/filter code paths)
                         └─► U8  recently_completed_items
U13 schema drift  ────── (no dep on U1–U12; standalone)
U14 docs + contract ──── depends on U1–U13 (last)
```

Note: within Phase A/B, U4→U7 and U6→U8 in the unit-numbering order are sequencing choices (grouping related file edits together for review), not data dependencies — the arrows above are the authoritative dependency list; unit numbering itself does not imply dependency.

## Implementation Units

Each unit lists the requirements it covers, the files it touches, the approach (with directional guidance, not code), patterns to follow, and enumerated test scenarios. Test scenarios reference the Acceptance Examples (AE#) in the Product Contract where applicable.

### U1. Extend stage aliases for the five new stages

**Goal:** Items whose raw `Stage` is `Tabled`, `Canceled`, `Definition`, `New`, or `Delivery` receive a non-`unknown` `stageCategory` consistent with their lifecycle position. Existing stages continue to map the same way they do today (regression-free).

**Covers:** R1, R2, R3, F1, AE1

**Files:**
- `config/workboard.defaults.yaml` (modify — extend `stage_aliases`)
- `src/workboard_cli/normalize.py` (no code change expected — `_get_stage_category` already iterates aliases; verify behavior)
- `tests/test_normalize.py` (extend — add test cases for the five new stages)

**Approach:**
- Update the `stage_aliases` block in `workboard.defaults.yaml`:
  - `open:` — add `"New"` (already present), `"Definition"` (new), and `"Delivery"` (new — an active, in-flight stage, so it maps to `open` rather than `closed`).
  - `closed:` — add `"Canceled"` (new, American spelling). Note the config already has `"Cancelled"` (British spelling) under `closed`; live data uses the American spelling `"Canceled"`, so both are kept as separate aliases rather than normalizing one away, so neither historical nor live-shape values fall through to `unknown`. Also add `"Tabled"` (new).
  - Note: `"New"` already exists under `open` in the current defaults, so the net adds are `"Definition"` and `"Delivery"` under `open`, and `"Canceled"` and `"Tabled"` under `closed`. Verify before editing.
- No code change in `_get_stage_category` is expected: the function is already a flat lookup over the alias list. After the config edit, items with these stage values will resolve to `open` or `closed` automatically.
- Regression check: existing test `_get_stage_category("Open")` and the other tests in `test_normalize.py` must continue to pass.

**Patterns to follow:**
- Alias iteration pattern in `_get_stage_category` (normalize.py:42–50).
- Existing config structure in `workboard.defaults.yaml` lines 41–53.

**Test scenarios:**
- After config update, `normalize_item` on an item with `Stage: "Tabled"` returns `stageCategory: "closed"` (covers AE1).
- `Stage: "Canceled"` → `stageCategory: "closed"`.
- `Stage: "Cancelled"` (existing British spelling) → `stageCategory: "closed"` (regression check).
- `Stage: "Definition"` → `stageCategory: "open"`.
- `Stage: "Delivery"` → `stageCategory: "open"`.
- `Stage: "New"` → `stageCategory: "open"` (regression check — was already mapped, but re-assert after config update).
- `_get_stage_category("Tabled", stage_aliases)` returns `"closed"`.
- `byStageCategory.unknown` count drops to zero for the live data shape (sample with one item per stage, confirm no item lands in `unknown`).
- All existing `test_normalize.py` tests pass with no behavioral change for previously-covered stages.

**Verification:** `pytest tests/test_normalize.py` green; manual: run `workboard summary manager` against live data, confirm `byStageCategory.unknown` count is 0 (it was ~16 of 43 items in the discovery report).

### U2. CycleTime coercion with anomaly warnings

**Goal:** The raw SharePoint `CycleTime` string becomes a typed integer (`cycleTimeDays`) when valid, and an explicit anomaly flag + warning when invalid. Raw value is preserved under `raw.CycleTime` when `include_raw_fields` is on.

**Covers:** R4, R5, R6, F3, AE2

**Files:**
- `src/workboard_cli/normalize.py` (modify — add `_coerce_cycle_time`, add new keys to WorkItem dict)
- `config/workboard.defaults.yaml` (no change — `cycle_time` mapping already exists at line 34)
- `tests/test_normalize.py` (extend)

**Approach:**
- Add `_coerce_cycle_time(raw_value, warnings) -> {"cycleTimeDays": <int|None>, "cycleTimeAnomaly": <bool>}` helper. It must:
  - Return `cycleTimeDays=None, cycleTimeAnomaly=False` when raw is `None` or empty string (legitimate "not yet measured").
  - Strip commas (the wild values look like `"-46,113"`), call `int(...)` inside try/except. On `ValueError` or negative result: append a warning `"CycleTime value '<raw>' is anomalous (non-integer or negative)"`, return `cycleTimeDays=None, cycleTimeAnomaly=True`.
  - On clean non-negative int: return `cycleTimeDays=<int>, cycleTimeAnomaly=False`.
- In `normalize_item`, after the existing date field reads, read `raw_fields.get(field_map["cycle_time"])` (handle the `_get_field` fallback to `CycleTimeLookupId` only if present; otherwise just direct read) and call the helper.
- Add `"cycleTimeDays"` and `"cycleTimeAnomaly"` to the WorkItem dict (additive — R22).
- When `output.include_raw_fields` is true, the existing `raw: raw_fields` assignment already preserves `raw.CycleTime` (R6).
- Order of warnings: append the CycleTime anomaly warning to `warnings` so it surfaces in the envelope's `warnings` array.

**Patterns to follow:**
- Helper-function placement and `_` prefix convention in normalize.py (e.g., `_parse_date`, `_parse_person`).
- Warning accumulation: existing code uses a single `warnings` list passed by reference and appended to throughout `normalize_item`.

**Test scenarios:**
- `_coerce_cycle_time("8")` returns `{"cycleTimeDays": 8, "cycleTimeAnomaly": False}`.
- `_coerce_cycle_time("-46,113")` returns `{"cycleTimeDays": None, "cycleTimeAnomaly": True}` and the warnings list contains an anomaly message referencing `"-46,113"` (covers AE2).
- `_coerce_cycle_time("not a number")` returns anomaly.
- `_coerce_cycle_time(None)` returns `{"cycleTimeDays": None, "cycleTimeAnomaly": False}` and adds no warning (legitimate "not set" — distinct from "anomalous").
- `normalize_item` on a sample item with `CycleTime: "-46,216"` produces a WorkItem whose `cycleTimeDays is None`, `cycleTimeAnomaly is True`, `warnings` contains the anomaly message, and (with `include_raw_fields=True`) `raw.CycleTime == "-46,216"`.
- A sample item with `CycleTime: "8"` produces `cycleTimeDays == 8` and `cycleTimeAnomaly is False`.

**Verification:** `pytest tests/test_normalize.py` green; manual: run `workboard items list --list WorkBoard --normalize --limit 5` and inspect the envelope's `warnings` array for CycleTime anomaly entries against live data.

### U3. RelProject JSON parsing

**Goal:** The raw `RelProject` JSON string becomes a structured `{id, text}` object; malformed JSON produces a null + warning + raw preservation.

**Covers:** R7, F2, AE3

**Files:**
- `src/workboard_cli/normalize.py` (modify — add `_parse_rel_project`, add to WorkItem)
- `tests/test_normalize.py` (extend)

**Approach:**
- Add `_parse_rel_project(raw_value, warnings) -> dict|None` helper:
  - When raw is `None` or empty string, return `None` (no warning).
  - On `json.loads` success with both `id` (int) and `text` (str), return `{"id": <int>, "text": <str>}`.
  - On `json.JSONDecodeError`, append warning `"RelProject value is not valid JSON: '<raw>'"`, return `None`.
  - On successful parse but missing/typed-wrong keys, append warning, return `None`.
- Read raw via `_get_field(raw_fields, field_map["rel_project"], warnings)`.
- Add `"relProject": <parsed or None>` to WorkItem.
- When `include_raw_fields=True`, raw preservation is automatic via the existing `raw = raw_fields` assignment.

**Patterns to follow:**
- `_parse_date`, `_parse_person` — small helpers returning structured values, appending to a passed-in warnings list.

**Test scenarios:**
- `_parse_rel_project('{"id":3,"text":"Retirement System"}')` returns `{"id": 3, "text": "Retirement System"}` (covers AE3 happy path).
- `_parse_rel_project("not json")` returns `None` and the warnings list contains `"not valid JSON"` (covers AE3 malformed path).
- `_parse_rel_project(None)` returns `None` with no warning.
- `normalize_item` on a sample with a well-formed `RelProject` produces `work_item["relProject"] == {"id": 3, "text": "Retirement System"}`.
- `normalize_item` on a sample with a malformed `RelProject` produces `work_item["relProject"] is None`, `raw.RelProject == "not json"`, and the warnings list contains the JSON-parse warning.

**Verification:** `pytest tests/test_normalize.py` green.

### U4. RelWorkBrief HTML parsing + long-form HTML plain-text extraction

**Goal:** `RelWorkBrief` HTML exposes a structured list of link targets; long-form HTML fields (`Why`, `Schedule`, `AcceptanceCriteria`, `Deliverables`) expose both raw HTML and a plain-text view.

**Covers:** R8, R9, F2, AE4

**Files:**
- `src/workboard_cli/normalize.py` (modify — add `_parse_work_brief`, `_extract_long_form_text`)
- `tests/test_normalize.py` (extend)

**Approach:**
- Add `_parse_work_brief(html, site_url, warnings) -> list[dict]`:
  - Returns `[]` when html is None/empty.
  - Use stdlib only (KD6): `html.parser.HTMLParser` (or `re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)` is simpler and sufficient for the wild shape).
  - For each match: take `href` and inner text. For inner text, strip nested tags via `_strip_tags(inner_text)` and decode entities via `html.unescape(...)`. The `href` itself is also entity-encoded (e.g. `&#58;` for `:`, `&amp;` for `&` in query strings) — decode it with `html.unescape(href)` before resolving. Resolve the decoded relative `href` against `site_url` using `urljoin(site_url, html.unescape(href))` from `urllib.parse`. (`html.unescape` matches semicolon-less legacy entities like `&amp` too, but SharePoint's own query params never collide with that shorthand form, so this is safe here.) Skip non-`http(s)` schemes and empty text. Append `{"url": <abs>, "text": <stripped>}` to the result.
  - On no matches, return `[]` (this is not an error — the HTML might just contain prose with no `<a>` tags).
- Add `_extract_long_form_text(html) -> str`:
  - Returns `""` for None/empty input.
  - Order: `html.unescape(...)` first to handle `&#58;` etc., then strip tags via regex (`<[^>]+>` → ``), collapse whitespace (`\s+` → ` `), strip.
- Wire into `normalize_item`:
  - Read `RelWorkBrief`, `Why`, `Schedule`, `AcceptanceCriteria`, `Deliverables` via `_get_field`. Add `workBriefLinks`, `whyText`, `scheduleText`, `acceptanceCriteriaText`, `deliverablesText` to the WorkItem.
  - The existing `raw` passthrough covers raw HTML fidelity (R8, R9).

**Patterns to follow:**
- Stdlib-only parsing (KD6). No `BeautifulSoup`, no `lxml`.
- `_parse_person`/`_parse_date` style: small helpers returning structured values.

**Test scenarios:**
- `_parse_work_brief('<div><a href="/&#58;w&#58;/r/sites/itdocumentcontrol/Shared%20Documents/Workboard/01%20Develop.docx?d=w08f&amp;csf=1&amp;web=1&amp;e=Lzq60F">01 Develop.docx</a></div>', "https://southernasiapacific.sharepoint.com/sites/ITWorkboard", [])` returns `[{"url": "https://southernasiapacific.sharepoint.com/:w:/r/sites/itdocumentcontrol/Shared%20Documents/Workboard/01%20Develop.docx?d=w08f&csf=1&web=1&e=Lzq60F", "text": "01 Develop.docx"}]` — note the decoded query string (`&amp;` → `&`, `&#58;` → `:`) in the expected output (covers AE4 happy path).
- `_parse_work_brief` on HTML with no `<a>` tags returns `[]`.
- `_parse_work_brief` on HTML with multiple `<a>` tags returns one entry per tag.
- Relative href starting with `/:w:/r/sites/...` resolves to `https://<site>/<path>`.
- Absolute href is passed through unchanged.
- `_extract_long_form_text('<div class="ExternalClass1ED5E4D75D7D4844945CC8352F57DB4C"><p>Outcome&#58; Finalized</p></div>')` returns `"Outcome: Finalized"` (entity decoded, tags stripped).
- `_extract_long_form_text` collapses runs of whitespace.
- `normalize_item` on a sample with populated `RelWorkBrief` produces `work_item["workBriefLinks"]` as a non-empty list and `raw.RelWorkBrief` containing the original HTML when `include_raw_fields=True`.

**Verification:** `pytest tests/test_normalize.py` green; manual: run a query against live data and confirm at least one item has populated `workBriefLinks` URLs.

### U5. Map Description and PriorityStatus onto WorkItem

**Goal:** `Description` and `PriorityStatus` are no longer silently dropped when `include_raw_fields` is off. They become first-class WorkItem fields.

**Covers:** R10, F2

**Files:**
- `config/workboard.defaults.yaml` (modify — `description` and `priority_status` are not present in the current `fields:` block; add both)
- `src/workboard_cli/normalize.py` (modify — read these fields)
- `tests/test_normalize.py` (extend)

**Approach:**
- Audit `config/workboard.defaults.yaml` for `description` and `priority_status` keys. If absent, add them (point at `Description` and `PriorityStatus` SharePoint columns).
- In `normalize_item`, read both via `_get_field` and add them as `"description"` and `"priorityStatus"` on the WorkItem.
- These are plain text fields with no parser; pass-through is sufficient.

**Patterns to follow:**
- Existing field read pattern in `normalize_item` (e.g., `why`, `who`).

**Test scenarios:**
- `normalize_item` on a sample with `Description` and `PriorityStatus` populated produces `work_item["description"]` and `work_item["priorityStatus"]` matching the raw values.
- `normalize_item` on a sample with these fields absent produces `description=None` and `priorityStatus=None` (no warnings, since these are optional).

**Verification:** `pytest tests/test_normalize.py` green.

### U6. Expand person-lookup and WorkIntake lookups to structured objects

**Goal:** `DeliveryOwner`, `DecisionAuthority`, `AcceptanceAuthority` become `{displayName, email, id}` objects (with nulls where absent); `WorkIntake` becomes `[{lookupId, lookupValue}, ...]` when present.

**Covers:** R11, R12, F4, AE7

**Files:**
- `src/workboard_cli/normalize.py` (modify — extend `_parse_person` or add `_expand_person_lookup`, add `_expand_work_intake`)
- `tests/test_normalize.py` (extend)

**Approach:**
- The current `_parse_person` already handles dict and string inputs. Extend it (or add a sibling) to:
  - When the value is a dict, return `{"displayName": <displayName|title>, "email": <email|Email>, "id": <LookupId|id>}`. This is the shape Graph returns for expanded person lookups.
  - When the value is a string (which is what the live `items_WorkBoard.json` shows — see Discovery findings), return `{"displayName": <str>, "email": None, "id": None}`.
  - When `None`, return `None`.
- Wire the three fields (`DeliveryOwner`, `DecisionAuthority`, `AcceptanceAuthority`) into `normalize_item` to produce `deliveryOwner`, `decisionAuthority`, `acceptanceAuthority` on the WorkItem.
- Add `_expand_work_intake(raw_value)` that:
  - Returns `None` when raw is None/empty.
  - When raw is a string (the live shape — see `tmp/items_WorkBoard.json`), return `[{"lookupId": None, "lookupValue": <str>}]`.
  - When raw is a list of dicts (expanded Graph shape), map each `{"LookupId", "LookupValue"}` to `{"lookupId": <id>, "lookupValue": <str>}`.
- Wire `WorkIntake` into `normalize_item` as `workIntake`.
- Note: `id` for the lookup is currently `None` in the live shape because Graph's default response carries `LookupValue` only; the `<field>LookupId` companion column may be present in some payloads. Document the limitation but do not block on it (R11 explicitly allows `id: null` when only `LookupValue` is present).

**Patterns to follow:**
- `_parse_person` (normalize.py:29–39) — extend it rather than fork.

**Test scenarios:**
- `_parse_person({"displayName": "Dennis Arquillano", "email": "dennis@ssd.org", "id": "c1520444-..."})` returns `{"displayName": "Dennis Arquillano", "email": "dennis@ssd.org", "id": "c1520444-..."}`.
- `_parse_person("Dennis Arquillano")` returns `{"displayName": "Dennis Arquillano", "email": None, "id": None}` (covers AE7 string path).
- `_parse_person(None)` returns `None`.
- `normalize_item` on a sample with `DeliveryOwner: "Dennis Arquillano"` produces `deliveryOwner == {"displayName": "Dennis Arquillano", "email": None, "id": None}`.
- `normalize_item` on a sample with `WorkIntake: "House 143 AP Installation"` produces `workIntake == [{"lookupId": None, "lookupValue": "House 143 AP Installation"}]`.
- `normalize_item` on a sample with `WorkIntake: None` produces `workIntake is None` (no warning).

**Verification:** `pytest tests/test_normalize.py` green.

### U7. New intent: `new_items` (created within last N days)

**Goal:** Agent can ask "what was added since mid-June?" and get items whose `createdDate` falls within the last N days.

**Covers:** R13 (intent name), R14 (validation + dispatch pattern), F5

**Files:**
- `src/workboard_cli/queries.py` (modify — add `filter_new_items(items, days)`)
- `src/workboard_cli/agent.py` (modify — add intent name to `APPROVED_INTENTS`, add dispatcher case, add param validation)
- `src/workboard_cli/cli.py` (modify — extend `agent_query` to accept `--days` if not already handled)
- `tests/test_queries.py` (extend)
- `tests/test_agent.py` (extend)
- `tests/test_cli.py` (extend — CLI flag test)

**Approach:**
- `filter_new_items(items, days)` in `queries.py`:
  - Reuse the date-parsing pattern from `_is_recently_updated` (queries.py:17–26), but against `createdDate` instead of `modifiedDate`.
  - Excludes items where `createdDate` is missing/unparseable.
- In `agent.py`:
  - Add `"new_items"` to `APPROVED_INTENTS`.
  - Add a validation block: when `intent == "new_items"` and `params.get("days")` is missing, raise `WorkboardError("validation_error", "The 'new_items' intent requires a --days parameter.", ...)`.
  - Add a dispatcher case that calls `filter_new_items(items, params["days"])` and falls through to `build_envelope`.
- In `cli.py`, the existing `agent_query` already accepts `--days` and forwards it to `params` (lines 478, 490–491). Verify the wiring works for `new_items`; no CLI change required if it does.

**Patterns to follow:**
- `filter_recently_updated` (queries.py:55–56) — direct copy of the date logic, swapping `modifiedDate` for `createdDate`.
- `recently_updated_items` validation in `agent.py:46–51` — exact same shape, new intent name.
- `execute_intent` dispatcher pattern (agent.py:55–67).

**Test scenarios:**
- `filter_new_items` with an item whose `createdDate` is 3 days old and `--days 7` returns the item.
- `filter_new_items` with the same item and `--days 1` returns no items.
- `filter_new_items` with an item whose `createdDate` is unparseable returns no items (excluded, not raised).
- `validate_intent("new_items")` does not raise.
- `execute_intent("new_items", items, config, {"days": 7})` returns a standard envelope with `intent == "new_items"`.
- `execute_intent("new_items", items, config, {})` raises `WorkboardError("validation_error", ...)`.
- CLI: `workboard agent query --intent new_items --days 7` succeeds (exit 0) and produces a valid envelope (covered by `test_cli.py` extension using the existing `_mock_query_patches` pattern).

**Verification:** `pytest tests/test_queries.py tests/test_agent.py tests/test_cli.py` green.

### U8. New intent: `recently_completed_items` (closed within last N days)

**Goal:** Agent can ask "what did Dennis close recently?" and get items whose `dateClosed` falls within the last N days, regardless of stage.

**Covers:** R13, R14, F5

**Files:** Same shape as U7 (queries.py + agent.py + tests).

**Approach:**
- `filter_recently_completed(items, days)` in `queries.py`:
  - Filter to items with a parseable `dateClosed` value, where `dateClosed >= now - days`.
  - Do NOT filter by `stageCategory == "closed"` — `dateClosed` presence is the canonical signal. (A `Delivery` item with a populated `DateClosed` field should still surface; today's items in `Tabled`/`Canceled` also have populated `DateClosed`.)
- Add `"recently_completed_items"` to `APPROVED_INTENTS`, add validation block, add dispatcher case — same shape as U7.

**Patterns to follow:** Same as U7.

**Test scenarios:**
- `filter_recently_completed` returns items with `dateClosed` within the window, including `Tabled`/`Canceled` items.
- `filter_recently_completed` excludes items without `dateClosed`.
- `execute_intent("recently_completed_items", items, config, {"days": 30})` returns the envelope.
- Missing `--days` raises `validation_error`.

**Verification:** Same as U7.

### U9. New intent: `cycle_time_stats` (aggregate cycle time by owner or stage)

**Goal:** Aggregated `median_days`, `p95_days`, `count`, `bogus_count` stats, with a `--group-by owner|stage` flag (default `owner`). Anomalous items excluded from `count` and the percentiles, tallied under `bogus_count`.

**Covers:** R13, R14, R15, F5, AE5

**Files:**
- `src/workboard_cli/queries.py` (modify — add `compute_cycle_time_stats(items, group_by)`)
- `src/workboard_cli/agent.py` (modify — add intent, dispatcher case, validation, optional `--group-by` flag plumbing)
- `src/workboard_cli/cli.py` (modify — accept `--group-by`)
- `tests/test_queries.py` (extend)
- `tests/test_agent.py` (extend)

**Approach:**
- `compute_cycle_time_stats(items, group_by="owner") -> dict`:
  - Iterate normalized items. For each, check `cycleTimeAnomaly`: if `True`, increment a `bogus_count` and skip the rest of the stats.
  - For valid items (`cycleTimeAnomaly == False` and `cycleTimeDays is not None`), bucket by group key:
    - `group_by == "owner"`: use `deliveryOwner.displayName` (fall back to `"Unknown"`).
    - `group_by == "stage"`: use the raw `stage` value (fall back to `"Unknown"`).
  - For each bucket, compute `median_days` (use `statistics.median`), `p95_days` (use a small helper: `sorted_values[int(0.95 * (n - 1))]` or interpolate — keep simple, sorted index is fine for n>0), `count` (length).
  - Overall envelope: also include `total_items` (all normalized items considered), `valid_count`, `bogus_count`.
  - The result goes into the summary envelope (the shape is aggregations, not a list of items — so use `build_summary_envelope`).
- `build_summary_envelope` (output.py:35–48) currently hardcodes `intent: "manager_summary"` and `filters: {}`. Parameterize it: `build_summary_envelope(summary, config, list_id=None, intent_name="manager_summary", filters=None)`. Use `intent_name` for the `"intent"` key and `filters or {}` for the `"filters"` key, preserving today's defaults so the existing `manager_summary` call site needs no change unless it wants to be explicit.
  - `manager_summary` call site in `agent.py` (line 67): pass `intent_name="manager_summary"` explicitly for clarity (behavior-preserving).
  - `cycle_time_stats` call site: `build_summary_envelope(stats, config, intent_name="cycle_time_stats", filters={"group_by": group_by})`.
- In `agent.py`:
  - Add `"cycle_time_stats"` to `APPROVED_INTENTS`.
  - Validation: `params.get("group_by")` defaults to `"owner"` when absent; reject anything other than `{"owner", "stage"}` with `validation_error`.
  - Dispatcher case: build stats → return `build_summary_envelope(stats, config, intent_name="cycle_time_stats", filters={"group_by": group_by})`. (No `target.get("id")` — there is no single-list target for this intent; `list_id` is left at its default of `None`.)
- In `cli.py`, extend `agent_query` with a new optional `--group-by` option (validated by Typer / by `execute_intent`).

**Patterns to follow:**
- `build_summary_envelope` for aggregated output (output.py:35–48).
- `manager_summary` flow in `agent.py:66–67` — same dispatcher shape.

**Test scenarios:**
- Sample of 10 items: 7 with `cycleTimeDays` in [3, 5, 7, 8, 10, 12, 15], 2 with `cycleTimeAnomaly=True`, 1 with `cycleTimeDays=None`. `compute_cycle_time_stats(items)` returns `valid_count=7, bogus_count=2, median_days=<median of 7 values>` (covers AE5 anomaly-exclusion).
- `p95_days` for the same bucket equals the 95th percentile of the 7 valid values.
- `group_by="stage"` buckets by raw stage value; `group_by="owner"` buckets by `deliveryOwner.displayName`.
- `execute_intent("cycle_time_stats", items, config)` (no `group_by` param) defaults to `owner` grouping.
- `execute_intent("cycle_time_stats", items, config, {"group_by": "month"})` raises `validation_error`.

**Verification:** `pytest tests/test_queries.py tests/test_agent.py` green; manual: run against live data and confirm the bogus_count is non-zero (the discovery data had multiple `-46,xxx` values).

### U10. New intent: `items_by_project` (filter by `relProject.text`)

**Goal:** Agent can ask "what's in the Retirement System project?" and get items whose parsed `relProject.text` matches.

**Covers:** R13, R14, F5

**Files:** Same shape as U7.

**Approach:**
- `filter_by_project(items, project_name)` in `queries.py`:
  - For each item, read `relProject["text"]` when `relProject is not None`. Case-insensitive substring match (consistent with `filter_by_owner`'s case-insensitive substring on name/email — queries.py:29–36).
  - Items with `relProject is None` are excluded (not matched).
- Add `"items_by_project"` to `APPROVED_INTENTS`, add validation requiring `--project`, add dispatcher case.
- `cli.py` `agent_query` needs a new `--project` option (add alongside `--owner`).

**Patterns to follow:**
- `filter_by_owner` (queries.py:51–52).
- `items_by_owner` validation in `agent.py:39–44`.

**Test scenarios:**
- Sample with two items whose `relProject.text == "Retirement System"` and one whose `relProject is None`: `filter_by_project(items, "Retirement")` returns 2 items (case-insensitive substring).
- `filter_by_project(items, "Retirement")` excludes items with `relProject is None`.
- Missing `--project` raises `validation_error`.

**Verification:** Same as U7.

### U11. New intent: `items_by_stage` (filter by raw stage)

**Goal:** Agent can ask "what's in the Tabled stage?" and get items whose raw `Stage` matches (case-insensitive exact match on the configured/observed raw value).

**Covers:** R13, R14, F5

**Files:** Same shape as U7.

**Approach:**
- `filter_by_stage(items, stage)` in `queries.py`:
  - Case-insensitive exact match on raw `stage` value (NOT on `stageCategory` — the intent is to surface "raw Tabled" / "raw Delivery" / "raw Definition" regardless of category). "Delivery" is aliased to `open` by U1; this intent still filters on the raw string, independent of that mapping.
- Add `"items_by_stage"` to `APPROVED_INTENTS`, add validation requiring `--stage`, add dispatcher case.
- `cli.py` needs `--stage` option.

**Patterns to follow:** Same as U10.

**Test scenarios:**
- `filter_by_stage(items, "Tabled")` returns only items whose raw `stage == "Tabled"`.
- Case insensitive: `filter_by_stage(items, "tabled")` matches `"Tabled"`.
- `filter_by_stage(items, "Tabled")` returns both `stageCategory == "closed"` items (per U1) and any items whose raw stage is `Tabled` regardless of category (regression-safe).

**Verification:** Same as U7.

### U12. New intent: `items_by_decision_authority` (filter by `decisionAuthority.displayName`)

**Goal:** Agent can ask "what did Ryann Micua have decision authority over?" and get items whose `decisionAuthority.displayName` matches.

**Covers:** R13, R14, F5

**Files:** Same shape as U7.

**Approach:**
- `filter_by_decision_authority(items, person)` in `queries.py`:
  - Case-insensitive substring match on `decisionAuthority.displayName`. Items with `decisionAuthority is None` excluded.
- Add `"items_by_decision_authority"` to `APPROVED_INTENTS`, add validation requiring `--person`, add dispatcher case.
- `cli.py` needs `--person` option.

**Patterns to follow:**
- `filter_by_owner` (queries.py:51–52) — same match logic, different field.

**Test scenarios:**
- Sample with 3 items having `decisionAuthority.displayName == "Ryann Micua"` and 2 with other owners: `filter_by_decision_authority(items, "Ryann")` returns 3 items.
- Items with `decisionAuthority is None` excluded.
- Missing `--person` raises `validation_error`.

**Verification:** Same as U7.

### U13. `workboard schema drift` command

**Goal:** One-shot command that exports schemas for all six work-related lists, diffs against a baseline (default `discovery/workboard_schema.baseline.json`), and reports added/removed/changed lists and columns with severity. Establishes the baseline on first run. Exits non-zero when high-severity drift is detected.

Note: U13 is the manual precursor to the observations-self-improvement roadmap's Phase 3.3 (`docs/roadmaps/observations-self-improvement.md`) — this unit ships detection only; auto-correction (opening PRs to reconcile drift) is out of scope here and remains tracked on that roadmap.

**Covers:** R16, R16a, R17, R18, R19, F6, AE6

**Files:**
- `src/workboard_cli/schema.py` (modify — extract `build_schema_columns(client, site_id, list_id) -> dict` from `export_schema`)
- `src/workboard_cli/schema_drift.py` (create — pure logic, testable without CLI)
- `src/workboard_cli/cli.py` (modify — register `schema drift` subcommand on `schema_app`)
- `tests/test_schema.py` (extend — cover `build_schema_columns` directly)
- `tests/test_schema_drift.py` (create)
- `tests/test_cli.py` (extend)

**Approach:**
- Refactor `src/workboard_cli/schema.py` to extract the column-building logic (currently inlined at `export_schema` lines 8–17) into a standalone function:
  - `build_schema_columns(client, site_id, list_id) -> dict` — calls `get_list_columns`, builds the `{"columns": [...], "column_count": N, "list_id": list_id}` dict (renaming `count` to `column_count` for clarity now that it sits alongside `list_id` in a multi-list context; `export_schema`'s on-disk shape for a single list stays `{"columns": [...], "count": N}` for backward compatibility — `export_schema` maps the two).
  - `export_schema(client, site_id, list_id, output_path)` calls `build_schema_columns(...)`, then writes `{"columns": ..., "count": ...}` to `output_path` as before (no change to its own output shape or callers).
- New module `src/workboard_cli/schema_drift.py` with:
  - Constant `WORK_RELATED_LISTS = ["WorkBoard", "Deliverables", "Tasks", "WorkIntake", "WorkReview", "Users"]`.
  - Function `export_all_schemas(client, site_id) -> dict[str, dict | None]` — iterates `WORK_RELATED_LISTS`, calls `find_list` on the site's list catalog, and for each found list calls `build_schema_columns(client, site_id, list_id)` directly (not `export_schema`, since no file write is needed here) to build an in-memory dict. Missing lists (not on the site) are returned as `None` slots — they participate in drift detection (R16a list-removed). The baseline/current JSON shape is `{"<list_name>": {"columns": [...], "column_count": N, "list_id": "..."}, ...}`, with `None` for a missing list.
  - Function `diff_schemas(baseline: dict[str, dict | None], current: dict[str, dict | None]) -> list[dict]` — returns a list of change entries. Each entry has keys:
    - `list` (str): list name.
    - `changeType` (str): `"list_added"`, `"list_removed"`, `"column_added"`, `"column_removed"`, `"column_type_changed"`, `"column_display_name_changed"`, `"column_lookup_target_changed"`.
    - `severity` (str): `"high"` for list_added/removed and column_lookup_target_changed, tiered for `column_type_changed` (see below), `"low"` for column_added/removed/display_name_changed.
    - `column` (str|None): internal column name when applicable.
    - `note` (str): one-line human-readable description.
  - `diff_schemas` per-list slot handling, given `baseline.get(list_name)` and `current.get(list_name)`:
    - Both `None` → no entry (list absent in both baseline and current; nothing to report).
    - `baseline` slot `None`, `current` slot a dict → one `list_added` entry, severity `"high"`.
    - `baseline` slot a dict, `current` slot `None` → one `list_removed` entry, severity `"high"`.
    - Both slots dicts → proceed to column-level diff (added/removed/type-changed/display-name-changed/lookup-target-changed) as described above.
  - `column_type_changed` severity is tiered rather than a flat `"medium"`:
    - Either side's type is `"unknown"` (SharePoint's `unknown` type covers calculated/system columns whose underlying type Graph doesn't expose) → `"low"` — these transitions are noise, not structural changes.
    - A behavioral transition between two known, non-`"unknown"` types (e.g. `text`→`choice`, `lookup`→`text`) → `"medium"` — the column still exists and holds data, but callers reading its old shape may need to adapt.
    - A transition where one side has a type entirely absent (`None`, i.e. the column's type key is missing rather than present-and-`"unknown"`) and the other side has a concrete type (type→none or none→type) → `"high"` — this indicates a column was effectively removed or newly materialized at the API level, distinct from the `"unknown"` case above where a type value is present but opaque.
  - Function `establish_baseline(baseline_path, current_schemas)` — creates the parent directory if absent (`Path(baseline_path).parent.mkdir(parents=True, exist_ok=True)`, since `discovery/` does not exist by default) before writing the current schemas dict to `baseline_path` as JSON. Returns a status dict for the CLI to print.
  - Function `load_baseline(baseline_path)` — reads JSON if present, else returns `None`.
- CLI command `schema drift`:
  - Options: `--baseline PATH` (default `discovery/workboard_schema.baseline.json`), `--output PATH` (default None — print to stdout).
  - Every output envelope (both the first-run and diff cases) includes `source: {"system": "workboard-cli", "siteUrl": <site_url>}`, `retrievedAt: <ISO timestamp>`, `sessionId: <uuid>` — the same metadata shape as `build_envelope`/`build_summary_envelope`, built the same way (via `_now_iso()` and `get_session_id()`), but without `listName`/`listId` since this command spans multiple lists, not one.
  - Calls `_get_client()`, then `export_all_schemas(client, site_id)`, then attempts `load_baseline`. If absent, calls `establish_baseline`, prints `{"status": "ok", "baseline_established": true, "source": {...}, "retrievedAt": ..., "sessionId": ..., "lists": [...]}` with the list of lists established, exits 0 (covers AE6 first-run). First-run success is distinguished from a diff run purely by the `baseline_established: true` key — there is no separate "no drift" signal on first run, because a first run blesses whatever schema state currently exists as correct; any drift that predates the first run is by definition undetectable until the baseline is refreshed against a known-good state.
  - Otherwise calls `diff_schemas`, prints `{"status": "ok", "drift": <entries>, "summary": {"high": N, "medium": M, "low": K}, "source": {...}, "retrievedAt": ..., "sessionId": ...}`, exits with code **6** iff any entry has severity `"high"` (0 otherwise). Exit code 6 is a new code, added to the CLI's exit-code table in `docs/cli_command_contract.md`, distinct from the existing exit code 3 ("API/Graph error") because schema drift is a detected condition, not a request failure.
  - Wire it as a subcommand on the existing `schema_app` Typer sub-app (cli.py:54).

**Patterns to follow:**
- Existing `export_schema` function (schema.py:6–20), and the new `build_schema_columns` extracted from it, for the per-list export call.
- Existing `find_list` (sharepoint.py:20–24) for list lookup.
- Existing Typer command pattern in `cli.py` (e.g., `schema_export` at line 211 — uses `_get_client`, `_error_exit`).
- Existing exit codes in `docs/cli_command_contract.md` (lines 137–143); this unit adds a new code, 6, to that table (see U14/docs task below).

**Test scenarios:**
- `export_all_schemas` with a mocked client returning 6 lists with columns returns a dict of 6 entries.
- `diff_schemas` with identical baseline and current returns an empty list.
- `diff_schemas` where both `baseline[name]` and `current[name]` are `None` produces no entry for that list.
- Baseline with one list missing (`None` slot) → current with that list present (dict) → one entry `changeType="list_added"`, severity `"high"` (covers AE6 list-added path).
- Baseline with one list present (dict) → current with that list missing (`None` slot) → one entry `changeType="list_removed"`, severity `"high"`.
- Baseline with column X type "text" → current with column X type "choice" (both known types) → one entry `changeType="column_type_changed"`, severity `"medium"`.
- Baseline with column X type "unknown" → current with column X type "text" (or vice versa) → one entry `changeType="column_type_changed"`, severity `"low"`.
- Baseline with column X having a type → current with column X's type key absent (or vice versa) → one entry `changeType="column_type_changed"`, severity `"high"`.
- Baseline with column X absent → current with column X present → one entry `changeType="column_added"`, severity `"low"` (covers AE6 low-severity path).
- Baseline with `DeliveryOwner` lookup target listId A → current with listId B → one entry, severity `"high"` (covers AE6 lookup-target path).
- `load_baseline` on a missing path returns `None`.
- `establish_baseline` writes the baseline file.
- End-to-end CLI: `workboard schema drift` with no baseline present (mocked) → prints `baseline_established: true` (plus `source`/`retrievedAt`/`sessionId`) and exits 0.
- End-to-end CLI: with a baseline and a high-severity drift in mock → exits with code 6 and prints drift entries.
- `build_schema_columns` (tests/test_schema.py): mocked `get_list_columns` returns the expected `{"columns": [...], "column_count": N, "list_id": ...}` shape; `export_schema` still writes the original `{"columns": [...], "count": N}` file shape via `build_schema_columns`.

**Verification:** `pytest tests/test_schema.py tests/test_schema_drift.py tests/test_cli.py` green; manual against live data: run once to establish baseline, run twice to confirm zero-drift exit 0, manually edit the baseline to simulate a removed list, run again to confirm high-severity exit 6.

### U14. Documentation and contract updates

**Goal:** The new WorkItem fields, six new intents, and new command all appear in the user/agent-facing contracts. Source metadata is present on every new envelope variant.

**Covers:** R22, R23, R24

**Files:**
- `docs/agent_json_contract.md` (modify — extend WorkItem table with new fields, extend Approved Intents table with six new rows, document `cycle_time_stats` summary envelope shape, document schema-drift envelope shape)
- `docs/cli_command_contract.md` (modify — add `workboard schema drift` to command tree, add new intent rows to `workboard agent query` section, add a new row to the exit-code table: `6 | Schema drift detected (high severity)`)
- `docs/agent-instructions/field-mapping.md` (modify — add rows for `description`, `priority_status`, `cycle_time`, `rel_project`, `rel_work_brief`, `decision_authority`, `acceptance_authority`, `work_intake` in the key-fields table)
- `docs/agent-instructions/agent-intents.md` (modify — extend pipeline diagram, add new intent registration steps)

**Approach:**
- For each new WorkItem field added by U2–U6, add a row to the WorkItem fields table in `agent_json_contract.md`. Include type, nullable, and a notes column.
- Add the six new intent rows to the Approved Intents table. For `cycle_time_stats`, document that it returns a summary envelope (not the standard items envelope), that `--group-by` is optional and defaults to `owner` (valid values `owner|stage`), and that `--days` does not apply to this intent.
- Add `workboard schema drift` to the command tree with its options, output shape (baseline-established status or drift report), and exit code behavior — including the new exit code 6 for high-severity drift (distinct from the existing code 3 for API/Graph errors).
- Update field-mapping docs to reflect that `Description`, `PriorityStatus`, `CycleTime`, `RelProject`, `RelWorkBrief`, `DecisionAuthority`, `AcceptanceAuthority`, `WorkIntake` are now surfaced via the normalize step.
- Verify each existing test for envelope source metadata (`source.system`, `source.siteUrl`, `retrievedAt`, `sessionId`, plus `source.listName`/`source.listId` where a single list applies) covers the new paths. The `schema drift` envelope omits `listName`/`listId` (it spans multiple lists) but includes `source.system`, `source.siteUrl`, `retrievedAt`, and `sessionId` on both the first-run and diff output shapes (see U13).

**Patterns to follow:**
- Existing WorkItem table format in `docs/agent_json_contract.md` (lines 83–101).
- Existing Approved Intents table format (lines 8–16).

**Test scenarios:**
- Document-level review only — no automated tests. Human reviewer reads each modified doc and confirms it matches the implementation shipped by U1–U13.

**Verification:** Manual review against the test outputs from U1–U13.

## Exit Criteria

The plan is complete and the feature ships when **all** of the following hold:

1. **Functional parity with acceptance examples.** AE1–AE8, as embedded in the "Acceptance Examples" section above, each pass under `pytest` (U1–U12 + U13 provide the corresponding tests; U14 documents the contract surface they confirm).
2. **No regression in existing tests.** `pytest -q` runs all 88 pre-existing tests green plus the new tests added by U1–U13.
3. **Lint clean.** `ruff check .` exits 0.
4. **Source metadata present on every new envelope.** Manual inspection of envelope output for `cycle_time_stats` (summary envelope: `source.system`, `source.siteUrl`, `retrievedAt`, `sessionId`) and `workboard schema drift` (both the first-run and diff output shapes: `source: {system: "workboard-cli", siteUrl: <site_url>}`, `retrievedAt`, `sessionId`; no `listName`/`listId` since it spans multiple lists) confirms all fields are populated.
5. **No new runtime dependencies.** `pyproject.toml` `dependencies` block is unchanged. HTML parsing uses only stdlib.
6. **No writes against SharePoint.** Manual review of the new code paths in `schema_drift.py` and the new envelope builders confirms no Graph mutation endpoints are called (only `GET` for site/lists/columns/items).
7. **WorkItem contract is additive.** No existing key (`id`, `title`, `stage`, `deliveryOwner.displayName`, `dueDate`, `stageCategory`, `sourceUrl`, `raw`, `warnings`) is renamed or removed. Verified by reading the updated `normalize_item` against the existing `test_normalize.py` snapshot tests.
8. **Approved-intent surface grows from 6 to 12.** `len(APPROVED_INTENTS) == 12` after U7–U12 land.
9. **Schema-drift command exits code 6 on high-severity drift.** Verified by U13's end-to-end CLI tests.
10. **Manual smoke against live data.** `workboard summary manager` shows `byStageCategory.unknown == 0` (requires U1's five stage aliases, including `Delivery`, to be in place — without a `Delivery` alias this bar is unreachable given the live data's five `Delivery`-stage items). A `cycle_time_stats` invocation returns a non-empty `bogus_count`. `workboard schema drift` (first run) establishes a baseline, exits 0, and is distinguished as a first run by `baseline_established: true` in its output (a first run blesses the current schema state as correct — any drift that predates it is undetectable until the baseline is refreshed); a second run reports zero drift and exits 0.

## Confidence Check

- **Approach certainty:** High. Each unit maps to a specific acceptance example or a small cluster of them. The data shape (CycleTime strings, RelProject JSON, RelWorkBrief HTML, lookup strings) is empirically verified against `tmp/items_WorkBoard.json` (read during planning). The HTML parsing strategy (stdlib `html.unescape` + `<[^>]+>` strip + `re.findall` for `<a>` tags) has been validated against the wild HTML snippets — the patterns are regular, not adversarial.
- **Unknowns / risks:**
  - **R11/R12 (lookup expansion)** — the live data shows lookup fields as plain strings, not the expanded dict shape. The implementation handles both, but real-world coverage of the expanded shape is unverified. If Graph ever returns the expanded shape, the unit tests cover it; if it does not, no harm done. *Severity:* low.
  - **R8/R9 (workBriefLinks/HTML parsing)** — relative `href` values like `/:w:/r/sites/itdocumentcontrol/...` are also entity-encoded (`&#58;`, `&amp;`). The original risk here was that `urljoin` alone would mis-resolve the raw encoded string; the actual fix is `html.unescape(href)` before `urljoin` (see U4), which is now specified and covered by the AE4 test with a known-good expected URL. *Severity:* low — addressed in the approach, not merely mitigated.
  - **R16a (list removal in drift detection)** — when a baseline lists a list that has been deleted from the site, `find_list` returns `None` and `export_all_schemas` records that slot as `None`. The diff must treat `None` slots correctly. Covered by test scenarios, but worth re-checking during execution.
  - **R17–R19 (schema-drift cross-list)** — the discovery found 11 lists; the plan names 6 as work-related. If a list is renamed or its purpose shifts, the constant `WORK_RELATED_LISTS` becomes stale. Document this in the constant's docstring so a future maintainer can edit it without re-reading the whole plan.
- **Validation approach at execution time:**
  - Run `pytest -q` after each unit lands (units are small enough for incremental commits).
  - Run `ruff check .` after each unit.
  - Smoke against live data after U1, U6, U9, U13 — these touch the visible CLI surface.
- **Open product scope questions:** None deferred from the requirements stage (the five were resolved at the top of this plan).
- **Confidence verdict:** Implementation can begin. No further planning-time work required.

## Sources / Research

- `tmp/sharepoint_changes_report.md` — primary discovery findings driving this plan
- `tmp/items_WorkBoard.json` — sample items showing actual field shapes (CycleTime strings, RelProject JSON, RelWorkBrief HTML, lookup fields). Empirically verified during planning: CycleTime values include `"8"`, `"-46,113"`, `"-46,216"` (anomalous); RelProject values are JSON like `{"id":3,"text":"Retirement System"}`; RelWorkBrief is HTML with `ExternalClass<id>` divs, `&#58;` entity encoding, and `<a href="/:w:/r/sites/...">` relative links; `DeliveryOwner`/`DecisionAuthority`/`AcceptanceAuthority` are plain strings (not expanded dicts) in the current payload.
- `tmp/schema_WorkBoard.json` — exported schema with `unknown` type entries on calculated columns
- `src/workboard_cli/normalize.py` — current normalization path; the new field handling plugs in here
- `src/workboard_cli/queries.py` — current filter surface; basis for new intent filters
- `src/workboard_cli/agent.py` — current `APPROVED_INTENTS` set; grows from six to twelve
- `src/workboard_cli/schema.py` — current schema export; basis for the drift diff
- `src/workboard_cli/cli.py` — current command surface; new commands register here
- `src/workboard_cli/output.py` — envelope builders; reused for new intents (summary envelope for `cycle_time_stats`)
- `src/workboard_cli/sharepoint.py` — `find_list`, list/column/item accessors reused by the drift command
- `config/workboard.defaults.yaml` — current field mapping + stage aliases; `stage_aliases` extended for U1
- `tests/test_normalize.py`, `tests/test_queries.py`, `tests/test_agent.py`, `tests/test_cli.py`, `tests/test_output.py` — existing test patterns and fixtures to extend
- `docs/cli_command_contract.md` — current command contract; new commands document here
- `docs/agent_json_contract.md` — current WorkItem contract; new fields append here
- `docs/agent-instructions/architecture.md` — module layout that constrains where new code lives
- `docs/agent-instructions/field-mapping.md` — field mapping guide; new mappings follow this pattern
- `docs/agent-instructions/agent-intents.md` — intent pipeline; new intents register here
- `docs/roadmaps/observations-self-improvement.md` — adjacent schema-drift roadmap (Phase 3.3); referenced for boundary clarity, not duplicated
- `STRATEGY.md` — read-only commitment and product positioning
- `MEMORY.md` — current session state and prior decisions
- `docs/plans/2026-06-19-001-feat-correlation-id-observation-streams-plan.md` — sibling implementation plan, used as format reference
