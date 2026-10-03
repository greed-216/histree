---
name: histree-history-ingest
description: 按《资治通鉴》编年顺序录入 Histree 历史人物、事件、关系和原文出处，并将其他史书作为补证。用于新增或修订 content 中的历史批次、出处索引和进度；不用于普通界面或部署任务。
---

# Histree 史料录入

当前阶段按用户决定，以《资治通鉴》和二十四史构建基础数据面；《清史稿》和其他专门史籍暂缓新增，既有发布出处保留。范围见 `resources/catalog/ingestion-source-scope.json`。二十四史分段检索入口为 `resources/derived/history-library/README.md`，用 `scripts/search-history-library.py` 查关键词、段落ID与来源定位；自动分段、卷界和完整性不等于人工校核通过。

二十四史及清史稿统一选用 `resources/originals/twenty-four-histories/*-EPUB全文.txt`，其他来源版本在 `backup/`。新分段文件为每书 `paragraphs.jsonl.gz`，阅读文本为 `reading.txt`；原EPUB及转换审计可回查。清史稿仅本地规范化，不改变既定录入范围。旧 `readable`、`readable-txt`、`corrected-txt` 等处理产物已清理，勿使用已归档的旧脚本重新产生多套数据。

首次克隆或检索缓存缺失、过期时，运行 `python3 scripts/build-history-library.py --rebuild-search`，从版本化分段记录重建本地SQLite，不重新转换底本或改写段落ID。检索、阅读、逐字导出及来源问题检查按 [分段检索与引用参考](references/source-library.md) 操作。录入引用用导出的原TXT片段；`reading.txt`和搜索摘要仅供查阅，不直接作为原文快照。

以书、卷、年、**连续原文段落**为工作单元。主线为《资治通鉴》；人物、事件和关系是跨书共享实体。开始前看仓库根目录 `AGENTS.md`、`content/yearly-progress.json` 的 `active_cursor`、对应卷年的 `paragraphs.json`，从 `next_paragraph` 开始。可以按可审核的段数分批，不要越过未处理段落。卷末接下一卷；只有该年所跨各卷全部段落处理并发布后，才记整年完成。

新批次置于 `content/books/zizhi-tongjian/vol-{卷}/year-{年}/part-{序号}/`。旧目录 `content/later-liang-907-923/`、`content/year-0907/`、`content/late-tang-zhu-wen-early/` 是发布档案，保留其稳定 key、UUID 和固定引用。可参考 `content/books/zizhi-tongjian/vol-255/year-0884/part-02/` 的结构；示例中的卷、年、段号和人物不应照搬。

## 整理与校核

1. 每段保留稳定段落 ID、源文件行号、原文、处理状态、事件 key 和必要的编校备注。一段可拆多个事件；各地记载均按顺序处理。追叙、`初`、`久之`、`后月余`不直接认作该年发生。未知年份用 `null`，保留原纪年，不自行换算月日。地点先写史载名称；坐标需另有证据。
   年界须查看相邻原文行。自动账本可能把下一年的帝纪标题或分隔符算入上年；核实后保留原 ID、原字与行号，标 `kind: section_heading` 或 `separator`、`status: excluded_non_body_verified`，事件列表为空，不生成事实引用。在 `boundaries.json` 登记排除原因，正文统计扣除结构项；既有源快照和原始文本不改写。年度完成审计分别统计已发布正文与已核结构项，不把标题误当史事，也不将尚待录入正文标完成。
2. 在 `content-batch.json` 为人物、事件、参与和关系使用全站稳定 key。查已有批次、别名、异体字和关系端点，复用同一人。复用人物前同时检查 `content/revisions/` 已应用的同人合并记录，按其 `canonical_key`/UUID 复用，不重新启用已隐藏的重复主体；历史批次中的旧 key 保持原档案不改。只建原文明示的关系，限定其适用时期；同场出现不能推成盟友或因果。人物关系统一为 `A —关系→ B` 表示“A是B的该关系”。原文明示长幼时用兄长／弟弟，父子／母子写具体父亲／母亲；未明示长幼的兄弟、姻亲、结义等保留对称关系。反向阅读不另建重复关系，性别未知时用子女。复用旧关系前检查 `content/revisions/` 的修正记录，按修正后的端点和类型识别同一关系，保留原 key/UUID。
   史料兼有繁体和简体。检索同一人物或地名时两种字形都要回查；录入主体名称与本站已有规范统一，繁简形式放入别名或校核说明，不因字形不同新建实体。`sources/source.txt`、逐字摘录及定位保持底本原字；繁简转换仅用于规范化展示和实体匹配。疑似讹字、避讳字、异名须另作校核，不能靠自动转换合并。
3. 每条事实引用指定 source、主体、字段、卷年段落和可在 `sources/` 快照逐字找到的摘录。`note` 用 `原文：…；核对说明：…`。`sources/manifest.json` 记录 SHA-256、电子底本及变换；出处 URL 指向仓库固定提交。新采集的来源先提交原文快照，得到固定提交哈希后再生成 source URL 和发布批次。原文中的讹字或异文保留并注明，不悄悄改字。纸本未核就注明。
4. 其他书证保留独立 source 和原文；在 `coverage.json.supplements` 登记对应的《通鉴》段落、同一实体，以及印证、补充或异说。冲突并列保留，不覆盖主书说法；相互依赖的书证不算独立确证。

具体判例见 [史料校核参考](references/editorial.md)。批次字段说明在 `docs/DATA_PREPARATION.md`。

新增人物关系不使用“父子”“母子”“统属”等含糊标签，填写 A 相对于 B 的具体身份。未发布批次的 `prepare-book-import.py` 会拒绝这些新增类型，并检查复用关系是否符合已存的方向修正；若报错，应修正新批次中的端点和类型，保留原 key/UUID，不改写已发布档案。

## 校验、发布与交接

- 运行 `python3 scripts/validate-content-batch.py <批次>/content-batch.json`；用 `python3 scripts/prepare-book-import.py <批次>/content-batch.json` 生成 UUID 映射与排除复用对象的 SQL；运行 `python3 scripts/publish-book-batch.py <批次>/content-batch.json` 做**只读预检**。结构检查不替代逐段人工核对。
- 当前任务已授权发布时，发布命令加 `--apply`。确认 `publication.json` 的批次哈希、匿名读回和引用可见，才把段落记为 `published_verified`；运行 `python3 scripts/index-book-claims.py` 更新书目索引，再把 `active_cursor` 移到下一段。发布前保持 `reviewed` 或 `pending`。
- 交接时提交本批内容、来源快照、manifest、coverage、校验和发布审计、段落账本及进度，并写清下一段位置和待考问题。只暂存本次文件，保留他人工作区修改。

发布异常处理见 [发布参考](references/publication.md)。服务端环境文件和密钥不得入库。发布脚本的多次 REST 写入没有整批事务；遇到冲突或中断先核对线上状态及审计，不直接执行通用下架 SQL。
