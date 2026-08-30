# MathArc v0.3 工程开发路径 — v4 SSOT

Updated: 2026-08-28 (Asia/Taipei)

> **This file is the current single entrypoint for engineering decisions.**
> The full v2/v3 milestone tables are preserved verbatim in
> `DEV_PATH_V03_DETAIL_V3.md`. Those detailed R/F/V/N/S/G descriptions remain
> applicable only where they do not conflict with the v4 decisions below.
> `DEV_PATH_V03_AMENDMENT_2026-08-28.md` is retained as change provenance; this
> file is the authoritative consolidated decision surface.

## 1. Non-negotiable invariants

1. Worker/model output is proposal-only. Claim promotion authority remains `ResearchTrace.promote_claim()`.
2. Every new acceptance/promotion gate needs a negative-path regression.
3. `COUNTEREXAMPLE` is negative evidence and never counts as positive proof-capable evidence.
4. Route failure is not claim refutation. ReviewGap / RouteFailure / ClaimCounterexample remain separate channels.
5. Planning prose does not hand-maintain current test counts, skip counts, or mypy file counts; G0-c baselines do.

## 2. Gate 0 — current authority contract

The old wording “local `make ci` is the unique authoritative gate” is superseded.

```text
make bootstrap-full
        ↓
make ci-full
        ↓
make clean-ci
        ↓
make baseline
```

### G0-b — authoritative local gate

- `make ci` is a developer loop. Without z3 it may return zero only with an explicit `DEGRADED` message and MUST NOT be cited as authoritative green.
- `make ci-full` is authoritative. It requires `.[research,dev,formal]`, including `sympy` and `z3-solver`.
- Unit-test output and `artifacts/ci/unittest-summary.json` must record total tests, all skips, and SMT discovered/executed/skipped counts.
- Authoritative mode fails if z3 is unavailable, if no SMT tests are discovered, if no SMT test executes, **or if any SMT test is skipped**.

### G0-c — clean-check and versioned baseline

- `make clean-ci` refuses dirty Gate 0 inputs, expands the committed `HEAD:.` tree plus the `HEAD:registry.yaml` authority into a temporary repository layout, creates a fresh venv, installs `.[research,dev,formal]`, then reruns `make ci-full`.
- `make baseline` writes a dated baseline only after current-checkout `ci-full` and clean-checkout `clean-ci` both return zero.
- Baseline content includes Python/z3/sympy versions, dynamic `matharc/v02/**/*.py` count, unit/skip/SMT counts, and SHA-256 digests for acceptance/certificate artifacts.
- A large milestone is not “reproducibly green” without that committed baseline.

### G0-d — remote CI

When GitHub runners can actually execute steps, remote CI installs the same formal extras and calls the same `make ci-full`; it is not a second, looser gate. A workflow that terminates with no executed steps is neither green evidence nor a code-test failure.

### G0-f — real Claude smoke

`make smoke-claude` is optional and paid. It runs one synthetic-math, proposal-only real Claude Code turn and emits sanitized structured proposal/public trace/ToolCallRecord/ModelUsage evidence. Historical prose without a versioned artifact is not current authoritative smoke evidence.

## 3. Current vertical sequence

```text
Gate 0
  → v0.3-core
       F0 KillTestSpec
       → F0.5 RouteEvaluationRecord
       → F1 compile/execute
       → F2 promotion hard blocker
       → F3 counterexample cascade
       + R5 three-channel semantics
       + V3 SAT + DRAT/LRAT
       + N0.5 semantic evidence-gain
       + N2.5 paired-regression wiring
  → v0.3-review
       R0 → R1 → R2 → R3 → R4 → R5 CLI chain
  → v0.3-learning
       N0 → N1 → N2 + Assurance Vector
  → v0.4
       R6/R7, S/G, V1→V2, V4, N3
       + V0 only after second instance
       + W3-0 only after second real consumer
```

The unchanged detailed milestone definitions, estimates, and acceptance criteria are in `DEV_PATH_V03_DETAIL_V3.md`.

## 4. W3-0 explicit decision — SSOT

**W3-0 MathArc Engine extraction is deferred from v0.3-core to the v0.4 entry point, and it MUST NOT start until a second real consumer exists.**

Rationale: F0.5, F2, R5, evidence semantics, and assurance boundaries are still being stabilized. Extracting the package now would turn implementation accidents into reusable APIs.

A second consumer must be concrete: a real non-Research caller such as Resolve/EDA, or another actual project. A slide, planned reuse, or hypothetical future integration does not count.

Module-count growth does raise later move cost. The **Harness_Engineering repository owner** owns that migration-cost risk and re-reviews it at every v0.3 milestone close. Each milestone PR/G0-c record must state either:

- `DEFER_W3_0` + current reason; or
- `START_W3_0` + named second consumer.

Rising migration cost is not by itself permission to prematurely generalize an unstable interface.

## 5. Prototype freeze

`docs/prototypes/review-console.html` is the current **v3 recruiting/demo prototype** and is frozen as `FROZEN_RECRUITING_DEMO`.

No further visual/product iteration is funded until all four conditions hold:

1. F0.5 negative semantics: `property_random` no-counterexample ⇒ `INCONCLUSIVE`, never `PASS_BOUNDED`.
2. F2 negative gate: a structured active route without a current qualifying evaluation cannot promote a claim.
3. R5 negative semantics: ReviewGap changes no theorem status; RouteFailure changes only the route; only an independently verified ClaimCounterexample may refute/cascade.
4. Those tests pass the current authoritative `make ci-full` gate.

Exceptions are only security, privacy/data-leak, or accessibility blockers. Recruiting may use the frozen prototype, but prototype behavior is not evidence that the backend contract exists.

## 6. Stage exit rules

Every stage exits only when:

- `make ci-full` passes on the committed tree;
- every new gate in the stage has a negative regression;
- large milestones also pass `make clean-ci` and commit the `make baseline` G0-c artifact;
- the implementation-status document lists partial/not-started items without promotion by prose.

The v0.3-core functional exit remains two real cases:

1. a false proposition is automatically and exactly falsified at the correct layer (route failure does not refute the claim; claim counterexample does); and
2. a true subclaim obtains cold-replayable evidence and either passes promotion or receives an exact, named blocker.

## 7. Count drift policy

Do not copy forward fixed numbers such as “39 mypy files”, “40 files”, “135 tests”, “155 tests”, or later snapshots as current truth. They are historical measurements. The current committed baseline dynamically records source-file count and test/skip counts for its own SHA.

## 8. Branch hygiene

Repository-wide governance changes (`HARNESS-LAYERING.md`, global `registry.yaml` policy, `AGENTS.md` placement rules) use dedicated `governance/*` or narrowly scoped governance-fix branches. MathArc research feature branches do not carry unrelated governance changes unless the dependency is unavoidable and explicitly documented in the PR.

This Gate 0 repair is intentionally isolated on `fix/matharc-gate0-ci-evidence`, after the v0.3 feature PR was merged.

## 9. Historical detailed plan

For the full v2/v3 tables covering:

- R0–R7 expert review,
- F0–F4 falsification,
- V0–V4 verifier factory,
- N0–N3 learning/data,
- S/G assurance and business layers,
- reviewer-facing copy rules and external-review adoption notes,

see `DEV_PATH_V03_DETAIL_V3.md`.

If a historical detail conflicts with Sections 1–8 here, this v4 master wins.
