# UX6 Runtime Console Human Acceptance Checklist

Status: **TEMPLATE - NOT SIGNED**  
Task: `UX6`  
Scope: invitation-only desktop and mobile console viewing, permission negative paths, and the complete operator flow.

This document is a record for a human acceptance run. It is intentionally not
machine evidence and does not claim that UX6 is accepted. The reviewer must
fill every observation, attach the browser evidence, and sign the result.

## Run Identity

| Field | Value |
| --- | --- |
| Environment / base URL | `<fill before run>` |
| Build / commit | `<fill before run>` |
| Browser and version | `<fill before run>` |
| Desktop viewport | `<fill before run>` |
| Mobile device or emulation | `<fill before run>` |
| Invitation identity (redacted) | `<fill before run>` |
| Runtime run / generation observed | `<fill before run>` |
| Evidence directory | `<fill before run>` |

## Desktop Invitation Flow

- [ ] Landing page clearly distinguishes demo data from a signed-in console.
- [ ] Without an invitation, protected console data and write actions remain unavailable.
- [ ] Valid invitation redemption enters the console and shows the signed-in identity, scope, run status, generation, and data boundary.
- [ ] Invalid or expired invitation shows an actionable error and does not enter the console.
- [ ] Invitation code is not retained in visible state, URL, or browser storage.
- [ ] Navigation, live refresh/reconnect, and the permitted read/action flow complete without a horizontal overflow or hidden status.

Observation / evidence: `<fill>`  
Reviewer initials: `<fill>`

## Mobile Flow

- [ ] At 390x844 and the selected real device width, the shell is single-column and the top bar remains usable.
- [ ] Provenance, runtime status, and data-boundary indicators remain visible or reachable without clipping.
- [ ] Controls are reachable by touch and keyboard; expanded/disclosure states are understandable.
- [ ] No horizontal page scroll hides content or action controls.
- [ ] The same invitation, permission, reconnect, and read/action outcomes as desktop are observed.

Observation / evidence: `<fill>`  
Reviewer initials: `<fill>`

## Permission Negative Paths

- [ ] Anonymous request to a protected snapshot is rejected.
- [ ] A valid session with an out-of-scope topic cannot read or mutate that topic.
- [ ] Simulated or unregistered write actions are rejected with no state change.
- [ ] Logout removes access; returning to a protected view requires invitation/session recovery.

Observation / evidence: `<fill>`  
Reviewer initials: `<fill>`

## Complete Operator Flow

- [ ] Redeem invitation.
- [ ] Inspect the current runtime snapshot and provenance.
- [ ] Navigate to the permitted view and perform only an allowed action.
- [ ] Observe live update or reconnect from the server cursor.
- [ ] Confirm the final status, generation, and boundary indicators.
- [ ] Logout and confirm the protected view is no longer accessible.

Observation / evidence: `<fill>`  
Reviewer initials: `<fill>`

## Human Sign-off

Result: `[ ] ACCEPTED  [ ] REJECTED  [ ] PARTIAL`  
Open defects / follow-up: `<fill>`  
Reviewer name and role: `<fill>`  
Signature: `<fill>`  
Signed at (Asia/Shanghai): `<fill>`

