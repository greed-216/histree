# 批次发布与交接

在仓库根目录运行，将 `<批次>` 换成当前 `content/books/zizhi-tongjian/vol-.../year-.../part-...` 路径：

```bash
python3 <批次>/build_batch.py
python3 scripts/validate-content-batch.py <批次>/content-batch.json
python3 scripts/prepare-book-import.py <批次>/content-batch.json
python3 scripts/publish-book-batch.py <批次>/content-batch.json
```

新增来源先把原文快照提交到仓库，再用该提交哈希生成固定 Git URL；尚未归档来源时不要发布引用。先逐段审查生成的 batch 和 coverage，确认段落连续、下一段正确、复用 key 列入 `reused-keys.json`，并查看只读预检的新增与复用数量。手动检查主语、行动、前后次序、地点和摘录支持范围。勿直接使用通用 `scripts/prepare-content-import.py` 生成的发布/撤回 SQL；`prepare-book-import.py` 才会排除复用对象。

当前任务已授权上线时执行：

```bash
python3 scripts/publish-book-batch.py <批次>/content-batch.json --apply
```

检查 `publication.json` 的 `batch_sha256` 与批次文件匹配，`verified: true`，`public_counts` 完整。脚本先插草稿、再逐表公开，最后按匿名权限读回；Supabase REST 分步写入不具整批 SQL 原子性。中断后先看 `stages`、线上记录和来源。若已有 key 内容不同，或姓名别名、关系端点冲突，停止并校核身份。

公开读回后，更新 `paragraphs.json` 的状态为 `published_verified`，更新 `content/yearly-progress.json` 的最后已发布段、下一段、年覆盖和批次路径，更新 `content/books/zizhi-tongjian/index.json`，再运行 `python3 scripts/index-book-claims.py`。如需验证问答，选本批的具体问题，检查回答与出处定位；问答成功不替代史料审核。

提交时只暂存本批及必要索引和进度，避免其他人的未提交修改或 `apps/api/.env`。在交接说明写明发布段落范围、待考点、下一段和该年是否完成。
