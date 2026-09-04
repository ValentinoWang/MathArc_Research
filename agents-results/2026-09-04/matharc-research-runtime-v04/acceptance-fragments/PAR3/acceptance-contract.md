# Acceptance Contract: PAR3

- Task ID: PAR3
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-PAR3
- SSOT node: PAR3
- SSOT path: .ssot/nodes/PAR3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.par3
- AC budget: 5
- Baseline identity: ssot-input.json#items[PAR3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching bounded-parallelism drives item PAR3 (unspecified dimension) through the interface declared for PAR3. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Problem

Item PAR3 exists because the interface declared for PAR3 does not yet satisfy the acceptance seeds registered for it, leaving bounded-parallelism incomplete. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Expected outcome

After item PAR3 lands, the interface declared for PAR3 satisfies every acceptance seed below and bounded-parallelism reflects that behavior. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Non-goals

Item PAR3 covers only the interface declared for PAR3 and bounded-parallelism as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Normal path

```gherkin
Given a user reaches bounded-parallelism for item PAR3
When the flow defined by the interface declared for PAR3 executes
Then every acceptance seed for item PAR3 holds  Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.
```

## Exception paths

If the interface declared for PAR3 fails for item PAR3, bounded-parallelism must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Invariants

For item PAR3, the interface declared for PAR3 must continue to satisfy every acceptance seed below on every call; bounded-parallelism must never show a state the seeds forbid. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Data impact

Item PAR3 constrains any create, update, or delete reachable through the interface declared for PAR3; only the acceptance seeds below define what data changes are permitted for bounded-parallelism. Node-specific data assertions: 在 matharc/v02/runtime/scheduler.py 中实现有界并发、独立 execution_id 和隔离工作区 | 在 tests/test_runtime_parallelism.py 中证明至少三个不同进程存在真实时间重叠且写入区域无交集 | 在 tests/test_runtime_parallelism_contract.py 中验证冻结输入、并发上限和隔离工作区遵守运行时数据合同 | 在 matharc/v02/runtime/scheduler.py 中固定 GenerationInputSnapshot 输入、execution_id 与隔离工作区输出、并发上限、成员幂等键、超时/取消/失败分类、有限重试和恢复回执；在 tests/test_runtime_parallelism.py 与 tests/test_runtime_parallelism_contract.py 中保护真实重叠与独立验收身份 | tests/test_runtime_parallelism.py 和 tests/test_runtime_parallelism_contract.py 实现后必须在 protected_tests 登记各自 SHA-256 及真实重叠/隔离合同覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Permissions

Item PAR3 is owned by principal:acceptance-a; access to the interface declared for PAR3 and bounded-parallelism follows the acceptance seeds below and no wider grant. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR3: the thresholds and failure evidence for the interface declared for PAR3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PAR3 | machine/non-functional | 在 matharc/v02/runtime/scheduler.py 中实现有界并发、独立 execution_id 和隔离工作区 | Non-functional | Automatic | Yes |
| AC-02 | behavior | SRC-PAR3 | machine/local-runtime | 在 tests/test_runtime_parallelism.py 中证明至少三个不同进程存在真实时间重叠且写入区域无交集 | Local runtime | Automatic | Yes |
| AC-03 | behavior | SRC-PAR3 | machine/integration-contract | 在 tests/test_runtime_parallelism_contract.py 中验证冻结输入、并发上限和隔离工作区遵守运行时数据合同 | Integration | Automatic | Yes |
| AC-04 | behavior | SRC-PAR3 | machine/non-functional | 在 matharc/v02/runtime/scheduler.py 中固定 GenerationInputSnapshot 输入、execution_id 与隔离工作区输出、并发上限、成员幂等键、超时/取消/失败分类、有限重试和恢复回执；在 tests/test_runtime_parallelism.py 与 tests/test_runtime_parallelism_contract.py 中保护真实重叠与独立验收身份 | Non-functional | Automatic | Yes |
| AC-05 | behavior | SRC-PAR3 | machine/local-runtime | tests/test_runtime_parallelism.py 和 tests/test_runtime_parallelism_contract.py 实现后必须在 protected_tests 登记各自 SHA-256 及真实重叠/隔离合同覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY | Local runtime | Automatic | Yes |

## Human acceptance

Item PAR3 is fully determined by its acceptance seeds; outcomes for the interface declared for PAR3 on bounded-parallelism are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item PAR3; executable baseline not yet locked. Concrete seed references: matharc/v02/runtime/scheduler.py, tests/test_runtime_parallelism.py, tests/test_runtime_parallelism_contract.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Non-functional | matharc/v02/runtime/scheduler.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_parallelism.py | Automatic | Yes |
| AC-03 | Integration | tests/test_runtime_parallelism_contract.py | Automatic | Yes |
| AC-04 | Non-functional | matharc/v02/runtime/scheduler.py | Automatic | Yes |
| AC-05 | Local runtime | tests/test_runtime_parallelism.py | Automatic | Yes |

## Exploratory testing

Probe bounded-parallelism for item PAR3 under retry, interruption, and boundary-value inputs against the interface declared for PAR3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item PAR3 reverts the change to the interface declared for PAR3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR3: review risks specific to bounded-parallelism and record any open decision.
