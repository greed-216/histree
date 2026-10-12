> 本文是 2026-10-10 切换记录，保留当时步骤与证据。当前开发、发布、配置和工具入口以 README、DEPLOYMENT.md 与 ECS README 为准；旧的试迁移命令不属于日常流程。

# Histree 迁移到 RDS MySQL

## 当前生产状态（2026-10-10）

已完成 ECS 正式切换，并修复首次构建误用旧前端源码造成的画卷与导读遗漏。`histree-api` 当前运行镜像 `histree-api:51933b3a65456c11388cadce2330c427db6a1e91413a1614b733246d0e8a8562`，健康状态为 healthy；后端复用已验收的 MySQL 镜像，前端以迁移前实际线上提交 `e42cef86e91d2a54fe61056039b33cc81a3d6159` 恢复。后端为 Node.js v24.21.0 / NestJS / TypeScript，前端为 React / Vite。

运行配置使用 `HISTREE_DATABASE=mysql`、`rm-2zeiv0233csd46w9v.mysql.rds.aliyuncs.com:3306`、数据库 `histree` 及用户提供的账号密码。凭据仅在 ECS 私密环境文件中，新生产容器没有 Supabase 环境变量或旧配额服务密钥。登录与网页管理入口已移除。

最新只读导出和 MySQL 的 8 张业务表、119,774 条记录逐字段散列一致，0 插入、0 更新、0 删除；导出前后单条 PostgreSQL 语句取得的全表记录摘要一致。配额暂停期间再次读回核对，2 条源配额记录已事务同步，替换并私密归档 6 条试验计数。业务记录未再次改写，历史批次及出处保持原样。

Supabase 在核对开始时三个读取通道均超时，经用户明确授权重启后恢复。最终有效归档是 `backups/mysql-migration/2026-10-10-after-restart/` 中的完整 REST 导出、源库前后摘要、完整字段对照计划及部署审计；仍不是包含 auth/storage/roles 的 pg_dump，不把此前失败的原生快照目录当作备份。

切换后的原生实例身份、业务计数和 11 项公开接口验证通过；实际公网 HTTPS 问答 14.8 秒返回 6 条出处，6 条均匿名读回并核对 claim、source 与固定 URL，一次模型请求。公网浏览器事件页正常，登录按钮为 0。匿名准入已恢复，原 nginx 配置与证书保持。验收结果为 `production-ai-validation.json`、`deployment-audit.json` 和 `production-page.jpg`。

旧镜像、旧私密环境配置和 Supabase 数据保留。发布目录为 `/opt/histree/releases/mysql-20261010-32c39237cc42`；第一次切换在替换容器前因 ECS Python 3.6 时间解析失败，自动恢复入口，修复后重新确认三方配额一致才执行成功。后续回滚须先暂停入站并核对切换后的资料和配额变化，再恢复旧环境与镜像；不能直接丢弃 MySQL 上的新写入。

本地发布及别名、关系修订工具默认目标已改为 MySQL，默认仍只读，通过实际公网 API 匿名读回。旧发布审计保留，MySQL 使用单独审计；本次未执行历史资料发布或修改账本。代码与文档修改尚未提交推送；后续 CI 构建需包含实际部署源码及恢复的原前端资源，避免再次从本地旧版本构建。

### 画卷版本修复

首次迁移镜像错误地使用了落后于实际线上版本的本地前端。缺失的不仅是 `/timeline/scroll`，还包括首页画卷、导读、新版交互及已使用匿名会话的 Ask/Guess 客户端。已按原生产提交逐文件恢复：`apps/web/src` 和 `public` 相对该提交仅保留 `App.tsx` 登录/管理移除、`lib/api.ts` API 接入、`lib/aiGateway.ts` 匿名调用三处差异，原画卷与导读数据未重新生成。

修复镜像只替换前端，API、AI worker、内网 MySQL 配置均沿用已验收版本；生产环境文件 SHA-256 在部署前后不变。原始长图 v6 的 SHA-256 为 `04eadb90c98471d1dc08dbd3453bfdbddbe998594e600c202c5c9a6bb208606f`，9360×720；原图、接缝与坐标测试、缩放边界、构建、lint、匿名 AI 客户端模拟、首页/完整长图/导读浏览器验收通过。实际公网首页和完整长图已恢复，无浏览器错误。

