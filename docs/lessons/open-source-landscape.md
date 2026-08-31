# Open-source theorem-proving landscape and MathArc integration targets

Status date: 2026-08-23. This is an architectural comparison, not a claim that MathArc has already exceeded every model on formal-proof pass rate.

## Primary integration targets

- **LeanDojo** — Lean interaction/data infrastructure and reproducible theorem-proving research environment: <https://github.com/lean-dojo/LeanDojo>
- **LeanAgent** — continual/lifelong theorem proving over Lean repositories: <https://github.com/lean-dojo/LeanAgent>
- **DeepSeek-Prover-V2** — open model/research assets for Lean theorem proving: <https://github.com/deepseek-ai/DeepSeek-Prover-V2>
- **Goedel-Prover-V2** — open Lean prover research assets: <https://github.com/Goedel-LM/Goedel-Prover-V2>
- **miniF2F** — a cross-system formal-mathematics benchmark: <https://github.com/openai/miniF2F>
- **Pantograph** — programmatic Lean interaction suitable for proof-search adapters: <https://github.com/stanford-centaur/PyPantograph>

These systems are potential backends or benchmark peers. MathArc's layer sits above them: it freezes the research claim, routes work across mechanisms, governs evidence, remembers failures, and controls what can be publicly claimed.

## Capability comparison semantics

The matrix in `benchmarks/framework-capability-matrix.json` uses three values:

- `native`: a first-class system responsibility;
- `partial_or_external`: possible through surrounding code or integrations but not the central contract;
- `unknown`: not scored without a reproducible audit.

No external model score is copied into MathArc's headline metrics. A controlled evaluation must use the same theorem split, timeout, compute budget, Lean version, retrieval corpus, and pass@k definition.
