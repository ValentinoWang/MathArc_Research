# Acceptance Contract: DOG1

- Task ID: DOG1
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 试点任务负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[19]
- SSOT node: DOG1
- SSOT path: .ssot/nodes/DOG1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dog1
- AC budget: 2
- Baseline identity: ssot-input.json#items[DOG1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching pilot-baseline drives item DOG1 (unspecified dimension) through the interface declared for DOG1.

## Problem

Item DOG1 exists because the interface declared for DOG1 does not yet satisfy the acceptance seeds registered for it, leaving pilot-baseline incomplete.

## Expected outcome

After item DOG1 lands, the interface declared for DOG1 satisfies every acceptance seed below and pilot-baseline reflects that behavior.

## Non-goals

Item DOG1 covers only the interface declared for DOG1 and pilot-baseline as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches pilot-baseline for item DOG1
When the flow defined by the interface declared for DOG1 executes
Then every acceptance seed for item DOG1 holds
```

## Exception paths

If the interface declared for DOG1 fails for item DOG1, pilot-baseline must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item DOG1, the interface declared for DOG1 must continue to satisfy every acceptance seed below on every call; pilot-baseline must never show a state the seeds forbid.

## Data impact

Item DOG1 constrains any create, update, or delete reachable through the interface declared for DOG1; only the acceptance seeds below define what data changes are permitted for pilot-baseline. Node-specific data assertions: 在 benchmarks/runtime-pilot-plan.json 中固定首个真实任务、评价器、范围、预算和单成员基线 | 在 tests/test_runtime_pilot_baseline.py 中证明基线可重放且成功与失败条件可机器判断

## Permissions

Item DOG1 is owned by 试点任务负责人; access to the interface declared for DOG1 and pilot-baseline follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG1: the thresholds and failure evidence for the interface declared for DOG1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DOG1 | machine/e2e | 在 benchmarks/runtime-pilot-plan.json 中固定首个真实任务、评价器、范围、预算和单成员基线 | E2E | Automatic | Yes |
| AC-02 | behavior | SRC-DOG1 | persistent-runtime | 在 tests/test_runtime_pilot_baseline.py 中证明基线可重放且成功与失败条件可机器判断 | Persistent runtime | Automatic | Yes |

## Human acceptance

Item DOG1 is fully determined by its acceptance seeds; outcomes for the interface declared for DOG1 on pilot-baseline are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DOG1; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | benchmarks/runtime-pilot-plan.json | Automatic | Yes |
| AC-02 | Persistent runtime | tests/test_runtime_pilot_baseline.py | Automatic | Yes |

## Exploratory testing

Probe pilot-baseline for item DOG1 under retry, interruption, and boundary-value inputs against the interface declared for DOG1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DOG1 reverts the change to the interface declared for DOG1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG1: review risks specific to pilot-baseline and record any open decision.
