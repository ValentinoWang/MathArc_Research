# Acceptance Contract: PAR4

- Task ID: PAR4
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 资源记账负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:h2[4]
- SSOT node: PAR4
- SSOT path: .ssot/nodes/PAR4.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.par4
- AC budget: 2
- Baseline identity: ssot-input.json#items[PAR4]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching resource-accounting drives item PAR4 (unspecified dimension) through the interface declared for PAR4.

## Problem

Item PAR4 exists because the interface declared for PAR4 does not yet satisfy the acceptance seeds registered for it, leaving resource-accounting incomplete.

## Expected outcome

After item PAR4 lands, the interface declared for PAR4 satisfies every acceptance seed below and resource-accounting reflects that behavior.

## Non-goals

Item PAR4 covers only the interface declared for PAR4 and resource-accounting as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches resource-accounting for item PAR4
When the flow defined by the interface declared for PAR4 executes
Then every acceptance seed for item PAR4 holds
```

## Exception paths

If the interface declared for PAR4 fails for item PAR4, resource-accounting must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item PAR4, the interface declared for PAR4 must continue to satisfy every acceptance seed below on every call; resource-accounting must never show a state the seeds forbid.

## Data impact

Item PAR4 constrains any create, update, or delete reachable through the interface declared for PAR4; only the acceptance seeds below define what data changes are permitted for resource-accounting. Node-specific data assertions: 在 matharc/v02/budget.py 中按运行回执记录实际费用而不是模型自报费用 | 在 tests/test_runtime_semantic_deduplication.py 中证明同一语义实验不会重复运行

## Permissions

Item PAR4 is owned by 资源记账负责人; access to the interface declared for PAR4 and resource-accounting follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR4: the thresholds and failure evidence for the interface declared for PAR4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PAR4 | machine/unit | 在 matharc/v02/budget.py 中按运行回执记录实际费用而不是模型自报费用 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-PAR4 | machine/non-functional | 在 tests/test_runtime_semantic_deduplication.py 中证明同一语义实验不会重复运行 | Non-functional | Automatic | Yes |

## Human acceptance

Item PAR4 is fully determined by its acceptance seeds; outcomes for the interface declared for PAR4 on resource-accounting are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item PAR4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/budget.py | Automatic | Yes |
| AC-02 | Non-functional | tests/test_runtime_semantic_deduplication.py | Automatic | Yes |

## Exploratory testing

Probe resource-accounting for item PAR4 under retry, interruption, and boundary-value inputs against the interface declared for PAR4, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item PAR4 reverts the change to the interface declared for PAR4; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR4: review risks specific to resource-accounting and record any open decision.
