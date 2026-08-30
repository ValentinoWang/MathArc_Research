# Lessons extracted from MathArc's theorem-proofing runs

This document distills recurring mechanisms from the project's Frankl, graceful-tree, Erdős–Szekeres, Hadwiger–Nelson, Hadamard, and no-three-in-line conversations. It records auditable research behavior rather than private model chain-of-thought.

## 1. Frankl: fixed-parameter success is not a global bridge

**What worked.** Complete finite enumeration, exact flow/compression certificates, and an independent checker closed the frozen `n=5` milestone.

**Why the global proof still failed.** The remaining obligations were quantifier lifts: compression for arbitrary ground sets, global positive-flow existence, and a support-line bridge. Renaming these bridges as lemmas did not reduce their theorem strength.

**Harness rule learned.** Scope and trust must be separate coordinates. A machine-verified finite result may be 100% closed while the global theorem remains binary `0/1 = 0`.

## 2. Graceful trees: local calculus accumulated faster than the universal bridge

**What worked.** Exact label calculations, port operations, infinite recursive classes, and obstruction searches produced genuine theorems and reusable constructions.

**Why repeated rounds stalled.** Most routes eventually depended on a universal compatible relabeling or decomposition theorem. More local examples did not discharge that critical node; they moved activity around the bottleneck.

**Harness rule learned.** Track theorem-strength gap relocation and weight critical obligations separately from easy supporting nodes. Park a route after repeated zero evidence gain unless it supplies a mechanism delta.

## 3. Erdős–Szekeres: an encoding is not a proof certificate

**What worked.** Anchored/order-type subfamilies can be isolated and checked with exact SAT encodings.

**Why the full claim was unsafe.** Until the encoding, symmetry reductions, certificate format, and independent checker are frozen, an UNSAT process exit does not establish the intended geometric statement.

**Harness rule learned.** Lock the verifier before optimization and store statement correspondence, positive/negative/tampered fixtures, and certificate replay.

## 4. Hadwiger–Nelson: coordinates and colorability have different trust boundaries

A finite unit-distance obstruction needs exact coordinates (or exact distance certificates) and a separate non-colorability certificate. Numerical drawings and a solver's `unsat` log can each fail independently.

**Harness rule learned.** Split object validity from obstruction validity and require two evidence channels.

## 5. Hadamard: structural monoculture can look like route diversity

Trying many prompt variants around the same construction grammar does not create independent mathematical mechanisms. Compute can explode while the effective mechanism count remains near one.

**Harness rule learned.** Cluster routes by object, invariant, operation, and missing obligation—not by worker name or prompt wording. Display route entropy and effective mechanisms.

## 6. No-three-in-line: the strongest successful pattern

A finite witness can be separated from its search process and checked by a small exact verifier. Local-repair theory can then be developed as a distinct contribution with its own claims and certificates. Independent reconstruction of the witness prevents the discovery program from being part of the final trust base.

**Harness rule learned.** Prefer proof-carrying outputs whose acceptance checker is much smaller and more stable than the search system.

## 7. Cross-run failure taxonomy

The dominant failures were not simply “the model was not creative enough.” They were scope overreach, hidden quantifier lifts, verifier mismatch, numerical-to-exact gaps, statement drift, route monoculture, missing independent replay, and progress percentages that measured activity rather than theorem closure. MathArc makes each one machine-visible.
