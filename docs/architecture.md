# Architecture

## 1. Control plane

`ResearchEngine` owns the theorem contract, routes, atomic claims, dependency DAG, evidence ledger, tool-call ledger, failure memory, public reasoning cards, and release state. Workers can propose artifacts; only the engine's verifier policy can promote claims.

## 2. Mathematical scope lattice

```text
INSTANCE < FINITE_RANGE < PARAMETRIC_FAMILY < GLOBAL
```

Evidence may support a claim only when its scope is at least the claim's scope. A fixed parameter result is not a global theorem. Quantifier lifts are represented as claims with their own dependencies and exact evidence.

## 3. Trust lattice

```text
UNSUPPORTED < HEURISTIC < TESTED < EXACT < KERNEL_CHECKED < INDEPENDENT_REPLAY
```

Trust and scope are orthogonal. A perfectly exact certificate for one instance remains instance-scoped.

## 4. Event flow

```text
Problem card
   ↓
Route portfolio ── mechanism fingerprints / basin diversity
   ↓
Claim DAG ─────── dependencies / criticality / scope / trust requirement
   ↓
Tool adapters ─── exact arithmetic / SAT-SMT / CAS / Lean / search
   ↓
Evidence ledger ─ content hash / replay command / producer / independence
   ↓
Adversarial audit ─ counterexample / scope / assumptions / circularity
   ↓
Independent reconstruction
   ↓
Release gate ─── graded state + binary theorem closure
```

## 5. Public trace versus hidden model internals

MathArc records decision-relevant artifacts, not raw hidden model chain-of-thought. A reasoning card contains the objective, explicit hypothesis, action, observation, falsification attempt, decision, and artifact references. This is sufficient for reproducibility and human review and avoids treating unverifiable introspective prose as mathematical evidence.

## 6. External prover adapters

Lean, SMT solvers, CAS systems, search programs, and LLM theorem provers are worker tools. Their process exit becomes a tool event. Mathematical promotion requires statement correspondence, accepted certificate semantics, exact scope, and—in high-stakes cases—independent replay.
