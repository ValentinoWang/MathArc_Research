# Acceptance Contract: DOG4

- Task ID: DOG4
- Contract kind: release-decision
- Contract profile: acceptance-contract-kind-profiles@1
- Verification layer: Human decision
- Acceptance mode: Manual / Authority-attested
- Evidence target: signed decision record
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: principal:acceptance-a
- Execution actor: human
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-DOG4
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
- Resolved Governance Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

An authorized decision authority reviews the evidence and records the signed decision for item DOG4.

## Problem

Item DOG4 remains open because its required governance decision has not yet been recorded in the isolated decision record.

## Expected outcome

After item DOG4 is accepted, the signed decision record exists, is attributable to the declared authority, and is bound to the seeds below.

## Non-goals

Item DOG4 covers only the governance decision and its isolated record; implementation changes are owned by the downstream item named in the seeds.

## Normal path

```gherkin
Given the declared decision authority reviews item DOG4 evidence
When the authority records the decision in the isolated decision record
Then every acceptance seed for item DOG4 holds
```

## Exception paths

If item DOG4 lacks an authorized signed decision or its record is invalid, promotion must stop and the failure must be recorded.

## Invariants

Item DOG4 must retain an immutable, attributable decision record; no implementation or runtime state may be inferred from an unsigned recommendation.

## Data impact

Item DOG4 writes only its isolated decision record; it must not modify implementation files, generated nodes, or evidence collectors.

## Permissions

Only the declared decision authority may accept item DOG4; the execution owner and downstream implementer cannot substitute for that authority.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG4: the thresholds and failure evidence for the interface declared for DOG4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-DOG4 | human | 在 acceptance/human/runtime-pilot/release-checklist.md 中汇编二至五人邀请试点的人类验收记录 | Human decision | Manual / Authority-attested | Yes |
| AC-02 | behavior | SRC-DOG4 | human | 在 acceptance/runtime-pilot/release-evidence.json 中证明用户可理解研究状态且本地正式检查与干净重放通过 | Human decision | Manual / Authority-attested | Yes |

## Human acceptance

Decision item DOG4 requires an authorized human decision against the acceptance seeds; record the signed decision before promotion.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item DOG4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Human decision | acceptance/human/runtime-pilot/release-checklist.md | Manual / Authority-attested | Yes |
| AC-02 | Human decision | acceptance/runtime-pilot/release-evidence.json | Manual / Authority-attested | Yes |

## Exploratory testing

Review item DOG4 for missing signatures, stale references, duplicate records, and attempts to promote an unsigned recommendation.

## Production monitoring and rollback

To roll back item DOG4, invalidate its decision record and return the dependent implementation node to its pre-decision state.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item DOG4: review risks specific to pilot-release-evidence and record any open decision.
