# 问题情报平面开发计划

```yaml
ARTIFACT_CLASS: ssot-development
APPLICABILITY_DECISION: ssot
GOVERNANCE_REASON: "跨文献资料、问题状态、新颖性审计和分级发布需要长期决策与五个独立发布切片；现行路线图仍是唯一工程权威。"
TARGET_EVIDENCE_LEVEL: source
PLAN_VERSION: 2
DAG_VERSION: 1
INTERFACE_FREEZE_VERSION: 2
NODE_CONTRACT_VERSION: 2
SSOT_SCHEMA_VERSION: 2
SSOT_PLANNING_COMPILER: .ssot/planning-compiler.json
SSOT_MACHINE_SOURCE: .ssot/manifest.json
```

## 一、业务结论与范围

### 术语说明

“问题情报平面”是研究流程中的支持层：它整理公开资料、记录问题在某个时间点的开放状态，并在产生候选结果后单独检查新颖性。它不是证明系统，也不拥有最终数学结论的晋升权。本文所说的“开放”只表示在明确资料范围和观察时间内尚未得到足够反证；它不等于永久证明问题没有答案。

本计划把评审建议收敛成五个可以分别验收、分别停止的发布切片。L1 资料观察合同和 L2 资料导入已实现并完成 A2 验收；后续正式验收仍必须由各自指定负责人完成。计划不改变现有论文准备路线，也不改变正式结论的唯一晋升入口。

本修订版本 2 固定机器源中的两组定义：

1. 四路检索分别是：从正典来源展开前向引用；检索名称、别名和等价表述；按陈述与数学结构做语义检索；以及记录综述、作者、问题源和专家线索。每一路都必须独立保留查询范围、命中和未决项，不能把单一路“没有搜到”当作开放性证明。
2. 三种真实档案分别是：弗兰克尔（Frankl）q=6 问题，用于保留既有覆盖和不作新颖性宣传；数据库标记为开放（open）但文献实际已解决的碰撞题，用于验证状态失效和人工复核；当前确实需要继续研究的问题，用于验证证据不足时不自动升级结论。三例只验证资料、状态和预算闭环，不预先证明开放状态或结果新颖性。

首个目标是形成一条最小的“资料观察—问题状态—新颖性审计—预算授权”链路。它先服务现有的论文准备和资料登记能力，再用一个主题和三份真实档案验证边界。只有回归记录表明流程稳定，才考虑扩大主题数量或增加长期观测。

## 二、用户、角色与受影响行为

### 术语说明

“资料观察”是对论文元数据、版本、许可依据和内容摘要的可追溯记录；“证明证据”是已经通过现有证明门的材料，二者不能互相替代。“问题状态证书”回答目标问题在观察日期的状态；“候选结果新颖性审计”回答本次结果是否已在资料中出现，这两个问题由不同记录和不同人员复核。

| 角色 | 需要完成的工作 | 计划带来的行为变化 |
|---|---|---|
| 研究负责人 | 选择是否启动支持性小切片、确定首个主题、接受发布边界 | 在没有批准前不能把候选方案当作已排期 |
| 研究基础设施负责人 | 建立统一资料观察和受预算约束的导入 | 重复资料只产生可核对的同一记录，新版本保留独立观察 |
| 问题状态负责人 | 维护命题版本、开放状态证书和失效关系 | 命题摘要变化或证书过期会收回相应预算授权 |
| 文献审计负责人 | 执行四条检索路线并复核解决碰撞 | “没有搜到”不能单独成为开放性证明 |
| 主题观测负责人 | 运行一次性同步并整理三份真实档案 | 预算耗尽、游标重跑和高风险事件停在人工通道 |
| 评测负责人 | 建立小型回归集、消融记录和难度量表 | 小样本只报告命中、漏检和人工耗时，不包装成泛化性能 |
| 仓库所有者 | 维护当前路线图和权威文件边界 | 未获批准的支持层不能绕过现行路线图进入主线 |

## 三、明确排除的工作

本计划不包含常驻后台观测程序、多主题抓取、大规模候选池、付费出版社全文自动归档、自动把普通相关文章改写为问题状态、未经校准的统计性能声明，也不包含“已解决”或“已确认新颖性”的宣传。首个主题已接受为并集封闭问题（`union-closed`），但该选择不预先证明开放状态或任何结果的新颖性。

任何实现都不得改写唯一的正式结论晋升入口（`ResearchTrace.promote_claim()`）；资料观察、问题状态和新颖性审计只能提供受限输入或阻塞信号，不能自行制造正式数学结论。

## 四、已接受的人工决定

### 术语说明

这里的“支持性小切片”是把问题情报能力明确登记为现有论文准备和资料登记的辅助发布；它不等于批准完整平台。“首个主题”是一次性观测的范围边界；修订批准记录（`decision.problem-intelligence.amendment@2`）是让后续正式消费者依赖的人工决定。

1. 支持性小切片路线已由研究负责人和仓库所有者接受（`decision.problem-intelligence.activation-route@2`）：范围限于现有论文准备和资料登记，不得绕过现行唯一工程决策入口。该决定供支持性小切片决定节点（`D1`）、修订接受节点（`A1`）及其正式消费者使用。
2. 首个监测主题已由研究负责人接受（`decision.problem-intelligence.first-topic@2`）：采用并集封闭问题，并保留资料范围、预算和不宣称事项；该选择决定检索合同、三种真实档案定义和回归样本，但不预先证明任何结果新颖。该决定供首个主题决定节点（`D2`）、修订接受节点（`A1`）及主题观测切片使用。
3. 当前路线图修订批准记录（`decision.problem-intelligence.amendment@2`）已由研究负责人和仓库所有者接受：它解锁已接受的资料底座和当前问题状态模型节点（`S1`）的正式前沿，但不替代任何后续切片各自的验收。

活动假设（`ASM-ACTIVATION-ROUTE`）仅保留为修订批准前的可撤销隔离草稿历史，不再描述当前主视图的执行资格；所有正式消费者统一绑定修订批准记录（`decision.problem-intelligence.amendment@2`）。

