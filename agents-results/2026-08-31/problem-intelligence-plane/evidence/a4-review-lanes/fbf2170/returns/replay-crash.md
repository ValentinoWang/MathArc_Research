# Findings

## P0

None observed.

## P1

### P1-1: A data-path writer can roll back to an earlier valid authenticated triple

The HMAC authenticates the current state bytes and literature snapshot bytes, but the authentication record has no generation, cursor monotonicity, or external freshness commitment. The message format is only the domain, lengths, state bytes, and snapshot bytes (matharc/v02/topic_observation.py:193-200); the sidecar fields are only schema versions, two digests, and mac_sha256 (matharc/v02/topic_observation.py:1909-1915). Cursor validation proves only the chain contained in the supplied state (matharc/v02/topic_observation.py:1450-1523).

An attacker restricted to rewriting the data-path state, literature, and authentication files, without reading or changing the signing key, can restore state/auth/literature bytes from an earlier valid point. The fresh runner accepted the restored cursor:

    rollback_old_valid_triple=ACCEPTED:c1

This loses later durable history and permits later batches to be processed again. It is a valid-MAC rollback, not a forged MAC, so the stated same-user-host exclusion does not remove it. This is a blocking replay/recovery integrity finding within the declared boundary.

Reproduction, using only a temporary directory and copying the already persisted bytes:

    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
    import shutil
    import tempfile
    from pathlib import Path
    from tests.test_v02_topic_observation_integrity import batch, input_for
    from matharc.v02.topic_observation import TopicObservationRunner

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
        runner.run(batch("c0", "c1", input_for("A")))
        old_state = runner.state_path.read_bytes()
        old_auth = runner.authentication_path.read_bytes()
        old_literature = root / "literature-c1"
        shutil.copytree(root / "literature", old_literature)
        runner.run(batch("c1", "c2", input_for("B")))
        runner.state_path.write_bytes(old_state)
        runner.authentication_path.write_bytes(old_auth)
        shutil.rmtree(root / "literature")
        shutil.copytree(old_literature, root / "literature")
        print(TopicObservationRunner(
            root, topic_id="integrity-topic", initial_cursor="c0"
        ).next_cursor)
    PY

### P1-2: An idempotent existing observation with a different observation ID succeeds once and then fails on restart

LiteratureBase deliberately returns the already persisted observed record when logical identity and content digest match, even when the incoming observation ID differs (matharc/v02/literature_base.py:91-130). The runner records that returned persisted ID as the result and evidence (matharc/v02/topic_observation.py:742-754). On reload, however, the general non-manual check requires the result observation ID to equal the input projection observation ID (matharc/v02/topic_observation.py:1657-1660), before the EXISTING_OBSERVED-specific checks (matharc/v02/topic_observation.py:1661-1673).

The initial run therefore returns IDEMPOTENT with OBS-A for an input projected as OBS-B, but restart rejects the state:

    alternate_identity_run=status:IDEMPOTENT,observation:OBS-A
    alternate_identity_restart=REJECTED:TopicObservationError:stored result observation identity conflicts with input projection

This breaks a supported LiteratureBase idempotent replay path and makes a successfully advanced cursor unrecoverable. The distinct preexisting A+B case with different logical sources passes; this is the same-logical-source/different-observation-ID edge that the current integrity test does not cover.

Reproduction:

    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
    import hashlib
    import tempfile
    from tests.test_v02_topic_observation_integrity import batch
    from matharc.v02.literature_base import ImportDisposition
    from matharc.v02.source_observation import LicenseStatus, new_observation
    from matharc.v02.topic_observation import TopicObservationInput, TopicObservationRunner

    content = b"same logical source"
    digest = hashlib.sha256(content).hexdigest()

    def observation(observation_id):
        return new_observation(
            observation_id=observation_id,
            canonical_uri="https://integrity.example/same",
            pinned_version="v1",
            observed_at="2026-09-02T08:00:00+00:00",
            license_status=LicenseStatus.OPEN,
            license_basis="probe",
            content_summary="same",
            summary_basis="probe",
            media_type="text/plain",
            content_digest_sha256=digest,
        )

    with tempfile.TemporaryDirectory() as directory:
        runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
        assert runner.literature.import_bytes(observation("OBS-A"), content).disposition is ImportDisposition.IMPORTED
        result = runner.run(batch(
            "c0", "c1", TopicObservationInput("B", observation("OBS-B"), content)
        ))
        print("alternate_identity_run=status:%s,observation:%s" % (
            result.item_results[0].status.value,
            result.item_results[0].observation_id,
        ))
        try:
            print("alternate_identity_restart=ACCEPTED:%s" % TopicObservationRunner(
                directory, topic_id="integrity-topic", initial_cursor="c0"
            ).next_cursor)
        except Exception as exc:
            print("alternate_identity_restart=REJECTED:%s:%s" % (
                type(exc).__name__, exc
            ))
    PY

