# Q1 Independent Identity-Contract Review

- Lane: `identity-contract`
- Reviewer identity: `q1-identity-contract-r1-accepted-3-sol-l4-r2`
- Wrapper: `/Users/vsiyo/.codex/workers/run-l4.sh` (available; focused commands were executed directly under the same local reviewer environment)
- Review mode: `zero-write`
- Frozen implementation base / observed HEAD: `bd4ecbecd699d0ea8177ff944d62b4cbcfee6170`
- Frozen inputs SHA-256: `7a63f8f71dfb5287d57205ca1f450e3112ce5798fb2bdb7b38de24b35903786b`

## Scope and boundary

This is an independent, read-only identity/contract review of the frozen Q1
candidate. It does not establish formal Q1 acceptance, mathematical proof,
external literature or open-status confirmation, novelty, calibration or
statistical performance, production/device behavior, or public-release
authorization. The sole permitted write is this report.

## Identity checks

The observed `HEAD` matches the frozen `implementation_base`. Recomputed
candidate hashes match the frozen inputs:

| Artifact | SHA-256 | Result |
| --- | --- | --- |
| Q1 evidence | `d9418a75e2ff99388e1c97f5e9bcefd87f617ca363e9f4a1a77b7899272a69d5` | PASS |
| Q1 policy fixture | `566d86da2d3ab3f9a44e380f38ed11858d021a2ac029517dd8f21d8a7e82f0b0` | PASS |
| Q1 implementation | `d7ac4010b960bacfb601a0670a0c1c45ef7da0be049839fd551b8a69d5b79bc7` | PASS |
| protected Q1 test | `63ea5244fac913208ff3e5ffa5d98cee7ffd68a62958c45b4c3c67d853912ced` | PASS |

The candidate is `EV-Q1-CANDIDATE-1`, consumes `EV-R1-ACCEPTED-3`, and remains
`CANDIDATE`/non-public. The fixture parses to three ordered records, all
`UNCALIBRATED` and `NOT_READY`, with policy digest
`0705e8af012c36afc85c5af61d9a473ec8f3d369f877450acc9587be82281252` and
`public_release_allowed=false`. The current Q1 SSOT node is `READY` with
`write_authority: evidence-only` and `side_effect_class: none`.

## Commands and terminal results

1. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`
   -> exit `0`; `Ran 15 tests`; `OK`.
2. A read-only Python identity/policy consistency probe recomputed the frozen
   manifest, candidate artifact hashes, Q1 status, consumed R1 identity,
   policy digest, record count/statuses, and SSOT node state -> exit `0`; all
   reported values above matched.
3. `git diff --check` -> exit `0`; no output.

## Blocking finding

The approved Q1 acceptance contract is not identity-consistent with the frozen
candidate: `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md`
declares the protected test SHA-256 as
`e511c5a26eb05b5be81f6e2f7c74a7c48f685f94e67a64729316678a0353ce57`, while
the actual protected test, frozen-inputs, and Q1 evidence all identify it as
`63ea5244fac913208ff3e5ffa5d98cee7ffd68a62958c45b4c3c67d853912ced`.
The contract also retains baseline identity `origin/main@20d41af...` while
the frozen candidate implementation base is `bd4ecbec...`. Until the approved
contract is re-bound or otherwise reconciled to the frozen candidate, the
identity-contract gate cannot be considered closed.

No source, test, SSOT, evidence, acceptance binding, or existing report was
modified by this review. Q1 remains a candidate and no release is authorized.

Verdict: FAIL
