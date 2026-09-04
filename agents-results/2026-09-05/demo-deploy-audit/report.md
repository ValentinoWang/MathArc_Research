# MathArc demo deployment audit

Audit date: 2026-09-05 (Asia/Shanghai)

Scope: `deploy/matharc-research.service`, `deploy/matharc-research.env.example`,
`examples/serve_workspace_v02.py`, the local v0.2 workspace bundle, the public
origin `https://research.matharc.space/`, and read-only probes of
`ubuntu@43.156.50.78`.

## Evidence

### Local complete workspace server

Command:

```text
/opt/homebrew/bin/python3.12 examples/serve_workspace_v02.py \
  --workspace artifacts/v02-workspace --host 127.0.0.1 --port 8765
```

Startup metadata declared `read_only: true`, `authentication: false`, TLS
outside the process, and per-request full workspace hash validation. A local
HTTP probe returned:

| Path | Result |
| --- | --- |
| `/` | 200 `text/html` |
| `/api/health` | 200, `audit_errors: 0`, `audit_warnings: 2` |
| `/api/workspace` | 200 |
| `/api/audit` | 200 |
| `/api/events?after=-1` | 200 |
| `/api/artifacts` | 200 |
| `/events?after=-1` | 200 SSE |

The source bundle is internally valid (`artifacts/v02-workspace/audit.json`:
`valid: true`, `error_count: 0`, state digest
`8aba2912a4dcd23f88310a3c60d0e9ecb8f35ef2641a89cabebaad8afb089eda`). The two
scope warnings are expected demo warnings, not deployment failures.

### Deployment entrypoint mismatch

`deploy/matharc-research.service:13` starts:

```text
/usr/bin/python3 -m matharc.v02.runtime.ops serve ...
```

`matharc/v02/runtime/ops.py:212-218` bootstraps the durable runtime, then calls
`matharc.api.serve`. That server exposes the older v0.1 surface (`/api/run`,
`/api/metrics`, `/api/validate`, `/api/agent/*`) and does not expose the v0.2
workspace observatory (`/api/workspace`, `/api/console`, `/api/audit`,
`/api/events`, `/api/artifacts`, `/events`) or invitation/session routes.

Reproduction with concrete temporary env, credential, run file, and runtime
store: `ops healthz` and `ops readyz` both exited 0; `ops serve` returned 200 for
`/` and `/api/health`, but returned 404 for `/api/workspace`, `/api/console`,
and `/api/runtime/snapshot`. This is a code-path mismatch, not a missing Caddy
route.

### Public origin (`https://research.matharc.space/`)

Read-only probes from this machine:

| Path | Result |
| --- | --- |
| `/api/health` | 200 JSON; `run_id: MATHARC-V02-DEMO-ODD-SUM`, `audit_errors: 0`, `audit_warnings: 2`; remote state digest starts `3d220c6e`, event head starts `ea702f32` |
| `/api/access/session` | 401 `invalid_credentials` |
| `/api/workspace` | 401 `access_required` |
| `/api/console` | 401 `access_required` |
| `/api/audit` | 401 `access_required` |
| `/api/events?after=-1` | 401 `access_required` |
| `/events?after=-1` | 401 `access_required` |
| `/api/runtime/snapshot` | 401 `access_required` |
| `/api/runtime/events?after=-1` | 401 `access_required` |
| `/api/review-queue` | 404 `not_found` (the public HTML advertises this endpoint) |
| `/api/run` | 404 `not_found` |

