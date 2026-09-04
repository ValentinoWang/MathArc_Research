# Acceptance Contract: UX6

- Task ID: UX6
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 浏览器产品验收负责人
- Approval evidence: TBD
- Request source: item UX6
- SSOT node: UX6
- SSOT path: .ssot/nodes/UX6.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ux6
- AC budget: 2
- Baseline identity: ssot-input.json#items[UX6]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching console-human-acceptance drives item UX6 (unspecified dimension) through the interface declared for UX6.

## Problem

Item UX6 exists because the interface declared for UX6 does not yet satisfy the acceptance seeds registered for it, leaving console-human-acceptance incomplete.

## Expected outcome

After item UX6 lands, the interface declared for UX6 satisfies every acceptance seed below and console-human-acceptance reflects that behavior.

## Non-goals

Item UX6 covers only the interface declared for UX6 and console-human-acceptance as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches console-human-acceptance for item UX6
When the flow defined by the interface declared for UX6 executes
Then every acceptance seed for item UX6 holds
```

## Exception paths

If the interface declared for UX6 fails for item UX6, console-human-acceptance must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item UX6, the interface declared for UX6 must continue to satisfy every acceptance seed below on every call; console-human-acceptance must never show a state the seeds forbid.

## Data impact

Item UX6 constrains any create, update, or delete reachable through the interface declared for UX6; only the acceptance seeds below define what data changes are permitted for console-human-acceptance. Node-specific data assertions: 在 acceptance/human/runtime-console/desktop-checklist.md 中覆盖桌面邀请制查看和操作流程 | 在 tests/test_runtime_console_mobile.py 中覆盖移动端、权限负路径和完整操作流

## Permissions

Item UX6 is owned by 浏览器产品验收负责人; access to the interface declared for UX6 and console-human-acceptance follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX6: the thresholds and failure evidence for the interface declared for UX6 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/e2e | 在 acceptance/human/runtime-console/desktop-checklist.md 中覆盖桌面邀请制查看和操作流程 | E2E | Automatic | Yes |
| AC-02 | behavior | none | visual-fidelity | 在 tests/test_runtime_console_mobile.py 中覆盖移动端、权限负路径和完整操作流 | Visual fidelity | Automatic | Yes |

## Human acceptance

Item UX6 is fully determined by its acceptance seeds; outcomes for the interface declared for UX6 on console-human-acceptance are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item UX6; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | acceptance/human/runtime-console/desktop-checklist.md | Automatic | Yes |
| AC-02 | Visual fidelity | tests/test_runtime_console_mobile.py | Automatic | Yes |

## Exploratory testing

Probe console-human-acceptance for item UX6 under retry, interruption, and boundary-value inputs against the interface declared for UX6, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item UX6 reverts the change to the interface declared for UX6; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX6: review risks specific to console-human-acceptance and record any open decision.
