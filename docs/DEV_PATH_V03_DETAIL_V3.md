# v0.3 开发路径：专家评审工作流（R 轨）与差异化五轴（F/V/N/S/G 轨）

> 本文把 `IMPROVEMENT_PLAN_V03.md` 附录 B（七步评审工作流）与附录 C
> （五条差异化轴）展开为按依赖排序的工程里程碑：每项给出触碰的文件、
> 依赖、粗估工作量与**可执行的验收标准**（沿用本仓库的纪律：每个新门
> 落地时必须带一个证明否定路径的测试——"不能晋升/不能宣称"的测试比
> "能"的测试更重要）。
>
> 基线：commit `c397d18`（闭环 campaign + Claude Code worker 桥 + 精确
> 工具/SMT 评价器已落地，**本地** `make ci` 全绿）。所有里程碑的不变
> 前提：本地 `make ci` 保持全绿；晋升权永远只在 `trace.promote_claim`。

## 修订记录

- **v3（2026-08-27）**：吸纳第二轮外部评审（对象为前端原型与 v1 文本）。
  **前端部分全盘采纳并已重写原型**（`docs/prototypes/review-console.html`）：
  ① 引入 **View Model 分层**——Domain DTO（后端字段草案）→ 中文视图模型
  → 界面；`EXACT_COMPUTATION`/`ACCEPTED`/`independence_group` 等后端枚举
  与摘要只出现在逐证据「技术详情」与「包信息」层，默认不渲染；
  ② **渐进披露**——证据卡默认只答「证明了什么/覆盖什么/是否独立核验」，
  全部证据与依赖/攻击史两节默认折叠；原始 Bundle/Record JSON 收进
  开发者层入口；
  ③ **响应式壳层重做**——桌面断点提前到 1280px，左右栏加视口高度上限
  与独立滚动；平板/手机端裁决区改为 60px 折叠条 + ≤70dvh 抽屉，队列改
  抽屉；顶栏收敛为「品牌+当前任务+进度+包信息」，摘要/链头/名册移入
  包信息弹层；手机端 2×2 裁决按钮、44px 触达高度；
  ④ **四个真实缺陷修复**——切包时利益冲突勾选串包（状态流改为单向）、
  已提交视图顶栏残留旧包信息、ReviewRecord 曾用截断摘要（现全长
  SHA-256，显示层才缩略）、攻击史 innerHTML 注入面（改结构化
  summary+emphasis，全量转义）；草稿键绑定评审人并加 7 天过期，注明
  生产环境须服务端草稿；证据链接从"滚动跳转"改为**侧边抽屉**，评审人
  不丢上下文；新增未核验筛选、"下一条未核验"（n 键）、上下文化阻塞项。
  **方案部分**：评审第 2/3 点（V2 双实现语义、G0 标量）针对的是 v1
  文本，v2 已修——本轮仅补显式命名：V2 增加
  `implementation_diversity` 标志位表述（双实现一致只置此标志，永不
  单独决定证据档）；G0 担保向量补 `formalization: none|partial|full`
  维度（原型与文档向量自此同源）；R6/P2 增加**服务端 ReviewBundle
  View Model** 要求（前端不得直接消费 Domain DTO）。第 1 点（前端跑在
  后端前面）成立——原型页内已加"原型承诺 ≠ 后端事实"标注，落地顺序
  仍按 v2：F0.5 共享 RouteEvaluationRecord 先行。第 4 点（远程 CI
  Gate）维持 v2 的额度分档结论不变。
