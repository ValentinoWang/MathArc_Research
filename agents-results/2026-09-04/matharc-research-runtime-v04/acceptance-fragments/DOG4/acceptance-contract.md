# Acceptance Contract: DOG4

- Task ID: DOG4
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 试点发布负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[22]
- SSOT node: DOG4
- SSOT path: .ssot/nodes/DOG4.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.dog4
- AC budget: 2
- Baseline identity: ssot-input.json#items[DOG4]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching pilot-release-evidence drives item DOG4 (unspecified dimension) through the interface declared for DOG4.

## Problem

Item DOG4 exists because the interface declared for DOG4 does not yet satisfy the acceptance seeds registered for it, leaving pilot-release-evidence incomplete.

## Expected outcome

After item DOG4 lands, the interface declared for DOG4 satisfies every acceptance seed below and pilot-release-evidence reflects that behavior.

## Non-goals

Item DOG4 covers only the interface declared for DOG4 and pilot-release-evidence as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches pilot-release-evidence for item DOG4
When the flow defined by the interface declared for DOG4 executes
Then every acceptance seed for item DOG4 holds
```

## Exception paths

If the interface declared for DOG4 fails for item DOG4, pilot-release-evidence must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item DOG4, the interface declared for DOG4 must continue to satisfy every acceptance seed below on every call; pilot-release-evidence must never show a state the seeds forbid.

## Data impact

Item DOG4 constrains any create, update, or delete reachable through the interface declared for DOG4; only the acceptance seeds below define what data changes are permitted for pilot-release-evidence. Node-specific data assertions: 在 acceptance/human/runtime-pilot/release-checklist.md 中汇编二至五人邀请试点的人类验收记录 | 在 acceptance/runtime-pilot/release-evidence.json 中证明用户可理解研究状态且本地正式检查与干净重放通过

## Permissions

Item DOG4 is owned by 试点发布负责人; access to the interface declared for DOG4 and pilot-release-evidence follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG4: the thresholds and failure evidence for the interface declared for DOG4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DOG4 | human | 在 acceptance/human/runtime-pilot/release-checklist.md 中汇编二至五人邀请试点的人类验收记录 | Human | Automatic | Yes |
| AC-02 | behavior | SRC-DOG4 | release | 在 acceptance/runtime-pilot/release-evidence.json 中证明用户可理解研究状态且本地正式检查与干净重放通过 | Release | Automatic | Yes |

## Human acceptance

Item DOG4 is fully determined by its acceptance seeds; outcomes for the interface declared for DOG4 on pilot-release-evidence are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DOG4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Human | acceptance/human/runtime-pilot/release-checklist.md | Automatic | Yes |
| AC-02 | Release | acceptance/runtime-pilot/release-evidence.json | Automatic | Yes |

## Exploratory testing

Probe pilot-release-evidence for item DOG4 under retry, interruption, and boundary-value inputs against the interface declared for DOG4, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item DOG4 reverts the change to the interface declared for DOG4; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG4: review risks specific to pilot-release-evidence and record any open decision.
