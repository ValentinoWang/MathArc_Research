# Production readback: research.matharc.space

- Readback time: 2026-09-05 17:05 CST (2026-09-05 09:05 UTC)
- Deployed source release: `c3be6e9`
- Previous release retained for rollback: `60cfadb73bae25e12bc6d7176b2a456c852d2acb`
- Workspace state digest: `8aba2912a4dcd23f88310a3c60d0e9ecb8f35ef2641a89cabebaad8afb089eda`
- Workspace event head: `9d2ff670ee0cc60a25ae25402f40975154aa9ea11b657a019949f53134cccdd7`

## Machine results

- `matharc-research.service`: `enabled`, `active (running)`; `User=matharc`, `Group=matharc`, listener `127.0.0.1:8173`.
- systemd unit SHA-256: `62b2c1d4def3a520c56368bc2936620eba6f0b66e03c46b03fe7dbba23373584` (matches the local tracked unit).
- systemd `ExecStartPost` health probe: `status=0/SUCCESS`.
- systemd `runtime.ops readyz`: `ok=true`, `status=ready`, `release_id=c3be6e9`, `runtime_run_id=pilot-research-20260905`.
- Caddy configuration validation: `Valid configuration`.
- Caddy config SHA-256: `4e0c9cd19a036675ac17ec3441c44a369b9b61a67d53ab8067602cb9a6b5caa8`.
- Caddy route: `research.matharc.space -> 127.0.0.1:8173`; TLS is terminated by Caddy.
- TLS certificate: `CN=research.matharc.space`, Let's Encrypt `YE1`, valid 2026-09-03 through 2026-12-02; SHA-256 fingerprint `64:4C:CE:75:33:69:66:0A:78:5E:E0:99:E6:6D:74:2B:76:07:E5:33:5B`.
- Independent public root readback: HTTP/1.1 and HTTP/2, 3 runs each, all `rc=0`, HTTP `200`, `42394` bytes, body SHA-256 `222ed6d050136b5f2bfb614e1a009f3e10c4be2e54034f8ca4171c9ef2fa7c62`.
- Public `/api/health`: HTTP `200`; reports `audit_errors=0`, `audit_warnings=2`, and the workspace digests above.
- Unauthenticated public `/api/workspace`, `/api/console`, and `/api/runtime/snapshot`: HTTP `401` with `access_required`.

## Remaining boundaries

- The production access store currently has zero applications, invitations, and sessions. No recipient email or operator-issued invitation was supplied, so authenticated `/api/console`, `/api/runtime/snapshot`, SSE, and runtime action readback were not fabricated or performed.
- Human acceptance remains `PENDING`; this machine report is not a signature or a substitute for a real person visiting over HTTPS.
- The project SSOT validation remains `release_complete=false`, `integrity_result=fail`, `bundle_valid=false`, and `push_gate_eligible=false`; those states were not changed by deployment.
- An earlier HTTP/1.1 partial-body timeout was observed before the final three-run recheck. The final recheck passed, but this remains a residual monitoring item rather than a claim of zero historical transport risk.
