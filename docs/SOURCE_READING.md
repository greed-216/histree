# 站内原文阅读

## 2026-10-19 生产状态

已随应用 `9041ea21` 上线。生产 `source_text` 回填 2,267 份固定原文；其中一份按线上已修订的当前存档重新读取，未改原来源 URL。主键外键的 `source_id` 明确使用 `ascii_bin`，与现有 `source.id` 一致；正文和 URL 仍为 utf8mb4。逐字读回与线上匿名正文 SHA-256 校验通过。

私有 `feedback` 表已建立，邮箱可空。实际服务的保存、同请求去重、同编号改内容拒绝均在原生 MySQL 事务内验证并回滚；公网无读取入口，无效提交被拒绝，浏览器表单已验收。本次未留下测试反馈，也未向外发信。


原文正文存入 MySQL `source_text`，复用现有 `source.id`；不改旧来源、引文或已发布批次。站内出处按钮指向来源页。根据产品要求，页面不展示底本处理说明、机器段落编号、引用固定链接或 GitHub 入口；固定版本 URL、哈希与校核元数据仍保留在后台。

## 数据与索引

- `content`：原文 `LONGTEXT`。TXT 快照逐字保留；旧 JSONL 仅在 URL 有明确 `#L行号` 时提取对应记录的 `text` 字段，不展示序列化 JSON，也不猜测无定位的记录。
- `content_sha256`：展示正文的 UTF-8 字节哈希；`archive_blob_sha256`：固定 Git blob 的原始字节哈希；`archive_commit`：完整提交号。旧短 SHA 存档在导入时解析成完整提交，不修改旧来源 URL。
- `(source_id, archive_url_sha256)` 为主键，确保同来源、同版本幂等；单独的存档地址哈希索引用于导读与问答的站内跳转。现阶段不新增全文搜索索引。
- 读取时来源当前 URL 必须与存档 URL 相同，并且至少有一条匿名可见的已发布引用；关系任一端点未发布时，相应引用不能开放原文。旧版本保留在表中，不会误显示到新版本来源。

页面只高亮能在正文中逐字连续匹配的摘录，匹配失败保留原文并提示人工核对，不修改原字以凑匹配。选定引用单独按 ID 读取，避免来源引用列表超过一页时丢失定位。没有原文或数据库尚未迁移时仍展示已有摘录；其他数据库错误显示重试提示。事实异说等补充说明折叠保留，后台版本和原字不改。

## 本地准备与预览

以下命令不需要生产凭据，不连接线上数据库：

```sh
python3 scripts/import-source-texts.py prepare --output /private/tmp/histree-source-texts-preview/plan.json
python3 scripts/import-source-texts.py import /private/tmp/histree-source-texts-preview/plan.json
pnpm --filter api build
node scripts/run-source-reading-preview.mjs
```

准备命令仅选择批次/修订发布审计 `verified` 且文件哈希相符、被 claim 引用的来源；无法确定具体片段的旧来源列在计划 `skipped` 中。所有正文从固定 Git blob 读取，不使用可变工作区文件、不在读者访问时请求 GitHub。缓存缺少引用提交时需先补齐对应 Git 对象；不会退回当前分支或静默下载。

预览默认只监听 `127.0.0.1:5186`（可用 `PORT` 改端口），使用隔离的本地 PGlite 数据库，加载《资治通鉴》卷十三的真实引用与原文；除本地反馈提交外只允许 GET。反馈存在 `/private/tmp/histree-source-texts-preview/feedback-db`，可通过 `HISTREE_FEEDBACK_PREVIEW_DB` 改位置。读取与提交执行实际应用服务及 SQL，仅适配数据库方言；原文样本独立于反馈保存，反馈支持重启后读回。它不是原生 MySQL 迁移验证，未验证的其他页面不代理线上服务。

验证：

```sh
python3 scripts/test-source-texts.py
node scripts/test-source-reading-data.mjs
node scripts/test-feedback-data.mjs
pnpm --filter api test --runInBand editorial.service.spec.ts
pnpm --filter api test --runInBand feedback.service.spec.ts
pnpm --filter web build
```

## MySQL 上线流程

迁移与导入须有明确上线授权，先预检后执行。

1. 在独立 MySQL 测试库运行 `apps/api/mysql/migrations/20261019_source_text.sql` 并验证导入与索引；DDL 不受事务回滚保护。
2. 用实际来源元数据核对回填计划。`python3 scripts/import-source-texts.py import '<计划>' --mysql-env '<私密环境文件>'` 只读预检。来源缺失、URL 已变、原文已有不同内容均拒绝导入，先核查，不覆盖旧值。
3. 授权后使用同一命令加 `--apply`；首次明确建表时再加 `--create-table`。脚本与批次发布器共用写锁，先校验全部行，再插入缺失片段，逐字读回，事务提交；重复导入复用相同记录。不会 UPDATE 原文。
4. 部署 API/前端后，匿名读回 `/api/v1/sources/:id/text`，核对正文哈希并验收实际页面。旧 Supabase 维持原用途，不新增写入。

`publish-book-batch.py` 的 MySQL 分支已接入：默认预检同时检查原文；`--apply` 在写任何批次记录前要求原文表已迁移，缺表直接停止。来源/实体/引用草稿验证后、公开发布前导入原文；最终匿名 HTTP 读回也校验原文。保留旧批次和原审计，回填另用本脚本，不重跑历史发布器。

## 站内反馈

引用卡片与来源页提供“提交勘误”，页尾提供“意见反馈”。正文建议必填，邮箱选填；服务端从公开引用/来源核验上下文，保存后才返回 `received: true`。客户端请求编号用于同内容重试去重，不允许同编号覆盖旧反馈；数据库失败返回可重试错误，不能显示虚假成功。

生产反馈存在私有 `feedback` 表；上线前另行应用 `apps/api/mysql/migrations/20261019_feedback.sql`，迁移须随明确授权的上线执行。保留关联 ID、页面路径、服务端生成的上下文摘要、建议、可空邮箱和待处理状态。仅开放 `POST /api/v1/feedback`，无匿名列表/详情读取接口，不向 GitHub 提交，不发送邮件，也不自动改史料。邮箱不回传、不写日志。此阶段每个访问地址每小时最多提交 10 次，计数仅保存在进程内存，并限制计数器数量；多副本部署时应再配置统一入口限流。
