# Residual Review Findings

**Branch:** `feat/correlation-id-plan`
**Head SHA:** `67b7b7a`
**Run:** `review-20260619-152555`
**Date:** 2026-06-19

## Applied

- **#1** (P1) UUID v4 version nibble assertion — added `assert parsed.version == 4` to `test_session_id_is_valid_uuid` (`tests/test_observations.py:89`)
- **#7** (P3) Weak sessionId regex — replaced permissive regex with proper UUID format pattern in `_assert_valid_session_id` (`tests/test_output.py:85`)

## Filed as Issues

| # | Severity | File:Line | Title | Ticket |
|---|----------|-----------|-------|--------|
| 2, 3 | P2 | `tests/test_observations.py:64` | Missing invalid/non-UUID and empty-string WORKBOARD_SESSION_ID env var edge case tests | [#1](https://github.com/adventistasia/itworkboard-cli/issues/1) |
| 4 | P2 | `tests/test_cli.py:101` | Missing cross-stream correlation end-to-end test (stdout + JSONL + counters in one invocation) | [#2](https://github.com/adventistasia/itworkboard-cli/issues/2) |
| 5, 6 | P2 | `tests/test_cli.py:81` + `tests/test_observations.py:76` | Missing sessionId assertions on error envelopes and disabled-mode stdout | [#3](https://github.com/adventistasia/itworkboard-cli/issues/3) |
| 8 | P3 | `tests/test_cli.py:101` | Integration test should assert envelope sessionId matches `obs.get_session_id()` | [#4](https://github.com/adventistasia/itworkboard-cli/issues/4) |

## Testing Gaps (not filed)

- No test for session_id on gap/interaction_gap events (`make_on_gap()`)
- No test for session_id on custom events with non-trivial data payloads
- No test for `_flush()` when no events captured (early return path)
- No cross-process isolation test (separate invocations → different session_id)
- `test_cli_capture_with_mocked_query_includes_session_id` mutates module state directly

## Residual Risks (not filed)

- UUID collision risk across independent CLI processes (acceptable by design)
- Gap events via `make_on_gap()` not tested for session_id stamping
