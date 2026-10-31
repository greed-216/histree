# 批次发布与交接

新增批次按[工作台流程](workbench.md)准备与审阅，史实保存在 `curation.json`，不再为新批次编写专用生成脚本。以下命令在仓库根目录运行，`<批次>` 是本书当前工作线下的实际批次目录。

线上已于 2026-10-10 切换为 MySQL。发布器及别名、关系修订工具默认使用 MySQL，默认仍只读；连接凭据在被 Git 忽略的 `.env.migration.local`，匿名读回默认走 `https://123.56.189.146/api/v1`。其他部署可显式指定 `--mysql-env`、`--public-api-url`。保留旧 Supabase 数据与 `publication.json`，MySQL 发布使用独立的 `publication-mysql.json`，不重建历史批次或原发布审计。只有明确操作旧库时才指定 `--backend supabase`。

站内原文读取使用独立的 MySQL `source_text` 表。发布器预检同时检查固定原文快照；`--apply` 在任何批次写入前要求该表已迁移，缺表时停止，不自动建表。新批次在草稿验证后、公开前写入原文，并在最终匿名读回核验正文；已有批次用独立回填流程，不重写旧发布档案。迁移、回填和本地预览见[站内原文阅读](../../../docs/SOURCE_READING.md)，其中上线步骤仅在获得对应授权后执行。

## 归档、绑定与预检

发布前先归档新快照，并确认归档提交已推送到当前项目的受信任远端。只归档本次相关文件，不顺带推送其他工作线或未授权提交；需要独立来源分支时，以已核对的远端现有提交为父提交，保留其他工作区改动。授权发布包含使本批出处可回查的必要归档操作，不要求用户对相同范围反复确认。

```sh
python3 scripts/history-batch-workbench.py link-sources '<批次>' --commit '<完整归档提交SHA>'
python3 scripts/history-batch-workbench.py build '<批次>'
python3 scripts/prepare-book-import.py '<批次>/content-batch.json'
python3 scripts/publish-book-batch.py '<批次>/content-batch.json'
```

如果快照在提交中的目录与本地目录不同，给 `link-sources` 加 `--archive-prefix '<仓库相对sources目录>'`。该命令仅检查本地Git归档blob与快照哈希、更新manifest链接，不执行提交、推送或发布。失败不部分改写链接，已开始发布的批次拒绝重绑。绑定后重新build，确保生成source与manifest使用同一固定URL；再匿名访问固定链接并核对内容哈希，不能把本地Git存在当作远端可访问。

存在身份或解释待考时，保留原稿与暂缓记录，在独立发布目录准备已校核事实子集。未核人物不建成确定节点，未核亲属不建立确定连接；必要时保留以“本书记载”为范围的叙述，不发布其未证实身份对应。语义上无法隔离的问题暂缓整条事实，不只删除待考标签。

已有旧格式未发布批次继续使用原生成器，保持来源、ID和账本，不迁移既有发布档案：

```bash
python3 <批次>/build_batch.py
python3 scripts/validate-content-batch.py <批次>/content-batch.json
python3 scripts/prepare-book-import.py <批次>/content-batch.json
python3 scripts/publish-book-batch.py <批次>/content-batch.json
```

新书首次录入前检查现有工具支持：`index-book-claims.py` 使用显式书目key与来源前缀映射，新书尚未接入时先补齐映射并验证。当前发布器不支持专题发布，不能将工具未支持的内容假造为其他类型绕过校验。

尚未归档来源时不要发布引用。审查生成的 batch 和 coverage，确认段落连续、下一段正确、复用 key 列入 `reused-keys.json`，并查看只读预检的新增与复用数量。校核主语、行动、前后次序、地点和摘录支持范围。勿直接使用通用 `scripts/prepare-content-import.py` 生成的发布/撤回 SQL；`prepare-book-import.py` 才会排除复用对象。

当前任务已授权上线时执行：

```bash
python3 scripts/publish-book-batch.py <批次>/content-batch.json --apply
```

多批有复用关系时按依赖顺序发布，前批公开核验后再发布后批。检查本次 MySQL 审计 `publication-mysql.json` 的 `batch_sha256` 与批次文件匹配，`verified: true`，`public_counts` 完整；旧 Supabase 的 `publication.json` 保留。脚本先插草稿、再逐表公开，最后通过匿名 HTTP 分块读回；分阶段写入不具整批原子性。中断后先看 `stages`、线上记录和来源，恢复缺失阶段，不能修改已开始发布的batch以绕过哈希守卫。若已有 key 内容不同，或姓名别名、关系端点冲突，停止并校核身份，不关闭守卫。

公开读回后检查实际网站的正文、人物关联、原文展开与固定出处；跨多批时覆盖首、中、末代表条目。仅状态接口或数据库写入成功不足以证明读者可用。

更新本书当前工作线的段落账本、最后已发布段、下一段、卷/篇章覆盖和批次路径，具体路径见[资料目录与定位](source-library.md)。全部事实校核完成且公开核验的段落用 `published_verified`；只上线明确事实子集用 `published_fact_subset_verified`，工作线可用 `published_fact_subset_verified_with_deferred_identity` 并保留暂缓队列，不标卷、篇章或年全部完成。其他书与旧工作线保持原状态。

