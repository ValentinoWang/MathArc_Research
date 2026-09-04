# Acceptance Contract: OPS2

- Task ID: OPS2
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-OPS2
- SSOT node: OPS2
- SSOT path: .ssot/nodes/OPS2.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1, decision.matharc-pilot-deployment@1
- Assumption IDs: none
- Invalidation keys: task.ops2
- AC budget: 2
- Baseline identity: ssot-input.json#items[OPS2]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching pilot-operations drives item OPS2 (unspecified dimension) through the interface declared for OPS2. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Problem

Item OPS2 exists because the interface declared for OPS2 does not yet satisfy the acceptance seeds registered for it, leaving pilot-operations incomplete. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Expected outcome

After item OPS2 lands, the interface declared for OPS2 satisfies every acceptance seed below and pilot-operations reflects that behavior. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Non-goals

Item OPS2 covers only the interface declared for OPS2 and pilot-operations as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Normal path

```gherkin
Given a user reaches pilot-operations for item OPS2
When the flow defined by the interface declared for OPS2 executes
Then every acceptance seed for item OPS2 holds  Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.
```

## Exception paths

If the interface declared for OPS2 fails for item OPS2, pilot-operations must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Invariants

For item OPS2, the interface declared for OPS2 must continue to satisfy every acceptance seed below on every call; pilot-operations must never show a state the seeds forbid. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Data impact

Item OPS2 constrains any create, update, or delete reachable through the interface declared for OPS2; only the acceptance seeds below define what data changes are permitted for pilot-operations. Node-specific data assertions: 在 tests/test_runtime_ops_observability.py 中验证健康检查、结构化日志和单用户/全局配额 | 在 tests/test_runtime_ops_backup.py 中验证备份、恢复演练和恢复后身份连续性 Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Permissions

Item OPS2 is owned by principal:acceptance-a; access to the interface declared for OPS2 and pilot-operations follows the acceptance seeds below and no wider grant. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item OPS2: the thresholds and failure evidence for the interface declared for OPS2 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-OPS2 | machine/integration-contract | 在 tests/test_runtime_ops_observability.py 中验证健康检查、结构化日志和单用户/全局配额 | Integration | Automatic | Yes |
| AC-02 | behavior | SRC-OPS2 | persistent-runtime | 在 tests/test_runtime_ops_backup.py 中验证备份、恢复演练和恢复后身份连续性 | Persistent runtime | Automatic | Yes |

## Human acceptance

Item OPS2 is fully determined by its acceptance seeds; outcomes for the interface declared for OPS2 on pilot-operations are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item OPS2; executable baseline not yet locked. Concrete seed references: tests/test_runtime_ops_backup.py, tests/test_runtime_ops_observability.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Integration | tests/test_runtime_ops_observability.py | Automatic | Yes |
| AC-02 | Persistent runtime | tests/test_runtime_ops_backup.py | Automatic | Yes |

## Exploratory testing

Probe pilot-operations for item OPS2 under retry, interruption, and boundary-value inputs against the interface declared for OPS2, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item OPS2 reverts the change to the interface declared for OPS2; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item OPS2: review risks specific to pilot-operations and record any open decision.
