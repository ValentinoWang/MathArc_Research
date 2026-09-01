# A4/R1/Q1/A5 Acceptance-Chain Identity Audit

- Audit date: 2026-09-01
- Project HEAD: `fe9de3fd86e3670dc3a0c10621afa48fc4740fa8`
- Scope: current source, acceptance evidence, SSOT node states, and the project human acceptance ledger.
- Authority rule: a historical PASS is not current acceptance when its bound source, upstream evidence, node, or human record has changed.

## Findings

1. A4's former acceptance record was bound to `46d924fbfc4daa00eb02d3ffaf06cb17a78be4fe`, while the A4 implementation and tests were subsequently changed. The current A4 evidence now correctly records `acceptance_self_check: partial`, `proposed_state: VERIFIED`, and `formal_acceptance_result: null` in its release record. The current A4 node is `VERIFIED`, not `ACCEPTED`.
2. R1 evidence still describes `EV-R1-ACCEPTED-2` and consumes the old A4 evidence digest `85a3e6335bf8e5c886bef328e87f853c8eadc132a793b55ff39a962caae618dd`; the current A4 evidence digest is `31760d41791f5eab689ebc8a420f57cde4632a4b65789b79f37b7a5e81a13e0`. R1's human run is bound to `95ce4faf...`, not the current HEAD, and its node is now `BLOCKED`.
3. Q1 evidence still proposes `ACCEPTED` and consumes the old R1 evidence digest `073fecdf...`; its node is now `BLOCKED`. The Q1 human ledger entry still says `PASSED`, so the project-level ledger and SSOT node disagree.
4. A5 evidence still proposes `ACCEPTED` from the old Q1 identity and retains the old Q1 node digest `b889b619...`; the current Q1 node digest is `851b6ac813282d7b5df64ec09dd548e31f0056a272ccba960d59fc2a3b373ab8`. A5 is `BLOCKED` in SSOT and `INVALIDATED` in the human ledger, so the evidence is historical only until a new upstream chain is accepted.

## Current SSOT states

| Node | Current state | Interpretation |
| --- | --- | --- |
| A4 | `VERIFIED` | Implementation/review evidence exists; formal acceptance was not performed. |
| R1 | `BLOCKED` | Hard dependency A4 is not accepted; old R1 acceptance cannot unlock Q1. |
| Q1 | `BLOCKED` | Hard dependency R1 is not accepted; old Q1 acceptance cannot unlock A5. |
| A5 | `BLOCKED` | Hard dependency Q1 is not accepted; old A5 source-release decision is invalidated. |

## Verification

The focused source behavior suite was run at the current checkout:

```text
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.13 -m unittest -v \
  tests.test_v02_dogfood_archives tests.test_v02_topic_observation \
  tests.test_v02_regression_evaluation tests.test_v02_calibration_disclosure \
  tests.test_v02_release_decision
```

Result: 58 tests ran; 57 passed and 1 failed. The single failure is
`test_release_decision_pins_current_accepted_q1_artifacts`: its protected
expectation still requires the old Q1 node digest after the node was correctly
changed to `BLOCKED`. This is a useful red identity gate, not evidence of a
current A5 acceptance.

No business source defect was found by this identity audit. The remaining work
is to regenerate the downstream evidence/acceptance records from a fresh A4
acceptance (after A4 P1 repairs), or leave the chain explicitly blocked and
update the static identity gate to assert that blocked state. No Git commit or
remote operation was performed.
