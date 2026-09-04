# Acceptance Contract: SYN3

- Task ID: SYN3
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 研究记忆负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[13]
- SSOT node: SYN3
- SSOT path: .ssot/nodes/SYN3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.syn3
- AC budget: 2
- Baseline identity: ssot-input.json#items[SYN3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching research-memory drives item SYN3 (unspecified dimension) through the interface declared for SYN3.

## Problem

Item SYN3 exists because the interface declared for SYN3 does not yet satisfy the acceptance seeds registered for it, leaving research-memory incomplete.

## Expected outcome

After item SYN3 lands, the interface declared for SYN3 satisfies every acceptance seed below and research-memory reflects that behavior.

## Non-goals

Item SYN3 covers only the interface declared for SYN3 and research-memory as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches research-memory for item SYN3
When the flow defined by the interface declared for SYN3 executes
Then every acceptance seed for item SYN3 holds
```

## Exception paths

If the interface declared for SYN3 fails for item SYN3, research-memory must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item SYN3, the interface declared for SYN3 must continue to satisfy every acceptance seed below on every call; research-memory must never show a state the seeds forbid.

## Data impact

Item SYN3 constrains any create, update, or delete reachable through the interface declared for SYN3; only the acceptance seeds below define what data changes are permitted for research-memory. Node-specific data assertions: 在 matharc/v02/episode_memory.py 中从真实运行蒸馏 FailureMemory 与 EpisodeMemory 记录 | 在 tests/test_runtime_memory_provenance.py 中要求每条记忆携带 run_id、generation_id 和候选出处

## Permissions

Item SYN3 is owned by 研究记忆负责人; access to the interface declared for SYN3 and research-memory follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN3: the thresholds and failure evidence for the interface declared for SYN3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-SYN3 | machine/unit | 在 matharc/v02/episode_memory.py 中从真实运行蒸馏 FailureMemory 与 EpisodeMemory 记录 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-SYN3 | machine/local-runtime | 在 tests/test_runtime_memory_provenance.py 中要求每条记忆携带 run_id、generation_id 和候选出处 | Local runtime | Automatic | Yes |

## Human acceptance

Item SYN3 is fully determined by its acceptance seeds; outcomes for the interface declared for SYN3 on research-memory are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item SYN3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/episode_memory.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_memory_provenance.py | Automatic | Yes |

## Exploratory testing

Probe research-memory for item SYN3 under retry, interruption, and boundary-value inputs against the interface declared for SYN3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item SYN3 reverts the change to the interface declared for SYN3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN3: review risks specific to research-memory and record any open decision.
