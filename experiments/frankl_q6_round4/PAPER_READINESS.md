# Frankl q=6 — paper-readiness gate

Status date: 2026-08-23

## Evidence status

The repository preserves a historical machine-checked candidate report for the following frozen statement:

> If a finite union-closed family has a minimum nonempty member of size three and exactly six outside elements, then the family satisfies Frankl's conclusion.

The 2026-08-23 report states that a monolithic verifier accepted the complete bridge, checked all `244,068` residual trace-type multisets for the `k=4,5,6,7` layers, and produced two byte-identical outputs with SHA-256 `f98e52d7ce76c131ae5b7db55114d25616b555887eae059591b67ae6ab5f2719`.

The current checkout cannot reproduce that result: three declared verifier sources and all eight component-result files are absent. Its current status is **`ARCHIVE_INTEGRITY_PASS / FULL_COLD_REPLAY_UNAVAILABLE`**. This preserves a historical claim record; it is not current replayable proof and does not mean that Frankl's full conjecture has been proved.

## Literature / novelty boundary

The truth of this scoped theorem is not itself a new Frankl case: its universe has size `|S|+|Omega|=3+6=9`, and Frankl's conjecture was already known for universes of this size.

Therefore the paper must not claim “the first proof of the nine-element case.” The potentially publishable contribution is instead the trace-fiber/charge proof architecture, the structural decomposition of the residual cases, the dual modular/monolithic replay pipeline, and the MathArc Research methodology that discovered, falsified and closed the proof obligations.

## Gate status

| gate | status | remaining work |
|---|---|---|
| Internal proof-DAG closure | **HISTORICAL RECORD / CURRENTLY UNVERIFIED** | restore missing sources and component results, then cold replay |
| Deterministic replay and hashes | **BLOCKED** | current archive hash passes, but historical full-output/source hashes are not bound to complete tracked objects |
| Second code path | **HISTORICAL RECORD / CURRENTLY UNVERIFIED** | modular and monolithic agreement cannot be rerun from this checkout |
| Human mathematical audit | **OPEN** | independent combinatorics researcher checks every reduction |
| Novelty/literature audit | **OPEN** | compare trace-fiber and charge lemmas with FC-family, Poonen-weight and small-universe literature |
| Paper-facing artifact freeze | **BLOCKED** | archive summary is frozen; complete source/output release is absent |

## Paper decision

**Historical drafting may continue, but any current proof claim and submission remain blocked.**

A defensible first manuscript would be an agent-assisted/computer-assisted proof-method paper, not a theorem-priority paper. Before arXiv or journal submission, first restore and cold-replay the complete exact artifact release, then obtain an independent mathematical audit and a literature/novelty comparison.

## Recommended one-sentence contribution

> We develop a replayable trace-fiber and charge proof architecture for a nine-element Frankl subclass, while MathArc Research autonomously decomposes the problem into proof obligations, kills false routes, generates exact verifiers, and closes the evidence DAG without overstating the still-open global conjecture.
