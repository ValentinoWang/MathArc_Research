# Acceptance Contract: RUN2

- Task ID: RUN2
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-RUN2
- SSOT node: RUN2
- SSOT path: .ssot/nodes/RUN2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.run2
- AC budget: 2
- Baseline identity: ssot-input.json#items[RUN2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching run-store drives item RUN2 (unspecified dimension) through the interface declared for RUN2. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Problem

Item RUN2 exists because the interface declared for RUN2 does not yet satisfy the acceptance seeds registered for it, leaving run-store incomplete. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Expected outcome

After item RUN2 lands, the interface declared for RUN2 satisfies every acceptance seed below and run-store reflects that behavior. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Non-goals

Item RUN2 covers only the interface declared for RUN2 and run-store as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Normal path

```gherkin
Given a user reaches run-store for item RUN2
When the flow defined by the interface declared for RUN2 executes
Then every acceptance seed for item RUN2 holds  Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.
```

## Exception paths

If the interface declared for RUN2 fails for item RUN2, run-store must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Invariants

For item RUN2, the interface declared for RUN2 must continue to satisfy every acceptance seed below on every call; run-store must never show a state the seeds forbid. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Data impact

Item RUN2 constrains any create, update, or delete reachable through the interface declared for RUN2; only the acceptance seeds below define what data changes are permitted for run-store. Node-specific data assertions: 在 matharc/v02/runtime/run_store.py 中写入哈希链运行事件和原子快照 | 在 tests/test_runtime_store_replay.py 中拒绝截断、损坏和摘要不匹配的运行快照 Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Permissions

Item RUN2 is owned by principal:acceptance-a; access to the interface declared for RUN2 and run-store follows the acceptance seeds below and no wider grant. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN2: the thresholds and failure evidence for the interface declared for RUN2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-RUN2 | machine/unit | 在 matharc/v02/runtime/run_store.py 中写入哈希链运行事件和原子快照 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-RUN2 | machine/local-runtime | 在 tests/test_runtime_store_replay.py 中拒绝截断、损坏和摘要不匹配的运行快照 | Local runtime | Automatic | Yes |

## Human acceptance

Item RUN2 is fully determined by its acceptance seeds; outcomes for the interface declared for RUN2 on run-store are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item RUN2; executable baseline not yet locked. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_store_replay.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/runtime/run_store.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_store_replay.py | Automatic | Yes |

## Exploratory testing

Probe run-store for item RUN2 under retry, interruption, and boundary-value inputs against the interface declared for RUN2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item RUN2 reverts the change to the interface declared for RUN2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item RUN2: review risks specific to run-store and record any open decision.