## 五、五个发布切片摘要

| 发布切片 | 业务价值 | 独立验收边界 | 失败时的处理 |
|---|---|---|---|
| `PI-R1` 治理准入与修订 | 明确是否启动支持层、首个主题和负责人 | 权威对账、两个选项和修订决定可追溯 | 未批准则不解锁实现 |
| `PI-R2` 统一文献资料底座 | 让公开资料可去重、可追溯并受预算约束 | 资料观察、开放资料导入和信任门通过专项测试 | 资料停留在待审观察 |
| `PI-R3` 问题状态与新颖性审计 | 分离开放状态与候选结果新颖性 | 状态对象、四路检索和失效规则通过负面测试 | 冻结完整预算和公开定性 |
| `PI-R4` 一次性主题观测与三例档案 | 用一个主题验证重放、恢复、去重和人工闭环 | 同一游标可重放，三种失败模式各有证据 | 进入人工复核，不自动改状态 |
| `PI-R5` 回归集、难度记录与分级披露 | 比较检索路线增量并约束发布措辞 | 小型回归、三张量表和披露模板完成 | 只报告具体命中与缺口 |

## 六、实施路径摘要

先由治理对账确认当前权威边界，再并行形成“是否启动”和“首个主题”两个选项；只有二者都被正式接受，才进入统一资料底座。资料底座验收后建立问题状态与新颖性审计竖切，再运行一次性主题观测和三份真实档案，最后才建立回归集、难度记录和分级披露。每个切片都有独立失败半径，不能把后续切片的完成度倒推为前置切片已获批准。

当前计划状态是“治理已对账、决定版本 2 已接受、L1/L2/A2/S1/S2/A3/T1/T2/A4/R1 已接受；Q1 已解锁，A5 因依赖阻断”。R1 的合同版本 9 已获得两份独立、零写入、持久化通过（`PASS`）的 AI 复审报告，且报告完整性门禁拒绝硬链接和字节相同重放。A5 仅能在 Q1 重新接受后再作仓库源级交付决定；它不构成数学结论、外部状态、新颖性、校准表现或生产发布报告。

## 七、权威边界与剩余不确定性路由

### 输入一致性

| 承诺行为 | 输入位置 | 所属模型或字段 | 进入方式 | 权限或状态依据 | 结论 | 后续动作 | 阻塞决定节点 |
|---|---|---|---|---|---|---|---|
| 新能力必须先服从当前路线图 | `docs/DEV_PATH_V03.md` | v0.3 路线与唯一入口 | 工程规划 | 当前 SSOT 顺序 | 已确认 | 只允许修订后进入 | `A1` |
| 延期发现平面不能直接排期 | `docs/DISCOVERY_PLANE_V04.md` | 延期标记与边界 | 规划对账 | 文档权威 | 已确认 | 作为冲突记录保留 | `D1`、`D2` |
| 统一资料导入复用现有信任门 | `matharc/v02/source_registry.py` | 来源版本与对应关系 | 资料底座 | 既有来源登记 | 已确认 | 作为实现输入 | `L1` |
| 预算沿用现有墙钟和请求边界 | `matharc/v02/budget.py` | 预算记录与停止条件 | 资料导入、主题观测 | 既有预算模块 | 已确认 | 作为实现输入 | `L1` |
| Frankl q=6 不得作为新九元素结果宣传 | 论文准备资料与评审原文 | 精确范围与已知覆盖 | 研究复核 | 新颖性仍开放 | 需要保留限定 | 进入真实档案与审计 | `D2`、`A3` |

### 权威注册表

| 声明或领域 | 权威路径 | 权威层 | 查询方式 | 是否需要修改 | 归属节点 | 验证 |
|---|---|---|---|---|---|---|
| 编排、决定与依赖 | `.ssot/manifest.json` 及其分片 | decision/orchestration | 机器校验器 | 本计划生成 | `CHARTER`、`A1` | 程序校验 |
| 当前工程决策入口 | `docs/DEV_PATH_V03.md` | domain-contract | 版本和内容校验 | 否 | `CHARTER` | 提交身份与 SHA-256 |
| 当前实现状态 | `docs/V03_IMPLEMENTATION_STATUS.md` | domain-contract | 版本和内容校验 | 否 | `F1` | 提交身份与 SHA-256 |
| 延期发现边界 | `docs/DISCOVERY_PLANE_V04.md` | domain-contract | 版本和内容校验 | 否 | `F1` | 提交身份与 SHA-256 |
| 来源信任门 | `matharc/v02/source_registry.py` | domain-contract | 源码阅读与专项测试 | 否 | `L1`、`L2` | 源码身份 |
| 预算边界 | `matharc/v02/budget.py` | domain-contract | 源码阅读与专项测试 | 否 | `L1`、`L2` | 源码身份 |
| 用户评审建议 | 用户提供的评审附件 | research/hypothesis | 人工阅读 | 否 | `F1`、`D1`、`D2` | 仅作为方案输入 |

生成的主视图（Markdown）是机器源的阅读投影；Obsidian 副本只用于审计，不拥有决定权。

### 不确定性路由

| 不确定性 | 分类 | 去向 | 负责人 | 阻塞范围 | 解决证据 |
|---|---|---|---|---|---|
| 支持性小切片路线 | accepted-decision | `openproblem.md` | 研究负责人和仓库所有者 | 已满足 `D1`、`A1` 依赖 | `decision.problem-intelligence.activation-route@2` |
| 首个主题采用并集封闭问题 | accepted-decision | `openproblem.md` | 研究负责人 | 已满足 `D2`、`A1` 依赖 | `decision.problem-intelligence.first-topic@2` |
| 路线图修订 | accepted-decision | `openproblem.md` | 研究负责人和仓库所有者 | 已满足 `A1` 依赖 | `decision.problem-intelligence.amendment@2` |
| 延期文档与现行路线图的优先级 | resolved-authority-conflict | `openproblem.md` 与冲突分片 | 仓库所有者 | 不再阻塞 `D1`、`D2`、`A1` | 当前路线图与 `decision.problem-intelligence.amendment@2` |
| 现有字段和预算实现细节 | discoverable-fact | 节点内有界调查 | 对应负责人 | 不单独阻塞人工决定 | 源码、配置和测试 |
| 真实文献审计样本不足 | evidence-gap | 节点证据台账 | 文献审计负责人 | 只阻塞相应验收声明 | 具体验证记录 |
| 外部检索凭据或服务不可用 | execution-blocker | 节点阻塞台账 | 主题观测负责人 | 只阻塞需要外部访问的动作 | 能力恢复记录 |
| 单次同步出现网络或解析故障 | incident | 运行工作流 | 主题观测负责人 | 只影响当次同步 | 事故与恢复记录 |

