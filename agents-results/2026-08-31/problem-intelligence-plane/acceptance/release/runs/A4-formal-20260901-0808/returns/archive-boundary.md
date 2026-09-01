# A4 Archive-Boundary Independent Acceptance Review

- Review lane: `archive-boundary`
- Scope: SSOT node `A4` only
- Review mode: zero-write review lane; the only repository write is this return
- Frozen source: `5af1d9ff6fde02d86633cca50cf815ef04661d4a`
- Proposed state: `VERIFIED`
- Acceptance authority: none in this lane. **This lane cannot accept A4.**

## Findings

### P0

None.

### P1

None.

No protected test was deleted, skipped, weakened, or bypassed in the reviewed scope. The focused archive suite and an independent temporary-directory execution/restart probe passed against the frozen source. The evidence is sufficient for `VERIFIED` at this review-lane boundary only.

## Source Identity

- `HEAD`: `5af1d9ff6fde02d86633cca50cf815ef04661d4a`
- `origin/main`: `5af1d9ff6fde02d86633cca50cf815ef04661d4a`
- Tree: `fb14013eb548b220ec319d60e9c3814c9158a029`
- Parent: `b4c6d3676428a2fb1f43a81978f8c9364b8ab8fa`
- Commit subject: `fix: bind dogfood archive fixture contract`
- Business project status before this return: `main...origin/main`, with the review-run directory already untracked; no tracked diff.
- Harness SSOT: `/Users/vsiyo/Desktop/Opensource_Tool/Harness_Engineering`, `HEAD 86d7c2cc7bdb0ed6f6628c8ad40250119ccb84a2`, `main...origin/main`, clean.

Reviewed byte identities:

| Artifact | SHA-256 |
| --- | --- |
| `matharc/v02/dogfood_archives.py` | `3be729235ac138f9358654c60d5462dbacb731e46dbec496e0ed895f46c031a8` |
| `matharc/v02/topic_observation.py` | `ee7b31685b58ed0130df17006244ca7c43b8afc416d84c02da863ff8686dfa20` |
| `evidence/t2-fixtures/three-real-archives.json` | `475e9bdd6cdceb3d497706eff25ff77329016941c5f4dec389c2099a59de412c` |
| `.ssot/nodes/A4.json` | `8e667181bafda099594037805028725d8b6c71e567e1a3ec113863dc4612ad30` |
| `.ssot/execution-contracts/A4.json` | `f1258adac692989c52f91579972cf11bb4589066467b5812bd2f2fc5ac0fba5e` |
| `.ssot/edges/E-T2-A4.json` | `331d94dcdd5ede19482ce5d4b098d0ea9e1b32b9936a5a51f1b63c7e8acc23eb` |
| `.ssot/edges/E-A4-R1.json` | `a1624001ed27995067553987eb246e96cebbf1601d820aa98b72578d71afac3e` |
| `evidence/T2.json` | `42e5e5993a2705cd5a51532282f887f0950bf2634b2d4c186771b7f2a37fbaa3` |
| `evidence/A4.json` | `f876e26f0438a1bb25434fddc96518125f7e69234af5919482545e8e5cdbfc29` |

The A4 node embeds execution-contract SHA-256 `f1258adac692989c52f91579972cf11bb4589066467b5812bd2f2fc5ac0fba5e`, exactly matching the observed A4 execution-contract bytes.

## Protected-Test Integrity

| Protected path | Frozen SHA-256 | Integrity disposition |
| --- | --- | --- |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | Present at `HEAD`; 13 discovered tests; no skips; focused run passed. Relative to prior reviewed hash `40f9350211415a32b59daa219971b34c45faafb7751d5f3516d3935502500635`, the frozen commit adds the immutable `non_claim_boundary` / `source_fixture_directory` test and changes the copied fixture directory to the required `s1-fixtures` identity. |
| `tests/test_v02_topic_observation.py` | `1b505da5b1757b66a37ce859a8745fd20ac34c651ee1c7f53f9102bc18cfaa56` | Present at `HEAD`; reviewed for replay, duplicate suppression, budget/manual queue, cursor conflict, persisted-result linkage, coordinated projection tampering, and legacy recovery assertions. No skip decorator or broad weakening found. |

`git show 5af1d9f:<path> | sha256sum` matched the working-tree SHA-256 for both protected tests and both reviewed implementation modules. `git diff --exit-code HEAD -- <reviewed paths>` returned exit `0` before this return was written.

