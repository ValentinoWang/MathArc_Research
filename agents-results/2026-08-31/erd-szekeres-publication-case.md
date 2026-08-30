# Erdős–Szekeres Publication Case

## Provenance

- Repository: `https://github.com/ValentinoWang/Erd-s-Szekeres`
- Audited ref: `main`
- Audited commit: `af13a373be5b52ee0af494cb615a11e801d59b52`
- Audit date: `2026-08-31`

## Scope

This is a MathArc publication-gate calibration case for the planar
Erdős–Szekeres open case `ES(7)=33`. The repository explicitly states that it
does not claim a proof of the global case. Its local structural theorems and
exact computations are distinct from a complete global certificate.

## Reproduction results

`src/reproduce_local_dynamics.sh` was run from `src/`. The C++ reconstruction
generated the following values before the script stopped because its expected
record was absent:

```text
n8_no_convex7 = 1221504
n9_no_convex7_models = 108068130
compatible_transitions = 59441346
strongly_connected = true
```

The script exited non-zero because `rebuild_local_dynamics_result.json` is not
present in the checkout, so expected-vs-actual cold replay could not be
completed.

## Artifact and release gates

- `unzip -t paper/ES7_33_arXiv_source.zip` failed with `BadZipFile` / missing
  end-of-central-directory signature.
- The ZIP is 15,009 bytes with SHA-256
  `78930d89405d4fe34849a575b12f2cb401125238ca747b5bea5c38ba51df326b`.
- `paper/submission/SIZE_AUDIT.json` declares 70,430 compressed bytes, which
  does not match the checked-out file.
- `scripts/verify_archive.sh` failed its structure gate because the declared
  `paper/source/main.tex` and release/archive paths are absent from this ref.

## Publication disposition

```yaml
scientific_closure: BLOCKED
evidence_integrity: INCOMPLETE
manuscript_state: REVIEWABLE
technical_preflight: FAIL
human_signoff: PENDING
submission_route: UNDECIDED
```

This case must not be promoted to a submission-ready or global-proof claim
until the missing expected replay record, intact arXiv source, declared release
paths, and corresponding claim/review bundle are restored and independently
verified.
