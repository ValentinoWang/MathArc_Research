### Dependency edge table

| From | To | Dependency type | Dependency scope | Required upstream state | Assumption IDs | Invalidation keys | Transferred input | Gate/evidence |
|---|---|---|---|---|---|---|---|---|
| DOG1 | DOG2 | hard | specific-output | ACCEPTED | none | requirement.dog1 | 固定首个真实任务、评价器、范围、预算和可重放的单成员基线。 | acceptance contract evidence |
| DOG1 | QRTR7 | hard | specific-output | ACCEPTED | none | requirement.dog1 | 固定首个真实任务、评价器、范围、预算和可重放的单成员基线。 | acceptance contract evidence |
| DOG2 | DOG3 | hard | specific-output | ACCEPTED | none | requirement.dog2 | 在运维闭环完成后执行两代真实并行研究并证明第二代消费第一代事实。 | acceptance contract evidence |
| DOG2 | QRTR7 | hard | specific-output | ACCEPTED | none | requirement.dog2 | 在运维闭环完成后执行两代真实并行研究并证明第二代消费第一代事实。 | acceptance contract evidence |
| DOG3 | DOG4 | hard | specific-output | ACCEPTED | none | requirement.dog3 | 执行崩溃、篡改、虚假反例、重复导入和权限攻击演练并验证安全恢复。 | acceptance contract evidence |
| DOG3 | QRTR7 | hard | specific-output | ACCEPTED | none | requirement.dog3 | 执行崩溃、篡改、虚假反例、重复导入和权限攻击演练并验证安全恢复。 | acceptance contract evidence |
| DOG4 | QRTR7 | hard | specific-output | ACCEPTED | none | requirement.dog4 | 汇编邀请试点的人类验收与发布证据，作出独立发布决策。 | acceptance contract evidence |
| DP1 | DOG1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DOG2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DOG3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DOG4 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DUR1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DUR2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DUR3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DUR4 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | DUR5 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | FND1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | FND2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | OPS1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | OPS2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | OPS3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | PAR1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | PAR2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | PAR3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | PAR4 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | PAR5 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | RUN1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | RUN2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | RUN3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | RUN4 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | RUN5 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | SYN1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | SYN2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | SYN3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | SYN4 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | SYN5 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | UX1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | UX2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | UX3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | UX4 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | UX5 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | UX6 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | VER1 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | VER2 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | VER3 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | VER4 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | VER5 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DP1 | VER6 | hard | specific-output | ACCEPTED | none | decision.matharc-native-runtime.v1 | MathArc 原生运行时拥有执行状态和数学权威；GitHub Harness 只提供治理工具链。 | acceptance contract evidence |
| DUR1 | DUR2 | hard | specific-output | ACCEPTED | none | requirement.dur1 | 定义冻结输入、代际提交、GenerationReducer 和 GenerationClosePolicy 的持久边界。 | acceptance contract evidence |
| DUR1 | DUR3 | hard | specific-output | ACCEPTED | none | requirement.dur1 | 定义冻结输入、代际提交、GenerationReducer 和 GenerationClosePolicy 的持久边界。 | acceptance contract evidence |
| DUR1 | QRTR2 | hard | specific-output | ACCEPTED | none | requirement.dur1 | 定义冻结输入、代际提交、GenerationReducer 和 GenerationClosePolicy 的持久边界。 | acceptance contract evidence |
| DUR2 | DUR4 | hard | specific-output | ACCEPTED | none | requirement.dur2 | 以带来源身份的幂等账本保存候选、费用和执行回执，拒绝来源漂移。 | acceptance contract evidence |
| DUR2 | QRTR2 | hard | specific-output | ACCEPTED | none | requirement.dur2 | 以带来源身份的幂等账本保存候选、费用和执行回执，拒绝来源漂移。 | acceptance contract evidence |
| DUR2 | SYN1 | hard | specific-output | ACCEPTED | none | requirement.dur2 | 以带来源身份的幂等账本保存候选、费用和执行回执，拒绝来源漂移。 | acceptance contract evidence |
| DUR2 | UX1 | hard | specific-output | ACCEPTED | none | requirement.dur2 | 以带来源身份的幂等账本保存候选、费用和执行回执，拒绝来源漂移。 | acceptance contract evidence |
| DUR2 | VER1 | hard | specific-output | ACCEPTED | none | requirement.dur2 | 以带来源身份的幂等账本保存候选、费用和执行回执，拒绝来源漂移。 | acceptance contract evidence |
| DUR3 | DUR4 | hard | specific-output | ACCEPTED | none | requirement.dur3 | 实现停止、排空、暂停、继续和取消的显式运行状态协议。 | acceptance contract evidence |
| DUR3 | QRTR2 | hard | specific-output | ACCEPTED | none | requirement.dur3 | 实现停止、排空、暂停、继续和取消的显式运行状态协议。 | acceptance contract evidence |
| DUR4 | DUR5 | hard | specific-output | ACCEPTED | none | requirement.dur4 | 从最后一个完整 GenerationCommit 生成可重放的崩溃恢复计划。 | acceptance contract evidence |
| DUR4 | QRTR2 | hard | specific-output | ACCEPTED | none | requirement.dur4 | 从最后一个完整 GenerationCommit 生成可重放的崩溃恢复计划。 | acceptance contract evidence |
| DUR5 | DOG3 | hard | specific-output | ACCEPTED | none | requirement.dur5 | 独立验收冷启动恢复、幂等恢复和不跳代不重复规则。 | acceptance contract evidence |
| DUR5 | PAR3 | hard | specific-output | ACCEPTED | none | requirement.dur5 | 独立验收冷启动恢复、幂等恢复和不跳代不重复规则。 | acceptance contract evidence |
| DUR5 | QRTR2 | hard | specific-output | ACCEPTED | none | requirement.dur5 | 独立验收冷启动恢复、幂等恢复和不跳代不重复规则。 | acceptance contract evidence |
| DUR5 | SYN5 | hard | specific-output | ACCEPTED | none | requirement.dur5 | 独立验收冷启动恢复、幂等恢复和不跳代不重复规则。 | acceptance contract evidence |
| DUR5 | UX3 | hard | specific-output | ACCEPTED | none | requirement.dur5 | 独立验收冷启动恢复、幂等恢复和不跳代不重复规则。 | acceptance contract evidence |
| F | DOG1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DOG2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DOG3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DOG4 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DP1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DUR1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DUR2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DUR3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DUR4 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | DUR5 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | FND1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | FND2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | OPS1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | OPS2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | OPS3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | PAR1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | PAR2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | PAR3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | PAR4 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | PAR5 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | RUN1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | RUN2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | RUN3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | RUN4 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | RUN5 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | SYN1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | SYN2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | SYN3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | SYN4 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | SYN5 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | UX1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | UX2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | UX3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | UX4 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | UX5 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | UX6 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | VER1 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | VER2 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | VER3 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | VER4 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | VER5 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| F | VER6 | hard | specific-output | ACCEPTED | none | source.identity | Freeze the readable identity of every normative source artifact. | acceptance contract evidence |
| FND1 | FND2 | hard | specific-output | ACCEPTED | none | requirement.fnd1 | 建立 MathArc 原生运行时所有权与依赖允许清单，阻断治理工具链进入产品运行路径。 | acceptance contract evidence |
| FND1 | QRTRZ | hard | specific-output | ACCEPTED | none | requirement.fnd1 | 建立 MathArc 原生运行时所有权与依赖允许清单，阻断治理工具链进入产品运行路径。 | acceptance contract evidence |
| FND2 | QRTRZ | hard | specific-output | ACCEPTED | none | requirement.fnd2 | 保留 ResearchTrace 的数学结论晋升权威，并证明运行状态不能直接变成正式证明。 | acceptance contract evidence |
| FND2 | RUN1 | hard | specific-output | ACCEPTED | none | requirement.fnd2 | 保留 ResearchTrace 的数学结论晋升权威，并证明运行状态不能直接变成正式证明。 | acceptance contract evidence |
| FND2 | UX2 | hard | specific-output | ACCEPTED | none | requirement.fnd2 | 保留 ResearchTrace 的数学结论晋升权威，并证明运行状态不能直接变成正式证明。 | acceptance contract evidence |
| OPS1 | OPS2 | hard | specific-output | ACCEPTED | none | requirement.ops1 | 固定试点部署配置、持久目录、密钥来源和进程守护方式。 | acceptance contract evidence |
| OPS1 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ops1 | 固定试点部署配置、持久目录、密钥来源和进程守护方式。 | acceptance contract evidence |
| OPS2 | OPS3 | hard | specific-output | ACCEPTED | none | requirement.ops2 | 建立健康检查、日志、配额、备份和恢复观测闭环。 | acceptance contract evidence |
| OPS2 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ops2 | 建立健康检查、日志、配额、备份和恢复观测闭环。 | acceptance contract evidence |
| OPS3 | DOG2 | hard | specific-output | ACCEPTED | none | requirement.ops3 | 独立验收部署、重启、回滚和试点用户数据清理。 | acceptance contract evidence |
| OPS3 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ops3 | 独立验收部署、重启、回滚和试点用户数据清理。 | acceptance contract evidence |
| PAR1 | PAR2 | hard | specific-output | ACCEPTED | none | requirement.par1 | 把研究路线和角色编译为带机制、预算、目标和隔离写入区的运行拓扑。 | acceptance contract evidence |
| PAR1 | QRTR3 | hard | specific-output | ACCEPTED | none | requirement.par1 | 把研究路线和角色编译为带机制、预算、目标和隔离写入区的运行拓扑。 | acceptance contract evidence |
| PAR2 | PAR3 | hard | specific-output | ACCEPTED | none | requirement.par2 | 接入已批准的动态任务并执行一次性、可审计的任务启动。 | acceptance contract evidence |
| PAR2 | QRTR3 | hard | specific-output | ACCEPTED | none | requirement.par2 | 接入已批准的动态任务并执行一次性、可审计的任务启动。 | acceptance contract evidence |
| PAR3 | PAR4 | hard | specific-output | ACCEPTED | none | requirement.par3 | 在持久化和恢复能力之后实现有界并行、冻结输入和隔离工作区调度。 | acceptance contract evidence |
| PAR3 | QRTR3 | hard | specific-output | ACCEPTED | none | requirement.par3 | 在持久化和恢复能力之后实现有界并行、冻结输入和隔离工作区调度。 | acceptance contract evidence |
| PAR4 | PAR5 | hard | specific-output | ACCEPTED | none | requirement.par4 | 按执行回执记录实际资源消耗，并对语义重复实验做确定性去重。 | acceptance contract evidence |
| PAR4 | QRTR3 | hard | specific-output | ACCEPTED | none | requirement.par4 | 按执行回执记录实际资源消耗，并对语义重复实验做确定性去重。 | acceptance contract evidence |
| PAR5 | DOG2 | hard | specific-output | ACCEPTED | none | requirement.par5 | 独立验收多成员一代归并、冲突、部分失败和迟到结果规则。 | acceptance contract evidence |
| PAR5 | QRTR3 | hard | specific-output | ACCEPTED | none | requirement.par5 | 独立验收多成员一代归并、冲突、部分失败和迟到结果规则。 | acceptance contract evidence |
| PAR5 | SYN5 | hard | specific-output | ACCEPTED | none | requirement.par5 | 独立验收多成员一代归并、冲突、部分失败和迟到结果规则。 | acceptance contract evidence |
| RUN1 | PAR1 | hard | specific-output | ACCEPTED | none | requirement.run1 | 定义可版本化的研究运行合同、身份层级、候选包和运行动作回执。 | acceptance contract evidence |
| RUN1 | QRTR1 | hard | specific-output | ACCEPTED | none | requirement.run1 | 定义可版本化的研究运行合同、身份层级、候选包和运行动作回执。 | acceptance contract evidence |
| RUN1 | RUN2 | hard | specific-output | ACCEPTED | none | requirement.run1 | 定义可版本化的研究运行合同、身份层级、候选包和运行动作回执。 | acceptance contract evidence |
| RUN1 | RUN3 | hard | specific-output | ACCEPTED | none | requirement.run1 | 定义可版本化的研究运行合同、身份层级、候选包和运行动作回执。 | acceptance contract evidence |
| RUN1 | VER1 | hard | specific-output | ACCEPTED | none | requirement.run1 | 定义可版本化的研究运行合同、身份层级、候选包和运行动作回执。 | acceptance contract evidence |
| RUN2 | QRTR1 | hard | specific-output | ACCEPTED | none | requirement.run2 | 建立可重放的运行存储，使事件、快照和候选导入在进程重启后保持一致。 | acceptance contract evidence |
| RUN2 | RUN4 | hard | specific-output | ACCEPTED | none | requirement.run2 | 建立可重放的运行存储，使事件、快照和候选导入在进程重启后保持一致。 | acceptance contract evidence |
| RUN3 | QRTR1 | hard | specific-output | ACCEPTED | none | requirement.run3 | 建立有预算、种子和最小试跑门槛的评价器合同，失败时不启动完整研究。 | acceptance contract evidence |
| RUN3 | RUN4 | hard | specific-output | ACCEPTED | none | requirement.run3 | 建立有预算、种子和最小试跑门槛的评价器合同，失败时不启动完整研究。 | acceptance contract evidence |
| RUN4 | PAR2 | hard | specific-output | ACCEPTED | none | requirement.run4 | 将各类执行后端统一为 MathArc 请求，只返回不可变 WorkerExecutionResult 并由协调器组装候选包。 | acceptance contract evidence |
| RUN4 | QRTR1 | hard | specific-output | ACCEPTED | none | requirement.run4 | 将各类执行后端统一为 MathArc 请求，只返回不可变 WorkerExecutionResult 并由协调器组装候选包。 | acceptance contract evidence |
| RUN4 | RUN5 | hard | specific-output | ACCEPTED | none | requirement.run4 | 将各类执行后端统一为 MathArc 请求，只返回不可变 WorkerExecutionResult 并由协调器组装候选包。 | acceptance contract evidence |
| RUN5 | DOG1 | hard | specific-output | ACCEPTED | none | requirement.run5 | 独立验证单任务从试跑、执行到候选回传的闭环，并阻断候选越级晋升。 | acceptance contract evidence |
| RUN5 | DUR1 | hard | specific-output | ACCEPTED | none | requirement.run5 | 独立验证单任务从试跑、执行到候选回传的闭环，并阻断候选越级晋升。 | acceptance contract evidence |
| RUN5 | QRTR1 | hard | specific-output | ACCEPTED | none | requirement.run5 | 独立验证单任务从试跑、执行到候选回传的闭环，并阻断候选越级晋升。 | acceptance contract evidence |
| RUN5 | SYN1 | hard | specific-output | ACCEPTED | none | requirement.run5 | 独立验证单任务从试跑、执行到候选回传的闭环，并阻断候选越级晋升。 | acceptance contract evidence |
| S1 | UX6 | hard | specific-output | ACCEPTED | none | write-region.s1 | 可写入区域: acceptance/human/runtime-console/desktop-checklist.md | acceptance contract evidence |
| S10 | RUN4 | hard | specific-output | ACCEPTED | none | write-region.s10 | 可写入区域: matharc/v02/runtime/backends/claude_code.py | acceptance contract evidence |
| S11 | RUN4 | hard | specific-output | ACCEPTED | none | write-region.s11 | 可写入区域: matharc/v02/runtime/backends/codex.py | acceptance contract evidence |
| S12 | RUN4 | hard | specific-output | ACCEPTED | none | write-region.s12 | 可写入区域: matharc/v02/runtime/backends/local_process.py | acceptance contract evidence |
| S13 | RUN4 | hard | specific-output | ACCEPTED | none | write-region.s13 | 可写入区域: matharc/v02/runtime/backends/model_api.py | acceptance contract evidence |
| S14 | DUR2 | hard | specific-output | ACCEPTED | none | write-region.s14 | 可写入区域: matharc/v02/runtime/candidate.py | acceptance contract evidence |
| S14 | SYN1 | hard | specific-output | ACCEPTED | none | write-region.s14 | 可写入区域: matharc/v02/runtime/candidate.py | acceptance contract evidence |
| S14 | VER1 | hard | specific-output | ACCEPTED | none | write-region.s14 | 可写入区域: matharc/v02/runtime/candidate.py | acceptance contract evidence |
| S15 | RUN1 | hard | specific-output | ACCEPTED | none | write-region.s15 | 可写入区域: matharc/v02/runtime/contracts.py | acceptance contract evidence |
| S16 | PAR2 | hard | specific-output | ACCEPTED | none | write-region.s16 | 可写入区域: matharc/v02/runtime/coordinator.py | acceptance contract evidence |
| S16 | PAR4 | hard | specific-output | ACCEPTED | none | write-region.s16 | 可写入区域: matharc/v02/runtime/coordinator.py | acceptance contract evidence |
| S16 | RUN4 | hard | specific-output | ACCEPTED | none | write-region.s16 | 可写入区域: matharc/v02/runtime/coordinator.py | acceptance contract evidence |
| S17 | RUN3 | hard | specific-output | ACCEPTED | none | write-region.s17 | 可写入区域: matharc/v02/runtime/evaluator.py | acceptance contract evidence |
| S18 | DUR1 | hard | specific-output | ACCEPTED | none | write-region.s18 | 可写入区域: matharc/v02/runtime/generation.py | acceptance contract evidence |
| S18 | SYN4 | hard | specific-output | ACCEPTED | none | write-region.s18 | 可写入区域: matharc/v02/runtime/generation.py | acceptance contract evidence |
| S19 | RUN1 | hard | specific-output | ACCEPTED | none | write-region.s19 | 可写入区域: matharc/v02/runtime/identity.py | acceptance contract evidence |
| S2 | DOG4 | hard | specific-output | ACCEPTED | none | write-region.s2 | 可写入区域: acceptance/human/runtime-pilot/release-checklist.md | acceptance contract evidence |
| S20 | DUR4 | hard | specific-output | ACCEPTED | none | write-region.s20 | 可写入区域: matharc/v02/runtime/recovery.py | acceptance contract evidence |
| S21 | DUR1 | hard | specific-output | ACCEPTED | none | write-region.s21 | 可写入区域: matharc/v02/runtime/reducer.py | acceptance contract evidence |
| S21 | SYN3 | hard | specific-output | ACCEPTED | none | write-region.s21 | 可写入区域: matharc/v02/runtime/reducer.py | acceptance contract evidence |
| S22 | DUR2 | hard | specific-output | ACCEPTED | none | write-region.s22 | 可写入区域: matharc/v02/runtime/run_store.py | acceptance contract evidence |
| S22 | RUN2 | hard | specific-output | ACCEPTED | none | write-region.s22 | 可写入区域: matharc/v02/runtime/run_store.py | acceptance contract evidence |
| S23 | PAR3 | hard | specific-output | ACCEPTED | none | write-region.s23 | 可写入区域: matharc/v02/runtime/scheduler.py | acceptance contract evidence |
| S24 | UX2 | hard | specific-output | ACCEPTED | none | write-region.s24 | 可写入区域: matharc/v02/runtime/service.py | acceptance contract evidence |
| S24 | UX3 | hard | specific-output | ACCEPTED | none | write-region.s24 | 可写入区域: matharc/v02/runtime/service.py | acceptance contract evidence |
| S24 | UX5 | hard | specific-output | ACCEPTED | none | write-region.s24 | 可写入区域: matharc/v02/runtime/service.py | acceptance contract evidence |
| S25 | DUR3 | hard | specific-output | ACCEPTED | none | write-region.s25 | 可写入区域: matharc/v02/runtime/state_machine.py | acceptance contract evidence |
| S26 | SYN1 | hard | specific-output | ACCEPTED | none | write-region.s26 | 可写入区域: matharc/v02/runtime/synthesis.py | acceptance contract evidence |
| S26 | SYN2 | hard | specific-output | ACCEPTED | none | write-region.s26 | 可写入区域: matharc/v02/runtime/synthesis.py | acceptance contract evidence |
| S27 | PAR1 | hard | specific-output | ACCEPTED | none | write-region.s27 | 可写入区域: matharc/v02/runtime/topology.py | acceptance contract evidence |
| S28 | VER1 | hard | specific-output | ACCEPTED | none | write-region.s28 | 可写入区域: matharc/v02/runtime/verification.py | acceptance contract evidence |
| S28 | VER2 | hard | specific-output | ACCEPTED | none | write-region.s28 | 可写入区域: matharc/v02/runtime/verification.py | acceptance contract evidence |
| S28 | VER3 | hard | specific-output | ACCEPTED | none | write-region.s28 | 可写入区域: matharc/v02/runtime/verification.py | acceptance contract evidence |
| S28 | VER4 | hard | specific-output | ACCEPTED | none | write-region.s28 | 可写入区域: matharc/v02/runtime/verification.py | acceptance contract evidence |
| S28 | VER5 | hard | specific-output | ACCEPTED | none | write-region.s28 | 可写入区域: matharc/v02/runtime/verification.py | acceptance contract evidence |
| S29 | UX1 | hard | specific-output | ACCEPTED | none | write-region.s29 | 可写入区域: matharc/v02/runtime/view_model.py | acceptance contract evidence |
| S29 | UX4 | hard | specific-output | ACCEPTED | none | write-region.s29 | 可写入区域: matharc/v02/runtime/view_model.py | acceptance contract evidence |
| S29 | UX5 | hard | specific-output | ACCEPTED | none | write-region.s29 | 可写入区域: matharc/v02/runtime/view_model.py | acceptance contract evidence |
| S3 | OPS3 | hard | specific-output | ACCEPTED | none | write-region.s3 | 可写入区域: acceptance/runtime-pilot/ops-checklist.md | acceptance contract evidence |
| S30 | FND1 | hard | specific-output | ACCEPTED | none | write-region.s30 | 可写入区域: scripts/check_runtime_dependency_allowlist.py | acceptance contract evidence |
| S31 | FND1 | hard | specific-output | ACCEPTED | none | write-region.s31 | 可写入区域: scripts/check_runtime_ownership.py | acceptance contract evidence |
| S32 | VER4 | hard | specific-output | ACCEPTED | none | write-region.s32 | 可写入区域: tests/test_candidate_evidence_conversion.py | acceptance contract evidence |
| S33 | VER1 | hard | specific-output | ACCEPTED | none | write-region.s33 | 可写入区域: tests/test_candidate_identity.py | acceptance contract evidence |
| S34 | VER3 | hard | specific-output | ACCEPTED | none | write-region.s34 | 可写入区域: tests/test_candidate_independent_replay.py | acceptance contract evidence |
| S35 | RUN5 | hard | specific-output | ACCEPTED | none | write-region.s35 | 可写入区域: tests/test_candidate_promotion_boundary.py | acceptance contract evidence |
| S36 | VER2 | hard | specific-output | ACCEPTED | none | write-region.s36 | 可写入区域: tests/test_candidate_scope_binding.py | acceptance contract evidence |
| S37 | VER5 | hard | specific-output | ACCEPTED | none | write-region.s37 | 可写入区域: tests/test_evidence_invalidation.py | acceptance contract evidence |
| S38 | DUR1 | hard | specific-output | ACCEPTED | none | write-region.s38 | 可写入区域: tests/test_generation_commit.py | acceptance contract evidence |
| S39 | DUR1 | hard | specific-output | ACCEPTED | none | write-region.s39 | 可写入区域: tests/test_generation_input_snapshot.py | acceptance contract evidence |
| S4 | DOG4 | hard | specific-output | ACCEPTED | none | write-region.s4 | 可写入区域: acceptance/runtime-pilot/release-evidence.json | acceptance contract evidence |
| S40 | DOG3 | hard | specific-output | ACCEPTED | none | write-region.s40 | 可写入区域: tests/test_runtime_adversarial_drills.py | acceptance contract evidence |
| S41 | PAR2 | hard | specific-output | ACCEPTED | none | write-region.s41 | 可写入区域: tests/test_runtime_approved_task_ingestion.py | acceptance contract evidence |
| S42 | DOG3 | hard | specific-output | ACCEPTED | none | write-region.s42 | 可写入区域: tests/test_runtime_attack_recovery.py | acceptance contract evidence |
| S43 | FND2 | hard | specific-output | ACCEPTED | none | write-region.s43 | 可写入区域: tests/test_runtime_authority_boundaries.py | acceptance contract evidence |
| S44 | RUN4 | hard | specific-output | ACCEPTED | none | write-region.s44 | 可写入区域: tests/test_runtime_backend_contract.py | acceptance contract evidence |
| S45 | SYN1 | hard | specific-output | ACCEPTED | none | write-region.s45 | 可写入区域: tests/test_runtime_candidate_synthesis.py | acceptance contract evidence |
| S46 | UX3 | hard | specific-output | ACCEPTED | none | write-region.s46 | 可写入区域: tests/test_runtime_command_surface.py | acceptance contract evidence |
| S47 | UX6 | hard | specific-output | ACCEPTED | none | write-region.s47 | 可写入区域: tests/test_runtime_console_mobile.py | acceptance contract evidence |
| S48 | UX2 | hard | specific-output | ACCEPTED | none | write-region.s48 | 可写入区域: tests/test_runtime_console_permissions.py | acceptance contract evidence |
| S49 | UX1 | hard | specific-output | ACCEPTED | none | write-region.s49 | 可写入区域: tests/test_runtime_console_projection.py | acceptance contract evidence |
| S5 | DOG1 | hard | specific-output | ACCEPTED | none | write-region.s5 | 可写入区域: benchmarks/runtime-pilot-plan.json | acceptance contract evidence |
| S50 | UX5 | hard | specific-output | ACCEPTED | none | write-region.s50 | 可写入区域: tests/test_runtime_console_reconnect.py | acceptance contract evidence |
| S51 | UX4 | hard | specific-output | ACCEPTED | none | write-region.s51 | 可写入区域: tests/test_runtime_console_redaction.py | acceptance contract evidence |
| S52 | RUN1 | hard | specific-output | ACCEPTED | none | write-region.s52 | 可写入区域: tests/test_runtime_contracts.py | acceptance contract evidence |
| S53 | SYN2 | hard | specific-output | ACCEPTED | none | write-region.s53 | 可写入区域: tests/test_runtime_counterexample_review.py | acceptance contract evidence |
| S54 | DUR5 | hard | specific-output | ACCEPTED | none | write-region.s54 | 可写入区域: tests/test_runtime_crash_recovery.py | acceptance contract evidence |
| S55 | FND1 | hard | specific-output | ACCEPTED | none | write-region.s55 | 可写入区域: tests/test_runtime_dependency_allowlist.py | acceptance contract evidence |
| S56 | RUN3 | hard | specific-output | ACCEPTED | none | write-region.s56 | 可写入区域: tests/test_runtime_evaluator.py | acceptance contract evidence |
| S57 | SYN5 | hard | specific-output | ACCEPTED | none | write-region.s57 | 可写入区域: tests/test_runtime_generation_delta.py | acceptance contract evidence |
| S58 | DUR2 | hard | specific-output | ACCEPTED | none | write-region.s58 | 可写入区域: tests/test_runtime_idempotent_import.py | acceptance contract evidence |
| S59 | RUN1 | hard | specific-output | ACCEPTED | none | write-region.s59 | 可写入区域: tests/test_runtime_identity.py | acceptance contract evidence |
| S6 | OPS1 | hard | specific-output | ACCEPTED | none | write-region.s6 | 可写入区域: deploy/matharc-research.env.example | acceptance contract evidence |
| S60 | PAR5 | hard | specific-output | ACCEPTED | none | write-region.s60 | 可写入区域: tests/test_runtime_late_result_policy.py | acceptance contract evidence |
| S61 | DUR3 | hard | specific-output | ACCEPTED | none | write-region.s61 | 可写入区域: tests/test_runtime_lifecycle_control.py | acceptance contract evidence |
| S62 | SYN3 | hard | specific-output | ACCEPTED | none | write-region.s62 | 可写入区域: tests/test_runtime_memory_provenance.py | acceptance contract evidence |
| S63 | SYN4 | hard | specific-output | ACCEPTED | none | write-region.s63 | 可写入区域: tests/test_runtime_next_generation_agenda.py | acceptance contract evidence |
| S64 | DUR5 | hard | specific-output | ACCEPTED | none | write-region.s64 | 可写入区域: tests/test_runtime_no_duplicate_recovery.py | acceptance contract evidence |
| S65 | OPS2 | hard | specific-output | ACCEPTED | none | write-region.s65 | 可写入区域: tests/test_runtime_ops_backup.py | acceptance contract evidence |
| S66 | OPS3 | hard | specific-output | ACCEPTED | none | write-region.s66 | 可写入区域: tests/test_runtime_ops_cleanup.py | acceptance contract evidence |
| S67 | OPS1 | hard | specific-output | ACCEPTED | none | write-region.s67 | 可写入区域: tests/test_runtime_ops_deployment.py | acceptance contract evidence |
| S68 | OPS2 | hard | specific-output | ACCEPTED | none | write-region.s68 | 可写入区域: tests/test_runtime_ops_observability.py | acceptance contract evidence |
| S69 | OPS3 | hard | specific-output | ACCEPTED | none | write-region.s69 | 可写入区域: tests/test_runtime_ops_release.py | acceptance contract evidence |
| S7 | OPS1 | hard | specific-output | ACCEPTED | none | write-region.s7 | 可写入区域: deploy/matharc-research.service | acceptance contract evidence |
| S70 | FND1 | hard | specific-output | ACCEPTED | none | write-region.s70 | 可写入区域: tests/test_runtime_ownership.py | acceptance contract evidence |
| S71 | PAR5 | hard | specific-output | ACCEPTED | none | write-region.s71 | 可写入区域: tests/test_runtime_parallel_generation.py | acceptance contract evidence |
| S72 | PAR3 | hard | specific-output | ACCEPTED | none | write-region.s72 | 可写入区域: tests/test_runtime_parallelism.py | acceptance contract evidence |
| S73 | PAR5 | hard | specific-output | ACCEPTED | none | write-region.s73 | 可写入区域: tests/test_runtime_partial_failure.py | acceptance contract evidence |
| S74 | DOG1 | hard | specific-output | ACCEPTED | none | write-region.s74 | 可写入区域: tests/test_runtime_pilot_baseline.py | acceptance contract evidence |
| S75 | DOG2 | hard | specific-output | ACCEPTED | none | write-region.s75 | 可写入区域: tests/test_runtime_pilot_generation_consumption.py | acceptance contract evidence |
| S76 | DUR4 | hard | specific-output | ACCEPTED | none | write-region.s76 | 可写入区域: tests/test_runtime_recovery_plan.py | acceptance contract evidence |
| S77 | PAR4 | hard | specific-output | ACCEPTED | none | write-region.s77 | 可写入区域: tests/test_runtime_semantic_deduplication.py | acceptance contract evidence |
| S78 | RUN5 | hard | specific-output | ACCEPTED | none | write-region.s78 | 可写入区域: tests/test_runtime_single_run.py | acceptance contract evidence |
| S79 | RUN2 | hard | specific-output | ACCEPTED | none | write-region.s79 | 可写入区域: tests/test_runtime_store_replay.py | acceptance contract evidence |
| S8 | DOG2 | hard | specific-output | ACCEPTED | none | write-region.s8 | 可写入区域: experiments/runtime-pilot/two-generation-report.md | acceptance contract evidence |
| S80 | PAR1 | hard | specific-output | ACCEPTED | none | write-region.s80 | 可写入区域: tests/test_runtime_topology.py | acceptance contract evidence |
| S81 | SYN5 | hard | specific-output | ACCEPTED | none | write-region.s81 | 可写入区域: tests/test_runtime_two_generation_synthesis.py | acceptance contract evidence |
| S82 | VER6 | hard | specific-output | ACCEPTED | none | write-region.s82 | 可写入区域: tests/test_verification_convergence.py | acceptance contract evidence |
| S83 | VER6 | hard | specific-output | ACCEPTED | none | write-region.s83 | 可写入区域: tests/test_verification_negative_paths.py | acceptance contract evidence |
| S9 | RUN4 | hard | specific-output | ACCEPTED | none | write-region.s9 | 可写入区域: matharc/v02/runtime/backends/base.py | acceptance contract evidence |
| SYN1 | QRTR4 | hard | specific-output | ACCEPTED | none | requirement.syn1 | 把普通执行输出标准化为带完整出处的探索候选，隔离于正式证据。 | acceptance contract evidence |
| SYN1 | SYN2 | hard | specific-output | ACCEPTED | none | requirement.syn1 | 把普通执行输出标准化为带完整出处的探索候选，隔离于正式证据。 | acceptance contract evidence |
| SYN1 | SYN3 | hard | specific-output | ACCEPTED | none | requirement.syn1 | 把普通执行输出标准化为带完整出处的探索候选，隔离于正式证据。 | acceptance contract evidence |
| SYN2 | QRTR4 | hard | specific-output | ACCEPTED | none | requirement.syn2 | 将疑似反例送入独立复核队列，未复核前不改变研究路线或结论。 | acceptance contract evidence |
| SYN2 | SYN4 | hard | specific-output | ACCEPTED | none | requirement.syn2 | 将疑似反例送入独立复核队列，未复核前不改变研究路线或结论。 | acceptance contract evidence |
| SYN3 | QRTR4 | hard | specific-output | ACCEPTED | none | requirement.syn3 | 从真实运行蒸馏带身份和候选出处的研究记忆。 | acceptance contract evidence |
| SYN3 | SYN4 | hard | specific-output | ACCEPTED | none | requirement.syn3 | 从真实运行蒸馏带身份和候选出处的研究记忆。 | acceptance contract evidence |
| SYN4 | QRTR4 | hard | specific-output | ACCEPTED | none | requirement.syn4 | 把失败、经历和评审缺口编译为明确消费上一代事实的下一代议程。 | acceptance contract evidence |
| SYN4 | SYN5 | hard | specific-output | ACCEPTED | none | requirement.syn4 | 把失败、经历和评审缺口编译为明确消费上一代事实的下一代议程。 | acceptance contract evidence |
| SYN5 | DOG2 | hard | specific-output | ACCEPTED | none | requirement.syn5 | 独立验收连续两代提交、路线变化和上一代事实消费。 | acceptance contract evidence |
| SYN5 | QRTR4 | hard | specific-output | ACCEPTED | none | requirement.syn5 | 独立验收连续两代提交、路线变化和上一代事实消费。 | acceptance contract evidence |
| UX1 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ux1 | 把 RuntimeStore 状态投影到现有控制台数据合同，保持单一真相源。 | acceptance contract evidence |
| UX1 | UX4 | hard | specific-output | ACCEPTED | none | requirement.ux1 | 把 RuntimeStore 状态投影到现有控制台数据合同，保持单一真相源。 | acceptance contract evidence |
| UX2 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ux2 | 复用邀请制 Cookie 会话和权限边界，阻断无权用户的运行动作。 | acceptance contract evidence |
| UX2 | UX3 | hard | specific-output | ACCEPTED | none | requirement.ux2 | 复用邀请制 Cookie 会话和权限边界，阻断无权用户的运行动作。 | acceptance contract evidence |
| UX2 | UX4 | hard | specific-output | ACCEPTED | none | requirement.ux2 | 复用邀请制 Cookie 会话和权限边界，阻断无权用户的运行动作。 | acceptance contract evidence |
| UX3 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ux3 | 提供登记动作的幂等运行控制服务，拒绝任意命令、目录、环境和参数。 | acceptance contract evidence |
| UX3 | UX5 | hard | specific-output | ACCEPTED | none | requirement.ux3 | 提供登记动作的幂等运行控制服务，拒绝任意命令、目录、环境和参数。 | acceptance contract evidence |
| UX4 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ux4 | 建立统一中文运行视图并递归脱敏密钥、路径、命令、环境变量和堆栈。 | acceptance contract evidence |
| UX4 | UX5 | hard | specific-output | ACCEPTED | none | requirement.ux4 | 建立统一中文运行视图并递归脱敏密钥、路径、命令、环境变量和堆栈。 | acceptance contract evidence |
| UX5 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ux5 | 实现断线重连后从服务端快照恢复的实时研究控制台。 | acceptance contract evidence |
| UX5 | UX6 | hard | specific-output | ACCEPTED | none | requirement.ux5 | 实现断线重连后从服务端快照恢复的实时研究控制台。 | acceptance contract evidence |
| UX6 | DOG3 | hard | specific-output | ACCEPTED | none | requirement.ux6 | 独立完成人类浏览器验收，覆盖桌面、移动端、权限负路径和完整操作流。 | acceptance contract evidence |
| UX6 | OPS1 | hard | specific-output | ACCEPTED | none | requirement.ux6 | 独立完成人类浏览器验收，覆盖桌面、移动端、权限负路径和完整操作流。 | acceptance contract evidence |
| UX6 | QRTR6 | hard | specific-output | ACCEPTED | none | requirement.ux6 | 独立完成人类浏览器验收，覆盖桌面、移动端、权限负路径和完整操作流。 | acceptance contract evidence |
| VER1 | QRTR5 | hard | specific-output | ACCEPTED | none | requirement.ver1 | 定义候选进入验证阶段所需的身份约束和 VerifierReceipt，而非重新定义候选包。 | acceptance contract evidence |
| VER1 | VER2 | hard | specific-output | ACCEPTED | none | requirement.ver1 | 定义候选进入验证阶段所需的身份约束和 VerifierReceipt，而非重新定义候选包。 | acceptance contract evidence |
| VER2 | QRTR5 | hard | specific-output | ACCEPTED | none | requirement.ver2 | 把候选绑定到具体命题、量词、对象和范围，拒绝范围扩大与对象错配。 | acceptance contract evidence |
| VER2 | VER3 | hard | specific-output | ACCEPTED | none | requirement.ver2 | 把候选绑定到具体命题、量词、对象和范围，拒绝范围扩大与对象错配。 | acceptance contract evidence |
| VER3 | QRTR5 | hard | specific-output | ACCEPTED | none | requirement.ver3 | 为候选生成干净环境的独立重放计划，排除同实现自证。 | acceptance contract evidence |
| VER3 | VER4 | hard | specific-output | ACCEPTED | none | requirement.ver3 | 为候选生成干净环境的独立重放计划，排除同实现自证。 | acceptance contract evidence |
| VER4 | QRTR5 | hard | specific-output | ACCEPTED | none | requirement.ver4 | 仅将通过 VerifierReceipt 的候选转换为带出处的 EvidenceRecord。 | acceptance contract evidence |
| VER4 | VER5 | hard | specific-output | ACCEPTED | none | requirement.ver4 | 仅将通过 VerifierReceipt 的候选转换为带出处的 EvidenceRecord。 | acceptance contract evidence |
| VER5 | QRTR5 | hard | specific-output | ACCEPTED | none | requirement.ver5 | 记录命题、源码、评价器或候选身份变化导致的证据失效。 | acceptance contract evidence |
| VER5 | VER6 | hard | specific-output | ACCEPTED | none | requirement.ver5 | 记录命题、源码、评价器或候选身份变化导致的证据失效。 | acceptance contract evidence |
| VER6 | DOG2 | hard | specific-output | ACCEPTED | none | requirement.ver6 | 独立验收验证汇合、篡改检测、越界阻断和非独立结果拒绝。 | acceptance contract evidence |
| VER6 | QRTR5 | hard | specific-output | ACCEPTED | none | requirement.ver6 | 独立验收验证汇合、篡改检测、越界阻断和非独立结果拒绝。 | acceptance contract evidence |
| VER6 | UX5 | hard | specific-output | ACCEPTED | none | requirement.ver6 | 独立验收验证汇合、篡改检测、越界阻断和非独立结果拒绝。 | acceptance contract evidence |

