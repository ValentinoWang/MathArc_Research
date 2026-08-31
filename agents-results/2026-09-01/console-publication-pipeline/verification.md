# Console Publication Pipeline: Verification Record

## Scope verified

- M0: deterministic console export and CLI output.
- M1: read-only observatory API, including an explicit `404 dashboard_not_found` when no dashboard exists.
- M2: console prototype bridge, EventLedger hash display, provenance visibility, and memory-only review-token handling.
- M3: source-bound topic projection with no inferred open/resolved/novelty status.
- M4: local, append-only operations ledger isolated from research replay state.

## Automated evidence

The final authoritative Gate 0 command was run from this worktree with an isolated Python environment:

```text
make ci-full PYTHON=/tmp/matharc-console-ci.zumGSg/bin/python
```

It passed strict mypy for 70 modules, 423 unit tests with zero failures/errors (two declared historical skips), 20 SMT tests with zero skips, v0.1 and v0.2 acceptance, and Frankl replay. The command ended with `Gate 0 authoritative CI complete: formal capability present and SMT suite executed.`

Focused console checks also passed:

```text
/tmp/matharc-console-ci.zumGSg/bin/python -m unittest -v tests.test_console_prototype tests.test_v02_console_export tests.test_v02_console_observatory tests.test_v02_console_topic tests.test_operations_ledger tests.test_v02_workspace_server
```

Result: 23 tests passed. JavaScript parsing of all script blocks in `docs/prototypes/problem-intel-console.html` also passed.

## Review disposition

Two independent AI review lanes examined the API/ledger and prototype/security surfaces. They found three defects that were repaired before the final Gate 0 run:

1. A non-HTTP canonical source URI could reach a clickable prototype link; links are now restricted to `http:` and `https:`.
2. The read-only observatory generated a missing dashboard on `GET /`; it now returns explicit 404 without creating state.
3. A caller could mutate the record returned by the operations ledger and affect later history; `append()` now returns a deep copy.

The reviewers were stopped after these source changes and did not emit final-version PASS reports. Therefore this record treats the final result as automated-gate evidence, not as completed independent-AI acceptance.

Browser automation was not run because the installed browser-control plugin lacks its required `scripts/browser-client.mjs` runtime. This is an environment limitation; it was not bypassed.

## Post-review hardening

Two subsequent fixed-commit AI reviews found a P0 export overwrite path and several P1/P2 integrity and presentation gaps. The hardening change closes them before final delivery:

1. `export` resolves its target and rejects every path inside the workspace root, so it cannot overwrite `workspace.json` or another audited workspace file.
2. Campaign reports now use a typed envelope whose report digest and three provenance values (`run_id`, state digest, and event head) must match the current workspace.
3. The operations ledger now validates an exact signed-record schema, serializes appenders with an exclusive lock and fresh state reload, and updates memory only after the atomic replace succeeds.
4. The browser bridge consumes only declared live-view contracts, verifies the fixed event genesis and unique IDs, hashes backend-provided canonical unsigned event bytes, coalesces SSE refreshes, clears stale snapshots on failure, preserves focus across a refresh, and restricts review tokens to same-origin `/api/review`.

New negative coverage rejects workspace-output overwrite, forged/malformed campaign envelopes, ledger field injection, two-instance lost writes, and persistence-failure memory contamination.

The final authoritative Gate 0 rerun after this hardening passed strict mypy for 70 modules, 428 unit tests with zero failures/errors (two declared historical skips), 20 SMT tests with zero skips, v0.1 and v0.2 acceptance, and Frankl replay. The focused console/observatory/ledger/workspace suite passed 27 tests; prototype JavaScript parsing passed.
