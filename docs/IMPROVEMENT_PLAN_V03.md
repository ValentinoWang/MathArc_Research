# MathArc v0.3 改进方案：从证明记账系统到研究级数学发现引擎

> 目标：让本仓库演进为「能够给出新的证明过程、面向研究级数学问题」的数学 Agent，
> 并使其核心能力（数学结构拆解）以 MathArc Engine 的形式被 MathArc Resolve
> （IC/EDA 候选评价等企业场景）复用。
>
> 依据：商业计划书（数弧智能 MathArc Labs, 2026-08）+ 对本仓库
> `feat/matharc-research-v0.2` 全量代码的多智能体盘点（4 个深读 + 3 个视角提案 +
> 1 轮对照代码的可行性批判，共核验 30 项提案，合并为下述工作项）。
> 基线 commit：`946eda7`（本地 CI 全绿：mypy --strict 33 文件、90 测试、
> v0.1/v0.2 验收、Frankl q=6 冷重放字节一致）。

---

## 落地状态（本次会话新增，随后续提交更新）

以下追踪 §3 工作项的实际代码落地情况，遵循本文档 §4 红线第 5 条的纪律：宣称
必须受证据门控。「完成」指有真实测试覆盖、mypy --strict 通过、且（对 W1-2）
经过真实 `claude` CLI 的端到端烟雾测试验证，而不只是脚手架。

**已落地（W1 Phase 1 核心闭环，commit 见 `git log` 中本节之后的提交）：**

- **W1-2 多模型 worker 桥**：不是接 Anthropic 原始 Messages API，而是把
  **Claude Code CLI 本身**作为 worker 运行时接入——架构上与 v0.1 的
  `codex_runtime.py` 完全对称（子进程 + 结构化 JSON 输出），新增
  `matharc/v02/claude_code_runtime.py`（`ClaudeCodeRunner`，`--print
  --output-format json --json-schema ... --strict-mcp-config
  --disallowedTools "Bash Read Write Edit ..."` 屏蔽全部可变更/联网工具）、
  `matharc/v02/prompting.py`（供应商无关的角色定义 + 9 条不可协商规则 + 有界
  trace 视图 + 强制输出 schema，从 v0.1 移植并扩展了 `new_claims`/
  `new_routes`）、`matharc/v02/model_workers.py`（`LLMProposalWorker`，实现
  与 `SubprocessProposalWorker` 相同的 `ProposalWorker` 协议，任何失败都
  转为 `ToolStatus.ERROR` 而不是抛异常）。**已用真实 `claude` CLI 端到端验证**：
  以 falsifier 角色对一个全新的奇数和定理 trace 跑一轮，模型真实攻击了
  「空和约定」这个隐藏假设、把 R-INDUCTION 的 kill test 执行完并记录、通过
  `new_claims` 通道提出了一个新的子 claim（`C-BASE-IMPL`，状态正确落在
  PROPOSED，从未触碰 PROVED）。
- **W1-1 自治多轮 Campaign + 受治理分解**：新增 `matharc/v02/campaign.py`
  （`ResearchCampaign`：plan → worker → 受治理创建 → 工具执行 → 晋升尝试 →
  停止条件，每轮持久化）；扩展 `matharc/v02/orchestrator.py` 的
  `accept_agent_proposal` 支持 `new_claims`/`new_routes`（新 claim 恒以
  PROPOSED 进入，依赖须已存在，每提案上限 5 个，单项失败不影响整批，
  `creation_log` 记录每次创建/拒绝的审计轨迹）。
- **W1-3 计量化预算账本（不含完整分层调度器）**：新增
  `matharc/v02/budget.py`（`BudgetLedger`：从真实 `ToolCallRecord` 时间戳与
  模型用量计量，而非单纯信任 worker 自报；`reconcile_self_report` 标记
  自报与实测的偏差）。**未做**：完整的 `EvaluatorTier`
  VALIDITY/FAST/PRECISE/ACCEPTANCE 分级调度与 Kendall τ 排序保真——那需要
  W3-2 的统一 Evaluator 接口先立起来，仍是后续工作。
- **首个真实评价器族（W2-7 的最小子集）**：新增 `matharc/v02/exact_tools.py`
  （白名单模板 `polynomial_identity`/`induction_certificate`，包装
  `matharc.polynomial` 的纯函数精确有理数运算，产出真正可冷重放的
  `ToolCallRecord`/`EvidenceRecord`）。集成测试证明了一个**真实的、非手写**
  闭环：给定一个全新的奇数和 trace，campaign 通过执行精确工具真实晋升了
  非关键的 C-BASE 到 PROVED；关键的 C-STEP 因为同一实现的两次调用共享同一
  independence_group（按设计不算独立证据）而被正确挡在 PROVED 之外——门在
  真实自动化回路面前按设计拒绝，而不是被绕过。

