# Histree 仓库协作指引

处理历史人物、事件、关系、出处、`content/` 批次或录入进度时，先读 [项目 Skill](skills/histree-history-ingest/SKILL.md)，再按本次任务决定是否读取其中的史料校核或发布参考。界面、部署等其他任务不需要加载这套史料流程。

历史资料的主线是《资治通鉴》的书、卷、年、连续段落。开始新批次先看 `content/yearly-progress.json` 的 `active_cursor` 和对应 `paragraphs.json`，不得按人物挑段或把尚未读完的卷、年标为完成。人物、事件与关系在全站共用稳定 key/UUID；其他史书作为独立出处补充到同一主体。

资料发布需有逐条可回溯的原文、具体定位和校核说明。提交前运行批次验证并审阅身份、时间和异文；发布由 `scripts/publish-book-batch.py` 执行，默认只读预检。`--apply` 会写入线上 Supabase，只在当前任务已授权发布时使用。不要把服务端环境文件或密钥加入提交。

保留已有发布批次和其他人工作区文件；处理新批次时只暂存本次相关路径。
