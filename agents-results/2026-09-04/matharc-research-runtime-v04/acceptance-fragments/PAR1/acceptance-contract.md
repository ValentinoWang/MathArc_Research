# Acceptance Contract: PAR1

- Task ID: PAR1
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-PAR1
- SSOT node: PAR1
- SSOT path: .ssot/nodes/PAR1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.par1
- AC budget: 2
- Baseline identity: ssot-input.json#items[PAR1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching research-topology drives item PAR1 (unspecified dimension) through the interface declared for PAR1. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Problem

Item PAR1 exists because the interface declared for PAR1 does not yet satisfy the acceptance seeds registered for it, leaving research-topology incomplete. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Expected outcome

After item PAR1 lands, the interface declared for PAR1 satisfies every acceptance seed below and research-topology reflects that behavior. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Non-goals

Item PAR1 covers only the interface declared for PAR1 and research-topology as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Normal path

```gherkin
Given a user reaches research-topology for item PAR1
When the flow defined by the interface declared for PAR1 executes
Then every acceptance seed for item PAR1 holds  Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.
```

## Exception paths

If the interface declared for PAR1 fails for item PAR1, research-topology must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Invariants

For item PAR1, the interface declared for PAR1 must continue to satisfy every acceptance seed below on every call; research-topology must never show a state the seeds forbid. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Data impact

Item PAR1 constrains any create, update, or delete reachable through the interface declared for PAR1; only the acceptance seeds below define what data changes are permitted for research-topology. Node-specific data assertions: 在 matharc/v02/runtime/topology.py 中把研究路线和角色编译为带机制、预算、目标和写入区域的运行拓扑 | 在 tests/test_runtime_topology.py 中拒绝缺少角色、预算或写入区域的研究成员 Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Permissions

Item PAR1 is owned by principal:acceptance-a; access to the interface declared for PAR1 and research-topology follows the acceptance seeds below and no wider grant. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR1: the thresholds and failure evidence for the interface declared for PAR1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PAR1 | machine/unit | 在 matharc/v02/runtime/topology.py 中把研究路线和角色编译为带机制、预算、目标和写入区域的运行拓扑 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-PAR1 | machine/integration-contract | 在 tests/test_runtime_topology.py 中拒绝缺少角色、预算或写入区域的研究成员 | Integration | Automatic | Yes |

## Human acceptance

Item PAR1 is fully determined by its acceptance seeds; outcomes for the interface declared for PAR1 on research-topology are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item PAR1; executable baseline not yet locked. Concrete seed references: matharc/v02/runtime/topology.py, tests/test_runtime_topology.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/runtime/topology.py | Automatic | Yes |
| AC-02 | Integration | tests/test_runtime_topology.py | Automatic | Yes |

## Exploratory testing

Probe research-topology for item PAR1 under retry, interruption, and boundary-value inputs against the interface declared for PAR1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item PAR1 reverts the change to the interface declared for PAR1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item PAR1: review risks specific to research-topology and record any open decision.