- **v2（2026-08-27）**：吸纳一份外部工程评审的核心意见，逐条经代码
  核实后修订（核实结论：`ResearchRoute` 确无提出者字段、
  `ToolCallRecord` 确无 route 关联、`import_legacy_harness` 返回的确是
  导入报告而非完整 trace、campaign 停滞判断确实只看
  `weighted_proof_closure`——评审的事实性论断全部成立）。主要改动：
  ① 新增 **Gate 0 工程可信基线**（按 Actions 额度耗尽的现实拆成
  本地权威与远程恢复两档，并已拆除 bootstrap/materialize 两个
  push 触发的载荷覆写工作流的自动触发）；
  ② R1 的依赖从 R0 改为 **F 轨的共享 `RouteEvaluationRecord`**，
  "kill test 已执行"第一次有了对象级定义（含
  `property_random` 无反例只算 INCONCLUSIVE、永不算 PASS）；
  ③ R0 的"禁止自审"从 RolePolicy 能力检查改为**对象级授权 +
  出处（provenance）字段 + ReviewRecord 版本绑定 + 评审生命周期**；
  ④ R4 放弃"最大权重路径"口径，改为**逐义务 required_assurance**；
  ⑤ R5 把专家 REJECT 与数学否证**拆成三个通道**（ReviewGap /
  RouteFailure / ClaimCounterexample）；
  ⑥ V 轨重排：**V3（SAT/DRAT 证明对象）前置**，V2 从"跨模型双实现
  一致即获 EXACT"改写为"证书 + 小型可信检查器门"（双实现一致只是
  缺陷探测信号），V0 通用抽象推迟到出现第二个真实实例；
  ⑦ G0 从 L0–L4 标量改为 **Assurance Vector + 派生商业标签**；
  ⑧ 排期从六轨并行改为**单条 claim 生命周期的垂直切片**
  （Gate 0 → v0.3-core → v0.3-review → v0.3-learning → v0.4）。
  未吸纳/调整吸纳的点见文末"采纳说明"。

---

## 0. 总览与依赖关系

```text
Gate 0 工程可信基线（先于一切轨道）
  └─ v0.3-core：先关闭机器证据循环
       F0 KillTestSpec ─→ F0.5 共享 RouteEvaluationRecord ─→ F1 执行
       ─→ F2 硬阻断 ─→ F3 反例级联（走 ClaimCounterexample 通道）
       + R5 前置件：ReviewGap / RouteFailure / ClaimCounterexample 拆分
       + V3 SAT+DRAT 证明对象（关闭 z3 unsat 的真实信任缺口）
  └─ v0.3-review：CLI 垂直切片（R0 → R1 → R2 → R3 → R4 → R5）
  └─ v0.3-learning：N0 蒸馏 → N1 导出 → N2 回填 + Assurance Vector(G0)
       + 小型配对回归从第一个 Sprint 就跑
  └─ v0.4：R6 HTTP、R7 大规模校准、S 轨运营、G1 定价、
       V1→V2 验证器工厂、V0 通用抽象（第二实例后）、V4 旗舰、N3 实验
```

关键交叉依赖：
- **"kill test 已执行"只定义一次**：F0.5 的 `RouteEvaluationRecord` 是
  R、F、audit、campaign 四方共用的对象；R 轨与 F 轨不得各自实现一份。
- **audit 的 kill-test WARNING→硬阻断（F2）与 W2-5 对抗评审共用一个
  改动**，先到者落地。
- **R4 的升级阶梯是「陈小杨科学标准层」的编码**：写代码前先拿阶梯参数
  （逐义务 required_assurance 的默认档位）找首席科学家签字。
- **R7 的日历时间由人主导**：评审人招募（王宇鹏/社群渠道）在
  v0.3-review 启动时就开始，而不是等代码写完。前端交互原型已先行：
  `docs/prototypes/review-console.html`（评审台 HTML 原型，含逐义务
  核验、三通道 REJECT、ReviewRecord JSON 预览），供招募演示与 R6 设计
  输入。

---

## Gate 0：工程可信基线（先于一切轨道）

背景：远程 GitHub Actions 因**额度耗尽**处于启动层失败状态（任务无
steps 即告 failure），且分支未受保护、无必需状态检查。同时仓库里存在
两个 push 触发、持 `contents:write` 的载荷物化工作流
（matharc-v02-bootstrap / matharc-v02-materialize），它们会把一份冻结
的旧 v0.2 快照解包覆写到本分支——**一旦额度恢复、下一次 push 就会
触发覆写新工作**。

