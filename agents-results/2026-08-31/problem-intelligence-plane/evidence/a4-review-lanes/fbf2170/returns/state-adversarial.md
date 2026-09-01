# A4 Authenticated Replay State-Adversarial Review

## Findings

### P0

None observed.

### P1

1. **A previously valid authenticated tuple can replace newer literature and cursor history without the signing key.**

   `_verify_state_authentication()` authenticates only the state/snapshot tuple presented at load time (`matharc/v02/topic_observation.py:1076-1124`). The sidecar written by `_save_state()` has state and snapshot digests plus a MAC, but no monotonic generation, predecessor commitment, or trusted external high-water mark (`matharc/v02/topic_observation.py:1909-1920`). Restoring the exact old state, authentication sidecar, literature manifest, and artifact manifest after advancing from `c1` to `c2` was accepted as `next_cursor=c1`. The probe did not read, replace, or use the signing key. This is an authenticated rollback, not a recomputed-MAC attack, and it can hide every batch and literature record added after the captured tuple.

   Reproduction:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
   import tempfile
   from pathlib import Path
   from matharc.v02.topic_observation import TopicObservationRunner
   from tests.test_v02_topic_observation_integrity import input_for, batch

   with tempfile.TemporaryDirectory() as directory:
       root = Path(directory)
       runner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
       runner.run(batch("c0", "c1", input_for("A")))
       paths = [
           root / "topic-observation-state.json",
           root / ".topic-observation-state.auth.json",
           root / "literature" / "observations.json",
           root / "literature" / "artifacts" / "manifest.json",
       ]
       old = {path: path.read_bytes() for path in paths}
       runner.run(batch("c1", "c2", input_for("B")))
       before = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0").next_cursor
       for path, content in old.items():
           path.write_bytes(content)
       after = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0").next_cursor
       print(f"before={before} after={after} key_read_or_used=False")
   PY
   ```

   Observed: `before=c2 after=c1 key_read_or_used=False` (exit 0).

2. **A normal interruption after literature persistence leaves an authenticated state that cannot recover.**

   `run()` imports each item through `LiteratureBase` before calling `_save_state()` (`matharc/v02/topic_observation.py:623-665,742-755`); `LiteratureBase` persists its artifact and observation manifest before returning (`matharc/v02/literature_base.py:204-222`). If the process stops in that window, the old state/auth sidecar remains while the literature snapshot has advanced, and restart rejects it. A second crash window exists because `_save_state()` replaces the state and authentication sidecar in two separate atomic writes (`matharc/v02/topic_observation.py:1916-1920`). No journal, two-slot generation, rollback pointer, or recovery operation closes either window. This violates the recovery portion of AC-02; fail-closed detection alone does not restore an interrupted durable transition.

   Reproduction:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
   import tempfile
   from matharc.v02.topic_observation import TopicObservationRunner
   from tests.test_v02_topic_observation_integrity import input_for, batch

   with tempfile.TemporaryDirectory() as directory:
       runner = TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0")
       runner.run(batch("c0", "c1", input_for("A")))
       def interrupted(_state):
           raise RuntimeError("simulated interruption before state save")
       runner._save_state = interrupted
       try:
           runner.run(batch("c1", "c2", input_for("B")))
       except RuntimeError as exc:
           print(f"run={exc}")
       try:
           TopicObservationRunner(directory, topic_id="integrity-topic", initial_cursor="c0").next_cursor
       except Exception as exc:
           print(f"restart={type(exc).__name__}:{exc}")
   PY
   ```

   Observed: the simulated interruption occurred after `OBS-B` was persisted; restart raised `TopicObservationError: topic observation state literature snapshot does not match current literature` (exit 0).