The historical A4 review hash is not silently treated as the current approved byte identity: `5af1d9f` intentionally changes the archive protected test. Inspection of that diff found 22 additions and 1 replacement relative to `2e47f50`, with the replacement aligning the copied fixture directory to the newly enforced contract identity; no prior assertion was removed.

## Fixed Fixtures And Source Artifacts

The three S1 fixture hashes exactly match `fixture_sha256` in `three-real-archives.json`:

| Fixture | SHA-256 |
| --- | --- |
| `confirmed-open.json` | `2eac896e4038750a0b59baadc5d4b3b04aa261f4680b51839fbb507ca035053a` |
| `frankl-q6.json` | `d76d9f4a03d781f1a2b66168666b00ff7c1c4107b8ca48fb48fefdc18325c592` |
| `resolved-collision.json` | `935ec7a4cc236f44fbba60c877be9cff85fc4edb99cfc7c0e55ab4f9ccdd2acd` |

The four fixed source bytes also match the contract:

| Source artifact | SHA-256 | Reviewed meaning |
| --- | --- | --- |
| `sources/engineering-progress.md` | `f0090168916eab1e1642c0ac0325914492b9725f1432027aa983b0bfe482b4cb` | Reports the constrained q=6 residual and explicitly keeps global Frankl open. |
| `sources/frankl-q6-exactly-three-small-outside-parts.md` | `8ef2177acb983fdd1ef6602e7cae1b4853eed0c94ba1eff2e3b6cd188fc33476` | States the four-or-more-small-parts residual and explicitly denies an upgrade to the general case or Frankl's conjecture. |
| `sources/erdos-397-current.html` | `ba778973416d0d89a00e206777be974891e0317c106ef155f8ddb430c00a6885` | Pinned database artifact identifies problem 397 and records a negative answer. |
| `sources/arxiv-2601.22401v3-main.tex` | `540973d154a63470f8648ed2b84b75be04c2c56ee7bf0d4047640510573647bd` | Pinned v3 source names Erdos-397 and reports infinitely many solutions; this is observed source content, not proof accepted by this lane. |

No network retrieval was performed. These are fixed source bytes only.

## Exact Contract Semantics

### `source_fixture_directory`

The contract value is exactly `../s1-fixtures`. `DogfoodArchiveRunner._load_contract()` first rejects every different string, then resolves the value relative to the T2 contract directory and requires it to equal the runner's supplied fixture root. The observed resolution was:

`evidence/t2-fixtures/../s1-fixtures` = `evidence/s1-fixtures` = runner fixture directory.

The protected test mutates this value to `/tmp/evil` and observes `DogfoodArchiveError: T2 source fixture directory identity drift`. Thus the field is an immutable relative identity plus a resolved-directory equality constraint, not a caller-controlled path.

### `non_claim_boundary`

The accepted value is exactly:

> All outputs are source observations and reported-status review boundaries. They do not create a mathematical claim, research trace, public conclusion, or research-budget authorization.

The implementation compares this full string to a code-owned constant before any execution. The protected test replaces it with `authorizes public mathematical claims` and observes `DogfoodArchiveError: T2 non-claim boundary identity drift`. The contract file's byte digest is also persisted and rechecked on restart.

## Three-Case Identity And Status

The contract and implementation require exactly these three IDs, roles, and order; duplicate, missing, unknown, or substituted cases fail closed. The fresh execution/restart probe observed:

| Problem ID | Role | Topic | Replay/dedup | Reported / validated | Manual / novelty | Promotion / claim / trace |
| --- | --- | --- | --- | --- | --- | --- |
| `P-FRANKL-Q6` | `frankl-q6-constrained-residual` | `APPLIED` | `REPLAYED` | `OPEN_REPORTED` / `OPEN_REPORTED` | none / none | `false / false / false` |
| `P-ARXIV-2601-22401-COLLISION` | `database-open-literature-resolved-collision` | `APPLIED` | `DUPLICATE` | `RESOLVED_REPORTED` / `RESOLVED_REPORTED` | `HIGH_RISK_EVENT` / `PENDING_HUMAN_AUDIT` | `false / false / false` |
| `P-FRANKL-Q6-FOUR-OR-MORE-SMALL-OUTSIDE-PARTS` | `frankl-q6-four-or-more-small-outside-parts-residual` | `MANUAL_REVIEW` | `NOT_APPLICABLE` | `OPEN_REPORTED` / `STALE` | `BUDGET_EXHAUSTED` / none | `false / false / false` |

The result remained `archive_blocked: true` with two canonical blocking manual entries.

