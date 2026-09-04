# Acceptance Contract: OPS1

- Task ID: OPS1
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-OPS1
- SSOT node: OPS1
- SSOT path: .ssot/nodes/OPS1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1, decision.matharc-pilot-deployment@1
- Assumption IDs: none
- Invalidation keys: task.ops1
- AC budget: 4
- Baseline identity: ssot-input.json#items[OPS1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching pilot-operations drives item OPS1 (unspecified dimension) through the interface declared for OPS1.

## Problem

Item OPS1 exists because the interface declared for OPS1 does not yet satisfy the acceptance seeds registered for it, leaving pilot-operations incomplete.

## Expected outcome

After item OPS1 lands, the interface declared for OPS1 satisfies every acceptance seed below and pilot-operations reflects that behavior.

## Non-goals

Item OPS1 covers only the interface declared for OPS1 and pilot-operations as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches pilot-operations for item OPS1
When the flow defined by the interface declared for OPS1 executes
Then every acceptance seed for item OPS1 holds
```

## Exception paths

If the interface declared for OPS1 fails for item OPS1, pilot-operations must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item OPS1, the interface declared for OPS1 must continue to satisfy every acceptance seed below on every call; pilot-operations must never show a state the seeds forbid.

## Data impact

Item OPS1 constrains any create, update, or delete reachable through the interface declared for OPS1; only the acceptance seeds below define what data changes are permitted for pilot-operations. Node-specific data assertions: 在 tests/test_runtime_ops_deployment.py 中固定 deploy/matharc-research.service、deploy/matharc-research.env.example 的持久目录、密钥来源和进程守护配置 | 在 tests/test_runtime_ops_deployment.py 中拒绝临时路径、明文密钥和无守护部署 | 在 deploy/matharc-research.service 和 deploy/matharc-research.env.example 中固定 Linux+systemd 输入、健康检查/运行身份输出、release_id 幂等键、启动超时/取消/失败分类、回滚与恢复边界；在 tests/test_runtime_ops_deployment.py 中保护持久目录、外部 secret source 和独立验收身份 | tests/test_runtime_ops_deployment.py 实现后必须在 protected_tests 登记 SHA-256 及持久目录/外部密钥/守护进程覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY

## Permissions

Item OPS1 is owned by principal:acceptance-a; access to the interface declared for OPS1 and pilot-operations follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item OPS1: the thresholds and failure evidence for the interface declared for OPS1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-OPS1 | machine/static | 在 tests/test_runtime_ops_deployment.py 中固定 deploy/matharc-research.service、deploy/matharc-research.env.example 的持久目录、密钥来源和进程守护配置 | Static analysis | Automatic | Yes |
| AC-02 | behavior | SRC-OPS1 | persistent-runtime | 在 tests/test_runtime_ops_deployment.py 中拒绝临时路径、明文密钥和无守护部署 | Persistent runtime | Automatic | Yes |
| AC-03 | behavior | SRC-OPS1 | machine/static | 在 deploy/matharc-research.service 和 deploy/matharc-research.env.example 中固定 Linux+systemd 输入、健康检查/运行身份输出、release_id 幂等键、启动超时/取消/失败分类、回滚与恢复边界；在 tests/test_runtime_ops_deployment.py 中保护持久目录、外部 secret source 和独立验收身份 | Static analysis | Automatic | Yes |
| AC-04 | behavior | SRC-OPS1 | persistent-runtime | tests/test_runtime_ops_deployment.py 实现后必须在 protected_tests 登记 SHA-256 及持久目录/外部密钥/守护进程覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY | Persistent runtime | Automatic | Yes |

## Human acceptance

Item OPS1 is fully determined by its acceptance seeds; outcomes for the interface declared for OPS1 on pilot-operations are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item OPS1; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Static analysis | tests/test_runtime_ops_deployment.py | Automatic | Yes |
| AC-02 | Persistent runtime | tests/test_runtime_ops_deployment.py | Automatic | Yes |
| AC-03 | Static analysis | deploy/matharc-research.service | Automatic | Yes |
| AC-04 | Persistent runtime | tests/test_runtime_ops_deployment.py | Automatic | Yes |

## Exploratory testing

Probe pilot-operations for item OPS1 under retry, interruption, and boundary-value inputs against the interface declared for OPS1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item OPS1 reverts the change to the interface declared for OPS1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item OPS1: review risks specific to pilot-operations and record any open decision.
