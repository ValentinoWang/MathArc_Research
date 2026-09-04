# Acceptance Contract: DOG3

- Task ID: DOG3
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 试点攻击演练负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[21]
- SSOT node: DOG3
- SSOT path: .ssot/nodes/DOG3.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dog3
- AC budget: 3
- Baseline identity: ssot-input.json#items[DOG3]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching pilot-adversarial-drills drives item DOG3 (unspecified dimension) through the interface declared for DOG3.

## Problem

Item DOG3 exists because the interface declared for DOG3 does not yet satisfy the acceptance seeds registered for it, leaving pilot-adversarial-drills incomplete.

## Expected outcome

After item DOG3 lands, the interface declared for DOG3 satisfies every acceptance seed below and pilot-adversarial-drills reflects that behavior.

## Non-goals

Item DOG3 covers only the interface declared for DOG3 and pilot-adversarial-drills as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches pilot-adversarial-drills for item DOG3
When the flow defined by the interface declared for DOG3 executes
Then every acceptance seed for item DOG3 holds
```

## Exception paths

If the interface declared for DOG3 fails for item DOG3, pilot-adversarial-drills must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item DOG3, the interface declared for DOG3 must continue to satisfy every acceptance seed below on every call; pilot-adversarial-drills must never show a state the seeds forbid.

## Data impact

Item DOG3 constrains any create, update, or delete reachable through the interface declared for DOG3; only the acceptance seeds below define what data changes are permitted for pilot-adversarial-drills. Node-specific data assertions: 在 tests/test_runtime_adversarial_drills.py 中执行崩溃、篡改、虚假反例、重复导入和权限演练 | 在 tests/test_runtime_attack_recovery.py 中证明每条攻击路径都被拒绝或安全恢复 | 在 acceptance/runtime-pilot/production-attack-drills.md 中记录生产试点攻击演练的零容忍结果

## Permissions

Item DOG3 is owned by 试点攻击演练负责人; access to the interface declared for DOG3 and pilot-adversarial-drills follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG3: the thresholds and failure evidence for the interface declared for DOG3 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DOG3 | machine/e2e | 在 tests/test_runtime_adversarial_drills.py 中执行崩溃、篡改、虚假反例、重复导入和权限演练 | E2E | Automatic | Yes |
| AC-02 | behavior | SRC-DOG3 | persistent-runtime | 在 tests/test_runtime_attack_recovery.py 中证明每条攻击路径都被拒绝或安全恢复 | Persistent runtime | Automatic | Yes |
| AC-03 | behavior | SRC-DOG3 | production | 在 acceptance/runtime-pilot/production-attack-drills.md 中记录生产试点攻击演练的零容忍结果 | Production | Automatic | Yes |

## Human acceptance

Item DOG3 is fully determined by its acceptance seeds; outcomes for the interface declared for DOG3 on pilot-adversarial-drills are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DOG3; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | tests/test_runtime_adversarial_drills.py | Automatic | Yes |
| AC-02 | Persistent runtime | tests/test_runtime_attack_recovery.py | Automatic | Yes |
| AC-03 | Production | acceptance/runtime-pilot/production-attack-drills.md | Automatic | Yes |

## Exploratory testing

Probe pilot-adversarial-drills for item DOG3 under retry, interruption, and boundary-value inputs against the interface declared for DOG3, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DOG3 reverts the change to the interface declared for DOG3; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG3: review risks specific to pilot-adversarial-drills and record any open decision.
