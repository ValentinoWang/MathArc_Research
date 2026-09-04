---
ARTIFACT_CLASS: ssot-development
APPLICABILITY_DECISION: ssot
GOVERNANCE_REASON: "建立数学研究平台（MathArc）原生、可并行、可恢复、可验证、可进行邀请制测试的自主研究运行时，并保持执行状态、候选结果与数学结论权威相互隔离。"
SSOT_DEPTH: L2
TARGET_EVIDENCE_LEVEL: persistent-runtime
PLAN_VERSION: 2
DAG_VERSION: 2
INTERFACE_FREEZE_VERSION: 2
NODE_CONTRACT_VERSION: 2
SSOT_SCHEMA_VERSION: 2
FACTS_REGISTRY_VERSION: 1
VIEW_MODEL_VERSION: 2
SSOT_PLANNING_COMPILER: .ssot/planning-compiler.json
SSOT_MACHINE_SOURCE: .ssot/manifest.json
---

# 任务（matharc-research-runtime-v04）开发 SSOT

## 业务结论与范围

建立数学研究平台（MathArc）原生、可并行、可恢复、可验证、可进行邀请制测试的自主研究运行时，并保持执行状态、候选结果与数学结论权威相互隔离。

## 需要拍板的问题

尚无待拍板问题时在此写明当前没有；有则写入问题记录文件（openproblem.md）并在此引用。

## 发布切片

| Release ID | 用户价值 | 独立失败边界 |
| --- | --- | --- |
| RTRZ | MathArc 自己拥有执行权威、数据合同和运行边界。 | 不启动真实研究；后续运行时切片保持未接受。 |
| RTR1 | 一个数学任务可以从验证、运行到候选回传形成闭环。 | 单任务失败不改变数学工作区，也不产生正式证据。 |
| RTR2 | 单任务运行可以可靠保存、停止、恢复和幂等导入。 | 不确定状态不得猜测完成、重复计费或跳过代际。 |
| RTR3 | 不同研究路线可以在隔离工作区中真实并行执行。 | 单成员失败不破坏整轮，且不得伪造并行证据。 |
| RTR4 | 上一代的失败和研究经历可以改变下一代议程。 | 蒸馏失败或缺少出处时，下一代保持未启动。 |
| RTR5 | 候选结果可以经过独立验证后受控转换为正式证据。 | 运行成功、模型自报或篡改候选都不能成为证明。 |
| RTR6 | 受邀用户可以在有持久运维保障的环境中查看并受控操作研究运行。 | 浏览器不能执行任意命令、目录、环境变量或未登记后端；运维缺口阻断试点。 |
| RTR7 | 真实两代研究和邀请制试点具备可复核发布证据。 | 任一错误晋升、越权动作或不可重放结果阻断试点发布. |

## 节点清单

