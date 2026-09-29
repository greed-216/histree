# 历史史料资料库

采集日期：2026-09-29。本目录是研究资料库；内容尚未经过史实审阅，不直接作为网站已发布数据。

## 从哪里开始

- [采集与质量报告](COLLECTION_REPORT.md)：下载结果、版本限制和未完成事项。
- [按时代检索](PERIOD_INDEX.md)：先定位时代和书目，再定位卷次。
- [按规范做数据](PROCESSING.md)：原文到人物、事件、关系与引用的流程。
- `catalog/`：来源网址、固定版本、SHA-256、页数和卷目索引。
- `originals/twenty-four-histories/`：用户指定 GitHub 仓库的24个PDF，保留原文件。
- `originals/kanripo/`：汉籍仓库补充文本、版本说明和下载归档。
- `originals/supplements/`：维基文库原始API响应与文本、Project Gutenberg文本。维基文库未齐卷的副本不作为整书完成件。
- `derived/tongjian/`：用户TXT的294个分卷副本，卷次及年份见 `catalog/tongjian-volumes.json`。
- `derived/twenty-four-histories/`：《旧五代史》《新五代史》按PDF页提取的JSONL，每行有 `pdf_page` 与 `text`。

用户提供的《资治通鉴》TXT保留在本目录原位置，未改写。下载资料与派生全文保留在本地，不放入前端公共资源或Git发布包；脚本、来源清单和整理规范可以版本管理。

## 来源入口

- 二十四史：https://github.com/LeungGeorge/grimoire-kindle/tree/main/kindle_free_books/二十四史/PDF
- 汉籍仓库：https://github.com/kanripo
- 五代史补：https://zh.wikisource.org/wiki/五代史補_(四庫全書本)
- 北梦琐言：https://www.gutenberg.org/ebooks/25173

PDF文件完整下载不等于底本可靠、原书完整或已完成校勘。电子文本、PDF页号和古籍原版叶码应分别记录。
