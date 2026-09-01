# Q1 Independent Identity-Contract Review

## Findings

- P1: `agents-results/2026-08-31/problem-intelligence-plane/evidence/Q1.json` still binds its `machine_acceptance_run` to `20260901T103800Z-local-q1c001/result.md` (SHA-256 `4a48b309c7a6220655de808dcd7d41e771727b44594216276ce4a890a39a69d8`) and its `human_acceptance_result` to `20260901T103900Z-local-q1h001/result.md` (SHA-256 `d96d1b85a7d38931ba6584eaf12e5d46b96817ea85e0c6eac36a189ca697ba28`). Both results declare contract version `5`, while the current approved Q1 contract, active binding, and checklist are version `6` (contract SHA-256 `fdfbc542fe28f016d41fc8e013c086a20ca728f4b95a2cf79854ab6e83860eb0`, binding SHA-256 `51b84fe5fedf7c2d4249a72019ae4abd0c49cedc4a30b0726b3fad2cb3431fd1`, checklist SHA-256 `3cf9cf31c24e20c7d3428e47933a928c6f0d1d5f7ce88b1fd2971c90e12f132d`). Fresh version-6 results exist (`q1c002`, SHA-256 `59b1cf182fedac14186dee45b789fba49ebd7a848d983259154c7105a9dde7af`; `q1h003`, SHA-256 `1a26421b8c3c66a27d0ef15b57f8571f24e80c2f4911b92a64097e6bcf761a5c`) and are listed in the affected acceptance indexes, but Q1 evidence still points to the version-5 runs. In addition, `acceptance/human/Q1-calibration-disclosure/handoff.json` is stale at `contract_version: 4`, with file SHA-256 `1c7612bfab8053a9d8238b5c527b3d5e83c42190ff11d3de8026f9344e961c48`, contract SHA `38cacfefc654acf2b5d5cb9a54e827a5fe83e54937fe957ae4e752b941ecd1fb`, binding SHA `dccf8d6f09c99f682ece450789cb59a27e8e78ec340a4619fed1f5faa6bad271`, checklist SHA `0a25e57af95eafe3093db314eb720303bda3d6d5d6737ca62d8e44fbcbf77e81`, and an obsolete machine run/source identity. The candidate is therefore not identity-closed for formal Q1 acceptance until Q1 evidence and handoff are rebound to the current version-6 run identities.

No P0 source or policy-boundary finding was observed. The implementation and frozen policy identities below are internally consistent.

## Review Identity and Boundary

- Reviewer identity: `q1-identity-contract-r2-luna`
- Lane: `identity-contract`
- Campaign: `q1-independent-review-20260901-r2`
- Frozen manifest: `agents-results/2026-09-01/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/reviews/q1-independent-review-20260901-r2/frozen-inputs.json`
- Frozen manifest SHA-256: `ea1519d44ae6cd2917435d492c9979c41dbe6f8d73535c5ef96da8df9b25a38c`
- Declared/required wrapper: `/Users/vsiyo/.codex/workers/run-l3.sh`
- Wrapper execution identity: the observed `run-l3.sh` invocation used `gpt-5.6-luna` with reasoning effort `max`; the wrapper is present and executable.
- `zero_write=true`: this report is the only file written by this review. Source, tests, SSOT, evidence, acceptance records, indexes, git state, and remote state were not modified.
- Observed HEAD: `bd4ecbecd699d0ea8177ff944d62b4cbcfee6170`, matching the frozen candidate implementation base.

This is review evidence only. It cannot formally accept Q1, transition Q1 to A5, authorize A5, or authorize public release.

## Inspected Hashes

