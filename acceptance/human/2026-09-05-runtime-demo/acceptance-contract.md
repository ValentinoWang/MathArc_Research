# Human acceptance contract: runtime demo

- Task ID: `2026-09-05-runtime-demo`
- Scope: local demo workbench and persisted run readback
- Source commit: `9a1cd523cd1add39d6ed06369ce7f78c03562bbc`
- Access URL: `http://127.0.0.1:4174/problem-intel-console.html?demo=1`
- Machine evidence: `agents-results/2026-09-05/runtime-demo-readback-112316/`
- Human status: `PENDING`

## Acceptance steps

1. Start `matharc.v02.runtime.demo_server` with `--evidence-dir` pointing at the machine evidence directory.
2. Open the access URL at 390px, 820px, and a desktop width.
3. Enter the supported odd-sum question and run the Agent.
4. Confirm every stage is visible, the final status is `VERIFIED_CERTIFICATE`, evidence is shown,
   and no theorem-promotion control is implied.
5. Refresh/reconnect and confirm the run is still available from the server readback endpoint.
6. Enter an unsupported question and confirm the result is `BLOCKED` with `promotion_allowed=false`
   or no evidence.

## Decision

No human reviewer has yet signed this contract. Machine checks are recorded separately and do not
substitute for this review. Production `research.matharc.space` acceptance is out of scope until
the owner supplies deployment access and a real operator performs the same steps over HTTPS.

