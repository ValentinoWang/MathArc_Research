# Acceptance Contract: RUN5

- Task ID: RUN5
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 单任务验收负责人
- Approval evidence: TBD
- Request source: item RUN5
- SSOT node: RUN5
- SSOT path: .ssot/nodes/RUN5.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.run5
- AC budget: 2
- Baseline identity: ssot-input.json#items[RUN5]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching single-run-e2e drives item RUN5 (unspecified dimension) through the interface declared for RUN5.

## Problem

Item RUN5 exists because the interface declared for RUN5 does not yet satisfy the acceptance seeds registered for it, leaving single-run-e2e incomplete.

## Expected outcome

After item RUN5 lands, the interface declared for RUN5 satisfies every acceptance seed below and single-run-e2e reflects that behavior.

## Non-goals

Item RUN5 covers only the interface declared for RUN5 and single-run-e2e as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches single-run-e2e for item RUN5
When the flow defined by the interface declared for RUN5 executes
Then every acceptance seed for item RUN5 holds
```

## Exception paths

If the interface declared for RUN5 fails for item RUN5, single-run-e2e must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item RUN5, the interface declared for RUN5 must continue to satisfy every acceptance seed below on every call; single-run-e2e must never show a state the seeds forbid.

## Data impact

Item RUN5 constrains any create, update, or delete reachable through the interface declared for RUN5; only the acceptance seeds below define what data changes are permitted for single-run-e2e. Node-specific data assertions: 在 tests/test_runtime_single_run.py 中完成真实任务到候选返回的端到端路径 | 在 tests/test_candidate_promotion_boundary.py 中拒绝候选直接进入 EvidenceRecord 或 PROVED

## Permissions

Item RUN5 is owned by 单任务验收负责人; access to the interface declared for RUN5 and single-run-e2e follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN5: the thresholds and failure evidence for the interface declared for RUN5 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/e2e | 在 tests/test_runtime_single_run.py 中完成真实任务到候选返回的端到端路径 | E2E | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_candidate_promotion_boundary.py 中拒绝候选直接进入 EvidenceRecord 或 PROVED | Local runtime | Automatic | Yes |

## Human acceptance

Item RUN5 is fully determined by its acceptance seeds; outcomes for the interface declared for RUN5 on single-run-e2e are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item RUN5; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_runtime_single_run.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_candidate_promotion_boundary.py | Automatic | Yes |

## Exploratory testing

Probe single-run-e2e for item RUN5 under retry, interruption, and boundary-value inputs against the interface declared for RUN5, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item RUN5 reverts the change to the interface declared for RUN5; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN5: review risks specific to single-run-e2e and record any open decision.
