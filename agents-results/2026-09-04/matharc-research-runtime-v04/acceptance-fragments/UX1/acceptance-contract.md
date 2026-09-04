# Acceptance Contract: UX1

- Task ID: UX1
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 控制台投影负责人
- Approval evidence: TBD
- Request source: item UX1
- SSOT node: UX1
- SSOT path: .ssot/nodes/UX1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ux1
- AC budget: 2
- Baseline identity: ssot-input.json#items[UX1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching runtime-console-projection drives item UX1 (unspecified dimension) through the interface declared for UX1.

## Problem

Item UX1 exists because the interface declared for UX1 does not yet satisfy the acceptance seeds registered for it, leaving runtime-console-projection incomplete.

## Expected outcome

After item UX1 lands, the interface declared for UX1 satisfies every acceptance seed below and runtime-console-projection reflects that behavior.

## Non-goals

Item UX1 covers only the interface declared for UX1 and runtime-console-projection as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches runtime-console-projection for item UX1
When the flow defined by the interface declared for UX1 executes
Then every acceptance seed for item UX1 holds
```

## Exception paths

If the interface declared for UX1 fails for item UX1, runtime-console-projection must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item UX1, the interface declared for UX1 must continue to satisfy every acceptance seed below on every call; runtime-console-projection must never show a state the seeds forbid.

## Data impact

Item UX1 constrains any create, update, or delete reachable through the interface declared for UX1; only the acceptance seeds below define what data changes are permitted for runtime-console-projection. Node-specific data assertions: 在 matharc/v02/console_export.py 中将 RuntimeStore 状态投影到现有控制台数据合同 | 在 tests/test_runtime_console_projection.py 中证明投影不是第二真相源且不暴露主机绝对路径

## Permissions

Item UX1 is owned by 控制台投影负责人; access to the interface declared for UX1 and runtime-console-projection follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX1: the thresholds and failure evidence for the interface declared for UX1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/integration-contract | 在 matharc/v02/console_export.py 中将 RuntimeStore 状态投影到现有控制台数据合同 | Integration | Automatic | Yes |
| AC-02 | behavior | none | machine/e2e | 在 tests/test_runtime_console_projection.py 中证明投影不是第二真相源且不暴露主机绝对路径 | E2E | Automatic | Yes |

## Human acceptance

Item UX1 is fully determined by its acceptance seeds; outcomes for the interface declared for UX1 on runtime-console-projection are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item UX1; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/console_export.py | Automatic | Yes |
| AC-02 | E2E | tests/test_runtime_console_projection.py | Automatic | Yes |

## Exploratory testing

Probe runtime-console-projection for item UX1 under retry, interruption, and boundary-value inputs against the interface declared for UX1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item UX1 reverts the change to the interface declared for UX1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX1: review risks specific to runtime-console-projection and record any open decision.