### ASCII topology graph

```text
Layer 0: F, S1, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S2, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S3, S30, S31, S32, S33, S34, S35, S36, S37, S38, S39, S4, S40, S41, S42, S43, S44, S45, S46, S47, S48, S49, S5, S50, S51, S52, S53, S54, S55, S56, S57, S58, S59, S6, S60, S61, S62, S63, S64, S65, S66, S67, S68, S69, S7, S70, S71, S72, S73, S74, S75, S76, S77, S78, S79, S8, S80, S81, S82, S83, S9
Layer 1: DP1
Layer 2: FND1
Layer 3: FND2
Layer 4: QRTRZ, RUN1, UX2
Layer 5: PAR1, RUN2, RUN3
Layer 6: RUN4
Layer 7: PAR2, RUN5
Layer 8: DOG1, DUR1, QRTR1
Layer 9: DUR2, DUR3
Layer 10: DUR4, SYN1, UX1, VER1
Layer 11: DUR5, SYN2, SYN3, UX4, VER2
Layer 12: PAR3, QRTR2, SYN4, UX3, VER3
Layer 13: PAR4, VER4
Layer 14: PAR5, VER5
Layer 15: QRTR3, SYN5, VER6
Layer 16: QRTR4, QRTR5, UX5
Layer 17: UX6
Layer 18: OPS1
Layer 19: OPS2
Layer 20: OPS3
Layer 21: DOG2, QRTR6
Layer 22: DOG3
Layer 23: DOG4
Layer 24: QRTR7
Edges:
  DOG1 -> DOG2
  DOG1 -> QRTR7
  DOG2 -> DOG3
  DOG2 -> QRTR7
  DOG3 -> DOG4
  DOG3 -> QRTR7
  DOG4 -> QRTR7
  DP1 -> DOG1
  DP1 -> DOG2
  DP1 -> DOG3
  DP1 -> DOG4
  DP1 -> DUR1
  DP1 -> DUR2
  DP1 -> DUR3
  DP1 -> DUR4
  DP1 -> DUR5
  DP1 -> FND1
  DP1 -> FND2
  DP1 -> OPS1
  DP1 -> OPS2
  DP1 -> OPS3
  DP1 -> PAR1
  DP1 -> PAR2
  DP1 -> PAR3
  DP1 -> PAR4
  DP1 -> PAR5
  DP1 -> RUN1
  DP1 -> RUN2
  DP1 -> RUN3
  DP1 -> RUN4
  DP1 -> RUN5
  DP1 -> SYN1
  DP1 -> SYN2
  DP1 -> SYN3
  DP1 -> SYN4
  DP1 -> SYN5
  DP1 -> UX1
  DP1 -> UX2
  DP1 -> UX3
  DP1 -> UX4
  DP1 -> UX5
  DP1 -> UX6
  DP1 -> VER1
  DP1 -> VER2
  DP1 -> VER3
  DP1 -> VER4
  DP1 -> VER5
  DP1 -> VER6
  DUR1 -> DUR2
  DUR1 -> DUR3
  DUR1 -> QRTR2
  DUR2 -> DUR4
  DUR2 -> QRTR2
  DUR2 -> SYN1
  DUR2 -> UX1
  DUR2 -> VER1
  DUR3 -> DUR4
  DUR3 -> QRTR2
  DUR4 -> DUR5
  DUR4 -> QRTR2
  DUR5 -> DOG3
  DUR5 -> PAR3
  DUR5 -> QRTR2
  DUR5 -> SYN5
  DUR5 -> UX3
  F -> DOG1
  F -> DOG2
  F -> DOG3
  F -> DOG4
  F -> DP1
  F -> DUR1
  F -> DUR2
  F -> DUR3
  F -> DUR4
  F -> DUR5
  F -> FND1
  F -> FND2
  F -> OPS1
  F -> OPS2
  F -> OPS3
  F -> PAR1
  F -> PAR2
  F -> PAR3
  F -> PAR4
  F -> PAR5
  F -> RUN1
  F -> RUN2
  F -> RUN3
  F -> RUN4
  F -> RUN5
  F -> SYN1
  F -> SYN2
  F -> SYN3
  F -> SYN4
  F -> SYN5
  F -> UX1
  F -> UX2
  F -> UX3
  F -> UX4
  F -> UX5
  F -> UX6
  F -> VER1
  F -> VER2
  F -> VER3
  F -> VER4
  F -> VER5
  F -> VER6
  FND1 -> FND2
  FND1 -> QRTRZ
  FND2 -> QRTRZ
  FND2 -> RUN1
  FND2 -> UX2
  OPS1 -> OPS2
  OPS1 -> QRTR6
  OPS2 -> OPS3
  OPS2 -> QRTR6
  OPS3 -> DOG2
  OPS3 -> QRTR6
  PAR1 -> PAR2
  PAR1 -> QRTR3
  PAR2 -> PAR3
  PAR2 -> QRTR3
  PAR3 -> PAR4
  PAR3 -> QRTR3
  PAR4 -> PAR5
  PAR4 -> QRTR3
  PAR5 -> DOG2
  PAR5 -> QRTR3
  PAR5 -> SYN5
  RUN1 -> PAR1
  RUN1 -> QRTR1
  RUN1 -> RUN2
  RUN1 -> RUN3
  RUN1 -> VER1
  RUN2 -> QRTR1
  RUN2 -> RUN4
  RUN3 -> QRTR1
  RUN3 -> RUN4
  RUN4 -> PAR2
  RUN4 -> QRTR1
  RUN4 -> RUN5
  RUN5 -> DOG1
  RUN5 -> DUR1
  RUN5 -> QRTR1
  RUN5 -> SYN1
  S1 -> UX6
  S10 -> RUN4
  S11 -> RUN4
  S12 -> RUN4
  S13 -> RUN4
  S14 -> DUR2
  S14 -> SYN1
  S14 -> VER1
  S15 -> RUN1
  S16 -> PAR2
  S16 -> PAR4
  S16 -> RUN4
  S17 -> RUN3
  S18 -> DUR1
  S18 -> SYN4
  S19 -> RUN1
  S2 -> DOG4
  S20 -> DUR4
  S21 -> DUR1
  S21 -> SYN3
  S22 -> DUR2
  S22 -> RUN2
  S23 -> PAR3
  S24 -> UX2
  S24 -> UX3
  S24 -> UX5
  S25 -> DUR3
  S26 -> SYN1
  S26 -> SYN2
  S27 -> PAR1
  S28 -> VER1
  S28 -> VER2
  S28 -> VER3
  S28 -> VER4
  S28 -> VER5
  S29 -> UX1
  S29 -> UX4
  S29 -> UX5
  S3 -> OPS3
  S30 -> FND1
  S31 -> FND1
  S32 -> VER4
  S33 -> VER1
  S34 -> VER3
  S35 -> RUN5
  S36 -> VER2
  S37 -> VER5
  S38 -> DUR1
  S39 -> DUR1
  S4 -> DOG4
  S40 -> DOG3
  S41 -> PAR2
  S42 -> DOG3
  S43 -> FND2
  S44 -> RUN4
  S45 -> SYN1
  S46 -> UX3
  S47 -> UX6
  S48 -> UX2
  S49 -> UX1
  S5 -> DOG1
  S50 -> UX5
  S51 -> UX4
  S52 -> RUN1
  S53 -> SYN2
  S54 -> DUR5
  S55 -> FND1
  S56 -> RUN3
  S57 -> SYN5
  S58 -> DUR2
  S59 -> RUN1
  S6 -> OPS1
  S60 -> PAR5
  S61 -> DUR3
  S62 -> SYN3
  S63 -> SYN4
  S64 -> DUR5
  S65 -> OPS2
  S66 -> OPS3
  S67 -> OPS1
  S68 -> OPS2
  S69 -> OPS3
  S7 -> OPS1
  S70 -> FND1
  S71 -> PAR5
  S72 -> PAR3
  S73 -> PAR5
  S74 -> DOG1
  S75 -> DOG2
  S76 -> DUR4
  S77 -> PAR4
  S78 -> RUN5
  S79 -> RUN2
  S8 -> DOG2
  S80 -> PAR1
  S81 -> SYN5
  S82 -> VER6
  S83 -> VER6
  S9 -> RUN4
  SYN1 -> QRTR4
  SYN1 -> SYN2
  SYN1 -> SYN3
  SYN2 -> QRTR4
  SYN2 -> SYN4
  SYN3 -> QRTR4
  SYN3 -> SYN4
  SYN4 -> QRTR4
  SYN4 -> SYN5
  SYN5 -> DOG2
  SYN5 -> QRTR4
  UX1 -> QRTR6
  UX1 -> UX4
  UX2 -> QRTR6
  UX2 -> UX3
  UX2 -> UX4
  UX3 -> QRTR6
  UX3 -> UX5
  UX4 -> QRTR6
  UX4 -> UX5
  UX5 -> QRTR6
  UX5 -> UX6
  UX6 -> DOG3
  UX6 -> OPS1
  UX6 -> QRTR6
  VER1 -> QRTR5
  VER1 -> VER2
  VER2 -> QRTR5
  VER2 -> VER3
  VER3 -> QRTR5
  VER3 -> VER4
  VER4 -> QRTR5
  VER4 -> VER5
  VER5 -> QRTR5
  VER5 -> VER6
  VER6 -> DOG2
  VER6 -> QRTR5
  VER6 -> UX5
```

