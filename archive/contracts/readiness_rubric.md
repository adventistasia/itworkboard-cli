# Readiness rubric for orchestrator gates

Score each dimension 1 to 5.

| Dimension | Critical | Pass threshold |
|---|---:|---:|
| Intent clarity | yes | 4 |
| Outcome clarity | yes | 4 |
| Scope bounded | yes | 4 |
| Success criteria | yes | 4 |
| Agent usability | yes | 4 |
| Judgment captured | no | 3 |
| Constraints stated | no | 3 |
| Output fit | no | 3 |

## Gate rule

A phase cannot pass if any critical dimension is below 4.

## Audit verdicts

- `Pass`: proceed.
- `Needs Revision`: return findings to builder.
- `Blocked`: human decision or permission is required.
