# Acceptance Contract: RUN-A7-console-controls

- Task ID: RUN-A7-console-controls
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 研究负责人和仓库所有者
- Approval evidence: 待研究负责人和仓库所有者共同批准；当前仅为隔离草稿
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A7.json
- SSOT node: A7
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.console-slices@1
- Assumption IDs: none
- Invalidation keys: release.problem-intelligence.console-v0
- AC budget: 3
- Baseline identity: U4, U5 and A5 current accepted identities required; release candidate not yet locked
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#910关闭条件
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#93唯一视图清单32个
- Visual Contract refs: docs/prototypes/problem-intel-console.html, docs/prototypes/console-dev-blueprint.html
- UI Change declaration: agents-results/2026-08-31/problem-intelligence-plane/.ssot/ui-change/console-plan-v3.json
- Human acceptance workspace: acceptance/human/2026-W36/2026-09-02-RUN-A7-console-controls

## User and scenario

研究负责人和仓库所有者需要在 U4 选题投影、U5 本地运营域及上游 A5 当前有效后，对控制台 v0 的平面①和账户端作独立发布决定，确保用户能理解只读投影、运营记录和研究结论之间的边界。

## Problem

局部实现或机器绿灯不能证明整个发布范围诚实。若沿用旧 A5/U4/U5 证据、隐藏未配置外部能力，或让用户把选题观察和运营数值误读为数学结论，控制台会在权限和披露边界尚未成立时被标为可发布。

## Expected outcome

A7 的发布门禁拒绝编造数字：计数必须派生，协议参数必须引用来源版本，禁止伪精确难度分；空 campaign 不借用数据，被拒绝的 promotion 不创建也不显示事件；人工发布复核拒绝缺少四态 chip 的能力声明或把计划能力呈现为已落地。当前仍只形成 `DRAFT`/`PLANNED` 合同，不代表已验收或可发布。

## Non-goals

不批准真实身份、支付、付费上游、外部文献服务或生产部署，不确认问题开放、已解决、新颖性或数学证明，不把本地/浏览器证据升级为设备或生产证据。

## Normal path

```gherkin
Given U4、U5 和 A5 均有当前有效且消费面一致的接受证据
When 发布综合门禁通过且授权角色完成 H-01 业务边界闭环
Then 发布决定只列出已验收的控制台 v0 范围
And 所有未配置、未校准和非研究结论事项仍显式披露
```

## Exception paths

- U4、U5、A5 任一非当前接受态、摘要漂移、证据缺失或历史回放身份不一致时阻断 A7，不复用旧 PASS。
- 任一未配置外部能力被显示为可用、选题记录被呈现为裁定或运营记录影响研究重放时发布结论为 FAIL/PARTIAL。
- H-01 未批准、未执行、非 PASS 或共同批准人缺失时不产生发布接受记录；修复后必须使用新 run 重验。

## Invariants

- 发布范围严格等于已验收范围，不能用未来配置、演示数据或计划项填补。
- 平面①、账户端、选题投影、运营账本和研究结论始终保持来源与权限分离。
- A7 只记录发布决定，不修改研究工作区、运营账本、上游证据或人类签名。

## Data impact

仅创建不可变的 A7 release evidence 和共同决定记录；不部署、不写业务数据。上游身份或消费面变化时当前决定失效，历史记录保留审计且不可重标复用。

## Permissions

研究负责人和仓库所有者必须共同作出最终决定；主题观测负责人和研究基础设施负责人提供上游证据；真实产品角色执行 H-01，但不能单独批准发布。

## Performance and reliability

发布综合必须一次性读取固定上游 run ID、摘要和状态，避免检查期间漂移；任一来源变化或不可读即 fail closed。不存在通过重试掩盖缺项或跨来源拼接 PASS 的路径。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PI-R7-A7-01 | release | 控制台若包含编造数字则发布失败：计数必须由来源派生，协议参数必须引用来源版本，并禁止伪精确难度分 | Release gate | Automatic | Yes |
| AC-02 | behavior | SRC-PI-R7-A7-02 | release | 发布保持诚实空态：空 campaign 不得借用其他数据，被拒绝的 promotion 不得创建或在界面伪造事件 | Release gate | Automatic | Yes |
| AC-03 | behavior | SRC-PI-R7-A7-03 | human | 人工发布复核必须拒绝任何缺少四态 chip 的能力声明，以及任何把计划能力呈现为已落地行为的界面 | Human release review | Human | Yes |

## Human acceptance

详细步骤和签署结果只保存在项目级 workspace；当前清单是未批准、未执行草稿，不能计作 A7 或发布通过。

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 从真实入口拒绝缺少四态 chip 的能力声明，或把计划能力呈现为已落地行为的界面 | acceptance/human/2026-W36/2026-09-02-RUN-A7-console-controls/checklist.md#h-01 | 研究负责人和被授权的运营边界负责人 | Yes |

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Test baseline 为 PLANNED；批准并锁定可执行接口后登记 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 派生计数、来源版本引用和伪精确难度负测 | 计划锁定的 A7 release run | Automatic | Yes |
| AC-02 | 空 campaign 与被拒 promotion 的零借用、零事件门禁 | 计划锁定的 A7 release run | Automatic | Yes |
| AC-03 | 四态 chip 与计划/已落地声明人工复核 | acceptance/human/2026-W36/2026-09-02-RUN-A7-console-controls/checklist.md#h-01 | Human | Yes |
| H-01 | 四态 chip 与计划/已落地声明人工复核 | acceptance/human/2026-W36/2026-09-02-RUN-A7-console-controls/checklist.md#h-01 | Human | Yes |

## Exploratory testing

探测部分外部配置、跨工作区导航、陈旧浏览器标签、重放后快速切换和长免责声明；探索发现只能收紧或新增后续范围，不能绕过发布阻断项。

## Production monitoring and rollback

本合同不包含生产部署或监控。若未来发布后发现范围误标，应撤回控制台 v0 发布决定并恢复为明确不可用/未配置状态；生产回滚需另立合同。

## Risks and open decisions

U4/U5/A5 当前身份、source registry、人工清单/binding 和 protected tests 尚未全部锁定；严格 UI change 声明已经绑定，但 A7 必须保持 `DRAFT`/`PLANNED`，不能代表 release-ready。
