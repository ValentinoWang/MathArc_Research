# Guard Card: frozen-review-inputs

- Failure class: review-evidence identity drift
- Scope: R1 and downstream formal AI review campaigns that declare `frozen-inputs.json`
- Blocking level: release gate
- Command: `python3 scripts/validate_frozen_review_inputs.py <campaign>/frozen-inputs.json --project-root .`
- Fast proof: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_frozen_review_inputs`

## Failure contract

The guard fails when the manifest schema or R1 input profile drifts, when local and remote candidate heads differ, when the declared input set is not an exact match for the profile, when the manifest is missing or outside the project, when an input path is missing, duplicated, non-normalized, outside the project, a symlink, not a regular file, or when any declared SHA-256 differs from the observed bytes. Validation covers every required entry and cannot stop after a selected prefix.

## Evidence

- Red proof: the protected tests omit a required input, alter candidate-head identity and schema, mutate the fifth entry, path identity, duplicate identity, missing input, escape path, symbolic link, hard-link alias, and digest.
- Green proof: the fixed `r1-regression-evaluation-v11` profile exact-matches all required entries and the CLI reports the exact validated count.
- Repair path: regenerate the campaign manifest from the committed frozen candidate, rerun this guard, and discard reviews that consumed the stale manifest.

## Calibration

Historical campaigns are immutable audit evidence and are not scanned automatically. The guard runs against the manifest explicitly selected by the current acceptance evidence, so historical drift cannot create false positives and stale current evidence cannot be silently reused. Mutable terminal evidence and node state remain outside the frozen set to avoid a self-invalidating hash cycle and are checked by lifecycle gates instead.
