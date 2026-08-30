# MathArc Research v0.3 — implementation status

Updated: 2026-08-28 (Asia/Taipei)

This file is the evidence-oriented implementation delta for `DEV_PATH_V03.md` at the repository-level `v0.3` boundary. It does **not** redefine the plan or promote partial milestones beyond their recorded scope.

## Gate 0 authority change — 2026-08-28

The previous local replay (`make ci`, 175 tests, 10 skips) remains useful historical engineering evidence, but it is **no longer sufficient to call the current tree authoritative-green**. The reason is structural: an environment without `z3-solver` can skip the SMT test family and still return zero.

The current authority contract is now:

```text
make bootstrap-full
        ↓
make ci-full
  - formal preflight requires sympy + z3
  - all unittest skip counts are printed and serialized
  - SMT discovered / executed / skipped are explicit
  - all-SMT-skipped is a hard failure
        ↓
make clean-ci
  - git archive of committed Projects/MathArc_Research
  - fresh temporary venv
  - install .[research,dev,formal]
  - rerun make ci-full
        ↓
make baseline
  - only after both gates pass
  - writes dated G0-c Markdown with counts, versions and SHA-256 digests
```

`make ci` remains a developer loop. If z3 is unavailable it prints `DEGRADED` and must not be cited as authoritative Gate 0 green evidence.

## Audit cleanup

| Item | Status | Evidence boundary |
|---|---|---|
| Local CI self-containment | IMPLEMENTED | Makefile exports project `PYTHONPATH`; `make bootstrap` / `make bootstrap-full` install editable dependencies. `make clean-ci` proves the committed project plus root registry and workflow authorities from a minimal `git archive` in a fresh repository layout and venv. |
| z3 and skip fail-closed gate | IMPLEMENTED | `scripts/run_unittest_suite.py` writes total/skipped and SMT discovered/executed/skipped counts. `make ci-full` requires z3, rejects skipped SMT coverage, and requires the actual non-SMT skip-ID set to equal the explicit whitelist. |
| G0-c baseline | IMPLEMENTED AS EXECUTABLE CONTRACT | `make baseline` runs current checkout `ci-full` plus clean archive `clean-ci` and writes a dated baseline only if both return zero. Historical baseline files remain historical rather than being relabeled. |
| Registry §4 compliance | IMPLEMENTED | `project-matharc-research` is registered and `PROJECT.md` declares it active. `project_namespace` is still governance provenance; whole-project materialization remains a separate target-contract decision. |
| Default campaign budget | IMPLEMENTED | Default wall budget = 1800s; unbounded operation requires explicit `--no-budget`; numeric budget flags conflict with `--no-budget`. |
| Usage self-report reconciliation | IMPLEMENTED, TRACE-LEVEL | Campaign compares optional worker `usage_report` against provider-metered usage and records divergence in `BudgetLedger` plus trace metadata. It is not yet a Workspace EventLedger transition. |
| Source-checkout server script | IMPLEMENTED | `serve_workspace_v02.py` falls back to the project root only when the missing module is the top-level `matharc` package. |
| Remote CI alignment | IMPLEMENTED CONFIGURATION, RUNNER EVIDENCE PENDING | `matharc-research-ci.yml` is the only automatic MathArc workflow, pushes trigger only on `main`, and it installs `.[research,dev,formal]` before calling `make ci-full`. Historical content workflows are manual-only. Remote runner availability is external infrastructure; a run that dies before steps is neither green evidence nor a code-test failure. |
| Round-4 archive boundary | IMPLEMENTED | The surviving aggregate is SHA-256 bound as a historical record. Missing verifier sources/component results force `FULL_COLD_REPLAY_UNAVAILABLE`; `rebuild_all.sh` fails before side effects and ordinary archive acceptance never reports current theorem acceptance. |
| Claude Code smoke evidence | IMPLEMENTED ENTRYPOINT, NOT YET EXECUTED | `make smoke-claude` performs one real proposal-only turn on synthetic math input and writes sanitized structured proposal/public trace/ModelUsage evidence. Until such an artifact is actually generated and versioned for a milestone, historical prose about a real Claude CLI smoke is non-authoritative observation only. |
| Prototype iteration | FROZEN | `docs/prototypes/review-console.html` is the current v3 recruiting/demo design and is frozen. No further visual iteration except security/accessibility blockers until F0.5/F2/R5 negative gates are present and pass `ci-full`. |

