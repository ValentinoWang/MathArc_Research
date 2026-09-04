# Acceptance Contract: RUN1

- Task ID: RUN1
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-RUN1
- SSOT node: RUN1
- SSOT path: .ssot/nodes/RUN1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.run1
- AC budget: 6
- Baseline identity: ssot-input.json#items[RUN1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching run-contracts drives item RUN1 (unspecified dimension) through the interface declared for RUN1.

## Problem

Item RUN1 exists because the interface declared for RUN1 does not yet satisfy the acceptance seeds registered for it, leaving run-contracts incomplete.

## Expected outcome

After item RUN1 lands, the interface declared for RUN1 satisfies every acceptance seed below and run-contracts reflects that behavior.

## Non-goals

Item RUN1 covers only the interface declared for RUN1 and run-contracts as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches run-contracts for item RUN1
When the flow defined by the interface declared for RUN1 executes
Then every acceptance seed for item RUN1 holds
```

## Exception paths

If the interface declared for RUN1 fails for item RUN1, run-contracts must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item RUN1, the interface declared for RUN1 must continue to satisfy every acceptance seed below on every call; run-contracts must never show a state the seeds forbid.

## Data impact

Item RUN1 constrains any create, update, or delete reachable through the interface declared for RUN1; only the acceptance seeds below define what data changes are permitted for run-contracts. Node-specific data assertions: 在 matharc/v02/runtime/contracts.py 中定义 ResearchRunSpec、ResearchWorkerSpec、WorkerExecutionResult、CandidateEnvelope 和 RuntimeActionReceipt 的严格 round-trip | 在 matharc/v02/runtime/identity.py 中定义 workspace_id、trace_id、runtime_run_id、generation_id、worker_id、execution_id、candidate_id、evidence_id 的层级约束 | 在 tests/test_runtime_contracts.py 和 tests/test_runtime_identity.py 中拒绝未知字段、未知状态、身份错配和不兼容合同版本 | 在 matharc/v02/runtime/generation.py 中定义 GenerationInputSnapshot、GenerationReducer 和 GenerationClosePolicy 的输入输出边界 | 在 matharc/v02/runtime/contracts.py 中固定输入合同、输出信封、状态转换、幂等键 runtime_run_id+generation_id、超时、取消与失败分类；在 tests/test_runtime_contracts.py 中把合同版本和独立验收身份作为受保护目标 | tests/test_runtime_contracts.py 和 tests/test_runtime_identity.py 实现后必须在 protected_tests 登记各自 SHA-256 及覆盖范围；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY

## Permissions

Item RUN1 is owned by principal:acceptance-a; access to the interface declared for RUN1 and run-contracts follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN1: the thresholds and failure evidence for the interface declared for RUN1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-RUN1 | machine/unit | 在 matharc/v02/runtime/contracts.py 中定义 ResearchRunSpec、ResearchWorkerSpec、WorkerExecutionResult、CandidateEnvelope 和 RuntimeActionReceipt 的严格 round-trip | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-RUN1 | machine/integration-contract | 在 matharc/v02/runtime/identity.py 中定义 workspace_id、trace_id、runtime_run_id、generation_id、worker_id、execution_id、candidate_id、evidence_id 的层级约束 | Integration | Automatic | Yes |
| AC-03 | behavior | SRC-RUN1 | machine/unit | 在 tests/test_runtime_contracts.py 和 tests/test_runtime_identity.py 中拒绝未知字段、未知状态、身份错配和不兼容合同版本 | Unit | Automatic | Yes |
| AC-04 | behavior | SRC-RUN1 | machine/integration-contract | 在 matharc/v02/runtime/generation.py 中定义 GenerationInputSnapshot、GenerationReducer 和 GenerationClosePolicy 的输入输出边界 | Integration | Automatic | Yes |
| AC-05 | behavior | SRC-RUN1 | machine/unit | 在 matharc/v02/runtime/contracts.py 中固定输入合同、输出信封、状态转换、幂等键 runtime_run_id+generation_id、超时、取消与失败分类；在 tests/test_runtime_contracts.py 中把合同版本和独立验收身份作为受保护目标 | Unit | Automatic | Yes |
| AC-06 | behavior | SRC-RUN1 | machine/integration-contract | tests/test_runtime_contracts.py 和 tests/test_runtime_identity.py 实现后必须在 protected_tests 登记各自 SHA-256 及覆盖范围；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY | Integration | Automatic | Yes |

## Human acceptance

Item RUN1 is fully determined by its acceptance seeds; outcomes for the interface declared for RUN1 on run-contracts are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item RUN1; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/runtime/contracts.py | Automatic | Yes |
| AC-02 | Integration | matharc/v02/runtime/identity.py | Automatic | Yes |
| AC-03 | Unit | tests/test_runtime_contracts.py | Automatic | Yes |
| AC-04 | Integration | matharc/v02/runtime/generation.py | Automatic | Yes |
| AC-05 | Unit | matharc/v02/runtime/contracts.py | Automatic | Yes |
| AC-06 | Integration | tests/test_runtime_contracts.py | Automatic | Yes |

## Exploratory testing

Probe run-contracts for item RUN1 under retry, interruption, and boundary-value inputs against the interface declared for RUN1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item RUN1 reverts the change to the interface declared for RUN1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN1: review risks specific to run-contracts and record any open decision.
