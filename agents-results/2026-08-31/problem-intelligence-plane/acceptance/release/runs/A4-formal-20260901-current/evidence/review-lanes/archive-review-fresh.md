# A4 Fresh Archive/State Review

- Review lane: archive/state, read-only
- Run date: 2026-09-01 (Asia/Shanghai)
- Source identity: `main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
- Remote readback: `origin/main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80`
- Contract v2 SHA-256: `4b7ac7ea035d59be7c87fef9867b97529f8b00f68c207d7460963cd625095c84`
- Binding SHA-256: `7b299dff38c8c36b9041c8f121b28dc0b70a6539c894081bd4111dab17b4cc78`
- Checklist SHA-256: `cd57b8e24177664d0796084d81cda6891703a9fe7a6b5a958dbd943cfc180593`
- Boundary: checked-in fixed source bytes, offline archive/state engineering only; no mathematical proof, live literature confirmation, production/device evidence, or public-release authorization
- Write policy: this file only; no implementation, test, SSOT, acceptance-state, or Git mutation

## Findings

### P0

None.

### P1

None within the requested archive/state boundary. Current protected source/test blobs match the v2 contract, the current remote main tip matches local HEAD, and fresh focused execution plus independent restart replay passed.

### P2 / residual

The accepted upstream `evidence/T2.json` records an earlier T2 implementation revision (`87e315c4...` / `55c50f7...`), not the current A4 repair tip. Its fixed fixture contract and source bytes were checked directly here; this lane does not treat the historical T2 source revision as current-HEAD evidence. Release synthesis must bind its own current tuple and T2 dependency explicitly.

The local digest model is not an external trust anchor against a fully compromised host. Fixed artifacts remain offline evidence only.

## Identity and protected-test integrity

Observed SHA-256 values:

| Path | SHA-256 |
| --- | --- |
| `matharc/v02/topic_observation.py` | `16743b6097480044253c50fc8188b65a23062e5f57435361863311b1483a80e1` |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` |
| `evidence/t2-fixtures/three-real-archives.json` | `475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c` |

All four protected test/source hashes match the approved contract v2 values. Contract, binding, and checklist hashes match the requested tuple exactly. `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` both returned the pinned main SHA.

## T2 fixture and contract checks

`evidence/T2.json` was read as the upstream accepted T2 record. Its acceptance matrix covers source-byte/fixture digest binding, distinct historical/current provenance, cursor replay and manual queue, budget reconstruction, tamper fail-closed behavior, and no-claim/no-trace boundaries. The record explicitly leaves live retrieval, mathematical proof review, and separate A4 acceptance unverified.

The checked-in T2 contract currently resolves to `t2-dogfood-archive-contract`, topic `union-closed`, source fixture directory `../s1-fixtures`, and the approved non-claim sentence. The contract SHA and all four pinned source artifact bytes were read and matched; no network retrieval was performed.

## Fresh machine evidence

Command:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/matharc-a4-current-pycache TMPDIR=/tmp python3 -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives
```

Result: exit `0`; `41` tests passed, zero skips, zero failures/errors.

Independent temporary-directory probe:

```text
DogfoodArchiveRunner(tempdir, evidence/s1-fixtures).run()
DogfoodArchiveRunner(tempdir, evidence/s1-fixtures).run()
```

Result: first `replayed=False`; restart `replayed=True`; `archive_blocked=True`; two deterministic manual queue entries (`manual-331c33be322f606d88588305`, `manual-ab63a3b2b7aa1769c73dbef8`); budget digest `efdf4e18af10228e0706db1ee91b896ead57982e132a4e5315faf79860eb4b45`; `no_claim_or_trace_created=True`; no claim/trace files in the temporary root.

Case readback:

| Problem | Topic | Replay | Reported/validated | Manual | Promotion/claim/trace |
| --- | --- | --- | --- | --- | --- |
| `P-FRANKL-Q6` | `APPLIED` | `REPLAYED` | `OPEN_REPORTED` / `OPEN_REPORTED` | none | `false / false / false` |
| `P-ARXIV-2601-22401-COLLISION` | `APPLIED` | `DUPLICATE` | `RESOLVED_REPORTED` / `RESOLVED_REPORTED` | `HIGH_RISK_EVENT` | `false / false / false` |
| `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS` | `MANUAL_REVIEW` | `NOT_APPLICABLE` | `OPEN_REPORTED` / `STALE` | `BUDGET_EXHAUSTED` | `false / false / false` |

The focused tests include recomputed-digest disposition/status tampering, cross-field projection swaps, manual-result/queue linkage, orphan queue closure, legacy 1.0/1.1 preservation and fail-closed recovery, case-set and promotion/claim/trace mutations, contract metadata immutability, budget/source/fixture drift, and archive replay.

## Verdict

`VERIFIED` for this independent archive/state review lane only.

This result does not alter A4/T2 state, does not accept the A4 fragment, and does not authorize release, publication, mathematical conclusions, external literature claims, or production/device behavior. The historical T2 implementation revision noted above remains a release-synthesis binding concern, not a failure of the current fixed-byte archive/state execution verified here.
