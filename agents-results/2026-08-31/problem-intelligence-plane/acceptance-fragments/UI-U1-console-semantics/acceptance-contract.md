# Acceptance Contract: UI-U1-console-semantics

- Task ID: UI-U1-console-semantics
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 验收负责人（用户授权）
- Approval evidence: 待验收负责人批准；当前仅为隔离草稿
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/U1.json
- SSOT node: U1
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.console-slices@1
- Assumption IDs: none
- Invalidation keys: contract.problem-intelligence.console-visual-baseline
- AC budget: 3
- Baseline identity: decision.problem-intelligence.console-slices@1; consumer_surface_digest 待源注册表集成后计算
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#92后端端点与视图数据映射
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#93唯一视图清单32个
- Visual Contract refs: docs/prototypes/problem-intel-console.html, docs/prototypes/console-dev-blueprint.html
- UI Change declaration: agents-results/2026-08-31/problem-intelligence-plane/.ssot/ui-change/console-plan-v3.json
- Human acceptance workspace: none

## User and scenario

验收负责人需要先冻结控制台的视觉基线、唯一视图、状态词汇和建设状态，供后续只读接线、视觉还原与交互验收消费，而不让原型常量或某次截图成为新的业务事实源。

## Problem

当前蓝图、原型、浏览器门禁和 SSOT 阅读投影分别描述视图、案例与建设状态。若没有一个带来源摘要的基线合同，后续实现可以漏掉视图、重复计算导航入口，或在来源变化后沿用旧视觉证据。

## Expected outcome

产生一个确定性的控制台视觉基线：保留 root、system dark、explicit dark 三种 token 模式及蓝图声明的组件类；保留 topbar、plane switcher 和三列应用壳；每个视图恰好标记五种建设状态之一，且标记为已落地时必须有自动化证据。

## Non-goals

不实现 M0-M4 接线，不运行浏览器或人工视觉验收，不批准候选视觉方向，不改变后端、研究状态、发布状态或现有人工清单。

## Normal path

```gherkin
Given 已接受的控制台切片决定与冻结蓝图来源
When 静态合同核对视觉 token、组件类、应用壳和每个视图的建设状态
Then 三种 token 模式、声明组件类、topbar、plane switcher 和三列结构均被保留
And 每个视图只有一个建设状态，任何已落地声明都有自动化证据
```

## Exception paths

- 任一 token 模式、声明组件类、topbar、plane switcher 或三列壳缺失时，静态合同失败。
- 任一视图无建设状态、多重建设状态或使用五态词汇之外的值时 fail closed。
- 视图标记为已落地却没有可定位的自动化证据时，不得接受该状态声明。

## Invariants

- 后端投影始终是业务事实源；视觉基线只拥有蓝图声明的视觉、布局和建设状态语义。
- 三种 token 模式和声明组件类不能被合并为一个隐式主题。
- 建设状态一视图一值；计划、待接线、部分待建、需新建或已推迟均不能冒充已落地。

## Data impact

仅创建可再生的基线合同与摘要；不写研究工作区、业务数据库、运营账本或人类验收结果。来源改变时废止旧摘要并重新生成，不覆盖历史证据。

## Permissions

验收负责人拥有基线合同批准权；控制台维护者可提出来源映射；后续实现和验证节点只能消费已批准且摘要匹配的基线，不能自行改写它。

## Performance and reliability

同一输入字节必须得到相同清单、排序和摘要；校验必须在本地有界完成，任一缺失或不可解析来源均返回失败且不产生部分可接受基线。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PI-R6-U1-01 | machine/static | 视觉基线完整保留 root、system dark、explicit dark 三种 token 模式以及蓝图声明的全部组件类 | Static contract | Automatic | Yes |
| AC-02 | behavior | SRC-PI-R6-U1-02 | machine/static | 控制台应用壳完整保留蓝图声明的 topbar、plane switcher 和三列结构 | Static contract | Automatic | Yes |
| AC-03 | behavior | SRC-PI-R6-U1-03 | machine/static | 每个控制台视图恰好具有五种建设状态之一；任何已落地状态都必须关联自动化证据 | Static contract | Automatic | Yes |

## Human acceptance

本 fragment 只判断清单、映射和摘要的确定性完整性，机器证据可以完全裁定；视觉理解与候选选择分别由 A6 人工验收和项目视觉工作台处理，因此不设置 H-* 项。

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Test baseline 为 PLANNED；批准并锁定可执行接口后登记 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 三种 token 模式和声明组件类静态覆盖检查 | 计划锁定的 U1 静态合同门禁 | Automatic | Yes |
| AC-02 | topbar、plane switcher 和三列壳静态结构检查 | 计划锁定的 U1 静态合同门禁 | Automatic | Yes |
| AC-03 | 每视图唯一五态与已落地证据引用检查 | 计划锁定的 U1 静态合同门禁 | Automatic | Yes |

## Exploratory testing

检查重复导航入口、仅标题不同的同义视图、动作数据键顺序变化和来源换行变化；探索结果用于改进规范化规则，不替代阻断门禁。

## Production monitoring and rollback

不适用。该 fragment 是源级合同，不部署到生产；来源漂移时回退为未批准基线并阻断下游证据复用。

## Risks and open decisions

源需求注册表与严格 UI change 声明已经绑定；合同仍待验收负责人批准并锁定 protected tests，因此保持 `DRAFT`/`PLANNED`。本合同不得被解读为视觉还原、实现或发布已完成。
