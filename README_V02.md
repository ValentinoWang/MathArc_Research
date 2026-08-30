# MathArc Research v0.2

MathArc Research v0.2 is a verifier-gated theorem-research harness.  It turns a mathematical project into an auditable dependency graph rather than treating a fluent model response as a proof.

## What changed from v0.1

v0.1 established proof-carrying claims, exact tools, deterministic demos, a browser console, and proposal-only Codex workers.  v0.2 adds:

- a theorem contract with explicit scope and non-claims;
- a weighted claim DAG with automatic failure propagation;
- mechanism signatures and kill tests for every research route;
- reusable cross-run failure memory;
- a strict public-reasoning record instead of private token traces;
- complete tool-call provenance and cold-replay contracts;
- critical-claim independent-evidence gates;
- research-quality metrics whose percentages are not interpreted as theorem probabilities;
- a self-contained dashboard for claims, routes, tools, failures, and release boundaries;
- an equal-budget paired benchmark layer that refuses unsupported superiority claims.

## Run the v0.2 demo

```bash
cd Projects/MathArc_Research
python -m pip install -e ".[research]"
python -m matharc.v02 demo --out-dir artifacts/v02-demo
python -m matharc.v02 validate \
  --trace artifacts/v02-demo/research-trace.json
```

Open:

```text
artifacts/v02-demo/research-dashboard.html
```

The demo deliberately contains both:

1. an exact failed route: finite-prefix agreement is not a universal proof rule;
2. a successful route: base case, arbitrary induction step, two independent evidence groups, and target promotion.

The dashboard therefore demonstrates failure learning rather than hiding every unsuccessful attempt.

## Run all tests and acceptance gates

```bash
make ci
```

or separately:

```bash
python -m unittest discover -s tests -v
python scripts/v0_1_acceptance.py
python scripts/v0_2_acceptance.py
```

v0.2 acceptance contains fourteen semantic gates, including dependency guards, independent evidence, failure cascades, public-reasoning policy, proposal-only agents, benchmark qualification, dashboard generation, exact cold replay, serialization integrity, and route-distinctness checks.

## Public reasoning, not private chain-of-thought

The demonstrable record is:

```json
{
  "objective": "close the arbitrary-n induction step",
  "premises": ["the base is proved", "the next odd term is 2n+1"],
  "proposed_move": "reduce to a polynomial identity",
  "observation": "two independent normalizers return zero",
  "falsification_test": "any nonzero coefficient blocks induction",
  "decision": "submit the step to the promotion gate"
}
```

Fields such as `chain_of_thought`, `scratchpad`, and `private_reasoning` are rejected.  The public record is sufficient to reconstruct the research decision and connect it to evidence without exposing or depending on unstructured private token traces.

## Release states

| State | Meaning |
|---|---|
| `OPEN_RESEARCH` | target dependency graph remains open |
| `CANDIDATE_UNVERIFIED` | a proposed result lacks acceptance evidence |
| `BLOCKED_EXACT` | an explicit load-bearing obligation is open |
| `REFUTED_EXACT` | an exact counterexample refutes the contracted target |
| `PROVED_WITH_AUDIT_DEBT` | target is proved but replay/independence debt remains |
| `PROVED_AND_AUDITED` | target and all promotion gates close |

Only `PROVED_AND_AUDITED` permits a completion claim for the theorem contract.

## Benchmark policy

MathArc does not infer superiority from architecture diagrams or one curated demo.  A comparison is eligible only when:

- candidate and baseline solve the same pinned cases;
- seeds and budgets are paired;
- every artifact cold-replays;
- the candidate makes zero false claim promotions;
- at least 30 paired runs are present;
- every preregistered primary metric has a positive 95% paired-bootstrap lower bound.

The open-source adapter registry is in `benchmarks/agent_registry_v02.json`.  Entries are integration targets, not measured results.

## Main files

```text
matharc/v02/schema.py           strict records and enums
matharc/v02/trace.py            claim DAG, promotion and invalidation
matharc/v02/orchestrator.py     load-bearing round planning
matharc/v02/failure_memory.py   transparent cross-run failure retrieval
matharc/v02/metrics.py          proof-research observability metrics
matharc/v02/benchmark.py        qualification-gated comparisons
matharc/v02/visualization.py    self-contained dashboard
matharc/v02/demo.py             deterministic failure-to-proof demo
scripts/v0_2_acceptance.py      fourteen-gate release acceptance
```

## Claim boundary

The current branch implements and tests the research protocol.  It does not by itself establish that MathArc is universally stronger than every existing mathematics agent.  The benchmark layer is specifically designed to make that statement impossible until measured, paired evidence exists.
