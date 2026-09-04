# Acceptance Contract: DUR5

- Task ID: DUR5
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 恢复验收负责人
- Approval evidence: TBD
- Request source: item DUR5
- SSOT node: DUR5
- SSOT path: .ssot/nodes/DUR5.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dur5
- AC budget: 2
- Baseline identity: ssot-input.json#items[DUR5]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching cold-restart drives item DUR5 (unspecified dimension) through the interface declared for DUR5.

## Problem

Item DUR5 exists because the interface declared for DUR5 does not yet satisfy the acceptance seeds registered for it, leaving cold-restart incomplete.

## Expected outcome

After item DUR5 lands, the interface declared for DUR5 satisfies every acceptance seed below and cold-restart reflects that behavior.

## Non-goals

Item DUR5 covers only the interface declared for DUR5 and cold-restart as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches cold-restart for item DUR5
When the flow defined by the interface declared for DUR5 executes
Then every acceptance seed for item DUR5 holds
```

## Exception paths

If the interface declared for DUR5 fails for item DUR5, cold-restart must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item DUR5, the interface declared for DUR5 must continue to satisfy every acceptance seed below on every call; cold-restart must never show a state the seeds forbid.

## Data impact

Item DUR5 constrains any create, update, or delete reachable through the interface declared for DUR5; only the acceptance seeds below define what data changes are permitted for cold-restart. Node-specific data assertions: 在 tests/test_runtime_crash_recovery.py 中强制终止进程后完成冷启动恢复 | 在 tests/test_runtime_no_duplicate_recovery.py 中证明恢复不会重复任务、费用、候选或跳代

## Permissions

Item DUR5 is owned by 恢复验收负责人; access to the interface declared for DUR5 and cold-restart follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR5: the thresholds and failure evidence for the interface declared for DUR5 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/e2e | 在 tests/test_runtime_crash_recovery.py 中强制终止进程后完成冷启动恢复 | E2E | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_runtime_no_duplicate_recovery.py 中证明恢复不会重复任务、费用、候选或跳代 | Local runtime | Automatic | Yes |

## Human acceptance

Item DUR5 is fully determined by its acceptance seeds; outcomes for the interface declared for DUR5 on cold-restart are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DUR5; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_runtime_crash_recovery.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_no_duplicate_recovery.py | Automatic | Yes |

## Exploratory testing

Probe cold-restart for item DUR5 under retry, interruption, and boundary-value inputs against the interface declared for DUR5, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DUR5 reverts the change to the interface declared for DUR5; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR5: review risks specific to cold-restart and record any open decision.
