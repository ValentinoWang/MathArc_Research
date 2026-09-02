# Acceptance Contract: A4-topic-observation-dogfood

- Task ID: A4-topic-observation-dogfood
- Contract version: 3
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: 验收负责人（用户授权）
- Approval evidence: 用户于 2026-09-02 以书面验收负责人指令批准 A4 contract v3：新增 threat model、durability model 与 residual-risk disposition；AC 与 H acceptance condition 不变；并在第 1.2 条机械审查全部通过的条件下批准 protected tests v2 → v3 的新增测试与辅助重构；指定 local CI。本批准不构成 H-01 PASS。
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A4.json
- SSOT node: A4
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/.ssot/manifest.json
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.amendment@2
- Assumption IDs: none
- Invalidation keys: acceptance.problem-intelligence.dogfood
- AC budget: 5
- Baseline identity: main@7a29d00b1896b41654f3c1d86645114b71b8c4d2
- Human acceptance workspace: acceptance/human/A4-topic-observation-dogfood

## User and scenario

验收负责人在单一可信用户账号的本机、离线且输入为仓库内固定字节的三例档案这一既有范围内，依据 AC-01 至 AC-05 与 H-01 验收 A4。

## Problem

A4 需要在既有验收条件不变的前提下，明确本轮闭合式复核所适用的威胁模型、持久化模型和残余风险处置边界。

## Expected outcome

由 AC-01 至 AC-05 和 H-01 定义；本节不新增 acceptance condition。

## Scope

验收一次性主题观测和三例来源固定档案的重放、恢复、去重、预算与失败模式闭环。资料只来自仓库固定字节；结果不构成数学证明、外部文献确认、生产或设备证据，也不授权公开发布。

## Acceptance criteria

| ID | Class | Lane | Requirement | Verification | Blocking |
| --- | --- | --- | --- | --- | --- |
| AC-01 | behavior | machine/unit | 三例固定档案的身份、状态、来源和不晋升边界完整 | T2 evidence plus archive-boundary review | Yes |
| AC-02 | behavior | machine/unit | 重放、恢复、去重、预算和人工队列绑定且篡改 fail-closed | focused topic/archive tests plus state-integrity review | Yes |
| AC-03 | behavior | machine/static | 合同元数据（来源目录与 non-claim boundary）语义不可变 | protected negative test and archive-boundary review | Yes |
| AC-04 | behavior | machine/e2e | 全量回归、浏览器门禁和技术预检通过且不越界 | regression-ssot review | Yes |
| AC-05 | behavior | release | 当前主线、合同、边、T2 证据和三条独立 AI return 哈希一致 | release synthesis | Yes |
| H-01 | 用户确认本次仅为离线源级验收，不是数学证明或公开发布 | human checklist | Yes |

## Protected acceptance tests

| Path | SHA-256 |
| --- | --- |
| tests/test_v02_topic_observation.py | bccdbb46c5bb8bb256d7f2c403e3fcbcf7c6c51976134fd8c18b23bc4b2ce497 |
| tests/test_v02_dogfood_archives.py | 345a2c94299df3f001757606ac2c9db6f7243a20dd42d150a77360e28c678242 |

## Non-goals

不进行实时网络检索，不判断数学真伪，不确认外部文献完整性或开放状态，不生成 ResearchTrace/ClaimStatus，不证明生产/设备行为，不授权公开研究结论。

## Invariants

术语说明：

「威胁模型」指本合同假定的对手及其能力。

「持久化模型」指本合同要求的 crash/recovery guarantee。

「残余风险」指落在上述模型之外、可以记录但不阻塞 acceptance 的 observation。

1. 运行环境：单一可信用户账号的本机，离线，输入只来自仓库内固定字节的三例档案。

2. 威胁模型：不设恶意攻击者。与运行进程同属一个用户账号、能够读写仓库目录、状态目录、密钥文件或 sidecar 的任何进程均视为可信主体。针对这类主体的主动篡改、rollback、TOCTOU、symbolic-link substitution、hard-link alias、fork inheritance、key access、sidecar restore 等发现，一律不构成 AC-02 failure。

