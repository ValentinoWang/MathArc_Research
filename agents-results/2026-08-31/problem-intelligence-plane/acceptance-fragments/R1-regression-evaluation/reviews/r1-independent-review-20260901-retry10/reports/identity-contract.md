# R1 Identity-Contract Review

- Lane: `identity-contract`
- Reviewer identity: `r1-identity-contract-l4-sol-retry10`
- Wrapper: `/Users/vsiyo/.codex/workers/run-l4.sh`
- Review mode: `zero-write`
- Frozen head: `359e1e2944ef29d0aee65de7de6e68437b76c94d`
- Frozen input manifest SHA-256: `9e2bc6cfcf6004f36ed3d6f952979334a1baa86f68baf48833bbcd1b29c83561`
- Zero-write compliance: PASS. Before this report, no project file was written. No skills, agents, network, release workflows, remote actions, or peer-report reads were used. This is the sole assigned write.

## Frozen identity and lifecycle

- Manifest integrity: PASS. git rev-parse HEAD matched the declared frozen head, and all 14 of 14 manifest-listed input files matched their declared SHA-256 values.
- A4 identity and scope: PASS. The evidence is EV-A4-ACCEPTED-2 with status ACCEPTED; its boundary is offline, fixed-source, non-mathematical-proof, and non-public-release.
- R1 lifecycle: PASS as an observed blocked state. EV-R1-REOPENED-5 has acceptance_self_check=blocked and BLOCKED_PENDING_TWO_DURABLE_PASS_REPORTS; R1 remains blocked pending this pair of durable independent reports.
- Downstream lifecycle: PASS as an observed blocked state. Q1 and A5 both remain BLOCKED; A5 also records BLOCKED_UPSTREAM_Q1 and no release or source-delivery authorization.
- R1 SSOT node: PASS. execution_state is BLOCKED.
- Contract bindings: PASS. Contract version 9, the acceptance contract, human binding, human checklist, and protected regression test all match the frozen manifest and their cross-references. The verified artifact hashes are:

| Artifact | SHA-256 |
| --- | --- |
| R1 acceptance contract | 6faa8116278e8fe64d26f39bfcd0277d6dfac74fea0aa74a11aacb8046fd85ee |
| Human binding | ec6336739a676253620abeb24c0df22fefec99796ad113390b1f161b428c874b |
| Human checklist | d7a89e055f43e192d899b86f9acf707457abad034db8a29094d660108afffdde |
| Protected test | 4afbed63fc11fa3133999e3f2d90683fa6663d62ed60791674362725a5dbcdc6 |

## Commands and results

The following are the exact verification commands and observed results.

~~~sh
env PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import hashlib
import json
import pathlib
import subprocess
import sys

manifest_path = pathlib.Path('agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/reviews/r1-independent-review-20260901-retry10/frozen-inputs.json')
manifest = json.loads(manifest_path.read_text())
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
print('HEAD {} expected {} {}'.format(head, manifest['frozen_head'], 'PASS' if head == manifest['frozen_head'] else 'FAIL'))
print('MANIFEST_SHA256 {}'.format(hashlib.sha256(manifest_path.read_bytes()).hexdigest()))
failures = 0
for item in manifest['inputs']:
    actual = hashlib.sha256(pathlib.Path(item['path']).read_bytes()).hexdigest()
    result = 'PASS' if actual == item['sha256'] else 'FAIL'
    print('{} {} expected {} {}'.format(item['path'], actual, item['sha256'], result))
    failures += actual != item['sha256']
sys.exit(failures)
PY
~~~

Result: exit 0; frozen HEAD matched; MANIFEST_SHA256 was 9e2bc6cfcf6004f36ed3d6f952979334a1baa86f68baf48833bbcd1b29c83561; 14/14 inputs passed.

~~~sh
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests.test_v02_regression_evaluation tests.test_v02_calibration_disclosure tests.test_v02_release_decision
~~~

Result: exit 0; 21 tests ran, 0 failures, 0 errors; OK.

~~~sh
git diff --check
~~~

Result: exit 0; no output.

## P0/P1 findings

None in the assigned identity-contract lane. No frozen-input hash drift, identity mismatch, contract-binding mismatch, or lifecycle contradiction was observed. The blocked R1 state is the required pending-pair state, not a finding.

## AC-01 through AC-06 dispositions

| Criterion | Disposition |
| --- | --- |
| AC-01 | PASS - The frozen fixture and passing protected tests retain three fixed cases and exactly four ordered independent routes per case. |
| AC-02 | PASS - Full coverage, route increments, leave-one-route-out loss, and bounded hit/miss/gap results are deterministic under the protected tests. |
| AC-03 | PASS - Identity, digest, range, source, manual-minute, and ablation tampering are covered by fail-closed negative tests. |
| AC-04 | PASS - The implementation is passive and the protected static check finds no ResearchTrace, ClaimStatus, authorize, or network dependency. |
| AC-05 | PASS at the lane-local contract/gate layer - The frozen contract requires a durable independent zero-write ablation PASS report; pair completion remains blocked and is not asserted here. |
| AC-06 | PASS at the lane-local identity layer - This report binds its lane, reviewer identity, wrapper, frozen inputs, zero-write mode, and terminal verdict; the second independent report is still required. |

## Residual limits

- Evidence is local source-level evidence over the fixed three-case/four-route fixture only.
- This review does not establish mathematical proof or theorem acceptance, external literature or open-status confirmation, novelty, calibration quality, accuracy, recall, statistical performance, generalization, production/deployed/device behavior, monitoring, or public communication.
- No remote reference readback was performed, and the peer report was intentionally not read. Pair-level R1 acceptance and the dependent human acceptance remain pending.

## Boundary

This report does not accept R1 or transition Q1/A5.

Verdict: PASS
