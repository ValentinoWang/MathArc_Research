### Release RTR2 node contract summary

- Title: RT-R2 持久化、生命周期与恢复
- User value: 单任务运行可以可靠保存、停止、恢复和幂等导入。
- Independent failure: 不确定状态不得猜测完成、重复计费或跳过代际。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| DUR1 | requirement.dur1 | implementation | implementation | reversible | F; DP1; S18; S21; S38; S39; RUN5 | none | decision.matharc-native-runtime@1 | nodes/DUR1.json | acceptance-fragments/DUR1/acceptance-contract.md |
| DUR2 | requirement.dur2 | implementation | implementation | reversible | F; DP1; S14; S22; S58; DUR1 | none | decision.matharc-native-runtime@1 | nodes/DUR2.json | acceptance-fragments/DUR2/acceptance-contract.md |
| DUR3 | requirement.dur3 | implementation | implementation | reversible | F; DP1; S25; S61; DUR1 | none | decision.matharc-native-runtime@1 | nodes/DUR3.json | acceptance-fragments/DUR3/acceptance-contract.md |
| DUR4 | requirement.dur4 | implementation | implementation | reversible | F; DP1; S20; S76; DUR2; DUR3 | none | decision.matharc-native-runtime@1 | nodes/DUR4.json | acceptance-fragments/DUR4/acceptance-contract.md |
| DUR5 | requirement.dur5 | validation | implementation | reversible | F; DP1; S54; S64; DUR4 | none | decision.matharc-native-runtime@1 | nodes/DUR5.json | acceptance-fragments/DUR5/acceptance-contract.md |
| QRTR2 | acceptance.release.rtr2 | release-decision | shared-generated | none | DUR1; DUR2; DUR3; DUR4; DUR5 | none | none | nodes/QRTR2.json | none |

### Release RTR2 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| DUR1 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | 代际提交负责人 | none | none | acceptance-fragments/DUR1/acceptance-contract.md | DUR2; DUR3; QRTR2 |
| DUR2 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | 幂等账本负责人 | none | none | acceptance-fragments/DUR2/acceptance-contract.md | DUR4; QRTR2; SYN1; UX1; VER1 |
| DUR3 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | 运行控制负责人 | none | none | acceptance-fragments/DUR3/acceptance-contract.md | DUR4; QRTR2 |
| DUR4 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | 恢复负责人 | none | none | acceptance-fragments/DUR4/acceptance-contract.md | DUR5; QRTR2 |
| DUR5 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | 恢复验收负责人 | none | none | acceptance-fragments/DUR5/acceptance-contract.md | DOG3; PAR3; QRTR2; SYN5; UX3 |
| QRTR2 | RTR2 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR2 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
