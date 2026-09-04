# Acceptance Contract: SYN5

- Task ID: SYN5
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 连续代际验收负责人
- Approval evidence: TBD
- Request source: item SYN5
- SSOT node: SYN5
- SSOT path: .ssot/nodes/SYN5.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.syn5
- AC budget: 2
- Baseline identity: ssot-input.json#items[SYN5]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching two-generation-synthesis drives item SYN5 (unspecified dimension) through the interface declared for SYN5.

## Problem

Item SYN5 exists because the interface declared for SYN5 does not yet satisfy the acceptance seeds registered for it, leaving two-generation-synthesis incomplete.

## Expected outcome

After item SYN5 lands, the interface declared for SYN5 satisfies every acceptance seed below and two-generation-synthesis reflects that behavior.

## Non-goals

Item SYN5 covers only the interface declared for SYN5 and two-generation-synthesis as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches two-generation-synthesis for item SYN5
When the flow defined by the interface declared for SYN5 executes
Then every acceptance seed for item SYN5 holds
```

## Exception paths

If the interface declared for SYN5 fails for item SYN5, two-generation-synthesis must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item SYN5, the interface declared for SYN5 must continue to satisfy every acceptance seed below on every call; two-generation-synthesis must never show a state the seeds forbid.

## Data impact

Item SYN5 constrains any create, update, or delete reachable through the interface declared for SYN5; only the acceptance seeds below define what data changes are permitted for two-generation-synthesis. Node-specific data assertions: 在 tests/test_runtime_two_generation_synthesis.py 中完成连续两代运行并保留两份 GenerationCommit | 在 tests/test_runtime_generation_delta.py 中证明第二代路线或攻击任务因第一代结果发生可解释变化

## Permissions

Item SYN5 is owned by 连续代际验收负责人; access to the interface declared for SYN5 and two-generation-synthesis follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN5: the thresholds and failure evidence for the interface declared for SYN5 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/e2e | 在 tests/test_runtime_two_generation_synthesis.py 中完成连续两代运行并保留两份 GenerationCommit | E2E | Automatic | Yes |
| AC-02 | behavior | none | machine/local-runtime | 在 tests/test_runtime_generation_delta.py 中证明第二代路线或攻击任务因第一代结果发生可解释变化 | Local runtime | Automatic | Yes |

## Human acceptance

Item SYN5 is fully determined by its acceptance seeds; outcomes for the interface declared for SYN5 on two-generation-synthesis are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item SYN5; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_runtime_two_generation_synthesis.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_generation_delta.py | Automatic | Yes |

## Exploratory testing

Probe two-generation-synthesis for item SYN5 under retry, interruption, and boundary-value inputs against the interface declared for SYN5, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item SYN5 reverts the change to the interface declared for SYN5; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN5: review risks specific to two-generation-synthesis and record any open decision.
