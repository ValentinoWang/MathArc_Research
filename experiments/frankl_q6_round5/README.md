# Frankl q=6 Round 5 — exact residual trace-type audit

Status date: 2026-08-23

## Result

This round independently audits the residual `k=4..7` trace-type space used by the historical Round-4 q=6 candidate record.

For the frozen setting

- `|S| = 3`, where `S` is a minimum nonempty member;
- `|Omega| = 6` outside elements;
- `k` = number of nonempty outside parts of size one or two;

Round 5 enumerates every trace-type multiset for `k=4,5,6,7` and obtains:

- `244,068` exact trace-type multisets checked;
- `82` multisets surviving the coarse `H_p` / full-pair bounds;
- `38` low-positive-geometry rows surviving the generic top-fiber correction;
- those `38` rows collapse to exactly `8` exceptional categories;
- every exceptional category has a finite trace-superfamily / support-union repair whose lower bound covers its remaining shortfall.

The Round-5 verifier returns `ACCEPT` for this residual-type audit.

## Claim boundary

This is an independent residual-type audit of one dependency layer. It strengthens confidence in the finite case decomposition, but it is **not** an independently rewritten implementation of the complete q=6 proof from the mathematical specification. The current checkout is missing three Round-4 verifier sources and all eight Round-4 component results, so Round 5 cannot promote the historical aggregate to current full-replay evidence.

The historical candidate statement remains:

> If a finite union-closed family has a minimum nonempty member of size three and exactly six outside elements, then the family satisfies Frankl's conclusion.

This is **not** a proof of Frankl's full conjecture. The universe has nine elements, so truth of the special case is already covered by the known verification for universes of size at most twelve; any paper-level novelty must therefore be in the trace-fiber/charge proof architecture, structural decomposition, replayable evidence pipeline, or MathArc Research methodology rather than theorem priority.

## Reproduce

```bash
python3 verifier/verify_q6_residual_type_multisets.py \
  > results/q6-round5-residual-type-audit.json
```

Expected key fields:

```json
{
  "status": "ACCEPT",
  "counts": {
    "trace_type_multisets": 244068,
    "coarse_residual_multisets": 82,
    "unresolved_rows_before_exception_repair": 38,
    "exception_categories": 8,
    "repaired_rows": 38
  }
}
```

## Paper-readiness implication

Round 5 closes a concrete residual-type audit gap in its own checked input: the compression is checked against all `244,068` residual trace-type multisets rather than only worst-cost representatives. It does not close the current Round-4 source/result coverage gap.

It does **not** close the remaining submission gates listed in `../frankl_q6_round4/PAPER_READINESS.md`: full independent reimplementation, external combinatorics audit, novelty/literature audit, and final artifact freeze are still required before treating the preprint as submission-ready.