- **W2-7 SMT 适配器（继首批精确工具后的第二档评价器）**：新增
  `matharc/v02/smt_tools.py`——z3 上的两个白名单模板
  `smt_universal_no_counterexample`（有界全称：解 `bounds ∧ ¬φ`）与
  `smt_existential_witness`（存在见证），覆盖「有限模型检查 / 可判定片段 /
  有界验证」这档介于纯穷举与 Lean 之间的命题。信任语义刻意不对称、逐条
  落实本文档的红线：**UNKNOWN（含超时）硬阻断**（`ToolStatus.ERROR`、
  永不产生证据——SOLVER_UNKNOWN_PROMOTION 失败类的可执行化）；**sat 模型
  永不单信 z3**——由本模块内与 z3 无共享代码的纯 Python 整数求值器独立
  复核，两个检查器不一致时结果是 ERROR（NON_INDEPENDENT_CHECKER 事件）
  而非任何一方的结论；经独立复核的见证 → `EXACT_CERTIFICATE`
  （producer=z3、verifier=独立求值器，真独立组）；**unsat 判定如实降级**
  为 `EXACT_COMPUTATION` 且 producer==verifier（自验证告警会如实出现，
  limitations 明确记录「无独立可查证明对象，DRAT/proof-term 是后续
  工作」）——关键 claim 依旧无法只靠一次 z3 运行闭合；**反例刻意不进
  证据通道**（附着在 claim 上的证据在晋升门里算支持证据——把否证记录成
  证据是洗白通道；已核实的反模型进入工具输出摘要，接入 FailureRecord
  级联是 W2-2 反例引擎的活）。公式以受校验的 JSON AST 传入（节点/深度/
  变量数上限），worker 永远不能递给求解器一段裸语法字符串。z3 是可选
  依赖（`formal` extra）：模板无条件注册，缺 z3 时执行返回
  `REJECTED_TOOL_UNAVAILABLE` 而非崩溃（3.10 无 z3 环境全套 155 测试
  优雅跳过验证通过）。campaign 现在把可用模板清单注入 worker 的
  trace 视图。**三个模板族（多项式/归纳/SMT）的 replay 命令全部真实
  执行验证过**，SMT 重放输出摘要逐字节一致——顺带抓出并修复了原 replay
  命令的 shell 转义缺陷（JSON 载荷内双引号未转义，改用 `shlex.quote`）。

**修复的既有代码问题（本次实现过程中发现）**：`matharc/polynomial.py` 的
`Polynomial.__add__` 类型推断缺陷与 `identity_certificate` 缺失的返回类型
标注（因被 v0.2 的 `exact_tools.py` 引用而首次进入 `mypy --strict` 的检查
闭包时暴露）；三个精确工具模板 replay 命令的 shell 引号转义缺陷（仅在
真实执行重放时暴露——恰好证明了 W2-1「执行式重放门」的必要性：只检查
命令字符串存在的门抓不到这类问题）。

**仍未落地（按 §3 编号，供下一阶段延续）**：

- W1-4/W3-1 FormalProblemStatement/ProblemStructure schema（问题接收与
  跨场景不变结构落码）——本次的 campaign 只能推进*已存在*的 claim DAG，
  还不能从一段自然语言问题描述自动构造初始契约。
- W2-1/2/3/4/5/6 执行式重放门、可执行反例引擎（`KillTestSpec`）、真实 Lean
  管线、专家评审回路、跨模型对抗评审、文献适配器——均未动手。W2-7 已落地
  SMT 档（见上），SAT+DRAT、CAS（sympy）、证书化分支定界抽取与双实现
  验证器合成门仍开放。
- W3-0/2/3/4/5/6/7 引擎包抽取、统一 Evaluator 接口与注册表、候选/排序记录、
  客户验收闸门、方法包库、交付包导出器、EDA 演示——Resolve 侧栈整体未开始；
  `exact_tools.py` 是它未来 Evaluator 接口的一个具体先例，不是接口本身。
- W4-1/2/3/4 数据集自动蒸馏与导出、语料/基准战役、多 run 服务器、v0.1 退役——
  未开始。
- W5 五个盲区（误差有界数值证据、私域治理、外审发表管线、长时程鲁棒性、
  语句对应性作为可审计对象）——未开始。

验证方式：本地权威门 `make ci-full`（mypy --strict、单测、SMT 套件实际
执行、v0.1/v0.2 验收脚本、Frankl 冷重放）与一次真实 `claude` CLI 调用的
手动烟雾测试，而非仅凭代码审查或计划文字本身。**具体文件数/测试数/跳过数
不在本文手工维护**——`DEV_PATH_V03.md` §7「Count drift policy」明确禁止
此类数字被当作计划文字随时间漂移；权威数字见最新一份
`docs/baselines/*-local-ci.md`（G0-c，由 `make baseline` 生成，带 commit
与内容寻址摘要，而非手工誊写）。

---

## 0. 结论

v0.2 是一个**高质量的「证明记账与验收协议」，还不是一个「会做数学的 Agent」**。
它最有价值的资产是权限边界：模型输出永远只是提案（proposal-only），晋升
（PROVED）只能经由 `trace.promote_claim` 的三重门（证据规则 + 工作区审计 +
角色能力）。这一不变量是全部改进的地基，任何新能力都必须**接入这道门，
而不是绕过它**。

在此之上，距离目标有六个结构性缺口（§2），对应四条工作流（§3）：

1. **关闭发现回路**（W1）：v0.2 没有任何 LLM 集成，worker 提案无人消费，
   没有多轮自治循环，agent 无法创建 claim/route——「数学结构拆解」今天只能由
   人手写 Python 完成。
2. **让验证真正验证**（W2）：晋升门检查的是形式（有 replay 命令字符串、有
   64 位摘要）而非数学（从不执行重放；kill test 未执行仅是 WARNING；Lean
   从未对真实内核跑通）。
3. **抽取引擎边界并实例化 Resolve**（W3）：商业计划书的跨场景不变结构
   （搜索空间/约束/目标函数/评价器）、快评/精评预算调度、Kendall τ 排序保真、
   客户验收闸门、方法包库——在仓库中均为**零代码**。
4. **数据飞轮与评测**（W4）：episode/failure 记忆是手工种子数据，没有从完成
   的 run 自动蒸馏的进水口；配对基准从未测过真实 agent；BP 的 18 个月里程碑
   （真实运行→数据可复现→模型有增益）在仓库中没有对应资产。

另有五个所有提案最初都遗漏、由批判轮补充的盲区（§3.5），其中**语句对应性
（statement_correspondence）作为可审计对象**是当前体系中最大的「洗白通道」。

---

## 1. 商业计划书要求 ↔ 代码库现状映射