## 八、工程执行附录

### 术语说明

本附录中的节点编号、状态、版本和路径是机器合同的精确值。它们只描述执行资格和证据边界，不改变前文的业务决定。机器权威是 `.ssot/manifest.json`、节点分片、边分片、假设分片和冲突分片；本文件由这些记录生成。

### 规划编译身份

```text
planning_compiler_schema_version: 1
ssot_schema_version: 2
machine_validation_profile: release
parallelism_contract_version: 1
execution_contract_validation: strict
main_thread_policy: orchestration-only
main_thread_source_write: false
planning source: .ssot/planning-compiler.json
machine source: .ssot/manifest.json
current project HEAD: 797b20fe91776602037ad22ae667086099def189
```

### 发布、基线与候选

| Macro phase | Release ID | User value | Independent acceptance | Independent failure | Development baseline | Promotion baseline | Release candidate |
|---|---|---|---|---|---|---|---|
| P0 治理准入与事实对账 | PI-R1 | 决定是否启动支持层 | 对账、选项和修订决定 | 未批准即停止 | `git:797b20fe91776602037ad22ae667086099def189` | `main:797b20fe91776602037ad22ae667086099def189` | `candidate:pi-r1-v2` |
| P1 共享文献资料底座 | PI-R2 | 公开资料可追溯导入 | 观察、去重、预算和信任门 | 资料停留待审 | `candidate:pi-r1-v1` | `accepted:pi-r1-v1` | `candidate:pi-r2-v1` |
| P2 问题状态与新颖性审计 | PI-R3 | 状态与新颖性分离 | 四路检索和失效负测 | 冻结完整预算 | `candidate:pi-r2-v1` | `accepted:pi-r2-v1` | `candidate:pi-r3-v1` |
| P3 一次性主题观测 | PI-R4 | 三例真实闭环 | 重放、恢复、去重和人工审计 | 进入人工通道 | `candidate:pi-r3-v1` | `accepted:pi-r3-v1` | `candidate:pi-r4-v1` |
| P4 回归、校准与披露 | PI-R5 | 路线比较与准确发布 | 回归、量表和披露模板 | 只报告具体缺口 | `candidate:pi-r4-v1` | `accepted:pi-r4-v1` | `candidate:pi-r5-v1` |

### 最小节点合同

| Node ID | Goal | Dependencies | Acceptance | Owner |
|---|---|---|---|---|
| `CHARTER` | 确认问题情报能力只能作为当前路线图的修订候选 | 无 | 权威入口、状态和延期边界完成对账 | 仓库所有者 |
| `F1` | 形成权威事实、现有能力和延期边界核对包 | `CHARTER` | 每项事实绑定路径、提交身份和缺口 | 规划编排者 |
| `D1` | 提出支持性小切片路线选项 | `F1` | 选项、代价、停止条件和批准人齐全 | 研究负责人 |
| `D2` | 提出首个监测主题选项 | `F1` | 主题、范围、预算上限和不宣称事项齐全 | 研究负责人 |
| `A1` | 接受或拒绝问题情报修订 | `D1`、`D2` | 研究负责人和仓库所有者共同记录 | 研究负责人和仓库所有者 |
| `L1` | 定义统一文献观察、版本、许可和内容摘要合同 | `A1` | 能区分观察资料与证明证据 | 研究基础设施负责人 |
| `L2` | 复用现有来源登记与预算边界实现开放资料导入 | `L1` | 重复导入幂等，超预算或错误类型停在待审 | 研究基础设施负责人 |
| `A2` | 验收统一文献资料底座 | `L2` | 专项测试和负面路径证据齐全 | 验收负责人 |
| `S1` | 建立命题版本、开放状态证书和问题档案快照关系 | `A2` | 先以三种真实档案定义建立独立纸面 dry-run 夹具；该夹具只校验 S1 合同，不执行或验收后续 `T2`。摘要变化、证书过期和来源缺失使状态失效 | 问题状态负责人 |
| `S2` | 建立独立候选结果新颖性审计与人工入口 | `S1` | 四路结果可分开记录 | 文献审计负责人 |
| `A3` | 验收问题状态与新颖性竖切 | `S2` | 未审计解决声称不能获得完整预算或公开定性 | 验收负责人 |
| `T1` | 实现一次性主题观测、游标恢复和去重 | `A3` | 游标可重放，预算和高风险事件进入人工通道 | 主题观测负责人 |
| `T2` | 用三种真实档案演练资料、状态和预算闭环 | `T1` | 三种档案停在正确审计状态 | 主题观测负责人 |
| `A4` | 验收一次性主题观测和三例真实档案 | `T2` | 重放、恢复、去重和失败模式证据可查 | 验收负责人 |
| `R1` | 建立四条检索路线的回归集和消融记录 | `A4` | 比较路线增量且不包装小样本性能 | 评测负责人 |
| `Q1` | 建立难度量表、实验性预测和分级披露模板 | `R1` | 未校准预测标记为 `UNCALIBRATED` | 研究负责人 |
| `A5` | 作出问题情报平面 v0 发布决定 | `Q1` | 只发布已验收范围并披露限制 | 研究负责人和仓库所有者 |

### 执行波次