## Replay, Recovery, Deduplication, And Budget

- Replay: the first execution returned `replayed: false`; a new runner over the same temporary state returned `replayed: true`. Replay revalidates the contract, all S1 fixture bytes, all fixed source bytes, the full canonical archive body, both persisted topic-state snapshots, cursors, ArtifactStore counts, and manual queue.
- Recovery: archive schemas `1.0` and `1.1` and legacy topic-state schema require explicit operator recovery and are preserved byte-for-byte on rejection. Unsupported recovery-contract drift fails closed; there is no silent rewrite.
- Deduplication: the Frankl cursor replay is `REPLAYED`; the collision source recheck is `DUPLICATE`; persisted observation counts are checked on restart. Topic-observation state binds input projections, fingerprints, results, disposition evidence, manual queue/event linkage, and cursor state.
- Budget: the residual runner reconstructs an exhausted ledger with input-token limit/spend `1`, model calls `1`, tool calls `0`, and no divergent usage reports. Observed and contract budget digest: `efdf4e18af10228e0706db1ee91b896ead57982e132a4e5315faf79860eb4b45`. Recomputed archive/budget digests cannot authorize altered budget content because canonical execution and the contract-owned expected snapshot are compared.
- Failure-closed coverage: protected tests exercise coordinated manual-queue tampering, manual-result tampering, invalid state enums, case/status/provenance/novelty drift after digest recomputation, case-set substitution, promotion/claim/trace mutation, malformed data, source/fixture/contract drift, and legacy recovery.

## No-Promotion And No-Claim Boundary

Every contract case requires `expected_promotion_allowed: false`. Every generated and replayed case must have `promotion_allowed`, `claim_created`, and `trace_created` exactly `false`; canonical replay rejects coordinated recomputation of a modified archive. The collision novelty authorization remains `PENDING_HUMAN_AUDIT`, with complete research budget and public qualitative conclusion both disallowed. The run root contains no `claims.json`, `research-trace.json`, or `trace.json`, and `no_claim_or_trace_created` remained `true` on restart.

This mechanism proves the declared archive schema and named-artifact boundary. It does not semantically classify arbitrary filenames or independently validate the mathematical content contained in the pinned source documents; those limits remain explicit residual risk rather than promotion authority.

## A4 Criterion Disposition

| A4 criterion | Disposition | Evidence |
| --- | --- | --- |
| T2 hard dependency and artifact binding | PASS | T2 evidence is `EV-T2-ACCEPTED-1`; `E-T2-A4` requires `ACCEPTED`; A4 consumes `DL-T2`. Contract and source identities revalidate at restart. |
| Exactly three real source-pinned archive cases | PASS | Exact IDs/roles/order, S1 fixture hashes, four fixed source hashes, and observed statuses match the T2 contract. |
| Replay and restart | PASS | Fresh run then new-runner restart produced `false -> true`; canonical archive and persisted state equality are enforced. |
| Recovery | PASS | Legacy archive/state inputs fail closed, require explicit recovery, and remain preserved. |
| Deduplication | PASS | Frankl replay `REPLAYED`; collision recheck `DUPLICATE`; state/ArtifactStore closure is checked. |
| Budget and failure-mode closure | PASS | Exhausted one-token budget, two manual boundaries, status collision, residual `STALE`, and canonical manual linkage are bound. |
| No promotion, claim, trace, public conclusion, or budget authorization | PASS within declared offline archive boundary | Exact non-claim contract string, per-case false flags, pending human novelty audit, forbidden named-artifact check, and canonical replay all pass. |
| A4 formal acceptance | NOT PERFORMED by this lane | A4's actor pool and acceptance authority are human. `E-A4-R1` requires A4 `ACCEPTED`; this lane supplies review evidence only and cannot unlock R1. |

## Commands And Results

1. Source freeze and status:

   `git rev-parse HEAD origin/main; git rev-parse HEAD^{tree}; git rev-parse HEAD^; git status --short --branch`

   Result: exit `0`; `HEAD == origin/main == 5af1d9ff6fde02d86633cca50cf815ef04661d4a`; tree and parent as recorded above; no tracked changes.

2. Focused archive tests:

   `env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/tmp python3 -m unittest -v tests.test_v02_dogfood_archives`

   Result: exit `0`; `Ran 13 tests in 6.936s`; `OK`; 0 failures, 0 errors, 0 skips.