## P2

### P2-1: Pair persistence is fail-closed but not crash-recoverable

run() mutates LiteratureBase while processing an input (matharc/v02/topic_observation.py:620-665; the import path is matharc/v02/topic_observation.py:742-754). _save_state() then writes the state file and authentication sidecar as two separate atomic operations, in that order (matharc/v02/topic_observation.py:1896-1921). There is no pair journal, commit marker, or resume/reconciliation path.

An injected interruption after state replacement and before authentication replacement produced:

    state_then_auth_files=state_changed:True,auth_unchanged:True
    state_then_auth_restart=REJECTED:TopicObservationError:topic observation authentication state digest mismatch; persisted literature observations are not bound to the canonical state (canonical dogfood state replay must reject it)

An injected interruption after literature mutation but before state/auth completion produced:

    literature_then_pair_files=literature_changed:True,state_unchanged:True,auth_unchanged:True
    literature_then_pair_restart=REJECTED:TopicObservationError:topic observation state literature snapshot does not match current literature

The ordering is safe against accepting either torn state: _load_state reaches keyed verification before returning (matharc/v02/topic_observation.py:1523), and verification checks the snapshot, state digest, and MAC (matharc/v02/topic_observation.py:1076-1124). The result is nevertheless permanent availability loss for that root until an operator restores a matching triple or replays into a new root. Fail-closed safety is not recoverability.

The temporary-directory injection command was:

    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
    import tempfile
    from unittest.mock import patch
    import matharc.v02.topic_observation as topic_module
    from tests.test_v02_topic_observation_integrity import batch, input_for
    from matharc.v02.topic_observation import TopicObservationRunner

    with tempfile.TemporaryDirectory() as directory:
        runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
        runner.run(batch("c0", "c1", input_for("A")))
        prior_state = runner.state_path.read_bytes()
        prior_auth = runner.authentication_path.read_bytes()
        real_write = topic_module._atomic_write_bytes

        def fail_auth(path, content, mode):
            if path == runner.authentication_path:
                raise OSError("injected interruption before auth replace")
            return real_write(path, content, mode)

        try:
            with patch.object(topic_module, "_atomic_write_bytes", side_effect=fail_auth):
                runner.run(batch("c1", "c2", input_for("B")))
        except OSError:
            pass
        print("state_then_auth_files=state_changed:%s,auth_unchanged:%s" % (
            runner.state_path.read_bytes() != prior_state,
            runner.authentication_path.read_bytes() == prior_auth,
        ))
        try:
            TopicObservationRunner(
                directory, topic_id="integrity-topic", initial_cursor="c0"
            ).next_cursor
        except Exception as exc:
            print("state_then_auth_restart=REJECTED:%s:%s" % (
                type(exc).__name__, exc
            ))

    with tempfile.TemporaryDirectory() as directory:
        runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
        runner.run(batch("c0", "c1", input_for("A")))
        prior_state = runner.state_path.read_bytes()
        prior_auth = runner.authentication_path.read_bytes()
        prior_literature = runner.literature.manifest_path.read_bytes()
        with patch.object(runner, "_save_state", side_effect=OSError(
            "injected interruption after literature mutation"
        )):
            try:
                runner.run(batch("c1", "c2", input_for("B")))
            except OSError:
                pass
        print("literature_then_pair_files=literature_changed:%s,state_unchanged:%s,auth_unchanged:%s" % (
            runner.literature.manifest_path.read_bytes() != prior_literature,
            runner.state_path.read_bytes() == prior_state,
            runner.authentication_path.read_bytes() == prior_auth,
        ))
        try:
            TopicObservationRunner(
                directory, topic_id="integrity-topic", initial_cursor="c0"
            ).next_cursor
        except Exception as exc:
            print("literature_then_pair_restart=REJECTED:%s:%s" % (
                type(exc).__name__, exc
            ))
    PY

### P2-2: next_cursor can verify a stale in-memory literature snapshot

The runner loads LiteratureBase once during construction (matharc/v02/topic_observation.py:553-568). next_cursor calls _load_state without reloading that LiteratureBase (matharc/v02/topic_observation.py:570-577), while run() explicitly reloads it first (matharc/v02/topic_observation.py:579-586). The snapshot builder hashes self.literature (matharc/v02/topic_observation.py:968-985).

