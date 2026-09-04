# Acceptance Contract: PAR2

- Task ID: PAR2
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 任务审批接线负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[5]
- SSOT node: PAR2
- SSOT path: .ssot/nodes/PAR2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.par2
- AC budget: 2
- Baseline identity: ssot-input.json#items[PAR2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching approved-task-ingestion drives item PAR2 (unspecified dimension) through the interface declared for PAR2.

## Problem

Item PAR2 exists because the interface declared for PAR2 does not yet satisfy the acceptance seeds registered for it, leaving approved-task-ingestion incomplete.

## Expected outcome

After item PAR2 lands, the interface declared for PAR2 satisfies every acceptance seed below and approved-task-ingestion reflects that behavior.

## Non-goals

Item PAR2 covers only the interface declared for PAR2 and approved-task-ingestion as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches approved-task-ingestion for item PAR2
When the flow defined by the interface declared for PAR2 executes
Then every acceptance seed for item PAR2 holds
```

## Exception paths

If the interface declared for PAR2 fails for item PAR2, approved-task-ingestion must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item PAR2, the interface declared for PAR2 must continue to satisfy every acceptance seed below on every call; approved-task-ingestion must never show a state the seeds forbid.

## Data impact

Item PAR2 constrains any create, update, or delete reachable through the interface declared for PAR2; only the acceptance seeds below define what data changes are permitted for approved-task-ingestion. Node-specific data assertions: 在 matharc/v02/orchestrator.py 中消费现有动态派生任务批准记录并保持一次性启动 | 在 tests/test_runtime_approved_task_ingestion.py 中证明拒绝任务和超预算任务永不启动

## Permissions

Item PAR2 is owned by 任务审批接线负责人; access to the interface declared for PAR2 and approved-task-ingestion follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR2: the thresholds and failure evidence for the interface declared for PAR2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PAR2 | machine/integration-contract | 在 matharc/v02/orchestrator.py 中消费现有动态派生任务批准记录并保持一次性启动 | Integration | Automatic | Yes |
| AC-02 | behavior | SRC-PAR2 | machine/local-runtime | 在 tests/test_runtime_approved_task_ingestion.py 中证明拒绝任务和超预算任务永不启动 | Local runtime | Automatic | Yes |

## Human acceptance

Item PAR2 is fully determined by its acceptance seeds; outcomes for the interface declared for PAR2 on approved-task-ingestion are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item PAR2; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/orchestrator.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_approved_task_ingestion.py | Automatic | Yes |

## Exploratory testing

Probe approved-task-ingestion for item PAR2 under retry, interruption, and boundary-value inputs against the interface declared for PAR2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item PAR2 reverts the change to the interface declared for PAR2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR2: review risks specific to approved-task-ingestion and record any open decision.
