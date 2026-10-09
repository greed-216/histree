# 批次发布与交接

在仓库根目录运行，将 `<批次>` 换成当前书在 `content/books/{book-key}/` 下的实际批次路径。编年体可按卷年组织，纪传体按卷/篇章组织；若批次有 `build_batch.py`，先运行它：

```bash
python3 <批次>/build_batch.py
python3 scripts/validate-content-batch.py <批次>/content-batch.json
python3 scripts/prepare-book-import.py <批次>/content-batch.json
python3 scripts/publish-book-batch.py <批次>/content-batch.json
```

新书首次录入前检查现有工具支持：`index-book-claims.py` 使用显式书目key与来源前缀映射，新书尚未接入时先补齐映射并验证。当前发布器不支持专题发布，不能将工具未支持的内容假造为其他类型绕过校验。

新增来源先把原文快照提交到仓库，再用该提交哈希生成固定 Git URL；尚未归档来源时不要发布引用。先逐段审查生成的 batch 和 coverage，确认段落连续、下一段正确、复用 key 列入 `reused-keys.json`，并查看只读预检的新增与复用数量。手动检查主语、行动、前后次序、地点和摘录支持范围。勿直接使用通用 `scripts/prepare-content-import.py` 生成的发布/撤回 SQL；`prepare-book-import.py` 才会排除复用对象。

当前任务已授权上线时执行：

```bash
python3 scripts/publish-book-batch.py <批次>/content-batch.json --apply
```

检查 `publication.json` 的 `batch_sha256` 与批次文件匹配，`verified: true`，`public_counts` 完整。脚本先插草稿、再逐表公开，最后按匿名权限读回；Supabase REST 分步写入不具整批 SQL 原子性。中断后先看 `stages`、线上记录和来源。若已有 key 内容不同，或姓名别名、关系端点冲突，停止并校核身份。

公开读回后，更新本次书段落账本的状态为 `published_verified`，更新该书独立进度中的最后已发布段、下一段、卷/篇章覆盖和批次路径，以及该书已有索引，具体路径与历史兼容项见 [资料目录与定位](source-library.md)。其他书的进度保持不变。确认书目key与来源前缀受索引脚本支持后，再运行 `python3 scripts/index-book-claims.py`；新书未支持时先适配验证，不绕过检查。如需验证问答，选本批的具体问题，检查回答与出处定位；问答成功不替代史料审核。

提交时只暂存本批及必要索引和进度，避免其他人的未提交修改或 `apps/api/.env`。在交接说明写明发布段落范围、待考点、下一段和本次卷/篇章（编年体另含年）是否完成。

已核验同人合并会保留隐藏的旧主体。发布预检仅在plan稳定key与审计ID一致、规范主体仍公开、重复主体为draft且无剩余参与／人物引用／关系时，允许该隐藏记录指向规范主体。普通草稿重名仍报错，禁止重新发布重复key。变更此守卫时运行 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts/tests -p test_history_identity.py`，再做线上只读预检。

## 新来源补充已发布段落

新来源可以补证旧段落，无需重写旧批次。在当前书的 `coverage.json.supplements` 中填写原段落ID与主体key，并在 `cross_volume_supplements` 显式声明同一段落与主体。发布脚本要求旧段落已公开核验、旧批次哈希与发布审计相符、原coverage包含该段落、补证主体存在于旧批次；这类补证不计入当前连续正文段落覆盖，也不要求其他书独立新增的引文走该补证路径。

## 修订已发布资料的进度

旧数据审阅与新增录入使用独立游标。已有文案审阅位置以 `content/revisions/2026-10-04-modern-chinese-review/progress.json` 的 `review_workflow.review_cursor` 为准，按字段记录改写或保留理由，经旧值守卫和独立匿名读回后才标完成。审阅范围以当前任务为准，不在Skill中固定停留年份；不覆盖旧批次或历史审计，不把修订进度计入另一书的连续录入进度。
