# Acceptance Contract: DUR1

- Task ID: DUR1
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 代际提交负责人
- Approval evidence: TBD
- Request source: item DUR1
- SSOT node: DUR1
- SSOT path: .ssot/nodes/DUR1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dur1
- AC budget: 2
- Baseline identity: ssot-input.json#items[DUR1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching generation-commit drives item DUR1 (unspecified dimension) through the interface declared for DUR1.

## Problem

Item DUR1 exists because the interface declared for DUR1 does not yet satisfy the acceptance seeds registered for it, leaving generation-commit incomplete.

## Expected outcome

After item DUR1 lands, the interface declared for DUR1 satisfies every acceptance seed below and generation-commit reflects that behavior.

## Non-goals

Item DUR1 covers only the interface declared for DUR1 and generation-commit as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches generation-commit for item DUR1
When the flow defined by the interface declared for DUR1 executes
Then every acceptance seed for item DUR1 holds
```

## Exception paths

If the interface declared for DUR1 fails for item DUR1, generation-commit must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item DUR1, the interface declared for DUR1 must continue to satisfy every acceptance seed below on every call; generation-commit must never show a state the seeds forbid.

## Data impact

Item DUR1 constrains any create, update, or delete reachable through the interface declared for DUR1; only the acceptance seeds below define what data changes are permitted for generation-commit. Node-specific data assertions: 在 matharc/v02/generation.py 中定义 GenerationCommit 的输入摘要、候选清单和证据截止边界 | 在 tests/test_generation_commit.py 中拒绝没有连续正式提交边界的代际完成声明

## Permissions

Item DUR1 is owned by 代际提交负责人; access to the interface declared for DUR1 and generation-commit follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR1: the thresholds and failure evidence for the interface declared for DUR1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/unit | 在 matharc/v02/generation.py 中定义 GenerationCommit 的输入摘要、候选清单和证据截止边界 | Unit | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_generation_commit.py 中拒绝没有连续正式提交边界的代际完成声明 | Local runtime | Automatic | Yes |

## Human acceptance

Item DUR1 is fully determined by its acceptance seeds; outcomes for the interface declared for DUR1 on generation-commit are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DUR1; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/generation.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_generation_commit.py | Automatic | Yes |

## Exploratory testing

Probe generation-commit for item DUR1 under retry, interruption, and boundary-value inputs against the interface declared for DUR1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DUR1 reverts the change to the interface declared for DUR1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR1: review risks specific to generation-commit and record any open decision.
