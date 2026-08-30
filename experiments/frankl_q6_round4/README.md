# Frankl `q=6` trace-fiber closure bundle

This directory preserves a historical machine-checked candidate record for the `q=6` bridge. The current checkout does not contain the complete source and component-result set needed to reproduce that record from a cold start.

## Fast acceptance

```bash
./acceptance_commands.sh
```

This validates the SHA-256 and claim boundary of the checked-in historical aggregate. It does not regenerate component outputs or report current theorem acceptance.

Current status:

```text
ARCHIVE_INTEGRITY_PASS / FULL_COLD_REPLAY_UNAVAILABLE
```

## Full cold replay preflight

```bash
./rebuild_all.sh
```

The script fails before creating build/output directories because three declared verifier sources are absent:

- `verifier/verify_q6_exact6_card.cpp`
- `verifier/verify_q6_exact7_pair.cpp`
- `verifier/verify_q6_k7_full_cases.py`

All eight declared component-result JSON files are also absent. `archive_manifest.json` is the machine-readable authority for source/result coverage. Restoring only filenames is insufficient: component results must parse and carry their expected pass predicate before the audit can report that replay inputs are present.

## Claim boundary

- historical `q=6` candidate record: `CLOSED_INTERNAL_EXACT`
- current checkout evidence: `ARCHIVE_INTEGRITY_PASS / FULL_COLD_REPLAY_UNAVAILABLE`
- minimum-three-set `q>=7`: `OPEN`
- complete Frankl conjecture: `INCONCLUSIVE`
- external peer review / novelty audit: not yet completed

See `frankl-q6-complete-bridge-candidate-2026-08-23.md` for the historical proof structure. That document and the checked-in aggregate are archive records, not a replacement for the missing verifier sources.
