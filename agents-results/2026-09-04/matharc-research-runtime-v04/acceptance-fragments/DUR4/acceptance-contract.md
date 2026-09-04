# Acceptance Contract: DUR4

- Task ID: DUR4
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-DUR4
- SSOT node: DUR4
- SSOT path: .ssot/nodes/DUR4.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dur4
- AC budget: 4
- Baseline identity: ssot-input.json#items[DUR4]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching crash-recovery drives item DUR4 (unspecified dimension) through the interface declared for DUR4.

## Problem

Item DUR4 exists because the interface declared for DUR4 does not yet satisfy the acceptance seeds registered for it, leaving crash-recovery incomplete.

## Expected outcome

After item DUR4 lands, the interface declared for DUR4 satisfies every acceptance seed below and crash-recovery reflects that behavior.

## Non-goals

Item DUR4 covers only the interface declared for DUR4 and crash-recovery as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches crash-recovery for item DUR4
When the flow defined by the interface declared for DUR4 executes
Then every acceptance seed for item DUR4 holds
```

## Exception paths

If the interface declared for DUR4 fails for item DUR4, crash-recovery must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item DUR4, the interface declared for DUR4 must continue to satisfy every acceptance seed below on every call; crash-recovery must never show a state the seeds forbid.

## Data impact

Item DUR4 constrains any create, update, or delete reachable through the interface declared for DUR4; only the acceptance seeds below define what data changes are permitted for crash-recovery. Node-specific data assertions: 在 matharc/v02/runtime/recovery.py 中从确定的 GenerationCommit 边界生成恢复计划和故障矩阵 | 在 tests/test_runtime_recovery_plan.py 中对固定任务、模型或评价器变化拒绝恢复 | 在 matharc/v02/runtime/recovery.py 中固定 GenerationCommit 摘要输入、RecoveryPlan 输出、(runtime_run_id,generation_id) 幂等键、超时/取消/不可恢复失败分类、一次有限重试与恢复后状态；在 tests/test_runtime_recovery_plan.py 中保护恢复计划独立验收身份 | tests/test_runtime_recovery_plan.py 实现后必须在 protected_tests 登记 SHA-256 及恢复规划/拒绝恢复覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY

## Permissions

Item DUR4 is owned by principal:acceptance-a; access to the interface declared for DUR4 and crash-recovery follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR4: the thresholds and failure evidence for the interface declared for DUR4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DUR4 | machine/local-runtime | 在 matharc/v02/runtime/recovery.py 中从确定的 GenerationCommit 边界生成恢复计划和故障矩阵 | Local runtime | Automatic | Yes |
| AC-02 | behavior | SRC-DUR4 | machine/integration-contract | 在 tests/test_runtime_recovery_plan.py 中对固定任务、模型或评价器变化拒绝恢复 | Integration | Automatic | Yes |
| AC-03 | behavior | SRC-DUR4 | machine/local-runtime | 在 matharc/v02/runtime/recovery.py 中固定 GenerationCommit 摘要输入、RecoveryPlan 输出、(runtime_run_id,generation_id) 幂等键、超时/取消/不可恢复失败分类、一次有限重试与恢复后状态；在 tests/test_runtime_recovery_plan.py 中保护恢复计划独立验收身份 | Local runtime | Automatic | Yes |
| AC-04 | behavior | SRC-DUR4 | machine/integration-contract | tests/test_runtime_recovery_plan.py 实现后必须在 protected_tests 登记 SHA-256 及恢复规划/拒绝恢复覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY | Integration | Automatic | Yes |

## Human acceptance

Item DUR4 is fully determined by its acceptance seeds; outcomes for the interface declared for DUR4 on crash-recovery are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DUR4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Local runtime | matharc/v02/runtime/recovery.py | Automatic | Yes |
| AC-02 | Integration | tests/test_runtime_recovery_plan.py | Automatic | Yes |
| AC-03 | Local runtime | matharc/v02/runtime/recovery.py | Automatic | Yes |
| AC-04 | Integration | tests/test_runtime_recovery_plan.py | Automatic | Yes |

## Exploratory testing

Probe crash-recovery for item DUR4 under retry, interruption, and boundary-value inputs against the interface declared for DUR4, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DUR4 reverts the change to the interface declared for DUR4; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR4: review risks specific to crash-recovery and record any open decision.
