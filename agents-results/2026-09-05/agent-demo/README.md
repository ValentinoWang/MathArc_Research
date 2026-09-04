# MathArc Agent stable demo evidence

This directory records machine-observed evidence for the local demonstration only.
It is not production evidence and it is not a human acceptance record.

## Open

Start the local server from the project root:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m matharc.v02.runtime.demo_server --host 127.0.0.1 --port 4173
```

Then open [http://127.0.0.1:4173/problem-intel-console.html](http://127.0.0.1:4173/problem-intel-console.html), choose the visitor demo, and use the `演示工作台` entry under `选题情报`.

## Observable loop

The workbench submits the question to the local `POST /api/demo/run` endpoint and renders:

1. question input;
2. deterministic Agent decomposition;
3. proposal plus exact induction tool call;
4. independent replay verification;
5. result and evidence digest.

The runner is credential-free, network-free, deterministic, and proposal-only. A successful certificate does not promote a theorem.

## Machine checks

- `tests.test_runtime_demo_server`: 3/3
- `tests.test_runtime_demo_runner`: 3/3
- `tests.test_codex_api`: 2/2
- `tests.test_console_prototype`: 16/16
- 390px browser smoke: no horizontal overflow; ready/loading/empty/error states rendered
- local HTTP smoke: `/api/health` 200 and `/api/demo/run` returned `VERIFIED_CERTIFICATE`, decomposition `READY`, tool `PASS`, verification `PASS`

The full browser gate still has an existing failure at the restored-session assertion before workbench cases execute; that failure is kept visible and is not reclassified as a demo pass.
