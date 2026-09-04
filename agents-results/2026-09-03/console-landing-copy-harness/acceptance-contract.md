# Acceptance Contract: FEAT-20260903-02

- Task ID: FEAT-20260903-02
- Contract version: 1
- Contract status: DRAFT
- Test baseline: PLANNED
- Acceptance owner: 项目负责人
- Approval evidence: 本轮仅建立草稿，尚未获得人类批准
- Request source: 2026-09-03 user request：首页视觉与滚动体验、全站文案检查、并把原因沉淀回 Harness；同日复核后追加一轮调色与风格改版（向仪器台方向加强科技感）
- SSOT node: none
- SSOT path: none
- Readiness mode: FORMAL
- Decision refs: none
- Assumption IDs: none
- Invalidation keys: console.landing.visual; console.copy.lexicon; console.visual.token-table
- AC budget: 6
- Baseline identity: main@530de20757520cd340c18f5da8f728122537cf05 plus the uncommitted landing/copy candidate reviewed on 2026-09-03
- Product Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#九控制台视图合同plan-v3
- Role Context refs: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#911证据分层与视觉工作台边界
- Resolved Surface Contract refs: agents-results/2026-08-31/problem-intelligence-plane/.ssot/view-sources/00-main.md#913-视觉基线令牌组件类断点与字体
- Screen Contract ref: agents-results/2026-08-31/problem-intelligence-plane/ssot-development-paths.md#93唯一视图清单32个
- Visual Contract refs: docs/prototypes/problem-intel-console.html
- UI Change declaration: agents-results/2026-09-03/console-landing-copy-harness/ui-change.json
- Human acceptance workspace: acceptance/human/2026-W36/2026-09-03-FEAT-20260903-02

## User and scenario

数学研究者第一次打开公开首页，判断这个产品是什么、给谁用、能不能信；然后在控制台的任一视图、任一数据状态下读到的每一句话，都能知道它说的是哪个对象、什么事实、下一步是什么。

## Problem

首页视觉层级平、没有滚动设计，手机端导航标签竖排换行却被截图清单标为通过；全站文案在回退态与实时投影里泄露机器标识与实现词汇；演示原型与后端对同一枚举使用不同标签。既有门禁只断言文本存在与数字来源，不断言文本可读。

## Expected outcome

首页有唯一主焦点与证据对象，四节共用同一节奏，导航粘性并标记当前节，锚点落在导航之下，内容进入视口渐显，减少动效偏好下全部可见；全站文案通过词法门禁与意义审阅，演示与后端同名同义；这些要求以规则、检查项与守卫卡沉淀到 Harness。

## Claim boundary for the team-research section

首页「团队研究」一节列出四篇团队成员的 arXiv 预印本，并按项目负责人 2026-09-04 的决定，声明它们是**使用 MathArc 做出的成果**。该节仍**不主张**任何一篇已通过同行评审；四篇均为预印本，其可发布层级由分级披露决定。

**未解决的记录冲突（阻塞项）。**`docs/IMPROVEMENT_PLAN_V03.md` 的「真实数学产出」一行目前记着：arXiv:2607.28557 是人加对话流程、**未入引擎**，引擎唯一端到端运行是玩具级恒等式，诊断为「引擎与真实数学分离」；`docs/V03_IMPLEMENTATION_STATUS.md` 与 `V03_REVIEW_TRACEABILITY.md` 记着回灌该论文的 R7 dogfood **尚未开始**；另外三篇在仓库中没有任何产出记录。页面的产出声明与这三份文档直接矛盾。

本合同不裁决哪一方为真——产出事实由项目负责人掌握，不由本次前端任务判定。但该矛盾必须在人工验收签署前由负责人以下列方式之一关闭：更新上述文档以反映真实产出路径并补上可核验的产出记录，或收回页面的产出声明。在此之前，AC-06 不得判为通过。

## Non-goals

不改变 U1 静态视觉合同的**令牌名称集合、组件类清单与断点**（令牌取值按修订 6 改版并已重钉摘要）、不重开 §9.14 动作清单修订、不改变任何视图的接线状态、不把团队论文回灌为可审计 trace（R7 dogfood 仍未开始）、不核验论文的数学内容、不做生产部署或人工签署。

## Normal path

```gherkin
Given 一名研究者在 1440 宽度打开公开首页
When 页面加载并逐节滚动
Then Hero 标题、证据卡与两条行动路径在首屏可见
And 点击任一导航项后目标节落在粘性导航之下且该项被标记为当前
And 进入视口的内容全部完成渐显
```

## Exception paths

- 用户偏好减少动效：不挂任何渐显属性，内容始终可见，锚点仍然可用。
- 390 宽度：桌面导航项隐藏，标题、按钮与品牌均单行，无横向溢出。
- 脚本失效：渐显属性不会被挂上，页面以完整可见的静态形态呈现。
- 词法门禁失败：输出文件、行号、规则、原因与修复路径；词库是唯一的例外入口。

## Invariants