3. **Public recovered-state reads authenticate a stale in-memory literature snapshot after concurrent mutation.**

   The runner loads `LiteratureBase` once during construction (`matharc/v02/topic_observation.py:545-568`). `manual_queue` and `next_cursor` call `_load_state()` without taking the writer lock or reloading literature (`matharc/v02/topic_observation.py:570-577`), and the MAC check constructs its snapshot from that cached object (`matharc/v02/topic_observation.py:968-988,1081-1124,1215-1218`). `run()` explicitly reloads literature at line 585, but these two public reads do not. After a separate, successful `LiteratureBase.import_bytes()` added `OBS-B`, an already-constructed runner returned authenticated `c1`; a fresh runner correctly rejected the same on-disk state for snapshot mismatch. Recovered state was therefore trusted without authenticating the current persisted literature/artifact snapshot.

   Reproduction:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
   import tempfile
   from pathlib import Path
   from matharc.v02.literature_base import LiteratureBase
   from matharc.v02.topic_observation import TopicObservationRunner
   from tests.test_v02_topic_observation_integrity import input_for, batch

   with tempfile.TemporaryDirectory() as directory:
       root = Path(directory)
       owner = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
       owner.run(batch("c0", "c1", input_for("A")))
       stale = TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0")
       item_b = input_for("B")
       print("external=" + LiteratureBase(root / "literature").import_bytes(
           item_b.observation, item_b.content
       ).disposition.value)
       print("stale=" + stale.next_cursor)
       try:
           TopicObservationRunner(root, topic_id="integrity-topic", initial_cursor="c0").next_cursor
       except Exception as exc:
           print(f"fresh={type(exc).__name__}:{exc}")
   PY
   ```

   Observed: `external=IMPORTED`, `stale=c1`, then fresh load raised `TopicObservationError: topic observation state literature snapshot does not match current literature` (exit 0).

### P2

1. **The new one-key/one-record invariant relies on a lossy source identity and can launder distinct sources as an idempotent replay.**

   `SourceObservation.logical_identity` lowercases the entire URI, including the case-sensitive path, and concatenates URI/version with an unescaped `|`; the idempotency key hashes that ambiguous string (`matharc/v02/source_observation.py:99-107`). `LiteratureBase` returns `IDEMPOTENT` for an observed same-identity/digest record before reaching the new distinct-ID key check (`matharc/v02/literature_base.py:91-130,175-185`). Two valid URIs that differ only by path case therefore collapse, as do accepted field tuples such as `uri=https://probe.example/a|b, version=c` and `uri=https://probe.example/a, version=b|c`. In both probes `OBS-LOWER`/`OBS-RIGHT` was reported as the previously persisted ID rather than a distinct source.

   Reproduction core:

   ```bash
   PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
   import hashlib, tempfile
   from matharc.v02.literature_base import LiteratureBase
   from matharc.v02.source_observation import LicenseStatus, new_observation

   content = b"same-content"
   digest = hashlib.sha256(content).hexdigest()
   def obs(oid, uri, version="v1"):
       return new_observation(
           observation_id=oid, canonical_uri=uri, pinned_version=version,
           observed_at="2026-09-02T08:00:00+00:00", license_status=LicenseStatus.OPEN,
           license_basis="probe", content_summary="Descriptive metadata.",
           summary_basis="probe", media_type="text/plain", content_digest_sha256=digest,
       )
   for left, right in (
       (obs("OBS-UPPER", "https://probe.example/Paper"), obs("OBS-LOWER", "https://probe.example/paper")),
       (obs("OBS-LEFT", "https://probe.example/a|b", "c"), obs("OBS-RIGHT", "https://probe.example/a", "b|c")),
   ):
       with tempfile.TemporaryDirectory() as directory:
           base = LiteratureBase(directory)
           first = base.import_bytes(left, content)
           second = base.import_bytes(right, content)
           print(left.logical_identity == right.logical_identity, first.disposition.value,
                 second.disposition.value, second.observation.observation_id)
   PY
   ```

   Observed: `True IMPORTED IDEMPOTENT OBS-UPPER` and `True IMPORTED IDEMPOTENT OBS-LEFT` (exit 0). The candidate does prevent two IDs from being persisted under one computed key, but the computed key is not an injective source identity.

2. **State-path hardening is inconsistent, and key/auth path checks have a pathname TOCTOU.**

   Key and authentication sidecar loads use `lstat`, reject stable non-regular paths, and require exact mode `0600` (`matharc/v02/topic_observation.py:990-1006,1046-1060`). The state load only checks presence and then follows `read_bytes()` (`matharc/v02/topic_observation.py:1140-1155`); a symlinked state and a mode-`0666` state were both accepted when their bytes matched the MAC. Key/auth checks also perform `lstat()` and `read_bytes()` as separate pathname operations, so a concurrent rename can change the object between check and use. Exact state bytes remain MAC-bound, so the stable symlink/mode probes did not forge state semantics, but the declared non-regular/permission posture does not cover the state path and does not atomically bind key/auth checks to the bytes read.

   Reproduction: create one valid batch in a `TemporaryDirectory`; rename `topic-observation-state.json` to `state.backing`, symlink the original name to the backing file, and load `next_cursor`; repeat after `chmod 0666 topic-observation-state.json`. Observed `ACCEPTED:c1` for both. Equivalent stable symlink and mode-`0644` probes for the key and sidecar raised `not a regular file` and `must have mode 0600`, respectively.

### P3

1. **Artifact `created_at` is intentionally outside the authenticated canonical snapshot.**

   `_literature_snapshot_payload()` removes `created_at` from every artifact record (`matharc/v02/topic_observation.py:968-981`). Changing only that persisted manifest field to `1900-01-01T00:00:00+00:00` was accepted at `c1` without changing state, sidecar, or key. This matches the implementation return's disclosed provenance-only exclusion, so it is not treated as an A4 blocking semantic failure here. The field must not be presented downstream as authenticated provenance.

