# MathArc Research v0.2 Architecture

## 1. Design objective

The system must support research in which the final theorem may remain open for many rounds.  Its core output is therefore not a single answer but a tamper-evident research state:

```text
TheoremContract
    │
    ▼
Claim DAG ───── Evidence registry
    │                  │
    ├── Route ledger   ├── Tool-call ledger
    │                  │
    ├── Failure graph  └── Independent audit groups
    │
    ▼
Verifier-gated release state
```

Language models propose moves.  They do not possess claim-promotion authority.

## 2. Trust boundary

### Proposal layer

The following components can generate candidate content:

- Codex or another language-model worker;
- a natural-language mathematics agent;
- a formal proof-search worker;
- a SAT/SMT/MILP search process;
- a human researcher.

Proposal output may create or revise `PROPOSED`, `OPEN`, `CANDIDATE`, or `BLOCKED` records.  It cannot write `PROVED`.

### Evidence layer

Evidence objects contain:

- exact claim IDs;
- artifact URI and SHA-256 digest;
- producer and verifier;
- independence group;
- replay command;
- checked assumptions;
- statement correspondence;
- limitations.

### Promotion layer

`ResearchTrace.promote_claim` is the only v0.2 promotion path.  It verifies:

1. status is not terminal;
2. every dependency is `PROVED`;
3. proof-capable evidence exists;
4. critical claims have at least two independent groups;
5. critical evidence is replayable;
6. statement correspondence is explicit.

A failed promotion attempt is preserved as a boundary violation and lowers `boundary_integrity`.

## 3. Research cycle

### Stage A — Contract

Freeze target statement, scope, assumptions, sources, success criteria and non-claims.

### Stage B — Decompose

Create typed claims in dependency order.  Weights measure logical load, not subjective confidence.

### Stage C — Diversify

Create routes with:

- hypothesis;
- mechanism signature;
- kill test;
- expected discriminator;
- linked claim IDs.

Exact duplicate mechanism signatures are rejected.

### Stage D — Falsify

Run cheap counterexample, boundary and definition tests before expensive expansion.  An exact failure changes claim and route status and blocks all dependent claims.

### Stage E — Construct

The prover submits one atomic lemma, exact reduction, certificate or formal proof candidate.

### Stage F — Verify

An independent worker reconstructs the result.  Generator and verifier common-mode risk is represented by `independence_group`.

### Stage G — Synthesize

Report the strongest strict result, open critical obligations, release state and claim boundary.

## 4. Agent roles

| Role | Authority | Required output |
|---|---|---|
| Strategist | proposal | next load-bearing node, mechanism-distinct routes, kill tests |
| Prover | proposal | atomic derivation or certificate contract |
| Falsifier | conservative status change | minimal witness or exact PASS attack record |
| Verifier | evidence proposal | replay, hashes, statement correspondence, independence group |
| Synthesizer | reporting | strongest strict claim and open obligations |
| ResearchTrace gate | promotion | deterministic acceptance or explicit rejection reasons |

## 5. Open-source adapter architecture

### Natural-language research agents

These systems can be connected to the proposal layer.  Their free-form output is translated into the v0.2 public schema and stripped of proof authority.

### LeanDojo

LeanDojo is an intended formalizer adapter.  A successful adapter must return pinned Lean/mathlib revisions, theorem state, proof term, kernel outcome, resource budget and replay command.

### LeanStar or other proof search

A search system becomes one formal route worker.  Search-tree expansion, proof term and budget belong to one route record; success is still checked by the Lean kernel and then attached as evidence.

### PutnamBench and formal suites

Benchmarks supply pinned case manifests.  MathArc adds paired seeds, equal-budget accounting, false-promotion tracking, evidence replay and research-process metrics.

### Exact mathematical tools

SAT, SMT, MILP, Gröbner basis, symbolic normalization, interval arithmetic and bespoke certificate checkers implement one common tool record.  The interface does not treat a zero exit code alone as evidence: output digest, expected discriminator and statement correspondence remain mandatory.

## 6. Storage model

A run can be stored as:

```text
run/
├── research-trace.json
├── research-metrics.json
├── failure-memory.json
├── benchmark-comparison.json
├── research-dashboard.html
├── artifacts/
│   ├── certificates/
│   ├── verifier-output/
│   └── literature/
└── replay/
    ├── environment.lock
    └── reproduce.sh
```

The JSON trace is canonical authority.  The HTML dashboard is a read view.

## 7. Security and correctness properties

- Unknown schema fields are rejected.
- Private chain-of-thought field names are rejected.
- Proved claims are immutable; revision requires retraction and a new claim.
- Claim DAG cycles are rejected.
- Forward references are rejected during construction.
- Critical claims require independent evidence.
- Numerical experiments cannot promote a universal theorem.
- Exact failure propagates through descendants.
- Metrics never change claim status.
- Benchmark results cannot authorize a mathematical theorem.
- Benchmark superiority is scoped to a pinned suite and budget.

## 8. UI panels

The self-contained dashboard displays:

1. release state and target closure;
2. weighted claim DAG;
3. critical path;
4. public research timeline;
5. route mechanism signatures and kill tests;
6. tool calls and replay commands;
7. failure diagnosis, witness and repair;
8. evidence independence and audit debt;
9. benchmark qualification state;
10. exact claim boundary.

The visual priority is not token volume.  It is the distance from the current state to a verifier-accepted target.

## 9. Extension points

The next code-level interfaces should be:

```python
class ProposalWorker(Protocol):
    def propose(self, round_plan: ResearchRoundPlan) -> AgentProposal: ...

class ExactToolAdapter(Protocol):
    def run(self, request: ToolRequest) -> ToolCallRecord: ...

class FormalizerAdapter(Protocol):
    def prove(self, claim: ClaimRecord) -> EvidenceRecord: ...

class LiteratureAdapter(Protocol):
    def verify_source(self, citation: SourceClaim) -> EvidenceRecord: ...
```

Every adapter remains outside the promotion boundary.
