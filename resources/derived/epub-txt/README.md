# EPUB 转换文本


二十四史及《清史稿》全部转换为 UTF-8 TXT；原 EPUB、旧 TXT、PDF及已补卷版本归入 originals/twenty-four-histories/backup。分段和检索统一见 ../history-library/README.md。


保留繁体原字、标点、卷内题名和注文；按卷号及上下分部排序。正文缺表、外部子页、私用字和图片待核见各书 issues.json，不自动补写。网页题名栏中的补配标识保留，不视作原作者原本。卷前目录、序文与附录保留并独立标记。


每书 sections.json 提供全文的卷界偏移，不额外复制逐卷TXT。paragraphs.jsonl.gz 提供原 XHTML 元素路径、全文行号、字符区间和片段哈希；excluded.json.gz、restored-variants.json.gz 保存移出与还原记录。Gzip采用标准UTF-8 JSON/JSONL，可用Python gzip读取。表格的 rowspan/colspan 须回查原 XHTML。


重建：`python3 scripts/prepare-history-epubs.py`；校验：`python3 scripts/test-history-epubs.py`。


| 书名 | 全文 TXT | 分卷与审计 |
| --- | --- | --- |
| 史记 | [全文](../../originals/twenty-four-histories/01史记-EPUB全文.txt) | [分卷](01史记/sections.json) · [异常](01史记/issues.json) |
| 汉书 | [全文](../../originals/twenty-four-histories/02汉书-EPUB全文.txt) | [分卷](02汉书/sections.json) · [异常](02汉书/issues.json) |
| 后汉书 | [全文](../../originals/twenty-four-histories/03后汉书-EPUB全文.txt) | [分卷](03后汉书/sections.json) · [异常](03后汉书/issues.json) |
| 三国志 | [全文](../../originals/twenty-four-histories/04三国志-EPUB全文.txt) | [分卷](04三国志/sections.json) · [异常](04三国志/issues.json) |
| 晋书 | [全文](../../originals/twenty-four-histories/05晋书-EPUB全文.txt) | [分卷](05晋书/sections.json) · [异常](05晋书/issues.json) |
| 宋书 | [全文](../../originals/twenty-four-histories/06宋书-EPUB全文.txt) | [分卷](06宋书/sections.json) · [异常](06宋书/issues.json) |
| 南齐书 | [全文](../../originals/twenty-four-histories/07南齐书-EPUB全文.txt) | [分卷](07南齐书/sections.json) · [异常](07南齐书/issues.json) |
| 梁书 | [全文](../../originals/twenty-four-histories/08梁书-EPUB全文.txt) | [分卷](08梁书/sections.json) · [异常](08梁书/issues.json) |
| 陈书 | [全文](../../originals/twenty-four-histories/09陈书-EPUB全文.txt) | [分卷](09陈书/sections.json) · [异常](09陈书/issues.json) |
| 魏书 | [全文](../../originals/twenty-four-histories/10魏书-EPUB全文.txt) | [分卷](10魏书/sections.json) · [异常](10魏书/issues.json) |
| 北齐书 | [全文](../../originals/twenty-four-histories/11北齐书-EPUB全文.txt) | [分卷](11北齐书/sections.json) · [异常](11北齐书/issues.json) |
| 周书 | [全文](../../originals/twenty-four-histories/12周书-EPUB全文.txt) | [分卷](12周书/sections.json) · [异常](12周书/issues.json) |
| 隋书 | [全文](../../originals/twenty-four-histories/13隋书-EPUB全文.txt) | [分卷](13隋书/sections.json) · [异常](13隋书/issues.json) |
| 南史 | [全文](../../originals/twenty-four-histories/14南史-EPUB全文.txt) | [分卷](14南史/sections.json) · [异常](14南史/issues.json) |
| 北史 | [全文](../../originals/twenty-four-histories/15北史-EPUB全文.txt) | [分卷](15北史/sections.json) · [异常](15北史/issues.json) |
| 旧唐书 | [全文](../../originals/twenty-four-histories/16旧唐书-EPUB全文.txt) | [分卷](16旧唐书/sections.json) · [异常](16旧唐书/issues.json) |
| 新唐书 | [全文](../../originals/twenty-four-histories/17新唐书-EPUB全文.txt) | [分卷](17新唐书/sections.json) · [异常](17新唐书/issues.json) |
| 旧五代史 | [全文](../../originals/twenty-four-histories/18旧五代史-EPUB全文.txt) | [分卷](18旧五代史/sections.json) · [异常](18旧五代史/issues.json) |
| 新五代史 | [全文](../../originals/twenty-four-histories/19新五代史-EPUB全文.txt) | [分卷](19新五代史/sections.json) · [异常](19新五代史/issues.json) |
| 宋史 | [全文](../../originals/twenty-four-histories/20宋史-EPUB全文.txt) | [分卷](20宋史/sections.json) · [异常](20宋史/issues.json) |
| 辽史 | [全文](../../originals/twenty-four-histories/21辽史-EPUB全文.txt) | [分卷](21辽史/sections.json) · [异常](21辽史/issues.json) |
| 金史 | [全文](../../originals/twenty-four-histories/22金史-EPUB全文.txt) | [分卷](22金史/sections.json) · [异常](22金史/issues.json) |
| 元史 | [全文](../../originals/twenty-four-histories/23元史-EPUB全文.txt) | [分卷](23元史/sections.json) · [异常](23元史/issues.json) |
| 明史 | [全文](../../originals/twenty-four-histories/24明史-EPUB全文.txt) | [分卷](24明史/sections.json) · [异常](24明史/issues.json) |
| 清史稿 | [全文](../../originals/twenty-four-histories/25清史稿-EPUB全文.txt) | [分卷](25清史稿/sections.json) · [异常](25清史稿/issues.json) |
