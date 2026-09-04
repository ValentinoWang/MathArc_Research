# Acceptance Contract: PAR5

- Task ID: PAR5
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 并行验收负责人
- Approval evidence: TBD
- Request source: item PAR5
- SSOT node: PAR5
- SSOT path: .ssot/nodes/PAR5.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.par5
- AC budget: 2
- Baseline identity: ssot-input.json#items[PAR5]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching parallel-generation drives item PAR5 (unspecified dimension) through the interface declared for PAR5.

## Problem

Item PAR5 exists because the interface declared for PAR5 does not yet satisfy the acceptance seeds registered for it, leaving parallel-generation incomplete.

## Expected outcome

After item PAR5 lands, the interface declared for PAR5 satisfies every acceptance seed below and parallel-generation reflects that behavior.

## Non-goals

Item PAR5 covers only the interface declared for PAR5 and parallel-generation as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches parallel-generation for item PAR5
When the flow defined by the interface declared for PAR5 executes
Then every acceptance seed for item PAR5 holds
```

## Exception paths

If the interface declared for PAR5 fails for item PAR5, parallel-generation must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item PAR5, the interface declared for PAR5 must continue to satisfy every acceptance seed below on every call; parallel-generation must never show a state the seeds forbid.

## Data impact

Item PAR5 constrains any create, update, or delete reachable through the interface declared for PAR5; only the acceptance seeds below define what data changes are permitted for parallel-generation. Node-specific data assertions: 在 tests/test_runtime_parallel_generation.py 中完成多研究成员一代结果汇总 | 在 tests/test_runtime_partial_failure.py 中证明部分成员失败仍生成合法、可审计的一代结果

## Permissions

Item PAR5 is owned by 并行验收负责人; access to the interface declared for PAR5 and parallel-generation follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR5: the thresholds and failure evidence for the interface declared for PAR5 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/e2e | 在 tests/test_runtime_parallel_generation.py 中完成多研究成员一代结果汇总 | E2E | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_runtime_partial_failure.py 中证明部分成员失败仍生成合法、可审计的一代结果 | Local runtime | Automatic | Yes |

## Human acceptance

Item PAR5 is fully determined by its acceptance seeds; outcomes for the interface declared for PAR5 on parallel-generation are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item PAR5; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_runtime_parallel_generation.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_partial_failure.py | Automatic | Yes |

## Exploratory testing

Probe parallel-generation for item PAR5 under retry, interruption, and boundary-value inputs against the interface declared for PAR5, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item PAR5 reverts the change to the interface declared for PAR5; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR5: review risks specific to parallel-generation and record any open decision.
