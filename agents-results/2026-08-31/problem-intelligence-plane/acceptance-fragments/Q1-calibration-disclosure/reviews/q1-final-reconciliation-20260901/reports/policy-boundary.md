# Q1 Final Policy-Boundary Reconciliation

- reviewer_identity: `q1-final-policy-boundary-codex-20260901`
- review_mode: zero-write independent review; this report is the sole artifact written by this reviewer.
- verdict: **FAIL**

## Files and hashes read

| File | SHA-256 | Result |
| --- | --- | --- |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json` | `600153703b7e990e4db246d5a65fd06b2d1920d9f6a82cae1e470bb67a3d94be` | Read |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/q1-fixtures/uncalibrated-disclosure-policy.json` | `f519e824ef92274ae2f9f3749ef84dc71beece3fb1c4523c98a765db98cf17bf` | Read |
| `matharc/v02/calibration_disclosure.py` | `bd5ead52e02730203ae0e1a45405c9eeaedc74b22d9fa616f417fdc6f3cb5e83` | Read |
| `tests/test_v02_calibration_disclosure.py` | `7a38001d211c2b8ef5b6b45e8f8fa87f7b0ce9785559cc475eb511d250af5026` | Read |
| `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md` | `e2db06e4a9d863bc1963e19d5aac1c17bc070adb84df45d95c41ac1df39efc73` | Read |
| `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/reviews/q1-independent-review-20260901-reaccept/frozen-inputs.json` | `359984a62589023373cff985a5e1b1ad78cc25335e5ea0ec28a78e913f0dca8b` | Supplemental identity read |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/R1.json` | `672a4c439c3b7de7bfebe2e09576daa0fcefd731d874c3a48d3671d7ba625c71` | Supplemental source-identity read |
| `agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json` | `04839d8177b10b4b7749ee953b6bae0771db3ede63a79708ed9da64e6ce1b75c` | Supplemental source-identity read |

## Findings

1. **Blocking: the final-review frozen input manifest does not bind the current Q1 candidate.** The manifest pins `Q1.json` to `6e27b1665ef04f8bd4481fbd5e20388114799c9bad8b735224b5b19fd13cd197`; the current file is `600153703b7e990e4db246d5a65fd06b2d1920d9f6a82cae1e470bb67a3d94be`. Therefore, the prior independent policy-boundary PASS is not evidence for this current candidate. The manifest must be regenerated and independently reviewed before a final PASS can be claimed.

2. **Blocking: the asserted non-recomputable policy-digest guard is not fail closed against a fixture consumer who recomputes the digest.** `CalibrationDisclosurePolicy.from_dict` compares a supplied digest with `digest_json` of the supplied content, but it has no immutable expected Q1 policy digest or byte digest. A no-write in-memory probe changed the first record's `predicted_difficulty` from `HIGH` to `LOW`, recomputed the public canonical digest with `matharc.v02.schema.digest_json`, and `from_dict` accepted the modified policy. The protected test only changes the field without recomputing the digest, so its title and assertion at `tests/test_v02_calibration_disclosure.py:85` do not demonstrate the claimed property. This leaves AC-03's digest-tampering fail-closed requirement and the contract's byte-locked policy expectation unproven.

3. **Confirmed but insufficient:** the current fixture preserves all three required `UNCALIBRATED` and `NOT_READY` values, each required disclosure limit, and `public_release_allowed: false`. The implementation rejects direct `CALIBRATED`, `PUBLIC_READY`, missing-limit, source-identity, unknown-field, and unrecomputed-digest mutations. The protected Q1 suite passed locally: `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure` -> `7 passed`.

## Required repair and re-review boundary

Bind the loader or its mandatory acceptance entry point to an immutable candidate identity (at minimum the declared policy byte SHA-256 and canonical policy digest from independently pinned Q1 evidence), then add a negative test that changes a permitted field, recomputes the digest, and proves rejection. Regenerate the frozen-input manifest after the repaired candidate is fixed, then obtain a fresh independent policy-boundary review.

## Explicit non-proof and non-public boundary

This review does not establish mathematical proof, external-literature verification, reported-open-status confirmation, novelty acceptance, calibration quality, accuracy, recall, statistical performance, generalization, production or device behavior, human H-01 acceptance, or public-release authorization. Regardless of the two failures above, the reviewed Q1 fixture and implementation do not grant public release; any public-release decision remains exclusively with the independent A5 process.
