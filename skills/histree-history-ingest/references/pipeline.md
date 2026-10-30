# 可恢复的资料发布

工具默认不改生产。事实只在工作台草稿中编写一次；机械装配可按哈希复用，史料判断及匿名验收不能用缓存代替。先单独验证工具，再开始使用其冻结协议的新卷。

此发布编排命令一次验收一个完整卷的单批草稿；可在草稿内分阅读块。不能只发布同卷一部分就推进整卷，多个part需另行汇总所有发布收据或沿用已验证的逐批流程。冻结同时绑定实际MySQL目标指纹、匿名API与分期数据；切换目标或修改分期后必须在未发布状态重新校核，不复用旧验收。

1. 连续通读并填写草稿、逐事件时间结论、必要身份补证及待考。`editorial_checklist.events[事件key].participation` 显式给出 `status: complete`、`required_person_keys` 和具体 `reason`；无人名者可给空列表并说明，不从正文自动猜配人物。`period_checks` 记录人工核实的活动年和出处理由，工具只检查时代标签是否相容，不推生卒。
2. `reuse-history-sources.py <批次> --root <资料根目录>` 默认只查同书已发布快照；`--apply-local` 仅为未发布 manifest 复用最早已核固定出处，保护旧档。`archive-history-sources.py` 先保存只包含 source.txt/paragraph.json 的公开来源计划；已授权归档时用 `--apply --expected-plan-sha256 <精确哈希>`。保留结果，网络验收失败用原计划恢复，不另建重复归档。
3. `history-ingest.py ready <批次> --root <资料根目录> --mysql-env <凭据路径>`：集中检查来源、作者检查项、工作台、时间、整卷覆盖、UUID、线上复用/重复边和 MySQL 只读预检，再冻结事实、原文、审阅及工具哈希。未解决的问题先修正或来源限定并保留待考；不能关闭守卫。
4. 在当前任务授权范围运行 `history-ingest.py publish <批次> --apply --expected-freeze-sha256 <精确哈希>`，显式指定相同资料根、环境和 API。沿用标准 MySQL 发布器、结构化出处/年代侧表与匿名逐表读回，检查确年事件进入对应年份和原文双向定位。恢复时读取实际阶段；已提交的侧表只补匿名核验，不重复改写。
5. `.workflow/web-samples.json` 给首中末条目或纯原文样本。实际网页检查正文、身份、时间和引用展开；保存有 batch_sha256、book_key、volume、quote_expansion_verified（纯阅读可为 original_text_visible）的证据。observations 中每项包含样本 id、path、book_key、volume 及实际观察，不能把 API 结果充作网页观察。
6. `history-ingest.py accept <批次> --apply --expected-freeze-sha256 <精确哈希> --progress <本书实际进度> --web-proof <实际网页证据>`。验收全部匹配后投影本站原文覆盖，更新本书索引和待考队列，游标最后以旧值守卫推进。其他书不动。已开始发布的档案不重建；实质修正另建带完整旧值守卫的修订。

`history-ingest.py timings <批次>` 区分工程、史料校核和发布耗时。缓存只复用输入、产物及工具均未变化的机械结果；`apply` 和在线验收每次实查。工具变更、未声明输入变化或临时跳过检查不能拿来比较提速。

普通新批次只跑相应内容验证；工具改动另跑相关离线回归和隔离 MySQL。测试夹具不得引用生产凭据或假称线上验收。`test-history-sidecars-mysql.py` 仅允许 loopback、histree_test_*、MySQL8；完整验证由CI的隔离服务执行，不在生产新建测试表。
