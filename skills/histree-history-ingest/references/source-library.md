# 资料目录与定位

## 统一入口与文件约定

从 `resources/derived/history-library/catalog.json` 读取书名、`book_key`、`source_version`和各产物路径。所有书使用同一套定位流程，不要求在Skill中增加单本书的使用说明。新资料须登记到目录并提供相同元数据；仅把文件放入目录不会自动成为现有脚本可检索的资料。

| 层次 | 目录与约定 | 用途 |
| --- | --- | --- |
| 底本 | 原始资料归档在 `resources/originals/`；实际路径由目录 `inputs` 和段落 `locator` 指定 | 保存原件、选定工作文本、版本与转换审计 |
| 分段 | `resources/derived/history-library/{book_key}/` | 每书统一提供 `index.json`、`sections.json`、`paragraphs.jsonl.gz`；`reading.txt`供查阅，年标题等附加元数据按需提供 |
| 录入 | `content/books/{content_book_key}/` | 保存独立进度、段落处理账本、批次及出处索引 |

目录的 `paragraph_file`、`sections_file`、`reading_file` 指向对应产物；`inputs`记录底本和转换依赖。段落 `locator`记录源文件、哈希、字符/行号及原件定位，按这些字段回查，不按书名拼出底本路径。底本的存储差异留在元数据中，不变成不同录入流程。

已有底本可能位于历史目录，沿元数据与 `resources/catalog/source-replacements.json` 的归档映射读取，不为统一外观搬动、改写已发布引用。已有书目key与分段库key不同的，记录映射并沿用稳定key，不另建同书副本。新版本保留版本标识与旧引用定位，不用新文本冒充旧底本。

文件约定用于定位，不代表校核通过。检查 `index.json` 的版本、状态和警告，`sections.json.source_issues` 的卷界与覆盖问题，以及段落中的 `kind`、`flags`、`review_status`。原件未登记或缺少可回溯分段时，先完成来源准备，不伪造元数据继续录入。

## 独立进度与批次

先在 `content/books/` 查找目标书已有目录、索引和账本；新书在 `content/books/{content_book_key}/progress.json` 建独立账本，记录分段库book_key、底本版本、卷/篇章、最后已核/已发布段、`active_cursor.next_paragraph`和批次路径。相应 `paragraphs.json` 按原文次序保存段落ID与处理结果。

续接已有账本时沿用其路径和结构。历史兼容项：`content/yearly-progress.json` 是《资治通鉴》的既有账本，原卷年账本与批次路径继续保留；它不代表全站进度，不因其他书录入而改变。

新批次在该书目录内按卷/篇章/批次组织。编年体可用 `vol-{卷}/year-{年}/part-{序号}/`，纪传体可用 `vol-{卷}/section-{篇章标识}/part-{序号}/`；缺卷号时用来源分部标识。批次保存来源快照、manifest、coverage、校核说明、实体复用清单和发布审计。已有发布档案不迁移。

卷末或篇末接下一单元；编年体整年完成需覆盖该年所跨各卷，末卷有某年记载不等于该年全年完整。跨书引用不推进被引用书的连续阅读进度。无新增事实的段落记录核对结果；工具暂不支持的内容登记待整理，不假造事件或标为已发布。

## 检索、回查与导出

SQLite是可重建的本地缓存，不提交Git。缓存缺失或过期时运行：

```sh
python3 scripts/build-history-library.py --rebuild-search
```

该命令从已提交分段重建检索，不重新转换底本、改写段落ID或修改录入账本。仅为恢复搜索不要运行全量转换、清理流程。

以下参数由目录中的book_key、来源篇章和返回的段落ID替换：

```sh
python3 scripts/search-history-library.py '<关键词>' --book '<book_key>'
python3 scripts/search-history-library.py '<关键词>' --book '<book_key>' --section '<篇章标题>'
python3 scripts/search-history-library.py --id '<完整段落ID>'
python3 scripts/search-history-library.py --id '<完整段落ID>' --export /private/tmp/histree-source-draft
```

关键词按原文字面匹配，繁简、异体字和异名分别回查。默认搜正文与表格行，`--include-notes`增加注文，`--all-kinds`包括标题、目录与缺漏提示。最多返回100条，不代表全部命中；按账本连续阅读仍须读取原分段文件。

`--volume`按卷号候选过滤。`--year`仅在该来源有年标题候选元数据时有效，过滤的是标题上下文，不是事件发生年；未换算或无年标题时按卷/篇章定位。

读取完整记录、所属篇章与前后段落。标题、目录、网站编校提示和来源缺漏不能当正文事实；`not_original_paragraph`表示长段拆成阅读块，引用需回看完整上下文。结构验证的卷号候选不等于人工校核完成。

导出核对有效工作文本与原件哈希，生成 `source.txt`、`paragraph.json`、`manifest.json`。`source.txt`保留底本原换行和空格；`reading.txt`或搜索snippet不能替代它。摘录跨多个分段时分别导出并保留各段定位与哈希。

## 接入批次

1. 将核对后的导出文件保存到本批 `sources/`，合并manifest，保留段落ID、底本路径、版本、字符/行号、哈希及原件定位。导出结果是草稿审计，不自动构成已校核来源。
2. 每处引用创建独立source与claim，核对后复用全站主体key/UUID。当前书连续段落写入 `coverage.json.paragraphs`；临时跨书核对的对应关系见 [史料校核参考](editorial.md)。
3. citation注明书名、卷/篇章/分部与段落ID，编年材料另记原年标题。电子转录、缺表、私用字、图片字及纸本未核等问题如实保留，不凭描述猜字，不把卷目齐全当全文齐全。
4. 发布前归档来源快照并生成固定提交链接；按 [发布参考](publication.md) 校验和预检。检索、导出和来源准备不改变录入游标。

现有格式和转换工具细节见 [规范化说明](../../../docs/HISTORY_TEXT_NORMALIZATION.md)、[检索文档](../../../docs/HISTORY_LIBRARY.md)。这些文档中的既有书目与处理历史用于了解存量资料；本次录入范围以任务和仓库协作指引为准。