| Wave | Release ID | Node IDs | Resource decision |
|---|---|---|---|
| W0 | PI-R1 | `CHARTER` | 共享权威只读 |
| W1 | PI-R1 | `F1` | 共享事实记录唯一写入 |
| W2 | PI-R1 | `D1`、`D2` | 只读事实相同快照，写入区分离 |
| W3 | PI-R1 | `A1` | 人工决定记录串行 |
| W4 | PI-R2 | `L1` | 条件隔离草稿，未批准不可晋升 |
| W5 | PI-R2 | `L2` | 资料底座唯一实现写入 |
| W6 | PI-R2 | `A2` | 证据记录唯一写入 |
| W7 | PI-R3 | `S1` | 状态模型唯一实现写入 |
| W8 | PI-R3 | `S2` | 新颖性审计唯一实现写入 |
| W9 | PI-R3 | `A3` | 验收记录唯一写入 |
| W10 | PI-R4 | `T1` | 同步输出与预算记录隔离 |
| W11 | PI-R4 | `T2` | 三例档案独占主题输出 |
| W12 | PI-R4 | `A4` | 真实档案证据唯一写入 |
| W13 | PI-R5 | `R1` | 回归集唯一实现写入 |
| W14 | PI-R5 | `Q1` | 披露政策唯一写入 |
| W15 | PI-R5 | `A5` | 发布决定串行 |

### 复杂度预算

| Budget | Limit | Actual | Exception authority |
|---|---:|---:|---|
| 总节点数 | 20 | 17 | 规划编排者 |
| 每发布实现节点数 | 3 | 3 | 规划编排者 |
| Codex worker 节点数 | 0 | 0 | 不注册外部 worker |
| 生成视图数 | 1 | 1 | 唯一汇编者 |

### 状态台账

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---:|---|---|---|---|---|
| CHARTER | P0 | 1/1/1/1/2 | ACCEPTED | 0 | 仓库所有者 | EG-PLAN | 无 | source:authority-reconciled | F1 |
| F1 | P0 | 1/1/1/1/2 | ACCEPTED | 0 | 规划编排者 | EG-PLAN | 无 | source:fact-reconciliation | D1,D2 |
| D1 | P0 | 1/1/1/1/2 | ACCEPTED | 0 | 研究负责人 | EG-PLAN | 支持性小切片已批准 | source:decision-accepted | A1 |
| D2 | P0 | 1/1/1/1/2 | ACCEPTED | 0 | 研究负责人 | EG-PLAN | union-closed 已批准 | source:decision-accepted | A1 |
| A1 | P0 | 1/1/1/1/2 | ACCEPTED | 0 | 研究负责人和仓库所有者 | EG-PLAN | revision 2 已批准 | source:decision-accepted | L1 |
| L1 | P1 | 1/1/1/1/2 | ACCEPTED | 0 | 研究基础设施负责人 | EG-PLAN | 用户验收确认 | source:accepted | L2 |
| L2 | P1 | 1/1/1/1/2 | ACCEPTED | 0 | 研究基础设施负责人 | EG-PLAN | 完整性修复后接受 | source:accepted | A2 |
| A2 | P1 | 1/1/1/1/2 | ACCEPTED | 0 | 验收负责人 | EG-PLAN | 用户验收确认，专项负测通过 | source:accepted | S1 |
| S1 | P2 | 1/1/1/1/2 | ACCEPTED | 0 | 问题状态负责人 | EG-PLAN | 三例纸面 dry-run、失效和因果时间负测均通过 | source:accepted | S2 |
| S2 | P2 | 1/1/1/1/2 | ACCEPTED | 0 | 文献审计负责人 | EG-PLAN | 四路独立性、资料读回和时间负测通过 | source:accepted | A3 |
| A3 | P2 | 1/1/1/1/2 | ACCEPTED | 0 | 验收负责人 | EG-PLAN | 未审计结果不得授权的专项证据通过 | source:accepted | T1 |
| T1 | P3 | 1/1/1/1/2 | ACCEPTED | 0 | 主题观测负责人 | EG-PLAN | 游标重放、去重和人工通道专项及独立 AI 复审通过 | source:accepted | T2 |
| T2 | P3 | 1/1/1/1/2 | ACCEPTED | 0 | 主题观测负责人 | EG-PLAN | 三个固定来源档案、重放、预算和人工闭环均通过独立 AI 复审 | source:accepted | A4 |
| A4 | P3 | 1/1/1/1/2 | ACCEPTED | 0 | 验收负责人 | EG-PLAN | 三例档案、重放、恢复、去重和失败模式验收通过 | evidence:A4 | R1 |
| R1 | P4 | 1/1/1/1/2 | ACCEPTED | 0 | 评测负责人 | EG-PLAN | 合同版本 9 的两份独立冻结输入复审与 H-01 已通过 | evidence:R1-accepted-2 | Q1 |
| Q1 | P4 | 1/1/1/1/2 | READY | 1 | 研究负责人 | EG-PLAN | 已由 R1 重新接受解锁，须重新绑定未校准、双轨和禁止公开的专项验收 | evidence:Q1-historical | A5 |
| A5 | P4 | 1/1/1/1/2 | BLOCKED | 0 | 研究负责人和仓库所有者 | EG-PLAN | 等待 Q1 重新接受后重作范围受限的仓库源级发布决定 | evidence:A5-historical | 无 |

### 语义节点登记表

