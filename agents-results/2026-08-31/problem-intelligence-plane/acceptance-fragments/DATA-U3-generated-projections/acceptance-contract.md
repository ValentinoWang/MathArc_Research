# Acceptance Contract: DATA-U3-generated-projections

- Task ID: DATA-U3-generated-projections
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 研究基础设施负责人
- Approval evidence: 待研究基础设施负责人批准；当前仅为隔离草稿
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/U3.json
- SSOT node: U3
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.console-slices@1
- Assumption IDs: none
- Invalidation keys: implementation.problem-intelligence.console-review-loop
- AC budget: 3
- Baseline identity: U2 accepted readonly-wiring identity required; current candidate not yet locked
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#92后端端点与视图数据映射
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#96交互状态与安全语义
- Visual Contract refs: docs/prototypes/problem-intel-console.html, docs/prototypes/console-dev-blueprint.html
- UI Change declaration: agents-results/2026-08-31/problem-intelligence-plane/.ssot/ui-change/console-plan-v3.json
- Human acceptance workspace: none

## User and scenario

受权评审人需要从控制台读取当前命题的评审队列和送审包，逐项判断义务后通过既有唯一评审写口提交决定，并在服务真正持久化后看到更新后的队列与证据身份。

## Problem

如果界面只在按钮点击后显示成功、允许带未满足义务的 `APPROVE`、接受陈旧送审包，或把名册令牌保存到持久客户端存储，M2 会制造未经服务确认的评审事实并扩大安全边界。

## Expected outcome

M2 评审闭环只使用当前版本和摘要匹配的真服务送审包；任一非 `OK` 义务阻断 `APPROVE`；有效决定必须经 `/api/review` 持久化并读回队列和证据 ID 后才显示成功，令牌始终只驻留密码输入和内存。

## Non-goals

不新增第二个研究写口，不修改命题、证明、资料或晋升流程，不实现身份提供方、长期令牌存储、生产认证或 A6 人工视觉验收。

## Normal path

```gherkin
Given 受权评审人打开与当前命题修订和 bundle 摘要匹配的送审包
When 所有义务均为 OK 且评审人提交有效决定
Then 服务持久化评审并返回可读回的证据身份
And 页面刷新队列后才显示 success 并清空令牌
```

## Exception paths

- `APPROVE` 包含任一非 `OK` 义务时服务拒绝，且不创建评审或证据。
- 命题修订、bundle 摘要、名册身份或权限不匹配时拒绝提交；旧评审标记为 `SUPERSEDED` 而非继续生效。
- 网络失败、持久化失败或读回失败时不得显示成功；令牌在成功和失败路径都清空，重试重新加载当前送审包。

## Invariants

- `/api/review` 是唯一研究写口，且必须同源；控制台不得生成备用写端点。
- 客户端状态和乐观 UI 不是评审事实，只有服务持久化并读回的记录可显示为有效。
- 名册令牌不得进入 URL、日志、导出、`localStorage` 或 `sessionStorage`。

## Data impact

成功路径只通过既有评审服务创建一条受审计评审记录及其证据；拒绝和失败路径不产生部分记录。重试必须使用当前修订和 bundle 身份，不能复用陈旧提交。

## Permissions

只有当前名册中具备对应义务权限的评审人可以提交；普通研究人员只能读取获准的队列/送审包，不能评审、晋升或改写研究对象。

## Performance and reliability

提交有明确超时和终态；重复提交由服务身份与当前状态确定性处理，不能产生无法区分的双重有效决定。任何写入或读回不确定性均保持非成功状态。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PI-R6-U3-01 | machine/integration-contract | M2 将评审队列和送审包暴露为只读接口，仅允许名册令牌评审提交到 `POST /api/review`，并拒绝所有其他写路由 | Integration/contract | Automatic | Yes |
| AC-02 | behavior | SRC-PI-R6-U3-02 | persistent-runtime | 只有所有义务 verdict 均为 `OK` 才可批准；评审记录绑定修订、失配时变为 `SUPERSEDED`，且 `can_review` 始终按具体对象判定 | Persistent runtime | Automatic | Yes |
| AC-03 | behavior | SRC-PI-R6-U3-03 | machine/e2e | 控制台读取真实名册、评审队列和送审包，呈现各义务决定，仅通过唯一评审端点提交，并只在内存中保存令牌 | Browser E2E/security | Automatic | Yes |

## Human acceptance

本 fragment 的权限、事务结果、读回身份和令牌驻留均可由自动化确定性判断；评审流程的跨视图理解由 A6 人工验收覆盖，因此此处不设置 H-* 项。

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Test baseline 为 PLANNED；批准并锁定可执行接口后登记 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 队列/送审包只读、唯一写口与其他写路由拒绝测试 | 计划锁定的 M2 integration-contract run | Automatic | Yes |
| AC-02 | 全义务 OK、修订失配转态与对象级权限持久运行测试 | 计划锁定的 M2 persistent-runtime run | Automatic | Yes |
| AC-03 | 真实名册/队列/送审包、义务呈现、唯一提交和内存令牌浏览器测试 | 计划锁定的 M2 machine/e2e run | Automatic | Yes |

## Exploratory testing

探测双击提交、刷新期间送审包变化、浏览器返回/前进、断网恢复和多个标签页；发现的问题不得降低三条阻断 AC。

## Production monitoring and rollback

不构成生产认证验收。若 M2 行为回归，关闭控制台提交能力并保留只读队列；不得切换到未经审计的客户端本地决定。

## Risks and open decisions

真实身份提供方与生产权限模型不在本切片内；严格 UI change 声明已经绑定，但受保护测试摘要尚未锁定，合同保持 `DRAFT`/`PLANNED`。
