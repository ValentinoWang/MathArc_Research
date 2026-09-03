# Acceptance Contract: P1

- Task ID: P1
- Contract version: 1
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: Harness 推送资格负责人
- Approval evidence: protected-tests-locked: .agents/skills/report-to-ssot-development-paths/tests/test_execution_gates.py, .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py
- Request source: item P1
- SSOT node: P1
- SSOT path: .ssot/nodes/P1.json
- Readiness mode: FORMAL
- Decision refs: decision.execution-plane.scope@1
- Assumption IDs: none
- Invalidation keys: task.p1
- AC budget: 2
- Baseline identity: ssot-input.json#items[P1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching validation-binding-and-complexity-accounting drives item P1 (unspecified dimension) through the interface declared for P1.

## Problem

Item P1 exists because the interface declared for P1 does not yet satisfy the acceptance seeds registered for it, leaving validation-binding-and-complexity-accounting incomplete.

## Expected outcome

After item P1 lands, the interface declared for P1 satisfies every acceptance seed below and validation-binding-and-complexity-accounting reflects that behavior.

## Non-goals

Item P1 covers only the interface declared for P1 and validation-binding-and-complexity-accounting as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches validation-binding-and-complexity-accounting for item P1
When the flow defined by the interface declared for P1 executes
Then every acceptance seed for item P1 holds
```

## Exception paths

If the interface declared for P1 fails for item P1, validation-binding-and-complexity-accounting must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item P1, the interface declared for P1 must continue to satisfy every acceptance seed below on every call; validation-binding-and-complexity-accounting must never show a state the seeds forbid.

## Data impact

Item P1 constrains any create, update, or delete reachable through the interface declared for P1; only the acceptance seeds below define what data changes are permitted for validation-binding-and-complexity-accounting. Node-specific data assertions: 在 .agents/skills/report-to-ssot-development-paths/tests/test_execution_gates.py 中证明 validation 后修改报告或修改 bundle 都会使 check_push_gate.py 失败 | 在 .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py 中证明 strict 单发布 bundle 实际生成四个视图时 inventory 报告四个而不是 planning record 的一个

## Permissions

Item P1 is owned by Harness 推送资格负责人; access to the interface declared for P1 and validation-binding-and-complexity-accounting follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item P1: the thresholds and failure evidence for the interface declared for P1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/unit | 在 .agents/skills/report-to-ssot-development-paths/tests/test_execution_gates.py 中证明 validation 后修改报告或修改 bundle 都会使 check_push_gate.py 失败 | Unit | Automatic | Yes |
| AC-02 | behavior | none | machine/integration-contract | 在 .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py 中证明 strict 单发布 bundle 实际生成四个视图时 inventory 报告四个而不是 planning record 的一个 | Integration | Automatic | Yes |

## Human acceptance

Item P1 is fully determined by its acceptance seeds; outcomes for the interface declared for P1 on validation-binding-and-complexity-accounting are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
| .agents/skills/report-to-ssot-development-paths/tests/test_execution_gates.py | 443d99f0d6734873715135d979bbcd172adc41cff0088f2109de144352c609e7 | Stale validation binding and push-gate cases |
| .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py | a1dfbeee03d028f2fcbe366e79781f663fbc19fd136b3d40261172a75e082873 | Generated-view complexity cases |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | .agents/skills/report-to-ssot-development-paths/tests/test_execution_gates.py | Automatic | Yes |
| AC-02 | Integration | .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py | Automatic | Yes |

## Exploratory testing

Probe validation-binding-and-complexity-accounting for item P1 under retry, interruption, and boundary-value inputs against the interface declared for P1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item P1 reverts the change to the interface declared for P1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item P1: review risks specific to validation-binding-and-complexity-accounting and record any open decision.
