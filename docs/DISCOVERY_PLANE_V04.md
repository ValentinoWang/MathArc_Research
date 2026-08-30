# v0.4 方向修订：发现平面（D 轨）、障碍反转（X 轨）、优化合同（O 轨）

> **状态（2026-08-28 追记）：已推迟，不在当前路线图上。** 本文档写于
> `DEV_PATH_V03.md` 被重写为「v4 SSOT」之前；v4 SSOT 已把「v0.4」定义为
> 另一件事（R6/R7 评审 HTTP、S/G 担保分级、V1→V2 验证器工厂、V4 旗舰、
> N3 正式实验），与本文档的编号直接冲突。仓库所有者已就此拍板：先按
> v4 SSOT 的既定顺序完成 v0.3-review（R0–R5），本文档的 D/X/O 三轨
> 分析暂缓，留作未来并入路线图前的候选材料，**不要**当作当前正在开发
> 的计划。下方正文未改动，按原样保留供参考。

> 本文档处理第三份外部评审——一份以「零点比例突破的发现过程」为参照系、
> 对 MathArc 逐项对照的能力评估。按仓库纪律，**每条涉及本代码库的事实
> 性断言都先经代码核实，再决定采纳**；领域专项内容（黎曼 zeta、Weil
> 型、解析数论评价器、zeta 复现基准的具体实例）按所有者指示**本轮一律
> 不做**，只采纳可泛化的架构与机制。
>
> 基线：`docs/AUDIT_MAIN_2026-08-27.md`（main 与 feat 分支逐字节一致，
> 本地 `make ci` 全绿，见 `docs/baselines/2026-08-27-local-ci.md`）。

---

## 0. 结论：能不能用来改 MathArc？

**能，而且大部分该用。** 但要分四类处理，不能整包照收：

| 类别 | 内容 | 处理 |
|---|---|---|
| ① 已是我们计划的具体化 | 探索沙箱（≈V1）、控制世界（≈kill test 扩展）、文献自主检索（=W2-6）、Lean 闭环（=W2-3）、增益信号补全（=N0.5） | 并入既有里程碑，部分提前 |
| ② 真正的新增，采纳 | **发现平面作为架构层**、**障碍反转算子目录**、**OptimizationContract + 区间算术**、控制世界升为合同一等对象 | 本文档 D/X/O 轨 |
| ③ 修正后采纳 | 动态子智能体（不解禁 `Task`，走治理通道）、探索沙箱边界（如实声明哪些是策略信任、哪些是强制隔离） | 见 §2、§3 |
| ④ 不采纳或已过时 | 直接给 worker 开 Bash/网络而不加治理通道；「ci-full 待执行」的判断（已有带日期的全绿基线） | 见 §7 |

一句话：**评审识别的缺口是真的——MathArc 目前只有验证平面，没有发现
平面；但补法必须保持 fail-closed 不动摇：探索能力加在晋升门之前，而
不是把晋升门放松。** 这一点评审自己的方案（隔离发现平面）也是对的，
我们采纳并且给出更严格的对象级设计。

### 0.1 评审事实性断言的核实记录

| 评审断言 | 核实 | 结果 |
|---|---|---|
| 自治 worker 被禁用 Bash/Read/Write/Edit/Glob/Grep/WebFetch/WebSearch/Task | `claude_code_runtime.py` `_DEFAULT_DISALLOWED_TOOLS` | ✅ 属实 |
| Campaign 白名单工具只有多项式/归纳/SMT 四个模板 | `exact_tools.py` 默认注册表 + `smt_tools.py` | ✅ 属实 |
| 停滞判断只看 `weighted_proof_closure` | `campaign.py`（`max_rounds_without_gain`，闭合度单信号） | ✅ 属实（N0.5 已排期修） |
| 每提案最多新增 5 claim/5 route，无动态派生 worker 通道 | `orchestrator.py` 上限常量；`prompting.py` schema 无 spawn 字段 | ✅ 属实 |
| 有 Lean 工具但未进默认自治闭环 | `framework_adapters.py::LeanCliFormalizer` 存在；`exact_tools.py`/`campaign.py` 无 Lean 注册 | ✅ 属实 |
| `SourceRegistry` 是登记治理、非自主检索 | `source_registry.py` | ✅ 属实 |
| 无 baseline/candidate/delta/objective 一等数据结构 | `schema.py` 全文；`campaign.py` 增益统计 | ✅ 属实 |
| 「当前权威 ci-full 与 clean replay 被记录为待执行」 | `docs/baselines/2026-08-27-local-ci.md` | ❌ 过时——已有带日期的全绿基线 |