| BP 管线阶段 | 仓库现状 | 判定 |
|---|---|---|
| 01 问题结构化 | `TheoremContract`/`ClaimRecord` DAG 数据模型完整（schema.py），但全部字段为自由文本；无量词/对象/实例生成器的形式表示；agent 无法提交分解（orchestrator 丢弃未知 claim_id） | 有骨架，无自动化 |
| 02 候选搜索与筛选 | `ResearchRoute`（机制签名 + kill_test + 判别器）+ 机制重复拒绝，是好的原语；但无任何搜索实现，v0.2 无模型 | 仅原语 |
| 03 方法发现 | 五角色提示词（v0.1 Codex CLI）+ 提案 schema 存在；无自治循环、无工具执行、无 Claude/多模型桥 | 仅脚手架 |
| 04 反例攻击 | kill_test 为自由字符串；`audit.py` 对未执行 kill test 仅发 WARNING；无反例搜索引擎 | 文字纪律，非能力 |
| 05 验证与验收 | 最强部分：三重晋升门、独立证据组、内容寻址工件、哈希链事件账本、防篡改工作区、角色权限。但重放从不被执行 | 强，但需「执行重放」补洞 |
| 能力资产化 | FailureMemory/EpisodeMemory（15 条手工 episode）+ 词法检索；覆盖 6 类资产中的 2 类；无方法包（MethodAsset）、无结构签名检索、无自动蒸馏 | 胚胎 |
| 快评/精评预算调度 | `BudgetSpec` 是静态声明，仅用于配对基准；token/CPU 依赖 agent 自报；无调度器、无 Kendall τ 代码；BP 第 8/19 页 Open3DBench 数据（8 用例/41 候选、τ=1.0）在仓库零支撑 | 零代码 |
| 客户环境验收闸门 | release 状态机是论文语义（PROVED_AND_AUDITED）；无客户基线比较、无双方确认指标、无 customer-acceptor 角色 | 零代码 |
| 真实数学产出 | Frankl q=6 各层（双实现证书、冷重放）与 ES7 SAT 均为**绕过引擎**的手写验证程序；arXiv:2607.28557（无限维李群）是人 + 对话流程，未入引擎；引擎唯一端到端 run 是玩具奇数和恒等式 | 引擎与真实数学分离 |

**关键事实**：仓库中所有已闭合的真实数学（Frankl q=6 的 244,068 个残差型多重集
审计等）都是**每个问题手写专用验证器**得到的；引擎只做了记账。这不是缺陷
清单上的一项，而是诊断的核心——可复用能力不是任何单个验证器，而是
「验证器的受治理合成与交叉核对流水线」本身。

---

## 2. 核心诊断（六点，均经代码核验）

1. **发现回路断开**。`matharc/v02/workers.py` 只有 SubprocessProposalWorker
   （空壳协议适配器）与 StaticProposalWorker（演示 mock）；全仓库 grep 无
   anthropic/claude；`session.run_round` 只执行一轮且从不执行计划要求的工具；
   `orchestrator.accept_agent_proposal` 对不在 trace 中的 claim_id 直接
   `continue`，没有创建 claim/route 的动作词汇；CLI 无 `run` 子命令。
2. **验证检查形式而非数学**。`trace._promotion_issues` 只验证「重放命令与摘要
   字符串存在」；demo 中根 claim 的 FORMAL_PROOF 证据摘要是字符串
   `'base+step=>forall-n'` 的 SHA。round-4 Frankl 的 `rebuild_all.sh` 引用了
   三个仓库中不存在的验证器源文件（8 个结果 JSON 只有 1 个入库）——这正是
   「重放是记录的契约而非执行的契约」会发生的事。
3. **结构数学的证据通道存在但无治理**。`EvidenceKind.HUMAN_AUDIT` 已存在
   （schema.py:87）且**已经是 proof-capable**（proof_capable 只排除
   NUMERICAL_EXPERIMENT 与 HEURISTIC），但全仓库无任何代码路径产生它：
   没有评审工作流、没有评审者身份、没有升级阶梯。这意味着李群/量子群类
   结构数学今天「理论上」可以经两个独立 HUMAN_AUDIT 组闭合——却没有任何
   防护。真正要做的不是加证据类型，而是**建工作流并收紧策略**。
4. **「共享引擎」没有可导入的边界**。领域中立的协议代码与 Frankl 专用代码
   （`matharc/frankl_q6.py` 340 行位于通用包内）、两代冻结的重复词汇
   （v0.1/v0.2 双 ClaimStatus）纠缠在一个单体包里；Resolve 无法在不拖入
   全部历史的情况下依赖「引擎」。
5. **数据飞轮无进水口**。`episode_memory.py` 只有 `mark_reused`，没有任何
   ingest/add 路径；15 条 episode 全为手工策划，**零条**来自仓库自己的
   Frankl/ES7 run；无 datasets/ 目录、无导出模块；配对基准的唯一被测 agent
   是回显环境变量的 mock，`agent_registry_v02.json` 全部条目
   `measured=false`。
6. **预算与成本是声明而非计量**。基准 runner 对 token/模型调用/工具 CPU
   信任 agent 自报（仅强制墙钟与输出字节）；v0.1 `RouteRecord.cost_units/
   rounds_without_gain` 只写不读。被弃用的 `.matharc-v02-bootstrap` 载荷中
   存在一份含 `expected_information_gain/estimated_cost` 的调度器设计，
   从未进入正式代码——实现前值得先挖掘。

---

## 3. 改进工作项（30 项提案合并后 19 项 + 5 盲区）

优先级：P0 = 回路成立的前提；P1 = 可信度与商业化必需；P2 = 集成与产品化。

### W1 关闭发现回路（Research 侧的「会做数学」）

