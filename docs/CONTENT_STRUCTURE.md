# 内容结构与后端模块边界

本次保留三个 workspace 包和单体部署。原有稳定人物、事件、关系、来源 ID 与档案继续使用。数据库增量迁移、侧表回填和应用部署是分别执行的步骤；应用启动不创建表或改写历史资料。

## 实际模块

| 层 | 文件 / 职责 |
| --- | --- |
| 数据库基础 | `mysql-database.ts`：连接池、绑定参数、事务连接、超时、连接释放 |
| 公共读取边界 | `query-contracts.ts`：公开状态与关系端点可见性；`storage-port.ts`：最小存储能力接口 |
| 领域存储 | `content-repository.ts`、`graph-repository.ts`、`search-repository.ts`、`timeline-repository.ts`、`source-repository.ts` |
| 业务写入 | `game-repository.ts`、`quota-repository.ts`、`feedback-repository.ts`，保留原并发与事务契约 |
| 新内容结构 | `structure-repository.ts`：证据、身份说明与年代侧表读取；`person-directory.ts`：筛选与游标 |
| 缓存 | `revision-cache.ts`：小容量、合并并发、失败不入缓存；资料修改事务同时更新版本 |
| 兼容门面 | `MysqlService` 保留现有调用和受限 fluent 查询，不再承担各领域的 SQL 实现 |

领域存储只依赖声明的读／写端口；不依赖 Nest 控制器、模型运行器或兼容门面。web 通过共享类型消费新增字段，旧的 note、description、起止年份仍保留。

## 证据与身份

新增 `claim_structure` 是原 note 的无损拆分，保存原 note SHA-256。只有哈希仍相同时才使用结构化值；不匹配就回读旧字段。不能识别的格式保留为 unparsed，不标成校核完成。recorded 表示格式拆分成功，不能据此推定史实或身份已经无争议；待考说明仍保留为 deferred。

书、底本版本、卷章和段落从已经核对的 library_source_link 映射获取，不根据标题或近似文本猜测。来源 URL、存档哈希、当前公开事实及关系端点同时检查。人物简介采用保守规则拆出明确的身份审校句，原 description 不改；无法明确拆分的句子保持原样。目录与详情都提供可展开的待考说明。

## 年代

`event.start_year/end_year` 继续表达已有事件时间。新增 `event_dating` 独立表达界限、精度、时代、原文依据及审核状态，可保存多个不同说法。它不延长事件持续区间，也不把估计范围的第一年当作发生年。

- year：已校核到同一年；approximate/range：上下界；relative：可以只有一侧界限；era：仅知时代；unknown：不主张年份。
- 0年、反向范围、没有依据或引用的记录拒绝导入。proposed 不进入公开筛选。
- 公开读取只接受 reviewed 且原事件及所引事实仍可公开的记录。
- `dating=dated|undated|estimated` 和 `era` 可用于事件目录；估计范围按界限相交筛选。原来未知的年份仍为 null，年度概览不把估计值算成确年。
- 自动升级不从卷年标题、生卒年或任官年批量猜事件发生年。具体推定必须有逐条审核的日期计划。

## 覆盖与段落回链

`project-review-coverage.py` 从当前目录、逐段审计和匹配批次哈希的发布证明投影，默认只输出文件。兼容现代 published-paragraphs 和旧 paragraphs / workbench 审计。pending_textual_review 表示已经通读但尚有待考，不抹除其已发布事实子集；已发布段数与待考段数可重叠。缺失证明、底本不匹配和无法唯一关联的审计列入 skipped，不能按书末游标直接填满进度。

`library_review_coverage` 按书、底本版本、卷记录历史校核与发布验收；`library_paragraph_review` 保存逐段处理结果及原文哈希。API 仅展示当前底本、当前段落哈希相符的投影。未同步不等于未读，通读也不表示穷尽全部潜在事实。

连续原文阅读器按需查询段落关联的公开事实，引用、人物或事件可以回链。现有固定快照保持独立；没有唯一正文映射的旧出处继续用原片段阅读。

## 查询与缓存

`/timeline/overview?compact=1` 只读计数与年份分布；`/timeline/highlights?year=` 按需读取年度选例。原 overview/RPC 契约保留。前端悬停请求防抖，并避免使用上一年的选例冒充当前年。搜索详情和来源加载按类型批量读取。原文字面 LIKE 匹配保持不变，不把分词命中冒充逐字匹配。

人物目录提供时代、所属、已核来源书籍、年代信息及排序；默认按已知年代，最近录入是独立选项。游标绑定筛选、排序和资料版本；资料修改后旧游标返回409，避免静默漏项。对旧页码客户端保留兼容。

显式迁移中的触发器让现有发布器与修订器的修改自动更新 content_revision，不要求发布器认识新字段。副作用仅是版本计数，不修改历史业务字段；部署前应在隔离库测量目标批量写入开销。没有新迁移的旧库保持短TTL兼容，新增表功能在迁移后生效。

## 导读

时期编年路径使用统一组件与配置，并明确标为已录入条目；不会把自动列表称为编辑精选。原后周编辑导读与引用保留；人物导读文案移至 person-guides.json。新时期共用时期总览、史事、依据和人物／原文入口，实际叙事仍需独立编审。

## 验证与上线顺序

1. `pnpm build && pnpm lint && pnpm test`，以及 CI 的隔离 MySQL、历史导入与实际 Linux 镜像验证。
2. `pnpm schema:plan` 查看唯一有序清单。`node scripts/mysql-schema.mjs --bootstrap-test` 只接受本机、空的 histree_test_* 库，不接受生产库。
3. 在隔离库运行 `pnpm test:mysql`：新原文库全链路使用小型合成样本及真实 Nest HTTP，无付费模型。生产规模验证单独使用 `test-library-mysql.mjs --expected-manifest`，不再把旧总数写进合约测试。
4. 对现有库独立预检并执行 `005-content-structure.sql`；它依赖清单中此前所有基线和原文库迁移。DDL 不能按事务回滚，不能重放初始化基线；失败须先核对实际已执行语句，不盲目重跑。
5. 准备并审核侧表计划。覆盖投影不改旧账本；证据按500条分块、按最后ID续跑。日期计划必须逐条给出依据。

```sh
python3 scripts/project-review-coverage.py --source-root <含完整审计的仓库> --output /private/tmp/coverage.json
node scripts/upgrade-content-structure.mjs --mysql-env <私密文件> --coverage-plan /private/tmp/coverage.json --output /private/tmp/structure.json
# 可追加 --dating-plan <已审核日期JSON数组>、--after <上组最后ID>、--limit <1到5000>
# --apply 必须同时指定 --plan 和精确 --expected-sha256；目标指纹、旧note和底本均重新核对。
```

6. 先迁移和回填，再部署应用；核对目录筛选、待考说明、确年与推定范围、引用高亮、段落回链、缓存版本和深链接。原文快照哈希、匿名读取及旧应用的兼容性都应保留。
