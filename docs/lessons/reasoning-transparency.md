# Reasoning transparency contract

## Publicly shown

Each research step publishes:

- objective and exact claim IDs;
- explicit hypothesis;
- action or tool call;
- observation;
- falsification attempt;
- decision and scope impact;
- evidence hashes and replay commands;
- dependencies and invalidations.

## Not claimed

MathArc does not claim that a model's hidden private chain-of-thought is available, complete, faithful, or itself evidential. Provider-internal tokens are not a proof object.

## Why this is stronger for a research demo

A structured trace can be filtered, compared, replayed, audited, and linked to concrete artifacts. It also remains meaningful when the worker is a theorem prover, SAT solver, human mathematician, or an LLM that exposes no private reasoning.

## UI modes

- **Investor mode:** closure, reliability, route diversity, tool activity, and key discoveries.
- **Researcher mode:** claim DAG, proof obligations, counterexamples, assumptions, and evidence hashes.
- **Auditor mode:** exact commands, environment identities, statement correspondence, and independent reconstruction.
