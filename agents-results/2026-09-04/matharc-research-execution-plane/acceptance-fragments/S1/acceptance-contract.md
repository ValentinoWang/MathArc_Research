# Acceptance Contract: S1

- Task ID: S1
- Contract version: 1
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: Harness 状态模型负责人
- Approval evidence: protected-tests-locked: .agents/skills/report-to-ssot-development-paths/tests/test_ssot_state_model.py, .agents/skills/report-to-ssot-development-paths/tests/test_ssot_readiness.py
- Request source: item S1
- SSOT node: S1
- SSOT path: .ssot/nodes/S1.json
- Readiness mode: FORMAL
- Decision refs: decision.execution-plane.scope@1
- Assumption IDs: none
- Invalidation keys: task.s1
- AC budget: 2
- Baseline identity: ssot-input.json#items[S1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching execution-state-lifecycle-and-l1-readiness drives item S1 (unspecified dimension) through the interface declared for S1.

## Problem

Item S1 exists because the interface declared for S1 does not yet satisfy the acceptance seeds registered for it, leaving execution-state-lifecycle-and-l1-readiness incomplete.

## Expected outcome

After item S1 lands, the interface declared for S1 satisfies every acceptance seed below and execution-state-lifecycle-and-l1-readiness reflects that behavior.

## Non-goals

Item S1 covers only the interface declared for S1 and execution-state-lifecycle-and-l1-readiness as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches execution-state-lifecycle-and-l1-readiness for item S1
When the flow defined by the interface declared for S1 executes
Then every acceptance seed for item S1 holds
```

## Exception paths

If the interface declared for S1 fails for item S1, execution-state-lifecycle-and-l1-readiness must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item S1, the interface declared for S1 must continue to satisfy every acceptance seed below on every call; execution-state-lifecycle-and-l1-readiness must never show a state the seeds forbid.

## Data impact

Item S1 constrains any create, update, or delete reachable through the interface declared for S1; only the acceptance seeds below define what data changes are permitted for execution-state-lifecycle-and-l1-readiness. Node-specific data assertions: 在 .agents/skills/report-to-ssot-development-paths/tests/test_ssot_state_model.py 中证明 PLANNED、READY、BLOCKED、RUNNING、IMPLEMENTED、VERIFIED、ACCEPTED、FAILED、INVALIDATED 的转换前提只有一个正式定义 | 在 .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py 中证明 L1 bundle 不加载 worker ledger、runner registry 或外部候选工作区，并能由 orchestrator 推进到 ACCEPTED

## Permissions

Item S1 is owned by Harness 状态模型负责人; access to the interface declared for S1 and execution-state-lifecycle-and-l1-readiness follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item S1: the thresholds and failure evidence for the interface declared for S1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/unit | 在 .agents/skills/report-to-ssot-development-paths/tests/test_ssot_state_model.py 中证明 PLANNED、READY、BLOCKED、RUNNING、IMPLEMENTED、VERIFIED、ACCEPTED、FAILED、INVALIDATED 的转换前提只有一个正式定义 | Unit | Automatic | Yes |
| AC-02 | behavior | none | machine/integration-contract | 在 .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py 中证明 L1 bundle 不加载 worker ledger、runner registry 或外部候选工作区，并能由 orchestrator 推进到 ACCEPTED | Integration | Automatic | Yes |

## Human acceptance

Item S1 is fully determined by its acceptance seeds; outcomes for the interface declared for S1 on execution-state-lifecycle-and-l1-readiness are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
| .agents/skills/report-to-ssot-development-paths/tests/test_ssot_state_model.py | 2563becc12061dd45c557e271bd4b983014577fab980366ec04b8cb58d9fc2b6 | Node state transition cases |
| .agents/skills/report-to-ssot-development-paths/tests/test_ssot_readiness.py | 629547e533dbe9a800d4f5834849125ae1dfeee7b293e6e7f6ee250db2425903 | Readiness derivation cases |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | .agents/skills/report-to-ssot-development-paths/tests/test_ssot_state_model.py | Automatic | Yes |
| AC-02 | Integration | .agents/skills/report-to-ssot-development-paths/tests/test_ssot_complexity.py | Automatic | Yes |

## Exploratory testing

Probe execution-state-lifecycle-and-l1-readiness for item S1 under retry, interruption, and boundary-value inputs against the interface declared for S1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item S1 reverts the change to the interface declared for S1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item S1: review risks specific to execution-state-lifecycle-and-l1-readiness and record any open decision.
