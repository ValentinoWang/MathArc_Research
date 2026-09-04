### Release RTR6 node contract summary

- Title: RT-R6 邀请制控制台
- User value: 受邀用户可以查看并受控操作研究运行。
- Independent failure: 浏览器不能执行任意命令、目录、环境变量或未登记后端。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| UX1 | requirement.ux1 | implementation | implementation | reversible | F; DP1; DUR2 | none | decision.matharc-native-runtime@1 | nodes/UX1.json | acceptance-fragments/UX1/acceptance-contract.md |
| UX2 | requirement.ux2 | implementation | implementation | reversible | F; DP1; FND2 | none | decision.matharc-native-runtime@1 | nodes/UX2.json | acceptance-fragments/UX2/acceptance-contract.md |
| UX3 | requirement.ux3 | implementation | implementation | reversible | F; DP1; UX2; DUR5 | none | decision.matharc-native-runtime@1 | nodes/UX3.json | acceptance-fragments/UX3/acceptance-contract.md |
| UX4 | requirement.ux4 | implementation | implementation | reversible | F; DP1; UX1; UX2 | none | decision.matharc-native-runtime@1 | nodes/UX4.json | acceptance-fragments/UX4/acceptance-contract.md |
| UX5 | requirement.ux5 | implementation | implementation | reversible | F; DP1; UX3; UX4; VER6 | none | decision.matharc-native-runtime@1 | nodes/UX5.json | acceptance-fragments/UX5/acceptance-contract.md |
| UX6 | requirement.ux6 | implementation | implementation | reversible | F; DP1; UX5 | none | decision.matharc-native-runtime@1 | nodes/UX6.json | acceptance-fragments/UX6/acceptance-contract.md |
| QRTR6 | acceptance.release.rtr6 | release-decision | shared-generated | none | UX1; UX2; UX3; UX4; UX5; UX6 | none | none | nodes/QRTR6.json | none |

### Release RTR6 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| UX1 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/UX1/acceptance-contract.md | QRTR6; UX4 |
| UX2 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/UX2/acceptance-contract.md | QRTR6; UX3; UX4 |
| UX3 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/UX3/acceptance-contract.md | QRTR6; UX5 |
| UX4 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/UX4/acceptance-contract.md | QRTR6; UX5 |
| UX5 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/UX5/acceptance-contract.md | QRTR6; UX6 |
| UX6 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/UX6/acceptance-contract.md | DOG3; QRTR6 |
| QRTR6 | RTR6 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR6 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
