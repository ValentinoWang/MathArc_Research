# Acceptance Contract: RUN4

- Task ID: RUN4
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-RUN4
- SSOT node: RUN4
- SSOT path: .ssot/nodes/RUN4.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1, decision.matharc-backend-scope@1
- Assumption IDs: none
- Invalidation keys: task.run4
- AC budget: 4
- Baseline identity: ssot-input.json#items[RUN4]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching backend-coordinator drives item RUN4 (unspecified dimension) through the interface declared for RUN4.

## Problem

Item RUN4 exists because the interface declared for RUN4 does not yet satisfy the acceptance seeds registered for it, leaving backend-coordinator incomplete.

## Expected outcome

After item RUN4 lands, the interface declared for RUN4 satisfies every acceptance seed below and backend-coordinator reflects that behavior.

## Non-goals

Item RUN4 covers only the interface declared for RUN4 and backend-coordinator as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches backend-coordinator for item RUN4
When the flow defined by the interface declared for RUN4 executes
Then every acceptance seed for item RUN4 holds
```

## Exception paths

If the interface declared for RUN4 fails for item RUN4, backend-coordinator must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item RUN4, the interface declared for RUN4 must continue to satisfy every acceptance seed below on every call; backend-coordinator must never show a state the seeds forbid.

## Data impact

Item RUN4 constrains any create, update, or delete reachable through the interface declared for RUN4; only the acceptance seeds below define what data changes are permitted for backend-coordinator. Node-specific data assertions: 在 matharc/v02/runtime/coordinator.py 中只把 DeterministicTestBackend、CodexBackend 和 LocalExactToolBackend 接入 MathArc 后端请求；Claude Code 与通用模型 API 仅保留后置兼容接口 | 在 tests/test_runtime_backend_contract.py 中证明后端结果只能形成 CandidateEnvelope，不能写入 RuntimeStore 之外的数学状态 | 在 matharc/v02/runtime/backends/base.py 和 matharc/v02/runtime/coordinator.py 中固定首版后端输入、CandidateEnvelope 输出、execution_id 幂等键、超时/取消/重试和失败分类；在 tests/test_runtime_backend_contract.py 中逐一保护 DeterministicTestBackend、CodexBackend、LocalExactToolBackend 的独立验收身份 | tests/test_runtime_backend_contract.py 实现后必须在 protected_tests 登记 SHA-256 及三个首版后端的覆盖范围；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY

## Permissions

Item RUN4 is owned by principal:acceptance-a; access to the interface declared for RUN4 and backend-coordinator follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN4: the thresholds and failure evidence for the interface declared for RUN4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-RUN4 | machine/integration-contract | 在 matharc/v02/runtime/coordinator.py 中只把 DeterministicTestBackend、CodexBackend 和 LocalExactToolBackend 接入 MathArc 后端请求；Claude Code 与通用模型 API 仅保留后置兼容接口 | Integration | Automatic | Yes |
| AC-02 | behavior | SRC-RUN4 | machine/local-runtime | 在 tests/test_runtime_backend_contract.py 中证明后端结果只能形成 CandidateEnvelope，不能写入 RuntimeStore 之外的数学状态 | Local runtime | Automatic | Yes |
| AC-03 | behavior | SRC-RUN4 | machine/integration-contract | 在 matharc/v02/runtime/backends/base.py 和 matharc/v02/runtime/coordinator.py 中固定首版后端输入、CandidateEnvelope 输出、execution_id 幂等键、超时/取消/重试和失败分类；在 tests/test_runtime_backend_contract.py 中逐一保护 DeterministicTestBackend、CodexBackend、LocalExactToolBackend 的独立验收身份 | Integration | Automatic | Yes |
| AC-04 | behavior | SRC-RUN4 | machine/local-runtime | tests/test_runtime_backend_contract.py 实现后必须在 protected_tests 登记 SHA-256 及三个首版后端的覆盖范围；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY | Local runtime | Automatic | Yes |

## Human acceptance

Item RUN4 is fully determined by its acceptance seeds; outcomes for the interface declared for RUN4 on backend-coordinator are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item RUN4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/runtime/coordinator.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_backend_contract.py | Automatic | Yes |
| AC-03 | Integration | matharc/v02/runtime/backends/base.py | Automatic | Yes |
| AC-04 | Local runtime | tests/test_runtime_backend_contract.py | Automatic | Yes |

## Exploratory testing

Probe backend-coordinator for item RUN4 under retry, interruption, and boundary-value inputs against the interface declared for RUN4, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item RUN4 reverts the change to the interface declared for RUN4; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN4: review risks specific to backend-coordinator and record any open decision.