| Task ID | Semantic key | Work kind | Domain lane | Execution state | Decision state | Decision version | Readiness mode | Hard dependencies | Soft dependencies | Assumptions | Decision refs | Invalidation keys | Write authority | Acceptance authority |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CHARTER | decision.problem-intelligence.charter | charter | governance | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | none | none | none | none | decision.problem-intelligence.charter | isolated-record | 仓库所有者 |
| F1 | fact.problem-intelligence.authority-reconciliation | fact-discovery | governance | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | CHARTER | none | none | none | fact.problem-intelligence.authority-reconciliation | isolated-record | 规划编排者 |
| D1 | decision.problem-intelligence.activation-route | decision-acceptance | governance | ACCEPTED | ACCEPTED | 2 | FORMAL | F1 | none | none | none | decision.problem-intelligence.activation-route | isolated-record | 研究负责人 |
| D2 | decision.problem-intelligence.first-topic | decision-acceptance | governance | ACCEPTED | ACCEPTED | 2 | FORMAL | F1 | none | none | none | decision.problem-intelligence.first-topic | isolated-record | 研究负责人 |
| A1 | decision.problem-intelligence.amendment@2 | decision-acceptance | governance | ACCEPTED | ACCEPTED | 2 | FORMAL | D1,D2 | none | none | decision.problem-intelligence.activation-route@2,decision.problem-intelligence.first-topic@2 | decision.problem-intelligence.amendment@2 | isolated-record | 研究负责人和仓库所有者 |
| L1 | contract.problem-intelligence.source-observation | contract-compile | literature | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | A1 | none | none | decision.problem-intelligence.amendment@2 | contract.problem-intelligence.source-observation | isolated-record | 研究基础设施负责人 |
| L2 | implementation.problem-intelligence.literature-base | implementation | literature | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | L1 | none | none | decision.problem-intelligence.amendment@2 | implementation.problem-intelligence.literature-base | implementation | 研究基础设施负责人 |
| A2 | acceptance.problem-intelligence.literature-base | validation | literature | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | L2 | none | none | decision.problem-intelligence.amendment@2 | acceptance.problem-intelligence.literature-base | evidence-only | 验收负责人 |
| S1 | implementation.problem-intelligence.status-model | implementation | problem-status | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | A2 | none | none | decision.problem-intelligence.amendment@2 | implementation.problem-intelligence.status-model | implementation | 问题状态负责人 |
| S2 | implementation.problem-intelligence.novelty-audit | implementation | novelty-audit | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | S1 | none | none | decision.problem-intelligence.amendment@2 | implementation.problem-intelligence.novelty-audit | implementation | 文献审计负责人 |
| A3 | acceptance.problem-intelligence.status-novelty | validation | novelty-audit | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | S2 | none | none | decision.problem-intelligence.amendment@2 | acceptance.problem-intelligence.status-novelty | evidence-only | 验收负责人 |
| T1 | implementation.problem-intelligence.topic-observation | implementation | topic-observation | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | A3 | none | none | decision.problem-intelligence.amendment@2 | implementation.problem-intelligence.topic-observation | implementation | 主题观测负责人 |
| T2 | implementation.problem-intelligence.dogfood-archives | implementation | topic-observation | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | T1 | none | none | decision.problem-intelligence.amendment@2 | implementation.problem-intelligence.dogfood-archives | implementation | 主题观测负责人 |
| A4 | acceptance.problem-intelligence.dogfood | validation | topic-observation | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | T2 | none | none | decision.problem-intelligence.amendment@2 | acceptance.problem-intelligence.dogfood | evidence-only | 验收负责人 |
| R1 | implementation.problem-intelligence.regression | implementation | evaluation | ACCEPTED | NOT_APPLICABLE | n/a | FORMAL | A4 | none | none | decision.problem-intelligence.amendment@2 | implementation.problem-intelligence.regression | implementation | 评测负责人 |
| Q1 | validation.problem-intelligence.calibration-disclosure | validation | evaluation | READY | NOT_APPLICABLE | n/a | FORMAL | R1 | none | none | decision.problem-intelligence.amendment@2 | validation.problem-intelligence.calibration-disclosure | evidence-only | 研究负责人 |
| A5 | release.problem-intelligence.v0 | release-decision | governance | BLOCKED | NOT_APPLICABLE | n/a | FORMAL | Q1 | none | none | decision.problem-intelligence.amendment@2 | release.problem-intelligence.v0 | isolated-record | 研究负责人和仓库所有者 |

### 依赖边表

| From | To | Dependency type | Dependency scope | Required upstream state | Assumption IDs | Invalidation keys | Transferred input | Gate/evidence |
|---|---|---|---|---|---|---|---|---|
| CHARTER | F1 | hard | specific-output | ACCEPTED | none | edge.charter.fact-reconciliation | 已接受的治理准入记录 | CHARTER 范围和权威入口 |
| F1 | D1 | hard | specific-output | ACCEPTED | none | edge.fact-reconciliation.activation-option | 权威事实对账包 | F1 路径、提交身份和缺口 |
| F1 | D2 | hard | specific-output | ACCEPTED | none | edge.fact-reconciliation.topic-option | 权威事实对账包 | F1 路径、提交身份和缺口 |
| D1 | A1 | hard | specific-output | ACCEPTED | none | edge.activation-option.amendment | 支持性小切片路线选项 | D1 选项、代价和停止条件 |
| D2 | A1 | hard | specific-output | ACCEPTED | none | edge.topic-option.amendment | 首个监测主题选项 | D2 主题、范围和预算 |
| A1 | L1 | hard | specific-output | ACCEPTED | none | edge.amendment.source-observation | 已接受的 `decision.problem-intelligence.amendment@2` | A1 决定记录 |
| L1 | L2 | hard | specific-output | ACCEPTED | none | edge.source-observation.literature-base | 冻结的文献观察合同 | L1 字段和边界检查 |
| L2 | A2 | hard | specific-output | ACCEPTED | none | edge.literature-base.literature-acceptance | 导入实现和重放记录 | L2 幂等、预算和类型测试 |
| A2 | S1 | hard | specific-output | ACCEPTED | none | edge.literature-acceptance.status-model | 已验收的资料观察层 | A2 专项测试和负面证据 |
| S1 | S2 | hard | specific-output | ACCEPTED | none | edge.status-model.novelty-audit | 版本化命题和状态对象 | S1 失效规则和关系校验 |
| S2 | A3 | hard | specific-output | ACCEPTED | none | edge.novelty-audit.status-novelty-acceptance | 四路检索结果和人工记录 | S2 对应与权限测试 |
| A3 | T1 | hard | specific-output | ACCEPTED | none | edge.status-novelty.topic-observation | 已验收的状态与新颖性边界 | A3 未审计不得晋升测试 |
| T1 | T2 | hard | specific-output | ACCEPTED | none | edge.topic-observation.dogfood-archives | 可重放的主题观测结果 | T1 游标、预算和去重 |
| T2 | A4 | hard | specific-output | ACCEPTED | none | edge.dogfood-archives.dogfood-acceptance | 三例真实档案及审计结果 | T2 重放、恢复和失败模式 |
| A4 | R1 | hard | specific-output | ACCEPTED | none | edge.dogfood-acceptance.regression | 已验收的真实主题档案 | A4 三例闭环证据 |
| R1 | Q1 | hard | specific-output | pending R1 reacceptance | none | edge.regression.calibration-disclosure | 四路检索回归和消融结果 | R1 样本、增量和缺口 |
| Q1 | A5 | hard | specific-output | pending Q1 reacceptance | none | edge.calibration-disclosure.release | 难度记录、校准状态和披露模板 | Q1 未校准标记和双轨检查 |

