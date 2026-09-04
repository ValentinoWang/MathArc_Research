# Runtime Pilot Operations Release Checklist

State: `NOT READY`

- [ ] release ID, source commit, runtime run ID, and plan digest agree.
- [ ] Focused runtime pilot, adversarial, release, and cleanup tests pass with zero skips.
- [ ] Backup artifact and restore readback are attached.
- [ ] Health/readiness and service status readback are attached from the intended host.
- [ ] Rollback rehearsal restores the last complete generation commit and records the recovery plan digest.
- [ ] Human operator acceptance is stored separately and hash-bound; this template is not a signature.

No production run or human approval is claimed by this document. Do not change `NOT READY` without the corresponding evidence paths.
