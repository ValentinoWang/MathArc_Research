# Acceptance Contract: DUR2

- Task ID: DUR2
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-DUR2
- SSOT node: DUR2
- SSOT path: .ssot/nodes/DUR2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dur2
- AC budget: 2
- Baseline identity: ssot-input.json#items[DUR2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching durable-import-ledger drives item DUR2 (unspecified dimension) through the interface declared for DUR2. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Problem

Item DUR2 exists because the interface declared for DUR2 does not yet satisfy the acceptance seeds registered for it, leaving durable-import-ledger incomplete. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Expected outcome

After item DUR2 lands, the interface declared for DUR2 satisfies every acceptance seed below and durable-import-ledger reflects that behavior. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Non-goals

Item DUR2 covers only the interface declared for DUR2 and durable-import-ledger as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Normal path

```gherkin
Given a user reaches durable-import-ledger for item DUR2
When the flow defined by the interface declared for DUR2 executes
Then every acceptance seed for item DUR2 holds  Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.
```

## Exception paths

If the interface declared for DUR2 fails for item DUR2, durable-import-ledger must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Invariants

For item DUR2, the interface declared for DUR2 must continue to satisfy every acceptance seed below on every call; durable-import-ledger must never show a state the seeds forbid. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Data impact

Item DUR2 constrains any create, update, or delete reachable through the interface declared for DUR2; only the acceptance seeds below define what data changes are permitted for durable-import-ledger. Node-specific data assertions: 在 matharc/v02/runtime/run_store.py 中幂等导入候选、费用和执行回执并保留来源身份 | 在 tests/test_runtime_idempotent_import.py 中证明重复导入结果不变且来源身份变化时拒绝 Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Permissions

Item DUR2 is owned by principal:acceptance-a; access to the interface declared for DUR2 and durable-import-ledger follows the acceptance seeds below and no wider grant. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR2: the thresholds and failure evidence for the interface declared for DUR2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DUR2 | machine/integration-contract | 在 matharc/v02/runtime/run_store.py 中幂等导入候选、费用和执行回执并保留来源身份 | Integration | Automatic | Yes |
| AC-02 | behavior | SRC-DUR2 | machine/local-runtime | 在 tests/test_runtime_idempotent_import.py 中证明重复导入结果不变且来源身份变化时拒绝 | Local runtime | Automatic | Yes |

## Human acceptance

Item DUR2 is fully determined by its acceptance seeds; outcomes for the interface declared for DUR2 on durable-import-ledger are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DUR2; executable baseline not yet locked. Concrete seed references: matharc/v02/runtime/run_store.py, tests/test_runtime_idempotent_import.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | matharc/v02/runtime/run_store.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_idempotent_import.py | Automatic | Yes |

## Exploratory testing

Probe durable-import-ledger for item DUR2 under retry, interruption, and boundary-value inputs against the interface declared for DUR2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DUR2 reverts the change to the interface declared for DUR2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DUR2: review risks specific to durable-import-ledger and record any open decision.
