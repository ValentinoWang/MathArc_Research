# A4 Current-HEAD Archive Boundary Review

- Run: `A4-formal-20260901-current`
- Lane: `archive-review`
- Source: `HEAD == origin/main == 3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
- Contract v2 SHA-256: `4b7ac7ea035d59be7c87fef9867b97529f8b00f68c207d7460963cd625095c84`
- Binding SHA-256: `7b299dff38c8c36b9041c8f121b28dc0b70a6539c894081bd4111dab17b4cc78`
- Checklist SHA-256: `cd57b8e24177664d0796084d81cda6891703a9fe7a6b5a958dbd943cfc180593`
- Mode: read-only review; the sole write is this return file
- Boundary: offline, checked-in source bytes, non-mathematical-proof, non-public-release

## Findings

### P0

None.

### P1

None in the requested archive/state boundary. The current pushed commit changes the
topic-observation storage root to the external local-store boundary and does not
change the archive contract semantics; focused tests and fresh replay passed.

### P2 / residual

No blocking P2 was found. The fixed source snapshots remain offline evidence only;
they do not establish external-source freshness, mathematical proof, production or
device behavior, or public-release authorization.

## Current source and protected-test identity

`git ls-remote origin refs/heads/main` and `git rev-parse HEAD` both returned
`3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`; `git status --short --branch` was clean
(`main...origin/main`) before this return was created.

Observed SHA-256 values, also matching the frozen HEAD blobs:

| Path | SHA-256 |
| --- | --- |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` |
| `matharc/v02/topic_observation.py` | `16743b6097480044253c50fc8188b65a23062e5f57435361863311b1483a80e1` |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` |
| `evidence/t2-fixtures/three-real-archives.json` | `475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c` |

The prior accepted A4 run is bound to `5af1d9ff`; the current HEAD delta touches
`topic_observation.py` only for `external_root` routing in the reviewed implementation
surface. The archive and protected-test bytes are unchanged and were re-executed
at the current HEAD. The current human run is
`acceptance/human/A4-topic-observation-dogfood/runs/20260901T141500Z-local-a4f002/result.md`
with H-01 `ACCEPTED` under the three hashes above.

## Fixed fixtures, source bytes, and budget

All three S1 fixture digests and all four unique source artifact digests match the
T2 contract. The contract budget digest is
`efdf4e18af10228e0706db1ee91b896ead57982e132a4e5315faf79860eb4b45` and the
reconstructed snapshot is exhausted with input-token limit/spend `1`, one model
call, zero tool calls, zero output tokens, and no divergent usage reports.

Exact fixture/source SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `s1-fixtures/confirmed-open.json` | `2eac896e4038750a0b59baadc5d4b3b04aa261f4680b51839fbb507ca035053a` |
| `s1-fixtures/frankl-q6.json` | `d76d9f4a03d781f1a2b66168666b00ff7c1c4107b8ca48fb48fefdc18325c592` |
| `s1-fixtures/resolved-collision.json` | `935ec7a4cc236f44fbba60c877be9cff85fc4edb99cfc7c0e55ab4f9ccdd2acd` |
| `sources/engineering-progress.md` | `f0090168916eab1e1642c0ac0325914492b9725f1432027aa983b0bfe482b4cb` |
| `sources/frankl-q6-exactly-three-small-outside-parts.md` | `8ef2177acb983fdd1ef6602e7cae1b4853eed0c94ba1eff2e3b6cd188fc33476` |
| `sources/arxiv-2601.22401v3-main.tex` | `540973d154a63470f8648ed2b84b75be04c2c56ee7bf0d4047640510573647bd` |
| `sources/erdos-397-current.html` | `ba778973416d0d89a00e206777be974891e0317c106ef155f8ddb430c00a6885` |

The contract metadata is immutable in current code: `non_claim_boundary` must equal
the exact approved sentence, and `source_fixture_directory` must equal
`../s1-fixtures` and resolve to the runner fixture directory. The protected negative
test covers both mutations.

## Fresh execution and restart evidence

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/matharc-a4-current-pycache TMPDIR=/tmp \
python3 -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives
```