2. **The candidate-wide whitespace check fails in the committed implementation transcript.**

   `git diff --check f7603d642a241b925926f9535fbdf25508901473..fbf217074d7b8efe251bd9ebe30d20d0104e1f3e` exited 2 with trailing whitespace and final-blank-line diagnostics only in `agents-results/2026-08-31/problem-intelligence-plane/evidence/a4-remediation/authenticated-replay-v2/logs/implementation.log` (first reported at line 6391; final diagnostic at line 106374). The four functional source/test paths pass the scoped check. This is evidence hygiene, not the cause of the P1 verdict.

## Identity Tuple

| Item | Observed identity | Result |
| --- | --- | --- |
| Local `HEAD` | `fbf217074d7b8efe251bd9ebe30d20d0104e1f3e` | MATCH |
| Local `origin/main` | `fbf217074d7b8efe251bd9ebe30d20d0104e1f3e` | MATCH |
| Live `refs/heads/main` (`git ls-remote`, no ref update) | `fbf217074d7b8efe251bd9ebe30d20d0104e1f3e` | MATCH |
| Parent | `f7603d642a241b925926f9535fbdf25508901473` | MATCH requested range |
| Tree | `5606c42c95b684986c42a780e151920277bbf0e2` | RESOLVED |
| SHA-256 of `git diff --no-ext-diff f7603d6..fbf2170` | `13b3b79d6794391e05bda7e49feb426dcd9acc7a4b3d39614053a419bb025130` | RECORDED |
| Implementation return SHA-256 | `a74c0def4d6e26ec127ab84d0028a619cd60ca6e327783e0c55d99d5b3dbe407` | matches ledger |
| Execution ledger SHA-256 | `22ab1acf05ee0465ef75a71277a9eb4822ac810095c1ac5b73f562f4cad1bf86` | RECORDED |
| Implementation log SHA-256 | `4db47222cab9a0bceef23750838ae53520465d4aeab6fde4e6e1fcbdbec4f13f` | matches ledger |
| Prior `state-integrity.md` SHA-256 | `1039e3e697280ab96e4274a44f5bf0aee23b6c4cfa9390d3dc76c6b913f653da` | READ |
| Prior `replay-closure.md` SHA-256 | `34e126bfbc286e431c0741d73c678dd777137897bf393f58bf75170bc71eca84` | READ |
| Runtime | macOS 26.0.1 (25A362), Darwin 25.0.0 arm64, Python 3.13.7 | RECORDED |
| Review time | `2026-09-02T05:16:19+0800` | Asia/Shanghai |
| Authority | independent zero-write review; this report is the sole authorized write | NO ACCEPTANCE AUTHORITY |

The exact `f7603d6..fbf2170` functional diff modifies `matharc/v02/literature_base.py` and `matharc/v02/topic_observation.py` and adds the two integrity test modules. The two protected modules are not in that diff.

## Commands And Results

1. `GIT_OPTIONAL_LOCKS=0 git rev-parse HEAD refs/remotes/origin/main HEAD^ 'HEAD^{tree}'`
   - Exit 0; returned candidate, candidate, parent, and tree identities recorded above.
2. `GIT_TERMINAL_PROMPT=0 GIT_OPTIONAL_LOCKS=0 git ls-remote --exit-code origin refs/heads/main`
   - Exit 0; live remote main was the exact candidate SHA. No local ref was updated.
3. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_topic_observation_integrity.TopicObservationIntegrityTests.test_coordinated_literature_replacement_fails_after_unkeyed_recompute tests.test_v02_topic_observation_integrity.TopicObservationIntegrityTests.test_manual_reference_laundering_fails_after_unkeyed_recompute tests.test_v02_topic_observation_integrity.TopicObservationIntegrityTests.test_partial_preexisting_inventory_supports_incremental_existing_observed`
   - Exit 0; 3/3 passed.
   - Independent replay of their mutations produced `COORDINATED_REPLACEMENT=REJECTED` and `MANUAL_REFERENCE_LAUNDERING=REJECTED`, both at the exact-state digest check. The legitimate path produced `preimports=IMPORTED,IMPORTED results=IDEMPOTENT,IDEMPOTENT next_cursor=c2`.
4. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest -v tests.test_v02_topic_observation_integrity tests.test_v02_literature_base_integrity tests.test_v02_topic_observation tests.test_v02_dogfood_archives tests.test_v02_literature_base`
   - Exit 0; `Ran 69 tests in 1.647s`; `OK`; zero skips.
5. Reviewer HMAC reconstruction in a `TemporaryDirectory`, using `_state_authentication_message` over the exact state bytes and canonical snapshot bytes:
   - `state_sha256=True`, `literature_snapshot_sha256=True`, `hmac.compare_digest=True`.
   - The message is domain-separated and length-prefixed at `matharc/v02/topic_observation.py:183-191`; exact state and canonical snapshot bytes are both MAC inputs.
