# A4 Regression And SSOT Independent Review

## P0/P1 findings

None.

No P0 or P1 defect was found in the frozen A4 review scope at `HEAD 5af1d9ff6fde02d86633cca50cf815ef04661d4a`. This is a zero-write, offline review lane. This lane cannot accept A4, change its SSOT state, unlock R1, or authorize publication or release.

## Source identity

- Commit: `5af1d9ff6fde02d86633cca50cf815ef04661d4a` (`fix: bind dogfood archive fixture contract`), parent `b4c6d3676428a2fb1f43a81978f8c9364b8ab8fa`.
- Tree: `fb14013eb548b220ec319d60e9c3814c9158a029`.
- Local refs observed: `HEAD`, `main`, `origin/main`, and `origin/HEAD` all resolve to `5af1d9ff6fde02d86633cca50cf815ef04661d4a`. No network readback was performed or claimed.
- Tracked worktree against the frozen commit: clean before testing and clean after testing. Six pre-existing untracked prompt/log files under this release-run directory were preserved unchanged in scope; this return is the only file created by this lane.
- Current implementation SHA-256: `matharc/v02/topic_observation.py` = `ee7b31685b58ed0130df17006244ca7c43b8afc416d84c02da863ff8686dfa20`; `matharc/v02/dogfood_archives.py` = `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8`.
- The current commit adds exact validation of the T2 `source_fixture_directory` and `non_claim_boundary`. Its only test edit replaces a temporary fixture-directory name to satisfy that contract and adds a fail-closed mutation test.

## SSOT and evidence binding

- A4 node SHA-256: `8e667181bafda099594037805028725d8b6c71e567e1a3ec113863dc4612ad30`.
- `E-T2-A4` SHA-256: `331d94dcdd5ede19482ce5d4b098d0ea9e1b32b9936a5a51f1b63c7e8acc23eb`. It is a hard, specific-output dependency requiring T2 `ACCEPTED` and transferring `DL-T2`.
- T2 is `ACCEPTED`, produces `DL-T2`, and its evidence SHA-256 is `42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3`. A4 declares T2 as its hard dependency and consumes `DL-T2`.
- `E-A4-R1` SHA-256: `a1624001ed27995067553987eb246e96cebbf1601d820aa98b72578d71afac3e`. It requires A4 `ACCEPTED`; A4 is only `VERIFIED`, so R1 remains blocked.
- A4 execution-contract SHA-256 is `f1258adac692989c52f91579972cf11bb4589066467b5812bd2f2fc5ac0fba5e`, exactly matching `execution_contract_sha256` in the A4 node. The contract preserves `execution_actor: human`, `write_authority: evidence-only`, `side_effect_class: none`, and `hard_dependencies: [T2]`.
- A4 and T2 bind the same decision reference, `decision.problem-intelligence.amendment@2`; A4 retains invalidation key `acceptance.problem-intelligence.dogfood`.
- Repository evidence `evidence/A4.json` has SHA-256 `f876e26f0438a1bb25434fddc96518125f7e69234af5919482545e8e5cdbfc29`, but its embedded source HEAD is historical (`fe9de3fd86e3670dc3a0c10621afa48fc4740fa8`). It was not reused as proof of current source bytes. This return is bound to fresh commands and hashes at `5af1d9f`; the acceptance owner must bind any formal result separately.

## Protected-test integrity

- `tests/test_v02_topic_observation.py`: present; SHA-256 `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56`.
- `tests/test_v02_dogfood_archives.py`: present; SHA-256 `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873`.
- The direct-parent dogfood test hash was `40f9350211415a32b59daa219971b34c45faafb7751d5f3516d3935502500635`. The reviewed commit changes it by `22` additions and one fixture-path replacement; it adds `test_contract_boundary_and_fixture_directory_are_immutable`. No test, assertion, or skip was removed.
- The A4 node/contract does not declare a separate approved protected-test hash registry. Therefore this review records the frozen current hashes and direct-parent integrity diff; it does not claim equality to a nonexistent approved hash baseline.
- Fresh focused execution ran all `41` tests in the two files and passed.

## Exact commands and results