Result: exit `0`; 41 tests passed, zero skips, zero failures/errors.

Independent temporary-directory command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/matharc-a4-current-pycache TMPDIR=/tmp \
python3 - <<'PY'
import tempfile
from pathlib import Path
from matharc.v02.dogfood_archives import DogfoodArchiveRunner
e = Path("agents-results/2026-08-31/problem-intelligence-plane/evidence")
with tempfile.TemporaryDirectory(prefix="a4-current-", dir="/tmp") as d:
    first = DogfoodArchiveRunner(d, e / "s1-fixtures").run()
    restart = DogfoodArchiveRunner(d, e / "s1-fixtures").run()
    print(first["replayed"], restart["replayed"], restart["archive_blocked"],
          restart["blocking_manual_ids"], restart["budget_digest_sha256"],
          restart["no_claim_or_trace_created"],
          [(c["problem_id"], c["topic_status"], c["replay_status"],
            c["status"]["reported_status"], c["status"]["validated_status"],
            c["manual_reason"], c["promotion_allowed"], c["claim_created"],
            c["trace_created"]) for c in restart["cases"]])
PY
```

Result: `False True True`, manual IDs
`manual-331c33be322f606d88588305` and `manual-ab63a3b2b7aa1769c73dbef8`; budget
digest matched the contract; `no_claim_or_trace_created=True`; exact cases were:

| Problem | Topic | Replay | Reported/validated | Manual | Promotion/claim/trace |
| --- | --- | --- | --- | --- | --- |
| `P-FRANKL-Q6` | `APPLIED` | `REPLAYED` | `OPEN_REPORTED` / `OPEN_REPORTED` | none | `false / false / false` |
| `P-ARXIV-2601-22401-COLLISION` | `APPLIED` | `DUPLICATE` | `RESOLVED_REPORTED` / `RESOLVED_REPORTED` | `HIGH_RISK_EVENT` | `false / false / false` |
| `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS` | `MANUAL_REVIEW` | `NOT_APPLICABLE` | `OPEN_REPORTED` / `STALE` | `BUDGET_EXHAUSTED` | `false / false / false` |

The archive is therefore intentionally blocked by two manual-review entries. No
`claims.json`, `research-trace.json`, or `trace.json` is created in the temporary
run root.

## Replay and tamper boundaries

`DogfoodArchiveRunner._replay()` reconstructs both topic-observation runners from
the fixed fixtures, checks cursor positions and ArtifactStore counts, rebuilds the
budget, compares the complete blocking queue, and compares the persisted archive
and both state snapshots against a fresh canonical execution. The topic loader
validates input projections, disposition evidence, source/artifact digests,
manual-result linkage, orphan queue closure, duplicate provenance, and cursor chain.

The protected suite includes recomputed-digest mutations for source/fixture/contract
identity, budget, status/provenance/novelty, case set, per-case promotion/claim/trace,
manual queue/result linkage, and malformed/legacy state. A fresh temporary probe at
current HEAD confirmed normal execution/restart and the blocked non-promotion state.

## Acceptance boundary and verdict

| Criterion | Disposition |
| --- | --- |
| Three source-pinned archive cases and exact non-promotion flags | PASS |
| Restart replay, deduplication, budget, manual queue closure | PASS |
| Legacy archive/state recovery fails closed without rewrite | PASS |
| Source bytes/digests and canonical persisted-state replay | PASS |
| Offline/non-proof/non-public boundary | PASS within declared scope |
| Current pushed HEAD readback | PASS (`3353d6a` equals remote) |
| Current contract/binding/checklist identity | PASS (hashes above) |

Verdict: `proposed_state: VERIFIED` for this independent archive-review lane.
The lane has no acceptance authority and does not alter the existing A4 formal
acceptance record. The evidence proves only the bounded offline, source-fixed
archive/state engineering contract; it is not a mathematical proof, live literature
confirmation, production/device evidence, or public-release authorization.
