# Acceptance Contract: V1

- Task ID: V1
- Contract version: 1
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: Harness 集成验收负责人
- Approval evidence: protected-tests-locked: .agents/skills/report-to-ssot-development-paths/tests/test_execution_gates.py, .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py
- Request source: item V1
- SSOT node: V1
- SSOT path: .ssot/nodes/V1.json
- Readiness mode: FORMAL
- Decision refs: decision.execution-plane.scope@1
- Assumption IDs: none
- Invalidation keys: task.v1
- AC budget: 3
- Baseline identity: ssot-input.json#items[V1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching negative-acceptance-matrix-and-release-readback drives item V1 (unspecified dimension) through the interface declared for V1.

## Problem

Item V1 exists because the interface declared for V1 does not yet satisfy the acceptance seeds registered for it, leaving negative-acceptance-matrix-and-release-readback incomplete.

## Expected outcome

After item V1 lands, the interface declared for V1 satisfies every acceptance seed below and negative-acceptance-matrix-and-release-readback reflects that behavior.

## Non-goals

Item V1 covers only the interface declared for V1 and negative-acceptance-matrix-and-release-readback as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches negative-acceptance-matrix-and-release-readback for item V1
When the flow defined by the interface declared for V1 executes
Then every acceptance seed for item V1 holds
```

## Exception paths

If the interface declared for V1 fails for item V1, negative-acceptance-matrix-and-release-readback must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item V1, the interface declared for V1 must continue to satisfy every acceptance seed below on every call; negative-acceptance-matrix-and-release-readback must never show a state the seeds forbid.

## Data impact

Item V1 constrains any create, update, or delete reachable through the interface declared for V1; only the acceptance seeds below define what data changes are permitted for negative-acceptance-matrix-and-release-readback. Node-specific data assertions: agents-results/2026-09-04/matharc-research-execution-plane/evidence/acceptance-matrix.json 必须逐项记录附件 12 个反例的命令、退出码、Harness 提交和结果文件摘要 | agents-results/2026-09-04/matharc-research-execution-plane/evidence/harness-ci-result.json 必须记录 .github/workflows/ssot-ci.yml 对应本地全量命令全部通过且零跳过 | agents-results/2026-09-04/matharc-research-execution-plane/evidence/release-readback.json 必须记录 MathArc 与 Harness 的 GitHub main SHA、分支清理和持久 Git 代理配置为空

## Permissions

Item V1 is owned by Harness 集成验收负责人; access to the interface declared for V1 and negative-acceptance-matrix-and-release-readback follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item V1: the thresholds and failure evidence for the interface declared for V1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/unit | agents-results/2026-09-04/matharc-research-execution-plane/evidence/acceptance-matrix.json 必须逐项记录附件 12 个反例的命令、退出码、Harness 提交和结果文件摘要 | Unit | Automatic | Yes |
| AC-02 | behavior | none | release | agents-results/2026-09-04/matharc-research-execution-plane/evidence/harness-ci-result.json 必须记录 .github/workflows/ssot-ci.yml 对应本地全量命令全部通过且零跳过 | Release | Automatic | Yes |
| AC-03 | behavior | none | machine/unit | agents-results/2026-09-04/matharc-research-execution-plane/evidence/release-readback.json 必须记录 MathArc 与 Harness 的 GitHub main SHA、分支清理和持久 Git 代理配置为空 | Unit | Automatic | Yes |

## Human acceptance

Item V1 is fully determined by its acceptance seeds; outcomes for the interface declared for V1 on negative-acceptance-matrix-and-release-readback are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
| .agents/skills/report-to-ssot-development-paths/tests/test_execution_gates.py | 443d99f0d6734873715135d979bbcd172adc41cff0088f2109de144352c609e7 | Push binding and completion evidence cases |
| .agents/skills/report-to-ssot-development-paths/tests/test_rules_index.py | 14de2f416dad0b1b7cb0dc919be1e4938445ab2681820d0b32670e620029e037 | Reverse-conservation integration cases |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | agents-results/2026-09-04/matharc-research-execution-plane/evidence/acceptance-matrix.json | Automatic | Yes |
| AC-02 | Release | agents-results/2026-09-04/matharc-research-execution-plane/evidence/harness-ci-result.json | Automatic | Yes |
| AC-03 | Unit | agents-results/2026-09-04/matharc-research-execution-plane/evidence/release-readback.json | Automatic | Yes |

## Exploratory testing

Probe negative-acceptance-matrix-and-release-readback for item V1 under retry, interruption, and boundary-value inputs against the interface declared for V1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item V1 reverts the change to the interface declared for V1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-EXECUTION-PLANE@1 -->
Node-specific increment for item V1: review risks specific to negative-acceptance-matrix-and-release-readback and record any open decision.
