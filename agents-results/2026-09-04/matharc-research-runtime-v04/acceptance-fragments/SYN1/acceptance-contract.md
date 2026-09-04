# Acceptance Contract: SYN1

- Task ID: SYN1
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-SYN1
- SSOT node: SYN1
- SSOT path: .ssot/nodes/SYN1.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.syn1
- AC budget: 2
- Baseline identity: ssot-input.json#items[SYN1]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching candidate-synthesis drives item SYN1 (unspecified dimension) through the interface declared for SYN1. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Problem

Item SYN1 exists because the interface declared for SYN1 does not yet satisfy the acceptance seeds registered for it, leaving candidate-synthesis incomplete. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Expected outcome

After item SYN1 lands, the interface declared for SYN1 satisfies every acceptance seed below and candidate-synthesis reflects that behavior. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Non-goals

Item SYN1 covers only the interface declared for SYN1 and candidate-synthesis as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Normal path

```gherkin
Given a user reaches candidate-synthesis for item SYN1
When the flow defined by the interface declared for SYN1 executes
Then every acceptance seed for item SYN1 holds  Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.
```

## Exception paths

If the interface declared for SYN1 fails for item SYN1, candidate-synthesis must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Invariants

For item SYN1, the interface declared for SYN1 must continue to satisfy every acceptance seed below on every call; candidate-synthesis must never show a state the seeds forbid. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Data impact

Item SYN1 constrains any create, update, or delete reachable through the interface declared for SYN1; only the acceptance seeds below define what data changes are permitted for candidate-synthesis. Node-specific data assertions: 在 matharc/v02/runtime/synthesis.py 中把普通执行输出标准化为带完整出处的探索候选 | 在 tests/test_runtime_candidate_synthesis.py 中证明标准化候选不会进入正式证据 Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Permissions

Item SYN1 is owned by principal:acceptance-a; access to the interface declared for SYN1 and candidate-synthesis follows the acceptance seeds below and no wider grant. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN1: the thresholds and failure evidence for the interface declared for SYN1 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-SYN1 | machine/unit | 在 matharc/v02/runtime/synthesis.py 中把普通执行输出标准化为带完整出处的探索候选 | Unit | Automatic | Yes |
| AC-02 | behavior | SRC-SYN1 | machine/local-runtime | 在 tests/test_runtime_candidate_synthesis.py 中证明标准化候选不会进入正式证据 | Local runtime | Automatic | Yes |

## Human acceptance

Item SYN1 is fully determined by its acceptance seeds; outcomes for the interface declared for SYN1 on candidate-synthesis are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item SYN1; executable baseline not yet locked. Concrete seed references: matharc/v02/runtime/synthesis.py, tests/test_runtime_candidate_synthesis.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Unit | matharc/v02/runtime/synthesis.py | Automatic | Yes |
| AC-02 | Local runtime | tests/test_runtime_candidate_synthesis.py | Automatic | Yes |

## Exploratory testing

Probe candidate-synthesis for item SYN1 under retry, interruption, and boundary-value inputs against the interface declared for SYN1, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item SYN1 reverts the change to the interface declared for SYN1; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item SYN1: review risks specific to candidate-synthesis and record any open decision.
