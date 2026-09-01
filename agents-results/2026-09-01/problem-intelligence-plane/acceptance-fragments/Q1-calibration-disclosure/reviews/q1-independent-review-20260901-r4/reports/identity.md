# Q1 Identity Review

## Findings

- No identity, hash, pointer, contract, or release-boundary findings.
- The frozen campaign is `FROZEN_PENDING_REVIEWS`; Q1 remains a `CANDIDATE`. This PASS covers identity integrity only and does not establish formal Q1 acceptance or public-release authority.

## Hashes

All frozen manifest SHA-256 values match the current files:

| Input | SHA-256 | Result |
| --- | --- | --- |
| `evidence/Q1.json` | `ec5d31e829a5b2d161fd992f78fedf27e88eaad60f069275a32f3ad608b36876` | PASS |
| `evidence/q1-fixtures/uncalibrated-disclosure-policy.json` | `566d86da2d3ab3f9a44e380f38ed11858d021a2ac029517dd8f21d8a7e82f0b0` | PASS |
| `matharc/v02/calibration_disclosure.py` | `d7ac4010b960bacfb601a0670a0c1c45ef7da0be049839fd551b8a69d5b79bc7` | PASS |
| `tests/test_v02_calibration_disclosure.py` | `63ea5244fac913208ff3e5ffa5d98cee7ffd68a62958c45b4c3c67d853912ced` | PASS |
| `acceptance/human/Q1-calibration-disclosure/handoff.json` | `f1c0d3eea13b38f28e99053cc39d24d4475f79b3575106bcea2cfab0c5bde6b8` | PASS |
| `acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md` | `fdfbc542fe28f016d41fc8e013c086a20ca728f4b95a2cf79854ab6e83860eb0` | PASS |

Supplemental v6 and run identities also match their recorded bindings:

- `binding.md`: `51b84fe5fedf7c2d4249a72019ae4abd0c49cedc4a30b0726b3fad2cb3431fd1`.
- `checklist.md`: `3cf9cf31c24e20c7d3428e47933a928c6f0d1d5f7ce88b1fd2971c90e12f132d`.
- `q1c002/result.md`: `59b1cf182fedac14186dee45b789fba49ebd7a848d983259154c7105a9dde7af`.
- `q1h003/result.md`: `1a26421b8c3c66a27d0ef15b57f8571f24e80c2f4911b92a64097e6bcf761a5c`.
- Q1 source identity retains R1 evidence `effd9130a75b8e603f8d54f6ef37c511bc0ebc2de635f256353ac33f507b858a`, R1 fixture `9b7fb5c0e63cecde14ee658b4eac7e5b26196ee511ea8a6bbddcfa3dceec0429`, R1 fixture content `7ac8f8ef52b7cb23f77d2150b23975f9f3f0cfcdc8e12005ea5c99f925fe1b6f`, and Q1 policy digest `0705e8af012c36afc85c5af61d9a473ec8f3d369f877450acc9587be82281252`.

## Identity and pointers

- `git rev-parse HEAD` is `bd4ecbecd699d0ea8177ff944d62b4cbcfee6170`; branch is `main`.
- Frozen `candidate.q1_evidence` resolves to `agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json`.
- Q1 evidence points to the exact machine run `agents-results/2026-09-01/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance/machine/unit/runs/20260901T105300Z-local-q1c002/result.md` and human run `acceptance/human/Q1-calibration-disclosure/runs/20260901T105224Z-local-q1h003/result.md`.
- Handoff machine evidence points to q1c002 and records the matching result SHA. q1c002 and q1h003 both report `Status: PASS`, `Contract version: 6`, and the non-public boundary.

## Contract and boundary

- Contract status is `APPROVED`, version `6`, with locked protected-test baseline.
- Binding is `ACTIVE`; checklist is approved; both bind to the v6 contract and required blocking role `研究负责人`.
- Handoff `contract_version` is `6`; its contract, binding, checklist, and machine-result hashes match.
- `public_release_allowed` is `false` in the frozen manifest and policy fixture; Q1 records are `UNCALIBRATED` and `NOT_READY`.
- Pre-existing dirty worktree changes were preserved and are outside this identity review; no broad historical logs or other tasks were inspected.

## Commands and results

- `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`: exit 0; 15 tests passed.
- `git diff --check`: exit 0.
- Frozen JSON, evidence-pointer, release-flag, and v6 handoff assertions: all exit 0.

Verdict: PASS
