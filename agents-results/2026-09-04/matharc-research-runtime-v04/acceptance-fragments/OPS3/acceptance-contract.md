# Acceptance Contract: OPS3

- Task ID: OPS3
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 试点发布运维负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[25]
- SSOT node: OPS3
- SSOT path: .ssot/nodes/OPS3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ops3
- AC budget: 3
- Baseline identity: ssot-input.json#items[OPS3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching pilot-operations drives item OPS3 (unspecified dimension) through the interface declared for OPS3.

## Problem

Item OPS3 exists because the interface declared for OPS3 does not yet satisfy the acceptance seeds registered for it, leaving pilot-operations incomplete.

## Expected outcome

After item OPS3 lands, the interface declared for OPS3 satisfies every acceptance seed below and pilot-operations reflects that behavior.

## Non-goals

Item OPS3 covers only the interface declared for OPS3 and pilot-operations as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches pilot-operations for item OPS3
When the flow defined by the interface declared for OPS3 executes
Then every acceptance seed for item OPS3 holds
```

## Exception paths

If the interface declared for OPS3 fails for item OPS3, pilot-operations must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item OPS3, the interface declared for OPS3 must continue to satisfy every acceptance seed below on every call; pilot-operations must never show a state the seeds forbid.

## Data impact

Item OPS3 constrains any create, update, or delete reachable through the interface declared for OPS3; only the acceptance seeds below define what data changes are permitted for pilot-operations. Node-specific data assertions: 在 tests/test_runtime_ops_release.py 中完成部署、重启、回滚的不可变发布验收 | 在 tests/test_runtime_ops_cleanup.py 和 acceptance/runtime-pilot/ops-checklist.md 中验证临时工作区与试点用户数据可清理 | 在 acceptance/runtime-pilot/ops-release-checklist.md 中记录试点环境的部署、回滚和清理生产收尾

## Permissions

Item OPS3 is owned by 试点发布运维负责人; access to the interface declared for OPS3 and pilot-operations follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item OPS3: the thresholds and failure evidence for the interface declared for OPS3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-OPS3 | machine/e2e | 在 tests/test_runtime_ops_release.py 中完成部署、重启、回滚的不可变发布验收 | E2E | Automatic | Yes |
| AC-02 | behavior | SRC-OPS3 | persistent-runtime | 在 tests/test_runtime_ops_cleanup.py 和 acceptance/runtime-pilot/ops-checklist.md 中验证临时工作区与试点用户数据可清理 | Persistent runtime | Automatic | Yes |
| AC-03 | behavior | SRC-OPS3 | production | 在 acceptance/runtime-pilot/ops-release-checklist.md 中记录试点环境的部署、回滚和清理生产收尾 | Production | Automatic | Yes |

## Human acceptance

Item OPS3 is fully determined by its acceptance seeds; outcomes for the interface declared for OPS3 on pilot-operations are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item OPS3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_runtime_ops_release.py | Automatic | Yes |
| AC-02 | Persistent runtime | tests/test_runtime_ops_cleanup.py | Automatic | Yes |
| AC-03 | Production | acceptance/runtime-pilot/ops-release-checklist.md | Automatic | Yes |

## Exploratory testing

Probe pilot-operations for item OPS3 under retry, interruption, and boundary-value inputs against the interface declared for OPS3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item OPS3 reverts the change to the interface declared for OPS3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item OPS3: review risks specific to pilot-operations and record any open decision.
