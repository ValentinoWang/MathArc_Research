- Lane: `ablation-boundary`
- Reviewer identity: `r1-ablation-boundary-main-ea39bc2-luna`
- Wrapper: `/Users/vsiyo/.codex/workers/run-l3.sh`

Review mode: zero-write. No source, test, contract, evidence, SSOT, human-acceptance, release, network, remote, Q1, or A5 files were modified by this review; the only write is this report.

Frozen input manifest SHA-256: 8b61173e4ffd5f53deede4889f4bd026941294b71d6503c0ec84630492d810a4

Frozen-input verification: all 13 paths in `frozen-inputs.json` matched their declared SHA-256 values, including the R1 implementation, protected regression/calibration/release tests, four-route fixture, A4/R1/Q1/A5 evidence, v9 acceptance contract, R1 SSOT node, and human binding/checklist. The checkout HEAD and frozen/remote heads are `ea39bc29058aea2b940ac9f947e8236d601fb5a7`.

Bounded test evidence:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_regression_evaluation`: 7 tests passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile matharc/v02/regression_evaluation.py tests/test_v02_regression_evaluation.py`: passed.
- The protected tests cover AC-01 through AC-05, including three-case/four-route cardinality and ordering, deterministic full/incremental/leave-one-out calculations, tamper and identity/content digest rejection, hit/miss/gap and manual-minute bounds, passive non-authorization behavior, and v9 byte-identical hard-link dual-report rejection.

Ablation inspection: `RegressionSuite.from_dict(...).evaluate()` loaded the frozen fixture and produced deterministic digest `e6fdf4d1eb36b8179f6fcd6fd17e54b0a60332caa7a3d16115386fb85c52f13d`. All three accepted A4 case IDs were present in contract order, each with exactly four independent routes. Full hit sets, route-exclusive increments, and leave-one-route-out losses recomputed consistently; zero-increment routes were retained. Outcomes were closed to `hit`, `miss`, and `gap`, and manual minutes were finite and within 0..240 (12, 28, and 7 minutes).

Boundary review: the evaluator is passive and does not import or reference `ResearchTrace`, `ClaimStatus`, `authorize`, HTTP/network access, production state, statistical metrics, or external literature. The R1 evidence remains `BLOCKED` pending two durable independent PASS reports; this lane does not claim R1 acceptance and does not alter that state. Known limitations remain the fixed three-case A4 fixture and the contract exclusions for mathematical proof, live retrieval, production/device behavior, and statistical generalization.

No P0/P1 defect was found in AC-01..AC-05 or the non-promotion boundary under the frozen inputs and bounded checks.

Verdict: PASS
