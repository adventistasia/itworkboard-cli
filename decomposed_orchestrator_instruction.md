# Decomposed orchestrator instruction

Use this when the orchestrator can delegate one task at a time.

## Sequence

1. Give the builder `briefs/t01_discovery_spike.md`.
2. Give the auditor `audit_briefs/a01_discovery_audit.md` plus the builder output.
3. If A01 passes, give the builder `briefs/t02_architecture_and_contracts.md`.
4. Give the auditor `audit_briefs/a02_architecture_and_security_audit.md` plus the builder output.
5. If A02 passes, run T03, T04, and T05.
6. Run A03.
7. If A03 passes, run T06, T07, T08, T09, and T10.
8. Run A04 final acceptance audit.
9. Return `orchestrator_completion_report_template.md` filled in.

## Rule

If an audit fails, return findings to the builder and rerun the same audit after fixes. Do not proceed on a failed gate unless a human explicitly accepts the risk.