| # | 工作项 | 内容 | 位置 | 优先级 |
|---|---|---|---|---|
| W1-1 | **自治多轮 Campaign + 受治理分解**（合并 A1+C2+B9） | `campaign.py`：plan → worker 提案 → dispatcher → 工具执行 → 晋升尝试 → 指标 → 停止条件（预算耗尽/终态/N 轮无增益），每轮原子持久化。dispatcher 扩展提案词汇支持 `create_claim/create_route`：新 claim 一律以 PROPOSED 进入、校验依赖存在性/无环/机制签名去重/每轮上限、scope 不得超过父 claim；工具请求走**模板 id + 类型化参数的白名单注册表**，绝不透传 shell 字符串；晋升权保持在 promotion-gate。CLI 增加 `python -m matharc.v02 run` | 新增 `matharc/v02/campaign.py`、`dispatch.py`、`tool_executor.py`；改 `orchestrator.py`、`cli.py` | **P0** |
| W1-2 | **多模型 Worker 桥（Claude + Codex）**（合并 C1+A2） | `ModelClient` 协议 + AnthropicModelClient（JSON schema 强制输出）+ CodexCLIModelClient（包装现有 codex_runtime）+ OpenAI 兼容客户端；`LLMProposalWorker` 实现现有 ProposalWorker 协议直接落入 ResearchSession；把 v0.1 的角色提示与 8 条不可协商规则移植为供应商无关的 `prompts.py`，加 **token 预算内的 trace 视图裁剪**（焦点 claim + 祖先闭包 + 检索到的教训，而非整个 run JSON）；每次调用强制产生 `ModelUsage`（token/成本/供应商）记录 | 新增 `matharc/v02/model_workers.py`、`prompting.py`、`configs/models.toml` | **P0** |
| W1-3 | **计量化预算账本 + 快/精评调度器**（合并 B4+C3+A9） | `BudgetLedger`：从 ModelUsage 与 ToolCallRecord 时间戳**实测**计量，与自报 usage 对账并标记偏差；`EvaluatorTier{VALIDITY,FAST,PRECISE,ACCEPTANCE}` 分层，按 BP 第 20 页逐字实现降级顺序（预算不足时优先保留合法性检查与快评）；stdlib 实现 Kendall τ 的 `RankingFidelityRecord`（内核保持零依赖）；所有调度决策封入哈希链事件账本；实现前先挖掘 bootstrap 载荷中的信息增益调度器设计 | 新增 `matharc/v02/budget.py`（或引擎包内 `scheduler.py`、`fidelity.py`）；改 `benchmark_runner.py` | **P0** |
| W1-4 | **FormalProblemStatement + 问题接收/分解管线**（A3，与 W3-1 同一 schema PR） | 数学语句的形式表示：typed objects（挂接 ObjectRegistry）、hypotheses、quantifier_prefix、conclusion、parameters、finite_instance_generator；`intake.py`：自然语言/LaTeX → decomposer worker 产出形式语句 + 初始 claim DAG + 机制多样路线（经 W1-1 的创建通道）；把已被证明有效的「残差收缩」模式（Frankl ≥2→≥3→≥4 小部件）固化为 ResidualLadder 助手。试金石：用 intake 重建 Frankl q6 残差（≥4 小外部件）契约而非手写 | 改 `schema.py`、`object_registry.py`；新增 `intake.py` | **P0** |

### W2 让验证真正验证（可信度）

| # | 工作项 | 内容 | 位置 | 优先级 |
|---|---|---|---|---|
| W2-1 | **执行式重放门**（C4） | `ReplayExecutor`：沙箱子进程执行 `replay_command`、重算输出摘要并与 `digest_sha256` 比对，结果作为 ReplayAttempt 事件；策略位 `require_executed_replay` 使关键 claim 无通过重放即拒绝晋升；`matharc.v02 replay --trace` 批量模式进 `make ci` | 新增 `replay_executor.py`；改 `trace.py`、`_workspace_impl.py` | **P1**（对外宣称前为 P0） |
| W2-2 | **可执行反例引擎**（A6） | `KillTestSpec` 结构化 schema 取代自由文本 kill_test（enumeration/property_random/sat_search/instance_eval + 机器可判定判别器）；FalsificationEngine 把路线 kill test 与 director 的 mandatory_attack_tests 编译为可运行作业；**把 audit.py 的 kill-test WARNING 升级为硬性晋升阻断**（与 W2-4 协调，只改一次） | 新增 `falsification.py`；改 `schema.py`、`audit.py` | P1 |
| W2-3 | **真实 Lean 管线**（A4） | 入库一个 pinned lake 工程（lean-toolchain + mathlib manifest + 冒烟文件）；自动形式化往返：formalizer worker 产出 Lean 语句（sorry-free 编译门）→ **独立 worker 反向翻译回散文与 claim 语句比对**，以此填充 statement_correspondence（取代今天的自我断言）；内核 exit 0 才产生 FORMAL_PROOF 证据。首个里程碑：给一条已闭合的 Frankl 子引理做内核校验 | 新增 `formal/` lake 工程；改 `framework_adapters.py`、`cli.py`、CI | **P0/P1** |
| W2-4 | **专家评审回路 + HUMAN_AUDIT 治理**（合并 C7 + 重构后的 A7） | ReviewRecord（评审者身份、逐项核验清单、verdict、内容摘要）封入事件链；工作区服务器加**带鉴权的唯一写路径** `POST /api/review`（其余保持只读）；APPROVE 产生 HUMAN_AUDIT 证据记录；**收紧策略**：关键 claim 仅靠 HUMAN_AUDIT 闭合时要求第二独立评审组 + 关键引理形式化（散文→审计散文→部分形式化的升级阶梯）。随后经 `legacy_harness.py` 回灌 arXiv:2607.28557 为机器可审计 trace（人核节点标 SUPPORTED，不洗白为 PROVED），并从中蒸馏 episode | 新增 `review.py`；改 `_workspace_server_impl.py`、`schema.py`、晋升策略 | P1 |
| W2-5 | **跨模型对抗评审**（C6） | 多轮对抗审查落码：falsifier 必须与 proposer **不同供应商/模型**（用 ModelUsage.provider 机械校验，写入 independence_group——让至今为自报字符串的「独立性」第一次有机械含义）；每轮要么给出可执行反例尝试（交 ToolExecutor 运行）要么给出结构化 Objection；N 轮无异议才可提名人审 | 新增 `adversarial.py`；改 `metrics.py`（falsification_pressure） | P1 |
| W2-6 | **文献适配器**（A8） | 实现已声明的 LiteratureAdapter 协议：arXiv/Crossref 拉取 → PDF 按 SHA-256 钉入 ArtifactStore → SourceClaim（定位符/适用条件/语句对应）由 literature worker 起草、literature-auditor 角色确认；已知结果作为 source-linked 外部前提 claim 进入路线，复用「未验证来源阻断晋升」现有门。也服务 PAPER_READINESS 的新颖性审计义务 | 新增 `literature.py` | P1 |
| W2-7 | **证书化评价器族 + 验证器合成门**（合并 A5+B3 的适配器半） | 从 `frankl_q6.verify_geometry` 抽取**通用证书化分支定界**（单调下界协议 + 见证捕获 + 剪枝记账）；SAT 适配器（CNF + kissat/cadical + DRAT 校验，顺手补上 ES7 缺失的证据存档）；SMT 适配器（z3，UNKNOWN 硬阻断晋升）；CAS 适配器（sympy，精确有理=EXACT、数值=TESTED）；有限实例扫描（由 FormalProblemStatement.finite_instance_generator 驱动）。**验证器合成工作流**：prover worker 在沙箱写问题专用验证器，必须经「第二独立 worker 按规格重实现 + 全输入集输出比对」的双实现门才具 EXACT 资格——把现有 Python/C++ 双实现惯例从纪律变成可执行的门 | 新增 `evaluators/` 包、`verifier_synthesis.py` | P1 |

