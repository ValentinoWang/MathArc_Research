# Acceptance Run: 20260901T102745Z-local-r1a002

- Run ID: 20260901T102745Z-local-r1a002
- Task ID: R1-regression-evaluation
- Lane: human
- Status: PASS
- Acceptance contract: agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/acceptance-contract.md
- Contract version: 9
- Contract SHA-256: 6faa8116278e8fe64d26f39bfcd0277d6dfac74fea0aa74a11aacb8046fd85ee
- Human acceptance binding: acceptance/human/R1-regression-evaluation/binding.md
- Binding SHA-256: ec6336739a676253620abeb24c0df22fefec99796ad113390b1f161b428c874b
- Human checklist: acceptance/human/R1-regression-evaluation/checklist.md
- Checklist SHA-256: d7a89e055f43e192d899b86f9acf707457abad034db8a29094d660108afffdde
- Contract snapshot: evidence/acceptance-contract.md
- Binding snapshot: evidence/binding.md
- Checklist snapshot: evidence/checklist.md
- Source identity: ea39bc29058aea2b940ac9f947e8236d601fb5a7
- Runtime identity: user-acceptance
- Executor or reviewer: 用户
- Started at: 2026-09-01T10:27:45Z
- Completed at: 2026-09-01T10:27:45Z
- Evidence directory: evidence/

## H-01

Result: PASS. The acceptance owner confirmed that the result is limited to the fixed three accepted A4 cases and exactly four ordered routes per case. It reports route hits, misses, gaps, route increments, leave-one-route-out loss, and bounded manual minutes only. Zero-increment routes and unresolved gaps remain explicit.

The two independent zero-write reports are bound to frozen input manifest SHA-256 `8b61173e4ffd5f53deede4889f4bd026941294b71d6503c0ec84630492d810a4`, with distinct reviewer identities, wrappers, regular-file paths, and report hashes: `ablation-boundary` `70728e7c38ed6a19da99dcff37fdab7838ce3cec888d2e8fd153c092f890646d`; `identity-contract` `ff74a4115b610fa71e9fed75e41ea226a614e9872002aff675bc47c717bb84bd`.

## Scope Boundary

This acceptance fixes only the three-case, four-route local regression evaluation. It does not accept mathematical proof, live external literature retrieval, accuracy, recall, statistics, generalization, novelty, authorization, production/device behavior, or public release. No Q1 or A5 state is changed by this run.

## Conclusion

Role: 评测负责人. Decision: ACCEPTED for H-01. Signature identity: 用户（研究负责人和仓库所有者）.
