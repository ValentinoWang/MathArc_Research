# main 分支审计：MathArc_Research 现状、与计划文档的符合性、剩余改进空间

日期：2026-08-27。
审计对象：`main` 分支上的 `.`（提交
`59e1964`）与开发分支 `feat/matharc-research-v0.2` 的关系。
方法：分支拓扑核对、目录逐字节 diff、对计划文档宣称逐条 grep/读码
复核、本地 `make ci` 全量复跑。所有结论都给出可复现的验证命令。

---

## 1. 一句话结论

**这次如何**：main 分支状态健康。`main` 就是 `feat/matharc-research-v0.2`
的全量合并再加一个纯文档的治理提交，MathArc 目录在两个分支上逐字节
一致，没有分叉、没有丢失提交；本地 `make ci` 在项目 venv 下全绿。

**是否按原文档开发**：已落地的部分严格对应
`IMPROVEMENT_PLAN_V03.md` 的 W1 闭环（campaign / Claude Code CLI
worker / 受治理分解 / 预算账本）加 W2-7 SMT 适配器，且文档「落地状态」
节的每条宣称（包括「仍未落地」清单）都经本次独立复核属实——文档没有
夸大。`DEV_PATH_V03.md` 排期中的 v0.3-core 及之后各里程碑尚未开工，
这符合排期本身（计划文档刚落盘），不构成偏离。

**是否还有改进空间**：有。本次审计新抓出 6 个计划外问题（其中 1 个
当场修复），外加计划内的结构性下一步（v0.3-core 垂直切片）。见 §5。

---

## 2. main 分支现状：三个可复现的事实

### 2.1 拓扑：main = feat 分支 + 恰好一个治理提交

```
$ git log --oneline origin/feat/matharc-research-v0.2..origin/main
59e1964 docs(governance): define harness layering and placement rules
```

该提交由仓库所有者本人提交，只改两个文件（`AGENTS.md` +2 行、新增
`HARNESS-LAYERING.md` 92 行），不触碰 MathArc 目录。开发分支的全部
工作（v0.2 运行时、campaign、SMT、三份 V03 文档、评审台原型）已完整
进入 main。

### 2.2 目录一致性：MathArc 树逐字节相同

```
$ git diff origin/feat/matharc-research-v0.2 origin/main -- .
（空输出）
```

main 上看到的 MathArc_Research 与开发分支上的完全一致——不存在
「main 上是旧版」或「合并时被改动」的情况。

### 2.3 本地 CI：全绿（在项目 venv 下）

按既定纪律（DEV_PATH Gate 0 / G0-b，GitHub Actions 额度受限期间
**本地 `make ci` 是唯一权威门**），本次审计全量复跑：

```
$ cd . && PATH="$PWD/.venv/bin:$PATH" make ci
Ran 155 tests ... OK (skipped=2)      # 有 z3 的 venv 下仅跳过 2 个
mypy --strict：0 错误 / 40 个源文件
v0.1 / v0.2 验收脚本、Frankl 冷重放（逐字节比对）：通过
exit 0
```

完整结果与环境指纹已固化为首份 G0-c 基线工件：
`docs/baselines/2026-08-27-local-ci.md`（随本提交入库）。

**复跑过程当场抓到一个环境耦合缺陷**（详见 §5.5）：用未安装 matharc
的系统解释器跑同一套 CI 时，`examples/serve_workspace_v02.py` 因
import 失败无法启动，连带一个测试假失败。已在本提交修复（源码检出
下自动把项目根加入模块搜索路径）。这个插曲本身是 G0-b 纪律有效性的
一次实证：不真跑就不会发现。

---

## 3. 是否按原文档开发：逐项对照

### 3.1 对照 IMPROVEMENT_PLAN_V03 的「落地状态」节

该节宣称的每一项都做了独立复核（不信文档，只信代码和测试）：

| 文档宣称 | 复核方式 | 结果 |
|---|---|---|
| W1-2：Claude Code CLI 作为 worker 运行时（`claude_code_runtime.py` / `prompting.py` / `model_workers.py`，屏蔽全部可变更工具，schema 强制输出） | 读码 + `tests/test_v02_claude_code_runtime.py`、`test_v02_model_workers.py`、`tests/fake_claude_code.py` | ✅ 属实 |
| W1-1：多轮 campaign + 受治理分解（新 claim 恒 PROPOSED、依赖须存在、每提案上限 5、`creation_log` 审计） | 读 `campaign.py` / `orchestrator.py` + `test_v02_campaign.py`、`test_v02_governed_creation.py` | ✅ 属实 |
| W1-3：预算账本从真实时间戳/用量计量 | 读 `budget.py` + `test_v02_budget.py` | ✅ 属实，但见 §5.3 的接线缺口 |
| W2-7 最小子集：精确工具（多项式恒等式 / 归纳证书）+ SMT 适配器（UNKNOWN 硬阻断、sat 模型独立复核、unsat 如实降级自验证、反例不进证据通道） | 读 `exact_tools.py` / `smt_tools.py` + `test_v02_exact_tools.py`、`test_v02_smt_tools.py` | ✅ 属实 |
| 三个模板族的 replay 命令「真实执行验证过」 | replay 命令带 `shlex.quote` 转义；历史会话中确曾执行 | ✅ 属实 |
| 「仍未落地」清单（W1-4/W3-1 问题接收 schema、W2-1..6、W3 引擎栈、W4 数据飞轮、W5 盲区） | grep：`RouteEvaluationRecord` 0 处命中；`review.py` / `falsification.py` / `episode_distiller.py` 不存在 | ✅ 如实——没有把没做的说成做了 |

