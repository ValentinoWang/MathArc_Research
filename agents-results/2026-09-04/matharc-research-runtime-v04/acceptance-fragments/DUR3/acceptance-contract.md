# Acceptance Contract: DUR3

- Task ID: DUR3
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 运行控制负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[10]
- SSOT node: DUR3
- SSOT path: .ssot/nodes/DUR3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dur3
- AC budget: 2
- Baseline identity: ssot-input.json#items[DUR3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching lifecycle-control drives item DUR3 (unspecified dimension) through the interface declared for DUR3.

## Problem

Item DUR3 exists because the interface declared for DUR3 does not yet satisfy the acceptance seeds registered for it, leaving lifecycle-control incomplete.

## Expected outcome

After item DUR3 lands, the interface declared for DUR3 satisfies every acceptance seed below and lifecycle-control reflects that behavior.

## Non-goals

Item DUR3 covers only the interface declared for DUR3 and lifecycle-control as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches lifecycle-control for item DUR3
When the flow defined by the interface declared for DUR3 executes
Then every acceptance seed for item DUR3 holds
```

## Exception paths

If the interface declared for DUR3 fails for item DUR3, lifecycle-control must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item DUR3, the interface declared for DUR3 must continue to satisfy every acceptance seed below on every call; lifecycle-control must never show a state the seeds forbid.

## Data impact

Item DUR3 constrains any create, update, or delete reachable through the interface declared for DUR3; only the acceptance seeds below define what data changes are permitted for lifecycle-control. Node-specific data assertions: 在 matharc/v02/state_machine.py 中实现停止、排空、暂停和取消状态协议 | 在 tests/test_runtime_lifecycle_control.py 中证明停止后不再接收新任务且活动任务有明确终止结果

## Permissions

Item DUR3 is owned by 运行控制负责人; access to the interface declared for DUR3 and lifecycle-control follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR3: the thresholds and failure evidence for the interface declared for DUR3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DUR3 | machine/unit | 在 matharc/v02/state_machine.py 中实现停止、排空、暂停和取消状态协议 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-DUR3 | machine/integration-contract | 在 tests/test_runtime_lifecycle_control.py 中证明停止后不再接收新任务且活动任务有明确终止结果 | Integration | Automatic | Yes |

## Human acceptance

Item DUR3 is fully determined by its acceptance seeds; outcomes for the interface declared for DUR3 on lifecycle-control are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DUR3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/state_machine.py | Automatic | Yes |
| AC-02 | Integration | tests/test_runtime_lifecycle_control.py | Automatic | Yes |

## Exploratory testing

Probe lifecycle-control for item DUR3 under retry, interruption, and boundary-value inputs against the interface declared for DUR3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DUR3 reverts the change to the interface declared for DUR3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR3: review risks specific to lifecycle-control and record any open decision.
