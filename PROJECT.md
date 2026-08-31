# MathArc Research project adapter

- **Owning repository:** `ValentinoWang/MathArc_Research`
- **Canonical branch:** `main`
- **Registry profile:** `project-matharc-research`（`extends: core`；活跃项目，不是仅档案命名空间）
- **Namespace:** `./`
- **Frozen engineering contract:** MathArc Research v0.1 — `100% COMPLETE`
- **Current v0.3 implementation status:** `docs/V03_IMPLEMENTATION_STATUS.md`（此文件优先于计划文档中的历史“落地状态”文字，用于记录开发分支实际完成边界）
- **Purpose:** research-grade mathematical discovery orchestration, evidence governance, public structured reasoning traces, Codex-powered interactive workers, and verifier-backed release gates.
- **Upstream method source:** internal `math-research-proof-harness v1.1.0` protocol and audited Frankl, graceful-tree, Erdős–Szekeres, Hadwiger–Nelson, Hadamard, and no-three-in-line runs.
- **Authority split:** Codex and other workers propose; `ResearchEngine`, evidence scope/trust checks, dependency closure, replay, and independent reconstruction determine acceptance.
- **Claim boundary:** the Frankl q=6 frozen special-case contract is internally machine-checked; Frankl's full conjecture remains `INCONCLUSIVE`; comparative superiority remains benchmark-gated.

Runtime evidence belongs in `agents-results/YYYY-MM-DD/<task>/` for repository-facing task evidence. Local interactive Codex sessions are append-only under `.matharc/codex-sessions/` and are ignored by Git. Generated demo and acceptance artifacts under `artifacts/` are also ignored.

Reusable research contracts remain in this project until stabilized. Promotion into `Core/skills/` requires an explicit cross-project SSOT review and at least a second real consumer; v0.1 completion does not silently modify global Harness policy. When reusable MathArc Engine contracts are eventually extracted, this project remains their provenance source rather than a second authority copy.
