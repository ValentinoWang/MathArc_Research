# Acceptance Contract: VER1

- Task ID: VER1
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 候选身份负责人
- Approval evidence: TBD
- Request source: item VER1
- SSOT node: VER1
- SSOT path: .ssot/nodes/VER1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ver1
- AC budget: 2
- Baseline identity: ssot-input.json#items[VER1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching candidate-envelope drives item VER1 (unspecified dimension) through the interface declared for VER1.

## Problem

Item VER1 exists because the interface declared for VER1 does not yet satisfy the acceptance seeds registered for it, leaving candidate-envelope incomplete.

## Expected outcome

After item VER1 lands, the interface declared for VER1 satisfies every acceptance seed below and candidate-envelope reflects that behavior.

## Non-goals

Item VER1 covers only the interface declared for VER1 and candidate-envelope as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches candidate-envelope for item VER1
When the flow defined by the interface declared for VER1 executes
Then every acceptance seed for item VER1 holds
```

## Exception paths

If the interface declared for VER1 fails for item VER1, candidate-envelope must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item VER1, the interface declared for VER1 must continue to satisfy every acceptance seed below on every call; candidate-envelope must never show a state the seeds forbid.

## Data impact

Item VER1 constrains any create, update, or delete reachable through the interface declared for VER1; only the acceptance seeds below define what data changes are permitted for candidate-envelope. Node-specific data assertions: 在 matharc/v02/candidate_envelope.py 中定义不可变 CandidateEnvelope 身份摘要 | 在 tests/test_candidate_identity.py 中证明任务、源码、评价器、种子、预算或产物变化都会改变候选身份

## Permissions

Item VER1 is owned by 候选身份负责人; access to the interface declared for VER1 and candidate-envelope follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER1: the thresholds and failure evidence for the interface declared for VER1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/unit | 在 matharc/v02/candidate_envelope.py 中定义不可变 CandidateEnvelope 身份摘要 | Unit | Automatic | Yes |
| AC-02 | behavior | none | machine/integration-contract | 在 tests/test_candidate_identity.py 中证明任务、源码、评价器、种子、预算或产物变化都会改变候选身份 | Integration | Automatic | Yes |

## Human acceptance

Item VER1 is fully determined by its acceptance seeds; outcomes for the interface declared for VER1 on candidate-envelope are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item VER1; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/candidate_envelope.py | Automatic | Yes |
| AC-02 | Integration | tests/test_candidate_identity.py | Automatic | Yes |

## Exploratory testing

Probe candidate-envelope for item VER1 under retry, interruption, and boundary-value inputs against the interface declared for VER1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item VER1 reverts the change to the interface declared for VER1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER1: review risks specific to candidate-envelope and record any open decision.