A long-lived runner therefore accepted a stale cursor after an external LiteratureBase added literature, while a fresh runner rejected the same state:

    stale_runner_next_cursor=ACCEPTED:c1
    fresh_runner_next_cursor=REJECTED:TopicObservationError:topic observation state literature snapshot does not match current literature

This is a TOCTOU/availability contract gap: a cursor consumer can observe an apparently verified stale state, although the actual run path will reload and fail before processing.

Reproduction:

    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
    import tempfile
    from pathlib import Path
    from matharc.v02.literature_base import LiteratureBase
    from matharc.v02.topic_observation import TopicObservationRunner
    from tests.test_v02_topic_observation_integrity import batch, input_for

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        writer = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
        writer.run(batch("c0", "c1", input_for("A")))
        stale = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
        LiteratureBase(root / "literature").import_bytes(
            input_for("B").observation, input_for("B").content
        )
        print("stale_runner_next_cursor=ACCEPTED:%s" % stale.next_cursor)
        try:
            TopicObservationRunner(
                root, topic_id="integrity-topic", initial_cursor="c0"
            ).next_cursor
        except Exception as exc:
            print("fresh_runner_next_cursor=REJECTED:%s:%s" % (
                type(exc).__name__, exc
            ))
    PY

### P2-3: State path permissions and symlink policy are weaker than key/auth policy

The signing key and authentication sidecar use lstat(), require regular files, and require mode 0600 (matharc/v02/topic_observation.py:990-1007 and :1046-1074). Key creation is private and non-replacing: it uses a temporary 0600 file, fsync, hard-links it only if absent, then re-reads the final path (matharc/v02/topic_observation.py:1009-1044). These boundaries passed the mode/symlink probes.

The state path is different. _load_state only checks _path_present() and then calls read_bytes() (matharc/v02/topic_observation.py:1140-1153); it never requires a regular file or mode 0600. A valid state target behind a symlink and a valid state file at mode 0644 were both accepted:

    state_symlink_valid_pair=ACCEPTED:c1
    state_mode_0644_valid_pair=ACCEPTED:c1

The HMAC still prevents content forgery, so this is not a key-extraction or MAC-bypass finding. It is an inconsistent path-boundary and availability hardening gap: the state can alias an external file and expose/consume bytes outside the intended root, while authentication/key paths fail closed for the same filesystem conditions.

## P3

### P3-1: The new integrity tests do not exercise the blocking cases above

tests/test_v02_topic_observation_integrity.py:51-92 covers key/auth creation and missing/malformed/replaced auth; :94-114 covers distinct preexisting A+B; :116-175 covers snapshot and recomputed tamper rejection; :177-191 covers legacy v1.4 preservation. None covers a valid old authenticated rollback, a two-file crash window, the same-logical-source alternate observation ID, a long-lived runner cache, or state symlink/mode handling. The green 69-test result therefore does not establish the broader replay/recovery contract.

### P3-2: The complete candidate diff is not whitespace-clean

git diff --check f7603d642a241b925926f9535fbdf25508901473..fbf217074d7b8efe251bd9ebe30d20d0104e1f3e exited 2, with trailing-whitespace diagnostics throughout the committed implementation log and a new blank line at EOF (the final diagnostic was implementation.log:106374). The scoped source/new-test check exited 0. This is non-blocking hygiene, not the cause of the FAIL verdict.

# Review Record

## Identity tuple

The required precondition was satisfied; no BLOCKED stop was triggered.

    GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD refs/remotes/origin/main 'HEAD^' 'HEAD^{tree}'

    fbf217074d7b8efe251bd9ebe30d20d0104e1f3e
    fbf217074d7b8efe251bd9ebe30d20d0104e1f3e
    f7603d642a241b925926f9535fbdf25508901473
    5606c42c95b684986c42a780e151920277bbf0e2

Tuple: HEAD=origin/main=fbf217074d7b8efe251bd9ebe30d20d0104e1f3e; parent=f7603d642a241b925926f9535fbdf25508901473; tree=5606c42c95b684986c42a780e151920277bbf0e2. The reviewed diff is f7603d642a241b925926f9535fbdf25508901473..fbf217074d7b8efe251bd9ebe30d20d0104e1f3e.

