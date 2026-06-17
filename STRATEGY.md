---
title: IT WorkBoard CLI — Strategy
last_updated: 2026-06-18
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

1. **Discovery & Auth** — MSAL setup, site resolution, list discovery
2. **Schema export** — field discovery and normalization config
3. **Query intents** — predefined queries: open, overdue, blocked, by-owner, recently-updated, manager summary
4. **CLI commands** — Typer entrypoints wrapping the intents
5. **Output & Summaries** — structured JSON + markdown summary formats
6. **Testing & quality** — pytest, ruff, audit gates per the orchestrator flow

## Not working on

- **Write operations** — all mutations (create, update, delete) are out of scope. SharePoint remains the system of record for edits. Write access may be revisited in a future expansion.
