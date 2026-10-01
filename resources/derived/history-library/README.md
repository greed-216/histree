# 统一史料分段与检索

二十四史及《清史稿》的选定EPUB转换TXT已分段规范化；《资治通鉴》保留原段落ID。清史稿仅预处理，史料录入范围与游标不变。每书只有一套reading.txt、paragraphs.jsonl.gz、sections.json和index.json，SQLite为可重建缓存。

首次克隆或SQLite缓存缺失时，在仓库根目录运行 `python3 scripts/build-history-library.py --rebuild-search`。此命令只重建检索缓存，保留已提交的分段与ID。

[检索和引用说明](../../../docs/HISTORY_LIBRARY.md) · [规范化规则](../../../docs/HISTORY_TEXT_NORMALIZATION.md)

| 书名 | 阅读文本 | 分段记录数 | 索引 |
| --- | --- | ---: | --- |
| 史记 | [规范化TXT](shiji/reading.txt) | 7990 | [卷界与段落](shiji/index.json) |
| 汉书 | [规范化TXT](hanshu/reading.txt) | 10037 | [卷界与段落](hanshu/index.json) |
| 后汉书 | [规范化TXT](hou-hanshu/reading.txt) | 16139 | [卷界与段落](hou-hanshu/index.json) |
| 三国志 | [规范化TXT](sanguozhi/reading.txt) | 3525 | [卷界与段落](sanguozhi/index.json) |
| 晋书 | [规范化TXT](jinshu/reading.txt) | 12027 | [卷界与段落](jinshu/index.json) |
| 宋书 | [规范化TXT](songshu/reading.txt) | 13606 | [卷界与段落](songshu/index.json) |
| 南齐书 | [规范化TXT](nan-qishu/reading.txt) | 5040 | [卷界与段落](nan-qishu/index.json) |
| 梁书 | [规范化TXT](liangshu/reading.txt) | 2989 | [卷界与段落](liangshu/index.json) |
| 陈书 | [规范化TXT](chenshu/reading.txt) | 2260 | [卷界与段落](chenshu/index.json) |
| 魏书 | [规范化TXT](weishu/reading.txt) | 16031 | [卷界与段落](weishu/index.json) |
| 北齐书 | [规范化TXT](bei-qishu/reading.txt) | 1966 | [卷界与段落](bei-qishu/index.json) |
| 周书 | [规范化TXT](zhoushu/reading.txt) | 4135 | [卷界与段落](zhoushu/index.json) |
| 隋书 | [规范化TXT](suishu/reading.txt) | 11096 | [卷界与段落](suishu/index.json) |
| 南史 | [规范化TXT](nanshi/reading.txt) | 8270 | [卷界与段落](nanshi/index.json) |
| 北史 | [规范化TXT](beishi/reading.txt) | 8548 | [卷界与段落](beishi/index.json) |
| 旧唐书 | [规范化TXT](jiu-tangshu/reading.txt) | 21603 | [卷界与段落](jiu-tangshu/index.json) |
| 新唐书 | [规范化TXT](xin-tangshu/reading.txt) | 35967 | [卷界与段落](xin-tangshu/index.json) |
| 旧五代史 | [规范化TXT](jiu-wudaishi/reading.txt) | 3988 | [卷界与段落](jiu-wudaishi/index.json) |
| 新五代史 | [规范化TXT](xin-wudaishi/reading.txt) | 3689 | [卷界与段落](xin-wudaishi/index.json) |
| 宋史 | [规范化TXT](songshi/reading.txt) | 76468 | [卷界与段落](songshi/index.json) |
| 辽史 | [规范化TXT](liaoshi/reading.txt) | 6107 | [卷界与段落](liaoshi/index.json) |
| 金史 | [规范化TXT](jinshi/reading.txt) | 9381 | [卷界与段落](jinshi/index.json) |
| 元史 | [规范化TXT](yuanshi/reading.txt) | 23642 | [卷界与段落](yuanshi/index.json) |
| 明史 | [规范化TXT](mingshi/reading.txt) | 35498 | [卷界与段落](mingshi/index.json) |
| 清史稿 | [规范化TXT](qing-shigao/reading.txt) | 37062 | [卷界与段落](qing-shigao/index.json) |
| 资治通鉴 | [规范化TXT](zizhi-tongjian/reading.txt) | 3497 | [卷界与段落](zizhi-tongjian/index.json) |