| 项 | 内容 | 状态 |
|---|---|---|
| G0-a | 拆除覆写隐患：两个物化工作流改为 workflow_dispatch 手动触发 | **已完成（本次提交）** |
| G0-b | 额度受限期的权威门：**本地 `make ci` 是唯一权威门**，pre-commit 两钩（strict mypy + 架构测试）强制；每次推送前必须本地全绿——本文档所有"CI 全绿"均指此档 | 即刻生效的纪律 |
| G0-c | 版本化基线工件：`make ci` 的关键产出（验收 JSON、证书摘要、测试计数）随大里程碑入库为带日期的基线文件，替代远程 CI 缺位期间的"绿色历史" | v0.3-core 内落地 |
| G0-d | 额度/自托管 runner 恢复后：重启远程 CI（先跑通 3.10/3.12 全 steps）→ 启用分支保护 + 必需状态检查。**在检查能真实运行之前不启用必需检查**（否则会阻塞所有合并） | 条件触发 |
| G0-e | bootstrap 载荷退役评估：`.matharc-v02-bootstrap/` 16 段快照与两个物化工作流整体删除（历史已在 git 中） | v0.4 |

**在 G0-a/b 之外的轨道开工没有前置阻塞；但任何"CI 全绿"的宣称在
G0-d 完成前都必须写明"本地"二字。**

---

## 1. R 轨：专家评审工作流