### W3 引擎抽取与 Resolve 实例化（数学结构拆解的复用）

| # | 工作项 | 内容 | 位置 | 优先级 |
|---|---|---|---|---|
| W3-0 | **抽取 matharc_engine 内核包**（B1，重构后） | 把 v0.2 的领域中立内核（schema/trace/orchestrator/metrics/event_log/artifact_store/audit/authorization/registries/workers/session/memories/workspace/benchmark/framework_adapters）移入可独立分发的 `matharc-engine`（依赖为空，已经成立）；Frankl/奇数和演示移入 `matharc_research/problems/`；v0.2 入口变薄壳再导出，90 测试与两个验收脚本不改而绿。**时序警告**：大搬移与其它所有工作项的文件路径冲突，必须显式排在回路工作之前或之后，不可并行 | 新 `matharc_engine/`；改 `pyproject.toml`（双包分发） | **P0**（排期上先行或殿后） |
| W3-1 | **ProblemStructure：跨场景不变结构落码**（B2，与 W1-4 同一 PR） | `SearchSpace{CLAIM_DAG\|CANDIDATE_SET\|PARAMETRIC_FAMILY}`、`Constraint{HARD\|SOFT, checker_evaluator_id}`、`Objective{metric, direction, baseline}`、`EvaluatorBinding{tier, evidence_kind}`、`structure_signature`（规范形 SHA-256，作为方法包检索键）；TheoremContract 与新的 CandidateEvaluationContract 是它的两个实例化 | 新增 `problem_structure.py`、`contracts.py` | **P0** |
| W3-2 | **统一评价器接口 + 注册表**（B3 的接口半） | `Evaluator` 协议：`evaluate(request) -> {score\|verdict, ToolCallRecord, EvidenceRecord, artifacts}`——每个结果都是现有账本对象，晋升门/审计/工件库零改动直接适用；声明 tier + cost_model + 环境 pin；四个桥接适配器证明通用性：v0.1 Tool、LeanCliFormalizer、证书脚本模式（以 `verify_q6_residual_type_multisets.py` 为范本——仓库最佳的廉价精确自包含评价器）、SubprocessEvaluator（客户工具链用） | 新增 `evaluators.py`、`adapters/` | **P0** |
| W3-3 | **候选集与排序记录**（B5） | `CandidateRecord{payload 摘要, 合法性状态(违规阶段), 各评价器得分→ToolCall/Evidence 链接, 边界}`、`RankingRecord{排序, 依据评价器, 保真记录, 预算消耗}`；CandidateEvaluationTrace 与 ResearchTrace 共享事件账本/工件库/fail-closed 语义：Ranking 仅当每个候选的依据得分都链接到可重放的已接受证据才可标 ACCEPTANCE_READY | 新增 `candidates.py`、`candidate_trace.py` | P1 |
| W3-4 | **客户验收闸门**（B6） | `AcceptanceProtocol{客户基线引用, 双方确认指标(双签), 环境 pin, 所需签核}`；AcceptanceRun 在钉定环境执行 ACCEPTANCE 层评价器、复用 benchmark.py 的配对 bootstrap 机制做「方法 vs 客户基线」比较；authorization 增加 customer-acceptor 角色独占 ACCEPT_DELIVERY（镜像 promotion-gate 模式）；metrics 增加 Resolve 侧发布阶梯 SCREENED→PILOT_VALIDATED→CUSTOMER_ACCEPTED，营销开关钉在 CUSTOMER_ACCEPTED | 新增 `acceptance.py`；改 `authorization.py`、`metrics.py` | P1 |
| W3-5 | **方法包库（MethodAsset）+ 自动蒸馏**（B7，蒸馏与 W4-1 合一） | MethodAsset 完整承载 BP 六类资产：问题结构快照+签名 / 方法载荷（路线配方\|求解器配置\|验证器程序\|流程） / 证据引用 / 适用边界 / 失败边界（链接 FailureLesson） / 运行条件（环境摘要、工具 pin），外加 reuse 计数与出处；检索先按 structure_signature 精确/近似匹配、再落词法评分；director.plan_round 像消费 episode 一样消费方法包。先从 Frankl q=6 各轮回填种子资产 | 新增 `method_assets.py`；JSONL 存 `memory/` | P1 |
| W3-6 | **交付包导出器**（B8） | 在 workspace_bundle 机制上做 DeliverableBundle 两个 profile：`research`（论文支撑：claim DAG、证书、重放命令）与 `resolve`（验收依据：排序、逐候选得分溯源、基线比较、预算记账、工具原始报告、reproduce.sh、自包含 HTML 报告）——BP 第 4/16/20 页定义的付费交付物本体 | 新增 `deliverable.py`；CLI `export` | P1 |
| W3-7 | **合成 EDA 端到端演示**（B10） | `problems/eda_screening_demo/`：5 个确定性「网表配置」候选 + 合法性检查器 + 快评（解析特征分）+ 精评（带可控分歧旋钮的慢速模拟桩，专门测 τ<1.0 路径）+ 基线 + 双指标验收协议；全链路跑通 CandidateEvaluationContract→调度器→Ranking+τ→AcceptanceRun→resolve 交付包→自动蒸馏方法包，进 `make ci`。第二步（依赖仓库外资产）：把真实 Open3DBench 管线迁入此格式，让 BP 第 8/19 页数字变成可重放的引擎工件 | 新增 `matharc_resolve/`、演示问题 | P2（但须在任何付费试点前落地） |