| Node ID | Goal | Dependencies | Acceptance | Owner |
| --- | --- | --- | --- | --- |
| DOG1 | 固定首个真实任务、评价器、范围、预算和可重放的单成员基线。 | F, DP1, RUN5 | 合同与所需 lane 证据全部接受 | 试点任务负责人 |
| DOG2 | 在运维闭环完成后执行两代真实并行研究并证明第二代消费第一代事实。 | F, DP1, PAR5, SYN5, VER6, DOG1, OPS3 | 合同与所需 lane 证据全部接受 | 真实研究试点负责人 |
| DOG3 | 执行崩溃、篡改、虚假反例、重复导入和权限攻击演练并验证安全恢复。 | F, DP1, DOG2, DUR5, UX6 | 合同与所需 lane 证据全部接受 | 试点攻击演练负责人 |
| DOG4 | 汇编邀请试点的人类验收与发布证据，作出独立发布决策。 | F, DP1, DOG3 | 合同与所需 lane 证据全部接受 | 试点发布负责人 |
| DP1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | F | 合同与所需 lane 证据全部接受 | 决策负责人 |
| DP2 | 首版后端范围固定为 DeterministicTestBackend、CodexBackend 和 LocalExactToolBackend；Claude Code 与通用模型 API 后置，不阻塞首个邀请制试点。 | F | 合同与所需 lane 证据全部接受 | 决策负责人 |
| DP3 | 首版部署目标为 Linux + systemd，使用持久目录、外部 secret source 和反向代理/TLS 边界；生产身份仍需后续部署证据确认。 | F | 合同与所需 lane 证据全部接受 | 决策负责人 |
| DUR1 | 定义冻结输入、代际提交、GenerationReducer 和 GenerationClosePolicy 的持久边界。 | F, DP1, RUN5 | 合同与所需 lane 证据全部接受 | 代际提交负责人 |
| DUR2 | 以带来源身份的幂等账本保存候选、费用和执行回执，拒绝来源漂移。 | F, DP1, DUR1 | 合同与所需 lane 证据全部接受 | 幂等账本负责人 |
| DUR3 | 实现停止、排空、暂停、继续和取消的显式运行状态协议。 | F, DP1, DUR1 | 合同与所需 lane 证据全部接受 | 运行控制负责人 |
| DUR4 | 从最后一个完整 GenerationCommit 生成可重放的崩溃恢复计划。 | F, DP1, DUR2, DUR3 | 合同与所需 lane 证据全部接受 | 恢复负责人 |
| DUR5 | 独立验收冷启动恢复、幂等恢复和不跳代不重复规则。 | F, DP1, DUR4 | 合同与所需 lane 证据全部接受 | 恢复验收负责人 |
| FND1 | 建立 MathArc 原生运行时所有权与依赖允许清单，阻断治理工具链进入产品运行路径。 | F, DP1 | 合同与所需 lane 证据全部接受 | MathArc 运行时架构负责人 |
| FND2 | 保留 ResearchTrace 的数学结论晋升权威，并证明运行状态不能直接变成正式证明。 | F, DP1, FND1 | 合同与所需 lane 证据全部接受 | MathArc 研究协议负责人 |
| OPS1 | 固定试点部署配置、持久目录、密钥来源和进程守护方式。 | F, DP1, DP3, UX6 | 合同与所需 lane 证据全部接受 | 试点部署负责人 |
| OPS2 | 建立健康检查、日志、配额、备份和恢复观测闭环。 | F, DP1, DP3, OPS1 | 合同与所需 lane 证据全部接受 | 试点运维观测负责人 |
| OPS3 | 独立验收部署、重启、回滚和试点用户数据清理。 | F, DP1, DP3, OPS2 | 合同与所需 lane 证据全部接受 | 试点发布运维负责人 |
| PAR1 | 把研究路线和角色编译为带机制、预算、目标和隔离写入区的运行拓扑。 | F, DP1, RUN1 | 合同与所需 lane 证据全部接受 | 研究拓扑负责人 |
| PAR2 | 接入已批准的动态任务并执行一次性、可审计的任务启动。 | F, DP1, PAR1, RUN4 | 合同与所需 lane 证据全部接受 | 任务审批接线负责人 |
| PAR3 | 在持久化和恢复能力之后实现有界并行、冻结输入和隔离工作区调度。 | F, DP1, PAR2, DUR5 | 合同与所需 lane 证据全部接受 | 并发调度负责人 |
| PAR4 | 按执行回执记录实际资源消耗，并对语义重复实验做确定性去重。 | F, DP1, PAR3 | 合同与所需 lane 证据全部接受 | 资源记账负责人 |
| PAR5 | 独立验收多成员一代归并、冲突、部分失败和迟到结果规则。 | F, DP1, PAR4 | 合同与所需 lane 证据全部接受 | 并行验收负责人 |
| RUN1 | 定义可版本化的研究运行合同、身份层级、候选包和运行动作回执。 | F, DP1, FND2 | 合同与所需 lane 证据全部接受 | 运行合同负责人 |
| RUN2 | 建立可重放的运行存储，使事件、快照和候选导入在进程重启后保持一致。 | F, DP1, RUN1 | 合同与所需 lane 证据全部接受 | 运行存储负责人 |
| RUN3 | 建立有预算、种子和最小试跑门槛的评价器合同，失败时不启动完整研究。 | F, DP1, RUN1 | 合同与所需 lane 证据全部接受 | 评价器负责人 |
| RUN4 | 将各类执行后端统一为 MathArc 请求，只返回不可变 WorkerExecutionResult 并由协调器组装候选包。 | F, DP1, DP2, RUN2, RUN3 | 合同与所需 lane 证据全部接受 | 第一方后端负责人 |
| RUN5 | 独立验证单任务从试跑、执行到候选回传的闭环，并阻断候选越级晋升。 | F, DP1, RUN4 | 合同与所需 lane 证据全部接受 | 单任务验收负责人 |
| SYN1 | 把普通执行输出标准化为带完整出处的探索候选，隔离于正式证据。 | F, DP1, RUN5, DUR2 | 合同与所需 lane 证据全部接受 | 探索结果接线负责人 |
| SYN2 | 将疑似反例送入独立复核队列，未复核前不改变研究路线或结论。 | F, DP1, SYN1 | 合同与所需 lane 证据全部接受 | 反例复核负责人 |
| SYN3 | 从真实运行蒸馏带身份和候选出处的研究记忆。 | F, DP1, SYN1 | 合同与所需 lane 证据全部接受 | 研究记忆负责人 |
| SYN4 | 把失败、经历和评审缺口编译为明确消费上一代事实的下一代议程。 | F, DP1, SYN2, SYN3 | 合同与所需 lane 证据全部接受 | 代际议程负责人 |
| SYN5 | 独立验收连续两代提交、路线变化和上一代事实消费。 | F, DP1, SYN4, DUR5, PAR5 | 合同与所需 lane 证据全部接受 | 连续代际验收负责人 |
| UX1 | 把 RuntimeStore 状态投影到现有控制台数据合同，保持单一真相源。 | F, DP1, DUR2 | 合同与所需 lane 证据全部接受 | 控制台投影负责人 |
| UX2 | 复用邀请制 Cookie 会话和权限边界，阻断无权用户的运行动作。 | F, DP1, FND2 | 合同与所需 lane 证据全部接受 | 邀请权限负责人 |
| UX3 | 提供登记动作的幂等运行控制服务，拒绝任意命令、目录、环境和参数。 | F, DP1, UX2, DUR5 | 合同与所需 lane 证据全部接受 | 运行动作 API 负责人 |
| UX4 | 建立统一中文运行视图并递归脱敏密钥、路径、命令、环境变量和堆栈。 | F, DP1, UX1, UX2 | 合同与所需 lane 证据全部接受 | 控制台安全视图负责人 |
| UX5 | 实现断线重连后从服务端快照恢复的实时研究控制台。 | F, DP1, UX3, UX4, VER6 | 合同与所需 lane 证据全部接受 | 实时控制台负责人 |
| UX6 | 独立完成人类浏览器验收，覆盖桌面、移动端、权限负路径和完整操作流。 | F, DP1, UX5 | 合同与所需 lane 证据全部接受 | 浏览器产品验收负责人 |
| VER1 | 定义候选进入验证阶段所需的身份约束和 VerifierReceipt，而非重新定义候选包。 | F, DP1, RUN1, DUR2 | 合同与所需 lane 证据全部接受 | 候选身份负责人 |
| VER2 | 把候选绑定到具体命题、量词、对象和范围，拒绝范围扩大与对象错配。 | F, DP1, VER1 | 合同与所需 lane 证据全部接受 | 命题范围负责人 |
| VER3 | 为候选生成干净环境的独立重放计划，排除同实现自证。 | F, DP1, VER2 | 合同与所需 lane 证据全部接受 | 独立重放负责人 |
| VER4 | 仅将通过 VerifierReceipt 的候选转换为带出处的 EvidenceRecord。 | F, DP1, VER3 | 合同与所需 lane 证据全部接受 | 证据转换负责人 |
| VER5 | 记录命题、源码、评价器或候选身份变化导致的证据失效。 | F, DP1, VER4 | 合同与所需 lane 证据全部接受 | 证据失效负责人 |
| VER6 | 独立验收验证汇合、篡改检测、越界阻断和非独立结果拒绝。 | F, DP1, VER5 | 合同与所需 lane 证据全部接受 | 验证汇合负责人 |

拓扑、逐节点合同与来源登记的投影见伴随视图，不在本文件重复。

## 伴随视图

- 拓扑视图（`generated-views/topology.md`）：依赖边表、文本拓扑图与流程图，以及状态台账、语义节点登记、就绪前沿（跨全部发布切片的全量机器投影）。
- 节点视图（`generated-views/nodes-<release>.md`）：各发布切片的节点合同与状态台账。
- 来源登记视图（`generated-views/source-requirements.md`）：来源覆盖、视觉令牌、锚点与接线（严格来源模式）。

## 事实登记表（Facts Registry）

| 事实类别（Fact category） | 事实键（Fact key） | 登记值（Registered value） | 用途（Usage） |
| --- | --- | --- | --- |
| 路径 | planning-compiler | `.ssot/planning-compiler.json` | 规划编译记录 |
| 路径 | manifest | `.ssot/manifest.json` | SSOT 机器主记录 |
| 路径 | topology-view | `generated-views/topology.md` | 拓扑伴随视图 |
| 路径 | source-requirements-view | `generated-views/source-requirements.md` | 来源覆盖伴随视图 |
| 布局 | ssot-bundle | `agents-results/YYYY-MM-DD/<task-slug>/` | SSOT 项目产物布局 |