| # | 里程碑 | 内容与触碰文件 | 依赖 | 工作量 | 验收标准（必须含否定测试） |
|---|---|---|---|---|---|
| R0 | 评审 schema、出处与对象级授权 | 新 `matharc/v02/review.py`：`ReviewerProfile`（身份/机构/independence_group/利益冲突集）+ `ReviewerRoster`（版本化 JSON，roster_version 摘要）+ `ObligationVerdict`（义务编号 + OK/gap/error/cannot_judge + 备注）+ `ReviewRecord`。**版本绑定**：ReviewRecord 必须携带 `claim_id + claim_revision + statement_digest + bundle_digest + reviewer_profile_digest + roster_version + review_policy_version + conflict_declaration + review_signature`——claim 语句一改，旧评审自动失配。**生命周期**：ACTIVE / SUPERSEDED / REVOKED；评审撤回、利益冲突暴露或 claim revision 变更时，其派生的 HUMAN_AUDIT 证据自动失效（STALE）。**出处前置件**：`ResearchRoute` 增 `created_by` actor 字段（ClaimRecord.owner 已有、EvidenceRecord.producer 已有，补齐 route 一角）。**对象级授权**：`can_review(actor, bundle)` 领域规则（actor ≠ route.created_by、actor ≠ 任一 evidence.producer、评审人冲突集 ∩ 送审包贡献者集 = ∅）——RolePolicy 只管"角色能不能提交评审"，**管不了"这个人能不能审这个对象"**，两层都要有。APPROVE 经 `to_evidence()` 转 HUMAN_AUDIT 证据（组=评审人组） | 无 | 5–6 天（较 v1 加 2 天：出处与生命周期） | ReviewRecord 严格 round-trip（未知/CoT 字段拒收）；**路线提出者对自己路线的评审被 `can_review` 拒绝**（对象级，而非角色级）；**claim revision +1 后旧 ReviewRecord 派生的 HUMAN_AUDIT 证据不再满足晋升门**；REVOKED 评审的证据立即失效 |
| R1 | 提名预筛（机器门） | `review.py::nominate_for_review(trace, claim_id)`：仅当 claim 为 CANDIDATE、**其每条 ACTIVE 路线在 `RouteEvaluationRecord`（F0.5）中有 outcome ∈ {PASS_BOUNDED, COUNTEREXAMPLE} 的执行记录**（INCONCLUSIVE/ERROR 不算已执行完成）、无未决 RouteFailure/ClaimCounterexample 时通过；封 `REVIEW_NOMINATED` 事件 | **F0.5**、R0 | 1–2 天 | OPEN/仅 INCONCLUSIVE 记录的 claim 提名被拒并给出机器可读原因清单；通过的提名在事件链可查 |
| R2 | 送审包 ReviewBundle | 新 `review_bundle.py`（复用 `workspace_bundle` 机制）：冻结语句 + 钉定定义 + 依赖路径 + 全部证据（含重放命令）+ **编号义务清单**（每条义务是 `{title, ask, points[], ref, required_assurance}` 的结构化对象，不是一段散文——见下方文案规范；`required_assurance` 为 R4 服务）+ 攻击史（结构化 `{summary, emphasis[]}`，不含 HTML）；包内逐文件 SHA-256、包摘要封链；**另出数学家可读的自包含 HTML 视图**（复用 visualization 底子，评审人不读 JSON）——原型见 `docs/prototypes/review-console.html` | R0、R1 | 4–5 天（含 HTML 视图与文案审校） | 同一 trace 两次打包摘要逐字节一致；篡改包内任一文件校验失败；义务清单含语句对应单列项；**义务文案通过下方文案规范的自动检查** |
| R3 | CLI 提交路径 | `matharc.v02 review` 子命令组：`nominate` / `bundle` / `submit --record review.json --reviewer <id>`（对象级 `can_review` + RolePolicy 双检、封链、生成 HUMAN_AUDIT 证据）/ `revoke` / `status`。先 CLI 后 HTTP | R0–R2 | 2 天 | 全流程冷跑四步入链；roster 外 id 与冲突评审人提交均被拒；revoke 后证据 STALE |
| R4 | 晋升策略：逐义务担保阶梯 | **放弃"weight 最大路径"口径**（weight 是调度度量，不是数学必要性——低权重依赖同样可能是不可缺少的逻辑前提）。改为：ReviewBundle 的每条义务携带 `required_assurance`，晋升检查 **∀ 必要义务：其支撑证据的担保档 ≥ 要求档**；`critical: bool` 只保留结构重要性含义，证据要求由义务级策略表达。默认策略（找首席科学家签字）：关键 claim 仅靠 HUMAN_AUDIT 闭合时要求 2 个不同评审组，且所有计算类义务已有 EXACT 档证据。`metrics.py` 出 `closure_trust_class: machine|human|mixed` 与逐义务担保快照 | R0、R2；**参数须首席科学家确认** | 4 天 | **任一必要义务担保不足时晋升被拒**（boundary_violation 留痕，指名到义务编号）；单组 HUMAN_AUDIT 的关键 claim 晋升被拒；全部达标则晋升且 metrics 标信任类 |
| R5 | 反馈回路：三通道拆分 | **专家 REJECT ≠ 数学否证**。三个互不混同的通道：**① ReviewGap**（需要修改：证明缺步/语句对应不成立/书写不清——不改变命题真假，逐项 gap 写入 `AdaptiveResearchDirector` 的 mandatory_attack_tests/route_constraints）；**② RouteFailure**（杀死一条证明机制：路线 BLOCKED/FALSIFIED，**claim 不动**，可由其他路线继续）;**③ ClaimCounterexample**（仅当存在**独立核验的精确反例**时才走现有 `record_failure(exact=True)` 使 claim REFUTED 并级联）。为此 `FailureRecord` 补 `target_kind`（route/claim）、适用 revision、`resolution` 字段；`record_failure` 语义保持强，但只有通道③可触达它 | R3、R4；F3 复用通道③ | 3–4 天（较 v1 加 1 天：通道拆分） | **REJECT(gap) 后 claim 状态不变**且下一轮 plan 含 gap 原文；REJECT(route) 仅路线转 BLOCKED；只有带核验反例的 REJECT 才触发 REFUTED 级联 |
| R6 | HTTP 写路径与评审队列 | 唯一带鉴权写端点 `POST /api/review`（roster token、恒时比较、64KB 帽，其余 405）+ `GET /api/review-queue` + **服务端 ReviewBundle View Model**（`GET /api/review-bundle/{id}` 返回视图模型而非 Domain DTO——中文标签映射、渐进披露分层在服务端定型，前端不得直接消费领域对象）+ 评审面板（以 `docs/prototypes/review-console.html` 原型为界面规范）。与 W4-3 服务器整合同步 | R3；与 W4-3 协调 | 4–5 天（含 View Model +1 天） | 无/错 token POST 不改状态；HTTP 与 CLI 产生等价事件与证据；**bundle 端点响应中不出现未映射的后端枚举名**（否定测试） |
| R7 | 实战校准（dogfood） | **先补导入映射层**：`legacy_harness.import_legacy_harness` 返回的是保守导入报告（dict），距"直接回灌成可送审 trace"还差对象/来源/依赖/证据映射（+3–4 天，v1 低估）。之后回灌 arXiv:2607.28557（人核节点 SUPPORTED 不洗白），两名不同组真实评审人对 1–2 个关键引理走完整七步；测量逐义务覆盖率、周转时间、专家抓到的机器盲区失败类数 | R0–R6；招募提前启动 | 1–2 周日历 + 3–4 天映射层 | 一份真实 ReviewRecord 入链；≥1 个专家发现的失败类进入 episode memory 并出现在后续 plan 的强制攻击项 |

