---
ARTIFACT_CLASS: ssot-development
APPLICABILITY_DECISION: ssot
GOVERNANCE_REASON: "本轮同时修订 Harness Engineering 的声明 schema、执行证据、状态模型、推送门禁、规则守恒、复杂度盘点和验收采集器，并由 MathArc 项目持有跨仓库执行与发布证据；两个独立发布切片需要持久节点状态、验收合同和远端提交回读。"
SSOT_DEPTH: L2
TARGET_EVIDENCE_LEVEL: local-runtime
PLAN_VERSION: 1
DAG_VERSION: 1
INTERFACE_FREEZE_VERSION: 1
NODE_CONTRACT_VERSION: 2
SSOT_SCHEMA_VERSION: 2
FACTS_REGISTRY_VERSION: 1
VIEW_MODEL_VERSION: 2
SSOT_PLANNING_COMPILER: .ssot/planning-compiler.json
SSOT_MACHINE_SOURCE: .ssot/manifest.json
---

# 任务（matharc-research-execution-plane）开发 SSOT

## 业务结论与范围

本轮同时修订智能工程平台（Harness Engineering）的声明模式（schema）、执行证据、状态模型、推送门禁、规则守恒、复杂度盘点和验收采集器，并由数学研究项目（MathArc）持有跨仓库执行与发布证据；两个独立发布切片需要持久节点状态、验收合同和远端提交回读。

## 需要拍板的问题

尚无待拍板问题时在此写明当前没有；有则写入问题记录文件（openproblem.md）并在此引用。

## 发布切片

| Release ID | 用户价值 | 独立失败边界 |
| --- | --- | --- |
| R1 | SSOT 输入、执行完成证据、状态迁移和推送资格使用同一套可验证事实，不再接受仅靠声明的完成或过期验证报告。 | 任一负例未被封闭拒绝时，本切片保持未接受，不允许进入 GitHub 主线。 |
| R2 | 维护者只读取当前任务触发的规范，规则索引和实际产物双向守恒，证据 lane 与事实登记不再产生不可采集或仪式性内容。 | 任一规则、视图、采集器或事实类别无法从真实文件反查时，本切片保持未接受且不影响 R1 的已验证能力。 |

## 节点清单

| Node ID | Goal | Dependencies | Acceptance | Owner |
| --- | --- | --- | --- | --- |
| C1 | 执行 Draft 2020-12 schema，并让正式 execution 对象和真实完成证据从输入贯通到节点、worker 台账与运行器记录。 | DP1 | 合同与所需 lane 证据全部接受 | Harness 声明编译负责人 |
| DP1 | 用户确认本轮 Harness 改造与 MathArc/Harness 主线收口的工程执行范围。 | none | 合同与所需 lane 证据全部接受 | decision owner |
| E1 | 用可解析的证据 lane registry 绑定真实采集器，并按正文实际引用启用 Facts Registry 类别。 | DP1, C1 | 合同与所需 lane 证据全部接受 | Harness 证据与事实负责人 |
| P1 | 推送时重新计算并核对 validation report 的完整绑定，同时从 manifest 和磁盘实际产物复算复杂度。 | DP1, C1 | 合同与所需 lane 证据全部接受 | Harness 推送资格负责人 |
| QR1 | Accept the R1 candidate against its source completion criteria. | C1, S1, P1 | 合同与所需 lane 证据全部接受 | release decision owner |
| QR2 | Accept the R2 candidate against its source completion criteria. | RI1, E1, V1 | 合同与所需 lane 证据全部接受 | release decision owner |
| RI1 | 让规则索引双向守恒，补齐版本矩阵并以触发式阅读图限制基础上下文。 | DP1, S1, P1 | 合同与所需 lane 证据全部接受 | Harness 规则索引负责人 |
| S1 | 建立唯一节点状态转换模型，并让 L1 由当前编排者在零 worker 工件条件下推进到 ACCEPTED。 | DP1, C1 | 合同与所需 lane 证据全部接受 | Harness 状态模型负责人 |
| V1 | 在同一源码身份上运行附件规定的 12 个端到端反例和 Harness 全量本地 CI，并记录 GitHub 主线读回与清理结果。 | DP1, RI1, E1 | 合同与所需 lane 证据全部接受 | Harness 集成验收负责人 |