## v0.3-core

| Milestone | Status | Current boundary |
|---|---|---|
| F0 KillTestSpec | IMPLEMENTED-FIRST-SLICE | Typed/versioned contract with semantic SHA-256, explicit tested scope, random-vs-deterministic kinds. Stored compatibly in trace metadata rather than migrated into the v0.2 dataclass schema. `created_at` is provenance and is deliberately excluded from the semantic spec hash. |
| F0.5 RouteEvaluationRecord | IMPLEMENTED-FIRST-SLICE | Records route/claim revisions, spec digest, tool call, outcome, scope, verifier group and optional verified witness. Campaign, audit and promotion consume the shared record; public reasoning is not accepted as execution proof for structured routes. |
| F1 compile/execute | PARTIAL | Existing allowlisted exact tools can be attributed to a structured route and generate RouteEvaluationRecord. General KillTestSpec compiler for SMT/enumeration/property generators remains open. |
| F2 hard promotion blocker | IMPLEMENTED-FOR-STRUCTURED-ROUTES | The unique authority `ResearchTrace.promote_claim()` fails closed when an active structured route lacks a current `PASS_BOUNDED` record. Legacy v0.2 prose-only routes remain compatibility-warning mode until migrated. |
| F3 counterexample cascade | PARTIAL-SEMANTICS | Generic tool FAIL is never a claim counterexample. Claim refutation requires independently checked `COUNTEREXAMPLE` evidence; the Workspace path additionally requires a content-addressed artifact whose SHA-256 matches the evidence. Automatic SMT/tool-result → counterexample-artifact wiring remains open. |
| R5 three-channel failure semantics | IMPLEMENTED-FIRST-SLICE | `REVIEW_GAP` changes no mathematical status and feeds the director; `ROUTE_FAILURE` changes only the route; `CLAIM_COUNTEREXAMPLE` alone may refute a claim. Full expert-review R0–R5 CLI workflow remains future work. |
| Negative-evidence promotion safety | IMPLEMENTED | `EvidenceKind.COUNTEREXAMPLE` is excluded from positive proof-capable evidence in promotion and research metrics. |
| V3 SAT + DRAT/LRAT | IMPLEMENTED-CNF-FIRST-SLICE | `cnf_lrat_unsat` canonicalizes bounded propositional CNF, produces an addition-only LRAT/RUP refutation by deterministic resolution closure, and accepts evidence only after the separate checker derives the empty clause. SAT/saturation, resource limits, malformed CNF, proof tampering, and checker disagreement produce no UNSAT evidence. Existing Z3 integer-arithmetic UNSAT remains `z3-solver-replay-v1` / solver-replay-only. External Kissat/CaDiCaL ingestion, general LRAT, Z3-to-CNF translation, and ES7 certificate ingestion remain open. |
| N0.5 evidence-gain signal | IMPLEMENTED-FIRST-SLICE | Campaign logs semantic evidence gain plus per-round metered cost; replaying the same checker output under a fresh ID is zero gain. |
| N2.5 paired regression wiring | NOT STARTED | Existing benchmark infrastructure remains unchanged. |
| W3-0 MathArc Engine extraction | EXPLICITLY DEFERRED | Deferred to v0.4 entry **and** until a second real consumer appears. Harness_Engineering owner re-reviews migration-cost risk at each v0.3 milestone close; growing module count is recorded but is not grounds to prematurely generalize an unstable interface. |

## v0.3-review (started 2026-08-28)

Full clause-to-evidence matrix: `docs/V03_REVIEW_TRACEABILITY.md`.

