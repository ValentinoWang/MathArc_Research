# Acceptance Contract: E1

- Task ID: E1
- Contract version: 1
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: Harness 证据与事实负责人
- Approval evidence: protected-tests-locked: .agents/skills/report-to-ssot-development-paths/tests/test_evidence_lane_registry.py, .agents/skills/ssot-obsidian-snapshot/tests/test_doc_code_parity.py
- Request source: item E1
- SSOT node: E1
- SSOT path: .ssot/nodes/E1.json
- Readiness mode: FORMAL
- Decision refs: decision.execution-plane.scope@1
- Assumption IDs: none
- Invalidation keys: task.e1
- AC budget: 2
- Baseline identity: ssot-input.json#items[E1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching evidence-lane-registry-and-facts-registry drives item E1 (unspecified dimension) through the interface declared for E1.

## Problem

Item E1 exists because the interface declared for E1 does not yet satisfy the acceptance seeds registered for it, leaving evidence-lane-registry-and-facts-registry incomplete.

## Expected outcome

After item E1 lands, the interface declared for E1 satisfies every acceptance seed below and evidence-lane-registry-and-facts-registry reflects that behavior.

## Non-goals

Item E1 covers only the interface declared for E1 and evidence-lane-registry-and-facts-registry as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches evidence-lane-registry-and-facts-registry for item E1
When the flow defined by the interface declared for E1 executes
Then every acceptance seed for item E1 holds
```

## Exception paths

If the interface declared for E1 fails for item E1, evidence-lane-registry-and-facts-registry must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item E1, the interface declared for E1 must continue to satisfy every acceptance seed below on every call; evidence-lane-registry-and-facts-registry must never show a state the seeds forbid.

## Data impact

Item E1 constrains any create, update, or delete reachable through the interface declared for E1; only the acceptance seeds below define what data changes are permitted for evidence-lane-registry-and-facts-registry. Node-specific data assertions: 在 .agents/skills/report-to-ssot-development-paths/tests/test_evidence_lane_registry.py 中证明合同引用 persistent-runtime 但项目 adapter 没有 collector_key 时验收检查失败 | 在 .agents/skills/ssot-obsidian-snapshot/tests/test_doc_code_parity.py 中证明文档没有命令、flag 或 host 时 Facts Registry 不要求且不生成 none 占位事实

## Permissions

Item E1 is owned by Harness 证据与事实负责人; access to the interface declared for E1 and evidence-lane-registry-and-facts-registry follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item E1: the thresholds and failure evidence for the interface declared for E1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/static | 在 .agents/skills/report-to-ssot-development-paths/tests/test_evidence_lane_registry.py 中证明合同引用 persistent-runtime 但项目 adapter 没有 collector_key 时验收检查失败 | Static analysis | Automatic | Yes |
| AC-02 | behavior | none | machine/unit | 在 .agents/skills/ssot-obsidian-snapshot/tests/test_doc_code_parity.py 中证明文档没有命令、flag 或 host 时 Facts Registry 不要求且不生成 none 占位事实 | Unit | Automatic | Yes |

## Human acceptance

Item E1 is fully determined by its acceptance seeds; outcomes for the interface declared for E1 on evidence-lane-registry-and-facts-registry are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
| .agents/skills/report-to-ssot-development-paths/tests/test_evidence_lane_registry.py | 76fd082aefb3be3b093656febca8be26fbb5aadb227d9037620b436b320139f5 | Evidence collector binding cases |
| .agents/skills/ssot-obsidian-snapshot/tests/test_doc_code_parity.py | 7b2bf22b489e79a981e96ff658b8a99518b7a18181105eb7c0ab1c24fdcc6f97 | Conditional facts registry cases |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Static analysis | .agents/skills/report-to-ssot-development-paths/tests/test_evidence_lane_registry.py | Automatic | Yes |
| AC-02 | Unit | .agents/skills/ssot-obsidian-snapshot/tests/test_doc_code_parity.py | Automatic | Yes |

## Exploratory testing

Probe evidence-lane-registry-and-facts-registry for item E1 under retry, interruption, and boundary-value inputs against the interface declared for E1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item E1 reverts the change to the interface declared for E1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item E1: review risks specific to evidence-lane-registry-and-facts-registry and record any open decision.
