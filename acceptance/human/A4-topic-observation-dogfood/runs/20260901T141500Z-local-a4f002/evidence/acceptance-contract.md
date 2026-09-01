# Acceptance Contract: A4-topic-observation-dogfood

- Task ID: A4-topic-observation-dogfood
- Contract version: 2
- Contract status: APPROVED
- Test baseline: LOCKED
- Acceptance owner: 验收负责人（用户授权）
- Approval evidence: 用户批准在离线、来源固定、非数学证明、非公开发布边界内正式验收 A4，并指定使用 local CI；本次重验收将身份重钉到当前已推送的 `main` HEAD `3353d6a`，不扩大原范围。
- Request source: agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A4.json
- SSOT node: A4
- SSOT path: agents-results/2026-08-31/problem-intelligence-plane/.ssot/manifest.json
- Readiness mode: FORMAL
- Decision refs: decision.problem-intelligence.amendment@2
- Invalidation keys: acceptance.problem-intelligence.dogfood
- Baseline identity: main@3353d6aa8ce0e2511773b4ba2f2985bd2dc05a80
- Human acceptance workspace: acceptance/human/A4-topic-observation-dogfood

## Scope

验收一次性主题观测和三例来源固定档案的重放、恢复、去重、预算与失败模式闭环。资料只来自仓库固定字节；结果不构成数学证明、外部文献确认、生产或设备证据，也不授权公开发布。

## Acceptance criteria

| ID | Requirement | Verification | Blocking |
| --- | --- | --- | --- |
| AC-01 | 三例固定档案的身份、状态、来源和不晋升边界完整 | T2 evidence plus archive-boundary review | Yes |
| AC-02 | 重放、恢复、去重、预算和人工队列绑定且篡改 fail-closed | focused topic/archive tests plus state-integrity review | Yes |
| AC-03 | 合同元数据（来源目录与 non-claim boundary）语义不可变 | protected negative test and archive-boundary review | Yes |
| AC-04 | 全量回归、浏览器门禁和技术预检通过且不越界 | regression-ssot review | Yes |
| AC-05 | 当前主线、合同、边、T2 证据和三条独立 AI return 哈希一致 | release synthesis | Yes |
| H-01 | 用户确认本次仅为离线源级验收，不是数学证明或公开发布 | human checklist | Yes |

## Protected acceptance tests

| Path | SHA-256 |
| --- | --- |
| tests/test_v02_topic_observation.py | 1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56 |
| tests/test_v02_dogfood_archives.py | e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873 |

## Non-goals

不进行实时网络检索，不判断数学真伪，不确认外部文献完整性或开放状态，不生成 ResearchTrace/ClaimStatus，不证明生产/设备行为，不授权公开研究结论。
