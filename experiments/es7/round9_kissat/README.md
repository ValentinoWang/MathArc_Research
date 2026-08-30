# ES(7)=33 Round-9 Kissat experiment

This directory absorbs the former standalone branch `matharc/es7-round9-kissat` into the canonical MathArc Research development line.

## Purpose

Run a reproducible SAT attack on the canonical rank-3 signotope relaxation for the 33-point Erdős–Szekeres problem.

## Contents

- `generate_formula_ci.py` — deterministic CNF generator with a frozen SHA-256.
- `verify_sat_model.py` — independent SAT assignment checker.
- `.github/workflows/matharc-es7-round9-kissat.yml` — eight-seed Kissat run with SAT-model or UNSAT-DRAT verification.

## Interpretation boundary

- `UNSAT` plus an independently checked DRAT certificate proves the frozen signotope relaxation is impossible and therefore yields the corresponding ES(7) upper-bound consequence.
- `SAT` does **not** by itself produce a planar point configuration: the satisfying signotope may be non-stretchable and requires separate geometric analysis.
- `UNKNOWN`, timeout, solver crash, or a partial proof log is not a mathematical conclusion.

This is a MathArc research program/experiment, not a separate long-lived product branch.
