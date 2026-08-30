# v0.3-review — clause-to-evidence traceability matrix

Updated: 2026-08-29

This is the requested "spec clause → implementation location → test/evidence →
status" tracking matrix for `DEV_PATH_V03_DETAIL_V3.md` §1 (R track),
covering every milestone as it lands. It follows `V03_IMPLEMENTATION_STATUS.md`'s
own grading discipline: a row is IMPLEMENTED only when a negative-path test
backs it, not because the code exists.

Verified authoritative-green evidence for this slice: `make ci-full` real
exit code 0 (229 tests, 2 skipped, SMT suite actually executed — not
DEGRADED), confirmed by reading the command's own exit status directly
rather than trusting an intermediate summary. See §4 below for why that
distinction is called out explicitly.

## 1. R0 — review schema, provenance, object-level authorization

| Spec clause (`DEV_PATH_V03_DETAIL_V3.md` R0) | Implementation | Test | Status |
|---|---|---|---|
| `ReviewerProfile` (identity/affiliation/independence_group/conflict set) | `review.py::ReviewerProfile` | `test_round_trip` | IMPLEMENTED |
| `ReviewerRoster` (versioned JSON, `roster_version`) | `review.py::ReviewerRoster`, `set_reviewer_roster`/`get_reviewer_roster` | `test_reinstalling_identical_roster_content_is_a_noop` | IMPLEMENTED |
| Roster version pinning (not in the original spec text; added during self-review) | `set_reviewer_roster` rejects redefining an existing `roster_version` with different content | `test_redefining_roster_version_with_different_content_is_rejected` | IMPLEMENTED (hardening beyond spec) |
| `ObligationVerdict` (OK/gap/error/cannot_judge + note) | `review.py::ObligationVerdict`, `ObligationVerdictKind` | `test_approve_with_a_gap_verdict_is_rejected` | IMPLEMENTED |
| `ReviewRecord` version binding (claim_id + claim_revision + statement_digest + bundle_digest + reviewer_profile_digest + roster_version + review_policy_version + conflict_declaration + review_signature) | `review.py::ReviewRecord` (all 8 fields present and validated in `__post_init__`/`submit_review`) | `test_round_trip`, `test_stale_claim_revision_submission_is_rejected`, `test_tampered_signature_is_rejected` | IMPLEMENTED |
| Strict round-trip; unknown/CoT fields rejected | `review.py::_strict_keys` (reuses `schema._FORBIDDEN_REASONING_KEYS`) | `test_unknown_field_is_rejected`, `test_chain_of_thought_field_is_rejected` | IMPLEMENTED |
| Lifecycle ACTIVE / SUPERSEDED / REVOKED | `review.py::ReviewLifecycleStatus` | `test_revoked_review_record_lifecycle_status` | IMPLEMENTED **for REVOKED**; SUPERSEDED is a defined enum value with no caller that ever sets it yet (no "re-review supersedes an old one" flow exists — that is R3/R7 territory) — **NOT WIRED** |
| Revoked/conflicted/claim-revision-changed review's derived HUMAN_AUDIT evidence auto-invalidates (STALE) | `revoke_review` (eager, immediate) + `stale_review_evidence_ids` hooked into `trace.py::_promotion_issues` (lazy, at promotion time) — mirrors F2's `promotion_route_blockers` pattern exactly | `test_revoked_review_evidence_is_marked_stale_immediately`, `test_claim_revision_bump_makes_review_evidence_unable_to_promote` | IMPLEMENTED |
| `ResearchRoute` gains `created_by` (provenance parity with `ClaimRecord.owner`/`EvidenceRecord.producer`) | `schema.py::ResearchRoute.created_by` (backward-compatible optional field) | exercised by every `can_review` test | IMPLEMENTED |
| `can_review(actor, bundle)` object-level rule: actor ≠ route proposer, actor ≠ any evidence producer, reviewer conflict set ∩ bundle contributors = ∅ | `review.py::can_review`, `_bundle_contributor_ids` | `test_route_proposer_cannot_review_their_own_route`, `test_evidence_producer_cannot_review_the_same_claim`, `test_conflict_of_interest_overlap_is_rejected`, `test_unconflicted_reviewer_is_allowed` | IMPLEMENTED |
| APPROVE → `to_evidence()` → HUMAN_AUDIT evidence (group = reviewer group) | `review.py::review_to_evidence` | `test_full_happy_path_promotes_the_claim` (asserts the claim actually reaches PROVED through the real promotion gate, not a mock) | IMPLEMENTED |
| Non-APPROVE decisions never produce evidence | `review_to_evidence` raises if `overall_decision != APPROVE` | `test_non_approve_decision_cannot_become_evidence` | IMPLEMENTED |
| (Added invariant, not in spec text) APPROVE requires every obligation verdict to be OK | `ReviewRecord.__post_init__` | `test_approve_with_a_gap_verdict_is_rejected` | IMPLEMENTED (closes a laundering path the literal spec text didn't mention) |
| (Added invariant) `statement_correspondence` must be non-empty on every ReviewRecord | `ReviewRecord.__post_init__` | `test_empty_statement_correspondence_is_rejected` | IMPLEMENTED — `IMPROVEMENT_PLAN_V03.md` names this field the system's largest laundering channel; R0 does not repeat that gap |

**Acceptance criteria from the spec table, checked literally:**
- "ReviewRecord 严格 round-trip（未知/CoT 字段拒收）" → covered.
- "路线提出者对自己路线的评审被 `can_review` 拒绝（对象级，而非角色级）" → covered; note `RolePolicy` (role-level) is untouched and remains a separate layer, exactly as specified.
- "claim revision +1 后旧 ReviewRecord 派生的 HUMAN_AUDIT 证据不再满足晋升门" → covered end-to-end through the real `ResearchTrace.promote_claim`, not a unit check on an isolated helper.
- "REVOKED 评审的证据立即失效" → covered (eager `EvidenceStatus.STALE`, not just a lazy promotion-time check).

## 2. R1 — machine nomination pre-screen

| Spec clause | Implementation | Test | Status |
|---|---|---|---|
| `nominate_for_review(trace, claim_id)` gate: claim must be CANDIDATE | `review.py::nomination_blockers`, `nominate_for_review` | `test_non_candidate_claim_is_blocked` | IMPLEMENTED |
| Every ACTIVE route needs an F0.5 `RouteEvaluationRecord` with `outcome ∈ {PASS_BOUNDED, COUNTEREXAMPLE}` at the current claim revision / kill-test spec digest; INCONCLUSIVE/ERROR do not count as executed | `_route_is_executed` (reuses `falsification.get_kill_test_spec` + `iter_route_evaluations`) | `test_candidate_with_no_execution_record_is_blocked`, `test_candidate_with_only_inconclusive_record_is_blocked`, `test_candidate_with_pass_bounded_route_is_nominated`, `test_candidate_with_counterexample_outcome_route_is_nominated` | IMPLEMENTED |
| Seal a `REVIEW_NOMINATED` event | `review.py::NominationRecord` stored in `trace.metadata` + `nominations_for_claim` query helper | `test_candidate_with_pass_bounded_route_is_nominated` | IMPLEMENTED **as a metadata-store record**, matching the F0/F0.5/R0 precedent — **not** the workspace `EventLedger` hash chain, which only `ResearchWorkspace` owns and which bare-`ResearchTrace` functions (including every falsification.py/review.py function) never touch. Sealing into the actual hash-chained ledger is R3's job when this gets wrapped by `SecuredResearchWorkspace`. |
| Rejected nomination returns a machine-readable reason list | `NominationError.reasons: tuple[str, ...]` | all `NominationTests` cases assert on the reason text or `ctx.exception.reasons` | IMPLEMENTED |
| "无未决 RouteFailure/ClaimCounterexample" | **Deliberately not implemented as a separate check.** Both channels apply their effect immediately on recording (route → BLOCKED/FALSIFIED, claim → REFUTED/BLOCKED — see `failure_channels.py`), so they already surface through the CANDIDATE-status check and the active-route check above. A literal "any past ROUTE_FAILURE record ever blocks nomination" rule would break R5's own stated design (`ROUTE_FAILURE` must not touch claim status; other routes must be able to carry the claim forward) and is not exercised by the spec's own acceptance-criteria text, which only tests the OPEN/INCONCLUSIVE case. Reasoning is documented in `nominate_for_review`'s docstring. | — | DESIGN DEVIATION, DOCUMENTED (not silently dropped) |
| (Added, beyond the literal R1 text) an OPEN `ReviewGap` from a prior review round blocks re-nomination until addressed | `nomination_blockers` calls `failure_channels.open_review_gaps` | `test_open_review_gap_blocks_renomination` | IMPLEMENTED (extension; strengthens "unaddressed feedback loops back before re-review" without the over-blocking risk above) |

## 2.5 R2 — ReviewBundle

| Spec clause | Implementation | Test | Status |
|---|---|---|---|
| Frozen statement + pinned definitions + dependency path + full evidence (with replay commands) + numbered obligation checklist + attack history | `review_bundle.py::build_review_bundle`/`ReviewBundle` | `test_dependency_path_contains_the_ancestor`, `test_pinned_definitions_come_from_the_contract`, `test_attack_history_round_trips` | IMPLEMENTED. Scoping note: "pinned definitions" = the `TheoremContract`'s `assumptions`/`non_claims`/`scope`, not the `MathematicalObject` registry (which lives one layer up on `ResearchWorkspace`, unreachable from a bare `ResearchTrace` — same layering boundary R0/R1 already have). |
| Obligation = `{title, ask, points[], ref, required_assurance}` structured object, not prose | `review_bundle.py::Obligation` | round-trip + `test_obligation_requires_at_least_one_point` | IMPLEMENTED |
| `required_assurance` field present for R4 | `RequiredAssurance` enum (MACHINE_SUFFICIENT/HUMAN_SINGLE/HUMAN_DOUBLE) | `test_dependency_obligation_is_machine_sufficient`, `test_critical_claim_gets_independence_obligation_requiring_double_human_review` | IMPLEMENTED — R2 only assigns the label; R4 is where the promotion policy reads and enforces it |
| Attack history structured `{summary, emphasis[]}`, no HTML | `AttackHistoryItem` | `test_attack_history_round_trips`, `test_html_escapes_untrusted_free_text_fields` (HTML renderer escapes it regardless) | IMPLEMENTED |
| Per-file SHA-256 + sealed bundle digest | `write_review_bundle`/`verify_review_bundle_files` (manifest.json + 6 content files) | `test_tampering_any_file_is_detected`, `test_tampering_the_manifest_itself_is_detected`, `test_missing_bundle_file_is_detected` | IMPLEMENTED |
| Same trace bundled twice → byte-identical summary digest | deterministic construction: `created_at` excluded from `_files()`/digest (matching `KillTestSpec`'s convention), all collections sorted | `test_build_is_deterministic` | IMPLEMENTED |
| Numbered statement-correspondence item | `ReviewBundle.__post_init__` hard-requires `OB-STATEMENT-CORRESPONDENCE` to exist | `test_statement_correspondence_is_always_present_and_numbered`, `test_manually_built_bundle_without_statement_obligation_is_rejected` | IMPLEMENTED |
| Obligation copy passes appendix A's automated check | `check_obligation_copy`/`check_bundle_copy`: bans backend enum values, `snake_case`/`SCREAMING_SNAKE` identifiers, untranslated foreign quotes without the required `ref` disclaimer, internal jargon, titles over 20 characters, and semicolon-crammed points | `CopyRuleRegressionTests` (uses the spec's own before/after example as a literal fixture — the pre-revision text is rejected, the post-revision text passes), `test_generated_default_obligations_pass_the_copy_checker` | IMPLEMENTED. **Two real bugs found and fixed while building this, both worth recording**: (1) `_default_obligations`'s first draft embedded raw `EvidenceKind`/`ClaimStatus` values directly into obligation text (e.g. a title reading `证据 EV1（LITERATURE_RESULT）`) — caught by running the checker against its own output, not by inspection; fixed with an explicit natural-language label map and by moving identifiers into `ref`. (2) The checker's own enum-detection first missed enum values glued directly onto Chinese text with no whitespace (e.g. `...是 FALSIFIED，请...`), because it tokenized on `.split()` — a CJK-adjacent English token has no space to split on. Fixed by extracting ASCII-letter runs with a dedicated regex instead of whitespace tokenization. |
| Math-readable self-contained HTML view | `review_bundle.py::render_review_bundle_html` | `test_renders_self_contained_html_with_no_raw_json_dump`, `test_html_escapes_untrusted_free_text_fields` | IMPLEMENTED, **deliberately minimal**: reuses the color/type tokens already frozen in `docs/prototypes/review-console.html` (`FROZEN_RECRUITING_DEMO`) rather than proposing a new visual design — an instantiation with real data, not an iteration, so it does not count against the freeze. No JavaScript/interactivity: progressive disclosure is R6's job once this is served live; a bundle is inherently a static, archived artifact. |

## 2.75 R3 — CLI submission path

| Spec clause | Implementation | Test | Status |
|---|---|---|---|
| `matharc.v02 review` subcommand group: `nominate`/`bundle`/`submit --record review.json --reviewer <id>`/`revoke`/`status` | `cli.py::_run_review_command` wired under a new `review` subparser with nested `review_command` subparsers | `ColdFourStepFlowTests`, `CliRejectionTests` | IMPLEMENTED |
| Full cold four-step flow enters the chain | Each step is a **separate** `main()` invocation reloading the trace from the file the previous step wrote (`load_trace`/`save_trace`) — genuinely cold, not four calls sharing one in-memory trace | `test_nominate_bundle_submit_revoke_all_land_in_the_persisted_trace`: nominate → bundle → submit (mints HUMAN_AUDIT evidence, claim reaches PROVED-eligible) → revoke (evidence flips STALE) → status (shows both records) | IMPLEMENTED |
| Submissions from an id outside the roster, and from a conflicted reviewer, are both rejected | `submit` command propagates `ReviewAuthorizationError` as a non-zero `SystemExit` | `test_reviewer_outside_roster_is_rejected_with_nonzero_exit`, `test_conflicted_reviewer_is_rejected_with_nonzero_exit` | IMPLEMENTED |
| Revoke → evidence STALE | Same eager invalidation from R0, now verified end-to-end through the CLI (reload the trace file after a `revoke` CLI call and check `evidence[...].status`) | covered inside the four-step flow test | IMPLEMENTED |
| "对象级 `can_review` + RolePolicy 双检、封链" (object-level check *and* role-based policy, sealed into the hash-chained event ledger) | **Object-level `can_review` fully enforced** (it is `submit_review`'s own authority — not optional). **`RolePolicy` and `EventLedger` sealing deliberately deferred.** Every other `matharc.v02` CLI command (`run`, `plan`, `demo`, ...) already operates on a bare `load_trace`/`save_trace` round trip with no `ResearchWorkspace`/`SecuredResearchWorkspace`/`RolePolicy`/`EventLedger` involved at all — retrofitting that heavier layer onto only the review subcommands would be an inconsistent design choice imposed unilaterally this session, not a natural extension of the existing CLI. That integration is R6's job, where the spec's own dependency line already says it: "与 W4-3 服务器整合同步" (coordinated with the W4-3 server integration). | — | **SCOPED DOWN FROM THE LITERAL SPEC TEXT, DOCUMENTED** (not silently dropped) — see `_run_review_command`'s docstring for the same reasoning in the code itself |

## 2.9 R4 — promotion policy: per-obligation assurance ladder

Policy status: `review_policy.DEFAULT_POLICY_STATUS` = `CODED_DEFAULT_PENDING_CHIEF_SCIENTIST_SIGN_OFF`.
The default policy coded here is the spec's own proposal, not a value anyone
with the authority to set promotion policy has approved.

| Spec clause | Implementation | Test | Status |
|---|---|---|---|
| Abandon "max-weight path"; every obligation's `required_assurance` gates promotion instead | `review_policy.py::assurance_snapshot_for_claim` rebuilds the claim's `ReviewBundle` fresh at promotion time (same re-derive convention as F2's `promotion_route_blockers`) and checks every obligation's achieved assurance against what it requires | `SingleGroupCriticalClaimTests`, `TwoIndependentGroupsTests` | IMPLEMENTED |
| `critical: bool` keeps only structural meaning; assurance requirements live on the obligation | `OB-INDEPENDENCE` (HUMAN_DOUBLE) is generated only for critical claims by R2's own obligation generator; R4 does not special-case `claim.critical` anywhere in its own logic — it just evaluates whatever obligations R2 produced | — (structural; exercised implicitly by every R4 test) | IMPLEMENTED |
| Default policy: a critical claim closing wholly/partly on HUMAN_AUDIT needs 2 independent reviewer groups | Falls out of the general per-obligation mechanism: `OB-INDEPENDENCE` requires HUMAN_DOUBLE, achieved by counting distinct reviewer `independence_group` values with an OK verdict for that exact obligation_id across ACTIVE, current-revision `ReviewRecord`s | `test_critical_claim_closing_on_a_single_human_audit_group_is_rejected`, `test_critical_claim_with_two_independent_human_audit_groups_promotes` | IMPLEMENTED |
| "所有计算类义务已有 EXACT 档证据" (all computational obligations already have EXACT-tier evidence) | **Partially mechanized.** `OB-DEP-*` obligations (`required_assurance=MACHINE_SUFFICIENT`) are checked against the real dependency status. Beyond that, this clause doesn't have a crisp mechanical test given the current obligation model — it's closer to a process expectation than something `assurance_snapshot_for_claim` can verify on its own. Not silently claimed as done. | — | PARTIAL, DOCUMENTED |
| Opt-in trigger (not in the literal spec text, but load-bearing for not breaking every existing pure-machine claim) | `review_policy.review_gate_applies`: the entire R4 gate only activates when the claim's proof-capable accepted evidence includes ≥1 `HUMAN_AUDIT` item | `test_pure_machine_claim_is_untouched_by_the_gate` (critical claim, 2 independent EXACT groups, zero interaction with review.py, promotes exactly as before R4 existed) | IMPLEMENTED |
| Insufficient assurance on any necessary obligation blocks promotion, naming the obligation, with a `boundary_violation` trace | `assurance_blockers` produces one message per unsatisfied obligation naming its `obligation_id`; `trace.py::promote_claim`'s existing `boundary_violations.append(...)` on any `PromotionError` already covers this (unmodified — R4 reuses the same mechanism F2/R0 already established) | `test_critical_claim_closing_on_a_single_human_audit_group_is_rejected` (asserts both the obligation id and `boundary_violations[-1]`) | IMPLEMENTED |
| Fully-satisfied claim promotes and `metrics.py` tags `closure_trust_class` | `metrics.py::compute_research_metrics` now emits `review_assurance: {claim_id: {closure_trust_class, review_gate_applies, obligations[]}}` per claim (`machine`/`human`/`mixed`) | `test_critical_claim_with_two_independent_human_audit_groups_promotes` (asserts the full snapshot after a real promotion), `test_mixed_evidence_reports_mixed_trust_class` | IMPLEMENTED |
| **Real bug found and fixed while building this**: circular obligation | `_default_obligations`'s first draft generated an `OB-EVIDENCE-*` obligation for *every* non-machine accepted evidence item on a claim — including the review's own resulting `HUMAN_AUDIT` evidence, which would then demand a second "please independently assess this evidence" pass on itself that nothing could ever satisfy. Caught by running the new R4 gate against the *existing* R0 test suite, not by inspection — `test_full_happy_path_promotes_the_claim` (written before R2/R4 existed) started failing the moment R4 went live. Fixed with `review.is_review_derived_evidence`, which `_default_obligations` now checks to skip evidence a `ReviewRecord` itself produced. | Regression coverage: the pre-existing `test_full_happy_path_promotes_the_claim` in `test_v03_review.py` now exercises this path directly (it promotes through real `HUMAN_AUDIT` evidence with R4 active) | FIXED, kept as a permanent regression via the existing R0 test |

## 2.95 R6 — HTTP write path

Scope decision, made explicit in the module docstring and here: the spec
lines R6 up with W4-3's server integration, and W4-3 (the multi-run
workspace server) does not exist. The existing `WorkspaceHTTPServer` is
shaped around `ResearchWorkspace`'s object registry/source registry/
`EventLedger` commit-audit state machine — extending that safely under
time pressure without fully internalizing its invariants was a real risk
this session chose not to take. `review_server.py` is therefore a second
transport (HTTP) over the same bare-`ResearchTrace` library calls R3's CLI
already makes — not a new authority, and not yet integrated with
`ResearchWorkspace`/`EventLedger`. That integration remains real future
work once W4-3 exists, matching the spec's own acknowledged dependency
rather than working around it silently.

| Spec clause | Implementation | Test | Status |
|---|---|---|---|
| Unique authenticated write endpoint `POST /api/review`, roster token, constant-time compare, 64KB cap, everything else 405 | `review_server.py::ReviewRequestHandler.do_POST`/`_authorized` (`hmac.compare_digest`); `do_GET`/`do_PUT`/`do_DELETE`/`do_PATCH` all return 405 for `/api/review`; oversized bodies get 413 before any JSON parsing happens | `test_post_without_token_is_unauthorized_and_does_not_mutate`, `test_post_with_wrong_token_is_unauthorized`, `test_post_body_over_64kb_is_rejected`, `test_get_on_the_write_endpoint_is_405`, `test_put_anywhere_is_405` | IMPLEMENTED |
| `GET /api/review-queue` | Lists every nomination (`review.all_nominations`, new public wrapper) with a computed `has_active_review` flag | `test_review_queue_shows_the_nomination` | IMPLEMENTED |
| `GET /api/review-bundle/{id}` returns a **view model**, not the domain DTO; bundle endpoint response carries no unmapped backend enum name (negative test) | `review_server.py::bundle_view_model` maps every `EvidenceKind`/`EvidenceStatus`/`ClaimStatus`/`RequiredAssurance` value to a Chinese label before the response is built; `{id}` is the claim_id — the bundle is rebuilt fresh per request (same re-derive convention as everywhere else in this track), not fetched from a separately persisted bundle store | `test_review_bundle_view_model_has_no_unmapped_backend_tokens` (asserts specific raw enum literals are absent from the full response text), `test_review_bundle_for_unknown_claim_is_404` | IMPLEMENTED |
| Reviewer-facing evidence panel per `docs/prototypes/review-console.html` | **NOT DONE.** R6 shipped the API layer only; wiring a live front-end panel against these endpoints (as opposed to the static `render_review_bundle_html` from R2) is a separate, larger piece of work this session did not attempt, in service of reaching R7. | — | NOT STARTED |
| No/wrong token POST does not mutate state; HTTP and CLI produce equivalent events/evidence | Verified by reloading the trace file from disk after a rejected POST and confirming no evidence was added; the successful-POST path calls the exact same `submit_review`/`review_to_evidence` functions R3's CLI calls | `test_post_without_token_is_unauthorized_and_does_not_mutate`, `test_post_with_correct_token_submits_and_mints_evidence` | IMPLEMENTED |

## 2.99 R7 — import mapping layer (machine-completable half)

R7 splits into two genuinely different kinds of work. The spec itself
calls out the first half as underestimated in v1: **先补导入映射层**
("first fill in the import mapping layer") before anything about the
actual dogfood can happen. The second half — backfilling
arXiv:2607.28557 and having **two real human reviewers from different
institutions** walk 1-2 key lemmas through the full seven-step process —
requires actual recruited people; no automated session can produce that.
This slice implements the first half completely, and stops at the exact
boundary where the second half begins. See §4 below for what that means
concretely.

| Spec clause | Implementation | Test | Status |
|---|---|---|---|
| 对象/来源/依赖/证据映射 (object/source/dependency/evidence mapping) from `import_legacy_harness`'s conservative report into something directly submittable to R0-R6 | New `legacy_harness.py::build_importable_trace`: builds a real `TheoremContract` + `ClaimRecord`s (topologically ordered via a dedicated Kahn's-algorithm pass, `_topological_order`) + `EvidenceRecord`s for VERIFIED nodes, from the report plus the original acceptance manifest (which the report itself never echoes back in full — only a count). Open legacy obligations are preserved in `trace.metadata`, not dropped. | `BuildImportableTraceTests` (7 cases) | IMPLEMENTED |
| Dependency mapping specifically (the report previously discarded `dependencies` entirely — verified by reading `import_legacy_harness`'s original loop, which never read `raw.get("dependencies")` at all) | `import_legacy_harness` extended, additively, to read and validate each node's `dependencies` (dangling-reference and self-dependency both rejected at report-build time) and carry them into `imported_claims[].dependencies` | `DependencyMappingTests` (3 cases), `test_dependency_order_is_preserved_and_add_claim_succeeds`, `test_dependency_cycle_is_rejected_at_the_mapping_boundary` | IMPLEMENTED |
| "人核节点 SUPPORTED 不洗白" (a human-audited-but-not-independently-replayed node must not be laundered into something stronger) | A legacy node whose `matharc_status` is `SUPPORTED` maps to `ClaimStatus.CANDIDATE` — eligible for real nomination/review, **never** `PROVED`, regardless of how confident the legacy source's own status string was. Only `VERIFIED` nodes (which `import_legacy_harness` only assigns after confirming independent, replayable acceptance) receive real evidence — and even then `build_importable_trace` never calls `promote_claim` itself. | `test_supported_node_never_launders_to_proved`, `test_verified_node_gets_real_replayable_evidence` | IMPLEMENTED |
| The mapping layer's output is actually usable by R0-R6, not a disconnected data structure | An imported CANDIDATE claim is fed directly into `nominate_for_review` (R1) and succeeds | `test_imported_candidate_claim_closes_the_loop_into_r1_nomination` — also surfaces a genuine, correct-per-spec R1 behavior worth knowing about: a route-less claim (the mapping layer never fabricates a `ResearchRoute` the legacy source didn't have) passes R1's "every active route has a completed execution record" check vacuously, because it has zero active routes to check. This is not a bypass introduced by import — the identical vacuous-pass applies to any hand-built route-less CANDIDATE claim; R1's existing test suite already covers the route-bearing case correctly blocking. | `test_imported_candidate_claim_closes_the_loop_into_r1_nomination` | IMPLEMENTED, WITH A DOCUMENTED PRE-EXISTING EDGE CASE (not a regression from R7) |

## 3. What R0–R7's machine-completable half do *not* cover (honest boundary, not a promise)

- **The live reviewer-facing panel** (R6's UI half) — not built.
- **The rest of R7**: backfilling arXiv:2607.28557 through `build_importable_trace`, and having two real reviewers from different institutions actually walk 1-2 key lemmas through the full seven-step process, measuring per-obligation coverage, turnaround time, and machine-blind-spot failure classes the reviewers catch. **This cannot be produced by this session** — it requires real recruited human reviewers, which an automated agent has no means to fabricate honestly. The system this half would exercise (R0-R6, plus this slice's mapping layer) is real and ready for it; recruiting is the actual next step, not more code.
  (Correction made while drafting this document: an earlier version of this
  row claimed R5's REVIEW_GAP → `AdaptiveResearchDirector` wiring did not
  exist, based on a grep that searched for `AdaptiveResearchDirector`/
  `mandatory_attack_tests`/`route_constraints` as literal strings but missed
  the actual call site. It does exist —
  `_research_director_impl.py::AdaptiveResearchDirector.plan_round` already
  calls `failure_channels.open_review_gaps` and folds each open gap into
  both `mandatory_attack_tests` and `route_constraints` for the next round.
  R0/R1 do not add anything to that path; it predates this slice. Flagged
  here rather than silently fixed, since shipping a "verified, zero hits"
  claim that was actually wrong is exactly the kind of thing a second
  adversarial pass is supposed to catch.)
- v0.3-review as a *stage* does not formally exit per `DEV_PATH_V03.md` v4 §6's own dogfood-validated bar. This document covers real, tested, gated progress on R0 through R6 in full, plus R7's machine-completable import mapping layer — not a claim that the human-reviewer half of R7 has happened.

## 4. A verification-methodology bug caught and fixed during this session

Three consecutive `make ci-full` runs were launched as backgrounded shell
commands of the shape `(make ci-full > log; echo "exit:$?" >> log)` and were
read only through the task-completion notification, which reported
"exit code 0" for all three. That summary is the *wrapper shell's* exit
status (`echo` always succeeds), not `make ci-full`'s. All three runs had
actually failed with exit 2 — `sympy` was missing from the venv, so
`formal-preflight` refused before any test ran. This was only caught by
going back and reading each log file's own tail directly.

Fix: installed the `formal` extra (`pip install -e ".[research,dev,formal]"`)
and re-ran `make ci-full` in the foreground, reading `$?` directly with no
intermediate summarization step. That run is the one this document, and the
G0-c baseline it produced, actually rests on.

This is exactly the class of problem the user's own second-audit-round
instruction asked to be checked for (fake completion / evidence that
doesn't actually replay). It is recorded here rather than quietly
corrected, per this project's own disclosure discipline.
