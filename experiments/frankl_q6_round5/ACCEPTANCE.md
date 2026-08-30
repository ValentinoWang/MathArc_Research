# Frankl q=6 Round 5 acceptance gate

Status date: 2026-08-23

## Machine acceptance

`verifier/verify_q6_residual_type_multisets.py` is accepted when it exits successfully and its JSON output reports:

- `status = ACCEPT`;
- `trace_type_multisets = 244068`;
- `coarse_residual_multisets = 82`;
- `unresolved_rows_before_exception_repair = 38`;
- `exception_categories = 8`;
- `repaired_rows = 38`.

The checked-in result is `results/q6-round5-residual-type-audit.json`.

## Dependency boundary

Round 5 consumes `H_p` values attributed to Round 4's historical positive-core verification. It does not replace the Round-4 C++/Python verifiers; it audits only the residual trace-type compression used to connect them. The current checkout cannot cold-replay the complete Round-4 dependency; see `../frankl_q6_round4/archive_manifest.json`.

## Accepted scoped conclusion

The checked-in Round-5 audit records no uncovered `k=4..7` trace-type multiset within its frozen input contract. Because the complete Round-4 verifier/result set is absent, Round 5 cannot independently promote the historical aggregate conclusion to current replay evidence. The archived Round-4 record states:

`q6_bridge = CLOSED_INTERNAL_EXACT` (historical record; current full cold replay unavailable).

## Non-accepted claims

The following are explicitly **not** accepted by this gate:

- Frankl's full conjecture;
- a new first proof of the nine-element case;
- novelty of the trace-fiber/charge method relative to prior FC-family, Poonen-weight, or small-universe verification literature;
- full independent reimplementation of the complete q=6 proof pipeline;
- external expert validation.

## Submission gate

Paper drafting may proceed, but arXiv submission should be treated as **not yet submission-ready** until the remaining gates in `../frankl_q6_round4/PAPER_READINESS.md` are closed: independent full reimplementation, external combinatorics audit, novelty audit, and artifact freeze.
