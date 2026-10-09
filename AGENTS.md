# Histree 仓库协作指引

处理历史人物、事件、关系、出处、`content/` 批次或录入进度时，先读 [项目 Skill](skills/histree-history-ingest/SKILL.md)，再按本次任务决定是否读取其中的史料校核或发布参考。界面、部署等其他任务不需要加载这套史料流程。

历史资料按各书自身的卷、篇章和连续原文段落独立录入，不指定全站主线。开始新批次先看本次选定书的独立进度与对应段落账本；《资治通鉴》沿用 `content/yearly-progress.json`，其他书按Skill建独立账本。不得按人物挑段、跳段或把未读完的卷、篇章、年标为完成。人物、事件与关系在全站共用稳定 key/UUID，各书保留独立出处与异说；按已核时间汇集事件，不强定未知年代，也不把所有材料转成事件。

当前阶段以《资治通鉴》《续资治通鉴》和二十四史搭建基础数据面；《清史稿》及其他专门史籍留待后续增补，已有发布出处保留。资料范围见 `resources/catalog/ingestion-source-scope.json`；录入前用 `scripts/search-history-library.py` 检索和回查分段原文，自动分段、卷界及覆盖缺口仍须校核。

二十四史及清史稿的选定来源是 `resources/originals/twenty-four-histories/` 根目录的25份 `*-EPUB全文.txt`；其他版本与原EPUB在同目录 `backup/`。规范化及本地检索统一使用 `resources/derived/history-library/`；清史稿已预处理但尚不新增录入。旧阅读/校改副本已清理，不重建多套冗余文本，不移除已发布批次所引用的原文快照。

首次克隆或缓存缺失时用 `python3 scripts/build-history-library.py --rebuild-search` 从已提交的分段记录建立本地检索；录入引用按Skill导出原TXT片段并保留定位，不把搜索摘要或阅读排版当来源快照。

录入当前书不要求常规扩大多书补证；身份、时间、关系和疑似讹误仍须必要校核。其他书可独立新增资料，不必找《通鉴》对应段落。

《续资治通鉴》（毕沅）作为独立编年体史书，按其960—1368年所载宋元叙事录入，工作TXT在 `resources/originals/xutongjian/`，卷年分段入口在 `resources/derived/history-library/xu-zizhi-tongjian/`；公元年候选需校核，末年不视作全年完整。正式续录时建立独立账本，保留现有通鉴游标。

资料发布需有逐条可回溯的原文、具体定位和校核说明。提交前运行批次验证并审阅身份、时间和异文；发布由 `scripts/publish-book-batch.py` 执行，默认只读预检。`--apply` 会写入线上 Supabase，只在当前任务已授权发布时使用。不要把服务端环境文件或密钥加入提交。

保留已有发布批次和其他人工作区文件；处理新批次时只暂存本次相关路径。
