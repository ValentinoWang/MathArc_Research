### Release RTR6 node contract summary

- Title: RT-R6 邀请制产品与试点运行环境
- User value: 受邀用户可以在有持久运维保障的环境中查看并受控操作研究运行。
- Independent failure: 浏览器不能执行任意命令、目录、环境变量或未登记后端；运维缺口阻断试点。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| UX1 | requirement.ux1 | implementation | implementation | reversible | F; DP1; S29; S49; DUR2 | none | decision.matharc-native-runtime@1 | nodes/UX1.json | acceptance-fragments/UX1/acceptance-contract.md |
| UX2 | requirement.ux2 | implementation | implementation | reversible | F; DP1; S24; S48; FND2 | none | decision.matharc-native-runtime@1 | nodes/UX2.json | acceptance-fragments/UX2/acceptance-contract.md |
| UX3 | requirement.ux3 | implementation | implementation | reversible | F; DP1; S24; S46; UX2; DUR5 | none | decision.matharc-native-runtime@1 | nodes/UX3.json | acceptance-fragments/UX3/acceptance-contract.md |
| UX4 | requirement.ux4 | implementation | implementation | reversible | F; DP1; S29; S51; UX1; UX2 | none | decision.matharc-native-runtime@1 | nodes/UX4.json | acceptance-fragments/UX4/acceptance-contract.md |
| UX5 | requirement.ux5 | implementation | implementation | reversible | F; DP1; S24; S29; S50; UX3; UX4; VER6 | none | decision.matharc-native-runtime@1 | nodes/UX5.json | acceptance-fragments/UX5/acceptance-contract.md |
| UX6 | requirement.ux6 | validation | implementation | reversible | F; DP1; S1; S47; UX5 | none | decision.matharc-native-runtime@1 | nodes/UX6.json | acceptance-fragments/UX6/acceptance-contract.md |
| OPS1 | requirement.ops1 | implementation | implementation | reversible | F; DP1; S6; S7; S67; UX6 | none | decision.matharc-native-runtime@1 | nodes/OPS1.json | acceptance-fragments/OPS1/acceptance-contract.md |
| OPS2 | requirement.ops2 | validation | implementation | reversible | F; DP1; S65; S68; OPS1 | none | decision.matharc-native-runtime@1 | nodes/OPS2.json | acceptance-fragments/OPS2/acceptance-contract.md |
| OPS3 | requirement.ops3 | validation | implementation | reversible | F; DP1; S3; S66; S69; OPS2 | none | decision.matharc-native-runtime@1 | nodes/OPS3.json | acceptance-fragments/OPS3/acceptance-contract.md |
| QRTR6 | acceptance.release.rtr6 | release-decision | shared-generated | none | UX1; UX2; UX3; UX4; UX5; UX6; OPS1; OPS2; OPS3 | none | none | nodes/QRTR6.json | none |

### Release RTR6 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| UX1 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 控制台投影负责人 | none | none | acceptance-fragments/UX1/acceptance-contract.md | QRTR6; UX4 |
| UX2 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 邀请权限负责人 | none | none | acceptance-fragments/UX2/acceptance-contract.md | QRTR6; UX3; UX4 |
| UX3 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 运行动作 API 负责人 | none | none | acceptance-fragments/UX3/acceptance-contract.md | QRTR6; UX5 |
| UX4 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 控制台安全视图负责人 | none | none | acceptance-fragments/UX4/acceptance-contract.md | QRTR6; UX5 |
| UX5 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 实时控制台负责人 | none | none | acceptance-fragments/UX5/acceptance-contract.md | QRTR6; UX6 |
| UX6 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 浏览器产品验收负责人 | none | none | acceptance-fragments/UX6/acceptance-contract.md | DOG3; OPS1; QRTR6 |
| OPS1 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 试点部署负责人 | none | none | acceptance-fragments/OPS1/acceptance-contract.md | OPS2; QRTR6 |
| OPS2 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 试点运维观测负责人 | none | none | acceptance-fragments/OPS2/acceptance-contract.md | OPS3; QRTR6 |
| OPS3 | RTR6 | decision.matharc-native-runtime@1 | PLANNED | none | 试点发布运维负责人 | none | none | acceptance-fragments/OPS3/acceptance-contract.md | DOG2; QRTR6 |
| QRTR6 | RTR6 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR6 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
