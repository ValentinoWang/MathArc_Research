# Acceptance Contract: R1-regression-evaluation

- Task ID: R1-regression-evaluation
- Contract version: 4
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: 评测负责人
- Approval evidence: 用户于 2026-09-01 批准修订 R1 验收，要求两条独立 AI 复审均产出持久化 PASS 报告；缺失、停滞或非 PASS 报告均阻断接受
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/R1.json
- SSOT node: R1
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/.ssot/manifest.json
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.amendment@2
- Assumption IDs: none
- Invalidation keys: implementation.problem-intelligence.regression
- Baseline identity: origin/main@2e47f5040d3a833e10de07286d68f017efec5d42
- Human acceptance workspace: acceptance/human/R1-regression-evaluation

## User and scenario

评测负责人需要在已接受的 A4 三例档案上比较四条检索路线的具体增量，使用本地固定夹具记录命中、漏检、未决项和人工耗时。

## Problem

当前没有 R1 专用回归集或消融记录，不能证明四路结果被独立保留，也不能区分某一路的独有命中与其他路线重复命中。

## Expected outcome

存在一个严格可序列化的回归评估工件：固定绑定 A4/T2 身份和三例档案；每例恰有四路；可确定性计算全路覆盖、每路增量和留一路损失；仅报告 hit/miss/gap 与人工分钟，不输出准确率、召回率、泛化或公开结论。

## Non-goals

不进行网络检索、数学证明、生产部署、ResearchTrace/ClaimStatus 写入、预算授权、新颖性授权或统计性能推断。

## Normal path

```gherkin
Given a hash-bound three-case fixture with four independent search routes per case
When the regression suite is deserialized and evaluated
Then deterministic full coverage, route increments, leave-one-route-out loss, gaps, and bounded human minutes are returned
And the result remains a passive evaluation artifact
```

## Exception paths

- 缺少/多出档案或路线、复制查询/来源、错误摘要、A4/T2 身份漂移必须拒绝加载。
- 篡改命中、漏检、人工分钟或消融值必须因摘要或重算不一致而拒绝。
- 零增量路线必须保留为合法结果，不能被当作缺失数据。
- 不允许网络、持久运行时状态或外部服务；失败时不产生部分可接受结果。

## Invariants

- 三例身份、四路顺序、路线范围/查询/来源独立性、主题和固定夹具内容摘要在加载时闭合。
- 每一路增量命中必须确实不在其余路线的命中集合中；留一路损失由全路与去一路集合重算。
- hit、miss、gap 是封闭枚举；人工分钟为有限非负数并受上限约束。
- 评估不导入 `ResearchTrace`、`ClaimStatus` 或 `authorize`，不产生授权字段。

## Data impact

只读加载固定 JSON，生成内存中的不可变评估结果；不修改业务数据库、运行时状态或来源文件。

## Permissions

评测负责人可创建和评估 R1 工件；验收负责人复核机器证据；研究负责人和仓库所有者保留发布决定权。

## Performance and reliability

本地三例四路评估应在 1 秒内完成；重复加载同一字节必须得到相同摘要和结果；任何校验失败均 fail closed。

## Acceptance criteria

| ID | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 三例固定绑定且每例恰有四路独立记录 | Unit | Automatic | Yes |
| AC-02 | 全路、增量、留一路损失和 hit/miss/gap 确定性重算 | Unit | Automatic | Yes |
| AC-03 | 摘要、身份、范围、来源、人工分钟或消融篡改 fail closed | Unit | Automatic | Yes |
| AC-04 | 结果不含授权、声明或 ResearchTrace/ClaimStatus 依赖 | Static/Unit | Automatic | Yes |
| AC-05 | 消融边界复审必须在冻结输入上由独立零写入审阅进程产出持久化 `PASS` 报告 | Review evidence/Unit | Automatic | Yes |
| AC-06 | 身份与合同复审必须在同一冻结输入上由不同审阅身份的独立零写入审阅进程产出持久化 `PASS` 报告 | Review evidence/Unit | Automatic | Yes |

## Human acceptance

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 评测负责人确认结果只用于小样本路线比较，未包装成统计性能 | acceptance/human/R1-regression-evaluation/checklist.md#h-01 | 评测负责人 | Yes |

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| tests/test_v02_regression_evaluation.py | a8320b5af5c000515b0cd0bb5bc177fa4acc87ee9da63439f80f25edf26022cf | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | focused unit tests | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-02 | focused unit tests | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-03 | tamper/negative tests | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-04 | import/source guard | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-05 | frozen review ledger and report integrity gate | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-06 | distinct reviewer identity, wrapper, terminal verdict and report integrity gate | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| H-01 | human checklist | acceptance/human/R1-regression-evaluation/checklist.md#h-01 | Human | Yes |

## Exploratory testing

检查一条零增量路线、跨例重复命中、空未决项、边界人工分钟和 JSON 字段顺序变化；探索结果不改变发布判定。

## Production monitoring and rollback

不适用。R1 是本地评估工件，不进入生产运行；若夹具或算法变更，废止当前工件并以新版本重新验收。

## Risks and open decisions

小样本只代表固定 A4 档案，不代表检索系统总体准确率、召回率或文献开放性；真实外部文献检索仍未由本合同覆盖。

合同版本 4 保留版本 3 的夹具、主题和来源身份闭合，并将两份独立 AI 复审提升为硬性、可机读的接受条件。每份报告必须绑定同一冻结输入清单、使用不同审阅身份和不同外部包装器，并以 `PASS` 结束；缺少报告、传输超时、非终态输出、候选身份不匹配、重复审阅身份或任意非 `PASS` 均 fail closed。该修订重新打开 R1，并仅失效其后继 Q1 与 A5；历史 R1 证据只保留为不可接受的审计记录。
