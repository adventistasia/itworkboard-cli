# One-shot orchestrator instruction

Use this only if the orchestrator can ingest the whole package and manage subagent delegation internally.

```text
You are the orchestrator for building a usable read-only SharePoint WorkBoard CLI. Ingest the full execution package. Execute tasks in manifest order. Use builder subagents for build tasks and auditor subagents for audit gates. Do not skip discovery. Do not write to SharePoint. Do not commit secrets. Use the audit briefs as hard gates. The final output must be an installable, tested, documented CLI that can authenticate, discover the IT Workboard site/list, export schema, retrieve items, normalize fields through configuration, run operational queries, produce manager summaries, and return agent-safe JSON for approved query intents. At completion, return the completion report using `orchestrator_completion_report_template.md`.
```
