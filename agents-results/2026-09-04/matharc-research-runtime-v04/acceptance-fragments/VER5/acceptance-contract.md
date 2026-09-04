# Acceptance Contract: VER5

- Task ID: VER5
- Contract kind: implementation
- Contract profile: acceptance-contract-kind-profiles@1
- Verification layer: machine
- Acceptance mode: Automatic
- Evidence target: test result
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: principal:acceptance-a
- Execution actor: orchestrator
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-VER5
- SSOT node: VER5
- SSOT path: .ssot/nodes/VER5.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ver5
- AC budget: 2
- Baseline identity: ssot-input.json#items[VER5]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching evidence-invalidation drives item VER5 (unspecified dimension) through the interface declared for VER5. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Problem

Item VER5 exists because the interface declared for VER5 does not yet satisfy the acceptance seeds registered for it, leaving evidence-invalidation incomplete. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Expected outcome

After item VER5 lands, the interface declared for VER5 satisfies every acceptance seed below and evidence-invalidation reflects that behavior. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Non-goals

Item VER5 covers only the interface declared for VER5 and evidence-invalidation as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Normal path

```gherkin
Given a user reaches evidence-invalidation for item VER5
When the flow defined by the interface declared for VER5 executes
Then every acceptance seed for item VER5 holds  Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.
```

## Exception paths

If the interface declared for VER5 fails for item VER5, evidence-invalidation must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Invariants

For item VER5, the interface declared for VER5 must continue to satisfy every acceptance seed below on every call; evidence-invalidation must never show a state the seeds forbid. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Data impact

Item VER5 constrains any create, update, or delete reachable through the interface declared for VER5; only the acceptance seeds below define what data changes are permitted for evidence-invalidation. Node-specific data assertions: 在 matharc/v02/runtime/verification.py 中记录命题、源码、评价器或候选身份变化导致的证据失效 | 在 tests/test_evidence_invalidation.py 中证明失效证据不能继续支撑已晋升结论 Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Permissions

Item VER5 is owned by principal:acceptance-a; access to the interface declared for VER5 and evidence-invalidation follows the acceptance seeds below and no wider grant. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER5: the thresholds and failure evidence for the interface declared for VER5 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-VER5 | machine/unit | 在 matharc/v02/runtime/verification.py 中记录命题、源码、评价器或候选身份变化导致的证据失效 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-VER5 | machine/integration-contract | 在 tests/test_evidence_invalidation.py 中证明失效证据不能继续支撑已晋升结论 | Integration | Automatic | Yes |

## Human acceptance

Item VER5 is fully determined by its acceptance seeds; outcomes for the interface declared for VER5 on evidence-invalidation are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item VER5; executable baseline not yet locked. Concrete seed references: matharc/v02/runtime/verification.py, tests/test_evidence_invalidation.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/runtime/verification.py | Automatic | Yes |
| AC-02 | Integration | tests/test_evidence_invalidation.py | Automatic | Yes |

## Exploratory testing

Probe evidence-invalidation for item VER5 under retry, interruption, and boundary-value inputs against the interface declared for VER5, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item VER5 reverts the change to the interface declared for VER5; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER5: review risks specific to evidence-invalidation and record any open decision.
