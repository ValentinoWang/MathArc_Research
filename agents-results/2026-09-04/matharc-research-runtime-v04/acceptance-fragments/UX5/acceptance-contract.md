# Acceptance Contract: UX5

- Task ID: UX5
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
- Request source: SRC-MATHARC-RUNTIME-CONTRACT-HTML#html:requirement-id=SRC-UX5
- SSOT node: UX5
- SSOT path: .ssot/nodes/UX5.json
- Readiness mode: FORMAL
- Decision refs: decision.matharc-native-runtime@1
- Assumption IDs: none
- Invalidation keys: task.ux5
- AC budget: 3
- Baseline identity: ssot-input.json#items[UX5]
- Product Context refs: none
- Role Context refs: none
- Resolved Surface Contract refs: none
- Screen Contract ref: none
- Visual Contract refs: none
- UI Change declaration: none
- Human acceptance workspace: none

## User and scenario

The user reaching live-runtime-console drives item UX5 (unspecified dimension) through the interface declared for UX5. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Problem

Item UX5 exists because the interface declared for UX5 does not yet satisfy the acceptance seeds registered for it, leaving live-runtime-console incomplete. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Expected outcome

After item UX5 lands, the interface declared for UX5 satisfies every acceptance seed below and live-runtime-console reflects that behavior. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Non-goals

Item UX5 covers only the interface declared for UX5 and live-runtime-console as described by its acceptance seeds; behavior outside those seeds is out of scope. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Normal path

```gherkin
Given a user reaches live-runtime-console for item UX5
When the flow defined by the interface declared for UX5 executes
Then every acceptance seed for item UX5 holds  Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.
```

## Exception paths

If the interface declared for UX5 fails for item UX5, live-runtime-console must surface the failure exactly as the acceptance seeds below specify; no exception handling beyond those seeds is in scope. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Invariants

For item UX5, the interface declared for UX5 must continue to satisfy every acceptance seed below on every call; live-runtime-console must never show a state the seeds forbid. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Data impact

Item UX5 constrains any create, update, or delete reachable through the interface declared for UX5; only the acceptance seeds below define what data changes are permitted for live-runtime-console. Node-specific data assertions: 在 docs/prototypes/problem-intel-console.html 中展示研究成员、代际、预算、候选和验证状态 | 在 tests/test_runtime_console_reconnect.py 中证明断线后控制台从服务端快照恢复而不是从浏览器缓存猜测 | 在 matharc/v02/runtime/reconnect.py 中从服务端快照恢复断线会话并保留运行身份 Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Permissions

Item UX5 is owned by principal:acceptance-a; access to the interface declared for UX5 and live-runtime-console follows the acceptance seeds below and no wider grant. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py.

## Performance and reliability

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX5: the thresholds and failure evidence for the interface declared for UX5 must be evaluated against the shared policy and this item's acceptance seeds.

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-UX5 | machine/e2e | 在 docs/prototypes/problem-intel-console.html 中展示研究成员、代际、预算、候选和验证状态 | E2E | Automatic | Yes |
| AC-02 | behavior | SRC-UX5 | visual-fidelity | 在 tests/test_runtime_console_reconnect.py 中证明断线后控制台从服务端快照恢复而不是从浏览器缓存猜测 | Visual fidelity | Automatic | Yes |
| AC-03 | behavior | SRC-UX5 | machine/local-runtime | 在 matharc/v02/runtime/reconnect.py 中从服务端快照恢复断线会话并保留运行身份 | Local runtime | Automatic | Yes |

## Human acceptance

Item UX5 is fully determined by its acceptance seeds; outcomes for the interface declared for UX5 on live-runtime-console are machine-verifiable, so no human judgment step is declared.

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
| none | none | Behavior specification only for item UX5; executable baseline not yet locked. Concrete seed references: docs/prototypes/problem-intel-console.html, matharc/v02/runtime/reconnect.py, tests/test_runtime_console_reconnect.py |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | E2E | docs/prototypes/problem-intel-console.html | Automatic | Yes |
| AC-02 | Visual fidelity | tests/test_runtime_console_reconnect.py | Automatic | Yes |
| AC-03 | Local runtime | matharc/v02/runtime/reconnect.py | Automatic | Yes |

## Exploratory testing

Probe live-runtime-console for item UX5 under retry, interruption, and boundary-value inputs against the interface declared for UX5, beyond the deterministic acceptance seeds below.

## Production monitoring and rollback

Rollback for item UX5 reverts the change to the interface declared for UX5; no bespoke production metric is declared beyond the acceptance seeds below.

## Risks and open decisions

<!-- shared_acceptance_policy: SAP-MATHARC-RUNTIME@1 -->
Node-specific increment for item UX5: review risks specific to live-runtime-console and record any open decision.
