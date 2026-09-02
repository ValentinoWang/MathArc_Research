# Acceptance Contract: VIS-U5-visual-workbench

- Task ID: VIS-U5-visual-workbench
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 研究基础设施负责人
- Approval evidence: 待研究基础设施负责人批准；当前仅为隔离草稿
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/U5.json
- SSOT node: U5
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.console-slices@1
- Assumption IDs: none
- Invalidation keys: implementation.problem-intelligence.console-operations-domain
- AC budget: 3
- Baseline identity: A6 accepted console-wiring identity required; current candidate not yet locked
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-09-01/console-publication-pipeline/implementation-boundary-v2.md
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#92后端端点与视图数据映射
- Visual Contract refs: docs/prototypes/problem-intel-console.html, docs/prototypes/console-dev-blueprint.html
- UI Change declaration: agents-results/2026-08-31/problem-intelligence-plane/.ssot/ui-change/console-plan-v3.json
- Human acceptance workspace: none

## User and scenario

研究基础设施负责人需要通过 M4 本地运营域查看账户、积分、席位、计费和上游配置状态，同时保证这些记录与研究工作区隔离，且不会改变历史研究重放或制造尚未接入的外部能力。

## Problem

运营记录若写入研究工作区、缺少工作区 provenance 绑定或允许跨工作区复用，会污染研究回放。外部身份、支付和上游尚未获得配置及授权时，界面若显示演示余额或连接状态，会形成虚假的运营事实。

## Expected outcome

M4 提供账户概览、积分账本、充值与计划、预算与限额四类蓝图界面；运营账本保持本地并与研究核心隔离，身份、支付和真实上游路由必须另行批准与集成；账户和管理视图读取研究工作区外相互独立的积分、席位、计费和上游账本，未配置外部连接明确显示 `not_configured`。

## Non-goals

不接入真实身份提供方、支付处理器、付费上游或跨机器集中账户服务，不修改研究事实、预算、评审、晋升或数学结论，不以本地账本证明生产计费正确。

## Normal path

```gherkin
Given 工作区外存在严格校验且与当前工作区 provenance 绑定的本地运营账本
When 获准用户查看账户和管理端运营视图并追加受支持本地记录
Then 账本耐久读回且研究工作区字节保持不变
And 未配置外部能力继续明确显示 not_configured
```

## Exception paths

- 账本路径位于研究工作区内、provenance 不匹配或试图跨工作区复用时拒绝打开或追加。
- 记录字段、链、规范摘要或持久化原子性校验失败时不更新内存成功态，也不留下部分有效记录。
- 外部身份、支付或上游未配置时不发起外部副作用，不用演示账户、余额、费率或连接状态替代。

## Invariants

- 运营域不导入或改写研究 replay 状态，研究工作区永远不是运营账本存储位置。
- 每条本地记录规范化、可重载、追加式且绑定当前工作区 provenance；其他工作区不能冒用。
- 模型、上游或运营元数据变化不能改变既有研究结论及其重放字节。

## Data impact

仅在显式指定的工作区外账本追加本地运营记录；写入采用完整校验和原子替换，失败不污染内存。研究工作区、外部身份、支付系统和上游账户均无写入。

## Permissions

受权运营负责人可查看和追加合同允许的本地记录；研究人员只有获准只读视图。真实账户、支付或上游操作需要独立授权，不由 U5 隐式授予。

## Performance and reliability

并发追加必须串行化并在写前重载当前状态，避免丢写；持久化成功后才更新内存。重启后严格重载同一记录与摘要，任何畸形或陈旧 provenance 均 fail closed。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PI-R7-U5-01 | machine/integration-contract | M4 提供蓝图声明的账户概览、积分账本、充值与计划、预算与限额界面 | Integration/contract | Automatic | Yes |
| AC-02 | behavior | SRC-PI-R7-U5-02 | machine/unit | 运营账本保持本地并与研究核心隔离；身份、支付和真实上游路由必须经过独立批准与集成，U5 不隐式启用 | Unit | Automatic | Yes |
| AC-03 | behavior | SRC-PI-R7-U5-03 | machine/e2e | 账户和管理视图读取研究工作区外相互独立的本地积分、席位、计费和上游账本，并将外部身份、支付和上游连接显示为 `not_configured` | Browser E2E | Automatic | Yes |

## Human acceptance

本 fragment 的隔离、耐久、重放字节和未配置外部副作用均可由机器确定性判断；业务用户是否理解运营与研究边界由 A7 人工闭环负责，因此不设置 H-* 项。

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Test baseline 为 PLANNED；批准并锁定可执行接口后登记 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 四类运营界面数据合同覆盖测试 | 计划锁定的 M4 integration-contract run | Automatic | Yes |
| AC-02 | 本地运营隔离与未获独立批准能力禁用单元测试 | 计划锁定的 M4 machine/unit run | Automatic | Yes |
| AC-03 | 四类工作区外独立账本与三类 `not_configured` 视图测试 | 计划锁定的 M4 machine/e2e run | Automatic | Yes |

## Exploratory testing

探测磁盘写失败、两个进程同时追加、畸形旧账本、工作区刚发生转换和外部配置只完成一半；探索结果不放宽隔离或 fail-closed 规则。

## Production monitoring and rollback

不适用。本合同只验收本地隔离账本，不覆盖外部运营生产系统；回归时关闭运营写入并保留明确不可用状态，不迁移数据到研究工作区。

## Risks and open decisions

真实身份、支付、计费和付费上游均需未来独立决定与 sandbox/production 证据。严格 UI change 声明已经绑定，但 protected tests 尚未锁定，合同保持草稿。
