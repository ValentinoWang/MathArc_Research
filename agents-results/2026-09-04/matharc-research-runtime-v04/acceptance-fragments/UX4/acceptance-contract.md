# Acceptance Contract: UX4

- Task ID: UX4
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 控制台安全视图负责人
- Approval evidence: TBD
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:li[16]
- SSOT node: UX4
- SSOT path: .ssot/nodes/UX4.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ux4
- AC budget: 3
- Baseline identity: ssot-input.json#items[UX4]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching runtime-disclosure drives item UX4 (unspecified dimension) through the interface declared for UX4.

## Problem

Item UX4 exists because the interface declared for UX4 does not yet satisfy the acceptance seeds registered for it, leaving runtime-disclosure incomplete.

## Expected outcome

After item UX4 lands, the interface declared for UX4 satisfies every acceptance seed below and runtime-disclosure reflects that behavior.

## Non-goals

Item UX4 covers only the interface declared for UX4 and runtime-disclosure as described by its acceptance seeds; behavior outside those seeds is out of scope.

## Normal path

```gherkin
Given a user reaches runtime-disclosure for item UX4
When the flow defined by the interface declared for UX4 executes
Then every acceptance seed for item UX4 holds
```

## Exception paths

If the interface declared for UX4 fails for item UX4, runtime-disclosure must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope.

## Invariants

For item UX4, the interface declared for UX4 must continue to satisfy every acceptance seed below on every call; runtime-disclosure must never show a state the seeds forbid.

## Data impact

Item UX4 constrains any create, update, or delete reachable through the interface declared for UX4; only the acceptance seeds below define what data changes are permitted for runtime-disclosure. Node-specific data assertions: 在 matharc/v02/view_model.py 中建立统一中文运行视图并递归脱敏 | 在 tests/test_runtime_console_redaction.py 中证明密钥、路径、完整命令、环境变量和异常堆栈泄露为零 | 在 tests/test_runtime_console_redaction_visual.py 中验证脱敏后的运行视图不显示敏感字段

## Permissions

Item UX4 is owned by 控制台安全视图负责人; access to the interface declared for UX4 and runtime-disclosure follows the acceptance seeds below and no wider grant.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX4: the thresholds and failure evidence for the interface declared for UX4 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-UX4 | machine/static | 在 matharc/v02/view_model.py 中建立统一中文运行视图并递归脱敏 | Static analysis | Automatic | Yes |
| AC-02 | behavior | SRC-UX4 | machine/e2e | 在 tests/test_runtime_console_redaction.py 中证明密钥、路径、完整命令、环境变量和异常堆栈泄露为零 | E2E | Automatic | Yes |
| AC-03 | behavior | SRC-UX4 | visual-fidelity | 在 tests/test_runtime_console_redaction_visual.py 中验证脱敏后的运行视图不显示敏感字段 | Visual fidelity | Automatic | Yes |

## Human acceptance

Item UX4 is fully determined by its acceptance seeds; outcomes for the interface declared for UX4 on runtime-disclosure are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item UX4; executable baseline not yet locked |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Static analysis | matharc/v02/view_model.py | Automatic | Yes |
| AC-02 | E2E | tests/test_runtime_console_redaction.py | Automatic | Yes |
| AC-03 | Visual fidelity | tests/test_runtime_console_redaction_visual.py | Automatic | Yes |

## Exploratory testing

Probe runtime-disclosure for item UX4 under retry, interruption, and boundary-value inputs against the interface declared for UX4, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item UX4 reverts the change to the interface declared for UX4; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX4: review risks specific to runtime-disclosure and record any open decision.
