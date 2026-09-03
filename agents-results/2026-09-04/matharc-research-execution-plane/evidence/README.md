# Execution Evidence

This directory contains the machine evidence for the execution-plane release.
The structured artifacts are source-bound and must remain reproducible from the
recorded command, source identity, environment, and result digest.

- `acceptance-matrix.json` contains real NC-01 through NC-12 results.
- `negative-cases/` contains each case's structured result and raw command
  output; every result exits `0` and has `status: PASS`.
- `harness-ci-result.json` and `harness-ci-run.log` contain the complete
  17-command Harness workflow run with zero workflow skips.
- `release-readback.json` is written only after the live GitHub refs and branch
  cleanup have been inspected. It is the publication readback, not a substitute
  for a successful push.

The `.ssot/validation-report.json` file binds the validation run to the current
project state. Any change to bundle content requires a fresh compile/validation
run before `check_push_gate.py` can pass.
