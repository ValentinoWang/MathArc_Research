# Acceptance Contract: UX3

- Task ID: UX3
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 运行动作 API 负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[15]
- SSOT node: UX3
- SSOT path: .ssot/nodes/UX3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ux3
- AC budget: 2
- Baseline identity: ssot-input.json#items[UX3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching runtime-actions-api drives item UX3 (unspecified dimension) through POST /api/runtime/runs, POST /api/runtime/actions.

## Problem

Item UX3 exists because POST /api/runtime/runs, POST /api/runtime/actions does not yet satisfy the acceptance seeds registered for it, leaving runtime-actions-api incomplete.

## Expected outcome

After item UX3 lands, POST /api/runtime/runs, POST /api/runtime/actions satisfies every acceptance seed below and runtime-actions-api reflects that behavior.

## Non-goals

Item UX3 covers only POST /api/runtime/runs, POST /api/runtime/actions and runtime-actions-api as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches runtime-actions-api for item UX3
When the flow defined by POST /api/runtime/runs, POST /api/runtime/actions executes
Then every acceptance seed for item UX3 holds
```

## Exception paths

If POST /api/runtime/runs, POST /api/runtime/actions fails for item UX3, runtime-actions-api must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item UX3, POST /api/runtime/runs, POST /api/runtime/actions must continue to satisfy every acceptance seed below on every call; runtime-actions-api must never show a state the seeds forbid.

## Data impact

Item UX3 constrains any create, update, or delete reachable through POST /api/runtime/runs, POST /api/runtime/actions; only the acceptance seeds below define what data changes are permitted for runtime-actions-api. Node-specific data assertions: 在 matharc/v02/runtime/service.py 中提供启动、暂停、继续、停止和重新验证的幂等动作 | 在 tests/test_runtime_command_surface.py 中拒绝 command、cwd、environment、executable 和任意 arguments 字段

## Permissions

Item UX3 is owned by 运行动作 API 负责人; access to POST /api/runtime/runs, POST /api/runtime/actions and runtime-actions-api follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX3: the thresholds and failure evidence for POST /api/runtime/runs, POST /api/runtime/actions must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-UX3 | machine/integration-contract | 在 matharc/v02/runtime/service.py 中提供启动、暂停、继续、停止和重新验证的幂等动作 | Integration | Automatic | Yes |
| AC-02 | behavior | SRC-UX3 | machine/e2e | 在 tests/test_runtime_command_surface.py 中拒绝 command、cwd、environment、executable 和任意 arguments 字段 | E2E | Automatic | Yes |

## Human acceptance

Item UX3 is fully determined by its acceptance seeds; outcomes for POST /api/runtime/runs, POST /api/runtime/actions on runtime-actions-api are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item UX3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/runtime/service.py | Automatic | Yes |
| AC-02 | E2E | tests/test_runtime_command_surface.py | Automatic | Yes |

## Exploratory testing

Probe runtime-actions-api for item UX3 under retry, interruption, and boundary-value inputs against POST /api/runtime/runs, POST /api/runtime/actions, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item UX3 reverts the change to POST /api/runtime/runs, POST /api/runtime/actions; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX3: review risks specific to runtime-actions-api and record any open decision.