**「共享引擎为真」的判定门**：奇数和研究 trace 与 EDA 筛选 trace 从同一
`matharc_engine` 导入面跑绿于 CI，且两侧各蒸馏出一个方法包、能按
structure_signature 互相检索。此门应在首个付费 tier-01 诊断（BP 0–3 月里程碑）
之前达成。

### W4 数据飞轮与评测

| # | 工作项 | 内容 | 位置 | 优先级 |
|---|---|---|---|---|
| W4-1 | **统一蒸馏钩子 + 版本化数据集导出**（合并 C5+A10a+B7 蒸馏半） | run 收尾钩子把 trace 蒸馏为 ResearchEpisode + FailureLesson + MethodAsset **草稿**（DRAFT 态，人审后转正）——先回填仓库自己的 Frankl/ES7 run（当前贡献为零）；DatasetExporter 产出带摘要清单的版本化 JSONL：`episodes` / `sft`（plan+trace 视图→被接受提案对，schema 天然无 CoT）/ `eval`（BenchmarkCase）。这正是 BP 4–7 月「数据可复现」里程碑的字面交付物 | 新增 `episode_distiller.py`、`dataset_export.py`、`datasets/` 约定 | P1 |
| W4-2 | **基准战役：真实 agent 进配对基准**（C8） | 349 题研究级评测集（或首批 30–50 题以过 compare_agents 的 30 对下限）以现有 BenchmarkCase schema 入库 `benchmarks/corpus/`（**外部依赖**：语料在仓库外，需明确获取责任人）；`llm_benchmark_agent.py` 让 LLMProposalWorker+Campaign 走基准 runner 协议，让 `agent_registry` 第一个条目翻为 measured；`benchmarks/milestones.json` 把仓库工件机器映射到 BP 18 个月三闸门；「模型有增益」= 预注册的等预算 compare_agents 实验：{基础 agent} vs {基础 agent + 导出数据/记忆}，用现有 bootstrap-CI 资格门出证据 | 新增语料目录、示例 agent、milestones.json | P1 |
| W4-3 | **多 run 工作台服务器**（C9） | RunRegistry（目录 + 每 run 文件锁）+ REST `/api/runs/{id}/…` + campaign 实时 SSE（事件词汇已在 EventLedger 中）+ 评审端点（与 W2-4 的写路径共建）+ 交付包下载；保持 stdlib 零依赖。明确 P2：**不许服务器工作抢占回路工作** | 新 `matharc/server/` 整合三处 HTTP 面 | P2 |
| W4-4 | **v0.1 退役 + Frankl 入引擎**（C10 重构后） | ① frankl_q6.py 与 verifiers/*.cpp 包装为注册评价器，把 Frankl q=6 重建为真实 v0.2 trace——最短路径的非玩具端到端故事，随 Phase 1 落地；② round-4 重放链修复或降级：`rebuild_all.sh` 引用的三个验证器源在仓库任何位置都不存在、8 个结果 JSON 仅 1 个入库、证书清单 SHA 过期——要么恢复/重推导，要么把 `LATEST_Q6_AUDIT.md` 的声明降级到实际可冷重放的范围（**可信度问题，先于新功能**）；③ v0.1 面冻结加弃用说明，Codex 控制台独有价值（SSE 聊天、快捷提示）移植到新服务器 | `matharc/v02/adapters/frankl.py`；`experiments/frankl_q6_round4/` | ①P0 随 Phase1；②P0 可信度；③P2 |

### W5 批判轮补充的盲区（原 30 项提案全部遗漏）

1. **误差有界的数值证据语义**（连续域垂直场景的前提）。BP 已确认的两个二级
   垂直（GMPT/芯钬量子：PDE/线性方程组/约束优化；华灵动力：定容/充放电调度）
   不存在 Frankl 意义上的「精确」——验收是「证书化容差内成立」。需要新增
   区间算术/误差界证据类型与容差感知的验收语义、MILP/OR/ODE 求解器评价器
   适配器。没有它，「按问题结构扩张」只对离散可枚举问题成立。
2. **私域数据治理与私有化部署**（Resolve tier 02–03 前提）。客户网表/基线会
   流入 trace、工件库、LLM 提示词与交付包：需要证据链中的数据分级/脱敏、
   模型调用不出客户边界的部署形态（现仅一个裸 Dockerfile）、方法包库的
   许可/授权机制。回路开始在客户环境执行模型提出的工具请求后，沙箱策略
   从工程问题升格为合同问题。
3. **自有数学的外审与发表管线**。PAPER_READINESS 的开放门（q6 洁净室重实现、
   外部组合数学审计、新颖性审计、工件冻结）与下一个数学前沿（≥4 小部件
   分类、H_p/顶纤维机制升到 q≥7）没有任何提案排期——而 BP 的科研可信度
   叙事（科研轨迹证明能力上限）依赖结果经受外部检验。残差问题不应只当
   测试夹具，应作为承诺的数学交付物。
4. **长时程 campaign 的运行鲁棒性**。Lean 证明尝试/穷举枚举会跑数小时到数天：
   需要断点续跑、崩溃恢复、幂等重入、已消费预算账本的恢复、昂贵评价器
   作业的抢占——这是 0–3 月「真实运行」（保留失败与修订记录）与任何客户
   环境试点的基本盘。
5. **语句对应性作为一等可审计对象**。体系中几乎每道门最终都压在
   `statement_correspondence` 这个只查非空的自由文本上（trace.py 晋升检查）；
   BP 第 12 页的专家评审协议正是为控制这一风险而设。应把「非正式语句 ↔
   形式 claim ↔ 证据工件」的对应做成有独立签核的可验证记录（W2-3 的 Lean
   反向翻译与 W2-4 的人审勾选是两个入口，但需要统一的记录对象）。
   **这是全部改进落地后剩下的最大洗白通道。**

---

## 4. 分阶段路线图（对齐 BP 18 个月里程碑）

**Phase 0（已完成，commit `946eda7` + 本提交）**：本地 CI 全绿——mypy strict
从静默跳过 4 个核心模块变为全覆盖 33 文件（importlib 遮蔽垫片改为静态导入的
`_*_impl` 私有模块）；修复 Lean 适配器运行时崩溃、SSE 连接不关闭、依赖未闭合
claim 被选为轮次焦点、超时流 bytes/str、裸 prompt 绕过研究规则前言；清理 14 个
被跟踪的循环残留文件与 README_V01.tmp；PROJECT.md 分支引用更正。

**Phase 1（第 0–6 周，对应 BP 0–3 月「真实运行」）**：
先做 W3-0 引擎包抽取（趁文件搬移不与他人冲突），然后三条并行轨：
W1-2 模型桥 / W1-1 Campaign 回路 / W1-3 预算账本。集成目标：
`matharc.v02 run` 在两个夹具上完成多轮自治 campaign——奇数和演示与
**Frankl q=6 残差**（frankl_q6 包装为注册评价器，W4-4①）——产出带失败记录、
计量成本、无人转录的持久化 trace。W1-4/W3-1 的统一 schema PR 与 W4-4② 的
round-4 可信度修复随行。

**Phase 2（第 6–14 周，对应 4–7 月「数据可复现」）**：
W2-1 执行式重放门；W4-1 蒸馏 + 首个版本化数据集（从 Phase 1 的 run 切出）；
W2-5 跨模型对抗评审（消费第二供应商）；W2-3 Lean 真实内核 + 首条 Frankl
子引理形式化；W2-7 评价器族 + ES7 DRAT 证据存档；W4-2 首批 30–50 题语料
过配对基准，registry 首条翻 measured。里程碑：**一个由回路产出、除合成
工作流外零手写验证器代码的新的小结果**（如 Frankl 下一残差层）。

**Phase 3（第 14–26 周，对应 8–12 月「模型有增益」+ 产品）**：
W2-4 人审回路（依赖服务器写基建，与 W4-3 同步）；W2-6 文献适配器；
预注册等预算实验 {基础} vs {基础+数据/记忆}——这**就是**「模型有增益」的
证据本体；W2-4 后半：回灌 arXiv:2607.28557 并在团队李群/量子群领域端到端
攻一个开放子问题（目标：审计散文证明 + 一条关键引理形式化）——这是运行时
从「仅枚举证书」扩展到研究级广度的转折点。

**Phase 4（并行/其后，对应 13–18 月客户复用）**：
W3-3/4/5/6/7 Resolve 栈（候选/验收/方法包/交付包/EDA 演示）——其中 W3-1/2
已在 Phase 1 落地，故可从 Phase 2 起与 Research 轨并行推进；「共享引擎判定门」
须在首个付费诊断前通过。W5 盲区中，#1（数值证据）随二级垂直排期，#2（私域
治理）先于任何客户环境试点，#4（鲁棒性）随 Phase 1–2 的长 run 需求落地，
#5（语句对应）作为横切策略项在 W2-3/W2-4 落地时统一设计。

---

## 5. 设计红线（任何改进不得破坏）

1. **提案非验收**：模型/worker 输出只能到 PROPOSED/OPEN/CANDIDATE/BLOCKED；
   晋升唯一路径是 `trace.promote_claim`（+工作区审计+角色门）。新的回路、
   调度器、评审协议全部**接入**这道门。
2. **私有思维链禁令**：schema 解析、worker 合同、基准 runner、trace 序列化
   四层拒绝 CoT 字段；公开理由只走 6 字段 PublicReasoningStep。数据集导出
   天然继承此约束。
3. **fail-closed 作用域语义**：INSTANCE < FINITE_RANGE < PARAMETRIC_FAMILY <
   GLOBAL 的量词提升必须有自己的证据；有限/数值证据永不证全称命题。
4. **压缩搜索需未压缩审计**：任何压缩状态空间的闭合需要未压缩审计或被证明
   的压缩映射（244,068 多重集复审计的教训，已是强制条令）。
5. **宣称受门控**：营销/对外声明开关只钉在 PROVED_AND_AUDITED（Research）
   与 CUSTOMER_ACCEPTED（Resolve）；比较性宣称必须过 30 对等预算 + 零假晋升
   + bootstrap CI 下界的资格门。BP 文案不得跑在这些门前面——CI 在强制执行。

---

## 附录：本轮多智能体分析的证据基础

- 4 个深读报告覆盖：v0.1 内核（engine/models/tools/codex 运行时）、v0.2 全部
  28 模块、docs/benchmarks/scripts/bootstrap 载荷、experiments/verifiers/
  memory/tests。
- 3 份视角提案（研究级数学能力 / 引擎复用 / Agent 工程与数据飞轮）共 30 项。
- 1 轮对照 commit `946eda7` 的逐项可行性批判：30 项全部核验，三大合并
  （回路=A1+C2+B9、模型桥=C1⊃A2、调度器=B4+C3+A9），1 项事实纠错
  （HUMAN_AUDIT 已存在且 proof-capable——A7 从「加证据类型」改为
  「建工作流并收紧策略」），5 项盲区补充。
- 关键代码证据（文件:行）散见 §2 各条；完整 agent 报告见本次会话工作流
  `wf_f54ccb7b-624` 的 journal。

---

## 附录 B：W2-4 专家评审工作流的推荐设计（细化）

> 本附录与附录 C 的按依赖排序的工程里程碑分解（触碰文件、工作量、
> 验收标准、统一排期）见 `docs/DEV_PATH_V03.md`。

背景：`EvidenceKind.HUMAN_AUDIT` 已存在且 proof-capable，但全仓库无任何
产生它的代码路径——这是结构数学（李群/量子群/SDE，团队真实强项）进入
本系统的第一瓶颈，排在 Lean 之前。推荐工作流分七步，每步都复用已有
基础设施而非新造：

1. **进入条件（机器预筛）**：只有已到 CANDIDATE、且其路线 kill test 均已
   执行、且熬过 N 轮对抗评审（W2-5）无未决异议的 claim 才可提名送审。
   专家小时是最贵的评价器——BP 的「先快评再精评」纪律对人同样成立，
   预筛保证专家时间只花在幸存者上。
2. **审前打包（ReviewBundle）**：系统自动生成内容寻址的送审包——冻结的
   claim 语句 + 钉定的定义（ObjectRegistry）+ 依赖路径 + 全部证据及其
   重放命令 + 证明文本拆成**编号义务清单** + 已尝试过的攻击史。打包
   事件封入哈希链。复用 workspace_bundle 机制。
3. **逐项核验记录（ReviewRecord）**：评审人身份（roster + 机构 + 利益
   冲突声明）；**逐义务**给出 OK / gap / error / 无法判断——不是一个
   总体点头；`statement_correspondence` 单列为独立核验项（它是已知的
   最大洗白通道，见 W5-5）；总裁决 ∈ APPROVE / REQUEST_CHANGES /
   REJECT；内容摘要签名封入事件链。写入走工作区服务器**唯一的带鉴权
   写路径**（其余保持只读）。
4. **独立性规则（对人复用证据独立组机制）**：关键 claim 需要**两个不同
   independence group 的评审人**（不同机构/师承谱系，评审人注册表带
   组标签）；评审人不得是该路线的提出者——generator/checker 分离对人
   同样成立。
5. **升级阶梯（策略旋钮 `human_audit_policy`）**：非关键 claim 可由单个
   APPROVE 闭合；关键 claim 需两个独立 APPROVE **且**所有承重计算步骤
   已有精确证据（SMT/穷举/证书）；最高档（对外宣称级）另加关键引理
   形式化（Lean 落地后）。散文 → 审计散文 → 部分形式化，逐档加价。
6. **反馈回路**：REQUEST_CHANGES 的逐项 gap 自动转为下一轮计划的
   route_constraints / mandatory_attack_tests（喂给
   AdaptiveResearchDirector）；REJECT 触发 `record_failure`（从 14 类
   失败分类中选类）并级联。**专家抓到而机器没抓到的失败类，蒸馏进
   episode memory 成为下一次的机器强制攻击项**——专家评审在训练反例
   引擎，这是人审的复利。
7. **对外表述门**：仅靠 HUMAN_AUDIT 闭合的 claim 在 metrics 中标
   `human_trust_dependent: true`，release state 对外表述必须区分
   「机器校验闭合」与「人工审核闭合」——两者都合法，但不是同一种
   可信度，混同即违反红线第 5 条。

这套工作流同时就是 BP 第 12 页「陈小杨科学标准层」的产品化：ReviewBundle
是专家网络消费的对象，评审工时按精评预算计量，审核协议即 §3 的
AcceptanceProtocol 在科研侧的镜像。

## 附录 C：除「发现与治理流程」外的差异化候选轴

对照 Harmonic / Axiom（Lean 形式验证为核心卖点），除 claim DAG /
fail-closed 晋升 / 失败记忆 / 可审计轨迹这条主轴外，还有五条可选轴，
均已在本仓库有胚胎：

1. **否证优先（falsification-first）作为产品主打**：竞品全在卖「证明」，
   没有人卖「系统化的廉价否证」。kill-test 纪律 + 14 类失败分类 + 反例
   引擎（W2-2）→「我们用最便宜的手段杀死错误候选」——这恰好就是 Resolve
   IC/EDA 的价值主张（先筛掉低价值候选），科研与商业共用同一把刀。
   差异化压在评价器阶梯的**便宜端**而非昂贵端。
2. **问题专用验证器合成 + 双实现门**（W2-7 完整版）：竞品把问题形式化进
   一个固定系统；MathArc 为每个问题**制造**专属精确检查器并强制独立双
   实现交叉核对（Frankl 的 Python/C++ 模式的可执行化）。「验证器工厂」
   比「单一验证器」更难复制。
3. **负知识资产（failure/episode 数据）**：没有竞品在积累结构化的「证明
   如何失败」数据。跨问题失败库既是护城河数据集，也是 BP 8–12 月
   「模型有增益」实验的燃料——差异化即专有数据。
4. **认证人审网络作为双边资产**：专家网络 + 逐项核验协议（附录 B）=
   一个比期刊更快、可重放、逐条留痕的「审稿服务」。Lean 竞品短期内
   复制不了一个数学家网络。
5. **分级担保（graded assurance）作为定价结构**：证据类型阶梯
   （HEURISTIC → NUMERICAL → HUMAN_AUDIT → EXACT_* → FORMAL_PROOF）
   让同一结果可以按客户需要的可信档位交付并**分档定价**——卖阶梯本身，
   而不是只卖最顶层。工业客户要的是双方确认指标下的够用严谨
   （right-sized rigor），不是 Lean；这是对二元「形式化了没有」定位的
   正面差异化。

取舍建议：轴 1 与轴 2 技术含量最高且直接服务 Resolve，优先；轴 3 随
W4-1 蒸馏自动到位；轴 4 依赖附录 B 落地；轴 5 是叙事/定价层，成本最低，
可立即写进对外材料——前提是红线第 5 条的表述门先在 metrics 里可机读
（`human_trust_dependent` 等标记）。
