# Acceptance Contract: PAR5

- Task ID: PAR5
- Contract kind: validation
- Contract profile: acceptance-contract-kind-profiles@1
- Verification layer: machine
- Acceptance mode: Automatic
- Evidence target: validation result
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: principal:acceptance-a
- Execution actor: orchestrator
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-PAR5
- SSOT node: PAR5
- SSOT path: .ssot/nodes/PAR5.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.par5
- AC budget: 5
- Baseline identity: ssot-input.json#items[PAR5]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching parallel-generation drives item PAR5 (unspecified dimension) through the interface declared for PAR5. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Problem

Item PAR5 exists because the interface declared for PAR5 does not yet satisfy the acceptance seeds registered for it, leaving parallel-generation incomplete. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Expected outcome

After item PAR5 lands, the interface declared for PAR5 satisfies every acceptance seed below and parallel-generation reflects that behavior. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Non-goals

Item PAR5 covers only the interface declared for PAR5 and parallel-generation as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Normal path

```gherkin
Given a user reaches parallel-generation for item PAR5
When the flow defined by the interface declared for PAR5 executes
Then every acceptance seed for item PAR5 holds  Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.
```

## Exception paths

If the interface declared for PAR5 fails for item PAR5, parallel-generation must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Invariants

For item PAR5, the interface declared for PAR5 must continue to satisfy every acceptance seed below on every call; parallel-generation must never show a state the seeds forbid. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Data impact

Item PAR5 constrains any create, update, or delete reachable through the interface declared for PAR5; only the acceptance seeds below define what data changes are permitted for parallel-generation. Node-specific data assertions: 在 tests/test_runtime_parallel_generation.py 中证明每名成员只读取同一 GenerationInputSnapshot 且由单一 GenerationReducer 稳定归并 | 在 tests/test_runtime_partial_failure.py 中证明部分成员失败、必需角色缺失和超时不会伪造完整代际 | 在 tests/test_runtime_late_result_policy.py 中证明关闭代际不接受迟到结果改写 | 在 tests/test_runtime_parallel_generation.py 和 tests/test_runtime_partial_failure.py 中固定并行输入/归并输出、generation_id 幂等键、超时/取消/失败分类、有限重试与恢复判定，并以独立测试身份拒绝伪造完整代际 | tests/test_runtime_parallel_generation.py、tests/test_runtime_partial_failure.py 和 tests/test_runtime_late_result_policy.py 实现后必须在 protected_tests 登记 SHA-256 及归并/部分失败/迟到结果覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Permissions

Item PAR5 is owned by principal:acceptance-a; access to the interface declared for PAR5 and parallel-generation follows the acceptance seeds below and no wider grant. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR5: the thresholds and failure evidence for the interface declared for PAR5 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PAR5 | machine/e2e | 在 tests/test_runtime_parallel_generation.py 中证明每名成员只读取同一 GenerationInputSnapshot 且由单一 GenerationReducer 稳定归并 | E2E | Automatic | Yes |
| AC-02 | behavior | SRC-PAR5 | machine/local-runtime | 在 tests/test_runtime_partial_failure.py 中证明部分成员失败、必需角色缺失和超时不会伪造完整代际 | Local runtime | Automatic | Yes |
| AC-03 | behavior | SRC-PAR5 | machine/e2e | 在 tests/test_runtime_late_result_policy.py 中证明关闭代际不接受迟到结果改写 | E2E | Automatic | Yes |
| AC-04 | behavior | SRC-PAR5 | machine/local-runtime | 在 tests/test_runtime_parallel_generation.py 和 tests/test_runtime_partial_failure.py 中固定并行输入/归并输出、generation_id 幂等键、超时/取消/失败分类、有限重试与恢复判定，并以独立测试身份拒绝伪造完整代际 | Local runtime | Automatic | Yes |
| AC-05 | behavior | SRC-PAR5 | machine/e2e | tests/test_runtime_parallel_generation.py、tests/test_runtime_partial_failure.py 和 tests/test_runtime_late_result_policy.py 实现后必须在 protected_tests 登记 SHA-256 及归并/部分失败/迟到结果覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY | E2E | Automatic | Yes |

## Human acceptance

Item PAR5 is fully determined by its acceptance seeds; outcomes for the interface declared for PAR5 on parallel-generation are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item PAR5; executable baseline not yet locked. Concrete seed references: tests/test_runtime_late_result_policy.py, tests/test_runtime_parallel_generation.py, tests/test_runtime_partial_failure.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_runtime_parallel_generation.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_partial_failure.py | Automatic | Yes |
| AC-03 | E2E | tests/test_runtime_late_result_policy.py | Automatic | Yes |
| AC-04 | Local runtime | tests/test_runtime_parallel_generation.py | Automatic | Yes |
| AC-05 | E2E | tests/test_runtime_parallel_generation.py | Automatic | Yes |

## Exploratory testing

Probe parallel-generation for item PAR5 under retry, interruption, and boundary-value inputs against the interface declared for PAR5, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item PAR5 reverts the change to the interface declared for PAR5; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR5: review risks specific to parallel-generation and record any open decision.
