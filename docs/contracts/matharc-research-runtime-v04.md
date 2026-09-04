# MathArc 原生研究运行时 v0.4 产品合同

## 1. 权威边界

MathArc 原生运行时拥有研究运行的执行状态、任务调度、代际提交、恢复计划、候选导入和运行控制权威。数学结论仍只由 `ResearchTrace` 的验证门和晋升方法改变。`RuntimeStore` 保存执行状态，但不得把运行成功、模型自报或候选包直接写成 `PROVED`。

模型 API、Codex、Claude Code 和本地进程都是可替换后端。后端只返回不可变的 `WorkerExecutionResult`，不得直接写共享 `ResearchTrace`、`RuntimeStore` 或数学工作区。

## 2. 运行身份层级

运行身份必须按以下层级区分，并在每个事件、候选和证据回执中保持可追溯：

`workspace_id` → `trace_id` → `runtime_run_id` → `generation_id` → `worker_id` → `execution_id` → `candidate_id` → `evidence_id`。

`runtime_run_id` 是运行时实例身份，不复用既有 `ResearchTrace.run_id` 的语义。身份缺失、跨工作区引用或来源摘要不匹配时，导入和恢复均失败关闭。

## 3. 单任务与后端合同

`RUN1` 定义 `ResearchRunSpec`、`ResearchWorkerSpec`、`WorkerExecutionResult`、`CandidateEnvelope` 和 `RuntimeActionReceipt`。协调器把评价器摘要、运行身份、源码身份、工具注册表摘要、预算和产物摘要组合成 `CandidateEnvelope`；验证阶段只校验其身份约束，不负责第一次定义候选包。

每个运行先经过最小评价器试跑，再启动完整研究。执行请求必须幂等，动作必须带授权主体、目标身份、前置状态和结果回执。后端错误只能形成分类明确的失败结果，不得形成数学证据。

## 4. 冻结输入、并行与归并

每一代开始时生成不可变 `GenerationInputSnapshot`，至少包含 `trace_digest`、`contract_digest`、`agenda_digest`、`worker_spec_digest` 和 `tool_registry_digest`。成员只读取该快照和自己的隔离工作区，不能直接修改共享数学状态。

所有成员先产出不可变 `WorkerExecutionResult`，再由唯一的 `GenerationReducer` 归并。归并器负责稳定排序、冲突检查、重复结果去重、部分失败处理、最低完成成员数、必需角色完成、超时规则、迟到结果归属，并生成不可变 `GenerationCommit`。代际关闭由 `GenerationClosePolicy` 决定；关闭后迟到结果只能进入下一代或待处置队列，不能改写已关闭代际。

稳定排序使用 `(generation_id, worker_id, execution_id, result_digest)`，重复语义实验、重复费用和重复候选导入必须保持零次重复。任何成员都不得成为第二归并者。

## 5. 持久化、生命周期与恢复

运行事件采用哈希链和原子快照，候选、费用和执行回执使用带来源身份的幂等账本。停止、排空、暂停、继续、取消和崩溃恢复都必须经过显式状态转换。恢复只能从最后一个完整 `GenerationCommit` 边界生成，任务、源码、评价器、工具或合同摘要变化时拒绝恢复。

不确定状态不得猜测完成、重复计费、重复执行或跳过代际。恢复计划和恢复结果必须可重放，并保留原始失败分类。

## 6. 数学验证与证据转换

验证器接收 `CandidateEnvelope`，检查任务、源码、评价器、随机种子、预算、产物、命题范围和运行身份约束，并产生 `VerifierReceipt`。只有独立重放和范围检查都通过的候选，才可转换为带出处的 `EvidenceRecord`；转换本身不调用 `ResearchTrace.promote_claim()`。数学晋升继续由既有验证门独占。

## 7. 邀请制控制台与运行操作

邀请制控制台只投影 `RuntimeStore`，通过现有 Cookie 会话和权限边界提供查看、启动、暂停、继续、停止和重新验证动作。服务端只接受登记动作和目标身份，不接受任意命令、工作目录、环境变量、可执行文件或参数。所有敏感字段、主机路径、完整命令和异常堆栈在投影层递归脱敏。

## 8. 试点运行环境

小范围试点必须在 `OPS1`、`OPS2`、`OPS3` 完成后才可进入真实任务：固定部署配置、持久目录、密钥来源和进程守护；健康检查、日志、并发/费用配额、备份与恢复；部署、重启、回滚和用户数据清理验收。`DOG2` 必须依赖 `OPS3`，真实研究使用持久运行时证据，生产发布还需独立发布决策。

## 9. 零容忍不变量

- 错误数学晋升：0
- 重复执行、重复费用、重复候选导入：0
- 跨工作区写入：0
- 已关闭代际被迟到结果改写：0
- 公共接口敏感信息泄露：0
- 无权限运行动作：0

以上不变量由节点级受保护测试、独立验证和试点攻击演练共同证明；任一项不满足即阻断对应发布。