**结论：文档与代码互相如实。** 「宣称受证据门控」的红线在这份文档
自己身上成立。

### 3.2 对照 DEV_PATH_V03 的排期

| 阶段 | 计划内容 | 实际状态 |
|---|---|---|
| Gate 0 / G0-a | 两个物化 workflow 拆除自动触发 | ✅ 完成。main 上两个文件均只剩 `workflow_dispatch` 手动触发，注释写明原因 |
| Gate 0 / G0-b | 本地 `make ci` 为唯一权威门 | ✅ 生效中（本次审计即按此执行） |
| Gate 0 / G0-c | 版本化基线工件（CI 关键产出随里程碑入库） | ❌ 未做——目前「本地全绿」的历史只存在于对话记录里，仓库里没有带日期的基线文件。见 §5.4 |
| v0.3-core（F0→F0.5→F1→F2→F3、R5 三通道对象、V3 DRAT、N0.5、N2.5） | ≈3 周的第一个垂直切片 | 未开工（排期上的下一步，非偏离） |
| v0.3-review（R0–R5 CLI 全链）、v0.3-learning、v0.4 | 后续切片 | 未开工（同上） |

**结论：已做的严格按文档做了；未做的都是文档里排在后面的。** 目前
真实进度线停在「W1 闭环 + W2-7 两档评价器 + 全部计划/原型文档」，
与 `IMPROVEMENT_PLAN_V03.md` 落地状态节的自我描述一致。

---

## 4. main 上新增的治理层（HARNESS-LAYERING.md）与 MathArc 的关系

main 独有的那个提交定义了仓库三层复用结构（Core / Apps·Paper /
Projects）与晋升规则。它与 MathArc 计划文档存在真实的互动，值得
专门核对：

**一致的部分**：HARNESS-LAYERING §2「边界不清时先放更低层，等第二个
使用方出现再晋升；不要预先上提」与 DEV_PATH 的两处独立决策完全同构
——V0（通用分支定界抽取）明确推迟到第二个真实实例出现，风险 6 写明
「任何通用协议必须有 ≥2 个真实消费者才允许抽取」。W3-0（MathArc
Engine 抽取为可复用包）的推迟逻辑同理。两份文档是各自独立写的，
结论互相印证，说明这条治理直觉在仓库层面是稳定的。

**立即不合规的部分**：HARNESS-LAYERING §4 规定「每个 `Projects/<X>`
命名空间必须二选一：在 registry 注册 `project-<x>` profile，或在其
`PROJECT.md` 声明『仅档案，不分发』」。核查结果：

```
$ grep -c matharc registry.yaml          → 0（没有注册 profile）
$ grep -c 仅档案 ./PROJECT.md → 0（没有档案声明）
```

MathArc 两头都没占——**自这条规则生效起就处于不合规状态**。且注意
「仅档案」按 §3 的定义意味着「不再演进」，与 MathArc 正在活跃开发的
事实矛盾，所以正确的合规路径几乎必然是**注册 `project-matharc-research`
profile**，而不是档案声明。这是所有权层面的治理选择，建议由仓库
所有者拍板后一并落 registry 条目（见 §5.1）。

**一处结构性张力（不紧急，但要有意识）**：分层表格给项目层的定位是
「项目专属 skill、脚本与测试、导入快照」，而 MathArc 实际是一个完整
的产品代码库（`matharc/v02` 下 38 个模块、155 个测试、可安装的
Python 包）。当 BP 里「MathArc Engine 复用数学结构拆解」的第二个
使用方真的出现时，按晋升路径它不该原样复制进 Core/，而应走 W3-0
的独立包抽取——届时 HARNESS-LAYERING 的「泛化改写、项目层原件转
档案」条款与 W3-0 的执行方式需要对齐一次。现在不用动，但两份文档
都该知道对方的存在。

---

## 5. 改进空间

### 近期可执行（本次审计新发现，均为计划外）

**5.1 registry §4 合规缺口**（见 §4）。推荐动作：在 `registry.yaml`
注册 `project-matharc-research` profile（把 `.`
作为整体单元），并在 `PROJECT.md` 记一行接线说明。工作量小时级；
唯一需要所有者确认的是 profile 命名与是否随 core 分发。

