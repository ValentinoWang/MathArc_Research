# MathArc Research engineering progress

Status date: 2026-08-23.

Percentages below measure completion against the frozen `v0.1 research-agent demonstration` engineering contract. They are not probabilities that an open conjecture is true, solvable soon, or already proved.

| Stage | Completion | Closed evidence | Remaining work |
|---|---:|---|---|
| Conversation and proof-run audit | 100% | Frankl, graceful-tree, Erdős–Szekeres, Hadwiger–Nelson, Hadamard, and no-three-in-line failure/success patterns converted into rules | Continue adding new runs as regression fixtures |
| Theorem contract, scope and trust model | 100% | Separate scope/trust lattices, frozen theorem contract, quantifier-safe evidence promotion | Formal JSON Schema export and migration tooling |
| Claim DAG, failure propagation and release gates | 100% | Dependency cycle guard, refutation propagation, independent reconstruction gate, certificate debt | Distributed/event-sourced persistence |
| Deterministic tools and proof-carrying research runs | 94% | Exact polynomial/induction tools; Frankl q=6 zero-, one-, two-, and three-small-part layers closed with independent certificates | Attack four-or-more-small q=6 residual; kernel-test Lean and add SAT/SMT/interval adapters |
| Startup dashboard, public reasoning trace and API | 90% | Static dashboard, route/claim/tool/failure views, read-only JSON API, investor demo script | Live worker streaming, route graph visualization, role-based views |
| Tests, replay, container and CI | 94% | Unit/regression tests, atomic serialization, dual Python/C++ certificates, SHA manifests, Docker image, Python 3.10/3.12 CI replay contract | Resolve repository-level Actions `startup_failure`; add signed release manifest and more hostile fixtures |
| Controlled comparison with open-source provers | 30% | Framework capability matrix and benchmark protocol | Run equal-budget miniF2F/Lean repository evaluations and independent replay |
| Open-conjecture theorem closure | Binary per problem | Frankl q=6 outside-balance bridge closed whenever at most three small outside parts occur | Remaining q=6 counterexample must contain at least four small outside parts; global Frankl remains open |

## New strict mathematical milestones

In the minimum-three-set, six-outside-element Frankl trace setup:

1. exactly two small outside parts have exact orbit minima
   \[
   0,0,6,6;
   \]
2. exactly three small outside parts have eleven exact orbit minima
   \[
   0,6,6,6,6,6,6,6,6,6,24.
   \]

The two-small Python implementation re-enumerates all 8 singleton and 45 pair trace-family types, and an independent C++ implementation reconstructs the 42-core branch-and-bound. The three-small Python/NumPy implementation regenerates all 11 canonical \(S_6\)-orbits, while a separate C++ implementation independently verifies the 9/10/11-positive-core searches.

Consequently the precise residual moved twice in this round:

```text
at least two small outside parts
  → at least three
  → at least four.
```

## Weighted engineering completion

Using the frozen weights below:

```text
research audit and protocol             15% × 100%
core proof/evidence runtime              25% × 100%
tools and proof-carrying research runs   15% ×  94%
dashboard/API/product surface            15% ×  90%
tests/replay/release engineering         10% ×  94%
external controlled benchmark            20% ×  30%
---------------------------------------------------
MathArc Research v0.1 engineering = 83.0%
```

The next mathematical frontier is now sharply defined: classify admissible small-part hypergraphs of size four or more, use their total negative trace deficit to force additional positive cores, and either prove the coarse outside balance nonnegative or emit an exact surviving configuration for the full trace solver. The separate product frontier remains the controlled external prover benchmark.