（评审对外部论文与发现过程的叙述本文不作核实，也不依赖：以下所有
采纳决定只以「该机制对 MathArc 是否普遍成立」为准。）

---

## 1. 采纳的总原则：两个平面，一个门

```text
┌────────────────────────────────────────────┐
│ 发现平面（D 轨，新增）                       │
│ explorer 会话：可写代码、跑数值实验、          │
│ 生成猜想/候选不等式/疑似反例                  │
│ 产物资格上限：NUMERICAL_EXPERIMENT/HEURISTIC │
│ ——按现有 proof_capable 定义天然不具证明资格   │
└──────────────────┬─────────────────────────┘
                   │ 唯一入口：受治理创建通道
                   │ （猜想 → PROPOSED claim，与 new_claims 同一治理）
┌──────────────────▼─────────────────────────┐
│ 验证平面（现有全部机制，不动）                │
│ exact_tools / SMT / kill test / 独立组 /     │
│ trace.promote_claim 唯一晋升权               │
└────────────────────────────────────────────┘
```

关键设计事实：**发现平面不需要新的信任机制，因为现有晋升门已经把它
挡住了。** `EvidenceKind` 阶梯里 `NUMERICAL_EXPERIMENT` 与 `HEURISTIC`
本来就不具证明资格（`schema.py` 的 proof_capable 集合），探索产物只要
被钉死在这两档，无论 explorer 做了什么，都不可能推动任何 claim 晋升。
安全边界是晋升门，不是沙箱——沙箱只负责预算与整洁，这一点必须在文档
和代码注释里写明，不许把「沙箱隔离」宣称成安全保证（v1 的进程级隔离
是策略信任，见 D1 的如实声明条款）。

---

## 2. D 轨：发现平面