拓扑、逐节点合同与来源登记的投影见伴随视图，不在本文件重复。

## 伴随视图

- 拓扑视图（`generated-views/topology.md`）：依赖边表、文本拓扑图与流程图，以及状态台账、语义节点登记、就绪前沿（跨全部发布切片的全量机器投影）。
- 节点视图（`generated-views/nodes-<release>.md`）：各发布切片的节点合同与状态台账。
- 来源登记视图（`generated-views/source-requirements.md`）：来源覆盖、视觉令牌、锚点与接线（严格来源模式）。

### 文本拓扑图（ASCII 拓扑图）

依赖边和流程图由拓扑伴随视图（`generated-views/topology.md`）生成，本页不重复机器投影。

## 工程附录

本节是结构检查器与事实检查器要求的机器投影，字段名与标识符按英文原样登记。拓扑图、依赖边、状态台账和节点合同由伴随视图生成。

### 事实登记表（Facts Registry）

| 事实类别 | 事实键 | 登记值 |
| --- | --- | --- |
| path | machine-root | `.ssot/` |
| path | evidence-root | `agents-results/2026-09-04/matharc-research-execution-plane/evidence/` |
| layout | bundle-root | `agents-results/2026-09-04/matharc-research-execution-plane/` |

本 bundle 的固定布局是 `agents-results/2026-09-04/matharc-research-execution-plane/`，证据目录为 `agents-results/2026-09-04/matharc-research-execution-plane/evidence/`。

### 状态台账（State ledger）

| Task ID | Stage | State |
| --- | --- | --- |
| C1 | R1 | PLANNED |
| DP1 | R1 | ACCEPTED |
| E1 | R2 | PLANNED |
| P1 | R1 | PLANNED |
| QR1 | R1 | PLANNED |
| QR2 | R2 | PLANNED |
| RI1 | R2 | PLANNED |
| S1 | R1 | PLANNED |
| V1 | R2 | PLANNED |

### 依赖边表（Dependency edge table）

| From | To | Dependency type |
| --- | --- | --- |
| C1 | E1 | hard |
| C1 | P1 | hard |
| C1 | QR1 | hard |
| C1 | S1 | hard |
| DP1 | C1 | hard |
| DP1 | E1 | hard |
| DP1 | P1 | hard |
| DP1 | RI1 | hard |
| DP1 | S1 | hard |
| DP1 | V1 | hard |
| E1 | QR2 | hard |
| E1 | V1 | hard |
| P1 | QR1 | hard |
| P1 | RI1 | hard |
| RI1 | QR2 | hard |
| RI1 | V1 | hard |
| S1 | QR1 | hard |
| S1 | RI1 | hard |
| V1 | QR2 | hard |

### 语义节点登记（Semantic node registry）

| Task ID | Semantic key | Execution state |
| --- | --- | --- |
| C1 | requirement.c1 | PLANNED |
| DP1 | decision.execution-plane.scope | ACCEPTED |
| E1 | requirement.e1 | PLANNED |
| P1 | requirement.p1 | PLANNED |
| QR1 | acceptance.release.r1 | PLANNED |
| QR2 | acceptance.release.r2 | PLANNED |
| RI1 | requirement.ri1 | PLANNED |
| S1 | requirement.s1 | PLANNED |
| V1 | requirement.v1 | PLANNED |

### 就绪前沿（Ready frontier）

| Task ID | Eligibility |
| --- | --- |
| C1 | not-ready |
| DP1 | not-ready |
| E1 | not-ready |
| P1 | not-ready |
| QR1 | not-ready |
| QR2 | not-ready |
| RI1 | not-ready |
| S1 | not-ready |
| V1 | not-ready |

### 叶子交付物清单（Leaf deliverable inventory）

本次编译没有节点声明独立可并行的叶子交付物（每个节点的 deliverable_ids 均为空）。

| Deliverable ID | Owning node | Parallel batch |
| --- | --- | --- |

### 并行宽度表（Parallel width table）

| Parallel batch | Leaf deliverables |
| --- | --- |
