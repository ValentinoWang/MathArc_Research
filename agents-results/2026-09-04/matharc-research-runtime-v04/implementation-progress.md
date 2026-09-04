# MathArc research runtime v04 implementation progress

Updated: 2026-09-05

## Stable demonstration slice

The local, credential-free MathArc Agent demonstration is implemented and
machine-verified. It covers the core observable loop:

`question -> decomposition -> proposal -> exact tool -> independent replay -> result/evidence`

The demonstration is deterministic, network-free, and proposal-only. A passing
certificate is evidence and does not promote a theorem claim.

Primary entry points:

- `matharc/v02/runtime/demo_runner.py`
- `matharc/v02/runtime/demo_server.py`
- `docs/prototypes/problem-intel-console.html`
- `agents-results/2026-09-05/agent-demo/README.md`

## Machine evidence

- `tests.test_runtime_demo_runner`: 3/3
- `tests.test_runtime_demo_server`: 3/3
- `tests.test_console_prototype`: 16/16
- `tests.test_codex_api`: 2/2
- local HTTP `/api/health`: 200
- local HTTP `/api/demo/run`: verified certificate, exact tool PASS, independent replay PASS

## Explicit boundaries

- This slice does not claim real-model execution, production deployment, or
  human acceptance.
- The v04 SSOT node ledger remains governed by its compiled acceptance and
  authority contracts; implementation presence alone does not change a node
  to `ACCEPTED`.
- The existing full browser gate still has a restored-session failure before
  reaching the workbench cases; the dedicated demo checks remain green.
- Remote GitHub synchronization and production readback are separate release
  gates and must be verified independently.