### Dependency graph (mermaid)

```mermaid
flowchart LR
  DOG1["DOG1"]:::pending
  DOG2["DOG2"]:::pending
  DOG3["DOG3"]:::pending
  DOG4["DOG4"]:::pending
  DP1["DP1"]:::accepted
  DUR1["DUR1"]:::pending
  DUR2["DUR2"]:::pending
  DUR3["DUR3"]:::pending
  DUR4["DUR4"]:::pending
  DUR5["DUR5"]:::pending
  F["F"]:::accepted
  FND1["FND1"]:::pending
  FND2["FND2"]:::pending
  OPS1["OPS1"]:::pending
  OPS2["OPS2"]:::pending
  OPS3["OPS3"]:::pending
  PAR1["PAR1"]:::pending
  PAR2["PAR2"]:::pending
  PAR3["PAR3"]:::pending
  PAR4["PAR4"]:::pending
  PAR5["PAR5"]:::pending
  QRTR1["QRTR1"]:::pending
  QRTR2["QRTR2"]:::pending
  QRTR3["QRTR3"]:::pending
  QRTR4["QRTR4"]:::pending
  QRTR5["QRTR5"]:::pending
  QRTR6["QRTR6"]:::pending
  QRTR7["QRTR7"]:::pending
  QRTRZ["QRTRZ"]:::pending
  RUN1["RUN1"]:::pending
  RUN2["RUN2"]:::pending
  RUN3["RUN3"]:::pending
  RUN4["RUN4"]:::pending
  RUN5["RUN5"]:::pending
  S1["S1"]:::pending
  S10["S10"]:::pending
  S11["S11"]:::pending
  S12["S12"]:::pending
  S13["S13"]:::pending
  S14["S14"]:::pending
  S15["S15"]:::pending
  S16["S16"]:::pending
  S17["S17"]:::pending
  S18["S18"]:::pending
  S19["S19"]:::pending
  S2["S2"]:::pending
  S20["S20"]:::pending
  S21["S21"]:::pending
  S22["S22"]:::pending
  S23["S23"]:::pending
  S24["S24"]:::pending
  S25["S25"]:::pending
  S26["S26"]:::pending
  S27["S27"]:::pending
  S28["S28"]:::pending
  S29["S29"]:::pending
  S3["S3"]:::pending
  S30["S30"]:::pending
  S31["S31"]:::pending
  S32["S32"]:::pending
  S33["S33"]:::pending
  S34["S34"]:::pending
  S35["S35"]:::pending
  S36["S36"]:::pending
  S37["S37"]:::pending
  S38["S38"]:::pending
  S39["S39"]:::pending
  S4["S4"]:::pending
  S40["S40"]:::pending
  S41["S41"]:::pending
  S42["S42"]:::pending
  S43["S43"]:::pending
  S44["S44"]:::pending
  S45["S45"]:::pending
  S46["S46"]:::pending
  S47["S47"]:::pending
  S48["S48"]:::pending
  S49["S49"]:::pending
  S5["S5"]:::pending
  S50["S50"]:::pending
  S51["S51"]:::pending
  S52["S52"]:::pending
  S53["S53"]:::pending
  S54["S54"]:::pending
  S55["S55"]:::pending
  S56["S56"]:::pending
  S57["S57"]:::pending
  S58["S58"]:::pending
  S59["S59"]:::pending
  S6["S6"]:::pending
  S60["S60"]:::pending
  S61["S61"]:::pending
  S62["S62"]:::pending
  S63["S63"]:::pending
  S64["S64"]:::pending
  S65["S65"]:::pending
  S66["S66"]:::pending
  S67["S67"]:::pending
  S68["S68"]:::pending
  S69["S69"]:::pending
  S7["S7"]:::pending
  S70["S70"]:::pending
  S71["S71"]:::pending
  S72["S72"]:::pending
  S73["S73"]:::pending
  S74["S74"]:::pending
  S75["S75"]:::pending
  S76["S76"]:::pending
  S77["S77"]:::pending
  S78["S78"]:::pending
  S79["S79"]:::pending
  S8["S8"]:::pending
  S80["S80"]:::pending
  S81["S81"]:::pending
  S82["S82"]:::pending
  S83["S83"]:::pending
  S9["S9"]:::pending
  SYN1["SYN1"]:::pending
  SYN2["SYN2"]:::pending
  SYN3["SYN3"]:::pending
  SYN4["SYN4"]:::pending
  SYN5["SYN5"]:::pending
  UX1["UX1"]:::pending
  UX2["UX2"]:::pending
  UX3["UX3"]:::pending
  UX4["UX4"]:::pending
  UX5["UX5"]:::pending
  UX6["UX6"]:::pending
  VER1["VER1"]:::pending
  VER2["VER2"]:::pending
  VER3["VER3"]:::pending
  VER4["VER4"]:::pending
  VER5["VER5"]:::pending
  VER6["VER6"]:::pending
  DOG1 --> DOG2
  DOG1 --> QRTR7
  DOG2 --> DOG3
  DOG2 --> QRTR7
  DOG3 --> DOG4
  DOG3 --> QRTR7
  DOG4 --> QRTR7
  DP1 --> DOG1
  DP1 --> DOG2
  DP1 --> DOG3
  DP1 --> DOG4
  DP1 --> DUR1
  DP1 --> DUR2
  DP1 --> DUR3
  DP1 --> DUR4
  DP1 --> DUR5
  DP1 --> FND1
  DP1 --> FND2
  DP1 --> OPS1
  DP1 --> OPS2
  DP1 --> OPS3
  DP1 --> PAR1
  DP1 --> PAR2
  DP1 --> PAR3
  DP1 --> PAR4
  DP1 --> PAR5
  DP1 --> RUN1
  DP1 --> RUN2
  DP1 --> RUN3
  DP1 --> RUN4
  DP1 --> RUN5
  DP1 --> SYN1
  DP1 --> SYN2
  DP1 --> SYN3
  DP1 --> SYN4
  DP1 --> SYN5
  DP1 --> UX1
  DP1 --> UX2
  DP1 --> UX3
  DP1 --> UX4
  DP1 --> UX5
  DP1 --> UX6
  DP1 --> VER1
  DP1 --> VER2
  DP1 --> VER3
  DP1 --> VER4
  DP1 --> VER5
  DP1 --> VER6
  DUR1 --> DUR2
  DUR1 --> DUR3
  DUR1 --> QRTR2
  DUR2 --> DUR4
  DUR2 --> QRTR2
  DUR2 --> SYN1
  DUR2 --> UX1
  DUR2 --> VER1
  DUR3 --> DUR4
  DUR3 --> QRTR2
  DUR4 --> DUR5
  DUR4 --> QRTR2
  DUR5 --> DOG3
  DUR5 --> PAR3
  DUR5 --> QRTR2
  DUR5 --> SYN5
  DUR5 --> UX3
  F --> DOG1
  F --> DOG2
  F --> DOG3
  F --> DOG4
  F --> DP1
  F --> DUR1
  F --> DUR2
  F --> DUR3
  F --> DUR4
  F --> DUR5
  F --> FND1
  F --> FND2
  F --> OPS1
  F --> OPS2
  F --> OPS3
  F --> PAR1
  F --> PAR2
  F --> PAR3
  F --> PAR4
  F --> PAR5
  F --> RUN1
  F --> RUN2
  F --> RUN3
  F --> RUN4
  F --> RUN5
  F --> SYN1
  F --> SYN2
  F --> SYN3
  F --> SYN4
  F --> SYN5
  F --> UX1
  F --> UX2
  F --> UX3
  F --> UX4
  F --> UX5
  F --> UX6
  F --> VER1
  F --> VER2
  F --> VER3
  F --> VER4
  F --> VER5
  F --> VER6
  FND1 --> FND2
  FND1 --> QRTRZ
  FND2 --> QRTRZ
  FND2 --> RUN1
  FND2 --> UX2
  OPS1 --> OPS2
  OPS1 --> QRTR6
  OPS2 --> OPS3
  OPS2 --> QRTR6
  OPS3 --> DOG2
  OPS3 --> QRTR6
  PAR1 --> PAR2
  PAR1 --> QRTR3
  PAR2 --> PAR3
  PAR2 --> QRTR3
  PAR3 --> PAR4
  PAR3 --> QRTR3
  PAR4 --> PAR5
  PAR4 --> QRTR3
  PAR5 --> DOG2
  PAR5 --> QRTR3
  PAR5 --> SYN5
  RUN1 --> PAR1
  RUN1 --> QRTR1
  RUN1 --> RUN2
  RUN1 --> RUN3
  RUN1 --> VER1
  RUN2 --> QRTR1
  RUN2 --> RUN4
  RUN3 --> QRTR1
  RUN3 --> RUN4
  RUN4 --> PAR2
  RUN4 --> QRTR1
  RUN4 --> RUN5
  RUN5 --> DOG1
  RUN5 --> DUR1
  RUN5 --> QRTR1
  RUN5 --> SYN1
  S1 --> UX6
  S10 --> RUN4
  S11 --> RUN4
  S12 --> RUN4
  S13 --> RUN4
  S14 --> DUR2
  S14 --> SYN1
  S14 --> VER1
  S15 --> RUN1
  S16 --> PAR2
  S16 --> PAR4
  S16 --> RUN4
  S17 --> RUN3
  S18 --> DUR1
  S18 --> SYN4
  S19 --> RUN1
  S2 --> DOG4
  S20 --> DUR4
  S21 --> DUR1
  S21 --> SYN3
  S22 --> DUR2
  S22 --> RUN2
  S23 --> PAR3
  S24 --> UX2
  S24 --> UX3
  S24 --> UX5
  S25 --> DUR3
  S26 --> SYN1
  S26 --> SYN2
  S27 --> PAR1
  S28 --> VER1
  S28 --> VER2
  S28 --> VER3
  S28 --> VER4
  S28 --> VER5
  S29 --> UX1
  S29 --> UX4
  S29 --> UX5
  S3 --> OPS3
  S30 --> FND1
  S31 --> FND1
  S32 --> VER4
  S33 --> VER1
  S34 --> VER3
  S35 --> RUN5
  S36 --> VER2
  S37 --> VER5
  S38 --> DUR1
  S39 --> DUR1
  S4 --> DOG4
  S40 --> DOG3
  S41 --> PAR2
  S42 --> DOG3
  S43 --> FND2
  S44 --> RUN4
  S45 --> SYN1
  S46 --> UX3
  S47 --> UX6
  S48 --> UX2
  S49 --> UX1
  S5 --> DOG1
  S50 --> UX5
  S51 --> UX4
  S52 --> RUN1
  S53 --> SYN2
  S54 --> DUR5
  S55 --> FND1
  S56 --> RUN3
  S57 --> SYN5
  S58 --> DUR2
  S59 --> RUN1
  S6 --> OPS1
  S60 --> PAR5
  S61 --> DUR3
  S62 --> SYN3
  S63 --> SYN4
  S64 --> DUR5
  S65 --> OPS2
  S66 --> OPS3
  S67 --> OPS1
  S68 --> OPS2
  S69 --> OPS3
  S7 --> OPS1
  S70 --> FND1
  S71 --> PAR5
  S72 --> PAR3
  S73 --> PAR5
  S74 --> DOG1
  S75 --> DOG2
  S76 --> DUR4
  S77 --> PAR4
  S78 --> RUN5
  S79 --> RUN2
  S8 --> DOG2
  S80 --> PAR1
  S81 --> SYN5
  S82 --> VER6
  S83 --> VER6
  S9 --> RUN4
  SYN1 --> QRTR4
  SYN1 --> SYN2
  SYN1 --> SYN3
  SYN2 --> QRTR4
  SYN2 --> SYN4
  SYN3 --> QRTR4
  SYN3 --> SYN4
  SYN4 --> QRTR4
  SYN4 --> SYN5
  SYN5 --> DOG2
  SYN5 --> QRTR4
  UX1 --> QRTR6
  UX1 --> UX4
  UX2 --> QRTR6
  UX2 --> UX3
  UX2 --> UX4
  UX3 --> QRTR6
  UX3 --> UX5
  UX4 --> QRTR6
  UX4 --> UX5
  UX5 --> QRTR6
  UX5 --> UX6
  UX6 --> DOG3
  UX6 --> OPS1
  UX6 --> QRTR6
  VER1 --> QRTR5
  VER1 --> VER2
  VER2 --> QRTR5
  VER2 --> VER3
  VER3 --> QRTR5
  VER3 --> VER4
  VER4 --> QRTR5
  VER4 --> VER5
  VER5 --> QRTR5
  VER5 --> VER6
  VER6 --> DOG2
  VER6 --> QRTR5
  VER6 --> UX5
  classDef accepted fill:#E3F1E8,stroke:#146B3A,color:#0A2E1A;
  classDef blocked fill:#FAE5E3,stroke:#B3261E,color:#4A100C;
  classDef invalidated fill:#F7EDD9,stroke:#815500,color:#3D2900;
  classDef pending fill:#EEF0F3,stroke:#69707C,color:#14171C;
```

