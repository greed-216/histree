# 史料文本规范化

2026-10-01统一以二十四史及《清史稿》的EPUB转换TXT作为工作文本。当前入口：[规范化阅读与分段库](../resources/derived/history-library/README.md)。史料录入仍以《资治通鉴》和二十四史为基础；清史稿仅本地预处理，已发布出处与通鉴游标保留。

## 来源目录

`resources/originals/twenty-four-histories/` 根目录只保留25份选定来源TXT，命名 `01史记-EPUB全文.txt` 至 `25清史稿-EPUB全文.txt`。原EPUB、PDF、旧TXT、残稿和少量历史审计在 `backup/`，移动按SHA-256逐件核对。转换TXT与原EPUB仍是独立版本，不将其他版本的文字或页码混接进来。

[转换审计](../resources/derived/epub-txt/README.md)保留每卷范围、EPUB成员与元素路径、字形还原及移出记录。仅保存一套压缩JSON/JSONL元数据，不额外复制每卷TXT。图片字使用原EPUB的alt文字或部件描述，不猜字；私用字符保留待核。

## 规范化规则

- 按已核验的EPUB卷号、上下中和之一至之四排序；卷前目录、序文及附录独立标记。
- 优先保留来源HTML段落、标题、注文及表格行；完整保留正文非空白字符。仅清理首尾空白和非表格段内汉字之间的机械空格，不简繁互转，不改讹字、异文或标点。
- 长正文或注文段超过1200字符时，在约400—1000字符处找句末；找不到时按800字符拆阅读块。拆分记录标记 `not_original_paragraph`，不冒充古籍原段；表格行不按字数拆断。
- 正文、表格行、标题、目录、注文、网站编校提示、附录及来源缺漏分别标记。每个来源字符只覆盖一次；规范化显示文本与原TXT的行号、字符范围及片段哈希同时保存。
- 原来源中的“表略”、外部子页及缺字保留为待核问题，见各书 `sections.json.source_issues`。卷号覆盖完整不代表全文无删节，不标成校勘通过或已录入。

每书只保留一套 `reading.txt`、`paragraphs.jsonl.gz`、`sections.json` 和 `index.json`。阅读文本便于直接查看；压缩JSONL用于机器处理；SQLite是可重建的检索缓存。逐段定位仍指向选定来源TXT，引用导出保存其原换行和空格。

## 重建与校验

首次克隆或只需恢复本地检索时，运行 `python3 scripts/build-history-library.py --rebuild-search` 即可。此命令从版本化JSONL重建未提交的SQLite缓存，不修改来源、阅读文本、分段记录或ID。只有底本或处理规则发生变化时，才使用以下全量处理流程：

```sh
python3 scripts/organize-history-sources.py
python3 scripts/prepare-history-epubs.py
python3 scripts/test-history-epubs.py
python3 scripts/build-history-library.py
python3 scripts/test-history-library.py
python3 scripts/clean-history-text-artifacts.py
```

构建先写临时目录，完成后切换。校验通过才清理上一版临时数据；校验失败时保留旧版供排查。重复构建使用相同来源与规则时段落ID不变。《通鉴》从已有分段记录重建搜索缓存，保留其全部段落ID与编年账本。

读取压缩JSONL：

```python
import gzip, json
with gzip.open('resources/derived/history-library/jiu-wudaishi/paragraphs.jsonl.gz', 'rt', encoding='utf-8') as f:
    for line in f:
        paragraph = json.loads(line)
```

## 清理范围

旧 `readable/`、`readable-txt/`、`corrected-txt/`、`coverage-review/`、旧库版本和重复逐卷副本已移除；旧处理脚本移入backup供历史核查，不是当前工作流程。原周书PDF补卷审计少量保留。已发布批次引用的 `derived/twenty-four-histories/` 两份PDF提取及其他固定引用源保留原位，不重写。

[清理清单及保护文件校验](../resources/catalog/history-text-cleanup.json)记录删除范围、前后大小和保留来源；[来源迁移及哈希](../resources/originals/twenty-four-histories/backup/manifest.json)记录原件移动。详细搜索和引用方法见 [分段检索说明](HISTORY_LIBRARY.md)。