1. `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests`
   - Exit `0`; `Ran 510 tests in 75.109s`; `OK (skipped=10)`.
   - Non-failing diagnostics: existing `ResourceWarning` messages reported unclosed subprocess streams in `matharc/agent_service.py` and `tests/test_codex_runtime.py`.
2. `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v tests.test_v02_topic_observation tests.test_v02_dogfood_archives`
   - Exit `0`; `Ran 41 tests in 7.568s`; `OK`.
3. `PYTHONDONTWRITEBYTECODE=1 PYTHON=python3 make console-browser-gate`
   - Exit `0`; `52 cases x 2 campaigns x 6 widths` passed.
   - The gate also passed the M1 SSE refresh/reconnect flow and the M2 review queue/bundle/rejection/token-clearing/persisted-approval flow.
4. `PYTHONDONTWRITEBYTECODE=1 PYTHON=python3 make publication-gate`
   - Exit `0`; fixture `valid: true`; readiness `TECHNICAL_PREFLIGHT_PASS`.
   - Warnings: proved fixture claims `C-BASE` and `C-STEP` have no explicit applicability boundary.
   - The command itself states: fixture only; no real-paper or publication authorization.

No command redirected output to a repository log. Python bytecode was disabled. Test and browser fixture writes were confined to automatically removed operating-system temporary directories.

## A4 criterion disposition

| Criterion | Disposition | Evidence boundary |
| --- | --- | --- |
| Three fixed, source-pinned archives remain bound to the T2 contract | `VERIFIED` | The checked-in S1/T2 fixture bytes and exact contract fields are hash-bound and covered by fresh focused/full tests. This is not live literature confirmation. |
| Replay | `VERIFIED` | Restart replay, canonical archive/state comparison, cursor behavior, and recomputed-digest mutations pass or fail closed as specified. |
| Recovery | `VERIFIED` | Legacy archive/state preservation and explicit recovery failure paths are exercised; no silent rewrite is accepted. |
| Deduplication | `VERIFIED` | Same-batch/restart and cross-batch duplicate behavior is covered by the focused tests and full regression. |
| Three archive outcomes and failure/manual-review boundaries are queryable | `VERIFIED` | The Frankl q=6 constrained case, reported-resolution collision case, and residual reported-open case remain distinct, with persisted provenance/status/manual-review evidence. These are reported-status fixtures, not mathematical conclusions. |
| No claim, trace, promotion, or public conclusion is created | `VERIFIED` | Exact non-claim contract text is now enforced; per-case flags, archive shape, canonical replay, and forbidden artifact checks are covered. |
| Full regression | `VERIFIED` | `510` tests passed with `10` declared skips; warnings above remain non-blocking technical debt. |
| Browser gate | `VERIFIED` for prototype regression only | The local prototype contract passed. It provides no authenticated production, deployed service, or device evidence. |
| Publication gate boundary | `VERIFIED` for deterministic technical preflight only | The generated fixture passed with two applicability warnings. It is not a real-manuscript audit or public-release authorization. |
| Formal A4 acceptance | `NOT PERFORMED` | Reserved to the A4 acceptance authority. This lane cannot accept A4. |

## Residual risk and overclaim boundary

- The fixtures and digests are local, fixed-source integrity evidence without an external trust anchor. A fully compromised host able to replace source, state, and all local digests is outside this review.
- The browser gate is a local prototype gate, not production, deployed-service, authenticated-role, or device evidence.
- The publication gate is a generated technical-preflight fixture and emitted two non-failing applicability warnings. It is not a real-paper audit, human signoff, submission approval, or public-release authorization.
- The full suite retains ten skips and emits subprocess-stream `ResourceWarning` diagnostics; neither was introduced by the reviewed commit, but both remain regression-harness debt.
- This review is offline and fixed to repository bytes. It is not mathematical proof, independent mathematical review, external or live literature confirmation, statistical/generalization evidence, production/device evidence, remote delivery proof, or public-release authorization.
- Formal acceptance remains an independent human-authority action. Until it exists and is bound to the frozen source and review returns, `E-A4-R1` is not satisfied and R1 must remain blocked.

## Proposed state

`proposed_state: VERIFIED`

This is the proposed state of this independent regression/SSOT review lane only. It does not accept A4.
