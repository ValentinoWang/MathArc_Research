### Release RTR2 node contract summary

- Title: RT-R2 多研究成员并行
- User value: 不同研究路线可以在隔离工作区中真实并行执行。
- Independent failure: 单成员失败不破坏整轮，且不得伪造并行证据。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| PAR1 | requirement.par1 | implementation | implementation | reversible | F; DP1; RUN1 | none | decision.matharc-native-runtime@1 | nodes/PAR1.json | acceptance-fragments/PAR1/acceptance-contract.md |
| PAR2 | requirement.par2 | implementation | implementation | reversible | F; DP1; PAR1; RUN4 | none | decision.matharc-native-runtime@1 | nodes/PAR2.json | acceptance-fragments/PAR2/acceptance-contract.md |
| PAR3 | requirement.par3 | implementation | implementation | reversible | F; DP1; PAR2 | none | decision.matharc-native-runtime@1 | nodes/PAR3.json | acceptance-fragments/PAR3/acceptance-contract.md |
| PAR4 | requirement.par4 | implementation | implementation | reversible | F; DP1; PAR3 | none | decision.matharc-native-runtime@1 | nodes/PAR4.json | acceptance-fragments/PAR4/acceptance-contract.md |
| PAR5 | requirement.par5 | implementation | implementation | reversible | F; DP1; PAR4 | none | decision.matharc-native-runtime@1 | nodes/PAR5.json | acceptance-fragments/PAR5/acceptance-contract.md |
| QRTR2 | acceptance.release.rtr2 | release-decision | shared-generated | none | PAR1; PAR2; PAR3; PAR4; PAR5 | none | none | nodes/QRTR2.json | none |

### Release RTR2 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| PAR1 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/PAR1/acceptance-contract.md | PAR2; QRTR2 |
| PAR2 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/PAR2/acceptance-contract.md | PAR3; QRTR2 |
| PAR3 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/PAR3/acceptance-contract.md | PAR4; QRTR2 |
| PAR4 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/PAR4/acceptance-contract.md | PAR5; QRTR2 |
| PAR5 | RTR2 | decision.matharc-native-runtime@1 | PLANNED | none | acceptance owner | none | none | acceptance-fragments/PAR5/acceptance-contract.md | DOG2; DUR1; QRTR2 |
| QRTR2 | RTR2 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR2 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
