# Production Attack Drills

State: `NOT RUN`

This is an operator checklist, not evidence that a production drill occurred. Run only against an explicitly approved isolated target and retain raw output outside this template.

| Drill | Expected fail-closed behavior | Evidence path | Result |
| --- | --- | --- | --- |
| Cross-run or cross-generation identity | Reject the request/result; no state mutation | `<path>` | `PENDING` |
| Conflicting duplicate execution | Reject the conflicting payload; preserve first receipt | `<path>` | `PENDING` |
| Event-log or snapshot tampering | Refuse startup/recovery with a digest error | `<path>` | `PENDING` |
| Late result after close | Quarantine as late; do not rewrite the commit | `<path>` | `PENDING` |
| Forbidden process input | Reject command/cwd/env/executable fields | `<path>` | `PENDING` |
| Recovery input drift | Refuse recovery until the frozen snapshot is restored | `<path>` | `PENDING` |

No production host, customer data, operator approval, or human signature is implied by `PENDING`.