| # | 里程碑 | 内容与触碰文件 | 依赖 | 工作量 | 验收标准（必须含否定测试） |
|---|---|---|---|---|---|
| D0 | 猜想与探索记录 schema | `schema.py` 新对象：`ConjectureRecord`（`conjecture_id / statement / origin(exploration_id) / support_artifacts / status: OPEN\|PROMOTED_TO_CLAIM\|NUMERICALLY_REFUTED\|WITHDRAWN / created_by`）与 `ExplorationRecord`（`exploration_id / brief / scripts[](内容寻址) / outputs[](内容寻址) / commands_digest / wall_seconds / cost / findings[]`）。两者都**不是** EvidenceRecord，不进证据通道；序列化严格 round-trip，未知字段拒收 | 无 | 2–3 天 | 未知 status 拒收；ConjectureRecord 无法被附着为任何 claim 的 evidence（类型层面就不可能，测试固化这一点） |
| D1 | explorer 运行时档 | `claude_code_runtime.py` 增第二个配置档 `ClaudeCodeConfig.explorer()`：**允许** Bash/Read/Write/Glob/Grep，但 `--add-dir` 只挂一个一次性探索工作区（不挂仓库），网络与 `Task`/`WebFetch` 仍禁。会话产物（脚本、输出、stdout）全部内容寻址进 `ArtifactStore`，会话摘要封入 `EventLedger`。**如实声明条款**：文档与 docstring 必须写明 v1 的隔离是「工作目录约定 + 工具禁用策略」，不是强制沙箱（explorer 有 Bash 就技术上可越出约定）；强制隔离（容器/netns）列为后续加固项。正因如此，§1 的「晋升门才是安全边界」必须先于 D1 成立 | D0；**审计项 5.2（默认预算上限）必须先修**——explorer 每轮真实花钱，无默认上限的 CLI 不许接 explorer | 4–5 天 | explorer 会话结束后工作区外无文件改动（约定检查测试）；其全部输出在 ArtifactStore 可寻址；一个试图直接写 trace 文件的脚本不影响任何 claim 状态（trace 不在其可写路径） |
| D2 | campaign 接线：探索请求与猜想升格 | `prompting.py` 的 proposal schema 增可选 `exploration_requests[]`（brief + 预算上限申请）；`campaign.py` 派发 explorer 会话、解析 `EXPLORATION_OUTPUT_SCHEMA`（findings: conjectures / numeric_tables / candidate_inequalities / possible_counterexamples），落 D0 对象。猜想升格走**现有** `_create_proposed_structure` 同一通道：ConjectureRecord → PROPOSED claim + 附 NUMERICAL_EXPERIMENT 证据（钉档），每轮升格数量入既有上限 | D0、D1 | 3 天 | 升格出的 claim 恒为 PROPOSED；只带数值支持的猜想 claim 尝试晋升被现有门拒绝（端到端否定测试）；exploration 花费出现在 BudgetLedger |
| D3 | 疑似反例的走向 | explorer 报告的 `possible_counterexamples` **永不直接触发** `record_failure`：先入队精确核验（exact_tools/SMT 独立复算），核验通过才走 R5 通道③（ClaimCounterexample）/路线级走通道②。未核验的疑似反例只作为下一轮 planner 的攻击提示 | D2；R5 通道对象（v0.3-core 已排） | 1–2 天 | 一个错误的疑似反例（精确复算不成立）不改变任何 claim/route 状态；一个真反例经核验后正确级联 |
| D4 | 受治理的动态子任务 | **不解禁 `Task` 工具**（那会绕过预算与审计）。proposal schema 增 `spawn_requests[]`：worker 申请 N 个子探索/子提案（brief + 角色 + 预算申请），编排器统一裁决——每轮总数上限、递归深度上限 1、预算从本轮切分、逐项批/拒记入 `spawn_log`（与 `creation_log` 同构）。这把评审说的「60 个子智能体」变成可审计的扇出 | D2 | 2–3 天 | 超上限的 spawn 申请被逐项拒绝且不影响整批；spawn 出的会话花费全部入账；深度 2 的申请被拒 |

**D 轨合计**：约 2.5 周。红线：发现平面产物的证据档**永远**钉在
`NUMERICAL_EXPERIMENT`/`HEURISTIC`；explorer 会话对 trace/ledger 无
写路径；升格只走受治理创建通道。三条各配否定测试，长期保留。

---

## 3. X 轨：障碍反转算子目录（从「记录失败」到「诱导转化」）

评审最有价值的观察：我们能记住失败、避免重撞，但「把障碍重新解释为
资源」这类关键跃迁目前只能靠模型偶然提出，harness 不会主动诱导。修法
是把「研究变换」做成**数据**，不是代码：

