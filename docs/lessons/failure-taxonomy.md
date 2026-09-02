# Failure taxonomy and automatic response

| Failure class | Detection | Automatic response |
|---|---|---|
| `SCOPE_OVERREACH` | evidence scope below claim scope | block promotion; emit guard event |
| `MISSING_QUANTIFIER_LIFT` | finite/family result attached to global claim | create explicit lift obligation |
| `THEOREM_STRENGTH_RELOCATION` | new lemma implies or is equivalent to root bottleneck | mark route blocked; require mechanism delta |
| `FALSE_BRIDGE` | exact counterexample or failed identity | refute node; invalidate descendants |
| `VERIFIER_MISMATCH` | certificate checks a different statement/object | reject evidence; open correspondence audit |
| `NUMERICAL_EXACTNESS_GAP` | residual/float result used for exact claim | downgrade trust; request interval/exact proof |
| `HIDDEN_ASSUMPTION` | proof step needs undeclared regularity/genericity | amend contract or reject step |
| `CIRCULAR_DEPENDENCY` | cycle in claim DAG | reject graph mutation |
| `SOLVER_UNKNOWN_PROMOTION` | UNKNOWN/TIMEOUT treated as SAT/UNSAT | fail closed |
| `STATEMENT_DRIFT` | theorem hash or quantifiers change mid-run | fork contract; invalidate stale evidence |
| `ROUTE_MONOCULTURE` | low mechanism entropy despite many workers | reserve budget outside dominant basin |
| `REPLAY_FAILURE` | artifact hash/command/output mismatch | revoke evidence acceptance |
| `FORMALIZATION_MISMATCH` | Lean theorem differs from frozen statement | keep kernel result but block original claim |
| `PROVENANCE_STALE` | current status or attribution not audited | block novelty/public release |

A failure evolves through:

```text
failure event
  → minimal reproduction
  → root-cause class
  → DAG invalidation
  → dead-lemma / counterexample memory
  → regression fixture
  → harness rule or benchmark update
```