6. Literature identity matrix, all in temporary directories:
   - Observed alternate ID: `IMPORTED`, then `IDEMPOTENT` returning `OBS-A`; persisted IDs `['OBS-A']`.
   - Pending alternate ID: `PENDING`, then `REJECTED`; persisted IDs `['OBS-A']`.
   - Crafted reload with `OBS-A` and `OBS-C` under one key: `ValueError: duplicate observation idempotency key`.
   - Two forked concurrent observed imports: one `IMPORTED`, one `IDEMPOTENT` returning the winning ID; both processes exit 0; exactly one ID/key persisted.
7. Path/permission probes in isolated roots:
   - State symlink: accepted `c1`; state mode `0666`: accepted `c1`.
   - Auth symlink/key symlink: rejected as non-regular.
   - Auth mode/key mode `0644`: rejected; exact `0600` required.
8. `PYTHONDONTWRITEBYTECODE=1 .venv/bin/mypy --no-incremental --strict matharc/v02/topic_observation.py matharc/v02/literature_base.py`
   - Exit 0; no issues in two source files.
9. `git diff --check f7603d6..fbf2170 -- matharc/v02/literature_base.py matharc/v02/topic_observation.py tests/test_v02_literature_base_integrity.py tests/test_v02_topic_observation_integrity.py`
   - Exit 0. The candidate-wide form exits 2 only on the committed implementation log described at P3.

## Protected-Test Integrity

| Protected path | Required SHA-256 | Worktree SHA-256 | `HEAD:<path>` SHA-256 | Parent-to-candidate diff | Result |
| --- | --- | --- | --- | --- | --- |
| `tests/test_v02_topic_observation.py` | `a6ac5fdb82f832e4eb14402d9727fcc5027a7574fb5d9765002d3016741fc9eb` | same | same | none | PASS |
| `tests/test_v02_dogfood_archives.py` | `e1efa41cf802015ace54c35faaeb176bb22e5263f0e2824aea4bf9d82f779873` | same | same | none | PASS |

`git diff --exit-code f7603d6..fbf2170 -- <both protected paths>` exited 0. Searches found no `skip`, `expectedFailure`, mock/patch weakening in the protected or new integrity modules and no fixture/test-name branch in either changed source file. The new tests are additive and the required attack/positive assertions execute against real temporary persistence.

## Threat-Boundary Assessment

- **Confirmed repair within the declared key-separation boundary:** exact state bytes and the parsed canonical literature/artifact snapshot are inputs to HMAC-SHA256. Unkeyed recomputation of state digests does not close the MAC, so the coordinated replacement and manual-reference laundering attacks from the two prior failed reviews are rejected. The legitimate partial preexisting inventory path succeeds.
- **Real findings not requiring current signing-key compromise:** stale-runner acceptance and interrupted-transition failure require no key or sidecar access. Authenticated rollback requires a previously valid state/auth/snapshot tuple and ability to restore the sidecar, but no signing key or MAC recomputation. It is therefore distinct from a fully compromised signer and must be addressed or explicitly excluded by a durable trusted-storage boundary.
- **Explicitly disclosed outside boundary:** a same-user host/process that can read, replace, or invoke the 32-byte signing key can re-sign the prior manual-reference or coordinated-history mutations. That is not counted again as a vulnerability in this verdict. Mode `0600` is correctly enforced for stable key/auth files, but it is not a substitute for an external freshness anchor.
- **Canonical rather than byte-exact literature binding:** observation semantics and artifact metadata other than `created_at` are canonicalized and MAC-bound; artifact blob integrity is verified against bound SHA-256 metadata on `LiteratureBase` load. Raw manifest formatting, orphan unmanifested blobs, and artifact `created_at` are not committed. The HMAC construction itself has no length/cross-field ambiguity; the separate source-identity canonicalization at P2 does.
- This review is offline source/runtime evidence only. It does not accept A4, renew the stale formal acceptance tuple, impersonate a human reviewer, establish mathematical truth, authorize public release, or claim production/device evidence.

## Repository Status

- Business project before this return: `main...origin/main`, no tracked changes, with four pre-existing untracked prompt/log files under the `fbf2170` lane. This report is the only reviewer-authored path.
- Harness SSOT real repository: `/Users/vsiyo/Desktop/Opensource_Tool/Harness_Engineering`, `main...origin/main`, already dirty with unrelated tracked and untracked work. This review made no Harness SSOT change.

## Final Verdict

**FAIL**

The two named unkeyed attacks are closed and the required positive inventory behavior works, but authenticated rollback, stale-snapshot trust, and non-atomic crash recovery are blocking correctness/security findings within the reviewed A4 replay/recovery boundary. This lane does not accept A4 and has no human-acceptance authority.
