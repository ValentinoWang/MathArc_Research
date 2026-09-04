# Acceptance Contract: VER3

- Task ID: VER3
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-VER3
- SSOT node: VER3
- SSOT path: .ssot/nodes/VER3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ver3
- AC budget: 4
- Baseline identity: ssot-input.json#items[VER3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching independent-replay drives item VER3 (unspecified dimension) through the interface declared for VER3.

## Problem

Item VER3 exists because the interface declared for VER3 does not yet satisfy the acceptance seeds registered for it, leaving independent-replay incomplete.

## Expected outcome

After item VER3 lands, the interface declared for VER3 satisfies every acceptance seed below and independent-replay reflects that behavior.

## Non-goals

Item VER3 covers only the interface declared for VER3 and independent-replay as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches independent-replay for item VER3
When the flow defined by the interface declared for VER3 executes
Then every acceptance seed for item VER3 holds
```

## Exception paths

If the interface declared for VER3 fails for item VER3, independent-replay must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item VER3, the interface declared for VER3 must continue to satisfy every acceptance seed below on every call; independent-replay must never show a state the seeds forbid.

## Data impact

Item VER3 constrains any create, update, or delete reachable through the interface declared for VER3; only the acceptance seeds below define what data changes are permitted for independent-replay. Node-specific data assertions: 在 matharc/v02/runtime/verification.py 中为候选生成干净环境的独立重放计划 | 在 tests/test_candidate_independent_replay.py 中证明相同实现的重复执行不算独立验证 | 在 matharc/v02/runtime/verification.py 中固定 CandidateEnvelope 输入、独立 ReplayPlan 与 VerifierReceipt 输出、candidate_id+replay_digest 幂等键、超时/取消/失败分类、有限重试和恢复边界；在 tests/test_candidate_independent_replay.py 中保护独立验收身份 | tests/test_candidate_independent_replay.py 实现后必须在 protected_tests 登记 SHA-256 及干净环境/非同实现重放覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY

## Permissions

Item VER3 is owned by principal:acceptance-a; access to the interface declared for VER3 and independent-replay follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER3: the thresholds and failure evidence for the interface declared for VER3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-VER3 | machine/e2e | 在 matharc/v02/runtime/verification.py 中为候选生成干净环境的独立重放计划 | E2E | Automatic | Yes |
| AC-02 | behavior | SRC-VER3 | machine/local-runtime | 在 tests/test_candidate_independent_replay.py 中证明相同实现的重复执行不算独立验证 | Local runtime | Automatic | Yes |
| AC-03 | behavior | SRC-VER3 | machine/e2e | 在 matharc/v02/runtime/verification.py 中固定 CandidateEnvelope 输入、独立 ReplayPlan 与 VerifierReceipt 输出、candidate_id+replay_digest 幂等键、超时/取消/失败分类、有限重试和恢复边界；在 tests/test_candidate_independent_replay.py 中保护独立验收身份 | E2E | Automatic | Yes |
| AC-04 | behavior | SRC-VER3 | machine/local-runtime | tests/test_candidate_independent_replay.py 实现后必须在 protected_tests 登记 SHA-256 及干净环境/非同实现重放覆盖；摘要缺失或漂移时合同保持 DRAFT 并阻断 READY | Local runtime | Automatic | Yes |

## Human acceptance

Item VER3 is fully determined by its acceptance seeds; outcomes for the interface declared for VER3 on independent-replay are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item VER3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | matharc/v02/runtime/verification.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_candidate_independent_replay.py | Automatic | Yes |
| AC-03 | E2E | matharc/v02/runtime/verification.py | Automatic | Yes |
| AC-04 | Local runtime | tests/test_candidate_independent_replay.py | Automatic | Yes |

## Exploratory testing

Probe independent-replay for item VER3 under retry, interruption, and boundary-value inputs against the interface declared for VER3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item VER3 reverts the change to the interface declared for VER3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item VER3: review risks specific to independent-replay and record any open decision.