**R 轨合计**：约 4–5 个工程周（较 v1 增加：出处/生命周期/通道拆分/
导入映射层）+ 实战校准日历时间。

---

## 2. F 轨：否证优先（轴 1 / W2-2）

| # | 里程碑 | 内容 | 依赖 | 工作量 | 验收标准 |
|---|---|---|---|---|---|
| F0 | KillTestSpec schema | `schema.py`：结构化 kill test（kind ∈ enumeration/property_random/sat_search/instance_eval + 生成器规格 + 机器可判定判别器 + spec 版本摘要）；`ResearchRoute` 增可选 `kill_test_spec`（保留文本兼容） | 无 | 2 天 | round-trip + 未知 kind 拒收 |
| F0.5 | **共享 RouteEvaluationRecord**（新增，R/F/audit/campaign 四方共用） | `schema.py` 新记录：`evaluation_id / route_id / route_revision / claim_id / claim_revision / kill_test_spec_digest / tool_call_id / outcome / tested_scope / witness_artifact_id / verifier_group / replay_command`。**outcome 词汇**：`COUNTEREXAMPLE`（有独立核验反例）/ `PASS_BOUNDED`（在声明范围内未找到反例——确定性方法专用）/ `INCONCLUSIVE`（**`property_random` 未找到反例只能落此档，永不 PASS**；UNKNOWN/超时同此）/ `ERROR`。配套：`ToolCallRecord` 增 `linked_route_ids`，worker 的 `tool_requests` 增可选 `route_id`，campaign 派发时透传 | F0 | 2–3 天 | 随机测试无反例的记录 outcome 恒为 INCONCLUSIVE；audit/R1 消费同一对象（各自实现"已执行"判定的路径不存在） |
| F1 | 编译执行 | 新 `falsification.py`：spec 编译到已有评价器族（sat_search → `smt_universal_no_counterexample`、enumeration/instance_eval → exact_tools），执行后写 RouteEvaluationRecord 并封链 | F0.5 | 3 天 | 带 spec 的路线经 campaign 自动执行并留下可重放的评估记录 |
| F2 | WARNING→硬阻断 | `audit.py` 的"kill test 未执行"升为策略开关下的晋升硬阻断，判定依据 = RouteEvaluationRecord。**与 W2-5 共用的单次改动** | F1 | 1 天 | 无合格评估记录的支持路线使关键 claim 晋升被拒 |
| F3 | 反例→失败级联 | 独立核验的反模型走 **R5 通道③（ClaimCounterexample）** 触发 `record_failure`；路线级失败走通道②。失败类由 spec 声明，默认 FALSE_STATEMENT | F1、R5 通道拆分（可先落通道对象再接 R 轨） | 2 天 | 有界假命题被自动否证且**只杀正确层级**：路线级失败不动 claim，claim 级反例才 REFUTED+级联 |
| F4 | Resolve 侧复用 | 同一引擎作为未来调度器 VALIDITY 层进 W3-7 合成 EDA 演示 | F1–F3；W3 栈 | 随 W3-7 | 演示报告出现"N 个候选在昂贵评价前被否证淘汰"的可追溯记录 |

**F 轨合计**：F0–F3 约 2–2.5 周。产品度量：campaign 报告可统计「错误
候选在进入昂贵评价前被杀死的比例」。

## 3. V 轨：验证器工厂（轴 2 / W2-7 完整版）——**顺序重排**

> v2 重排理由：z3 的 unsat 无独立可查证明对象是**当前已明示的真实
> 信任缺口**（smt_tools 的 limitations 字段所写），DRAT/LRAT 正好关闭
> 它，收益确定，应最先做；而通用分支定界抽象只有 Frankl 一个实例，
> 过早抽象会把问题特定结构错误固化为"通用协议"。

