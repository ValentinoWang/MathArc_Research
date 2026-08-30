# Frankl q=6 — latest exact audit

Status date: 2026-08-23

## Frozen claim

> If a finite union-closed family has a minimum nonempty member of size three and exactly six outside elements, then the family satisfies Frankl's conclusion.

## Historical internal result record

- frozen q=6 proof DAG: **closed**;
- exact trace-family classes: `90`;
- exact `k=4,5,6,7` trace-type multisets audited: `244,068`;
- low-cost positive-core geometries audited: `11,625`;
- restricted six-core `L_7` collections audited: `296,010`;
- dangerous three-small-part geometries audited: `15,120`;
- final status: `MACHINE_CHECKED_CANDIDATE_THEOREM`;
- full Frankl conjecture: `INCONCLUSIVE`.

These counts and conclusions are preserved from the 2026-08-23 report. They are not current-checkout replay evidence.

## Current archive audit

```text
ARCHIVE_INTEGRITY_PASS / FULL_COLD_REPLAY_UNAVAILABLE
```

`archive_manifest.json` binds the checked-in historical aggregate `results/q6-round4-final.json` to SHA-256 `cba7336cf06a86ba19db07b4d4926037000d4019f23698a1c35fca8b4f880890`. The archive auditor verifies that exact file and preserves the explicit `full_frankl_conjecture = INCONCLUSIVE` boundary.

The current tree is missing three declared verifier sources and all eight component-result JSON files. Therefore neither the modular suite nor the historical monolithic replay can be rerun from this checkout. `rebuild_all.sh` now fails closed before creating build or result directories.

## Historical content hashes

```text
monolithic verifier
71b98785d01113310a3f256ff673750296514c8d9820a91cdc8846ff5f1c8762

accepted output and both cold replays
f98e52d7ce76c131ae5b7db55114d25616b555887eae059591b67ae6ab5f2719
```

Neither historical digest is currently bound to a complete tracked source/output object. They remain provenance from the earlier report and must not be cited as a current cold replay.

## Claim boundary

The archived report claimed closure of the frozen q=6 special-case contract only. The current checkout verifies preservation of that report, not a fresh closure. It does not close minimum-three-set cases with `q>=7`, cases with minimum nonempty set size at least four, or Frankl's full conjecture.

## Paper gate

The historical report allowed writing to begin. Current use or submission must first restore and rerun the complete declared verifier/result set, then still wait for:

1. clean-room review or reimplementation of the final verifier;
2. independent human audit of every mathematical reduction;
3. literature and novelty comparison;
4. frozen paper-facing release with environment and dependency manifest.

Because the scoped theorem has universe size nine and was already covered by earlier small-universe verification, a defensible paper must be framed around the trace-fiber/charge proof architecture, structural decomposition, replayable evidence pipeline, and MathArc Research agent methodology—not theorem priority.
