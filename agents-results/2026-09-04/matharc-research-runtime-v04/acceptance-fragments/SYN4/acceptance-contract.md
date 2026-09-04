# Acceptance Contract: SYN4

- Task ID: SYN4
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 代际议程负责人
- Approval evidence: TBD
- Request source: item SYN4
- SSOT node: SYN4
- SSOT path: .ssot/nodes/SYN4.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.syn4
- AC budget: 2
- Baseline identity: ssot-input.json#items[SYN4]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching next-generation-agenda drives item SYN4 (unspecified dimension) through the interface declared for SYN4.

## Problem

Item SYN4 exists because the interface declared for SYN4 does not yet satisfy the acceptance seeds registered for it, leaving next-generation-agenda incomplete.

## Expected outcome

After item SYN4 lands, the interface declared for SYN4 satisfies every acceptance seed below and next-generation-agenda reflects that behavior.

## Non-goals

Item SYN4 covers only the interface declared for SYN4 and next-generation-agenda as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches next-generation-agenda for item SYN4
When the flow defined by the interface declared for SYN4 executes
Then every acceptance seed for item SYN4 holds
```

## Exception paths

If the interface declared for SYN4 fails for item SYN4, next-generation-agenda must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item SYN4, the interface declared for SYN4 must continue to satisfy every acceptance seed below on every call; next-generation-agenda must never show a state the seeds forbid.

## Data impact

Item SYN4 constrains any create, update, or delete reachable through the interface declared for SYN4; only the acceptance seeds below define what data changes are permitted for next-generation-agenda. Node-specific data assertions: 在 matharc/v02/research_director/agenda.py 中把失败、经历、评审缺口和路线变换编译为下一代议程 | 在 tests/test_runtime_next_generation_agenda.py 中要求下一代明确引用上一代事实

## Permissions

Item SYN4 is owned by 代际议程负责人; access to the interface declared for SYN4 and next-generation-agenda follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN4: the thresholds and failure evidence for the interface declared for SYN4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/integration-contract | 在 matharc/v02/research_director/agenda.py 中把失败、经历、评审缺口和路线变换编译为下一代议程 | Integration | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_runtime_next_generation_agenda.py 中要求下一代明确引用上一代事实 | Local runtime | Automatic | Yes |

## Human acceptance

Item SYN4 is fully determined by its acceptance seeds; outcomes for the interface declared for SYN4 on next-generation-agenda are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item SYN4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/research_director/agenda.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_next_generation_agenda.py | Automatic | Yes |

## Exploratory testing

Probe next-generation-agenda for item SYN4 under retry, interruption, and boundary-value inputs against the interface declared for SYN4, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item SYN4 reverts the change to the interface declared for SYN4; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN4: review risks specific to next-generation-agenda and record any open decision.