当前发布目录 `/opt/histree/releases/mysql-webfix-20261010`，上一 MySQL 版本仍可回滚；修复包 SHA-256 `7927567c47b39d0602a24c58bf6d885eaed655b676b0ceae7f426249f350de17`。替换的 11 份本地前端文件均已先私密备份，未改动其他工作区路径；修复归档见 `backups/mysql-migration/2026-10-10-web-repair/`，含源码恢复清单、构建审计与公网截图。

## 本次范围

迁移至用户提供的 RDS MySQL，取消网站登录与网页管理入口，关闭对应的管理写接口。保留公开阅读、人物、事件、专题、图谱、时间图、证据和 AI 功能。资料仍由本地校核和发布脚本维护。原 Supabase 在切换验收前继续服务并作为回滚来源。

不得重放包含 DROP TABLE 或旧种子数据的 PostgreSQL 历史迁移文件。目标结构由实际线上结构和现行约束单独转换。保留既有 UUID、正文、出处 URL、引用定位、校核说明、草稿与发布状态，迁移不生成新史料、不改变各书账本或发布记录。

## 2026-10-10 首次只读检查

MySQL 账号密码有效，服务端版本为 8.0.36。连接实例成功，连接配置指定的数据库返回 1044：账号无访问权限。该账号看不到任何业务数据库，没有业务表读写或建库授权，不能据此确认实例中所有数据库均为空。

服务端默认字符集为 utf8mb3，时区为 Asia/Shanghai。目标库和表应显式使用 utf8mb4，应用连接显式使用 UTC。SSL 连接尝试返回 1043；常规连接能完成认证。生产连接应核对 ECS 内网地址与 VPC，不把当前公网预检的连接方式直接当成部署配置。

通过 Supabase 服务账号的 REST 接口取得下列精确计数。这些计数逐表读取，不是同一事务内的一致性快照；尚未导出数据或测量数据库实际占用。

| 表 | 记录数 | 迁移方式 |
| --- | ---: | --- |
| person | 3,540 | 保留全部记录与 ID |
| event | 13,794 | 保留未知年代、负数年份与原始时间表达 |
| person_relationship | 1,098 | 保留方向、关系类型和两端 ID |
| person_event | 25,755 | 保留人物、事件及角色 |
| event_causality | 0 | 保留结构与约束 |
| source | 2,413 | 保留完整出处、链接和说明 |
| fact_claim | 73,172 | 保留证据、定位、来源 ID 和状态 |
| topic | 2 | 保留 sections 与节点 ID |
| user_roles | 1 | 用户功能取消后不接入新应用；保存在源备份中 |
| ai_gateway_quota | 4 | 重建原子限额逻辑；核对窗口和全局额度规则 |

线上还暴露 consume_ai_gateway_quota，当前仓库迁移文件没有其实现。正式切换前需读取真实定义，不能根据函数名猜测额度规则。REST 元数据也不覆盖全部数据库对象，最终需要取得可验证的源备份和约束清单。

## 当前所需的 RDS 设置

1. 在实例的数据库管理中创建与 MYSQL_DATABASE 配置相同名字的数据库，字符集选 utf8mb4。若库已存在，仅补授权即可。
2. 在账号管理中给 MYSQL_USER 对该库授予“读写（DDL+DML）”，让迁移程序能建表、建索引、插入和查询。
3. 保留当前连接配置文件。无需再次发送或更改密码；如实际库名不同，只修改 MYSQL_DATABASE。

