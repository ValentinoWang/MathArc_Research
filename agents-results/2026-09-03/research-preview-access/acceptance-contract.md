# Acceptance Contract: FEAT-20260903-01

- Task ID: FEAT-20260903-01
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 项目负责人
- Approval evidence: 本轮仅建立草稿，尚未获得人类批准
- Request source: 2026-09-03 user request for a real research-preview invitation flow
- SSOT node: none
- SSOT path: none
- Readiness mode: FORMAL
- Decision refs: none
- Assumption IDs: none
- Invalidation keys: access.research-preview.session
- AC budget: 4
- Baseline identity: main@2f992d9b441d3904cfe02bf84e3544363ef8107c plus the uncommitted access candidate reviewed on 2026-09-03
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#910关闭条件
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#93唯一视图清单32个
- Visual Contract refs: docs/prototypes/problem-intel-console.html
- UI Change declaration: agents-results/2026-09-03/research-preview-access/ui-change.json
- Human acceptance workspace: acceptance/human/2026-W36/2026-09-03-FEAT-20260903-01

## User and scenario

数学研究者或数学智能体研发者从公开控制台入口申请研究预览，或使用与机构邮箱绑定的一次性邀请码进入受保护工作区。

## Problem

旧页面只在浏览器内模拟登录，未向服务端验证邮箱、邀请码或会话，因而不能支持真实研究预览准入，也无法防止匿名访问工作区 API。

## Expected outcome

申请人能看到诚实的待审核状态；获邀用户只有在服务端验证邮箱和单次邀请码后才能进入工作区；会话可在刷新后恢复，退出后立即失效，访客模式不暴露真实工作区数据。

## Non-goals

本变更不包含生产部署、公司级身份提供商、邮件自动审批、支付、管理员发码界面或按 `topic_scopes` 裁剪工作区数据。

## Normal path

```gherkin
Given 研究者拥有与其邮箱绑定的未使用邀请码
When 研究者在公开入口提交邮箱和邀请码
Then 服务端创建限时会话并允许访问工作区
And 刷新页面可恢复同一会话
And 退出后原会话不再可用
```

## Exception paths

- 错误邮箱、错误码、过期码、已撤销码和已兑换码均拒绝准入，不泄露哪个字段错误。
- 网络失败、畸形响应或服务端状态无法验证时，页面停留在准入层并提供可重试反馈。
- 匿名请求所有工作区、活动、评审、事件和导出 API 均返回未授权；公开页、健康检查和准入 API 仍可达。
- 客户端退出失败时不伪装成已退出；会话确实撤销后清空实时数据和 SSE 连接。

## Invariants

- 邀请码和会话令牌的明文不得写入项目、持久化状态、浏览器存储或机器证据。
- 邀请码仅能由绑定邮箱兑换一次，会话过期或退出后不能恢复。
- 准入会话不替代原有评审写入 Bearer token，两层权限均必须满足。
- 访客演示与真实工作区数据隔离。

## Data impact

在项目目录外的运行状态目录中原子记录申请、邀请和会话摘要。密钥只存 SHA-256 摘要；退出仅撤销当前会话。本变更无数据库迁移，删除运行目录即可回滚本地验收状态。

## Permissions

匿名用户只能打开公开页、提交申请、兑换邀请和查询当前会话。只有持有有效 HttpOnly 会话 Cookie 的用户可读工作区；评审写入还必须持有现有 Bearer token。管理员发码不通过公开 HTTP API 暴露。

## Performance and reliability

服务为本地单进程预览工具；准入状态写入使用跨进程锁和原子替换，并在每次读取时验证记录一致性。服务重启后有效会话可恢复；本地性能和并发证据不外推为生产 SLA。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/integration-contract | 申请产生待审核记录，不直接授权；邮箱绑定的有效单次邀请可创建限时会话 | Unit and HTTP integration | Automatic | Yes |
| AC-02 | behavior | none | machine/integration-contract | 匿名用户不能访问工作区 API，但公开页、健康检查和准入 API 可达；评审写入仍需另外的 Bearer token | HTTP integration | Automatic | Yes |
| AC-03 | behavior | none | machine/e2e | 页面覆盖申请、错码、兑换、刷新恢复、重放拒绝、退出、访客隔离和移动端状态 | Browser E2E with hash-bound screenshots | Automatic | Yes |
| AC-04 | behavior | none | human | 目标研究者能理解准入、申请和访客边界，并在无隐藏指导时完成进入、刷新恢复与退出闭环 | Human product review | Human | Yes |

## Human acceptance

详细步骤和签署结果只保存在项目级人工验收工作区。当前合同与清单均是未批准草稿，本地浏览器证据不等于人工签署。

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 从公开入口完成申请或获邀准入、刷新恢复和退出，并正确理解访客边界 | acceptance/human/2026-W36/2026-09-03-FEAT-20260903-01/checklist.md#h-01 | 项目负责人或数学研究者代表 | Yes |

## Protected acceptance tests

当前合同尚未经验收所有者批准，因此不把实现后新增的测试冒充为事先锁定的 protected baseline。

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Contract remains DRAFT and the protected baseline remains PLANNED |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | Domain and HTTP integration suites | tests/test_v02_access.py; tests/test_v02_access_server.py | Automatic | Yes |
| AC-02 | Workspace authorization integration suite | tests/test_v02_access_server.py | Automatic | Yes |
| AC-03 | Browser access journey and screenshot manifest | scripts/console_browser_gate.mjs; agents-results/2026-09-03/research-preview-access/screenshot-manifest.json | Automatic | Yes |
| AC-04 | Human product review | acceptance/human/2026-W36/2026-09-03-FEAT-20260903-01/checklist.md#h-01 | Human | Yes |
| H-01 | Human product review | acceptance/human/2026-W36/2026-09-03-FEAT-20260903-01/checklist.md#h-01 | Human | Yes |

## Exploratory testing

人工补充探测长邮箱、慢网络、多标签页、会话临近过期、退出中断和小屏输入法。探测结果只能新增缺陷或收紧后续范围，不能绕过阻塞性项。

## Production monitoring and rollback

本合同不包含生产发布。本地验收可通过停止服务并删除项目外的临时准入目录回滚；未来生产化需单独定义 TLS、密钥管理、监控、告警和撤回手段。

## Risks and open decisions

人工尚未批准合同或清单，也未签署 H-01；因此工程实现和本地机器验证可提交，但不能宣称人工验收或生产发布已完成。
