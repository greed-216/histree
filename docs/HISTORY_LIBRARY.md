# 统一史料分段与检索

[本地入口](../resources/derived/history-library/README.md)包含二十四史、清史稿的选定EPUB转换TXT及原《资治通鉴》分段。新TXT已切换为本地检索底本。《清史稿》仅预处理，正式录入仍遵循[资料范围](../resources/catalog/ingestion-source-scope.json)；已发布来源、实体key/UUID和通鉴进度保持原有状态。

每书提供 `reading.txt`、`paragraphs.jsonl.gz`、`sections.json`、`index.json`。段落记录包含规范化文字、类型、版本ID、原TXT行号与字符范围、原EPUB文件及XHTML成员、元素路径、来源问题和待核状态。SQLite缓存中的记录采用zlib压缩，由搜索脚本解码；数据库可重建，不作为史料原件。

## 搜索

在仓库根目录执行，关键词按原繁体字面查找：

SQLite不随Git提交。首次克隆或缓存缺失、过期时，先运行以下命令；它只从已提交的分段文件重建缓存，不改原文、分段或段落ID：

```sh
python3 scripts/build-history-library.py --rebuild-search
```

```sh
python3 scripts/search-history-library.py 石敬瑭 --book 旧五代史 --volume 75
python3 scripts/search-history-library.py 王昕 --book 北齐书 --volume 31
python3 scripts/search-history-library.py 明皇帝 --book 周书 --volume 4
python3 scripts/search-history-library.py 李克用 --book 资治通鉴
python3 scripts/search-history-library.py 天文 --book 清史稿 --all-kinds
```

`--book`支持简体中文书名或书目key；`--section`过滤EPUB卷题；`--volume`过滤卷号。上下分部保存在记录的 `volume_part`。卷号结构检查通过不代表纸本文字已校勘，因此 `volume_verified`仍为false，`structural_volume_verified`单独标记。

默认返回正文和表格行；`--include-notes`增加注文；`--all-kinds`包含目录、标题、网站提示和缺漏标记。支持一至二字字面查询；三字以上采用SQLite FTS5 trigram索引并逐字复核。异体字、简繁及异名不自动合并，如刘／劉、镠／鏐须分别查。最多返回100条，返回数量不是命中总数。

## 查看与引用

```sh
python3 scripts/search-history-library.py --id '<完整段落ID>'
python3 scripts/search-history-library.py --id '<完整段落ID>' --export /private/tmp/histree-source-draft
```

导出 `source.txt`、`paragraph.json`、`manifest.json`。source.txt逐字保存选定TXT中的原片段，包含原换行和空格，不是reading.txt的显示排版。导出前检查TXT、原EPUB哈希和片段哈希；原件移入backup后可按哈希迁移记录回查。

发布前仍需独立来源快照、具体定位与校核说明，并固定仓库提交链接。自动分段不表示史实审核或录入完成。长段阅读块、编者导航标题、注文和后世补配标识不作为原作者正文事实。

## 来源和覆盖

当前二十四史与清史稿的卷号覆盖均通过，但正文仍可能有缺漏：宋史卷215部分表格指向外部子页，明史及清史稿若干卷明示略表，部分来源仍有私用字或图片字。逐卷问题在各书sections.json中保留。旧五代史及北齐书的新来源已覆盖原旧TXT缺失的后半卷目，仍须逐段校核。

旧规范化产物与未被引用的旧索引已按用户要求清理，不再保持多套版本。已有发布批次及PDF提取引用保留原位，固定提交引用不变。《资治通鉴》原段落ID及进度不变。来源或分段规则再次改变时须审核现有引用依赖，不静默替换已发布出处。

## 重建与校验

规范化规则及完整重建流程见 [文本规范化说明](HISTORY_TEXT_NORMALIZATION.md)。转换、字符覆盖、卷序、原行/字符定位、逐书FTS、两字查询、旧缺卷搜索回归和原文导出均已有校验，报告见 [validation.json](../resources/derived/history-library/validation.json)。重建不联网、不发布、不改线上数据库。
