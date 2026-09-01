# Acceptance Contract: R1-regression-evaluation

- Task ID: R1-regression-evaluation
- Contract version: 11
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: 评测负责人
- Approval evidence: 用户于 2026-09-01 批准 R1 验收并要求尽量使用 AI 审阅，随后明确剩余闭环使用 local CI；v11 保留两条独立持久化 PASS 报告要求，并将冻结输入完整性、运行来源和路径组件隔离统一纳入 fail-closed 门禁。
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/R1.json
- SSOT node: R1
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/.ssot/manifest.json
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.amendment@2
- Assumption IDs: none
- Invalidation keys: implementation.problem-intelligence.regression
- Baseline identity: origin/main@3f1b69b5ab315442591f40295b036cd0d072be4e
- Human acceptance workspace: acceptance/human/R1-regression-evaluation
- UI Change declaration: none

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
| AC-05 | 消融边界复审必须在冻结输入上由 Luna L3 零写入审阅进程产出持久化 `PASS` 报告和运行记录 | Review evidence/Unit | Automatic | Yes |
| AC-06 | 身份与合同复审必须在同一冻结输入上由 Sol L4 独立零写入审阅进程产出持久化 `PASS` 报告和运行记录 | Review evidence/Unit | Automatic | Yes |
| AC-07 | 冻结清单必须使用 `r1-regression-evaluation-v11` 固定 profile，必需输入集合必须 exact-match，本地与远程提交身份必须相同；路径、SHA-256、重复、越界、符号链接或任一项漂移均 fail closed | Static/Unit | Automatic | Yes |
| AC-08 | 每个 AI lane 必须绑定独立的 execution/session/PID、包装器摘要、prompt 摘要、零写入日志和终态运行记录；报告、记录和日志的任一路径组件不得为符号链接 | Review evidence/Unit | Automatic | Yes |

## Human acceptance

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 评测负责人确认结果只用于小样本路线比较，未包装成统计性能 | acceptance/human/R1-regression-evaluation/checklist.md#h-01 | 评测负责人 | Yes |

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| tests/test_v02_regression_evaluation.py | 4aca520f3d27dd30a0d6422057df0742605b3c292c0f672f136781de66f71433 | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-08 |
| tests/test_frozen_review_inputs.py | 1e2bb185190579a45402f54096c98f14da9f338c7fbaa4f3075b3f5cfe60b64c | AC-07 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | focused unit tests | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-02 | focused unit tests | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-03 | tamper/negative tests | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-04 | import/source guard | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-05 | frozen review ledger and report integrity gate | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-06 | distinct reviewer identity, wrapper, terminal verdict and report integrity gate | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| AC-07 | full frozen-input manifest validator and negative path/drift tests | scripts/validate_frozen_review_inputs.py; tests/test_frozen_review_inputs.py; .harness/guards/frozen-review-inputs.md | Automatic | Yes |
| AC-08 | durable run-record/log provenance and ancestor-symlink negative tests | tests/test_v02_regression_evaluation.py | Automatic | Yes |
| H-01 | human checklist | acceptance/human/R1-regression-evaluation/checklist.md#h-01 | Human | Yes |

## Exploratory testing

检查一条零增量路线、跨例重复命中、空未决项、边界人工分钟和 JSON 字段顺序变化；探索结果不改变发布判定。

## Production monitoring and rollback

不适用。R1 是本地评估工件，不进入生产运行；若夹具或算法变更，废止当前工件并以新版本重新验收。

## Risks and open decisions

小样本只代表固定 A4 档案，不代表检索系统总体准确率、召回率或文献开放性；真实外部文献检索仍未由本合同覆盖。

合同版本 9 保留版本 8 的夹具、主题和来源身份闭合，并将两份独立 AI 复审维持为硬性、可机读的接受条件。报告完整性检查对冻结清单摘要接受等价的 Markdown 定界表达，避免把无语义差异的反引号写法误判为证据缺失；Q1 生命周期测试明确允许 R1 已重新接受而 Q1 仍阻断的中间状态；已接受分支不仅核验当前合同版本，还必须读取报告绑定的冻结清单，逐项比对当前受保护测试、R1 合同、人工绑定和清单的 SHA-256，阻止旧合同的整套报告/清单被重标后回放。每份报告还必须位于该冻结清单同一 campaign 的 `reports/<lane>.md`，正文自报与证据元数据一致的 lane、审阅身份和包装器，并以 `Verdict: PASS` 作为唯一终态末行；这样同一文件、prompt 或伪造元数据不能冒充两份独立报告。缺少报告、传输超时、非终态输出、候选身份不匹配、重复审阅身份或任意非 `PASS` 均 fail closed。该修订重新打开 R1，并仅失效其后继 Q1 与 A5；历史 R1 证据只保留为不可接受的审计记录。

Version 9 guard: the accepted review gate rejects reports unless the two report paths are distinct non-symlink regular files, their observed SHA-256 values differ, and each report contains exactly one lane marker, reviewer identity marker, and wrapper marker matching its evidence metadata. The protected negative test constructs one byte-identical report containing both lanes' declarations, hard-links it into both expected report paths, updates both synthetic report hashes, and verifies rejection. This is a stable review-integrity failure class; retry5 artifacts created before this guard are invalidated and cannot count as acceptance evidence. The guard does not expand the acceptance scope or limitations.

Version 10 guard: `scripts/validate_frozen_review_inputs.py` validates every manifest input rather than a selected prefix. It requires unique normalized project-relative POSIX paths, unique resolved file identities, a project-local non-symlink manifest, non-symlink regular input files inside the project root, lowercase SHA-256 values, and exact byte hashes. The protected negative tests drift an item after the fourth entry and also cover duplicate, hard-link alias, missing, non-normalized, escaping, symlink, and CLI repair-output paths. `.harness/guards/frozen-review-inputs.md` records the stable failure class, red/green proof, calibrated scope, and repair path. A current formal review campaign must run this validator successfully before either AI lane may issue `Verdict: PASS`. This hardening does not change R1 output semantics or widen its acceptance boundary.

Version 11 guard: the manifest schema now fixes one explicit R1 input profile and requires the exact eleven immutable inputs consumed by the two review lanes; omitted or extra files, an unknown profile, schema drift, or different local/remote candidate heads are rejected. The mutable R1 evidence and SSOT node are intentionally excluded from the manifest because accepting the node after review would otherwise create a self-invalidating hash cycle; their terminal identities remain enforced by the acceptance-state tests. Each report now binds a separate durable run record and log with distinct execution ID, Codex session, PID, wrapper identity, prompt hash and log identity, terminal exit code zero, and empty changed-path list. All report/run/log path components are checked for symlinks and exact campaign containment. These checks provide repository-level process provenance; they do not claim protection against replacement of the entire local repository trust root.
