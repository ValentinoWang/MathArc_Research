# Acceptance Contract: RUN3

- Task ID: RUN3
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 评价器负责人
- Approval evidence: TBD
- Request source: item RUN3
- SSOT node: RUN3
- SSOT path: .ssot/nodes/RUN3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.run3
- AC budget: 2
- Baseline identity: ssot-input.json#items[RUN3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching evaluation-contract drives item RUN3 (unspecified dimension) through the interface declared for RUN3.

## Problem

Item RUN3 exists because the interface declared for RUN3 does not yet satisfy the acceptance seeds registered for it, leaving evaluation-contract incomplete.

## Expected outcome

After item RUN3 lands, the interface declared for RUN3 satisfies every acceptance seed below and evaluation-contract reflects that behavior.

## Non-goals

Item RUN3 covers only the interface declared for RUN3 and evaluation-contract as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches evaluation-contract for item RUN3
When the flow defined by the interface declared for RUN3 executes
Then every acceptance seed for item RUN3 holds
```

## Exception paths

If the interface declared for RUN3 fails for item RUN3, evaluation-contract must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item RUN3, the interface declared for RUN3 must continue to satisfy every acceptance seed below on every call; evaluation-contract must never show a state the seeds forbid.

## Data impact

Item RUN3 constrains any create, update, or delete reachable through the interface declared for RUN3; only the acceptance seeds below define what data changes are permitted for evaluation-contract. Node-specific data assertions: 在 matharc/v02/evaluator.py 中定义评价器输入、输出、预算和随机种子合同 | 在 tests/test_runtime_evaluator.py 中证明最小试跑失败时不会启动完整研究

## Permissions

Item RUN3 is owned by 评价器负责人; access to the interface declared for RUN3 and evaluation-contract follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN3: the thresholds and failure evidence for the interface declared for RUN3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/unit | 在 matharc/v02/evaluator.py 中定义评价器输入、输出、预算和随机种子合同 | Unit | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_runtime_evaluator.py 中证明最小试跑失败时不会启动完整研究 | Local runtime | Automatic | Yes |

## Human acceptance

Item RUN3 is fully determined by its acceptance seeds; outcomes for the interface declared for RUN3 on evaluation-contract are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item RUN3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/evaluator.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_evaluator.py | Automatic | Yes |

## Exploratory testing

Probe evaluation-contract for item RUN3 under retry, interruption, and boundary-value inputs against the interface declared for RUN3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item RUN3 reverts the change to the interface declared for RUN3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN3: review risks specific to evaluation-contract and record any open decision.
