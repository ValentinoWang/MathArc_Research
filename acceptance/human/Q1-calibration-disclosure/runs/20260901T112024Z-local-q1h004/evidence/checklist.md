# 人工验收清单：Q1-calibration-disclosure

- 任务编号：Q1-calibration-disclosure
- 人工验收绑定：acceptance/human/Q1-calibration-disclosure/binding.md
- 验收合同：agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/Q1-calibration-disclosure/acceptance-contract.md
- 合同版本：7
- 清单状态：已批准
- 所需人工角色：研究负责人
- 清单负责人：用户
- 批准证据：用户已明确要求验收通过、持续完成，并在每个阶段推送 GitHub；A4 与 R1 已正式接受，Q1 v7 仅接受本地未校准披露边界
- 执行结果：acceptance/human/Q1-calibration-disclosure/runs/<run-id>/result.md

## H-01

- 验收问题：三例困难度和科学优先级是否被清楚地限制为未校准的内部研究记录，且没有把高优先级写成可传播、可公开或已经得到数学确认？
- 必须人工判断的原因：研究优先级与对外沟通边界的语义解释不能由字段一致性测试完全替代。
- 前置条件：Q1 专项机器测试已通过；打开当前 R1 接受证据、固定政策夹具和 R1 范围说明。
- 验收步骤：
  1. 检查三例均标为 `UNCALIBRATED`，传播准备度均为 `NOT_READY`。
  2. 检查高科学优先级的两例没有被描述成准确、已解决、开放已确认或可公开。
  3. 检查每例均保留数学证明、新颖性接受、开放状态确认、统计性能和公开发布的禁止项。
- 预期观察：优先级与传播状态清楚分离；措辞只限固定 R1 三例和本地披露策略；没有统计性能、数学证明、外部文献或发布授权结论。
- 是否阻塞发布：是
- 结果记录规则：将签署后的观察和结论写入新的 `acceptance/human/Q1-calibration-disclosure/runs/<run-id>/result.md`；不得通过修改这份已批准清单来记录某次执行结果。
