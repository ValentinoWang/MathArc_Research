# Acceptance Contract: VER2

- Task ID: VER2
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-VER2
- SSOT node: VER2
- SSOT path: .ssot/nodes/VER2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ver2
- AC budget: 2
- Baseline identity: ssot-input.json#items[VER2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching claim-binding drives item VER2 (unspecified dimension) through the interface declared for VER2.

## Problem

Item VER2 exists because the interface declared for VER2 does not yet satisfy the acceptance seeds registered for it, leaving claim-binding incomplete.

## Expected outcome

After item VER2 lands, the interface declared for VER2 satisfies every acceptance seed below and claim-binding reflects that behavior.

## Non-goals

Item VER2 covers only the interface declared for VER2 and claim-binding as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches claim-binding for item VER2
When the flow defined by the interface declared for VER2 executes
Then every acceptance seed for item VER2 holds
```

## Exception paths

If the interface declared for VER2 fails for item VER2, claim-binding must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item VER2, the interface declared for VER2 must continue to satisfy every acceptance seed below on every call; claim-binding must never show a state the seeds forbid.

## Data impact

Item VER2 constrains any create, update, or delete reachable through the interface declared for VER2; only the acceptance seeds below define what data changes are permitted for claim-binding. Node-specific data assertions: 在 matharc/v02/runtime/verification.py 中将候选绑定到具体命题、量词、对象和范围 | 在 tests/test_candidate_scope_binding.py 中拒绝范围扩大、量词变化和对象错配

## Permissions

Item VER2 is owned by principal:acceptance-a; access to the interface declared for VER2 and claim-binding follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER2: the thresholds and failure evidence for the interface declared for VER2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-VER2 | machine/unit | 在 matharc/v02/runtime/verification.py 中将候选绑定到具体命题、量词、对象和范围 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-VER2 | machine/integration-contract | 在 tests/test_candidate_scope_binding.py 中拒绝范围扩大、量词变化和对象错配 | Integration | Automatic | Yes |

## Human acceptance

Item VER2 is fully determined by its acceptance seeds; outcomes for the interface declared for VER2 on claim-binding are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item VER2; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/runtime/verification.py | Automatic | Yes |
| AC-02 | Integration | tests/test_candidate_scope_binding.py | Automatic | Yes |

## Exploratory testing

Probe claim-binding for item VER2 under retry, interruption, and boundary-value inputs against the interface declared for VER2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item VER2 reverts the change to the interface declared for VER2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER2: review risks specific to claim-binding and record any open decision.
