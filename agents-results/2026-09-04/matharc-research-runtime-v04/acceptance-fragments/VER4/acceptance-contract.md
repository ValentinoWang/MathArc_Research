# Acceptance Contract: VER4

- Task ID: VER4
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 证据转换负责人
- Approval evidence: TBD
- Request source: item VER4
- SSOT node: VER4
- SSOT path: .ssot/nodes/VER4.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ver4
- AC budget: 2
- Baseline identity: ssot-input.json#items[VER4]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching evidence-record drives item VER4 (unspecified dimension) through the interface declared for VER4.

## Problem

Item VER4 exists because the interface declared for VER4 does not yet satisfy the acceptance seeds registered for it, leaving evidence-record incomplete.

## Expected outcome

After item VER4 lands, the interface declared for VER4 satisfies every acceptance seed below and evidence-record reflects that behavior.

## Non-goals

Item VER4 covers only the interface declared for VER4 and evidence-record as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches evidence-record for item VER4
When the flow defined by the interface declared for VER4 executes
Then every acceptance seed for item VER4 holds
```

## Exception paths

If the interface declared for VER4 fails for item VER4, evidence-record must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item VER4, the interface declared for VER4 must continue to satisfy every acceptance seed below on every call; evidence-record must never show a state the seeds forbid.

## Data impact

Item VER4 constrains any create, update, or delete reachable through the interface declared for VER4; only the acceptance seeds below define what data changes are permitted for evidence-record. Node-specific data assertions: 在 matharc/v02/verification_bridge.py 中只将通过 VerifierReceipt 的候选转换为 EvidenceRecord | 在 tests/test_candidate_evidence_conversion.py 中证明候选转换不会自动调用 ResearchTrace.promote_claim()

## Permissions

Item VER4 is owned by 证据转换负责人; access to the interface declared for VER4 and evidence-record follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER4: the thresholds and failure evidence for the interface declared for VER4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/integration-contract | 在 matharc/v02/verification_bridge.py 中只将通过 VerifierReceipt 的候选转换为 EvidenceRecord | Integration | Automatic | Yes |
| AC-02 | behavior | none | machine/unit | 在 tests/test_candidate_evidence_conversion.py 中证明候选转换不会自动调用 ResearchTrace.promote_claim() | Unit | Automatic | Yes |

## Human acceptance

Item VER4 is fully determined by its acceptance seeds; outcomes for the interface declared for VER4 on evidence-record are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item VER4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/verification_bridge.py | Automatic | Yes |
| AC-02 | Unit | tests/test_candidate_evidence_conversion.py | Automatic | Yes |

## Exploratory testing

Probe evidence-record for item VER4 under retry, interruption, and boundary-value inputs against the interface declared for VER4, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item VER4 reverts the change to the interface declared for VER4; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER4: review risks specific to evidence-record and record any open decision.
