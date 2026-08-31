# Open-source mathematics-agent integration and comparison matrix

## 1. Scope

This matrix separates three questions that are often conflated:

1. **What capability does a project expose?**
2. **Where can that capability enter the MathArc architecture?**
3. **Has an equal-budget comparison actually been run?**

The third answer is currently `no` for every registry entry.  Therefore the repository does not claim measured universal superiority.

## 2. Integration targets

| Project | Repository | Primary contribution | MathArc role | Required additional contract | Measured in v0.2 branch |
|---|---|---|---|---|---|
| Math Research Agent | `Shengrong-Wu/Math-Research-Agent` | natural-language research workflow | proposal worker / baseline | public-reasoning schema, claim IDs, budget log, artifact hashes | No |
| LeanDojo | `lean-dojo/LeanDojo` | reproducible interaction with Lean repositories and proof states | formalizer infrastructure | pinned Lean/mathlib revisions, kernel result, replay command | No |
| LeanStar | `facebookresearch/LeanStar` | formal proof search | mechanism-distinct formal route | search budget, proof term, tree statistics, kernel replay | No |
| PutnamBench | `trishullab/PutnamBench` | formalized competition-level evaluation suite | benchmark source | pinned case manifest, paired seeds, common budget | No |

Machine-readable entries live in `benchmarks/agent_registry_v02.json`.

## 3. Why these systems are complementary

A natural-language research agent can propose decompositions and analogies, but it does not automatically provide kernel-checked proof artifacts.  LeanDojo supplies formal-environment infrastructure but does not by itself manage long-running informal research routes, failed definitions, literature claims, or cross-project failure memory.  LeanStar contributes a proof-search mechanism inside the formalizer route.  PutnamBench contributes evaluation cases, not an orchestration policy.

MathArc v0.2 places them behind explicit trust boundaries:

```text
Natural-language worker ─┐
Lean search worker ──────┼─> proposal/evidence adapters ─> ResearchTrace gate
Exact solver ────────────┤
Human mathematician ─────┘
```

No adapter can write `PROVED` directly.

## 4. Comparison dimensions

### 4.1 Mathematical outcome

- target logical closure;
- formally verified theorem count;
- exact counterexample count;
- strongest strict result when the target remains open;
- false promotion count.

### 4.2 Research process

- critical-path closure;
- mechanism-distinct route coverage;
- falsification coverage;
- useful-failure rate;
- failure reuse across later cases;
- number of hidden assumptions found before final synthesis.

### 4.3 Evidence quality

- statement-correspondence rate;
- independent-audit coverage;
- cold-replay rate;
- generator/checker separation;
- artifact and environment hash completeness.

### 4.4 Efficiency

- tokens and tool calls per closed critical node;
- wall time and compute budget;
- search nodes per formal proof;
- failed routes killed before expensive expansion;
- human audit minutes per accepted theorem.

### 4.5 Calibration and honesty

- Brier score for preregistered claim forecasts;
- frequency of local-to-global overclaim;
- frequency of declaring completion with open critical nodes;
- precision of `PROVED_AND_AUDITED` releases;
- abstention quality on unresolved targets.

## 5. Visual comparison design

The startup demonstration should use five synchronized views.

### View A — Outcome frontier

A scatter plot with audited target closure on the vertical axis and normalized budget on the horizontal axis.  A point is hollow until cold replay passes.  False promotions are shown separately and cannot be averaged away by more solved cases.

### View B — Research-state waterfall

For each case:

```text
initial obligations
  - exact failures found
  - redundant routes merged
  - claims proved
  + newly exposed obligations
= final open critical obligations
```

### View C — Evidence matrix

Rows are critical claims; columns are independent evidence groups.  A claim has a green row only after its required groups pass replay.

### View D — Failure reuse graph

A directed edge connects an earlier failure lesson to a later route when the lesson changes the later plan.  This measures actual learning across projects rather than prompt-level self-description.

### View E — Qualification board

Every baseline comparison displays:

- paired case count;
- suite and version;
- budget equality;
- cold-replay status;
- candidate false promotions;
- paired bootstrap interval for each primary metric;
- permitted claim text.

If any gate fails, the board prints `INSUFFICIENT_EVIDENCE` or `NOT_SUPERIOR`.

## 6. Preregistered benchmark families

A research-grade evaluation should not rely on one class of theorem.

| Family | Purpose |
|---|---|
| Formal theorem completion | integration with Lean proof search and kernel checking |
| Exact finite construction | certificate generation and independent checking |
| Counterexample discovery | ability to reverse direction and attack definitions |
| Flawed proof repair | dependency, quantifier, type and hidden-assumption diagnosis |
| Long-horizon research slice | route management and failure reuse across rounds |
| Literature-grounded theorem audit | primary-source matching and novelty boundaries |

Each case must freeze inputs, source versions, tool versions, time and token budgets, seeds, acceptance predicates and output hashes before comparison.

## 7. Qualification rule

For a baseline \(B\), MathArc is allowed to state a benchmark-scoped advantage only when:

1. at least 30 case-seed pairs are shared;
2. every pair uses the same pinned case and equal budget;
3. every candidate and baseline artifact cold-replays;
4. MathArc has zero false promotions;
5. each preregistered primary metric has a strictly positive 95% paired-bootstrap lower bound after direction normalization.

Even then the allowed statement is:

> MathArc v0.2 outperformed baseline B on the pinned suite, versions, adapters and budgets reported here.

The system is never allowed to convert this into “stronger for all mathematics” or “stronger than every existing agent” unless every named baseline independently passes the same qualification gates—and even that conclusion remains benchmark-scoped.
