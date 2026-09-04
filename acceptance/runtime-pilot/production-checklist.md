# Runtime Pilot Production Checklist

State: `NOT READY`  
Evidence lane: machine evidence only until a separately stored human acceptance record exists.

## Preflight

- [ ] The exact release commit and runtime run ID are recorded.
- [ ] `runtime-pilot-plan.json` is unchanged or its digest is recorded.
- [ ] Focused pilot tests pass with zero skips.
- [ ] The two-generation report contains raw machine output and snapshot/commit digests.

## Production gate (not executed by this pilot)

- [ ] Deployment target, service identity, and secret source are verified by an operator.
- [ ] Backup and restore have been exercised on the target host.
- [ ] Health/readiness and rollback commands have successful readback evidence.
- [ ] A human acceptance record is stored under `acceptance/human/runtime-pilot/<run-id>/` and hash-bound to this checklist.

Until every production item has independently retained evidence, this checklist must remain `NOT READY`. No item is signed by this template.
