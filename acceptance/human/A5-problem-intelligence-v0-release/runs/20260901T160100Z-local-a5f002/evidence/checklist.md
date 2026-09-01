# 人工验收清单：A5-problem-intelligence-v0-release

- 任务编号：A5-problem-intelligence-v0-release
- 人工验收绑定：acceptance/human/A5-problem-intelligence-v0-release/binding.md
- 验收合同：agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/A5-problem-intelligence-v0-release/acceptance-contract.md
- 合同版本：5
- 清单状态：已批准
- 所需人工角色：研究负责人和仓库所有者
- 清单负责人：用户
- 批准证据：用户已明确要求验收通过、持续完成，并在每个阶段提交并推送到 GitHub；Q1 v5 当前身份已由机器、H-01 和两条独立 AI 复审重新接受
- 执行结果：acceptance/human/A5-problem-intelligence-v0-release/runs/<run-id>/result.md

不要重复由自动化检查负责的哈希、字段、远端 ref 或测试断言。本清单只判断发布范围的研究语义。

## H-01

- 验收问题：本次决定是否明确只交付已接受的仓库源、测试、SSOT 和验收记录，而没有把三例未校准记录描述为数学结论、外部文献结论、已确认开放状态、新颖性、统计性能、生产能力或可公开的研究成果？
- 必须人工判断的原因：仓库源码交付与研究结论公开之间的语义边界需要研究负责人和仓库所有者共同判断，不能由字段一致性测试完全替代。
- 前置条件：A5 机器测试、合同检查、SSOT 严格验证和 Obsidian 快照检查已通过；打开 Q1 政策、A5 证据与本清单。
- 验收步骤：
  1. 检查 A5 的允许范围仅为仓库源级交付，并明确绑定 `union-closed` 的固定三例和 Q1 v5 节点、执行合同、冻结清单、台账及两条独立审阅。
  2. 检查 Q1 的三例仍为 `UNCALIBRATED` 和 `NOT_READY`，且 A5 仍保留 `q1_public_release_allowed=false`。
  3. 检查数学证明、外部资料、开放状态、新颖性、校准/统计性能、生产/设备和研究结论公开均在禁止列表中。
  4. 检查 GitHub 交付被限定为 A5 提交推送后的远端 `main` SHA 回读，不把回读写成任何更高层证据。
- 预期观察：范围受限、禁止项完整、联合角色清楚；源码交付与研究结论公开没有混淆。
- 是否阻塞发布：是
- 结果记录规则：将签署后的观察和结论写入新的 `acceptance/human/A5-problem-intelligence-v0-release/runs/<run-id>/result.md`；不得通过修改这份已批准清单来记录某次执行结果。
