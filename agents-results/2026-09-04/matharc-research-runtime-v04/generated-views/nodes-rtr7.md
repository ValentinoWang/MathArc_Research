### Release RTR7 node contract summary

- Title: RT-R7 真实任务与试点
- User value: 真实两代研究和邀请制试点具备可复核发布证据。
- Independent failure: 任一错误晋升、越权动作或不可重放结果阻断试点发布。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| DOG1 | requirement.dog1 | implementation | implementation | reversible | F; DP1; RUN5 | none | decision.matharc-native-runtime@1 | nodes/DOG1.json | acceptance-fragments/DOG1/acceptance-contract.md |
| DOG2 | requirement.dog2 | implementation | implementation | reversible | F; DP1; PAR5; SYN5; VER6; DOG1 | none | decision.matharc-native-runtime@1 | nodes/DOG2.json | acceptance-fragments/DOG2/acceptance-contract.md |
| DOG3 | requirement.dog3 | implementation | implementation | reversible | F; DP1; DOG2; DUR5; UX6 | none | decision.matharc-native-runtime@1 | nodes/DOG3.json | acceptance-fragments/DOG3/acceptance-contract.md |
| DOG4 | requirement.dog4 | implementation | implementation | reversible | F; DP1; DOG3 | none | decision.matharc-native-runtime@1 | nodes/DOG4.json | acceptance-fragments/DOG4/acceptance-contract.md |
| QRTR7 | acceptance.release.rtr7 | release-decision | shared-generated | none | DOG1; DOG2; DOG3; DOG4 | none | none | nodes/QRTR7.json | none |

### Release RTR7 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| DOG1 | RTR7 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DOG1/acceptance-contract.md | DOG2; QRTR7 |
| DOG2 | RTR7 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DOG2/acceptance-contract.md | DOG3; QRTR7 |
| DOG3 | RTR7 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DOG3/acceptance-contract.md | DOG4; QRTR7 |
| DOG4 | RTR7 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DOG4/acceptance-contract.md | QRTR7 |
| QRTR7 | RTR7 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR7 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
