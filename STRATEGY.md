---
title: IT WorkBoard CLI — Strategy
last_updated: 2026-06-19
status: draft
---

## Target problem

AI agents have no programmatic access to the IT WorkBoard SharePoint list, preventing them from helping the team manage, update, and monitor work items. Team members resort to manual SharePoint navigation for visibility into open, overdue, or blocked items.

## Our approach

A purpose-built CLI wrapping the Microsoft Graph API with predefined agent-friendly query intents (`open_items`, `overdue_items`, `blocked_items`, `items_by_owner`, `recently_updated_items`, `manager_summary`). Field names are normalized and output is structured JSON — designed for AI agent consumption, not generic API wrapping.

## Who it's for

- IT delivery leads (standup summaries, team-wide views)
- Project managers (cross-team status)
- IT directors (executive visibility)
- Team members (personal item queries, updates via their AI agents)

## Key metrics

- **Workboard accuracy** — reduction in stale items; the board reflects the actual state of work

## Tracks

1. **Data Source Integration** — SharePoint site resolution, list discovery, schema export, MSAL auth. Establishes the connection to the workboard.
2. **Agent Query Layer** — predefined query intents (`open`, `overdue`, `blocked`, `by_owner`, `manager_summary`) and their CLI entrypoints. The core value for AI agents.
3. **Output & Summaries** — structured JSON envelopes, markdown summary formats, agent-friendly output contracts. Makes the data consumable.
4. **Auto-Refinement** — the agent monitors interaction patterns and surfaced data to proactively suggest schema updates, new query intents, stale documentation refreshes, and output improvements without human triage.

## Not working on

- **Write operations** — all mutations (create, update, delete) are out of scope. SharePoint remains the system of record for edits. Write access may be revisited in a future expansion.