| # | 里程碑 | 内容 | 依赖 | 工作量 | 验收标准 |
|---|---|---|---|---|---|
| V3 | **SAT+DRAT/LRAT 证明对象（前置）** | kissat/cadical + drat-trim/lrat-check 适配器：unsat 第一次有独立可查证明对象；顺带把 ES7 缺失的求解证据入库 | 无 | 4–5 天 | DRAT/LRAT 证明经独立检查器验证后 unsat 才升为可独立重放证据；ES7 目录出现真实证书 |
| V1 | 沙箱合成隔离 | prover worker 在沙箱写问题专用验证器；产出一律钉在 NUMERICAL/TESTED 档（不具 EXACT 资格），来源/prompt/脚本内容寻址 | 闭环（已有） | 3–4 天 | 合成脚本单独存在时其证据不可支撑晋升 |
| V2 | **证书 + 小型可信检查器门**（改写） | **双实现输出一致 = 缺陷探测信号，不 = 数学正确**（可能共同误解规格/漏同一边界/共享训练模式）。EXACT 资格的构成改为：**规范摘要 + 定义好的证书格式 + 一个小型可信检查器**（小到可人工审读，只验证书不重算）**+ statement correspondence + 独立编码复核 + mutation/metamorphic 测试**。跨模型双实现保留为缺陷探测层（比对用**规范化形式**而非字节——两个正确实现可因输出排序不同而字节不同），一致时仅置 `implementation_diversity = true` 标志位，**该标志位永不单独决定 evidence_kind**；提供方多样性计作实现来源多样性，**不自动计作两组独立数学证据** | V1、V3（证书格式范式来自 DRAT 经验） | 1.5 周 | 人为引入单侧 bug 时缺陷探测层报警；**无可信检查器通过时任何双实现一致都无法授予 EXACT**（否定测试）；证书经检查器验证后才入 EXACT 档 |
| V0 | 通用分支定界抽取（**推迟**） | 从 frankl_q6 抽取通用证书化分支定界——**推迟到出现第二个真实使用实例后**再抽象，避免单实例过早泛化 | 第二个真实实例出现 | 1–2 周 | frankl 既有证书经新通用件重放逐字节一致 + 第二实例同时适配 |
| V4 | 旗舰：Frankl 残差层 | 用上述工件 + 闭环攻 `≥4 小外部件` 残差，按**单调残差收缩**口径管理（不承诺定理）；成功=新层证书入库，未成功=残差收缩与失败记录如实入 episode | V3、V1、V2、F 轨 | 2–4 周（研究性） | 两种结果都按红线如实表述 |

## 4. N 轨：负知识资产（轴 3 / W4-1）

| # | 里程碑 | 内容 | 依赖 | 工作量 | 验收标准 |
|---|---|---|---|---|---|
| N0 | 蒸馏器 | `episode_distiller.py`：run 收尾把 FailureRecord/已闭合关键 claim 蒸馏为 DRAFT episode/lesson（人审转正）；R5 的"专家盲区失败类"同管道打标 | 闭环（已有）；R5 增益 | 3 天 | campaign 结束后 memory 出现 DRAFT episode，转正前不参与检索 |
| N0.5 | **增益信号补全**（新增） | campaign 停滞判断目前只看 `weighted_proof_closure`；补全证据增量信号：promoted 数、killed mechanisms、scope narrowed、certificate maturity——这也是 N 轨学习数据的字段基础 | 闭环（已有） | 2 天 | 一轮"杀死一条路线但未晋升任何 claim"的 run 不被误判为无增益 |
| N1 | 版本化导出 | `dataset_export.py`：episodes/sft/eval 三种 JSONL + 摘要清单 + 版本号；schema 天然无 CoT | N0 | 2–3 天 | 两次导出摘要一致；清单校验可发现单字节篡改 |
| N2 | 回填 | Frankl/ES7 实验史 + 本分支真实 campaign run 回填首批资产 | N0–N1 | 2 天 | memory 出现来自自有 run 的 episode（非手工种子） |
| N2.5 | **小型配对回归常态化**（新增） | 从 v0.3-core 第一个 Sprint 起即运行小样本配对对比（带/不带 harness、带/不带记忆），**不等 N3 才第一次比较**；不做优越性宣称（30 对资格门未过），只做内部回归 | 闭环 + compare_agents（已有） | 1 天接线 | 每个 Sprint 产出一份内部配对报告；报告头部印"未过资格门，不得对外引用" |
| N3 | 模型有增益实验（正式） | 预注册 30 对等预算 compare_agents，bootstrap CI 资格门——BP 8–12 月里程碑证据本体 | N1–N2、W4-2 语料 | 实验日历 | 结果无论正负按资格门口径发布 |

## 5. S 轨：认证人审网络（轴 4）与 G 轨：分级担保（轴 5）

