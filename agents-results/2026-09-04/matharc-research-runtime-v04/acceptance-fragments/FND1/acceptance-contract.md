# Acceptance Contract: FND1

- Task ID: FND1
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: MathArc 运行时架构负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:h2[1]
- SSOT node: FND1
- SSOT path: .ssot/nodes/FND1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.fnd1
- AC budget: 3
- Baseline identity: ssot-input.json#items[FND1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching runtime-governance drives item FND1 (unspecified dimension) through the interface declared for FND1.

## Problem

Item FND1 exists because the interface declared for FND1 does not yet satisfy the acceptance seeds registered for it, leaving runtime-governance incomplete.

## Expected outcome

After item FND1 lands, the interface declared for FND1 satisfies every acceptance seed below and runtime-governance reflects that behavior.

## Non-goals

Item FND1 covers only the interface declared for FND1 and runtime-governance as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches runtime-governance for item FND1
When the flow defined by the interface declared for FND1 executes
Then every acceptance seed for item FND1 holds
```

## Exception paths

If the interface declared for FND1 fails for item FND1, runtime-governance must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item FND1, the interface declared for FND1 must continue to satisfy every acceptance seed below on every call; runtime-governance must never show a state the seeds forbid.

## Data impact

Item FND1 constrains any create, update, or delete reachable through the interface declared for FND1; only the acceptance seeds below define what data changes are permitted for runtime-governance. Node-specific data assertions: 在 scripts/check_runtime_ownership.py 和 tests/test_runtime_ownership.py 中登记 MathArc 原生运行时与治理工具链的允许边界 | 在 scripts/check_runtime_dependency_allowlist.py 和 tests/test_runtime_dependency_allowlist.py 中对未知运行时依赖 fail-closed | 在 tests/test_runtime_ownership.py 中证明所有实现节点只写入已登记的 MathArc 代码与测试文件

## Permissions

Item FND1 is owned by MathArc 运行时架构负责人; access to the interface declared for FND1 and runtime-governance follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item FND1: the thresholds and failure evidence for the interface declared for FND1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-FND1 | machine/static | 在 scripts/check_runtime_ownership.py 和 tests/test_runtime_ownership.py 中登记 MathArc 原生运行时与治理工具链的允许边界 | Static analysis | Automatic | Yes |
| AC-02 | behavior | SRC-FND1 | machine/unit | 在 scripts/check_runtime_dependency_allowlist.py 和 tests/test_runtime_dependency_allowlist.py 中对未知运行时依赖 fail-closed | Unit | Automatic | Yes |
| AC-03 | behavior | SRC-FND1 | machine/static | 在 tests/test_runtime_ownership.py 中证明所有实现节点只写入已登记的 MathArc 代码与测试文件 | Static analysis | Automatic | Yes |

## Human acceptance

Item FND1 is fully determined by its acceptance seeds; outcomes for the interface declared for FND1 on runtime-governance are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item FND1; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Static analysis | scripts/check_runtime_ownership.py | Automatic | Yes |
| AC-02 | Unit | scripts/check_runtime_dependency_allowlist.py | Automatic | Yes |
| AC-03 | Static analysis | tests/test_runtime_ownership.py | Automatic | Yes |

## Exploratory testing

Probe runtime-governance for item FND1 under retry, interruption, and boundary-value inputs against the interface declared for FND1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item FND1 reverts the change to the interface declared for FND1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item FND1: review risks specific to runtime-governance and record any open decision.
