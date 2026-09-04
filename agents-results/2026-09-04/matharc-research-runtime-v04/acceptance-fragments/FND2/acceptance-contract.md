# Acceptance Contract: FND2

- Task ID: FND2
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: MathArc 研究协议负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[1]
- SSOT node: FND2
- SSOT path: .ssot/nodes/FND2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.fnd2
- AC budget: 2
- Baseline identity: ssot-input.json#items[FND2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching authority-boundaries drives item FND2 (unspecified dimension) through the interface declared for FND2.

## Problem

Item FND2 exists because the interface declared for FND2 does not yet satisfy the acceptance seeds registered for it, leaving authority-boundaries incomplete.

## Expected outcome

After item FND2 lands, the interface declared for FND2 satisfies every acceptance seed below and authority-boundaries reflects that behavior.

## Non-goals

Item FND2 covers only the interface declared for FND2 and authority-boundaries as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches authority-boundaries for item FND2
When the flow defined by the interface declared for FND2 executes
Then every acceptance seed for item FND2 holds
```

## Exception paths

If the interface declared for FND2 fails for item FND2, authority-boundaries must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item FND2, the interface declared for FND2 must continue to satisfy every acceptance seed below on every call; authority-boundaries must never show a state the seeds forbid.

## Data impact

Item FND2 constrains any create, update, or delete reachable through the interface declared for FND2; only the acceptance seeds below define what data changes are permitted for authority-boundaries. Node-specific data assertions: 在 matharc/v02/trace.py 中保持 ResearchTrace 作为唯一数学结论晋升权威 | 在 tests/test_runtime_authority_boundaries.py 中证明 RuntimeStore 状态不能直接写成 PROVED

## Permissions

Item FND2 is owned by MathArc 研究协议负责人; access to the interface declared for FND2 and authority-boundaries follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item FND2: the thresholds and failure evidence for the interface declared for FND2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-FND2 | machine/unit | 在 matharc/v02/trace.py 中保持 ResearchTrace 作为唯一数学结论晋升权威 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-FND2 | machine/integration-contract | 在 tests/test_runtime_authority_boundaries.py 中证明 RuntimeStore 状态不能直接写成 PROVED | Integration | Automatic | Yes |

## Human acceptance

Item FND2 is fully determined by its acceptance seeds; outcomes for the interface declared for FND2 on authority-boundaries are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item FND2; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/trace.py | Automatic | Yes |
| AC-02 | Integration | tests/test_runtime_authority_boundaries.py | Automatic | Yes |

## Exploratory testing

Probe authority-boundaries for item FND2 under retry, interruption, and boundary-value inputs against the interface declared for FND2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item FND2 reverts the change to the interface declared for FND2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item FND2: review risks specific to authority-boundaries and record any open decision.
