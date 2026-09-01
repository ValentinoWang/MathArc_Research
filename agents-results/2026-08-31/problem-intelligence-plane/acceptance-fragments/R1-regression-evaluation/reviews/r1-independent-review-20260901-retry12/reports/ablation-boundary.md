- Lane: `ablation-boundary`
- Reviewer identity: `r1-ablation-boundary-l3-luna-retry12`
- Wrapper: `/Users/vsiyo/.codex/workers/run-l3.sh`

- Review mode: zero-write.
- Zero-write scope: The retry12 frozen manifest, evaluator, fixture, protected test, contract, evidence, binding, and checklist were read-only inputs. No source, test, contract, evidence, R1, Q1, A5, index, commit, deletion, network, skill, agent, release, or remote action was performed. This report is the only requested write.
- Frozen head: `7da57f155fa488fefb760791fed05013e6a38d10` (verified as `main` HEAD; manifest `frozen_head` and `remote_head` agree).
- Frozen input manifest SHA-256: `452990fe59524a5083360945ed651ec2611049ccb7bdbc6c70ebb28c441afaa7` (all 14 manifest input hashes match).
- Contract protected-test SHA-256: `4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6` (contract, frozen manifest, `R1.json` source identity, and the actual protected test agree).
- Focused verification: `env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q tests.test_v02_regression_evaluation` passed; 7 tests ran, exit 0, `OK`.

- Evaluator and fixture: `RegressionSuite.from_dict` fail-closes the fixed fixture kind/schema, topic, A4 identity, T2 identity, fixture content digest, case order, route order, route/query/source independence, hit/miss/gap labels, and bounded manual minutes. `evaluate()` deterministically recomputes full hits, route-exclusive increments, and leave-one-route-out loss in memory.
- Recomputed result digest: `e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d`. The three fixed cases contain exactly four routes each; duplicate hits are removed from increments, and zero-increment routes are retained.
- Ablation observations: `P-FRANKL-Q6` has full hits `frankl-boundary` and `frankl-structure`, exclusive to Forward Citation and Structural Semantic respectively; `P-ARXIV-2601-22401-COLLISION` has independent Forward Citation, Alias and Equivalence, and Review and Expert Lead hits, with Structural Semantic at zero; `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS` has only the Structural Semantic hit `q6-residual-boundary`. Leave-one-out losses match those exclusive hits.

- P0 findings: none.
- P1 findings: none.

- AC-01: PASS. The fixed fixture has three accepted case IDs and exactly four ordered, independently recorded routes per case.
- AC-02: PASS. Full-route hits, route-only increments, leave-one-route-out losses, hit/miss/gap labels, and bounded manual minutes were deterministically loaded and recomputed; repeated evaluation is equal.
- AC-03: PASS. The protected suite covers fail-closed digest, identity, scope, source, hit, manual-minute, and ablation tampering, and all seven tests pass.
- AC-04: PASS. The evaluator is a passive in-memory path with no `ResearchTrace`, `ClaimStatus`, `authorize`, HTTP, production-state, or public-claim dependency.
- AC-05: PASS for this assigned ablation-boundary lane. This persistent report is bound to the verified retry12 frozen inputs and declares the required zero-write review mode; overall R1 acceptance still requires the separate identity-contract report and aggregate gate.
- AC-06: NOT ASSESSED by this ablation-boundary lane. The separate identity-contract lane must independently verify its different reviewer identity and wrapper on the same frozen input; this report does not substitute for it.

- Limits: Evidence is limited to the local, fixed three-case A4 archive and four-route comparison. It does not establish mathematical proof, external-literature completeness or confirmation, accuracy, recall, statistical performance, generalization, novelty, production behavior, device behavior, public release, or human H-01 acceptance. The fixture reports route hits, misses, gaps, and manual minutes only.
- Lifecycle boundary: No R1 acceptance and no R1/Q1/A5 transition was performed. This report is independent ablation evidence only; current evidence remains `R1=EV-R1-REOPENED-5/ BLOCKED`, `Q1=EV-Q1-REOPENED-2/ BLOCKED`, and `A5=EV-A5-BLOCKED-1/ BLOCKED`.

Verdict: PASS
