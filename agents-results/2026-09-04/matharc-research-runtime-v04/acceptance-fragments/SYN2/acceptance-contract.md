# Acceptance Contract: SYN2

- Task ID: SYN2
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 反例复核负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[12]
- SSOT node: SYN2
- SSOT path: .ssot/nodes/SYN2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.syn2
- AC budget: 2
- Baseline identity: ssot-input.json#items[SYN2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching counterexample-review drives item SYN2 (unspecified dimension) through the interface declared for SYN2.

## Problem

Item SYN2 exists because the interface declared for SYN2 does not yet satisfy the acceptance seeds registered for it, leaving counterexample-review incomplete.

## Expected outcome

After item SYN2 lands, the interface declared for SYN2 satisfies every acceptance seed below and counterexample-review reflects that behavior.

## Non-goals

Item SYN2 covers only the interface declared for SYN2 and counterexample-review as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches counterexample-review for item SYN2
When the flow defined by the interface declared for SYN2 executes
Then every acceptance seed for item SYN2 holds
```

## Exception paths

If the interface declared for SYN2 fails for item SYN2, counterexample-review must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item SYN2, the interface declared for SYN2 must continue to satisfy every acceptance seed below on every call; counterexample-review must never show a state the seeds forbid.

## Data impact

Item SYN2 constrains any create, update, or delete reachable through the interface declared for SYN2; only the acceptance seeds below define what data changes are permitted for counterexample-review. Node-specific data assertions: 在 matharc/v02/synthesis.py 中把疑似反例放入独立复核队列 | 在 tests/test_runtime_counterexample_review.py 中证明未复核反例不会改变路线或结论

## Permissions

Item SYN2 is owned by 反例复核负责人; access to the interface declared for SYN2 and counterexample-review follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN2: the thresholds and failure evidence for the interface declared for SYN2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-SYN2 | machine/unit | 在 matharc/v02/synthesis.py 中把疑似反例放入独立复核队列 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-SYN2 | machine/integration-contract | 在 tests/test_runtime_counterexample_review.py 中证明未复核反例不会改变路线或结论 | Integration | Automatic | Yes |

## Human acceptance

Item SYN2 is fully determined by its acceptance seeds; outcomes for the interface declared for SYN2 on counterexample-review are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item SYN2; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/synthesis.py | Automatic | Yes |
| AC-02 | Integration | tests/test_runtime_counterexample_review.py | Automatic | Yes |

## Exploratory testing

Probe counterexample-review for item SYN2 under retry, interruption, and boundary-value inputs against the interface declared for SYN2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item SYN2 reverts the change to the interface declared for SYN2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN2: review risks specific to counterexample-review and record any open decision.
