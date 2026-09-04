### Release RTR2 node contract summary

- Title: RT-R2 持久化、生命周期与恢复
- User value: 单任务运行可以可靠保存、停止、恢复和幂等导入。
- Independent failure: 不确定状态不得猜测完成、重复计费或跳过代际。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| DUR1 | requirement.dur1 | implementation | implementation | reversible | F; DP1; RUN5 | none | decision.matharc-native-runtime@1 | nodes/DUR1.json | acceptance-fragments/DUR1/acceptance-contract.md |
| DUR2 | requirement.dur2 | implementation | implementation | reversible | F; DP1; DUR1 | none | decision.matharc-native-runtime@1 | nodes/DUR2.json | acceptance-fragments/DUR2/acceptance-contract.md |
| DUR3 | requirement.dur3 | implementation | implementation | reversible | F; DP1; DUR1 | none | decision.matharc-native-runtime@1 | nodes/DUR3.json | acceptance-fragments/DUR3/acceptance-contract.md |
| DUR4 | requirement.dur4 | implementation | implementation | reversible | F; DP1; DUR2; DUR3 | none | decision.matharc-native-runtime@1 | nodes/DUR4.json | acceptance-fragments/DUR4/acceptance-contract.md |
| DUR5 | requirement.dur5 | validation | implementation | reversible | F; DP1; DUR4 | none | decision.matharc-native-runtime@1 | nodes/DUR5.json | acceptance-fragments/DUR5/acceptance-contract.md |
| Q2 | acceptance.release.rtr2 | release-decision | shared-generated | none | DUR1; DUR2; DUR3; DUR4; DUR5 | none | none | nodes/Q2.json | none |

### Release RTR2 status ledger

| Task ID | Stage | Versions | Execution state | Attempt | Execution owner | Acceptance mode | Acceptance authorities | Quorum | Minimum trust | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DUR1 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | principal:owner-dur1 | dual | acceptance-a:principal:acceptance-a; acceptance-b:principal:acceptance-b | 2 | repository-bound | none | none | acceptance-fragments/DUR1/acceptance-contract.md | DUR2; DUR3; Q2 |
| DUR2 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | principal:owner-dur2 | dual | acceptance-a:principal:acceptance-a; acceptance-b:principal:acceptance-b | 2 | repository-bound | none | none | acceptance-fragments/DUR2/acceptance-contract.md | DUR4; Q2; SYN1; UX1; VER1 |
| DUR3 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | principal:owner-dur3 | dual | acceptance-a:principal:acceptance-a; acceptance-b:principal:acceptance-b | 2 | repository-bound | none | none | acceptance-fragments/DUR3/acceptance-contract.md | DUR4; Q2 |
| DUR4 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | principal:owner-dur4 | dual | acceptance-a:principal:acceptance-a; acceptance-b:principal:acceptance-b | 2 | repository-bound | none | none | acceptance-fragments/DUR4/acceptance-contract.md | DUR5; Q2 |
| DUR5 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | principal:owner-dur5 | dual | acceptance-a:principal:acceptance-a; acceptance-b:principal:acceptance-b | 2 | repository-bound | none | none | acceptance-fragments/DUR5/acceptance-contract.md | DOG3; PAR3; Q2; SYN5; UX3 |
| Q2 | RTR2 | none | PLANNED | none | 发布决策负责人 | dual | release-acceptance-a:principal:release-a; release-acceptance-b:principal:release-b | 2 | repository-bound | none | none | none | none |

### Release RTR2 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
