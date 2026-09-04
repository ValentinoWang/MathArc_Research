# Runtime Pilot Operations Checklist

State: `NOT READY`

- [ ] Record runtime run ID, release ID, source commit, and evidence directory.
- [ ] Verify a fresh backup before any cleanup or restart.
- [ ] Clean only explicitly named, regenerable candidates inside the declared runtime root.
- [ ] Keep protected services, credentials, Codex state, user media, and active dependencies untouched.
- [ ] Reopen the runtime store and verify event-chain, snapshot, and state digests.
- [ ] Attach raw command output; a checklist checkbox alone is not evidence.

The template does not authorize cleanup, restart, deployment, or production access. `NOT READY` remains until an operator supplies independently retained evidence.