- **S 轨**（依赖 R 轨全部；代码少、运营多）：评审人入网包 → SLA 度量
  （从 ReviewRecord 直接算）→ 按送审包计价。评审台原型
  （`docs/prototypes/review-console.html`）作为招募演示材料。
- **G 轨——G0 改为 Assurance Vector（v2 修订）**：单一 L0–L4 标量把
  不完全有序的维度压扁了（"专家完整核验的无限族解析证明" vs
  "仅覆盖 n≤30 的精确枚举"没有天然的高下线序）。改为逐 claim 的
  **担保向量**：

  ```text
  scope:                    bounded | parametric | universal
  evidence_mode:            heuristic | human | exact | formal
  independent_groups:       0 | 1 | 2+
  replayable:               false | true
  statement_correspondence: unchecked | checked
  formalization:            none | partial | full
  human_review:             none | single | double
  object_source_integrity:  incomplete | complete
  freshness:                current | stale
  ```

  再由向量**派生**面向客户的简单标签（探索级 / 机器核验级 / 专家审计级 /
  双重认证级 / 形式化认证级）——商业标签简单，底层语义不压扁。
  机器可判定的维度（scope/evidence_mode/groups/replayable/freshness）
  现在就能落（2–3 天）；human_review 维度待 R4。验收（否定测试）：
  任何派生标签不得高于其向量允许的上限。
- **G1**（1–2 天 + BP 修订）：交付包封面打担保向量与派生标签；对外
  定价表按标签分层。前提：G0 机读标记先在——表述永远不跑在门前面。

---

## 6. 统一排期（v2：垂直切片制，替代六轨并行）

主干 = **一条真实 claim 的完整生命周期**：

```text
proposal → kill test → exact evidence → review bundle → human review
        → promotion / block → memory → cold replay
```

| 阶段 | 内容 | 完成标准（Done） |
|---|---|---|
| **Gate 0** | G0-a 拆除覆写工作流（已完成）；G0-b 本地权威门纪律；G0-c 基线工件 | 覆写隐患不存在；每次推送有本地全绿记录；（G0-d 条件触发不阻塞后续） |
| **v0.3-core**（≈3 周） | F0 → F0.5 共享 RouteEvaluationRecord → F1 → F2 → F3；R5 的三通道对象（可先于 R 轨其余部分落对象层）；V3 SAT/DRAT；N0.5 增益信号；N2.5 配对回归接线 | **两个真实案例**：① 一个假命题被自动精确否证且只杀正确层级（路线级不动 claim）；② 一个真子命题获得可冷重放证据并通过现有晋升门或给出指名到义务的精确 blocker |
| **v0.3-review**（≈3 周） | R0 → R1 → R2 → R3 → R4 → R5 全接通，**只做 CLI，不做 R6 HTTP**；评审人招募启动；R4 参数签字 | 两位真人（不同独立组）用 CLI 完整审一个真实数学 claim：不可变送审包、revision 绑定、对象级冲突检查、REQUEST_CHANGES 回流下一轮、REJECT 不被洗成否证、撤回后证据失效——**先让真人审过一次，再决定服务器界面**（原型 HTML 收集其反馈） |
| **v0.3-learning**（≈2 周） | N0 → N1 → N2；G0 Assurance Vector（含 human 维度）；配对回归持续 | memory 有自有 run 的 episode；版本化数据集可重复导出；每 claim 有担保向量 |
| **v0.4** | R6 HTTP + 评审面板（按原型）；R7 大规模校准（含导入映射层）；S 轨运营；G1 定价；V1→V2 验证器工厂；V0（第二实例后）；V4 旗舰；N3 正式实验 | 各项按本文验收标准 |

**每阶段出口条件**：本地 `make ci` 全绿；本阶段每个新门都有否定测试；
落地状态节如实更新——包括没做成的。

## 7. 风险与前置动作

1. **R4 策略参数是科学标准问题不是工程问题**：先签字后编码。
2. **写路径安全（R6）**：token roster 是 v1；接入外部评审人前必须过
   W5-2 私域治理评审——写端点宁可晚上线，不可裸奔。
3. **V4 不许倒排承诺**：按残差收缩口径管理，失败也是合格产出。
4. **人是长杆**：招募在 v0.3-review 启动时开始；ReviewBundle 必须有
   数学家可读的 HTML 视图（原型已先行）。
