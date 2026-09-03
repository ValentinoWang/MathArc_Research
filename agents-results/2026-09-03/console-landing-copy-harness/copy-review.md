# Copy review: console landing and console views (2026-09-03)

Meaning pass for `docs/prototypes/problem-intel-console.html` (served as the console dashboard) with the
backend labels in `matharc/v02/review_server.py` and `matharc/v02/review_bundle.py` aligned to the same
vocabulary. The lexical checker (`scripts/check_ui_copy_quality.py`) ran before and after; its evidence is in
`quality-gates/ui-copy-quality.{json,md}`. The frozen `docs/prototypes/review-console.html` was inventoried
and passes the checker unchanged; it shares no defective term with the console.

Method: inventory of every CJK string (2 906 segments across 1 839 source lines), then one question per
string — which object, which fact, which next step, whose vocabulary. Only strings a reader could not act on,
or that leaked implementation text, were rewritten; deliberately plain, opinionated sentences were kept.

| Where | Before | After | Reason |
| --- | --- | --- | --- |
| Landing · hero chip | 读我 | 标注说明 | "读我" is a README joke a first-time reader cannot decode; the chip labels a legend. |
| Landing · hero eyebrow | (none) | 研究预览 · 面向数学与人工智能研究者 | The hero never said who the product is for; the eyebrow answers it before the statement. |
| Landing · hero figure | (none) | 一道题走完三步是什么样 (three demo rows with status pills) | The hero had no evidence object; the figure shows one problem's real demo states so the claim has a referent. |
| Landing · hero sub | …交给可证伪的攻克进程，最后只允许发布… | …交给可证伪的攻克进程。最后，它只允许发布证据真正支持的那一句话。 | One 60-character sentence split at the natural break; same content. |
| Landing · plane lead | 三步之间有一条主线：已知结果图上的残余缺口被编译成待证命题，根命题驱动攻克进程… | 三步由一条主线串起来：第一步在已知结果图上找出还没有人闭合的缺口；第二步把这个缺口编译成一条待证命题…；第三步由攻克留下的证据决定… | Four undefined terms in one clause; the rewrite walks the three steps in order and defines the gap before naming it. |
| Landing · step 01 | …不是一个布尔值——因为「没搜到解答」会随时间腐坏。九道硬门逐项否决… | …而不是一个「是／否」——因为「没搜到解答」这件事会随时间失效。开工前还有九道检查逐项否决… | "布尔值" is programmer vocabulary; "硬门" is internal. |
| Landing · step 02 | …而是残余区间里最小的那个可发表增量。 | …而是前沿上最小的那个可发表增量——我们称它为残余缺口。 | The term "残余缺口" is used in the heading but was never defined on the page. |
| Landing · step 03 | 五个角色轮转：策略选义务、证明提方案、证伪找最便宜的杀手测试、验证调用白名单精确工具、综合提交晋升尝试。 | 每一轮由五个角色接力：策略角色决定先证哪条义务，证明角色提出候选论证，证伪角色为它设计成本最低的证伪测试… | Telegraphic four-character clauses read like notes; "杀手测试" is a literal translation of *kill test* while the product elsewhere says 证伪测试. |
| Landing · sections | (h2 only) | 01 · 三个步骤 / 02 · 工作方式 / 03 · 一个真实案例 / 04 · 不做什么 eyebrows | One repeated rhythm (eyebrow → heading → lead) so the eye learns the page once; matches the nav labels. |
| Landing · case h2 | 一个真实案例：我们自己抓到了自己的结果不新颖 | 我们自己抓到了自己的结果不新颖 | The prefix moved to the eyebrow; the heading keeps the claim. |
| Landing · closing band | 申请进入 | 申请进入 / 先看演示 | A reader who is not ready to apply had no path back to the demo at the end of the page. |
| Login · invite hint | 邀请码与研究范围绑定，只有服务端确认会话后才会进入控制台。 | 邀请码与你的研究范围绑定。只有服务器确认邀请有效后，才会进入控制台。 | "服务端确认会话" names an implementation step; the reader needs to know what is checked. |
| Login · guest note | 访客模式只读，所有操作只改变本地状态。 | 访客模式只读：界面中的操作只影响当前浏览器，不会写入任何工作区。 | "本地状态" is developer vocabulary; says what actually happens. |
| Access · messages | 正在由服务端验证邮箱、邀请码与会话… / 身份与会话已确认。 / 身份与研究预览会话已由服务端确认。 / 服务未确认申请已进入待审核队列，未开通访问。 / 服务端未能确认当前会话… / 服务端未确认退出… / 暂时无法连接退出服务… | 正在验证邮箱与邀请码… / 邀请码已确认，正在进入控制台。 / 邀请码已确认，已进入研究预览。 / 服务器没有确认收到申请，访问未开通。请稍后重试。 / 无法确认当前会话，请重新使用邀请码进入。 / 退出没有成功，当前会话保持不变。 / 暂时无法连接服务，退出没有完成… | Every message now names what happened and what to do next in the reader's words; "服务端" and "会话" are implementation terms. |
| Topbar · provenance label | 演示数据 (next to a second 演示数据) | 未接入工作区 / 未接入工作区（console.json 不可用） | Two adjacent labels carried the same text for different facts (data source vs. view data class). The source label now says the source state. |
| Rail card | 开放状态还新鲜吗 | 开放状态还有效吗 | "新鲜" is a metaphor for a validity period the page then explains literally. |
| Topbar · topic task | 观测合同版本 3 | 监测合同 版本 3 | The rest of the product says 监测合同. |
| Difficulty · ledger | 每次每次攻克开始前 | 每次攻克开始前 | Doubled word. |
| Dependency graph note | …也无法解锁上游。 | …依赖它的上游命题也无法就绪。 | Says which object changes state instead of a game metaphor. |
| Roster · assurance levels (prototype + backend) | 机器足够 / 需一名人类 / 需两名独立人类 (prototype); 机器已核实 / 需要一位评审人判断 / 需要两位独立评审人分别判断 (backend) | 机器判定即可 / 需一名评审人判断 / 需两名独立评审人分别判断 (both) | Demo and production disagreed on the same enum; "机器已核实" also mis-states MACHINE_SUFFICIENT (a machine verdict suffices, nothing was verified yet). |
| Exploration · fan-out card | 受治理扇出已接线。 | 受治理扇出已启用。 | "接线" is the SSOT's construction-status word, not a user state. |
| Review queue · states | 同源 /api/review-queue 未返回可用响应 / 未接线示例 / 同源真实服务 | 评审服务（/api/review-queue）没有返回可用响应 / 示例数据，未连接评审服务 / 已连接评审服务 | "同源" and "接线" are implementation vocabulary. |
| Live source view · rail | 读模型边界 | 数据边界 | "读模型" (read model) is a CQRS term; every other live view calls this card 数据边界. |
| Live routes / disclosure / novelty fallbacks | routes projection 缺失… / disclosure projection 缺失… / 缺少已验证的 novelty audit projection… / 服务端未提供… | 路线投影缺失… / 披露投影缺失… / 缺少已验证的新颖性审计投影… / 服务器没有提供… | English tokens stood in for missing Chinese nouns. |
| Live campaign view | 当前工作区未附带 campaign report… / 账本 event_sequence 范围 / 报告由受治理的 campaign 运行时产生。每轮与账本的对应只使用导出提供的 event_sequence 范围或携带同一 round_index 的检查点事件… | 当前工作区没有附带攻克报告… / 账本事件序号范围 / 报告由受治理的攻克运行时产生。每一轮与账本的对应，只使用导出提供的事件序号范围，或携带同一轮次索引的检查点事件… | Field names as prose. |
| Local projections | 只有九道门均为 PASSED 的候选问题显示为可开始 / 状态必须为 UNCALIBRATED / 身份和支付提供方均为 not_configured / 拒绝持久化 token、secret、password、credential 或 API key / 此视图要求一个已验证的本地记录投影。服务端未提供该配置… / 摘要变更将使服务端投影拒绝加载。 | 只有九道门全部通过的候选问题才显示为可开工 / 状态必须标为未校准 / 身份与支付提供方均未配置 / 拒绝持久化任何凭据字段（token、secret、password、credential、API key） / 此视图需要服务器提供一份已验证的本地记录投影。当前没有配置… / 摘要一旦变更，服务器投影会拒绝加载。 | Enum values as prose; the credential list stays because those are the literal denied field names. |

Kept on purpose (reviewed, not changed): the opinionated one-liners (「等你决定」, 「这是评估，不是测量」), the
technical notes inside the tool-ledger view that quote backend field names in `.mono` containers, and the
review-form hints that name `reviewer_id` because the reader must type that field.

Pre-existing gap noted, not fixed here: `scripts/check_console_action_inventory.py` already fails on `main`
(`access-mode`, `application-submit`, `logout` emitted but absent from SSOT §9.14); this needs an SSOT revision,
not a copy change.