- 落地页与调色板改版均不新增设计令牌名、类名或 `@media` 规则；`check_console_visual_baseline.py` 保持通过。
- 令牌取值改版必须同步重钉 `token_table_sha256`、改写合同 §9.13.1 的令牌表与错误规则判别值，并更新红夹具的强调色字面量；三者缺一即视为绕过基线。
- 强调色与证据色上的文字一律取随主题翻转的令牌，不得写死 `#fff` 或深色字面量。
- 不新增 `data-act` 动作值。
- 演示数据的三行状态与控制台演示常量一致，不编造数字。
- 截图清单记录 `font_mode` 与 `review_note`，PASS 只表示门禁断言成立。

## Data impact

无数据模型变更；后端评审保证等级的中文标签变更不影响枚举值与接口。

## Permissions

无变化；落地页与登录页仍是公开视图，访客模式仍不消耗积分、不写入工作区。

## Performance and reliability

渐显使用 IntersectionObserver 与 CSS 过渡，无持续动画；滚动监听为 passive。门禁在 fallback-local 字体模式下运行，其度量不外推为联网机器的度量。

## Acceptance criteria

| ID | Class | Source requirement refs | Lane | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | none | machine/static | 词法文案门禁在两份原型上无错误；静态视觉基线、蓝图投影与原型契约测试全部通过 | Static guards and unit tests | Automatic | Yes |
| AC-02 | behavior | none | machine/e2e | 首页滚动体验：粘性导航状态、四个锚点偏移、渐显完成、单行控件、减少动效可见性、深色主题；五张哈希绑定截图 | Browser E2E | Automatic | Yes |
| AC-03 | behavior | none | machine/e2e | 全部视图 × 进程 × 视口的渲染文本不含机器标识或占位符；准入流程文案更新后流程与截图仍通过 | Browser E2E | Automatic | Yes |
| AC-04 | behavior | none | human | 目标研究者能说出首页在讲什么、给谁用、下一步做什么，并且控制台任一句话都不需要实现知识即可理解 | Human product review | Human | Yes |
| AC-05 | behavior | none | machine/static | 调色板改版后令牌名称集合、三态结构、235 个组件类与 14 条 `@media` 全部未变；`token_table_sha256` 已重钉并与合同 §9.13.1 一致，红夹具仍能判红 | Static baseline guard and its red/green fixtures | Automatic | Yes |
| AC-06 | behavior | none | human | 团队研究一节的四条转述与 arXiv 原文相符；「使用 MathArc 做出的成果」这一声明与 `IMPROVEMENT_PLAN_V03.md`、`V03_IMPLEMENTATION_STATUS.md`、`V03_REVIEW_TRACEABILITY.md` 的记录冲突已由负责人关闭（更新文档或收回声明），且未暗示已通过同行评审 | Human product review | Human | Yes |

## Human acceptance

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 首页层级、滚动与全站文案的可理解性审阅 | acceptance/human/2026-W36/2026-09-03-FEAT-20260903-02/checklist.md#h-01 | 项目负责人或数学研究者代表 | Yes |

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| none | none | Contract remains DRAFT and the protected baseline remains PLANNED |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | scripts/check_ui_copy_quality.py; tests.test_ui_copy_quality; tests.test_console_visual_baseline; tests.test_console_prototype | agents-results/2026-09-03/console-landing-copy-harness/quality-gates/ui-copy-quality.json | Automatic | Yes |
| AC-02 | scripts/console_browser_gate.mjs testLandingScrollExperience | agents-results/2026-09-03/console-landing-copy-harness/evidence/landing-screenshot-manifest.json | Automatic | Yes |
| AC-03 | scripts/console_browser_gate.mjs scanCopyQuality + access workflow | agents-results/2026-09-03/console-landing-copy-harness/evidence/screenshot-manifest.json | Automatic | Yes |
| AC-04 | Human product review | acceptance/human/2026-W36/2026-09-03-FEAT-20260903-02/checklist.md#h-01 | Human | Yes |
| AC-05 | scripts/check_console_visual_baseline.py; tests.test_console_visual_baseline | agents-results/2026-09-03/console-landing-copy-harness/acceptance/machine/static/ | Automatic | Yes |
| AC-06 | Human product review | acceptance/human/2026-W36/2026-09-03-FEAT-20260903-02/checklist.md#h-01 | Human | Yes |

## Exploratory testing

人工补充探测：窄高视口、键盘导航跳节、系统深色下的证据卡对比度、慢网络下字体切换后的排版。探测结果只能新增缺陷，不能绕过阻塞项。

## Production monitoring and rollback

无生产发布。回滚即恢复 `docs/prototypes/problem-intel-console.html` 与两处后端标签的上一版本。

## Risks and open decisions

首页的产出声明与三份仓库文档的记录直接矛盾，未关闭前不得对外发布；人工尚未审阅首页层级、配色与文案；`fallback-local` 字体模式下的截图与联网机器不同；§9.14 动作清单漂移是本次之前已存在的缺口；冻结的 `review-console.html` 与 `review_bundle.py` 仍用旧调色板，两者的对齐需要单独的解冻决定。
