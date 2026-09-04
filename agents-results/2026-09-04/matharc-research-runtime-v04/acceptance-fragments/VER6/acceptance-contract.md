# Acceptance Contract: VER6

- Task ID: VER6
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 验证汇合负责人
- Approval evidence: TBD
- Request source: item VER6
- SSOT node: VER6
- SSOT path: .ssot/nodes/VER6.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ver6
- AC budget: 2
- Baseline identity: ssot-input.json#items[VER6]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching verification-gate drives item VER6 (unspecified dimension) through the interface declared for VER6.

## Problem

Item VER6 exists because the interface declared for VER6 does not yet satisfy the acceptance seeds registered for it, leaving verification-gate incomplete.

## Expected outcome

After item VER6 lands, the interface declared for VER6 satisfies every acceptance seed below and verification-gate reflects that behavior.

## Non-goals

Item VER6 covers only the interface declared for VER6 and verification-gate as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches verification-gate for item VER6
When the flow defined by the interface declared for VER6 executes
Then every acceptance seed for item VER6 holds
```

## Exception paths

If the interface declared for VER6 fails for item VER6, verification-gate must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item VER6, the interface declared for VER6 must continue to satisfy every acceptance seed below on every call; verification-gate must never show a state the seeds forbid.

## Data impact

Item VER6 constrains any create, update, or delete reachable through the interface declared for VER6; only the acceptance seeds below define what data changes are permitted for verification-gate. Node-specific data assertions: 在 tests/test_verification_convergence.py 中证明真实候选通过独立验证后才形成正式证据 | 在 tests/test_verification_negative_paths.py 中阻止假候选、篡改包、越界和非独立结果

## Permissions

Item VER6 is owned by 验证汇合负责人; access to the interface declared for VER6 and verification-gate follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER6: the thresholds and failure evidence for the interface declared for VER6 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/e2e | 在 tests/test_verification_convergence.py 中证明真实候选通过独立验证后才形成正式证据 | E2E | Automatic | Yes |
| AC-02 | behavior | none | machine/integration-contract | 在 tests/test_verification_negative_paths.py 中阻止假候选、篡改包、越界和非独立结果 | Integration | Automatic | Yes |

## Human acceptance

Item VER6 is fully determined by its acceptance seeds; outcomes for the interface declared for VER6 on verification-gate are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item VER6; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_verification_convergence.py | Automatic | Yes |
| AC-02 | Integration | tests/test_verification_negative_paths.py | Automatic | Yes |

## Exploratory testing

Probe verification-gate for item VER6 under retry, interruption, and boundary-value inputs against the interface declared for VER6, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item VER6 reverts the change to the interface declared for VER6; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER6: review risks specific to verification-gate and record any open decision.