The public response headers identify Caddy and TLS is valid for
`research.matharc.space` (Let's Encrypt, valid 2026-09-03 through 2026-12-02).
The root advertises `200`, `content-length: 446193`; several GETs timed out
after receiving only a partial body (examples: 20,299 bytes and 118,603 bytes),
while a later probe completed the full body over both HTTP/1.1 and HTTP/2. The
transfer stall is therefore intermittent and still needs an independent-client
recheck before human acceptance. No invitation code was used or generated
during this audit.

The remote `/api/health` state/event digests do not match the current local
bundle (`8aba2912...` and `9d2ff670...`). Without authorized host readback this
cannot be classified as a bad deployment, but it does prove that the public
artifact is not the exact local bundle audited here; release provenance must be
recorded before presenting the demo as current `main`.

The delivered HTML also references `/api/review-queue`, `/api/review-bundle/{id}`
and `POST /api/review`; the unauthenticated queue probe is 404, indicating the
optional review API is not configured at the public edge. The basic read-only
workspace flow can still be tested after login, but a review workflow cannot be
claimed until those endpoints are intentionally enabled or the surface is
explicitly marked unavailable.

### Remote host access

TCP 22/80/443 on `43.156.50.78` are reachable, but the supplied local SSH
identity was rejected (`Permission denied (publickey,password)`). Therefore
`systemctl`, service logs, deployed commit, runtime identity, and local
readiness cannot be claimed from the host. This is an explicit evidence gap,
not evidence that the service is down.

### Existing acceptance/runtime-pilot state

`acceptance/runtime-pilot/ops-checklist.md`,
`ops-release-checklist.md`, and `production-checklist.md` remain `NOT READY`;
`production-attack-drills.md` remains `NOT RUN`; and
`acceptance/runtime-pilot/release-evidence.json` records
`NO_REAL_RELEASE_EVIDENCE`, `PENDING_UNSIGNED`, and no deployment or remote
readback evidence. The focused local deployment/bootstrap/observability/
backup/release/cleanup plus runtime HTTP suite passed 19/19 tests with zero
skips. These are local machine checks only and do not promote production
readiness.

## Minimum repair checklist for a stable demo loop

1. **Choose one serving path and bind the service to it.** The v0.2 demo loop
   requires `serve_workspace_v02.py`/`matharc.v02.workspace_server`, with the
   generated `workspace-dashboard.html` and the complete v0.2 API. The current
   `ops serve -> matharc.api.serve` path cannot satisfy that contract. A code
   integration (or a deliberately documented separate service) is required;
   changing only Caddy cannot create the missing endpoints.
2. **Provision immutable inputs before restart.** On the target, record the
   exact source commit/release ID, create the persistent run file at
   `MATHARC_RUN_PATH`, publish `workspace.json` plus every manifest-referenced
   file, and verify the workspace audit/state digest before opening the edge.
3. **Keep the durable runtime checks in the same process boundary.** Preserve
   the external systemd credential, `RuntimeStore`, runtime identity, and
   `readyz` check. Add an HTTP/readback contract for the same process (or retain
   a separately recorded CLI readback) so `/api/health` cannot be mistaken for
   runtime readiness.
4. **Configure invitation/TLS edge explicitly.** Use an external access store,
   `--access-cookie-secure` behind Caddy, and an operator-issued invitation.
   Verify one authenticated browser session can load `/api/console`, stream
   `/events`, and read `/api/runtime/snapshot`; keep unauthenticated 401
   negative checks.
5. **Resolve optional review-surface policy.** Either wire the configured review
   trace/token so `/api/review-queue` and `/api/review-bundle/{id}` return their
   documented view models, or record the feature as intentionally unavailable
   and verify the UI's unavailable state. Do not treat a 404 as a successful
   review loop.
6. **Verify the public transfer before human acceptance.** Investigate the
   intermittent Caddy/upstream body stall observed for `/` (headers are 200,
   with a 446,193-byte body; later HTTP/1.1 and HTTP/2 probes completed). Re-run
   repeated complete GETs and a browser load from an independent client.
7. **Collect release evidence on the intended host.** With authorized SSH,
   capture `systemctl show/status`, `ops healthz`, `ops readyz`, edge health,
   source commit, runtime/release IDs, backup/restore readback, and rollback
   rehearsal into a new `agents-results/YYYY-MM-DD/<task>/` directory. Only
   then can the runtime-pilot checklists move beyond `NOT READY`; human
   acceptance remains a separate signed lane.

## Verdict

The local v0.2 server is demonstrable and its focused tests are green. The
current declared deployment is **not a stable v0.2 demo loop** because its
systemd entrypoint serves a different API, the public root has an observed
intermittent partial-body timeout that still lacks independent-client proof,
and the target host cannot be read back with the available SSH credentials. No
remote restart or mutation was performed.
