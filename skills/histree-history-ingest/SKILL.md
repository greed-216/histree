---
name: histree-history-ingest
description: 按《资治通鉴》编年顺序录入 Histree 历史人物、事件、关系和原文出处，并将其他史书作为补证。用于新增或修订 content 中的历史批次、出处索引和进度；不用于普通界面或部署任务。
---

# Histree 史料录入

以书、卷、年、**连续原文段落**为工作单元。主线为《资治通鉴》；人物、事件和关系是跨书共享实体。开始前看仓库根目录 `AGENTS.md`、`content/yearly-progress.json` 的 `active_cursor`、对应卷年的 `paragraphs.json`，从 `next_paragraph` 开始。可以按可审核的段数分批，不要越过未处理段落。卷末接下一卷；只有该年所跨各卷全部段落处理并发布后，才记整年完成。

新批次置于 `content/books/zizhi-tongjian/vol-{卷}/year-{年}/part-{序号}/`。旧目录 `content/later-liang-907-923/`、`content/year-0907/`、`content/late-tang-zhu-wen-early/` 是发布档案，保留其稳定 key、UUID 和固定引用。可参考 `content/books/zizhi-tongjian/vol-255/year-0884/part-02/` 的结构；示例中的卷、年、段号和人物不应照搬。

## 整理与校核

1. 每段保留稳定段落 ID、源文件行号、原文、处理状态、事件 key 和必要的编校备注。一段可拆多个事件；各地记载均按顺序处理。追叙、`初`、`久之`、`后月余`不直接认作该年发生。未知年份用 `null`，保留原纪年，不自行换算月日。地点先写史载名称；坐标需另有证据。
2. 在 `content-batch.json` 为人物、事件、参与和关系使用全站稳定 key。查已有批次、别名、异体字和关系端点，复用同一人。只建原文明示的关系，限定其适用时期；同场出现不能推成盟友或因果。
3. 每条事实引用指定 source、主体、字段、卷年段落和可在 `sources/` 快照逐字找到的摘录。`note` 用 `原文：…；核对说明：…`。`sources/manifest.json` 记录 SHA-256、电子底本及变换；出处 URL 指向仓库固定提交。新采集的来源先提交原文快照，得到固定提交哈希后再生成 source URL 和发布批次。原文中的讹字或异文保留并注明，不悄悄改字。纸本未核就注明。
4. 其他书证保留独立 source 和原文；在 `coverage.json.supplements` 登记对应的《通鉴》段落、同一实体，以及印证、补充或异说。冲突并列保留，不覆盖主书说法；相互依赖的书证不算独立确证。

具体判例见 [史料校核参考](references/editorial.md)。批次字段说明在 `docs/DATA_PREPARATION.md`。

## 校验、发布与交接

- 运行 `python3 scripts/validate-content-batch.py <批次>/content-batch.json`；用 `python3 scripts/prepare-book-import.py <批次>/content-batch.json` 生成 UUID 映射与排除复用对象的 SQL；运行 `python3 scripts/publish-book-batch.py <批次>/content-batch.json` 做**只读预检**。结构检查不替代逐段人工核对。
- 当前任务已授权发布时，发布命令加 `--apply`。确认 `publication.json` 的批次哈希、匿名读回和引用可见，才把段落记为 `published_verified`；运行 `python3 scripts/index-book-claims.py` 更新书目索引，再把 `active_cursor` 移到下一段。发布前保持 `reviewed` 或 `pending`。
- 交接时提交本批内容、来源快照、manifest、coverage、校验和发布审计、段落账本及进度，并写清下一段位置和待考问题。只暂存本次文件，保留他人工作区修改。

发布异常处理见 [发布参考](references/publication.md)。服务端环境文件和密钥不得入库。发布脚本的多次 REST 写入没有整批事务；遇到冲突或中断先核对线上状态及审计，不直接执行通用下架 SQL。
