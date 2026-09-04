# Runtime Pilot: Two-Generation Report

Status: `TEMPLATE / NOT RUN`

This report records a deterministic local pilot only. It is not production evidence, a deployment report, or human acceptance.

## Run identity

- Plan: `benchmarks/runtime-pilot-plan.json`
- Runtime run ID: `<fill after machine run>`
- Release ID / source commit: `<fill from the invoking checkout>`
- Evidence directory: `agents-results/<UTC-date>/runtime-pilot/<run-id>/`

## Generation table

| Generation | Input snapshot digest | Commit digest | Accepted | Failed / late | Machine test |
| --- | --- | --- | --- | --- | --- |
| g1 | `<digest>` | `<digest>` | `<count>` | `<count>` | `tests/test_runtime_pilot_baseline.py` |
| g2 | `<digest>` | `<digest>` | `<count>` | `<count>` | `tests/test_runtime_pilot_generation_consumption.py` |

## Required observations

- Smoke gate: `PASS` / `FAIL` (attach raw test output).
- Frozen input identity: `PASS` / `FAIL`.
- Idempotent execution and commit replay: `PASS` / `FAIL`.
- Late results quarantined: `PASS` / `FAIL`.
- Recovery plan digest and input pin: `PASS` / `FAIL`.

## Boundary statement

No production host, external model, live customer data, restart, or human sign-off is represented by this document. Replace `NOT RUN` only with paths to actual, independently retained evidence.
