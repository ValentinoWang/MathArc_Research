# Acceptance Contract: VIS-A6-console-rendering

- Task ID: VIS-A6-console-rendering
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 验收负责人
- Approval evidence: 待验收负责人批准；当前仅为隔离草稿
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A6.json
- SSOT node: A6
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.console-slices@1
- Assumption IDs: none
- Invalidation keys: acceptance.problem-intelligence.console-wiring
- AC budget: 3
- Baseline identity: U1 baseline plus U2/U3 candidate identities required; consumer_surface_digest not yet locked
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#96交互状态与安全语义
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#94渲染状态案例清单52个
- Visual Contract refs: docs/prototypes/problem-intel-console.html, docs/prototypes/console-dev-blueprint.html, agents-results/2026-08-31/problem-intelligence-plane/.ssot/workbench/console-visual-workbench.json
- UI Change declaration: agents-results/2026-08-31/problem-intelligence-plane/.ssot/ui-change/console-plan-v3.json
- Human acceptance workspace: acceptance/human/2026-W36/2026-09-02-VIS-A6-console-rendering

## User and scenario

验收负责人需要对 PI-R6 的 U2 只读接线和 U3 评审闭环作独立验收，确认平面③、平面②与管理端在支持的浏览器矩阵中既保持冻结视觉语义，也如实呈现 loading、empty、error、ready 和 success。

## Problem

静态测试或合成 `trigger.click()` 不能证明真实控件可发现、页面在宽窄屏可读，或 live 载荷与视觉基线一致。历史截图也会在源码、fixture 或消费面变化后陈旧。

## Expected outcome

U2/U3 当前候选为 52 个蓝图视图/状态案例在两个 campaign 下完成浏览器矩阵，且无页面错误或 `undefined`、`NaN`、对象字符串泄漏；六个 1240 至 1920 的桌面宽度均满足声明的成对列自然高度差和比例阈值；五种账本篡改分别产生声明结果，包括完全重写链的 external-head 拒绝。授权人另行完成 H-01 视觉理解闭环。

## Non-goals

不验收 U4 选题投影、U5 运营域或 A7 发布，不把视觉通过提升为 API、持久化、生产、设备、外部身份、研究结论或公开授权证明。

## Normal path

```gherkin
Given U1 基线已批准且 U2/U3 候选绑定同一当前消费面摘要
When 机器门禁完成全矩阵渲染与真实交互证据并由授权人执行 H-01
Then 平面③、平面②和管理端的结构、状态与视觉表达可理解且无阻塞偏差
And A6 只对 PI-R6 的声明范围作出结论
```

## Exception paths

- 任一组合缺运行身份、页面错误、未定义文案、溢出、遮挡、对比度失败或摘要漂移时整项保持非 PASS。
- DOM、样式、contrast 或 interaction 证据缺失，或像素 mask 超出动态字形范围时不得用截图补判。
- H-01 未批准、未执行、结论非 PASS 或绑定哈希陈旧时 A6 不得接受；机器绿灯不能替代人工判断。

## Invariants

- 每个 case、campaign 和 viewport 证据独立可定位，不复用另一组合的身份或截图。
- `consumer_surface_digest` 变化使受影响的机器、视觉和人工证据失效。
- A6 不改变后端、研究工作区、人工清单或视觉选择，只选择并判断不可变证据。

## Data impact

仅在 A6 fragment 的 acceptance 树与项目级人工 run 中创建不可变证据和结论；不写业务状态。每次重跑使用新 run ID，不覆盖历史 PASS/FAIL/PARTIAL/BLOCKED。

## Permissions

验收负责人拥有机器证据综合判断权；研究负责人或被明确授权的产品/视觉验收人执行 H-01。实现人员不得修改已锁定测试、基线或人工结果以取得通过。

## Performance and reliability

浏览器矩阵、组合总数和布局阈值由获批 U1/视觉合同冻结；运行必须零页面错误且零跳过。中断或缺组合时可用新 run 恢复，但不得把两个来源身份混为一个结果。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | SRC-PI-R6-A6-01 | visual-fidelity | 浏览器验收矩阵为两个 campaign 分别渲染全部 52 个蓝图视图/状态案例，且没有页面错误或 `undefined`、`NaN`、对象字符串泄漏 | Visual fidelity | Automatic | Yes |
| AC-02 | behavior | SRC-PI-R6-A6-02 | visual-fidelity | 在 1240 至 1920 的六个声明桌面宽度上，每组成对列都满足蓝图声明的自然高度差与比例阈值 | Visual fidelity | Automatic | Yes |
| AC-03 | behavior | SRC-PI-R6-A6-03 | machine/e2e | 五种账本篡改模式分别产生蓝图声明的不同校验结果，其中完全重写链必须因 external head 不匹配而被拒绝 | Machine E2E | Automatic | Yes |

## Human acceptance

详细步骤和签署结果只保存在项目级 workspace；当前清单是未批准、未执行草稿，不能计作 A6 通过。

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 从受支持入口浏览 32 个唯一视图并与冻结基线并排判断结构、状态、可读性和视觉语义 | acceptance/human/2026-W36/2026-09-02-VIS-A6-console-rendering/checklist.md#h-01 | 研究负责人或被明确授权的产品/视觉验收人 | Yes |

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Test baseline 为 PLANNED；批准并锁定可执行接口后登记 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 52 案例乘两个 campaign 的页面错误与值泄漏视觉矩阵 | 计划锁定的 A6 visual-fidelity run | Automatic | Yes |
| AC-02 | 六桌面宽度的成对列自然高度差与比例检查 | 计划锁定的 A6 visual-fidelity run | Automatic | Yes |
| AC-03 | 五种账本篡改结果及 external-head 重写链拒绝浏览器测试 | 计划锁定的 A6 machine/e2e run | Automatic | Yes |
| H-01 | 真实入口下的跨视图视觉理解闭环 | acceptance/human/2026-W36/2026-09-02-VIS-A6-console-rendering/checklist.md#h-01 | Human | Yes |

## Exploratory testing

在支持矩阵外探测长中文、缩放、系统深浅色切换、慢字体加载和极端空态；探索问题独立记录，不得覆盖矩阵内阻断失败。

## Production monitoring and rollback

不适用。A6 是本地候选的视觉与产品验收，不证明生产或设备；失败时保持 U2/U3 非接受态并创建新的修复候选与证据 run。

## Risks and open decisions

人工清单与 binding 尚为 DRAFT，`consumer_surface_digest` 尚未形成；严格 UI change 声明已经绑定，但 A6 当前仍不可执行为正式 PASS，也不得解锁 U4/U5。