官方操作说明：[修改普通账号权限](https://help.aliyun.com/zh/rds/apsaradb-rds-for-mysql/modify-the-permissions-of-a-standard-account-on-an-apsaradb-rds-for-mysql-instance)。

## 迁移次序与验收

1. **复查权限与目标状态**：使用 scripts/mysql-migration-preflight.py，只读；目标库可访问且没有用户表后才准备建表。凭据在被 Git 忽略的 .env.migration.local 中。
2. **取得源备份**：覆盖业务记录及 schema，核对导出前后计数与源写入变化。REST 分页导出必须固定排序、处理分页上限并支持断点；不把分表分页导出宣称为一致性快照。
3. **目标结构与试迁**：UUID 保持原值；PG 数组转 MySQL JSON，JSON null 与 SQL NULL 区分；timestamptz 统一转换为 UTC DATETIME(6)，年代字段使用可存负数的整数。按 source/person/event/topic、关系、fact_claim 的依赖顺序导入。保留约束并检测无效引用。
4. **应用改造**：公开接口统一通过 NestJS，去掉前端 Supabase 备用读取与登录状态。业务查询依次替换 content_page、entry_detail/entry_context、search_entries、graph_slice、timeline_overview、ask_search/topic_detail。
5. **AI 路径**：apps/api/dsh/remote-library.mjs 当前直接调用 Supabase RPC，必须切换到受限的公开阅读接口，子进程仍不获得数据库写凭据。匿名会话保留签名、过期、原子限额与取消机制。
6. **资料发布**：publish-book-batch.py 及别名/关系修订工具目前依赖 Supabase REST，需改为 MySQL 数据访问，保留只读预检、原文校核、稳定 key/UUID、已发布记录保护及最终公开读回验证。
7. **文件检查**：查明 image_url 是否引用 Supabase Storage，枚举实际对象与使用关系。数据库导出不包含文件内容；按实际用量决定文件迁移方案。
8. **试迁验收**：逐表计数、完整规范化记录散列、关联完整性、草稿不公开、数组/JSON/时间转换、中文别名和繁体查询、关系方向、分页不漏不重、时间轴、AI 引用追溯及并发额度检查。
9. **正式切换**：暂停资料写入，做最终一致同步并再次核对。准备目标配置和可回滚镜像，确认后才切换线上流量。切换前未删除 Supabase 数据或停用旧项目。恢复到旧库前先核对切换后是否有新写入。

## 2026-10-10 授权后复查及试迁准备

目标 histree 库已可访问，账号对该库具有 ALL PRIVILEGES；只读检查确认没有用户表。

已将 10 张 API 可见表导出并归档至本机私密目录 `backups/mysql-migration/2026-10-10-trial/`（已被 Git 忽略）。总 JSONL 大小约 68.2 MiB；8 张业务表合计 119,774 条记录。业务表导出前、文件内、导出后计数一致，10 个文件的 SHA-256 校核完成；声明的关联不存在悬空引用，fact_claim 的多态主体检查也未发现悬空引用。计数与散列不能证明在线分页读取是同一事务快照，正式切换仍需暂停写入和最终同步。

人物与事件表的 image_url 当前均无非空值，因此这两类条目暂未发现需搬迁的 Supabase 图片引用；不据此认定 Storage 中没有其他对象。

新增工具：

- `scripts/mysql-migration-preflight.py`：只读连接与元数据盘点，输出不包含连接凭据。
- `scripts/mysql-migration.py export`：只读、固定主键排序的游标导出，支持 GET 重试及 `--resume`；保留源记录和逐表哈希。
- `scripts/mysql-migration.py prepare`：检查快照、数据类型和关联，生成 `schema.mysql.sql` 与 `import-plan.json`。
- `scripts/mysql-migration.py import`：默认仅检查计划；写入需要 `--apply` 及明确的 `--plan-sha256`。核对目标指纹、快照/DDL 哈希及空库状态，拒绝覆盖非空库。建表 DDL 不是事务；失败时保留表供检查，回滚记录插入，不自动删表或重跑。
- `scripts/test-mysql-migration.py`：8 项离线回归检查，包括 UTC/微秒转换、JSON 标量与 Unicode、未知/负数年份、短页续读、默认无写入、计划变更拒绝及非空库保护。

试迁写入范围为 8 张业务表和 2 个因果关系保护触发器，导入现有业务记录，排除 user_roles 与 ai_gateway_quota（原记录仍在本地快照和源库）。MySQL 不允许在带级联外键动作的字段上使用 CHECK，因此用 INSERT/UPDATE 触发器保留“事件不能导致自身”检查，保留原级联删除语义。[MySQL CHECK 限制](https://docs.oracle.com/cd/E17952_01/mysql-8.0-en/create-table-check-constraints.html)

MySQL 表与连接显式使用 utf8mb4，数组转 JSON，记录创建时间转 UTC DATETIME(6)，年代字段仍为有符号整数。试迁插入使用普通 INSERT，不使用覆盖更新、REPLACE、TRUNCATE 或 DROP。提交前逐表核对计数和每条规范化记录的全字段散列；完成后写入 import-audit.json。

## 2026-10-10 授权执行及结果

用户明确回复“执行”后，按照已审阅计划 `3880f545fb208ee03a0e09490d96bbf8b2b7f21d0bec58bdbf78ab5f2ef7c7bd` 在 histree 空库中创建 8 张业务表和 2 个因果关系保护触发器，导入 119,774 条原始业务记录。8 张表均通过计数和规范化全字段 SHA-256 比较，随后提交；审计保存在归档目录的 `import-audit.json`。

另用新连接再次逐表核对提交后的记录数，确认 8 张表均使用 utf8mb4。测试事务实际验证 INSERT/UPDATE 自因果关系被触发器拒绝（错误码 1644），引用不存在人物的关系被外键拒绝（1452）。合法临时测试记录也已回滚，event_causality 仍为 0 条；验证结果保存在 `mysql-validation.json`。

读取数据库存储统计，数据约 61,931,520 字节、索引约 40,009,728 字节，合计约 97.2 MiB。该值是当前表/索引分配统计，不是最终容量或查询性能承诺。

运行中的网站、登录、资料发布脚本和生产配置均未切换，仍使用 Supabase。MySQL 当前是验证通过的业务数据副本，查询服务、搜索、AI 检索和原子配额改造尚未完成；正式切换前需重新同步源库变化并验收应用。源 Supabase 保留，未删除或停用。

## 2026-10-10 应用改造及 ECS 内网验证

用户授权继续应用改造，并指定 `rm-2zeiv0233csd46w9v.mysql.rds.aliyuncs.com` 作为待核验的部署地址。已在实际生产 ECS `i-2zef04sw3q63b7uhe5n0`（cn-beijing）验证：DNS 返回 `172.31.53.141`；3306 TCP 和 MySQL 8.0.36 握手成功；用现有账号连接 `histree` 并逐表查询，8 张业务表合计 119,774 条。测试未变更生产环境文件。部署模板为 `deploy/ecs/mysql-runtime.env.example`，不含密码；不要用这个不完整模板直接覆盖运行环境。

应用通过 `HISTREE_DATABASE=mysql` 启用新 MySQL 公共读取实现，连接使用 utf8mb4 和 UTC，池最多 6 条连接、等待队列 30 个、SELECT 最长 10 秒。网站端统一调用 NestJS API，已移除登录、网页管理路由和 Supabase 备用读取；MySQL 模式下管理写接口和旧 Edge 服务凭据通道均拒绝访问。Supabase 后端暂保留为回滚兼容，当前生产仍使用它。

公开查询保留人物/事件/专题列表、稳定分页、详情、关系上下文、120 节点/300 边图谱、时间图、证据和 AI 搜索。证据及关系同时检查自身与父条目发布状态。AI worker 改用受限的公开 HTTP 阅读操作，无 MySQL 用户名、密码或写权限；引用仍必须来自本次实际检索的证据账本。匿名签名、过期、取消、来源检查和不自动重试模型请求保留。

已通过管理 API 只读取得并私密归档线上 `consume_ai_gateway_quota` 的真实定义及 public 函数。MySQL 新增 `ai_gateway_quota` 账本，按 UTC 自然小时、全局后身份的固定锁顺序，在同一事务扣减；拒绝个人额度会回滚全站扣减。原上限：问答 10/200、游戏 80/1600、签发每身份 1/全站 1000，清理两小时前账本。试验额度与源账本独立；正式切换须在暂停 AI 后同步当前窗口计数，不能以试验计数替代生产额度。

本次回归还补齐已有问答与游戏的 actor 绑定，并将游戏候选上限扩大到 5,000 人以覆盖当前 3,540 人；超出上限仍显式报错。没有变更史料、ID、引文或各书账本。

资料工具新增显式 `--backend mysql --mysql-env <私密文件>`，默认仍为 Supabase，避免切换前误写目标库。`--apply` 仍是写入开关；MySQL 写入必须配置 `--public-api-url <实际API/v1>`，最终匿名 HTTP 读回，不以管理连接成功代替公开验收。保留旧值、稳定 ID、批次哈希、重复人物和关系检查，原 Supabase 审计保留，MySQL 使用单独 `publication-mysql.json`。MySQL 发布工具共用写锁，拒绝同时发布；所有原书批次未重新生成或发布。

最终同步工具 `scripts/mysql-final-sync.py` 默认只生成差异计划；`--apply` 需要审核过的 `--plan-sha256` 和 `--source-writes-paused` 声明。执行时共用目标发布锁，锁定并核对目标完整字段散列，普通 INSERT/UPDATE 后逐字段验证，在同一事务提交，失败回滚；遇到目标有源端不存在的 ID 则停止，不自动删除。当前试迁快照的只读计划显示 0 插入/0 更新；这不代表已检查之后的源库变化。

验证工具：

- `scripts/test-mysql-read.mjs`：22 项真实 MySQL 只读契约，含中文/繁体与字面量 `%/_`、负数年份、分页、图谱端点和来源；AI 检索约 0.7–1.5 秒（本次测试值）。
- `scripts/test-mysql-parity.mjs`：20 项线上匿名 RPC 的逐字段对照一致；源端全表证据和两项 AI 搜索返回 500，单独记录不算通过。另经管理 API 只读执行同一线上 AI 函数，对“秦/楚、前500—前200年”逐字段验证排序、年代、别名和描述一致。
- `scripts/test-mysql-boundaries.mjs`：14 项原生验证，临时人物、关系和引文仅在事务中存在，结束已回滚。并发 14 次问答额度恰好接受 10 次，拒绝不扣全站；仅写入试验配额，不调用模型。
- `scripts/test-mysql-preview.mjs`：真实 Chrome 验收 8 个页面，无浏览器错误、无 Supabase 请求；登录/管理入口移除，4 类管理或私密接口拒绝。
- 原仓库完整 `pnpm test` 通过，追加后的 API 回归为 14 suites / 92 tests passed；前后端构建、前端 lint 通过；批次分块工具 3 项、导入工具 8 项离线检查通过。现有卷四批次 MySQL 预检通过，只读且未生成发布审计。

已将候选构建放到 ECS 独立私密目录 `/opt/histree/mysql-candidate-20261010` 进行原生验收，仅本机 3101 端口；生产 3000 端口、nginx、正式域名和运行配置均未切换。候选验收与正式切换是不同阶段。

ECS 内网候选的完整真实问答也已通过：HTTP 200、14.3 秒完成、5 条来自 MySQL 已发布证据的引用，`insufficientEvidence=false`；仅一次模型调用。题目为君王后与太史敫、齐襄王的关系，回答保留了原文未载具体年份的限制。审阅了回答与原文摘录，未出现强定年代；结果私密归档为 `ecs-ai-validation.json`。该结果不代表生产流量已切换。

源结构追加只读盘点：40 个 public 约束、29 个索引、18 条策略，源时区为 UTC。Storage 当前仅见 `images` 桶，根目录对象列表为空，无文件夹且未触及分页上限；结合两类条目没有 image_url，暂未发现需搬迁的对象。

最终候选包 SHA-256 为 `b30b1828e020b35b8779cd4795cd02ccb93efa990b75ed95cf7dd18d75dee9eb`，ECS 镜像 `histree-api:mysql-final-20261010` 的 image ID 为 `sha256:32c39237cc426aab19621ce6f9ba9b3a7b96f68715010ef77e84348cb5af14b1`。最后的只读 AI 检索和原有 5 条引用匿名读回也通过，不增加模型调用。

新增 `scripts/mysql-source-snapshot.py` 尝试经 linked CLI 用单个 PostgreSQL SELECT 取得同一时点的业务记录和配额，并绑定 CLI project-ref 与源配置，避免误取其他项目。但本次 Supabase 在初始化数据库连接角色时返回 544 / connection timeout，原生一致快照没有取得；`2026-10-10-consistent` 目录无完成 manifest，不可当作有效备份或用于同步。已有试迁 REST 快照、函数与约束归档均保留。正式切换仍需暂停所有源端资料发布和 AI 入站，重新取得有效快照/源备份并做最终同步；不能把只读预检或已成功的候选问答当成已完成生产切换。
