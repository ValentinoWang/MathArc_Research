### Release RTR5 node contract summary

- Title: RT-R5 数学验证汇合
- User value: 候选结果可以经过独立验证后受控转换为正式证据。
- Independent failure: 运行成功、模型自报或篡改候选都不能成为证明。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| VER1 | requirement.ver1 | implementation | implementation | reversible | F; DP1; RUN1; DUR2 | none | decision.matharc-native-runtime@1 | nodes/VER1.json | acceptance-fragments/VER1/acceptance-contract.md |
| VER2 | requirement.ver2 | implementation | implementation | reversible | F; DP1; VER1 | none | decision.matharc-native-runtime@1 | nodes/VER2.json | acceptance-fragments/VER2/acceptance-contract.md |
| VER3 | requirement.ver3 | implementation | implementation | reversible | F; DP1; VER2 | none | decision.matharc-native-runtime@1 | nodes/VER3.json | acceptance-fragments/VER3/acceptance-contract.md |
| VER4 | requirement.ver4 | implementation | implementation | reversible | F; DP1; VER3 | none | decision.matharc-native-runtime@1 | nodes/VER4.json | acceptance-fragments/VER4/acceptance-contract.md |
| VER5 | requirement.ver5 | implementation | implementation | reversible | F; DP1; VER4 | none | decision.matharc-native-runtime@1 | nodes/VER5.json | acceptance-fragments/VER5/acceptance-contract.md |
| VER6 | requirement.ver6 | implementation | implementation | reversible | F; DP1; VER5 | none | decision.matharc-native-runtime@1 | nodes/VER6.json | acceptance-fragments/VER6/acceptance-contract.md |
| QRTR5 | acceptance.release.rtr5 | release-decision | shared-generated | none | VER1; VER2; VER3; VER4; VER5; VER6 | none | none | nodes/QRTR5.json | none |

### Release RTR5 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| VER1 | RTR5 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/VER1/acceptance-contract.md | QRTR5; VER2 |
| VER2 | RTR5 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/VER2/acceptance-contract.md | QRTR5; VER3 |
| VER3 | RTR5 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/VER3/acceptance-contract.md | QRTR5; VER4 |
| VER4 | RTR5 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/VER4/acceptance-contract.md | QRTR5; VER5 |
| VER5 | RTR5 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/VER5/acceptance-contract.md | QRTR5; VER6 |
| VER6 | RTR5 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/VER6/acceptance-contract.md | DOG2; QRTR5; UX5 |
| QRTR5 | RTR5 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR5 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
