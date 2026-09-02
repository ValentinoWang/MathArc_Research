# MathArc Research

> A proof-carrying mathematical research runtime with verifier-controlled claims, real Codex workers, public research traces, and replayable evidence.

This is the v0.1-era baseline product doc. For the v0.2 delta — release states, benchmark policy, main files — see [README_V02.md](README_V02.md).

MathArc Research does not repeatedly ask a model to “try harder.” It turns a theorem or conjecture into an auditable state machine:

```text
freeze statement, quantifiers and scope
  -> create mechanism-diverse routes
  -> produce atomic claims and proof obligations
  -> call exact / formal / computational tools
  -> falsify every load-bearing step
  -> propagate failures through the claim DAG
  -> require independent reconstruction
  -> release only the claim language permitted by the evidence
```

## MathArc Research v0.1

The frozen v0.1 engineering contract is **100% complete**. This percentage measures implementation of the frozen product and research-reliability deliverables; it is not a theorem probability and does not imply that every open conjecture is solved.

Implemented surfaces include:

- theorem scope and evidence-trust lattices;
- claim / proof-obligation DAG with cycle checks;
- fail-closed promotion and downstream invalidation;
- content-addressed evidence, replay commands and certificate-debt accounting;
- independent reconstruction gate;
- exact polynomial and induction tools plus optional Lean integration;
- persistent failure memory and regression fixtures;
- multidimensional research metrics and binary theorem closure;
- official Codex CLI workers for interactive Agent answers and tool calls;
- JSONL event normalization, thread resume and append-only Agent session ledger;
- live Web research console with Server-Sent Events;
- Docker, CI, deterministic demo and executable v0.1 acceptance gate.

Read the frozen contract and acceptance report:

- `docs/reports/v0.1-engineering-contract-acceptance.md`
- `benchmarks/v0.1-acceptance-contract.json`

## Interactive Codex research console

The Web console delegates research turns to the official `openai/codex` CLI. It streams:

- public reasoning summaries;
- command executions and exit codes;
- file changes;
- MCP tool calls;
- research plans;
- token usage;
- a strict structured final proposal.

Five worker roles are built in:

```text
strategist
prover
falsifier
verifier
synthesizer
```

Codex is a worker, not an acceptance authority. Its allowed final states are:

```text
progress
blocked
falsified
candidate
error
```

It cannot self-assign `VERIFIED` or `ACCEPTED`. Mathematical promotion remains controlled by the claim DAG, scope/trust checks, replayable evidence and independent reconstruction.

The browser defaults to `read-only`; `workspace-write` requires an explicit user selection. Dangerous sandbox bypass is never exposed through the API.

See `docs/reports/codex-agent-runtime.md` for the full execution and security contract.

## Product views

The optimized Web UI provides:

1. release state, binary theorem closure and certificate debt;
2. multidimensional contract-health metrics;
3. route portfolio grouped by mathematical mechanism and basin;
4. interactive SVG claim / obligation DAG;
5. public structured reasoning trace;
6. evidence ledger with scope, trust, producer, SHA-256 and replay command;
7. typed tool-call ledger;
8. failure evolution and regression memory;
9. right-side Codex Agent workspace with quick prompts, role selection and live events;
10. public-trace export for review and demos.

The UI shows structured public rationale—objective, premise, move, observation, falsification and decision. It does not expose or treat hidden private token-level chain-of-thought as proof.

## Real research result: Frankl q=6 special-case bridge

The repository preserves a historical machine-checked candidate record for the frozen special-case contract:

> If a finite union-closed family has a minimum nonempty member of size three and exactly six outside elements, then the family satisfies Frankl's conclusion.

The 2026-08-23 audit records:

- all `90` union-closed trace families on the three-point minimum set;
- `111,820` admissible positive-core high-layer geometries;
- `296,010` restricted six-core `L_7` collections;
- `15,120` dangerous three-small-part geometries;
- `11,625` low-cost positive-core geometries;
- all `244,068` trace-type multisets in the residual `k=4,5,6,7` layers;
- two historically reported byte-identical cold replays with accepted-output SHA-256
  `f98e52d7ce76c131ae5b7db55114d25616b555887eae059591b67ae6ab5f2719`.

Strict status boundary:

```text
historical q=6 record: MACHINE_CHECKED_CANDIDATE_THEOREM
current checkout: ARCHIVE_INTEGRITY_PASS / FULL_COLD_REPLAY_UNAVAILABLE
full Frankl conjecture: INCONCLUSIVE
external expert review: not yet completed
novelty/theorem-priority claim: not made
```

Three declared verifier sources and all eight component-result JSON files are absent from the current tree, so the historical candidate cannot currently be cold-replayed. `experiments/frankl_q6_round4/archive_manifest.json` and its auditor freeze the surviving aggregate without promoting it to current proof evidence.

Because this scoped case has a nine-element universe and was already covered by earlier small-universe computational verification, any paper must be framed around the trace-fiber/charge architecture, residual-case decomposition, evidence pipeline and Agent methodology, not theorem priority for the nine-element case.

The proof process contributed several engineering rules now enforced by MathArc:

- compressed state-space closure requires an uncompressed audit or a proved compression map;
- cold replay identity is a release artifact;
- special-case and global theorem states stay separate;
- exceptional types remain regression objects;
- generator and checker independence is visible;
- model output stays a proposal until verifiers accept it.

See `experiments/frankl_q6_round4/LATEST_Q6_AUDIT.md`.

