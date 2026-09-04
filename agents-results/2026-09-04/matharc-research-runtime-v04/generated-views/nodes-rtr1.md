### Release RTR1 node contract summary

- Title: RT-R1 单任务运行闭环
- User value: 一个数学任务可以从验证、运行到候选回传形成闭环。
- Independent failure: 单任务失败不改变数学工作区，也不产生正式证据。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| RUN1 | requirement.run1 | implementation | implementation | reversible | F; DP1; FND3 | none | decision.matharc-native-runtime@1 | nodes/RUN1.json | acceptance-fragments/RUN1/acceptance-contract.md |
| RUN2 | requirement.run2 | implementation | implementation | reversible | F; DP1; RUN1 | none | decision.matharc-native-runtime@1 | nodes/RUN2.json | acceptance-fragments/RUN2/acceptance-contract.md |
| RUN3 | requirement.run3 | implementation | implementation | reversible | F; DP1; RUN1 | none | decision.matharc-native-runtime@1 | nodes/RUN3.json | acceptance-fragments/RUN3/acceptance-contract.md |
| RUN4 | requirement.run4 | implementation | implementation | reversible | F; DP1; RUN2; RUN3 | none | decision.matharc-native-runtime@1 | nodes/RUN4.json | acceptance-fragments/RUN4/acceptance-contract.md |
| RUN5 | requirement.run5 | implementation | implementation | reversible | F; DP1; RUN4 | none | decision.matharc-native-runtime@1 | nodes/RUN5.json | acceptance-fragments/RUN5/acceptance-contract.md |
| QRTR1 | acceptance.release.rtr1 | release-decision | shared-generated | none | RUN1; RUN2; RUN3; RUN4; RUN5 | none | none | nodes/QRTR1.json | none |

### Release RTR1 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| RUN1 | RTR1 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/RUN1/acceptance-contract.md | PAR1; QRTR1; RUN2; RUN3; VER1 |
| RUN2 | RTR1 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/RUN2/acceptance-contract.md | DUR1; QRTR1; RUN4 |
| RUN3 | RTR1 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/RUN3/acceptance-contract.md | QRTR1; RUN4 |
| RUN4 | RTR1 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/RUN4/acceptance-contract.md | PAR2; QRTR1; RUN5 |
| RUN5 | RTR1 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/RUN5/acceptance-contract.md | DOG1; QRTR1; SYN1 |
| QRTR1 | RTR1 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR1 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
