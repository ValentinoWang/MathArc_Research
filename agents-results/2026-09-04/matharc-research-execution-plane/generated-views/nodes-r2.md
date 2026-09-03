### Release R2 node contract summary

- Title: 规则守恒与比例治理闭环
- User value: 维护者只读取当前任务触发的规范，规则索引和实际产物双向守恒，证据 lane 与事实登记不再产生不可采集或仪式性内容。
- Independent failure: 任一规则、视图、采集器或事实类别无法从真实文件反查时，本切片保持未接受且不影响 R1 的已验证能力。

| Task ID | Semantic key | Work kind | Write authority | Side effect class | Hard dependencies | Soft dependencies | Decision refs | Execution contract ref | Acceptance contract ref |
|---|---|---|---|---|---|---|---|---|---|
| E1 | requirement.e1 | implementation | implementation | reversible | DP1; C1 | none | decision.execution-plane.scope@1 | nodes/E1.json | acceptance-fragments/E1/acceptance-contract.md |
| RI1 | requirement.ri1 | implementation | implementation | reversible | DP1; S1; P1 | none | decision.execution-plane.scope@1 | nodes/RI1.json | acceptance-fragments/RI1/acceptance-contract.md |
| V1 | requirement.v1 | validation | implementation | reversible | DP1; RI1; E1 | none | decision.execution-plane.scope@1 | nodes/V1.json | acceptance-fragments/V1/acceptance-contract.md |
| QR2 | acceptance.release.r2 | release-decision | shared-generated | none | RI1; E1; V1 | none | none | nodes/QR2.json | none |

### Release R2 status ledger

| Task ID | Stage | Versions | State | Attempt | Owner | Guard ID | Blocking reason | Evidence | Unlocks |
|---|---|---|---|---|---|---|---|---|---|
| E1 | R2 | decision.execution-plane.scope@1 | ACCEPTED | none | acceptance owner | none | none | acceptance-fragments/E1/acceptance-contract.md | QR2; V1 |
| RI1 | R2 | decision.execution-plane.scope@1 | ACCEPTED | none | acceptance owner | none | none | acceptance-fragments/RI1/acceptance-contract.md | QR2; V1 |
| V1 | R2 | decision.execution-plane.scope@1 | ACCEPTED | none | acceptance owner | none | none | acceptance-fragments/V1/acceptance-contract.md | QR2 |
| QR2 | R2 | none | READY | none | release decision owner | none | none | none | none |

### Release R2 deliverables

| Deliverable ID | Owning node |
|---|---|
| none | none |
