### Release RTR3 node contract summary

- Title: RT-R3 持久化与恢复
- User value: 中断后可以从明确的代际边界继续运行。
- Independent failure: 不确定状态不得猜测完成、重复计费或跳过代际。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| DUR1 | requirement.dur1 | implementation | implementation | reversible | F; DP1; PAR5; RUN2 | none | decision.matharc-native-runtime@1 | nodes/DUR1.json | acceptance-fragments/DUR1/acceptance-contract.md |
| DUR2 | requirement.dur2 | implementation | implementation | reversible | F; DP1; DUR1 | none | decision.matharc-native-runtime@1 | nodes/DUR2.json | acceptance-fragments/DUR2/acceptance-contract.md |
| DUR3 | requirement.dur3 | implementation | implementation | reversible | F; DP1; DUR1 | none | decision.matharc-native-runtime@1 | nodes/DUR3.json | acceptance-fragments/DUR3/acceptance-contract.md |
| DUR4 | requirement.dur4 | implementation | implementation | reversible | F; DP1; DUR2; DUR3 | none | decision.matharc-native-runtime@1 | nodes/DUR4.json | acceptance-fragments/DUR4/acceptance-contract.md |
| DUR5 | requirement.dur5 | implementation | implementation | reversible | F; DP1; DUR4 | none | decision.matharc-native-runtime@1 | nodes/DUR5.json | acceptance-fragments/DUR5/acceptance-contract.md |
| QRTR3 | acceptance.release.rtr3 | release-decision | shared-generated | none | DUR1; DUR2; DUR3; DUR4; DUR5 | none | none | nodes/QRTR3.json | none |

### Release RTR3 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| DUR1 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DUR1/acceptance-contract.md | DUR2; DUR3; QRTR3 |
| DUR2 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DUR2/acceptance-contract.md | DUR4; QRTR3; SYN1; UX1; VER1 |
| DUR3 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DUR3/acceptance-contract.md | DUR4; QRTR3 |
| DUR4 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DUR4/acceptance-contract.md | DUR5; QRTR3 |
| DUR5 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/DUR5/acceptance-contract.md | DOG3; QRTR3; SYN5; UX3 |
| QRTR3 | RTR3 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR3 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