3. 持久化模型：只考虑进程在任意程序步骤处异常终止，并随后在同一仍持续运行的操作系统和文件系统上重新启动。假定内核已经确认完成的 filesystem operation 在该进程重新启动后仍可观察。不考虑 OS crash、machine power loss、device cache loss、filesystem failure 或 directory-entry power-loss durability；不要求 component-by-component directory fsync。在本模型内，不允许将未完成 transaction 错误识别为已提交 transaction；replay、recovery、deduplication、budget 与 human-queue state 必须能够恢复，或者 fail-closed / refuse-to-proceed。

4. AC-02 中「tampering fail-closed」仅表示：在上述模型内，已提交的固定 fixture、evidence file 或 state file 出现不符合正常 commit protocol 的可检测 byte-level change 时，加载必须拒绝或者进入不可继续状态。它不构成针对能够同时修改 data、authentication material 或 key 的可信同用户主体的 security guarantee。

5. 已存在的 HMAC signed state、commit log 与 write-fence mechanism 保留现状，不再扩展。其 acceptance correctness 只针对本合同模型内的 normal path 与 process-interruption path。

## Normal path

由 AC-01 至 AC-05 的现有验证路径和 H-01 的人工确认共同治理；不新增 acceptance condition。

## Exception paths

重放、恢复、去重、预算、人工队列与 fail-closed 行为由 AC-02 和上述 Invariants 治理；不新增异常路径要求。

## Data impact

本验收切片不新增数据迁移、保留、删除或清理要求；现有固定档案、状态与验收证据仍由 AC-01 至 AC-05 治理。

## Permissions

合同批准权属于验收负责人；H-01 只能由用户（研究负责人/仓库所有者）执行。无额外权限要求。

## Performance and reliability

可靠性边界仅为上述 Invariants 已批准的 process-crash durability model；不新增延迟、并发、可用性或部署指标。

## Human acceptance

人工验收步骤和签名结果保存在本合同声明的项目级 workspace；本节不改变 H-01 语义。

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 用户确认本次仅为离线源级验收，不是数学证明或公开发布 | acceptance/human/A4-topic-observation-dogfood/checklist.md#h-01 | 用户（研究负责人/仓库所有者） | Yes |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | T2 evidence plus archive-boundary review | 现有 T2 evidence 与 archive-boundary review | Automatic | Yes |
| AC-02 | focused topic/archive tests plus state-integrity review | 本合同锁定的 protected tests 与闭合式复核 return | Automatic | Yes |
| AC-03 | protected negative test and archive-boundary review | 本合同锁定的 protected tests 与 archive-boundary review | Automatic | Yes |
| AC-04 | regression-ssot review | 现有 regression、browser gate 与 technical preflight evidence | Automatic | Yes |
| AC-05 | release synthesis | frozen manifest、两条 closure return 与 machine acceptance metadata | Automatic | Yes |
| H-01 | human checklist | acceptance/human/A4-topic-observation-dogfood/checklist.md#h-01 | Human | Yes |

## Exploratory testing

None. 本轮只允许对 F1 至 F4 进行闭合式复核，不新增探索性验收要求。

## Production monitoring and rollback

Not applicable for this acceptance slice. 本合同不证明生产或设备行为，也不授权公开发布。

## Risks and open decisions

1. 位于 threat model 或 durability model 之外的 observation 必须写入 review return 的 `residual_risk`，severity 固定为 `P3`，non-blocking；不得进入 `blocking_findings`，不得改变 Verdict。

2. 未来确实需要处理的 residual risk，只能登记为下一 release slice 的 candidate node；不得重开 A4，不得在本轮修改 A4 contract。

3. 从 contract v3 开始，只有以下三类事件能够使 A4 acceptance 失效：

   * 模型内 AC failure；
   * protected acceptance test 被删除、弱化、跳过或 hash 非授权变化；
   * human H-01 明确拒绝。

模型外 observation 不得重新打开 A4。
