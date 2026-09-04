# Acceptance Contract: PAR3

- Task ID: PAR3
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 并发调度负责人
- Approval evidence: TBD
- Request source: item PAR3
- SSOT node: PAR3
- SSOT path: .ssot/nodes/PAR3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.par3
- AC budget: 2
- Baseline identity: ssot-input.json#items[PAR3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching bounded-parallelism drives item PAR3 (unspecified dimension) through the interface declared for PAR3.

## Problem

Item PAR3 exists because the interface declared for PAR3 does not yet satisfy the acceptance seeds registered for it, leaving bounded-parallelism incomplete.

## Expected outcome

After item PAR3 lands, the interface declared for PAR3 satisfies every acceptance seed below and bounded-parallelism reflects that behavior.

## Non-goals

Item PAR3 covers only the interface declared for PAR3 and bounded-parallelism as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches bounded-parallelism for item PAR3
When the flow defined by the interface declared for PAR3 executes
Then every acceptance seed for item PAR3 holds
```

## Exception paths

If the interface declared for PAR3 fails for item PAR3, bounded-parallelism must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item PAR3, the interface declared for PAR3 must continue to satisfy every acceptance seed below on every call; bounded-parallelism must never show a state the seeds forbid.

## Data impact

Item PAR3 constrains any create, update, or delete reachable through the interface declared for PAR3; only the acceptance seeds below define what data changes are permitted for bounded-parallelism. Node-specific data assertions: 在 matharc/v02/scheduler.py 中实现有界并发、独立 execution_id 和隔离工作区 | 在 tests/test_runtime_parallelism.py 中证明至少三个不同进程存在真实时间重叠且写入区域无交集

## Permissions

Item PAR3 is owned by 并发调度负责人; access to the interface declared for PAR3 and bounded-parallelism follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR3: the thresholds and failure evidence for the interface declared for PAR3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/non-functional | 在 matharc/v02/scheduler.py 中实现有界并发、独立 execution_id 和隔离工作区 | Non-functional | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_runtime_parallelism.py 中证明至少三个不同进程存在真实时间重叠且写入区域无交集 | Local runtime | Automatic | Yes |

## Human acceptance

Item PAR3 is fully determined by its acceptance seeds; outcomes for the interface declared for PAR3 on bounded-parallelism are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item PAR3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Non-functional | matharc/v02/scheduler.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_parallelism.py | Automatic | Yes |

## Exploratory testing

Probe bounded-parallelism for item PAR3 under retry, interruption, and boundary-value inputs against the interface declared for PAR3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item PAR3 reverts the change to the interface declared for PAR3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR3: review risks specific to bounded-parallelism and record any open decision.
