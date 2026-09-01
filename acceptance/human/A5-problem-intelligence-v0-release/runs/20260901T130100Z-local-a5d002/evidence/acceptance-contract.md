# Acceptance Contract: A5-problem-intelligence-v0-release

- Task ID: A5-problem-intelligence-v0-release
- Contract version: 3
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: 研究负责人和仓库所有者
- Approval evidence: 用户已明确要求验收通过、持续完成，并在每个阶段提交和推送 GitHub；Q1 当前身份已由机器、H-01 和两条独立 AI 复审重新接受。
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A5.json
- SSOT node: A5
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/.ssot/manifest.json
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.amendment@2
- Assumption IDs: none
- Invalidation keys: release.problem-intelligence.v0
- Baseline identity: origin/main@ea3a76b98273a120f4acb5b8926877a32ff063fd
- Human acceptance workspace: acceptance/human/A5-problem-intelligence-v0-release

## User and scenario

研究负责人和仓库所有者需要将已接受的问题情报平面 v0 的仓库源级范围提交并交付到 GitHub `main`，同时防止该交付被误读为数学结论、外部资料结论或生产发布。

## Problem

Q1 仅产生三例固定档案的本地 `UNCALIBRATED`、`NOT_READY` 披露策略，且明确不授权公开发布。若没有独立 A5 记录，代码推送可能被误表述为校准完成、开放状态确认、新颖性接受或数学成果发布。

## Expected outcome

存在一个由 A5 独占写入的发布决定记录：它哈希绑定已接受 Q1 证据、政策夹具、实现和保护测试；仅授权已接受的仓库源、测试、SSOT 记录和验收证据交付到 GitHub `main`。它必须明确保留 Q1 的 `public_release_allowed=false`，并要求推送后的远端 ref 回读才可声称 GitHub 交付完成。

## Non-goals

不接受数学证明或定理；不执行实时外部文献检索或开放状态确认；不接受新颖性；不声明校准质量、准确率、召回率、统计性能或泛化；不产生生产、已部署服务、设备或监控证据；不授权公开传播任何研究结论。

## Normal path

```gherkin
Given a byte-locked current accepted Q1 evidence record and its fixed uncalibrated policy
When the joint source-level release decision is reviewed
Then A5 records only the accepted repository source scope and every excluded claim
And GitHub delivery may be claimed only after the final local HEAD equals origin/main by remote ref readback
```

## Exception paths

- Q1 evidence、政策夹具、政策摘要、实现或保护测试哈希漂移时，拒绝 A5 记录。
- 三例范围、`UNCALIBRATED`/`NOT_READY` 双轨或 Q1 的 `public_release_allowed=false` 不成立时，拒绝 A5。
- 任一禁止声明被移除，或研究结论发布授权变为真时，拒绝 A5。
- 推送失败、远端 `main` 与最终本地 HEAD 不一致，或远端身份无法读取时，不得声称 GitHub 交付完成；保留本地验收记录并修复传输后重新回读。

## Invariants

- A5 的证据等级恒为 `source`，写入权限仅限独立发布决定记录。
- A5 不能把 Q1 的 `public_release_allowed=false` 转换为研究结论公开授权。
- 允许范围只包含 `union-closed` 的固定三例本地/仓库工件和其 GitHub 源码交付，不包含任何外部或生产事实。
- 远端 SHA 相等是 GitHub 交付声明的必要条件，不是数学、文献、新颖性、统计或生产验证的替代品。

## Data impact

仅创建不可变的 A5 证据、机器/发布运行记录和项目级人工验收记录；不修改业务数据、外部系统、生产环境或既有 Q1 政策。

## Permissions

研究负责人和仓库所有者共同接受范围受限的 A5 决定。自动化只验证哈希、结构和范围边界，不能代替两种角色的发布语义判断。GitHub 推送由仓库所有者已授权的本地工作流执行。

## Performance and reliability

本地静态验证应在 1 秒内完成。发布决定没有服务运行时；GitHub 交付必须在单次推送后立即回读 `refs/heads/main`。远端分歧、缺少回读或身份漂移均 fail closed。

## Acceptance criteria

| ID | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | A5 严格绑定已接受 Q1 证据、政策、实现和保护测试身份 | Unit | Automatic | Yes |
| AC-02 | 仅允许仓库源级交付，完整列出数学、文献、新颖性、校准、生产和研究结论禁止项 | Unit | Automatic | Yes |
| AC-03 | A5 要求 GitHub `main` 的推送后远端 SHA 回读，推送前不声称交付 | Unit/Release | Automatic | Yes |
| AC-04 | 发布决定的合同、分根验收记录、SSOT、快照与严格验证均通过 | Contract/SSOT | Automatic | Yes |

## Human acceptance

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 联合确认允许的只是仓库源级交付，任何研究结论及外部、统计和生产声明仍被禁止 | acceptance/human/A5-problem-intelligence-v0-release/checklist.md#h-01 | 研究负责人和仓库所有者 | Yes |

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| tests/test_v02_release_decision.py | 15ce8bb5d33e2291b7bef161ab393ee44143370e6507f62c48817be83f54b031 | AC-01, AC-02, AC-03 |
| tests/test_v02_calibration_disclosure.py | 89d52c973a0d5e026da855aef85a57db8656e6cc5b593b98f09ff6d2541318db | AC-01, AC-02 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | release decision and Q1 policy unit tests | tests/test_v02_release_decision.py, tests/test_v02_calibration_disclosure.py | Automatic | Yes |
| AC-02 | source-level scope and prohibitions unit test | tests/test_v02_release_decision.py | Automatic | Yes |
| AC-03 | remote-readback invariant unit test plus final `git ls-remote` command | tests/test_v02_release_decision.py; release run result | Automatic | Yes |
| AC-04 | contract/index checker, SSOT validator, snapshot check and archive audit | acceptance and SSOT validation outputs | Automatic | Yes |
| H-01 | joint human checklist | acceptance/human/A5-problem-intelligence-v0-release/checklist.md#h-01 | Human | Yes |

## Exploratory testing

检查任一 Q1 身份摘要、范围计数、允许/禁止列表、研究结论授权或远端回读要求被篡改时的拒绝行为；探索结果不能扩大 A5 范围。

## Production monitoring and rollback

不适用。A5 不部署服务。若 Q1/R1 身份或披露边界变化，或 GitHub 远端回读失败，废止本次 A5 决定并从受影响的 Q1/A5 证据重新验收；不回滚或修改外部系统。

## Risks and open decisions

GitHub 源码交付并不回答数学真伪、文献完整性、新颖性、统计性能或生产可用性。任何面向公众的研究结论需要独立的后续授权与相应证据，不能引用 A5 代替。
