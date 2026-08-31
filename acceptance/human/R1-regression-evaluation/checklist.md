# 人工验收清单：R1-regression-evaluation

- 任务编号：R1-regression-evaluation
- 人工验收绑定：acceptance/human/R1-regression-evaluation/binding.md
- 验收合同：agents-results/2026-08-31/problem-intelligence-plane/acceptance-fragments/R1-regression-evaluation/acceptance-contract.md
- 合同版本：8
- 清单状态：已批准
- 所需人工角色：评测负责人
- 清单负责人：用户
- 批准证据：用户于 2026-09-01 批准修订 R1 验收，要求两份独立 AI 复审均有持久化 PASS 报告
- 执行结果：acceptance/human/R1-regression-evaluation/runs/<run-id>/result.md

## H-01

- 验收问题：评估结果是否清楚地只表达固定三例上的路线增量、命中、漏检、缺口和人工耗时，而没有暗示统计性能或数学结论？
- 必须人工判断的原因：发布措辞边界和研究解释不能由字段校验完全代替。
- 前置条件：机器测试、R1 evidence 和两份绑定同一冻结输入的独立 AI `PASS` 报告均已通过；打开对应的回归结果与限制说明。
- 验收步骤：
  1. 查看两份复审报告是否具有不同审阅身份、不同包装器和相同冻结输入摘要，且均以 `PASS` 结束。
  2. 查看三例名称、四路记录、增量和留一路结果。
  3. 核对每条结论是否限定在固定夹具范围。
  4. 检查是否出现准确率、召回率、泛化、已解决或已确认新颖性等越界表述。
- 预期观察：结果可复核、措辞保守，零增量和未决项被明确保留；没有授权或公开结论字段。
- 是否阻塞发布：是
- 结果记录规则：将签署后的观察和结论写入新的 `acceptance/human/R1-regression-evaluation/runs/<run-id>/result.md`。
