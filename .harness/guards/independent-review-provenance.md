# Guard Card: independent-review-provenance

- Failure class: independent AI review provenance substitution
- Scope: R1 v11 formal zero-write review reports, run records, and logs
- Blocking level: release gate
- Command: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_regression_evaluation`
- Repair path: discard the affected campaign, launch both approved wrappers against one frozen manifest, and persist fresh lane-specific reports, run records, and logs.

## Failure contract

The guard fails unless the Luna L3 and Sol L4 lanes have distinct execution IDs, Codex session IDs, PIDs, wrapper identities, prompt hashes, logs, reports, and terminal run records. Both runs must exit zero, declare zero-write operation, record no changed paths, bind the same frozen manifest, and end with `Verdict: PASS`. Every path component under `reports/`, `runs/`, and `logs/` must be a real campaign-local directory or file rather than a symbolic link.

## Evidence

- Red proof: synthetic campaigns replay one report as two lanes, hard-link byte-identical reports, and replace the reports directory with a symbolic-link ancestor.
- Green proof: two distinct synthetic execution records and logs bind the required lane, reviewer, wrapper, manifest, terminal result, and zero-write markers.

## Calibration

This guard proves repository-level provenance for the recorded local worker runs. It does not make AI an acceptance authority, replace the blocking H-01 decision, establish mathematical correctness, or protect against replacement of the entire local repository trust root.