### 当前就绪前沿

| Frontier | Task ID | Eligibility | Unsatisfied hard dependencies | Active assumptions | Resource decision |
|---|---|---|---|---|---|
| R1/Q1/A5 | R1 独立复审缺失 | pending | implementation.problem-intelligence.regression | 14/17 已接受；R1 重新验收，Q1/A5 依赖阻断 |

### 波前指标

| Metric | Value | Basis |
|---|---:|---|
| ready-frontier-width | 0 | 没有机器状态为 READY 的节点 |
| formal-ready | 0 | 没有待执行的正式节点 |
| conditional-ready | 0 | 当前没有条件草稿 |
| global-completeness-barriers | 0 | 没有把全局完成度作为普通节点前置条件 |
| critical-path-length | 16 | 显式硬边上的最长节点路径 |
| graph-ready-width | 0 | 没有待执行节点 |
| graph-antichain-width | 2 | 结构分析器计算的最大反链宽度 |
| resource-verified-width | 0 | 没有待执行节点需要资源分配 |

### 叶交付物清单

| Deliverable ID | Parallel batch | Deliverable | Authority write region | Dependencies | Isolation decision | Conflict class | Owning node | Grouping reason |
|---|---|---|---|---|---|---|---|---|
| DL-CHARTER | W0 | 治理准入记录 | artifact:pi-charter-record | none | independent | none | CHARTER | n/a |
| DL-F1 | W1 | 权威事实对账包 | artifact:pi-fact-reconciliation | DL-CHARTER | independent | none | F1 | n/a |
| DL-D1 | W2 | 激活路线选项 | artifact:pi-activation-option | DL-F1 | independent | none | D1 | n/a |
| DL-D2 | W2 | 首个主题选项 | artifact:pi-topic-option | DL-F1 | independent | none | D2 | n/a |
| DL-A1 | W3 | 修订决定记录 | artifact:pi-amendment-decision | DL-D1,DL-D2 | independent | none | A1 | n/a |
| DL-L1 | W4 | 资料观察合同 | artifact:pi-source-observation-contract | DL-A1 | independent | none | L1 | n/a |
| DL-L2 | W5 | 开放资料导入实现 | artifact:pi-literature-base | DL-L1 | independent | none | L2 | n/a |
| DL-A2 | W6 | 资料底座验收证据 | artifact:pi-literature-proof | DL-L2 | independent | none | A2 | n/a |
| DL-S1 | W7 | 问题状态模型 | artifact:pi-status-model | DL-A2 | independent | none | S1 | n/a |
| DL-S2 | W8 | 新颖性审计记录合同 | artifact:pi-novelty-audit | DL-S1 | independent | none | S2 | n/a |
| DL-A3 | W9 | 状态与新颖性验收证据 | artifact:pi-status-novelty-proof | DL-S2 | independent | none | A3 | n/a |
| DL-T1 | W10 | 一次性主题观测实现 | artifact:pi-topic-observation | DL-A3 | independent | none | T1 | n/a |
| DL-T2 | W11 | 三例真实档案 | artifact:pi-dogfood-archives | DL-T1 | independent | none | T2 | n/a |
| DL-A4 | W12 | 主题闭环验收证据 | artifact:pi-dogfood-proof | DL-T2 | independent | none | A4 | n/a |
| DL-R1 | W13 | 回归集与消融记录 | artifact:pi-regression-suite | DL-A4 | independent | none | R1 | n/a |
| DL-Q1 | W14 | 难度与披露政策 | artifact:pi-disclosure-policy | DL-R1 | independent | none | Q1 | n/a |
| DL-A5 | W15 | v0 发布决定 | artifact:pi-release-decision | DL-Q1 | independent | none | A5 | n/a |

### 并行宽度表

| Parallel batch | Leaf deliverables | Independent deliverables | Conflict-grouped deliverables | Logical lane target | Available worker slots | Wave count | Graph ready width | Graph antichain width | Resource-verified width |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| W4-formal-frontier | DL-L1 | 1 | 0 | 1 | 1 | 1 | 2 | 1 |

并行宽度的逻辑目标由独立交付物决定；当前正式前沿是 R1 的两条相互独立的零写入复审。Q1 和 A5 必须等待上游重新验收，不因历史接受记录而越过依赖。

### 假设与冲突登记

| 记录类型 | ID | 状态 | 内容 | 影响范围 | 失效或解决方式 |
|---|---|---|---|---|---|
| assumption | ASM-ACTIVATION-ROUTE | ACTIVE | 可在修订批准前生成只读、可撤销的资料观察隔离草稿 | L1 | D1、D2 和 A1 接受后重算 |
| authority-conflict | C-AUTHORITY-BOUNDARY | OPEN / BLOCKING | 延期发现文档不能越过当前唯一工程决策入口解锁实现 | D1、D2、A1、PI-R1 | 仓库所有者明确权威优先级并关闭冲突 |

### 跨切面适用性表