| # | 里程碑 | 内容 | 依赖 | 工作量 | 验收标准 |
|---|---|---|---|---|---|
| X0 | 变换目录 schema + 首批条目 | 新 `transformation_catalog.py`（或 YAML + 加载器）：每条 `{transformation_id, applicable_failure_classes[], directive(给 planner 的结构化指令模板), structural_requirements, provenance(来源实例)}`。**目录准入纪律：每个算子必须援引 ≥1 个真实历史实例**（文献或本仓库 run），不许凭空发明五十个算子。首批从通用失败类起步，如：`POSITIVITY_FAILURE → {保留不定结构并追踪惯性 / 对偶化 / 商掉障碍 / 标量陈述放宽为矩阵陈述 / 缺陷转不变量}`、`INDUCTION_STEP_FAILURE → {加强归纳假设 / 换归纳量}`、`COMPACTNESS_FAILURE → {有限截断 + 尾项控制}` | 无（FailureRecord 的 diagnosis 分类已存在） | 2–3 天 | 未知 failure_class 的条目拒收；无 provenance 的条目拒收（准入纪律进 schema） |
| X1 | planner 接线：转化派生路线 | 路线以某 failure_class 失败后，下一轮 plan 的强制项中包含按目录实例化的**转化指令**；由此开出的新路线携带 `derived_from_failure + transformation_id`，且 `mechanism_signature` 必须与死亡路线不同（防换皮）。转化派生与否、被哪条指令诱导，全部入事件链——这让「障碍反转」从模型运气变成可统计的 harness 动作 | X0；episode/failure memory（已有） | 1–2 天 | 同 mechanism_signature 的「转化」路线被拒；事件链可查某条新路线由哪个 transformation 诱导；无适用算子时 plan 不含伪造指令 |

**X 轨合计**：约 1 周。诚实边界：目录**提高提出关键转化的概率**，不
保证提出——这句话写进模块 docstring，营销表述不得超过它。

---

## 4. F 轨扩展：控制世界（proves-too-much 检测）

并入 v0.3-core 的 F0（KillTestSpec schema），不另开轨：

- `TheoremContract` 增可选 `control_worlds: [ControlWorldSpec]`——每条
  `{world_id, description, expected_verdict(该世界中目标命题已知为假/
  已知临界), evaluator_ref}`。领域无关的概念：**一个论证若在已知反例
  世界里也「成立」，它一定偷带了错误假设**。
- F0 的 kill-test kind 枚举增 `control_world`；F1 编译执行时对带控制
  世界的合同自动生成对应 kill test。
- 语义：路线在 expected_verdict=FALSE 的控制世界里「通过」⇒ 自动
  RouteFailure（失败类 `PROVES_TOO_MUCH`），走 R5 通道②，claim 不动。
- 非专项实例先行：归纳模板配一个故意为假的变体命题世界；Frankl q=6
  配一个违反前提的集合族世界。zeta 模型动物园属专项，本轮不做。
- 工作量：并入 F0/F1 各 +1 天。验收（否定测试）：一个刻意过度一般的
  论证在目标世界通过、在控制世界也「通过」→ 路线被 BLOCKED 且失败类
  正确；控制世界结果永不成为支持证据。

---

## 5. O 轨：OptimizationContract——把「提高一个常数」变成一等任务

评审正确指出：现有对象（Claim/Route/Evidence/Failure）适合真假命题，
不适合「把纪录从 B₀ 推到 B(θ)」这类任务。修法：

| # | 里程碑 | 内容 | 依赖 | 工作量 | 验收标准 |
|---|---|---|---|---|---|
| O0 | OptimizationContract schema | `schema.py` 新对象：`{quantity_id, direction(max/min), baseline{value, evidence_ref}, candidates[]{value, parameter_digest, mechanism_signature, assurance(沿用担保档), error_certificate_ref}, method_ceiling(可选，须带出处), acceptance_predicates[]}`。**数值纪律：所有 value 一律精确有理数或区间对象，禁止裸浮点**（与 exact_tools 的有理数纪律同源）。「新纪录」本身建模为普通 claim（陈述=「quantity ≥ B(θ)」），**复用现有晋升门**，合同只做簿记与调度目标——不为纪录任务另开晋升通道 | 无 | 2 天 | 浮点 value 拒收；candidate 的 assurance 不得高于其 error_certificate 支持的档（否定测试） |
| O1 | 区间算术评价器 | `exact_tools.py` 新模板族：纯 Python 有理区间算术（加乘除/幂/单调函数外推的保守界），产出可冷重放的 `EXACT_COMPUTATION` 证据；这是任何「候选常数被认证」的前置工具。与 SMT 同样的白名单模板 + replay 命令纪律 | O0 | 4–5 天 | 区间不包含真值的构造用例被检出（自检测试）；replay 逐字节一致；worker 无法递裸浮点进来 |
| O2 | 增益信号接线 | N0.5（已排期）的增益向量增加 `record_improved: {quantity_id, delta}`；campaign 停滞判断把「认证纪录提高」计为增益 | O0、N0.5 | 1 天 | 一轮只提高了认证下界、未晋升新 claim 的 run 不被判为无增益 |
| O3 | 纪录感知调度 | 「围绕最优候选分配预算、对临界候选加精度」的调度策略 | O0–O2、D 轨 | **推迟**：先让 O0–O2 在一个真实任务上跑过，再谈调度启发式，避免过早抽象（与 V0 同一纪律） | — |