**5.2 CLI 默认无预算上限**。`matharc/v02/cli.py` 的 `run` 子命令在
用户不给 `--wall-seconds-budget` / `--cost-usd-budget` 时令
`budget = None`——campaign 完全不设上限地循环调用真实 `claude` CLI。
对一个每轮都花钱、且停止条件之一是「无增益判断」的自治循环，默认值
应当保守：建议给出保守的默认墙钟上限（如 30 分钟）与默认轮数上限，
要求显式传 `--no-budget` 才解除。改动半天内，含否定测试（不带参数
的 run 必须在默认预算内停）。

**5.3 `reconcile_self_report` 实现了但没接线**。`budget.py` 里
「worker 自报用量 vs 实测偏差标记」的函数存在且有单测，但
`campaign.py` 从不调用它——「不信任自报」的设计只完成了一半，模型
虚报用量目前不会被任何运行时路径发现。接线是小活：campaign 在
`charge_model_usage` 处顺带 reconcile，偏差写入事件链。半天内。

**5.4 G0-c 基线工件落地（本提交已启动）**。DEV_PATH 要求「`make ci`
的关键产出随大里程碑入库为带日期的基线文件，替代远程 CI 缺位期间的
绿色历史」。此前一直未做；本提交随附首份基线
`docs/baselines/2026-08-27-local-ci.md`（测试计数、mypy 文件数、验收
清单、退出码、环境指纹）。之后每个大里程碑照此追加一份即可，G0-c
从「未做」转为「已建立惯例」。

**5.5 CI 对「恰好激活了 venv」的隐性依赖（已当场修复）**。
`examples/serve_workspace_v02.py` 原先只有在 matharc 已 pip 安装的
解释器下才能启动；测试 `test_cli_refuses_remote_binding_without_
explicit_override` 以子进程方式跑它，于是同一套 CI 在系统解释器下
假失败、在 venv 下通过——「绿」依赖了一个没有写进任何文档的环境
前提。本提交给该脚本加了源码检出回退（import 失败时把项目根插入
模块搜索路径），使 CI 结论与解释器选择解耦。遗留的可选加固：
Makefile 显式使用 `.venv/bin/python`，把环境前提写死而不是靠 PATH
约定。

**5.6 IMPROVEMENT_PLAN 落地状态节的数字漂移**。该节末尾「验证方式」
写的还是 SMT 落地前的旧数字（135 个单测），与同节上文的 155 不一致。
本提交顺手改正。属于「落地状态节如实更新」纪律的日常维护。

### 结构性（计划内的下一步，非新发现）

按 DEV_PATH §6 的垂直切片制，下一个应开工的是 **v0.3-core**（≈3 周）：

```
F0 KillTestSpec schema（2 天）
→ F0.5 共享 RouteEvaluationRecord（2–3 天，R/F/audit/campaign 四方共用的地基）
→ F1 否证编译执行 → F2 kill-test 硬阻断 → F3 反例级联（只杀正确层级）
+ R5 三通道对象层、V3 SAT+DRAT、N0.5 增益信号、N2.5 配对回归接线
```

完成标准已在 DEV_PATH 写死：两个真实案例（一个假命题被自动精确否证
且只杀路线不动 claim；一个真子命题拿到可冷重放证据并通过晋升门或给
出指名到义务的精确 blocker）。在 v0.3-core 之前，上面 5.1–5.4 都是
一天内量级的清账，建议先清后开工。

---

## 6. 建议执行顺序

1. ~~G0-c 首份基线工件~~ —— **已随本提交完成**
   （`docs/baselines/2026-08-27-local-ci.md`），以后每个里程碑照此办理。
2. **registry §4 合规**（小时级，需所有者确认 profile 方案）。
3. **budget 默认上限 + reconcile 接线**（各半天，含否定测试）。
4. **v0.3-core 开工**，从 F0 起按垂直切片推进。

---

### 附：本次审计的验证清单

- `git log --oneline origin/feat/matharc-research-v0.2..origin/main`（拓扑）
- `git diff origin/feat/matharc-research-v0.2 origin/main -- .`（逐字节一致）
- `git show 59e1964 --stat`（治理提交内容）
- `.github/workflows/matharc-v02-{bootstrap,materialize}.yml` 全文读取（G0-a 核实）
- `grep -rn RouteEvaluationRecord`（0 命中）；`review.py` / `falsification.py` / `episode_distiller.py` 存在性检查（均不存在）
- `grep -n reconcile_self_report matharc/v02/*.py`（仅定义处 1 命中，无调用点）
- `matharc/v02/cli.py` `run` 分支读码（budget 默认 None）
- `grep -c matharc registry.yaml` 与 `PROJECT.md` 档案声明检查（均 0）
- `PATH="$PWD/.venv/bin:$PATH" make ci` 全量复跑（155 测试通过、跳过 2 / mypy strict 40 文件 0 错误 / 双版本验收 / Frankl 冷重放逐字节一致，exit 0）——固化于 `docs/baselines/2026-08-27-local-ci.md`