| Artifact | SHA-256 |
| --- | --- |
| Frozen input manifest | `ea1519d44ae6cd2917435d492c9979c41dbe6f8d73535c5ef96da8df9b25a38c` |
| Q1 evidence | `d9418a75e2ff99388e1c97f5e9bcefd87f617ca363e9f4a1a77b7899272a69d5` |
| R1 evidence | `effd9130a75b8e603f8d54f6ef37c511bc0ebc2de635f256353ac33f507b858a` |
| R1 fixture | `9b7fb5c0e63cecde14ee658b4eac7e5b26196ee511ea8a6bbddcfa3dceec0429` |
| R1 fixture content digest in source identity | `7ac8f8ef52b7cb23f77d2150b23975f9f3f0cfcdc8e12005ea5c99f925fe1b6f` |
| Q1 policy fixture | `566d86da2d3ab3f9a44e380f38ed11858d021a2ac029517dd8f21d8a7e82f0b0` |
| Q1 implementation | `d7ac4010b960bacfb601a0670a0c1c45ef7da0be049839fd551b8a69d5b79bc7` |
| Protected Q1 test | `63ea5244fac913208ff3e5ffa5d98cee7ffd68a62958c45b4c3c67d853912ced` |
| Candidate `implementation_base` | `bd4ecbecd699d0ea8177ff944d62b4cbcfee6170` |
| Q1 policy canonical digest | `0705e8af012c36afc85c5af61d9a473ec8f3d369f877450acc9587be82281252` |
| Q1 acceptance contract (latest) | `fdfbc542fe28f016d41fc8e013c086a20ca728f4b95a2cf79854ab6e83860eb0` |
| Q1 active human binding | `51b84fe5fedf7c2d4249a72019ae4abd0c49cedc4a30b0726b3fad2cb3431fd1` |
| Q1 active human checklist | `3cf9cf31c24e20c7d3428e47933a928c6f0d1d5f7ce88b1fd2971c90e12f132d` |
| Q1 handoff (stale) | `1c7612bfab8053a9d8238b5c527b3d5e83c42190ff11d3de8026f9344e961c48` |
| Referenced machine result `q1c001` (version 5) | `4a48b309c7a6220655de808dcd7d41e771727b44594216276ce4a890a39a69d8` |
| Current machine result `q1c002` (version 6) | `59b1cf182fedac14186dee45b789fba49ebd7a848d983259154c7105a9dde7af` |
| Referenced human result `q1h001` (version 5) | `d96d1b85a7d38931ba6584eaf12e5d46b96817ea85e0c6eac36a189ca697ba28` |
| Current human result `q1h003` (version 6) | `1a26421b8c3c66a27d0ef15b57f8571f24e80c2f4911b92a64097e6bcf761a5c` |
| Q1 SSOT node | `01f0e276bb336be31a7d5f975bb655c0ce717a5e9cce69acdf678738a7dfb7c3` |
| Q1 SSOT execution contract | `bea478adc7da2f5f21c01990a2bcf6820ac4b469f7a131d1e9552f527dd7c31b` |

Q1 evidence is `EV-Q1-CANDIDATE-1`, consumes `EV-R1-ACCEPTED-3`, and declares `CANDIDATE` for both acceptance record and proposed state. Its source identity matches the observed R1 evidence/fixture, policy fixture, implementation, and protected-test bytes. The policy digest is `0705e8af012c36afc85c5af61d9a473ec8f3d369f877450acc9587be82281252`.

## Contract and Policy Checks

- The policy is bound to topic `union-closed` and exactly three records in the required order: `P-FRANKL-Q6`, `P-ARXIV-2601-22401-COLLISION`, `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS`.
- All records are `UNCALIBRATED` and `NOT_READY`; scientific priority remains separate (`HIGH`, `HIGH`, `MEDIUM`).
- Every record has the complete unique sorted limits `NO_MATHEMATICAL_PROOF`, `NO_NOVELTY_ACCEPTANCE`, `NO_OPEN_STATUS_CONFIRMATION`, `NO_PUBLIC_RELEASE`, and `NO_STATISTICAL_PERFORMANCE`; `public_release_allowed` is exactly `false`.
- The loader is a passive local value object using standard-library modules plus the local digest helper. Static source checks found no network, literature, authorization, novelty-audit, proof, or claim-status dependency.
- In-memory mutation checks rejected missing, duplicate, and unsorted limits, missing/unknown fields, duplicate or reordered cases, status/topic drift, public-release escalation, and digest tampering. A recomputed public digest over a mutated payload was also rejected.
- The current Q1 acceptance contract is version `6`, status `APPROVED`, with test baseline `LOCKED`; the active binding/checklist are version `6`, and the protected-test binding matches `63ea5244fac913208ff3e5ffa5d98cee7ffd68a62958c45b4c3c67d853912ced`.
- The Q1 node and execution contract agree on node `Q1`, semantic key, `READY`, `evidence-only`, `side_effect_class: none`, `candidate_identity_policy: none`, hard dependency `R1`, and local evidence output.

## Commands and Results

1. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v tests.test_v02_calibration_disclosure tests.test_v02_regression_evaluation`
   - exit `0`; `Ran 15 tests`; `OK`.
2. Read-only in-memory fail-closed mutation probe
   - exit `0`; `mutation_probe=PASS`.
3. `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m py_compile matharc/v02/calibration_disclosure.py tests/test_v02_calibration_disclosure.py`
   - exit `0`; no output.
4. `git diff --check`
   - exit `0`; no output.

The current version-6 machine result `q1c002` and human H-01 result `q1h003` both report `PASS`, but the Q1 evidence pointer remains on the older version-5 results described in P1, and the handoff remains version 4. H-01 and machine results do not by themselves establish formal Q1 acceptance.

## AC Disposition and Residual Risk

| Criterion | Disposition |
| --- | --- |
| AC-01 | PASS for source identity, topic, three records/order, and R1 fixture binding |
| AC-02 | PASS for uncalibrated status and separate priority/readiness |
| AC-03 | PASS for tested fail-closed identity, field, status, limit, byte, and digest drift |
| AC-04 | PASS for passive, local, non-public boundary |
| Formal acceptance chain | FAIL/P1 pending Q1 evidence and handoff rebinding to current version-6 machine and human runs |

Mathematical proof, external literature retrieval, reported-open status confirmation, novelty acceptance, calibration/statistical performance, production/device behavior, and public-release authorization remain unverified and outside this lane. No production monitoring or rollback control applies to this local policy artifact. Existing dirty worktree changes were preserved.

Verdict: FAIL