5. **两处单点改动去重**：kill-test 硬阻断（F2 vs W2-5）与服务器写基建
   （R6 vs W4-3）各只做一次。
6. **过早抽象风险（v2 新增）**：V0 通用分支定界等第二个真实实例；
   任何"通用协议"必须有 ≥2 个真实消费者才允许抽取。
7. **CI 额度风险（v2 新增）**：额度恢复前所有"全绿"宣称必须标注
   "本地"；恢复后第一件事是 G0-d，而不是继续写功能。

## 附录 A：评审面向文案的硬规范（R2/R6 验收项）

送审给数学家的每一条义务，都必须能被一个不了解本系统内部实现的人读懂。
以下规则对 ReviewBundle 的义务、攻击史、证据摘要一律适用，并应写成
可自动检查的门（R2 验收项之一）：

1. **禁止后端标识符出现在默认视图**：字段名（`new_residual`、
   `non_claims`、`independence_group`）、状态枚举（`FALSIFIED`、
   `ACCEPTED`、`EXACT_COMPUTATION`）、对象 ID（`OBJ-SEMIREG rev.2`）
   一律不得进入义务正文。需要溯源时用自然语言指代（「本结论第 3 版
   正式语句」「本结论声明的『不主张』列表」），标识符本身留在技术详情层。
   自动检查：义务文本对全大写下划线词与已知字段名做正则拒收。
2. **禁止未翻译的外文原文直接嵌入正文**：需要引用英文原句时，正文给
   中文转述，原文放证据区并在 `ref` 里注明「原文为英文，可在证据区查看」。
3. **一条义务 = 一个问题**：`title` 是评审人要回答的那个问题（疑问句或
   判断句，≤20 字）；`ask` 是一句白话说明要做什么；`points[]` 是逐条
   要点，每条只讲一件事。**禁止用分号把三件事挤进一句**。
4. **术语用行内解释代替黑话**：内部术语（kill test、越级、洗白通道、
   钉定、规范形、审计层）在面向评审人的文案里必须换成日常说法
   （廉价测试、把结论说得比实际更强、容易被含糊带过、固定下来、
   整理成同一格式、需要背景时再展开）。
5. **反例与「有界通过」的措辞必须自带边界**：写「在阶数不超过 5 的范围
   里没有找到反例」，不写「kill test 通过」——前者读者自己就能看出
   不可外推，后者需要解释。

反例（本次修订前的真实文本，作为回归用例）：
> 语句对应：非正式语句与证书字段 new_residual（"Any q=6 outside-balance
> counterexample must have at least three small outside parts."）语义一致；
> 「至少三个」与证书中排除 ≤2 的逻辑方向一致。

修订后：
> **白话与机器结论说的是同一件事吗**（必核项）
> 上面那句白话，应当和机器算出的结论指同一件事。请确认转述方向没有说反。
> · 机器给出的结论是：「小外部部件为 0、1、2 个的所有情形都已被排除」。
>   白话说的「至少三个」与它等价——请确认这一步换算方向正确。
> · 机器只处理了 q=6 的情形，白话也必须限定在 q=6。
> *对照对象：证书的结论字段（原文为英文，可在证据区查看）*

## 附：对外部评审意见的采纳说明

- **全盘采纳**：Gate 0（按额度现实分档）、R1 依赖修正与共享
  RouteEvaluationRecord、R0 对象级授权/出处/版本绑定/生命周期、
  R4 逐义务担保、R5 三通道拆分、V2 改写与 V 轨重排、V0 推迟、
  G0 向量化、垂直切片排期、R7 导入工作量修正、N 轨增益信号与
  早期配对回归。
- **调整后采纳**：评审建议"恢复远程 CI 与分支保护"作为 Gate 0——
  因 Actions 额度耗尽暂不可行，改为"本地权威门 + 覆写隐患拆除
  （立即）+ 远程恢复（条件触发）"三档；其中覆写隐患（push 触发的
  载荷物化工作流）是本次核查中新发现并已修复的问题。
- **补充**：评审判断"远程主任务 conclusion=failure 且 steps 为空"
  与额度耗尽的启动层失败一致（engineering-progress.md 早有
  startup_failure 记录），本文按额度耗尽口径表述，未逐一复核每次
  运行的元数据。