### State ledger

| Task ID | Stage | State |
|---|---|---|
| DOG1 | RTR7 | PLANNED |
| DOG2 | RTR7 | PLANNED |
| DOG3 | RTR7 | PLANNED |
| DOG4 | RTR7 | PLANNED |
| DP1 | RTRZ | ACCEPTED |
| DUR1 | RTR2 | PLANNED |
| DUR2 | RTR2 | PLANNED |
| DUR3 | RTR2 | PLANNED |
| DUR4 | RTR2 | PLANNED |
| DUR5 | RTR2 | PLANNED |
| F | RTRZ | ACCEPTED |
| FND1 | RTRZ | PLANNED |
| FND2 | RTRZ | PLANNED |
| OPS1 | RTR6 | PLANNED |
| OPS2 | RTR6 | PLANNED |
| OPS3 | RTR6 | PLANNED |
| PAR1 | RTR3 | PLANNED |
| PAR2 | RTR3 | PLANNED |
| PAR3 | RTR3 | PLANNED |
| PAR4 | RTR3 | PLANNED |
| PAR5 | RTR3 | PLANNED |
| QRTR1 | RTR1 | PLANNED |
| QRTR2 | RTR2 | PLANNED |
| QRTR3 | RTR3 | PLANNED |
| QRTR4 | RTR4 | PLANNED |
| QRTR5 | RTR5 | PLANNED |
| QRTR6 | RTR6 | PLANNED |
| QRTR7 | RTR7 | PLANNED |
| QRTRZ | RTRZ | PLANNED |
| RUN1 | RTR1 | PLANNED |
| RUN2 | RTR1 | PLANNED |
| RUN3 | RTR1 | PLANNED |
| RUN4 | RTR1 | PLANNED |
| RUN5 | RTR1 | PLANNED |
| S1 | RTRZ | READY |
| S10 | RTRZ | READY |
| S11 | RTRZ | READY |
| S12 | RTRZ | READY |
| S13 | RTRZ | READY |
| S14 | RTRZ | READY |
| S15 | RTRZ | READY |
| S16 | RTRZ | READY |
| S17 | RTRZ | READY |
| S18 | RTRZ | READY |
| S19 | RTRZ | READY |
| S2 | RTRZ | READY |
| S20 | RTRZ | READY |
| S21 | RTRZ | READY |
| S22 | RTRZ | READY |
| S23 | RTRZ | READY |
| S24 | RTRZ | READY |
| S25 | RTRZ | READY |
| S26 | RTRZ | READY |
| S27 | RTRZ | READY |
| S28 | RTRZ | READY |
| S29 | RTRZ | READY |
| S3 | RTRZ | READY |
| S30 | RTRZ | READY |
| S31 | RTRZ | READY |
| S32 | RTRZ | READY |
| S33 | RTRZ | READY |
| S34 | RTRZ | READY |
| S35 | RTRZ | READY |
| S36 | RTRZ | READY |
| S37 | RTRZ | READY |
| S38 | RTRZ | READY |
| S39 | RTRZ | READY |
| S4 | RTRZ | READY |
| S40 | RTRZ | READY |
| S41 | RTRZ | READY |
| S42 | RTRZ | READY |
| S43 | RTRZ | READY |
| S44 | RTRZ | READY |
| S45 | RTRZ | READY |
| S46 | RTRZ | READY |
| S47 | RTRZ | READY |
| S48 | RTRZ | READY |
| S49 | RTRZ | READY |
| S5 | RTRZ | READY |
| S50 | RTRZ | READY |
| S51 | RTRZ | READY |
| S52 | RTRZ | READY |
| S53 | RTRZ | READY |
| S54 | RTRZ | READY |
| S55 | RTRZ | READY |
| S56 | RTRZ | READY |
| S57 | RTRZ | READY |
| S58 | RTRZ | READY |
| S59 | RTRZ | READY |
| S6 | RTRZ | READY |
| S60 | RTRZ | READY |
| S61 | RTRZ | READY |
| S62 | RTRZ | READY |
| S63 | RTRZ | READY |
| S64 | RTRZ | READY |
| S65 | RTRZ | READY |
| S66 | RTRZ | READY |
| S67 | RTRZ | READY |
| S68 | RTRZ | READY |
| S69 | RTRZ | READY |
| S7 | RTRZ | READY |
| S70 | RTRZ | READY |
| S71 | RTRZ | READY |
| S72 | RTRZ | READY |
| S73 | RTRZ | READY |
| S74 | RTRZ | READY |
| S75 | RTRZ | READY |
| S76 | RTRZ | READY |
| S77 | RTRZ | READY |
| S78 | RTRZ | READY |
| S79 | RTRZ | READY |
| S8 | RTRZ | READY |
| S80 | RTRZ | READY |
| S81 | RTRZ | READY |
| S82 | RTRZ | READY |
| S83 | RTRZ | READY |
| S9 | RTRZ | READY |
| SYN1 | RTR4 | PLANNED |
| SYN2 | RTR4 | PLANNED |
| SYN3 | RTR4 | PLANNED |
| SYN4 | RTR4 | PLANNED |
| SYN5 | RTR4 | PLANNED |
| UX1 | RTR6 | PLANNED |
| UX2 | RTR6 | PLANNED |
| UX3 | RTR6 | PLANNED |
| UX4 | RTR6 | PLANNED |
| UX5 | RTR6 | PLANNED |
| UX6 | RTR6 | PLANNED |
| VER1 | RTR5 | PLANNED |
| VER2 | RTR5 | PLANNED |
| VER3 | RTR5 | PLANNED |
| VER4 | RTR5 | PLANNED |
| VER5 | RTR5 | PLANNED |
| VER6 | RTR5 | PLANNED |