| Concern | Decision | Owner | Required gate/evidence |
|---|---|---|---|
| Security, authentication, secrets | required | 仓库所有者 | 不把凭据写入命令、日志或资料档案 |
| Privacy, compliance, retention | required | 资料负责人 | 记录许可依据、保留期限和删除边界 |
| Migration, backup, recovery | not-applicable | 研究基础设施负责人 | 当前不做生产数据迁移；若新增迁移必须重新规划 |
| Reliability, rollback, disaster recovery | required | 主题观测负责人 | 一次性同步可重放、可恢复，预算耗尽即停止 |
| Performance and capacity | required | 评测负责人 | 请求、下载、模型令牌和人工分钟数均有预算 |
| Observability and alerting | required | 主题观测负责人 | 保存游标、去重、停止原因和待处置事件 |
| Accessibility and internationalization | not-applicable | 研究负责人 | 当前交付为内部命令和档案，无面向公众页面 |
| Cost and external-service limits | required | 研究基础设施负责人 | arXiv、Crossref、OpenAlex 访问与下载预算 |
| Deployment, readback, monitoring window | not-applicable | 仓库所有者 | 本计划不发布服务、不宣称线上可用 |
| Operational ownership and handoff | required | 仓库所有者 | 每个切片有明确负责人和停止条件 |

### 权威文件外部依赖

| External dependency ID | Authority path | Last-change commit | SHA-256 | Required state | Consumers |
|---|---|---|---|---|---|
| EXT-DEV-PATH | docs/DEV_PATH_V03.md | b3eb7512c5b03a9beb8b0eb5f946597c723d07be | a711ba1292bdbc9a2e312d5c639566d1e176526f9dbe32d55648b4011babb471 | ACCEPTED | CHARTER,F1,D1,D2,A1 |
| EXT-V03-STATUS | docs/V03_IMPLEMENTATION_STATUS.md | b3eb7512c5b03a9beb8b0eb5f946597c723d07be | a2436a810f92ef192ab16ce6e452828998a387e23ad7e294f093b38d80d8012e | ACCEPTED | F1,D1,D2 |
| EXT-DISCOVERY-V04 | docs/DISCOVERY_PLANE_V04.md | 0fb8f15f04451834719c929a264260278e1f6727 | 449aff96d31989e85582c04118541cb24368aae180cb0067c638b18ab6f05143 | ACCEPTED | CHARTER,F1,D1,D2,A1 |
| EXT-SOURCE-REGISTRY | matharc/v02/source_registry.py | 0fb8f15f04451834719c929a264260278e1f6727 | e697f0894d8ac35a19c39ade521a8dfa6d4e42f7c291261a6e0004702c1b3c22 | ACCEPTED | L1,L2 |
| EXT-BUDGET-V02 | matharc/v02/budget.py | 0fb8f15f04451834719c929a264260278e1f6727 | 24f9b7714324a3120c0addefcd391bc4f00000a84c06692875873a7804beec1e | ACCEPTED | L1,L2,T1,R1 |

### 执行合同与 worker 注册

本计划没有实际外部 worker 注册。所有节点由声明的人工负责人执行；`codex-primary` 容量池只用于保持 schema-v2 的路由合同完整，不能解释为已经启动进程。

| Task ID | Transport | Wrapper | Project root | Literal codex exec contract | Sandbox authority | Dispatch state | Return path |
|---|---|---|---|---|---|---|---|
| none | no-worker | n/a | n/a | n/a | no process | NOT_STARTED | n/a |

### 进程预算与清理登记

| Task ID | Worker processes | Retry limit | Stop condition | Cancellation owner | Idempotency key | PID/session | Log path | Exit code |
|---|---:|---:|---|---|---|---|---|---|
| none | 0 | 0 | 不启动外部进程 | 主编排者 | n/a | n/a | n/a | n/a |

| Task ID | Prompt path | Prompt SHA-256 | Launch barrier | Prompt cleanup | Runtime handle cleanup | Codex transcript retention |
|---|---|---|---|---|---|---|
| none | n/a | n/a | 不适用 | 不适用 | 不适用 | 保留既有记录 |

### 全局执行护栏

| Guard ID | Authority basis | Allowed write roots | Forbidden paths | External targets | External side effects | Destructive actions | Secret handling | Baseline | Recovery | Postflight diff | Readback | Rollback condition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EG-PLAN | 用户请求、项目规则和当前唯一路线图 | `agents-results/2026-08-31/problem-intelligence-plane/` | 运行代码、`docs/**`、权威分支、`~/.codex/sessions/`、`~/.codex/archived_sessions/` | 无 | 无；外部资料只允许在获批实现节点按预算读取 | 无 | 凭据不得进入提示、参数、日志或证据 | `git status`、当前 HEAD 和五份文件校验值 | 只保留可撤销隔离草稿；无生产迁移 | 检查仅有任务目录改动 | 本计划只做源文件和机器源核对 | 发现越界写入、权威漂移或决定冲突即停止 |

### 计划版本与局部失效

| Revision | Deviation level | Reason | Changed versions | Affected nodes | Invalidated acceptance/evidence | Nodes to rerun | Approving authority | Timestamp |
|---|---|---|---|---|---|---|---|---|
| 1 | L1 | 从评审建议编译为当前计划；未改变运行代码 | PLAN 1, DAG 1, INTERFACE 1, NODE 1, SSOT 2 | 全部计划节点 | 无既有实现证据 | CHARTER、F1 | 规划编排者 | 2026-08-31 |

| Changed key | Directly affected nodes | Propagation rule |
|---|---|---|
| decision.problem-intelligence.activation-route | D1、A1、L1 及其后继 | 只沿显式边和活动假设传播 |
| decision.problem-intelligence.first-topic | D2、A1、主题观测切片 | 只重算首个主题相关节点 |
| decision.problem-intelligence.amendment@2 | A1 及所有正式消费者 | 版本不匹配时阻塞正式验收 |
| edge.source-observation.literature-base | L1、L2、A2 | 不重置无关切片 |

### 资源与隔离核对

