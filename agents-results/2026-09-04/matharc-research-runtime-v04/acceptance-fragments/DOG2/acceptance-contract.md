# Acceptance Contract: DOG2

- Task ID: DOG2
- Contract kind: validation
- Contract profile: acceptance-contract-kind-profiles@1
- Verification layer: machine
- Acceptance mode: Automatic
- Evidence target: validation result
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: principal:acceptance-a
- Execution actor: orchestrator
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-DOG2
- SSOT node: DOG2
- SSOT path: .ssot/nodes/DOG2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dog2
- AC budget: 3
- Baseline identity: ssot-input.json#items[DOG2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching real-two-generation-pilot drives item DOG2 (unspecified dimension) through the interface declared for DOG2. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Problem

Item DOG2 exists because the interface declared for DOG2 does not yet satisfy the acceptance seeds registered for it, leaving real-two-generation-pilot incomplete. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Expected outcome

After item DOG2 lands, the interface declared for DOG2 satisfies every acceptance seed below and real-two-generation-pilot reflects that behavior. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Non-goals

Item DOG2 covers only the interface declared for DOG2 and real-two-generation-pilot as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Normal path

```gherkin
Given a user reaches real-two-generation-pilot for item DOG2
When the flow defined by the interface declared for DOG2 executes
Then every acceptance seed for item DOG2 holds  Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.
```

## Exception paths

If the interface declared for DOG2 fails for item DOG2, real-two-generation-pilot must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Invariants

For item DOG2, the interface declared for DOG2 must continue to satisfy every acceptance seed below on every call; real-two-generation-pilot must never show a state the seeds forbid. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Data impact

Item DOG2 constrains any create, update, or delete reachable through the interface declared for DOG2; only the acceptance seeds below define what data changes are permitted for real-two-generation-pilot. Node-specific data assertions: 在 experiments/runtime-pilot/two-generation-report.md 中记录三至四研究成员和至少两代真实实验 | 在 tests/test_runtime_pilot_generation_consumption.py 中证明第二代消费第一代结果且错误晋升为零 | 在 acceptance/runtime-pilot/production-checklist.md 中记录真实两代研究的持久运行环境与发布前置 Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Permissions

Item DOG2 is owned by principal:acceptance-a; access to the interface declared for DOG2 and real-two-generation-pilot follows the acceptance seeds below and no wider grant. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG2: the thresholds and failure evidence for the interface declared for DOG2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DOG2 | machine/e2e | 在 experiments/runtime-pilot/two-generation-report.md 中记录三至四研究成员和至少两代真实实验 | E2E | Automatic | Yes |
| AC-02 | behavior | SRC-DOG2 | persistent-runtime | 在 tests/test_runtime_pilot_generation_consumption.py 中证明第二代消费第一代结果且错误晋升为零 | Persistent runtime | Automatic | Yes |
| AC-03 | behavior | SRC-DOG2 | production | 在 acceptance/runtime-pilot/production-checklist.md 中记录真实两代研究的持久运行环境与发布前置 | Production | Automatic | Yes |

## Human acceptance

Item DOG2 is fully determined by its acceptance seeds; outcomes for the interface declared for DOG2 on real-two-generation-pilot are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DOG2; executable baseline not yet locked. Concrete seed references: acceptance/runtime-pilot/production-checklist.md, experiments/runtime-pilot/two-generation-report.md, tests/test_runtime_pilot_generation_consumption.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | experiments/runtime-pilot/two-generation-report.md | Automatic | Yes |
| AC-02 | Persistent runtime | tests/test_runtime_pilot_generation_consumption.py | Automatic | Yes |
| AC-03 | Production | acceptance/runtime-pilot/production-checklist.md | Automatic | Yes |

## Exploratory testing

Probe real-two-generation-pilot for item DOG2 under retry, interruption, and boundary-value inputs against the interface declared for DOG2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DOG2 reverts the change to the interface declared for DOG2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG2: review risks specific to real-two-generation-pilot and record any open decision.
