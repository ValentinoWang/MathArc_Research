# Acceptance Contract: RUN-U2-sse-runtime

- Task ID: RUN-U2-sse-runtime
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 研究基础设施负责人
- Approval evidence: 待研究基础设施负责人批准；当前仅为隔离草稿
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/U2.json
- SSOT node: U2
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.console-slices@1
- Assumption IDs: none
- Invalidation keys: implementation.problem-intelligence.console-readonly-wiring
- AC budget: 3
- Baseline identity: U1 approved baseline identity required; current candidate not yet locked
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#92后端端点与视图数据映射
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#93唯一视图清单32个
- Visual Contract refs: docs/prototypes/problem-intel-console.html, docs/prototypes/console-dev-blueprint.html
- UI Change declaration: agents-results/2026-08-31/problem-intelligence-plane/.ssot/ui-change/console-plan-v3.json
- Human acceptance workspace: none

## User and scenario

研究人员通过控制台观察当前工作区及攻克进程，需要 M0 静态导出和 M1 实时观察站呈现同一套只读事实，并在断线、代际变化或载荷失效时看到诚实的恢复状态。

## Problem

静态载荷、实时 API 与 SSE 可能在时序上交错。若缺少代际、游标和来源校验，页面可能混排演示与真实数据、显示陈旧工作区，或在重连后跳过和重复应用事件。

## Expected outcome

M0 把已审计工作区导出为工作区外的版本化 `console.json`，抓取失败时清除陈旧快照并显式标注演示回退；M1 通过只读 GET 与 SSE 观察当前工作区 campaign，按有序 `research_event` 游标续传，并将一个事件合并为一次 dashboard 刷新。

## Non-goals

不新增研究写口，不实现 M2 评审、M3 选题投影或 M4 运营账本，不证明生产高可用、设备适配或外部服务连通性。

## Normal path

```gherkin
Given 当前工作区有可验证的控制台投影和事件序列
When 用户加载静态导出或观察站并在新事件到达后继续浏览
Then 页面只呈现当前 provenance 下的真实字段
And SSE 从已见游标续传并以合并刷新保持选择和焦点
```

## Exception paths

- 静态导出缺失、schema 不兼容、provenance 或链头不匹配时清空陈旧载荷并进入明确的 `empty` 或 `error`，不得借演示字段补齐。
- SSE 断开时从最后已确认序号重连；`run_id` 改变、序号倒退或事件完整性失败时关闭旧流并完整重载。
- 重复或乱序响应不得覆盖较新的 UI 状态；失败重试不能制造成功、业务写入或研究结论。

## Invariants

- M0 与 M1 均只读；除既有独立评审服务外，观察站的其他写请求均拒绝。
- 真实投影与演示数据不得同屏混排，来源状态始终可见。
- 序号、前哈希、事件哈希、唯一事件 ID 和工作区链头全部通过后才可应用事件。

## Data impact

静态导出只写工作区外的显式目标；观察站与 SSE 不修改工作区。客户端只保存允许的浏览状态，载荷失败时丢弃陈旧内存快照。

## Permissions

获准查看工作区的研究人员可读取投影和事件；U2 不授予评审、晋升、问题状态、资料导入或运营写权限。

## Performance and reliability

同一事件窗口至多触发一次合并刷新；重连从服务器认可的已见游标继续。超时、断线、乱序或校验失败均 fail closed，并保留可再次加载的恢复入口。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PI-R6-U2-01 | machine/integration-contract | M0 将已审计工作区导出为工作区外的版本化 `console.json`；抓取失败会清除陈旧快照，并在使用演示回退时给出可见标记 | Integration/contract | Automatic | Yes |
| AC-02 | behavior | SRC-PI-R6-U2-02 | persistent-runtime | live observer 通过 SSE 按有序游标传输 `research_event` 记录，并支持从已确认游标继续 | Persistent runtime | Automatic | Yes |
| AC-03 | behavior | SRC-PI-R6-U2-03 | visual-fidelity | M1 仅使用只读 observer GET 与 SSE，campaign 报告始终绑定当前工作区，且一个事件只触发一次合并 dashboard 刷新 | Visual fidelity | Automatic | Yes |

## Human acceptance

本 fragment 的只读、时序、完整性和结构签名均可由确定性机器运行判断；跨视图视觉理解由 A6 的独立人工清单负责，因此此处不设置 H-* 项。

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Test baseline 为 PLANNED；批准并锁定可执行接口后登记 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 工作区外版本化导出、抓取失败清旧与演示标记合同测试 | 计划锁定的 M0 integration-contract run | Automatic | Yes |
| AC-02 | `research_event` 顺序与游标续传持久运行测试 | 计划锁定的 M1 persistent-runtime run | Automatic | Yes |
| AC-03 | 只读传输、当前工作区绑定与单事件合并刷新渲染测试 | 计划锁定的 M1 visual-fidelity run | Automatic | Yes |

## Exploratory testing

探测快速连续事件、慢响应覆盖、浏览器后台恢复、连接抖动和加载中切换视图；探索发现不替代 AC 的确定性门禁。

## Production monitoring and rollback

本合同只要求本地受支持运行时，不构成生产验收。若接线回归，禁用实时加载并回到明确标注的只读静态/不可用状态，不回退到混排演示数据。

## Risks and open decisions

真实浏览器矩阵与 `consumer_surface_digest` 尚待执行并锁定；严格 UI change 声明已经绑定，但在合同获批和 protected tests 锁定前不得宣称 M0/M1 正式验收完成。