| Resource ID | Type | Canonical path/name | Version/snapshot | Owning node | Access R/W | Isolation key | Conflict decision |
|---|---|---|---|---|---|---|---|
| authority:docs-dev-path-v03 | authority file | docs/DEV_PATH_V03.md | SHA-256 pinned | CHARTER | R | pi-authority | R/R allowed |
| authority:docs-discovery-v04 | authority file | docs/DISCOVERY_PLANE_V04.md | SHA-256 pinned | CHARTER | R | pi-authority | R/R allowed |
| artifact:pi-fact-reconciliation | plan artifact | bundle-local | plan v1 | F1 | W | pi-fact | single writer |
| artifact:pi-activation-option | plan artifact | bundle-local | plan v1 | D1 | W | pi-d1 | independent |
| artifact:pi-topic-option | plan artifact | bundle-local | plan v1 | D2 | W | pi-d2 | independent |
| artifact:pi-amendment-decision | plan artifact | bundle-local | plan v1 | A1 | W | pi-a1 | single writer |
| candidate:pi-r1-v1 | release candidate | bundle-local | candidate v1 | A1 | W | pi-r1 | serialized |

### 证据身份与验收层级

| Evidence ID | Task ID | Evidence level | Source revision | Artifact hashes | Environment | Runtime release | Actor role | Account/tenant | Device/browser | Mock/fixture | Observed at | Acceptance contract |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EV-CHARTER-SOURCE | CHARTER | source | 836dc6860f8f997e4e128bcd745c96b98c6b9b29 | five authority SHA-256 values | local repository | n/a | 仓库所有者 | n/a | n/a | false | 2026-08-31 | CHARTER |
| EV-F1-SOURCE | F1 | source | 836dc6860f8f997e4e128bcd745c96b98c6b9b29 | planning compiler | local repository | n/a | 规划编排者 | n/a | n/a | false | 2026-08-31 | F1 |
| EV-PLAN-STATIC | A1 | static-test | pending checker run | manifest and node hashes | local repository | n/a | 验收负责人 | n/a | n/a | false | pending | PI-R1 |
| EV-PI-FIXTURE | A2 | fixture/mock | not created | pending | isolated fixture | n/a | 验收负责人 | n/a | n/a | true | pending | PI-R2 |

### 验收合同与最终顺序

每个发布切片的终止节点只接受本切片声明的输入。`A1` 只接受两项人工决定；`A2`、`A3`、`A4` 和 `A5` 只接受对应专项证据。最终执行顺序为：CHARTER → F1 → D1 与 D2 → A1 → L1 → L2 → A2 → S1 → S2 → A3 → T1 → T2 → A4 → R1 → Q1 → A5。若任一验收节点失败，只重跑受失效键影响的后继，不把整条路线标记为已完成。

### 清理台账

| Scope | Type | Old or temporary item | Action | May remain | Evidence |
|---|---|---|---|---|---|
| 本任务目录 | temporary planning output | 视图源和生成输出 | 保留并由机器清单校验 | 是，作为当前计划 | renderer 和哈希检查 |
| 运行代码 | legacy interface | 无本次新增接口 | 不修改 | 是，保持现状 | Git diff |
| 资料缓存 | persisted runtime state | 尚未创建 | 不创建常驻缓存 | 否 | 目录清单 |
| 外部 worker | process | 未注册 | 不启动 | 否 | worker ledger 为零 |
| Codex 任务记录 | audit transcript | 既有记录 | 保留，不清理 | 是 | 执行规则 |

### 禁止路径检查

当前没有需要切换的旧消费者，因此不提前禁止兼容路径。计划不新增双写、备用运行路径、常驻 watcher 或把门禁实现成运行时行为；也不复制一份新的来源权威。只有在未来切片完成消费者对账后，才可以由人工决定是否移除兼容接口。

### 最终证据声明

目标证据等级为 `source`。本计划能证明的是：评审建议已经被编译成有明确边界、依赖、人工决定和失败半径的开发 SSOT，并绑定当前权威文件身份。它不能证明任何运行代码、文献抓取、真实主题档案、生产部署、认证角色行为、外部系统回读或物理设备结果。未完成的机器校验、缺少统一 Harness 入口或外部资料访问能力，只阻塞相应验证声明，不得被包装成产品完成。

### ASCII 拓扑图

```text
CHARTER
  |
  v
F1
  +--> D1 --+
  |         |
  +--> D2 --+--> A1 --> L1 --> L2 --> A2 --> S1 --> S2 --> A3
                                                        |
                                                        v
                                      T1 --> T2 --> A4 --> R1 --> Q1 --> A5

D1 与 D2 已接受，`decision.problem-intelligence.amendment@2` 已解锁其正式消费者；S1、S2、A3、T1、T2 和 A4 已接受，R1 正在重新验收，Q1/A5 因硬依赖阻断。
S1 的独立纸面 dry-run 已通过；它不执行或验收后续 T2。所有正式消费者都等待对应的明确接受记录，不等待无关阶段的整体完成。
```

### Mermaid 依赖图

```mermaid
flowchart LR
  CHARTER[CHARTER 治理准入] --> F1[F1 权威事实对账]
  F1 --> D1[D1 激活路线选项]
  F1 --> D2[D2 首个主题选项]
  D1 --> A1[A1 修订接受]
  D2 --> A1
  A1 --> L1[L1 资料观察合同]
  L1 --> L2[L2 资料导入]
  L2 --> A2[A2 资料底座验收]
  A2 --> S1[S1 问题状态]
  S1 --> S2[S2 新颖性审计]
  S2 --> A3[A3 状态与新颖性验收]
  A3 --> T1[T1 一次性主题观测]
  T1 --> T2[T2 三例真实档案]
  T2 --> A4[A4 主题闭环验收]
  A4 --> R1[R1 回归集]
  R1 --> Q1[Q1 难度与披露]
  Q1 --> A5[A5 v0 发布决定]
```

### 结论与当前停止点

当前已接受节点为 D1、D2、A1、L1、L2、A2、S1、S2、A3、T1、T2、A4；R1 必须先获得两份独立 AI 复审的持久化 PASS 证据，Q1/A5 随后按依赖顺序重新验收。A5 的最终范围仍限于已验收的仓库源、测试、SSOT 记录和验收证据；Q1 仍必须保持固定三例、`UNCALIBRATED` 和 `NOT_READY` 的披露政策。不得把本状态标记为部署完成、公开研究结论、数学结论或外部文献确认。