| Milestone | Status | Current boundary |
|---|---|---|
| R0 review schema, provenance, object-level authorization | IMPLEMENTED-FIRST-SLICE | New `matharc/v02/review.py`: `ReviewerProfile`/`ReviewerRoster` (version-pinned — redefining an existing `roster_version` with different content is rejected), `ObligationVerdict`, `ReviewRecord` with all 8 required version-binding fields, strict/CoT-safe round-trip, ACTIVE/REVOKED lifecycle (SUPERSEDED is defined but nothing sets it yet), object-level `can_review` (separate from and in addition to role-level `RolePolicy`), APPROVE→HUMAN_AUDIT via `review_to_evidence`. `ResearchRoute` gained `created_by` for provenance parity with `ClaimRecord.owner`/`EvidenceRecord.producer`. `trace.py::_promotion_issues` gained a lazy, opt-in hook (`stale_review_evidence_ids`) so a revoked review or a claim-revision bump immediately stops that review's HUMAN_AUDIT evidence from satisfying promotion — verified through the real `ResearchTrace.promote_claim`, not an isolated helper. |
| R1 nomination pre-screen | IMPLEMENTED-FIRST-SLICE | `review.py::nominate_for_review`/`nomination_blockers`: CANDIDATE-only, every ACTIVE route needs an F0.5 `RouteEvaluationRecord` with outcome ∈ {PASS_BOUNDED, COUNTEREXAMPLE} at the current revision (INCONCLUSIVE/ERROR never count), open ReviewGaps block re-nomination. `NominationRecord` is sealed into `trace.metadata` (same pattern as F0.5), not the workspace `EventLedger` — that only exists once `SecuredResearchWorkspace` wraps this in R3. The spec's literal "无未决 RouteFailure/ClaimCounterexample" clause is deliberately not implemented as a separate always-blocking check; see the traceability doc for why a literal reading would break R5's own "other routes may carry the claim forward" design. |
| R2 ReviewBundle | IMPLEMENTED-FIRST-SLICE | New `matharc/v02/review_bundle.py`: frozen statement + pinned contract-level definitions + dependency path + full evidence snapshots + numbered `Obligation` objects (`{title, ask, points, ref, required_assurance}`) + structured `AttackHistoryItem`s, all deterministic and digest-sealed with per-file SHA-256 (`write_review_bundle`/`verify_review_bundle_files`, real file-tamper detection). Automated appendix-A copy checker (`check_bundle_copy`) with the spec's own before/after example as a literal regression fixture; caught and fixed two real bugs during construction — raw enum values leaking into obligation text, and a whitespace-tokenization gap that let CJK-adjacent English enum tokens through the checker itself. Minimal self-contained HTML view reusing the frozen prototype's tokens without redesigning it. |
| R3 CLI submission path | IMPLEMENTED-FIRST-SLICE | `matharc.v02 review nominate/bundle/submit/revoke/status`, wired through the same bare `load_trace`/`save_trace` round trip every other v0.2 CLI command already uses. Verified genuinely cold: each of the four steps is a separate `main()` process invocation reloading state from disk, not four calls sharing memory. Object-level `can_review` is fully enforced at submission (roster-outside and conflicted reviewers both rejected with non-zero exit); `RolePolicy`/`EventLedger` sealing is explicitly deferred to R6, matching every other current v0.2 CLI command's own scope rather than retrofitting a heavier layer onto only the review subcommands. |
| R4 promotion policy | IMPLEMENTED-FIRST-SLICE, POLICY PARAMETERS PENDING SIGN-OFF | New `matharc/v02/review_policy.py`: every obligation in a claim's freshly-rebuilt `ReviewBundle` must have its `required_assurance` met by ACTIVE, current-revision `ReviewRecord` verdicts before promotion; wired into `trace.py::_promotion_issues` as another lazy, opt-in hook. Gate only activates when the claim's proof-capable evidence includes `HUMAN_AUDIT` (`review_gate_applies`) — a pure-machine critical claim (2 independent EXACT groups) promotes exactly as before R4 existed. `metrics.py` now emits `review_assurance` (`closure_trust_class`: machine/human/mixed, per-obligation snapshot) per claim. Coded default policy value is explicitly marked `CODED_DEFAULT_PENDING_CHIEF_SCIENTIST_SIGN_OFF`, not an approved parameter. Caught and fixed one real bug during construction: the obligation generator was creating a circular "review the review's own evidence" obligation nothing could ever satisfy — found by running the new gate against the pre-existing R0 test suite, not by inspection. |
| R5 REVIEW_GAP → planner wiring | ALREADY IMPLEMENTED (predates this slice) | Verified, not re-verified-away: `_research_director_impl.py::AdaptiveResearchDirector.plan_round` already calls `failure_channels.open_review_gaps` and folds each into `mandatory_attack_tests`/`route_constraints`. |
| R6 HTTP write path | IMPLEMENTED-FIRST-SLICE, API ONLY | New `matharc/v02/review_server.py`: `POST /api/review` (bearer roster token, `hmac.compare_digest`, 64KB cap, all other methods 405), `GET /api/review-queue`, `GET /api/review-bundle/{claim_id}` (server-side view model — every backend enum mapped to a Chinese label, verified absent from the raw response text). Stays at the bare-`ResearchTrace` layer R3's CLI already uses rather than integrating with `ResearchWorkspace`/`EventLedger`, which the spec itself lines up with the not-yet-built W4-3 multi-run server. The live reviewer-facing panel (wiring these endpoints into an interactive UI, as opposed to R2's static HTML export) is not built. |
| R7 import mapping layer | IMPLEMENTED-FIRST-SLICE | New `legacy_harness.py::build_importable_trace` maps a conservative `import_legacy_harness` report (plus the original acceptance manifest, which the report never echoes back in full) into a real `ResearchTrace`: `TheoremContract` + topologically-ordered `ClaimRecord`s + real `EvidenceRecord`s for VERIFIED nodes. `import_legacy_harness` extended additively to preserve `dependencies` per node (previously discarded entirely — the exact gap the spec calls out). "SUPPORTED never launders to PROVED" holds: mapped claims land at CANDIDATE, never stronger, and the function never calls `promote_claim`. Verified to actually interoperate with R0-R6 (a mapped claim feeds directly into R1 nomination). |
| R7 dogfood run | NOT STARTED, CANNOT BE COMPLETED BY THIS SESSION | Backfilling arXiv:2607.28557 and having two real reviewers from different institutions walk 1-2 key lemmas through the full seven-step process requires actually recruited human reviewers. The system this would exercise (R0-R6 plus the mapping layer above) is real and ready for it. |

