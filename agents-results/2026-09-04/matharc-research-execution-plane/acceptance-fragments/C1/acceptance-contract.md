# Acceptance Contract: C1

- Task ID: C1
- Contract version: 1
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: Harness 声明编译负责人
- Approval evidence: protected-tests-locked: .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py, .agents/skills/report-to-ssot-development-paths/tests/test_compile_ssot.py
- Request source: item C1
- SSOT node: C1
- SSOT path: .ssot/nodes/C1.json
- Readiness mode: FORMAL
- Decision refs: decision.execution-plane.scope@1
- Assumption IDs: none
- Invalidation keys: task.c1
- AC budget: 3
- Baseline identity: ssot-input.json#items[C1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching ssot-input-schema-and-completion-evidence drives item C1 (unspecified dimension) through the interface declared for C1.

## Problem

Item C1 exists because the interface declared for C1 does not yet satisfy the acceptance seeds registered for it, leaving ssot-input-schema-and-completion-evidence incomplete.

## Expected outcome

After item C1 lands, the interface declared for C1 satisfies every acceptance seed below and ssot-input-schema-and-completion-evidence reflects that behavior.

## Non-goals

Item C1 covers only the interface declared for C1 and ssot-input-schema-and-completion-evidence as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches ssot-input-schema-and-completion-evidence for item C1
When the flow defined by the interface declared for C1 executes
Then every acceptance seed for item C1 holds
```

## Exception paths

If the interface declared for C1 fails for item C1, ssot-input-schema-and-completion-evidence must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item C1, the interface declared for C1 must continue to satisfy every acceptance seed below on every call; ssot-input-schema-and-completion-evidence must never show a state the seeds forbid.

## Data impact

Item C1 constrains any create, update, or delete reachable through the interface declared for C1; only the acceptance seeds below define what data changes are permitted for ssot-input-schema-and-completion-evidence. Node-specific data assertions: 在 .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py 中证明未知顶层字段、未知 item 字段、错误 acceptance_contract_policy_version、缺失嵌套字段、错误枚举和错误类型均被 Draft 2020-12 schema 拒绝 | 在 .agents/skills/report-to-ssot-development-paths/tests/test_compile_ssot.py 中证明 items[].execution 可编译出 escalation、worker、预算、worker ledger 和 runner registry，旧 multi_executor 不能作为正式输入 | 在 .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py 中证明不存在的 40 位提交或非通过 result_path 都使完成登记失败；result_sha256 由编译器从 result_path 内容派生而不是由输入声明

## Permissions

Item C1 is owned by Harness 声明编译负责人; access to the interface declared for C1 and ssot-input-schema-and-completion-evidence follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item C1: the thresholds and failure evidence for the interface declared for C1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/unit | 在 .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py 中证明未知顶层字段、未知 item 字段、错误 acceptance_contract_policy_version、缺失嵌套字段、错误枚举和错误类型均被 Draft 2020-12 schema 拒绝 | Unit | Automatic | Yes |
| AC-02 | behavior | none | machine/integration-contract | 在 .agents/skills/report-to-ssot-development-paths/tests/test_compile_ssot.py 中证明 items[].execution 可编译出 escalation、worker、预算、worker ledger 和 runner registry，旧 multi_executor 不能作为正式输入 | Integration | Automatic | Yes |
| AC-03 | behavior | none | machine/unit | 在 .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py 中证明不存在的 40 位提交或非通过 result_path 都使完成登记失败；result_sha256 由编译器从 result_path 内容派生而不是由输入声明 | Unit | Automatic | Yes |

## Human acceptance

Item C1 is fully determined by its acceptance seeds; outcomes for the interface declared for C1 on ssot-input-schema-and-completion-evidence are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
| .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py | dd78a949ce83d0650eae4353520c7c331dad6927575c15e13c646c13930d3f91 | Draft 2020-12 schema and completion evidence cases |
| .agents/skills/report-to-ssot-development-paths/tests/test_compile_ssot.py | 2d8c40301f4c2bb41687aead0b788f5a9524394cf13bbea27ff13bc65da0d39f | Formal execution compilation cases |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py | Automatic | Yes |
| AC-02 | Integration | .agents/skills/report-to-ssot-development-paths/tests/test_compile_ssot.py | Automatic | Yes |
| AC-03 | Unit | .agents/skills/report-to-ssot-development-paths/tests/test_compile_execution_contract.py | Automatic | Yes |

## Exploratory testing

Probe ssot-input-schema-and-completion-evidence for item C1 under retry, interruption, and boundary-value inputs against the interface declared for C1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item C1 reverts the change to the interface declared for C1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item C1: review risks specific to ssot-input-schema-and-completion-evidence and record any open decision.