**O 轨合计（O0–O2）**：约 1.5 周。

---

## 6. 基准方法论：三级重发现模式（去专项化采纳）

评审的 Level A/B/C 模式本身可泛化，采纳为**基准方法论**并先在已有
非专项域实例化（zeta 实例按指示不做）：

- **Level A（重放）**：给全部材料，测验证平面——能否拆 DAG、核适用
  条件、独立证据闭合。我们已在 Frankl q=6 证书重放上有雏形。
- **Level B（藏引理）**：抽掉一个关键引理，从其失败类出发测 X 轨——
  harness 能否诱导出正确的转化方向。首个实例可用归纳/组合域内已知
  结果构造。
- **Level C（受控重发现）**：冻结材料 + 限预算，测 D+X+O 全链。**这
  是唯一有资格支持「具备发现能力」宣称的证据档**；A/B 通过不得对外
  表述为发现能力（表述纪律与 N2.5「未过资格门不得对外引用」同源）。
- 落地：`benchmarks/` 增 `rediscovery/` 说明与首个 Level A/B 实例
  （2–3 天，排在 D/X 轨落地之后才有意义）。

---

## 7. 不采纳与纠正的点

1. **不给 worker 直接解禁 `Task`/网络**。评审把「动态子智能体」描述为
   解除工具禁用；我们改为 D4 的治理通道（申请-裁决-入账）。理由：预算
   与审计闭环是本仓库的差异化本体，不能为带宽牺牲。
2. **文献自主检索（W2-6）与 Lean 闭环（W2-3）不提前**。评审正确指出
   缺口，但两者已在计划内且各有前置（受控抓取代理 + 出处钉定；真实
   Lean 管线）。把 `LeanCliFormalizer` 直接注册进默认工具表是假供给
   ——没有管线支撑的工具按钮比没有按钮更糟。维持原排期。
3. **「ci-full/重放待执行」的判断已过时**：见
   `docs/baselines/2026-08-27-local-ci.md`。
4. **领域专项整体不做**（所有者指示）：zeta/Weil 专项评价器、控制世界
   动物园的解析数论实例、Level C 的 zeta 实例，均留待专项立项。

---

## 8. 排期修订（对 DEV_PATH_V03 §6 的插片）

```text
Gate 0（已完成 G0-a/b/c 首份基线）
→ v0.3-core（≈3 周，内容不变；F0/F1 并入控制世界，+2 天）
→ v0.35-discovery（≈3 周，新增）：
    前置：审计项 5.2 默认预算上限（半天）
    D0 → D1 → D2 → D3 → D4；X0 → X1；O0 → O1 → O2
    完成标准：一次真实 campaign 中，explorer 产出的猜想经受治理
    通道成为 PROPOSED claim，仅数值支持时晋升被拒（端到端）；
    一条路线死于某失败类后，下一轮出现由目录诱导、机制不同的
    转化派生路线；一个候选常数拿到区间证书并作为普通 claim 过门
→ v0.3-review（≈3 周，不变；评审人招募在 v0.35 期间并行启动）
→ v0.3-learning → v0.4（不变；rediscovery 基准 Level A/B 实例入 v0.4）
```

出口条件不变：本地 `make ci` 全绿；每个新门带否定测试；落地状态如实
更新。三条 D 轨红线（§2 末）为永久红线，进 IMPROVEMENT_PLAN §5 设计
红线序列。
