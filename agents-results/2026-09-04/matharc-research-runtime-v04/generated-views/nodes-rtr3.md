### Release RTR3 node contract summary

- Title: RT-R3 多研究成员并行
- User value: 不同研究路线可以在隔离工作区中真实并行执行。
- Independent failure: 单成员失败不破坏整轮，且不得伪造并行证据。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| PAR1 | requirement.par1 | implementation | implementation | reversible | F; DP1; RUN1 | none | decision.matharc-native-runtime@1 | nodes/PAR1.json | acceptance-fragments/PAR1/acceptance-contract.md |
| PAR2 | requirement.par2 | implementation | implementation | reversible | F; DP1; PAR1; RUN4 | none | decision.matharc-native-runtime@1 | nodes/PAR2.json | acceptance-fragments/PAR2/acceptance-contract.md |
| PAR3 | requirement.par3 | implementation | implementation | reversible | F; DP1; PAR2; DUR5 | none | decision.matharc-native-runtime@1 | nodes/PAR3.json | acceptance-fragments/PAR3/acceptance-contract.md |
| PAR4 | requirement.par4 | implementation | implementation | reversible | F; DP1; PAR3 | none | decision.matharc-native-runtime@1 | nodes/PAR4.json | acceptance-fragments/PAR4/acceptance-contract.md |
| PAR5 | requirement.par5 | validation | implementation | reversible | F; DP1; PAR4 | none | decision.matharc-native-runtime@1 | nodes/PAR5.json | acceptance-fragments/PAR5/acceptance-contract.md |
| Q3 | acceptance.release.rtr3 | release-decision | shared-generated | none | PAR1; PAR2; PAR3; PAR4; PAR5 | none | none | nodes/Q3.json | none |

### Release RTR3 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| PAR1 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | principal:acceptance-a | none | none | acceptance-fragments/PAR1/acceptance-contract.md | PAR2; Q3 |
| PAR2 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | principal:acceptance-a | none | none | acceptance-fragments/PAR2/acceptance-contract.md | PAR3; Q3 |
| PAR3 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | principal:acceptance-a | none | none | acceptance-fragments/PAR3/acceptance-contract.md | PAR4; Q3 |
| PAR4 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | principal:acceptance-a | none | none | acceptance-fragments/PAR4/acceptance-contract.md | PAR5; Q3 |
| PAR5 | RTR3 | decision.matharc-native-runtime@1 | PLANNED | none | principal:acceptance-a | none | none | acceptance-fragments/PAR5/acceptance-contract.md | DOG2; Q3; SYN5 |
| Q3 | RTR3 | none | PLANNED | none | principal:release-a | none | none | none | none |

### Release RTR3 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