The read set included the two earlier failed returns under agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-review-lanes/1b05e61/returns/, the implementation return and execution ledger under agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/authenticated-replay-v2/, both changed sources, both new integrity tests, and protected tests tests/test_v02_topic_observation.py and tests/test_v02_dogfood_archives.py. The candidate diff has seven changed paths: the two source files, the two new integrity tests, and three authenticated-replay-v2 return/log/ledger artifacts.

## Commands and results

The required suite command was:

    PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_topic_observation_integrity tests.test_v02_topic_observation tests.test_v02_dogfood_archives tests.test_v02_literature_base_integrity tests.test_v02_literature_base

Result: exit 0; Ran 69 tests in 1.612s; OK; zero skips.

The protected hash command was:

    shasum -a 256 tests/test_v02_topic_observation.py tests/test_v02_dogfood_archives.py

Result:

    a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb  tests/test_v02_topic_observation.py
    e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873  tests/test_v02_dogfood_archives.py

The source/new-test scoped check was:

    git diff --check f7603d642a241b925926f9535fbdf25508901473..fbf217074d7b8efe251bd9ebe30d20d0104e1f3e -- matharc/v02/topic_observation.py matharc/v02/literature_base.py tests/test_v02_topic_observation_integrity.py tests/test_v02_literature_base_integrity.py

Result: exit 0. The full candidate diff check is the P3-2 result above.

The cheapest no-key same-data-path attacker was tested in two forms. Recomputing the current state snapshot and authentication digests after a literature mutation, while leaving the MAC unforgeable, returned:

    same_data_path_recompute_without_key=REJECTED:topic observation authentication MAC mismatch

Restoring a previously valid state/auth/literature triple returned ACCEPTED:c1 as P1-1 records. No probe read or changed the signing key, and a fully compromised same-user host was not used as a failure case.

The root/crash matrix is:

| Scenario | Observed outcome |
| --- | --- |
| New empty root | ACCEPTED; next_cursor=c0; state/auth/key remain absent until the first write |
| Key-only root | REJECTED; authentication state is missing |
| State-only root | REJECTED; authentication state is missing |
| Auth-only root | REJECTED; authentication state exists without a topic state |
| Legacy state v1.4 | REJECTED with the recovery-contract error; original legacy bytes preserved |
| Normal restart after c0 -> c1 | ACCEPTED; next_cursor=c1 |
| Distinct preexisting A+B, then incremental batches | PASS; both imports are IDEMPOTENT and restart advances to c2 |
| Same logical identity, alternate observation ID | Initial IDEMPOTENT write succeeds; restart REJECTED as P1-2 records |
| State replaced before auth | Fail closed with authentication state digest mismatch; no automatic repair |
| Literature mutated before state/auth | Fail closed with literature snapshot mismatch; no automatic repair |

Legacy behavior is implemented before current-schema field validation (matharc/v02/topic_observation.py:1158-1164) and is directly checked for byte preservation by tests/test_v02_topic_observation_integrity.py:177-191.

## Protected hashes

| Path | Required SHA-256 | Observed SHA-256 | Result |
| --- | --- | --- | --- |
| tests/test_v02_topic_observation.py | a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb | a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb | MATCH |
| tests/test_v02_dogfood_archives.py | e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873 | e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873 | MATCH |

## Boundary assessment

The implementation correctly keeps the 32-byte signing key outside JSON, creates it atomically with mode 0600, rejects key/auth mode-invalid and symlink paths, uses constant-time MAC comparison, and authenticates state plus the canonical literature snapshot before _load_state returns. Direct unkeyed recomputation is rejected. The distinct preexisting A+B incremental path and legacy v1.4 byte-preservation path pass.

Those passes do not close valid-triple rollback, the alternate-ID restart failure, the torn-write recovery gap, stale-runner snapshot verification, or the state-path policy inconsistency. AC-02 therefore has blocking correctness/security/recovery findings. This review treats implementation return claims as evidence only and does not renew any formal acceptance identity.

## Repository status

Business project: `## main...origin/main`; `git diff --name-only HEAD` was empty. The untracked fbf2170 review directory contains the pre-existing lane logs/prompts and state-adversarial return plus this newly written replay-crash return. No source, test, contract, SSOT, acceptance, or git-ref path was changed by this review.

Harness SSOT: `/Users/vsiyo/Desktop/Opensource_Tool/Harness_Engineering`, `## main...origin/main`, already dirty with unrelated tracked and untracked changes. This review made no Harness SSOT change.

## Final verdict

Verdict: FAIL

This is an independent zero-write evidence report. It does not accept A4, issue a human acceptance decision, or impersonate a human reviewer.