确认书目key与来源前缀受索引脚本支持后，只更新本书：`python3 scripts/index-book-claims.py --book '<索引book_key>'`；新书未支持时先适配验证。整卷发布前保留工作台覆盖审计；发布后核对各批最终哈希和匿名读回，在独立汇总审计中记录公开数量与待考项，不重建已发布batch。如需问答验收，选本批具体问题并核对回答与出处；问答成功不替代史料审核。

提交时只暂存本批及必要索引和进度，避免其他人的未提交修改或 `apps/api/.env`。在交接说明写明发布段落范围、待考点、下一段和本次卷/篇章（编年体另含年）是否完成。

遇到已核验同人合并，先读修订plan及其发布审计，复用规范主体key/UUID，不重新激活隐藏的重复主体。当前预检如不支持该档案状态，先适配并验证这个具体场景，不凭文档假定存在身份守卫例外，也不关闭普通重名和关系端点检查。

## 新来源补充已发布段落

新来源可以补证旧段落，无需重写旧批次。在当前书的 `coverage.json.supplements` 中填写原段落ID与主体key，并在 `cross_volume_supplements` 显式声明同一段落与主体。发布脚本要求旧段落已公开核验、旧批次哈希与发布审计相符、原coverage包含该段落、补证主体存在于旧批次；这类补证不计入当前连续正文段落覆盖，也不要求其他书独立新增的引文走该补证路径。

## 修订已发布资料的进度

必要补证尚无可公开source时，可准备明确标为“仅补证来源”的工作台包，归档后保持people/events/关系/参与/claims/topics全空。标准发布器显式加 `--source-only-evidence`，只发布source及全部固定原文；年代/出处侧表工具依据相同已验模式写原文定位，不制造占位事实，不推进任何书卷进度。随后独立修订才能引用这些source。该模式不能用于隐藏尚未校核的事实，已有事实的批次会拒绝。

发布后发现文案、身份、关系、引用或年份问题，在 `content/revisions/` 单独保存 `kind=reviewed_history_correction` 计划；保留原batch、固定快照、稳定ID和历史审计。使用 `scripts/history_revision.py`，默认只读核对，不通过重建旧批次覆盖已发资料。

计划绑定目标 `target_fingerprint`、相对资料根的 `protected_paths` SHA-256、逐字 `source_bindings`、所有更新行的完整 `full_before` 及仅含改动字段的 `before/after`。需要新增的行放入 `inserts`，来源/原文/定位行列入只读 `protected_rows`；需要保护引用集合时使用 `membership_guards` 和对应的 `invariants_after`。不能修改主键或 `created_at`，同一行不能重复列为更新或新增。新人物的逻辑key写在 `new_people` 元数据，数据库行沿用实际列；不把目录key写成数据库字段。历史年份不使用零年；若已有旧行含零年，先报告工具拒绝，不删改旧值守卫以强行执行。

```sh
python3 scripts/history_revision.py '<修订>/plan.json' --root '<资料根>' --mysql-env '<明确环境文件>'
python3 scripts/history_revision.py '<修订>/plan.json' --root '<资料根>' --mysql-env '<明确环境文件>' --apply --expected-plan-sha256 '<计划文件精确SHA-256>'
python3 scripts/history_revision.py '<修订>/plan.json' --root '<资料根>' --mysql-env '<明确环境文件>' --verify-db
```

只有当前任务已授权修订写入时才执行 `--apply`。工具核对实际schema和目标后，持有统一 `histree-content-publish` 锁，在单一事务内以锁定读执行完整行CAS、固定表新增和逐字段更新，再核对全部更新后的整行、非改字段、新增行及引用集合；任一旧值、原文字节、定位或后置条件冲突均回滚。已有新ID或旧收据不自动跳过或恢复；并发变化必须重新审阅。仅允许8张事实/侧表的INSERT/UPDATE，source、source_text和原文库定位只读保护，不执行DELETE或DDL。

默认收据为修订目录 `publication-mysql.json`，可用 `--receipt` 显式指定。收据绑定计划SHA、目标、计数、新人物元数据和提交后的完整行，状态只为 `committed_pending_anonymous`；`--verify-db` 只读确认数据库after状态，不代表公开核验。随后独立匿名逐项检查主体、参与/关系方向、claim、年代及原文双向定位，再做实际网页/UI验收。数据库提交、匿名API读回和网页验收分别留证，全部完成后才将本修订标为verified；工具不会自动更新书卷进度。

旧数据审阅与新增录入使用独立游标。续接既有文案修订时读取该修订目录实际存在的progress及字段审阅位置，记录改写或保留理由，经旧值守卫和独立匿名读回后才标完成。审阅范围以当前任务为准，不在Skill中固定修订日期或停留年份；不覆盖旧批次或历史审计，不把修订进度计入另一书的连续录入进度。

## 时间校核验收

新批次必须有绑定批次哈希的逐事件时间审计；先在统一草稿填好时间判断，再用 `validate-history-time.py --from-curation` 生成并验证。无统一草稿的旧格式新批次直接准备同格式审计。发布器在首次发布前检查，已有已核验发布档案保持兼容。详见[时间校核](time-review.md)。写入后核验年份、范围精度、异说和对应画卷，不以原文通读覆盖或网页可打开代替年代验收。
