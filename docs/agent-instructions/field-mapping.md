# Field Mapping & Normalization

## How it works

`normalize.py` reads the field mapping from config and transforms raw SharePoint column values into a normalized `WorkItem` dict. The mapping lives in `config/workboard.defaults.yaml` (committed) and can be overridden in `config/local.yaml`.

## Config schema

```yaml
fields:
  title: "Title"
  stage: "Stage"
  delivery_owner: "DeliveryOwner"
  why: "Why"
  who: "Who"
  schedule: "Schedule"
  date_due: "DateDue"
  date_committed: "DateCommitted"
  date_start: "DateStart"
  date_closed: "DateClosed"
  scope: "Scope"
  cycle_time: "CycleTime"
  acceptance_criteria: "AcceptanceCriteria"
  decision_authority: "DecisionAuthority"
  acceptance_authority: "AcceptanceAuthority"
  requirements: "Requirements"
  deliverables: "Deliverables"

stage_aliases:
  Backlog/Open: "open"
  In Progress: "in_progress"
  Blocked: "blocked"
  Done: "done"
  Closed: "done"
```

Keys are normalized field names; values are SharePoint internal column names from schema export.

## Adding a field mapping

1. Run `workboard schema export --list WorkBoard` to see current column names.
2. Add the mapping to `fields:` in `config/workboard.defaults.yaml`.
3. Add a test case in `tests/test_normalize.py` for the new field.
4. If the field needs special parsing (dates, people), add handling in `normalize.py`.
5. If the field changes the WorkItem shape, update `docs/agent_json_contract.md`.

## Stage category mapping

`stage_aliases` maps raw SharePoint status values to normalized categories: `open`, `in_progress`, `blocked`, `done`. The `queries.py` filters (`filter_open`, `filter_blocked`, etc.) use these normalized categories, not raw values.

## Discovery spike

The `discovery_spike.py` module was used during initial development to enumerate lists, columns, and sample items. It's retained as a reference but not part of the stable command surface.

## Key fields from discovery

| Normalized | SharePoint | Notes |
|---|---|---|
| `delivery_owner` | `DeliveryOwner` | Indexed, person/group field |
| `stage` | `Stage` | Choice field mapped via stage_aliases |
| `date_due` | `DateDue` | DateTime |
| `title` | `Title` | Standard SharePoint title |
| `_ColorTag` | (discovery only) | Present in raw data but not mapped |

Unknown fields encountered in live data should be added here after discovery, never silently dropped.
