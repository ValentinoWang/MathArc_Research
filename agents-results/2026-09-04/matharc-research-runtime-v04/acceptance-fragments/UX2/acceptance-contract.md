# Acceptance Contract: UX2

- Task ID: UX2
- Contract kind: implementation
- Contract profile: acceptance-contract-kind-profiles@1
- Verification layer: machine
- Acceptance mode: Automatic
- Evidence target: test result
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: principal:acceptance-a
- Execution actor: orchestrator
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-UX2
- SSOT node: UX2
- SSOT path: .ssot/nodes/UX2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ux2
- AC budget: 2
- Baseline identity: ssot-input.json#items[UX2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching invited-access drives item UX2 (unspecified dimension) through the interface declared for UX2.

## Problem

Item UX2 exists because the interface declared for UX2 does not yet satisfy the acceptance seeds registered for it, leaving invited-access incomplete.

## Expected outcome

After item UX2 lands, the interface declared for UX2 satisfies every acceptance seed below and invited-access reflects that behavior.

## Non-goals

Item UX2 covers only the interface declared for UX2 and invited-access as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches invited-access for item UX2
When the flow defined by the interface declared for UX2 executes
Then every acceptance seed for item UX2 holds
```

## Exception paths

If the interface declared for UX2 fails for item UX2, invited-access must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item UX2, the interface declared for UX2 must continue to satisfy every acceptance seed below on every call; invited-access must never show a state the seeds forbid.

## Data impact

Item UX2 constrains any create, update, or delete reachable through the interface declared for UX2; only the acceptance seeds below define what data changes are permitted for invited-access. Node-specific data assertions: 在 matharc/v02/runtime/service.py 中复用现有邀请制访问和 Cookie 会话边界 | 在 tests/test_runtime_console_permissions.py 中证明没有操作权限的用户不能启动或停止任务

## Permissions

Item UX2 is owned by principal:acceptance-a; access to the interface declared for UX2 and invited-access follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX2: the thresholds and failure evidence for the interface declared for UX2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-UX2 | machine/integration-contract | 在 matharc/v02/runtime/service.py 中复用现有邀请制访问和 Cookie 会话边界 | Integration | Automatic | Yes |
| AC-02 | behavior | SRC-UX2 | machine/e2e | 在 tests/test_runtime_console_permissions.py 中证明没有操作权限的用户不能启动或停止任务 | E2E | Automatic | Yes |

## Human acceptance

Item UX2 is fully determined by its acceptance seeds; outcomes for the interface declared for UX2 on invited-access are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item UX2; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/runtime/service.py | Automatic | Yes |
| AC-02 | E2E | tests/test_runtime_console_permissions.py | Automatic | Yes |

## Exploratory testing

Probe invited-access for item UX2 under retry, interruption, and boundary-value inputs against the interface declared for UX2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item UX2 reverts the change to the interface declared for UX2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX2: review risks specific to invited-access and record any open decision.