Verification for this slice: `make ci-full` real exit code 0, confirmed by
reading the command's own exit status directly in the foreground — not by
trusting an intermediate background-task summary, after that summary was
caught misreporting a wrapper shell's exit code as the gate's own result on
three earlier runs that had actually failed (missing `sympy`). See the
traceability doc §4 for the full account.

## Regression files already present

The v0.3 code contains targeted negative-path tests including:

- `tests/test_v03_audit_fixes.py`
- `tests/test_v03_falsification.py`
- `tests/test_v03_failure_channels.py`
- `tests/test_v03_failure_workspace.py`
- `tests/test_v03_review.py` (R0/R1, 28 tests)
- `tests/test_v03_evidence_gain.py`

Gate 0 itself now additionally has executable capability/summary/clean-check scripts under `scripts/`.

## Historical replay vs current validation state

Historical record from 2026-08-28:

```bash
PATH="$PWD/.venv/bin:$PATH" make ci
```

reported 175 unit/regression passes and 10 skips, plus strict typing and the existing v0.1/v0.2 acceptance/cold-replay gates. That result is retained as historical evidence for the earlier tree. Under the new authority contract, **a replay with 10 silent formal/SMT skips cannot by itself establish authoritative green**.

Current implementation status is recorded above. Validation authority belongs to a committed G0-c file under `docs/baselines/`, generated for the exact implementation commit by `make baseline`; this status page is not a substitute for that evidence. The paid Claude smoke remains optional and requires its own sanitized artifact.

The baseline generator computes the current `matharc/v02/**/*.py` count dynamically. Historical prose counts such as 39 or the later audit-time 40 are not copied forward as current truth; the count can change whenever v0.3 adds modules, so the versioned baseline is the SSOT.

## Branch hygiene

Repository-wide governance changes (`HARNESS-LAYERING.md`, global registry policy, `AGENTS.md` placement rules) should use dedicated `governance/*` or narrowly scoped governance-fix branches. MathArc research feature branches should not carry unrelated governance commits. This Gate 0 branch is intentionally separated from the already-merged v0.3 feature PR.
