# Acceptance Contract: Q1-calibration-disclosure

- Task ID: Q1-calibration-disclosure
- Contract version: 4
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: 研究负责人
- Approval evidence: 用户已要求持续完成、验收通过并逐阶段推送 GitHub；R1 合同版本 9 已以两份独立持久化 PASS 报告和 H-01 接受。Q1 合同版本 4 明确重新绑定当前 R1 身份并保留全部未校准及禁止公开边界。
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/Q1.json
- SSOT node: Q1
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/.ssot/manifest.json
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.amendment@2
- Assumption IDs: none
- Invalidation keys: validation.problem-intelligence.calibration-disclosure
- Baseline identity: origin/main@757feb11c6d6c05bb43332bcf3c1a523a7833a7d
- Human acceptance workspace: acceptance/human/Q1-calibration-disclosure

## User and scenario

研究负责人需要基于当前已接受 R1 三例固定回归夹具，记录困难度、研究优先级和传播边界，而不把该记录伪装为已校准预测、数学结论或公开发布授权。

## Problem

R1 固定了三例和四路检索增量，但没有机器可核验的困难度记录或披露限制。缺少该对象时，研究优先级可能被误当作传播准备度，小样本记录也可能被误读为统计性能或发布结论。

## Expected outcome

存在一个严格序列化的 Q1 政策夹具，逐字节绑定已接受的 R1 evidence 与回归夹具身份及内容摘要；三例均为 `UNCALIBRATED`，每例独立保留科学优先级与 `NOT_READY` 传播状态，并统一禁止数学证明、开放状态确认、新颖性接受、统计性能和公开发布结论。

## Non-goals

不进行网络检索、数学证明、开放状态确认、外部文献核验、统计校准、准确率/召回率/泛化计算、ResearchTrace/ClaimStatus 写入、新颖性授权、预算授权或生产发布。

## Normal path

```gherkin
Given a byte-locked current accepted R1 evidence record and its fixed three-case regression fixture
When the Q1 disclosure policy is loaded
Then it validates every source identity, case identity, uncalibrated label, priority, readiness, disclosure limit, and policy digest
And it returns a passive non-public policy record
```

## Exception paths

- R1 evidence ID、R1 evidence 摘要、夹具字节摘要、夹具内容摘要、主题或案例顺序漂移时必须拒绝。
- 缺少或多出字段、案例、限制项，或写入未知困难度/校准状态/科学优先级/传播状态时必须拒绝。
- 任意记录改为 `CALIBRATED`、`PUBLIC_READY`，或移除限制项时必须拒绝；不得降级为可发布结果。
- 策略摘要不一致时必须拒绝；失败时不产生部分政策或任何授权。

## Invariants

- Q1 只接受 `union-closed` 的 R1 固定三例及其既定顺序。
- 所有当前预测均为 `UNCALIBRATED`；传播准备度恒为 `NOT_READY`，不能由科学优先级提升。
- 每例的限制集合完整、去重且排序稳定，且 `public_release_allowed` 恒为 `false`。
- Q1 是只读、纯本地、被动的政策记录，不导入授权、声明、新颖性审计或网络能力。

## Data impact

仅新增不可变的本地 JSON 政策夹具和内存值对象；不修改数据库、运行时状态、R1 来源或外部系统。

## Permissions

研究负责人维护困难度和科学优先级的人工声明；研究负责人和仓库所有者保留后续 A5 发布决定权。Q1 本身无权发布或确认数学结论。

## Performance and reliability

固定三例政策加载应在 1 秒内完成；重复加载同一字节必须得到相同政策摘要；任一完整性校验失败均 fail closed。

## Acceptance criteria

| ID | Requirement | Verification layer | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | 三例、主题、R1 evidence、R1 夹具字节和内容身份被严格闭合 | Unit | Automatic | Yes |
| AC-02 | 未校准标记、科学优先级与传播准备度保持双轨分离 | Unit | Automatic | Yes |
| AC-03 | 身份、状态、优先级、限制、字段或摘要篡改均 fail closed | Unit | Automatic | Yes |
| AC-04 | 工件不授权公开发布，不依赖声明、新颖性或统计性能能力 | Static/Unit | Automatic | Yes |

## Human acceptance

| ID | Summary | Checklist path | Required role | Blocking |
| --- | --- | --- | --- | --- |
| H-01 | 研究负责人确认三例的优先级和披露措辞没有越过未校准、小样本与数学结论边界 | acceptance/human/Q1-calibration-disclosure/checklist.md#h-01 | 研究负责人 | Yes |

## Protected acceptance tests

| Path | SHA-256 | Covers |
| --- | --- | --- |
| tests/test_v02_calibration_disclosure.py | 89d52c973a0d5e026da855aef85a57db8656e6cc5b593b98f09ff6d2541318db | AC-01, AC-02, AC-03, AC-04 |

## Requirements-test traceability

| Requirement | Verification | Evidence target | Mode | Blocking |
| --- | --- | --- | --- | --- |
| AC-01 | fixed-source and three-record unit tests | tests/test_v02_calibration_disclosure.py | Automatic | Yes |
| AC-02 | priority/readiness unit test | tests/test_v02_calibration_disclosure.py | Automatic | Yes |
| AC-03 | identity, status, disclosure and digest tamper tests | tests/test_v02_calibration_disclosure.py | Automatic | Yes |
| AC-04 | static dependency boundary test | tests/test_v02_calibration_disclosure.py | Automatic | Yes |
| H-01 | human checklist | acceptance/human/Q1-calibration-disclosure/checklist.md#h-01 | Human | Yes |

## Exploratory testing

检查高科学优先级但仍不可传播的记录、合法的零外部结论、字段顺序变化、未知字段、错误类型和重新计算摘要后的来源漂移；探索结果不能升级校准、开放状态或发布结论。

## Production monitoring and rollback

不适用。Q1 是本地政策工件，不进入生产；若 R1 夹具、校准证据或定义变更，废止当前政策夹具并重新验收，不能沿用其优先级或披露结论。

## Risks and open decisions

三个固定案例不构成校准样本，也不构成统计性能、泛化、外部文献或独立数学审阅。是否公开任何范围仍由 A5 的独立发布决定处理。R1 身份、固定夹具或本合同的保护测试任一变化均使 Q1 失效，并要求 A5 重新验收。
