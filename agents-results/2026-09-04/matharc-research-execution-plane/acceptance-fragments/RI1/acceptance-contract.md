# Acceptance Contract: RI1

- Task ID: RI1
- Contract version: 1
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: Harness 规则索引负责人
- Approval evidence: protected-tests-locked: .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py, .agents/skills/report-to-ssot-development-paths/tests/test_audit_ssot_policy_impact.py
- Request source: item RI1
- SSOT node: RI1
- SSOT path: .ssot/nodes/RI1.json
- Readiness mode: FORMAL
- Decision refs: decision.execution-plane.scope@1
- Assumption IDs: none
- Invalidation keys: task.ri1
- AC budget: 3
- Baseline identity: ssot-input.json#items[RI1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching rules-index-and-triggered-reading-map drives item RI1 (unspecified dimension) through the interface declared for RI1.

## Problem

Item RI1 exists because the interface declared for RI1 does not yet satisfy the acceptance seeds registered for it, leaving rules-index-and-triggered-reading-map incomplete.

## Expected outcome

After item RI1 lands, the interface declared for RI1 satisfies every acceptance seed below and rules-index-and-triggered-reading-map reflects that behavior.

## Non-goals

Item RI1 covers only the interface declared for RI1 and rules-index-and-triggered-reading-map as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches rules-index-and-triggered-reading-map for item RI1
When the flow defined by the interface declared for RI1 executes
Then every acceptance seed for item RI1 holds
```

## Exception paths

If the interface declared for RI1 fails for item RI1, rules-index-and-triggered-reading-map must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item RI1, the interface declared for RI1 must continue to satisfy every acceptance seed below on every call; rules-index-and-triggered-reading-map must never show a state the seeds forbid.

## Data impact

Item RI1 constrains any create, update, or delete reachable through the interface declared for RI1; only the acceptance seeds below define what data changes are permitted for rules-index-and-triggered-reading-map. Node-specific data assertions: 在 .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py 中证明 rules-index.json 保留一条已从 SKILL.md 删除的规则时元测试失败 | 在 .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py 中证明每条规范句都反向绑定唯一 source_clause 摘要且版本矩阵覆盖 node state、acceptance policy、shared policy 和 validation schema | 在 .agents/skills/report-to-ssot-development-paths/reading-map.json 中按 planning、acceptance、execution、views 触发条件声明最小读取路径，并由 test_rules_index.py 校验引用存在

## Permissions

Item RI1 is owned by Harness 规则索引负责人; access to the interface declared for RI1 and rules-index-and-triggered-reading-map follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item RI1: the thresholds and failure evidence for the interface declared for RI1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/static | 在 .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py 中证明 rules-index.json 保留一条已从 SKILL.md 删除的规则时元测试失败 | Static analysis | Automatic | Yes |
| AC-02 | behavior | none | machine/unit | 在 .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py 中证明每条规范句都反向绑定唯一 source_clause 摘要且版本矩阵覆盖 node state、acceptance policy、shared policy 和 validation schema | Unit | Automatic | Yes |
| AC-03 | behavior | none | machine/static | 在 .agents/skills/report-to-ssot-development-paths/reading-map.json 中按 planning、acceptance、execution、views 触发条件声明最小读取路径，并由 test_rules_index.py 校验引用存在 | Static analysis | Automatic | Yes |

## Human acceptance

Item RI1 is fully determined by its acceptance seeds; outcomes for the interface declared for RI1 on rules-index-and-triggered-reading-map are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
| .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py | 14de2f416dad0b1b7cb0dc919be1e4938445ab2681820d0b32670e620029e037 | Rules index reverse-conservation cases |
| .agents/skills/report-to-ssot-development-paths/tests/test_audit_ssot_policy_impact.py | 77fef160264c9f5268b3c01dc7f8ae33b95977aeb51ed869f6bf995882aeb5fb | Policy impact and reading-map cases |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Static analysis | .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py | Automatic | Yes |
| AC-02 | Unit | .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py | Automatic | Yes |
| AC-03 | Static analysis | .agents/skills/report-to-ssot-development-paths/reading-map.json | Automatic | Yes |

## Exploratory testing

Probe rules-index-and-triggered-reading-map for item RI1 under retry, interruption, and boundary-value inputs against the interface declared for RI1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item RI1 reverts the change to the interface declared for RI1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item RI1: review risks specific to rules-index-and-triggered-reading-map and record any open decision.