### Semantic node registry

| Task ID | Semantic key | Execution state |
|---|---|---|
| DOG1 | requirement.dog1 | PLANNED |
| DOG2 | requirement.dog2 | PLANNED |
| DOG3 | requirement.dog3 | PLANNED |
| DOG4 | requirement.dog4 | PLANNED |
| DP1 | decision.matharc-native-runtime | ACCEPTED |
| DUR1 | requirement.dur1 | PLANNED |
| DUR2 | requirement.dur2 | PLANNED |
| DUR3 | requirement.dur3 | PLANNED |
| DUR4 | requirement.dur4 | PLANNED |
| DUR5 | requirement.dur5 | PLANNED |
| F | source.identity-baseline | ACCEPTED |
| FND1 | requirement.fnd1 | PLANNED |
| FND2 | requirement.fnd2 | PLANNED |
| OPS1 | requirement.ops1 | PLANNED |
| OPS2 | requirement.ops2 | PLANNED |
| OPS3 | requirement.ops3 | PLANNED |
| PAR1 | requirement.par1 | PLANNED |
| PAR2 | requirement.par2 | PLANNED |
| PAR3 | requirement.par3 | PLANNED |
| PAR4 | requirement.par4 | PLANNED |
| PAR5 | requirement.par5 | PLANNED |
| QRTR1 | acceptance.release.rtr1 | PLANNED |
| QRTR2 | acceptance.release.rtr2 | PLANNED |
| QRTR3 | acceptance.release.rtr3 | PLANNED |
| QRTR4 | acceptance.release.rtr4 | PLANNED |
| QRTR5 | acceptance.release.rtr5 | PLANNED |
| QRTR6 | acceptance.release.rtr6 | PLANNED |
| QRTR7 | acceptance.release.rtr7 | PLANNED |
| QRTRZ | acceptance.release.rtrz | PLANNED |
| RUN1 | requirement.run1 | PLANNED |
| RUN2 | requirement.run2 | PLANNED |
| RUN3 | requirement.run3 | PLANNED |
| RUN4 | requirement.run4 | PLANNED |
| RUN5 | requirement.run5 | PLANNED |
| S1 | write-region.s1 | READY |
| S10 | write-region.s10 | READY |
| S11 | write-region.s11 | READY |
| S12 | write-region.s12 | READY |
| S13 | write-region.s13 | READY |
| S14 | write-region.s14 | READY |
| S15 | write-region.s15 | READY |
| S16 | write-region.s16 | READY |
| S17 | write-region.s17 | READY |
| S18 | write-region.s18 | READY |
| S19 | write-region.s19 | READY |
| S2 | write-region.s2 | READY |
| S20 | write-region.s20 | READY |
| S21 | write-region.s21 | READY |
| S22 | write-region.s22 | READY |
| S23 | write-region.s23 | READY |
| S24 | write-region.s24 | READY |
| S25 | write-region.s25 | READY |
| S26 | write-region.s26 | READY |
| S27 | write-region.s27 | READY |
| S28 | write-region.s28 | READY |
| S29 | write-region.s29 | READY |
| S3 | write-region.s3 | READY |
| S30 | write-region.s30 | READY |
| S31 | write-region.s31 | READY |
| S32 | write-region.s32 | READY |
| S33 | write-region.s33 | READY |
| S34 | write-region.s34 | READY |
| S35 | write-region.s35 | READY |
| S36 | write-region.s36 | READY |
| S37 | write-region.s37 | READY |
| S38 | write-region.s38 | READY |
| S39 | write-region.s39 | READY |
| S4 | write-region.s4 | READY |
| S40 | write-region.s40 | READY |
| S41 | write-region.s41 | READY |
| S42 | write-region.s42 | READY |
| S43 | write-region.s43 | READY |
| S44 | write-region.s44 | READY |
| S45 | write-region.s45 | READY |
| S46 | write-region.s46 | READY |
| S47 | write-region.s47 | READY |
| S48 | write-region.s48 | READY |
| S49 | write-region.s49 | READY |
| S5 | write-region.s5 | READY |
| S50 | write-region.s50 | READY |
| S51 | write-region.s51 | READY |
| S52 | write-region.s52 | READY |
| S53 | write-region.s53 | READY |
| S54 | write-region.s54 | READY |
| S55 | write-region.s55 | READY |
| S56 | write-region.s56 | READY |
| S57 | write-region.s57 | READY |
| S58 | write-region.s58 | READY |
| S59 | write-region.s59 | READY |
| S6 | write-region.s6 | READY |
| S60 | write-region.s60 | READY |
| S61 | write-region.s61 | READY |
| S62 | write-region.s62 | READY |
| S63 | write-region.s63 | READY |
| S64 | write-region.s64 | READY |
| S65 | write-region.s65 | READY |
| S66 | write-region.s66 | READY |
| S67 | write-region.s67 | READY |
| S68 | write-region.s68 | READY |
| S69 | write-region.s69 | READY |
| S7 | write-region.s7 | READY |
| S70 | write-region.s70 | READY |
| S71 | write-region.s71 | READY |
| S72 | write-region.s72 | READY |
| S73 | write-region.s73 | READY |
| S74 | write-region.s74 | READY |
| S75 | write-region.s75 | READY |
| S76 | write-region.s76 | READY |
| S77 | write-region.s77 | READY |
| S78 | write-region.s78 | READY |
| S79 | write-region.s79 | READY |
| S8 | write-region.s8 | READY |
| S80 | write-region.s80 | READY |
| S81 | write-region.s81 | READY |
| S82 | write-region.s82 | READY |
| S83 | write-region.s83 | READY |
| S9 | write-region.s9 | READY |
| SYN1 | requirement.syn1 | PLANNED |
| SYN2 | requirement.syn2 | PLANNED |
| SYN3 | requirement.syn3 | PLANNED |
| SYN4 | requirement.syn4 | PLANNED |
| SYN5 | requirement.syn5 | PLANNED |
| UX1 | requirement.ux1 | PLANNED |
| UX2 | requirement.ux2 | PLANNED |
| UX3 | requirement.ux3 | PLANNED |
| UX4 | requirement.ux4 | PLANNED |
| UX5 | requirement.ux5 | PLANNED |
| UX6 | requirement.ux6 | PLANNED |
| VER1 | requirement.ver1 | PLANNED |
| VER2 | requirement.ver2 | PLANNED |
| VER3 | requirement.ver3 | PLANNED |
| VER4 | requirement.ver4 | PLANNED |
| VER5 | requirement.ver5 | PLANNED |
| VER6 | requirement.ver6 | PLANNED |