## Install and run

### Local Python runtime

```bash
cd .
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,api,research]"

python -m unittest discover -s tests -v
python -m matharc demo --out-dir artifacts/demo
python -m matharc validate --run artifacts/demo/run.json
python scripts/v0_1_acceptance.py
python -m matharc serve \
  --run artifacts/demo/run.json \
  --workspace . \
  --port 8000
```

Open `http://127.0.0.1:8000`.

### Configure Codex

Install the official CLI and configure authentication:

```bash
npm install -g @openai/codex
export CODEX_API_KEY=...
export MATHARC_CODEX_MODEL=...
export MATHARC_CODEX_WORKSPACE="$(pwd)"
```

Check the integration:

```bash
python -m matharc codex status --workspace .

python -m matharc codex turn \
  --run artifacts/demo/run.json \
  --role falsifier \
  --message 'Audit the current global bridge and state the cheapest kill test.' \
  --sandbox read-only \
  --workspace .
```

### Autonomous v0.2 research campaign (Claude Code worker)

`matharc.v02` closes the discovery loop: a `ResearchCampaign` runs repeated
plan → worker → dispatch rounds over an existing trace, letting a worker
extend the claim DAG (`new_claims`/`new_routes`) and execute allowlisted
exact tools (`polynomial_identity`, `induction_certificate`) that attach
real, replayable evidence and attempt promotion — never self-promoting.
The default worker bridge shells out to the `claude` CLI (Claude Code)
exactly the way `matharc/codex_runtime.py` shells out to `codex`: no
mutating or networked tool is available to the worker turn
(`--disallowedTools`, `--strict-mcp-config`, `--setting-sources ""`), and
its output is schema-forced (`--json-schema`) into the same proposal
contract every other worker speaks.

```bash
python -m matharc.v02 claude-status

python -m matharc.v02 run \
  --trace artifacts/v02-demo/research-trace.json \
  --role falsifier --role prover \
  --rounds 5 --max-rounds-without-gain 2 \
  --output artifacts/campaign-report.json
```

See `matharc/v02/campaign.py`, `matharc/v02/model_workers.py`, and
`matharc/v02/claude_code_runtime.py`; the report's `stop_reason` and every
round's `metrics_after`/`executed_tools` are the honest record of what
actually happened — a worker's proposal is never treated as proof, and a
failed promotion attempt is the gate correctly saying no, not an error.

With the optional `formal` extra (`pip install -e ".[formal]"`), the tool
allowlist also includes two SMT templates over z3
(`matharc/v02/smt_tools.py`): `smt_universal_no_counterexample` for bounded
universal claims and `smt_existential_witness` for witnessed existentials.
Their trust semantics are asymmetric on purpose: `unknown` (including
timeout) is a hard block that never yields evidence; a `sat` model must
survive an independent pure-Python evaluator before it counts (checker
disagreement is an ERROR, not a result); an `unsat` verdict is recorded as
solver-trusted `EXACT_COMPUTATION` with its limitation stated, so a critical
claim still cannot close on z3's word alone; and a verified counterexample
is reported through the tool call, never as claim-supporting evidence.

### Docker

```bash
export CODEX_API_KEY=...
docker compose up --build
```

The image installs Python, MathArc Research and the official Codex CLI. Credentials are injected only at runtime.

## Core guarantees

1. **Fail-closed scope semantics.** Instance, finite-range, parametric-family and global claims remain distinct. A quantifier lift needs its own evidence.
2. **Generation is not acceptance.** Codex and every other worker can propose but cannot self-promote a claim.
3. **Evidence is content-addressed.** Artifacts and tool results carry SHA-256 identities and replay metadata.
4. **Failure is first-class.** Refuting an upstream claim invalidates dependents and creates a regression object.
5. **Independent reconstruction is explicit.** Root release can require a different mechanism or implementation family.
6. **Progress is multidimensional.** Execution, obligation closure, evidence maturity, route diversity, replayability, scope safety, certificate debt and theorem closure are separate.
7. **Theorem closure is binary.** A polished narrative or high engineering percentage cannot replace `0/1` proof closure.
8. **Comparative claims are benchmark-gated.** MathArc does not claim higher pass@k than every prover before a matched-budget replay.

## Repository map

```text
matharc/                    runtime, Codex adapter, API, tools, metrics and exact research modules
examples/                   deterministic demos and research-run entry points
verifiers/                  independent Python/NumPy and C++ verifiers
experiments/                Frankl q=6 and ES(7) research programs
benchmarks/certificates/    checked outputs and manifests
benchmarks/                 acceptance, comparison and capability contracts
docs/                       see docs/README.md for the full index (architecture, lessons,
                             Frankl proof-trace docs, release/acceptance reports, baselines)
tests/                      fail-closed, mathematical and Codex regression tests
scripts/                    Gate 0 CI: preflight, unittest runner, workflow-policy checker,
                             clean-checkout proof, v0.1/v0.2 acceptance, baseline writer, smoke test
```

## What “stronger” means

MathArc's demonstrated differentiator is a wider **research reliability surface**: mixed informal/formal/computational routes, scope-safe promotion, adversarial falsification, persistent failure memory, independent reconstruction, tool transparency and proof-carrying release gates.

A claim of model-level superiority remains blocked until all systems use the same theorem split, model, budget, tool access, verifier and seeds. The benchmark infrastructure is complete in v0.1; matched empirical leaderboard runs are a v0.2 campaign.

## License

Apache-2.0.
