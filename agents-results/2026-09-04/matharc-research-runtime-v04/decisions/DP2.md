# DP2 — 首版后端范围

- 日期：2026-09-04
- 确认人：用户（本次 v2 修订请求）
- 决定：首版 MathArc 运行时只承诺 `DeterministicTestBackend`、`CodexBackend` 和 `LocalExactToolBackend` 三类后端。它们都必须通过 MathArc 后端接口返回候选结果，不得拥有 RuntimeStore、ResearchTrace 或数学结论晋升权。
- 后置范围：Claude Code 与通用模型 API 保留为后续可替换后端，不进入首个邀请制试点的完成条件，也不阻塞首版运行时合同、验证和试点部署。
- 约束：后端名称、输入输出合同、预算和失败分类由 MathArc 原生运行时登记；未登记后端必须 fail-closed。
