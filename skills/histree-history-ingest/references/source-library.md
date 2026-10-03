# 分段检索与引用参考

## 开始录入前

仍先检查《通鉴》`active_cursor`及对应卷年段落账本，按连续段落推进。二十四史用于同一人物、事件的独立补证，不按搜索命中改变主线进度。清史稿已规范化但暂不新增录入。

当前选定底本在 `resources/originals/twenty-four-histories/*-EPUB全文.txt`，原EPUB及旧版本在其 `backup/`。统一索引为 `resources/derived/history-library/catalog.json`；每书的 `sections.json`含卷界与`source_issues`，`paragraphs.jsonl.gz`含全文、定位及待核标记。

SQLite仅是本地缓存，不提交Git。首次克隆、缓存缺失或过期时，在仓库根目录运行：

```sh
python3 scripts/build-history-library.py --rebuild-search
```

此命令读取已提交的压缩分段文件，保留所有原文、段落ID和通鉴账本。底本未变化时不要运行全量转换和清理流程。

## 搜索、回查与导出

```sh
python3 scripts/search-history-library.py 石敬瑭 --book 旧五代史 --volume 75
python3 scripts/search-history-library.py 王昕 --book 北齐书 --volume 31
python3 scripts/search-history-library.py 明皇帝 --book 周书 --volume 4
python3 scripts/search-history-library.py --id '<搜索返回的完整段落ID>'
python3 scripts/search-history-library.py --id '<搜索返回的完整段落ID>' --export /private/tmp/histree-source-draft
```

书名可用简体或book key；关键词按原文字面搜索，繁简、异体字和异名需分别查询。默认搜索正文及表格行，`--include-notes`增加注文，`--all-kinds`包括标题、目录与缺漏提示。搜索返回最多100条，不代表全部命中或卷年已经读完。

读取完整记录并核对所属卷、分部、上下文和`sections.json.source_issues`。`volume_candidate`及`structural_volume_verified`是卷号结构结果；`volume_verified: false`和`review_status: pending`表示尚未人工校核。标题、目录、网站编校提示和来源缺漏不能当正文事实；`not_original_paragraph`表示长段拆成阅读块，引用时须回看原段上下文。

导出会核对TXT与原EPUB哈希，生成`source.txt`、`paragraph.json`和`manifest.json`。`source.txt`保留来源片段的原换行和空格；阅读排版或`snippet`不能替代它。逐字摘录若横跨多个分段，分别导出并在批次中保存各段的定位与哈希。

## 接入批次

1. 将核对后的导出文件保存到本批次`sources/`，按批次规范合并`sources/manifest.json`，保留段落ID、底本路径与哈希、字符/行号、EPUB成员及元素定位。导出清单是草稿审计，不自动构成已校核来源或发布清单。
2. 为书证创建独立source与claim，复用已有主体key/UUID；在`coverage.json.supplements`连接对应通鉴段落。citation包含书名、卷/分部和完整段落ID，note说明原文与核对范围。
3. EPUB来自电子转录本，纸本和异文未核须如实注明。表略、外部子页、私用字、图片字部件描述等有问题的部分单独标记待核，不凭描述猜字或将卷目齐全视为全文齐全。
4. 先提交来源快照，再使用所得固定commit生成出处URL；仍按主Skill校验批次和只读预检，只有当前任务授权发布才执行`--apply`。搜索与导出不改变录入游标。

规则与完整处理流程见 [规范化说明](../../../docs/HISTORY_TEXT_NORMALIZATION.md)，参数说明见 [检索文档](../../../docs/HISTORY_LIBRARY.md)。

## 卷内传主与电子章节标题

EPUB章节题可能只选同卷的一位传主，分段记录的section_title不能单独证明当前段落属于该传。例如《宋史》卷262的EPUB原题李濤傳，正文卷题为列传第二十一，开篇李穀，韩熙载与李谷谈话在李谷传内。出处展示应依据正文核对的卷号、传主，并在定位中保留原EPUB题名说明。

核对时查看原TXT卷题和传主起始段，导出证据并保留段落ID及原字。已发布出处标签的更正单列content/revisions中的plan、定向更新脚本和匿名回查证明，不覆盖原发布批次、电子底本或快照。示例见content/revisions/2026-10-03-songshi-262-ligu-heading/。
