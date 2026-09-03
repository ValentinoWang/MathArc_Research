### Release R1 node contract summary

- Title: 声明、状态与推送闭环
- User value: SSOT 输入、执行完成证据、状态迁移和推送资格使用同一套可验证事实，不再接受仅靠声明的完成或过期验证报告。
- Independent failure: 任一负例未被封闭拒绝时，本切片保持未接受，不允许进入 GitHub 主线。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| DP1 | decision.execution-plane.scope | decision-acceptance | isolated-record | none | none | none | none | nodes/DP1.json | none |
| C1 | requirement.c1 | implementation | implementation | reversible | DP1 | none | decision.execution-plane.scope@1 | nodes/C1.json | acceptance-fragments/C1/acceptance-contract.md |
| P1 | requirement.p1 | implementation | implementation | reversible | DP1; C1 | none | decision.execution-plane.scope@1 | nodes/P1.json | acceptance-fragments/P1/acceptance-contract.md |
| S1 | requirement.s1 | implementation | implementation | reversible | DP1; C1 | none | decision.execution-plane.scope@1 | nodes/S1.json | acceptance-fragments/S1/acceptance-contract.md |
| QR1 | acceptance.release.r1 | release-decision | shared-generated | none | C1; S1; P1 | none | none | nodes/QR1.json | none |

### Release R1 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| DP1 | R1 | none | ACCEPTED | none | decision owner | none | none | none | C1; E1; P1; RI1; S1; V1 |
| C1 | R1 | decision.execution-plane.scope@1 | ACCEPTED | none | acceptance owner | none | none | acceptance-fragments/C1/acceptance-contract.md | E1; P1; QR1; S1 |
| P1 | R1 | decision.execution-plane.scope@1 | ACCEPTED | none | acceptance owner | none | none | acceptance-fragments/P1/acceptance-contract.md | QR1; RI1 |
| S1 | R1 | decision.execution-plane.scope@1 | ACCEPTED | none | acceptance owner | none | none | acceptance-fragments/S1/acceptance-contract.md | QR1; RI1 |
| QR1 | R1 | none | READY | none | release decision owner | none | none | none | none |

### Release R1 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