### Ready frontier

| Task ID | Eligibility |
|---|---|
| DOG1 | not-ready |
| DOG2 | not-ready |
| DOG3 | not-ready |
| DOG4 | not-ready |
| DP1 | not-ready |
| DUR1 | not-ready |
| DUR2 | not-ready |
| DUR3 | not-ready |
| DUR4 | not-ready |
| DUR5 | not-ready |
| F | not-ready |
| FND1 | not-ready |
| FND2 | not-ready |
| OPS1 | not-ready |
| OPS2 | not-ready |
| OPS3 | not-ready |
| PAR1 | not-ready |
| PAR2 | not-ready |
| PAR3 | not-ready |
| PAR4 | not-ready |
| PAR5 | not-ready |
| QRTR1 | not-ready |
| QRTR2 | not-ready |
| QRTR3 | not-ready |
| QRTR4 | not-ready |
| QRTR5 | not-ready |
| QRTR6 | not-ready |
| QRTR7 | not-ready |
| QRTRZ | not-ready |
| RUN1 | not-ready |
| RUN2 | not-ready |
| RUN3 | not-ready |
| RUN4 | not-ready |
| RUN5 | not-ready |
| S1 | ready |
| S10 | ready |
| S11 | ready |
| S12 | ready |
| S13 | ready |
| S14 | ready |
| S15 | ready |
| S16 | ready |
| S17 | ready |
| S18 | ready |
| S19 | ready |
| S2 | ready |
| S20 | ready |
| S21 | ready |
| S22 | ready |
| S23 | ready |
| S24 | ready |
| S25 | ready |
| S26 | ready |
| S27 | ready |
| S28 | ready |
| S29 | ready |
| S3 | ready |
| S30 | ready |
| S31 | ready |
| S32 | ready |
| S33 | ready |
| S34 | ready |
| S35 | ready |
| S36 | ready |
| S37 | ready |
| S38 | ready |
| S39 | ready |
| S4 | ready |
| S40 | ready |
| S41 | ready |
| S42 | ready |
| S43 | ready |
| S44 | ready |
| S45 | ready |
| S46 | ready |
| S47 | ready |
| S48 | ready |
| S49 | ready |
| S5 | ready |
| S50 | ready |
| S51 | ready |
| S52 | ready |
| S53 | ready |
| S54 | ready |
| S55 | ready |
| S56 | ready |
| S57 | ready |
| S58 | ready |
| S59 | ready |
| S6 | ready |
| S60 | ready |
| S61 | ready |
| S62 | ready |
| S63 | ready |
| S64 | ready |
| S65 | ready |
| S66 | ready |
| S67 | ready |
| S68 | ready |
| S69 | ready |
| S7 | ready |
| S70 | ready |
| S71 | ready |
| S72 | ready |
| S73 | ready |
| S74 | ready |
| S75 | ready |
| S76 | ready |
| S77 | ready |
| S78 | ready |
| S79 | ready |
| S8 | ready |
| S80 | ready |
| S81 | ready |
| S82 | ready |
| S83 | ready |
| S9 | ready |
| SYN1 | not-ready |
| SYN2 | not-ready |
| SYN3 | not-ready |
| SYN4 | not-ready |
| SYN5 | not-ready |
| UX1 | not-ready |
| UX2 | not-ready |
| UX3 | not-ready |
| UX4 | not-ready |
| UX5 | not-ready |
| UX6 | not-ready |
| VER1 | not-ready |
| VER2 | not-ready |
| VER3 | not-ready |
| VER4 | not-ready |
| VER5 | not-ready |
| VER6 | not-ready |