3. Independent temporary execution/restart probe:

   `env PYTHONDONTWRITEBYTECODE=1 TMPDIR=/tmp python3 -c 'import json,tempfile; from pathlib import Path; from matharc.v02.dogfood_archives import DogfoodArchiveRunner; e=Path("agents-results/2026-08-31/problem-intelligence-plane/evidence"); c=json.loads((e/"t2-fixtures/three-real-archives.json").read_text()); d=tempfile.TemporaryDirectory(prefix="a4-archive-review-",dir="/tmp"); a=DogfoodArchiveRunner(d.name,e/"s1-fixtures").run(); r=DogfoodArchiveRunner(d.name,e/"s1-fixtures").run(); print(json.dumps({"source_fixture_directory":c["source_fixture_directory"],"resolved_matches":(e/"t2-fixtures"/c["source_fixture_directory"]).resolve()==(e/"s1-fixtures").resolve(),"non_claim_boundary":c["non_claim_boundary"],"first_replayed":a["replayed"],"restart_replayed":r["replayed"],"archive_blocked":r["archive_blocked"],"manual_count":len(r["blocking_manual_queue"]),"budget_digest":r["budget_digest_sha256"],"budget_exhausted":r["budget_snapshot"]["exhausted"],"no_claim_or_trace_created":r["no_claim_or_trace_created"],"cases":[[x["problem_id"],x["topic_status"],x["replay_status"],x["status"]["reported_status"],x["status"]["validated_status"],x["manual_reason"],None if x["novelty"] is None else x["novelty"]["authorization_status"],x["promotion_allowed"],x["claim_created"],x["trace_created"]] for x in r["cases"]]},sort_keys=True)); d.cleanup()'`

   Result: exit `0`; `resolved_matches: true`; first/restart replay `false/true`; `archive_blocked: true`; `manual_count: 2`; budget exhausted with digest `efdf4e18...`; `no_claim_or_trace_created: true`; exact case tuple values are recorded in the table above. The temporary directory was outside the repository and was removed by the probe.

4. Protected/source hash checks:

   `sha256sum matharc/v02/dogfood_archives.py matharc/v02/topic_observation.py tests/test_v02_dogfood_archives.py tests/test_v02_topic_observation.py agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures/three-real-archives.json agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures/sources/* agents-results/2026-08-31/problem-intelligence-plane/evidence/s1-fixtures/*.json`

   Result: exit `0`; hashes match the frozen Git blobs and the fixture contract values recorded above.

5. Scoped zero-diff check before writing this return:

   `git diff --exit-code HEAD -- matharc/v02/dogfood_archives.py matharc/v02/topic_observation.py tests/test_v02_dogfood_archives.py tests/test_v02_topic_observation.py agents-results/2026-08-31/problem-intelligence-plane/.ssot/nodes/A4.json agents-results/2026-08-31/problem-intelligence-plane/.ssot/execution-contracts/A4.json agents-results/2026-08-31/problem-intelligence-plane/.ssot/edges/E-T2-A4.json agents-results/2026-08-31/problem-intelligence-plane/.ssot/edges/E-A4-R1.json agents-results/2026-08-31/problem-intelligence-plane/evidence/T2.json agents-results/2026-08-31/problem-intelligence-plane/evidence/A4.json agents-results/2026-08-31/problem-intelligence-plane/evidence/t2-fixtures agents-results/2026-08-31/problem-intelligence-plane/evidence/s1-fixtures`

   Result: exit `0`; no reviewed implementation, protected test, fixture, SSOT, or evidence file differed from `HEAD`.

## Residual Risk And Boundary

- Offline review of fixed source bytes only. No live source freshness or external literature confirmation is established.
- The source documents contain reported mathematical statements; this lane did not validate them as mathematical proof and does not accept their correctness.
- No production environment, device, external sandbox, or public endpoint was exercised.
- No public-release authorization, research-trace creation, mathematical claim, qualitative public conclusion, or research-budget authorization is granted.
- Filename-based claim/trace absence is narrower than semantic inspection of arbitrary future artifact names; canonical archive comparison and exact false flags cover the current declared schema.
- Formal A4 acceptance remains outside this lane. A4 remains review-verified only; `R1` must remain blocked until the designated human acceptance authority records an A4 `ACCEPTED` result.

## Disposition

`proposed_state: VERIFIED`

Reason: no P0 or P1 finding was identified in the archive-boundary scope, focused archive tests passed, protected tests and fixed bytes are intact, and all reviewed A4 criteria are supported at the declared offline boundary. This is independent review evidence only. **This lane cannot accept A4.**
