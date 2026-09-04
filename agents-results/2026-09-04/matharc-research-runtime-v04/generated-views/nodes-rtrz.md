### Release RTRZ node contract summary

- Title: RT-R0 原生运行时章程
- User value: MathArc 自己拥有执行权威、数据合同和运行边界。
- Independent failure: 不启动真实研究；后续运行时切片保持未接受。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| F | source.identity-baseline | contract-foundation | evidence-only | none | none | none | none | nodes/F.json | none |
| DP1 | decision.matharc-native-runtime | decision-acceptance | isolated-record | none | F | none | none | nodes/DP1.json | none |
| DP2 | decision.matharc-backend-scope | decision-acceptance | isolated-record | none | F | none | none | nodes/DP2.json | none |
| DP3 | decision.matharc-pilot-deployment | decision-acceptance | isolated-record | none | F | none | none | nodes/DP3.json | none |
| FND1 | requirement.fnd1 | implementation | implementation | reversible | F; DP1 | none | decision.matharc-native-runtime@1 | nodes/FND1.json | acceptance-fragments/FND1/acceptance-contract.md |
| FND2 | requirement.fnd2 | implementation | implementation | reversible | F; DP1; FND1 | none | decision.matharc-native-runtime@1 | nodes/FND2.json | acceptance-fragments/FND2/acceptance-contract.md |
| QZ | acceptance.release.rtrz | release-decision | shared-generated | none | FND1; FND2 | none | none | nodes/QZ.json | none |

### Release RTRZ status ledger

| Task ID | Stage | Versions | Execution state | Attempt | Execution owner | Acceptance mode | Acceptance authorities | Quorum | Minimum trust | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F | RTRZ | none | ACCEPTED | none | 编排器 | none | none | none | none | none | none | none | DOG1; DOG2; DOG3; DOG4; DP1; DP2; DP3; DUR1; DUR2; DUR3; DUR4; DUR5; FND1; FND2; OPS1; OPS2; OPS3; PAR1; PAR2; PAR3; PAR4; PAR5; RUN1; RUN2; RUN3; RUN4; RUN5; SYN1; SYN2; SYN3; SYN4; SYN5; UX1; UX2; UX3; UX4; UX5; UX6; VER1; VER2; VER3; VER4; VER5; VER6 |
| DP1 | RTRZ | none | ACCEPTED | none | 决策负责人 | none | none | none | none | none | none | none | DOG1; DOG2; DOG3; DOG4; DUR1; DUR2; DUR3; DUR4; DUR5; FND1; FND2; OPS1; OPS2; OPS3; PAR1; PAR2; PAR3; PAR4; PAR5; RUN1; RUN2; RUN3; RUN4; RUN5; SYN1; SYN2; SYN3; SYN4; SYN5; UX1; UX2; UX3; UX4; UX5; UX6; VER1; VER2; VER3; VER4; VER5; VER6 |
| DP2 | RTRZ | none | ACCEPTED | none | 决策负责人 | none | none | none | none | none | none | none | RUN4 |
| DP3 | RTRZ | none | ACCEPTED | none | 决策负责人 | none | none | none | none | none | none | none | OPS1; OPS2; OPS3 |
| FND1 | RTRZ | decision.matharc-native-runtime@1 | PLANNED | none | principal:owner-fnd1 | dual | acceptance-a:principal:acceptance-a; acceptance-b:principal:acceptance-b | 2 | repository-bound | none | none | acceptance-fragments/FND1/acceptance-contract.md | FND2; QZ |
| FND2 | RTRZ | decision.matharc-native-runtime@1 | PLANNED | none | principal:owner-fnd2 | dual | acceptance-a:principal:acceptance-a; acceptance-b:principal:acceptance-b | 2 | repository-bound | none | none | acceptance-fragments/FND2/acceptance-contract.md | QZ; RUN1; UX2 |
| QZ | RTRZ | none | PLANNED | none | 发布决策负责人 | dual | release-acceptance-a:principal:release-a; release-acceptance-b:principal:release-b | 2 | repository-bound | none | none | none | none |

### Release RTRZ deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
