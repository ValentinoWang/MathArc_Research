# R1 Ablation Boundary Review

Lane: ablation-boundary
Reviewer identity: r1-ablation-boundary-l3-luna-retry10
Wrapper: /Users/vsiyo/.codex/workers/run-l3.sh
Review mode: zero-write

Frozen head: `359e1e2944ef29d0aee65de7de6e68437b76c94d`
Frozen input manifest: `agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901-retry10/frozen-inputs.json`
Frozen input manifest SHA-256: `9e2bc6cfcf6004f36ed3d6f952979334a1baa86f68baf48833bbcd1b29c83561`

## Zero-write compliance

PASS. All checks before this report write were read-only. No skills, agents, network, release workflow, or remote action was invoked. The only permitted write is this report.

## Exact commands and results

`git rev-parse --show-toplevel && git rev-parse HEAD && git status --short --untracked-files=all`

Result: exit 0; repository root was `/Users/vsiyo/Desktop/创业项目/AI4Math/Project/MathArc_Research`; HEAD matched the frozen head. The pre-write status contained only the six pre-existing campaign input/log/prompt/report-placeholder paths and no assigned report path.

`python3 - <<'PY'` short JSON hash loop over the manifest `inputs` list, comparing each file SHA-256 and `git rev-parse HEAD` to `frozen_head` `PY`

Result: exit 0; manifest SHA-256 was `9e2bc6cfcf6004f36ed3d6f952979334a1baa86f68baf48833bbcd1b29c83561`; all 14/14 manifest input hashes matched; HEAD matched `frozen_head`.

`rg -n -C 2 'protected|SHA-256|sha256|test_v02_regression_evaluation|4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6' agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/acceptance-contract.md`

Result: exit 0; the contract protected-test row pins `tests/test_v02_regression_evaluation.py` to `4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6`, matching the manifest and verified file hash.

`sed -n '1,380p' matharc/v02/regression_evaluation.py`

Result: exit 0; reviewed the 323-line frozen evaluator.

`sed -n '1,120p' agents-results/2026-08-31/problem-intelligence-plane/evidence/r1-fixtures/four-route-regression.json`

Result: exit 0; reviewed the 50-line frozen three-case, four-route fixture.

`env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_regression_evaluation`

Result: exit 0; all 7 tests passed in 0.025s (`OK`): deterministic three-case/four-route ablation, expected outcome bounds, tamper/identity/digest fail-closed behavior, passive import guard, and byte-identical dual-lane replay rejection.

`git diff --check`

Result: exit 0 with no output.

## Scoped review

The evaluator fixes exactly three case IDs and exactly four ordered routes. It validates strict fields, route/query/source uniqueness, fixed A4/T2/topic identities, the fixture content digest, bounded finite manual minutes, and the closed `hit`/`miss`/`gap` outcome set. Evaluation uses route hit-set union, per-route incremental hits, and full-minus-without-route leave-one-out loss, so zero-increment routes remain represented.

The frozen fixture records only local route queries, source IDs, hits, unresolved items, expected status, and manual minutes. The evaluator is passive and in-memory. Its imports contain no authorization, `ResearchTrace`, or `ClaimStatus` dependency and it creates no authorization field. The review makes no claim of external literature confirmation, statistical performance, mathematical proof, production behavior, device behavior, or public release.

## P0/P1 findings

None.

## AC dispositions

| Criterion | Disposition | Basis |
| --- | --- | --- |
| AC-01 | PASS | Frozen fixture and evaluator enforce the three fixed cases with exactly the four ordered independent routes; focused suite passed. |
| AC-02 | PASS | Deterministic full coverage, incremental hits, leave-one-route-out loss, and bounded outcome labels are implemented and covered by the passing focused suite. |
| AC-03 | PASS | Strict identity, field, source, content-digest, manual-minute, and ablation-recalculation rejection paths are present; tamper negative tests passed. |
| AC-04 | PASS | Scoped source review and the passive-import test found no authorization, declaration, `ResearchTrace`, or `ClaimStatus` dependency. |
| AC-05 | PASS | This persistent report supplies the assigned frozen-input ablation-boundary review evidence with the required self-binding metadata and terminal verdict. |
| AC-06 | NOT ASSESSED BY THIS LANE | The separate identity-and-contract review is outside this assignment; its report was not read and this disposition does not substitute for it. |

## Residual limits and boundary

This is a small, fixed, local three-case A4 regression fixture. It does not establish retrieval accuracy, recall, generalization, literature availability, statistical performance, mathematical truth or proof, production or device behavior, or public-release readiness. It does not exercise network retrieval or external services. Human acceptance and the separate identity review remain independent evidence layers.

This report is an ablation-boundary review only. It does not accept R1 and does not transition Q1 or A5.

Verdict: PASS
