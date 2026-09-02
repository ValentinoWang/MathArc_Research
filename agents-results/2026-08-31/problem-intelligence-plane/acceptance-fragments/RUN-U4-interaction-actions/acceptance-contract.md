# Acceptance Contract: RUN-U4-interaction-actions

- Task ID: RUN-U4-interaction-actions
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 主题观测负责人
- Approval evidence: 待主题观测负责人批准；当前仅为隔离草稿
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/U4.json
- SSOT node: U4
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.console-slices@1
- Assumption IDs: none
- Invalidation keys: implementation.problem-intelligence.console-local-projections
- AC budget: 3
- Baseline identity: A6, A4, R1 and Q1 current accepted identities required; current candidate not yet locked
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#95固定夹具检索路线与真实档案
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#92后端端点与视图数据映射
- Visual Contract refs: docs/prototypes/problem-intel-console.html, docs/prototypes/console-dev-blueprint.html
- UI Change declaration: agents-results/2026-08-31/problem-intelligence-plane/.ssot/ui-change/console-plan-v3.json
- Human acceptance workspace: none

## User and scenario

主题观测负责人需要在控制台查看 M3 选题资料，包括资料核验、四路回归、三例档案、难度与披露记录，同时明确这些都是来源绑定的只读投影，不是开放、已解决或新颖性的裁定入口。

## Problem

选题视图容易把固定夹具、局部命中和人工队列误读为研究结论。若缺少显式配置、provenance 和未校准边界，页面可能以演示数值填补缺口，或把小样本聚合成无依据总分。

## Expected outcome

M3 只读投影 SourceRegistry、SourceObservation、LiteratureBase、单主题游标和人工队列，不提供数据录入界面；R1 四条固定来源检索路线逐例呈现 scope、hits 和 unresolved；T2 三个档案合同逐例呈现身份、预期状态、人工理由和不晋升边界，执行与恢复继续由后端 runner 负责。

## Non-goals

不调用外部文献提供方，不写 SourceRegistry、主题存储、问题状态、NoveltyAuditRecord 或 ResearchTrace，不进行统计校准、总分排名或公开研究授权。

## Normal path

```gherkin
Given 当前工作区显式配置了身份匹配的选题资料和已接受上游工件
When 研究人员打开资料、路线、档案、难度和披露视图
Then 每个字段可追溯到对应只读来源和 provenance
And 页面保留未校准、不推断和不晋升边界
```

## Exception paths

- 任一配置路径缺失、内容摘要或上游接受身份不匹配时，对应投影为 `not_configured`、`empty` 或 `error`，不使用演示替代。
- 四路记录不完整、三例身份漂移或披露政策陈旧时拒绝该投影，其他独立投影不得掩盖失败。
- 样本不足、预测未校准或人工审计待定时不计算总分、不排序为结论，也不生成开放、已解决或新颖性判断。

## Invariants

- M3 全部为只读投影，不能借视图动作改写任何研究对象。
- R1 四路和 T2 三例保持各自规范身份、顺序、来源与限制，不由前端重解释。
- 科学优先级、难度记录和传播准备度相互分离；任一高值不自动解锁公开传播。

## Data impact

仅读取既有本地工件并生成内存或工作区外的确定性投影；运行前后受控来源字节不变。配置移除后投影立即不可用，不保留冒充当前事实的缓存。

## Permissions

获准研究人员可查看选题投影；主题观测负责人维护配置边界。U4 不授予资料导入、状态裁定、审计批准、预算授权、晋升或公开发布权限。

## Performance and reliability

同一来源身份产生相同规范投影；各投影独立 fail closed，单项缺失不能污染其他项。读取错误、摘要漂移或陈旧上游身份必须给出可诊断原因并允许修复配置后重试。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PI-R7-U4-01 | machine/integration-contract | M3 只读投影 SourceRegistry、SourceObservation、LiteratureBase、单主题游标和人工队列，且不授权或呈现数据录入界面 | Integration/contract | Automatic | Yes |
| AC-02 | behavior | SRC-PI-R7-U4-02 | machine/integration-contract | 控制台呈现 R1 的四条具名固定来源检索路线，并为每例完整显示 scope、hits 和 unresolved 项 | Integration/contract | Automatic | Yes |
| AC-03 | behavior | SRC-PI-R7-U4-03 | machine/e2e | 控制台呈现 T2 三个档案合同的案例身份、预期状态、人工理由和不晋升边界，执行与恢复仍只由后端 runner 负责 | Browser E2E | Automatic | Yes |

## Human acceptance

本 fragment 的来源、只读性、身份和禁止推断边界可由确定性机器测试裁定；业务角色是否真正理解这些边界由 A7 的独立人工闭环判断，因此此处不设置 H-* 项。

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Test baseline 为 PLANNED；批准并锁定可执行接口后登记 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 五类只读投影与无数据录入入口合同测试 | 计划锁定的 M3 integration-contract run | Automatic | Yes |
| AC-02 | R1 四路线 scope、hits、unresolved 完整性合同测试 | 计划锁定的 R1 integration-contract run | Automatic | Yes |
| AC-03 | T2 三档案身份、状态、理由、不晋升及后端执行边界浏览器测试 | 计划锁定的 T2 machine/e2e run | Automatic | Yes |

## Exploratory testing

探测部分配置、来源刚好在加载中被替换、空四路命中、超长未决项和高优先级但不可传播案例；探索结果不允许降低禁止推断边界。

## Production monitoring and rollback

不适用。本合同覆盖本地只读投影而非生产外部检索；回归时关闭受影响投影并显示不可用原因，不回退为无标注演示事实。

## Risks and open decisions

A4、R1、Q1 必须以当前有效接受身份进入 U4，历史接受记录不可复用。严格 UI change 声明已经绑定，但 protected tests 尚未锁定，合同保持草稿。
