### Release RTR4 node contract summary

- Title: RT-R4 代际学习
- User value: 上一代的失败和研究经历可以改变下一代议程。
- Independent failure: 蒸馏失败或缺少出处时，下一代保持未启动。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| SYN1 | requirement.syn1 | implementation | implementation | reversible | F; DP1; S14; S26; S45; RUN5; DUR2 | none | decision.matharc-native-runtime@1 | nodes/SYN1.json | acceptance-fragments/SYN1/acceptance-contract.md |
| SYN2 | requirement.syn2 | implementation | implementation | reversible | F; DP1; S26; S53; SYN1 | none | decision.matharc-native-runtime@1 | nodes/SYN2.json | acceptance-fragments/SYN2/acceptance-contract.md |
| SYN3 | requirement.syn3 | implementation | implementation | reversible | F; DP1; S21; S62; SYN1 | none | decision.matharc-native-runtime@1 | nodes/SYN3.json | acceptance-fragments/SYN3/acceptance-contract.md |
| SYN4 | requirement.syn4 | implementation | implementation | reversible | F; DP1; S18; S63; SYN2; SYN3 | none | decision.matharc-native-runtime@1 | nodes/SYN4.json | acceptance-fragments/SYN4/acceptance-contract.md |
| SYN5 | requirement.syn5 | validation | implementation | reversible | F; DP1; S57; S81; SYN4; DUR5; PAR5 | none | decision.matharc-native-runtime@1 | nodes/SYN5.json | acceptance-fragments/SYN5/acceptance-contract.md |
| QRTR4 | acceptance.release.rtr4 | release-decision | shared-generated | none | SYN1; SYN2; SYN3; SYN4; SYN5 | none | none | nodes/QRTR4.json | none |

### Release RTR4 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| SYN1 | RTR4 | decision.matharc-native-runtime@1 | PLANNED | none | 探索结果接线负责人 | none | none | acceptance-fragments/SYN1/acceptance-contract.md | QRTR4; SYN2; SYN3 |
| SYN2 | RTR4 | decision.matharc-native-runtime@1 | PLANNED | none | 反例复核负责人 | none | none | acceptance-fragments/SYN2/acceptance-contract.md | QRTR4; SYN4 |
| SYN3 | RTR4 | decision.matharc-native-runtime@1 | PLANNED | none | 研究记忆负责人 | none | none | acceptance-fragments/SYN3/acceptance-contract.md | QRTR4; SYN4 |
| SYN4 | RTR4 | decision.matharc-native-runtime@1 | PLANNED | none | 代际议程负责人 | none | none | acceptance-fragments/SYN4/acceptance-contract.md | QRTR4; SYN5 |
| SYN5 | RTR4 | decision.matharc-native-runtime@1 | PLANNED | none | 连续代际验收负责人 | none | none | acceptance-fragments/SYN5/acceptance-contract.md | DOG2; QRTR4 |
| QRTR4 | RTR4 | none | PLANNED | none | release decision owner | none | none | none | none |

### Release RTR4 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
