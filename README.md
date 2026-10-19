# Histree 历史之树

通过人物、事件、关系和可回溯史料，阅读历史的脉络。支持时间长卷、专题导读、关系图谱、搜索、有出处的问答与猜人物。

[访问网站](https://histree.wiki/) · [历史长卷](https://histree.wiki/timeline/scroll) · [导读](https://histree.wiki/learn) · [网站索引](docs/SITE_INDEX.md)

## 当前架构与分包

Node.js 24 + pnpm 10.28.1 workspace。北京 ECS 运行一个 Docker 镜像，包含 React/Vite 静态前端、NestJS/TypeScript API 与 dsh worker。宿主机 nginx 提供 HTTPS，API 通过 RDS MySQL 8 内网连接读取数据。

| 包／目录 | 职责 | 依赖与边界 |
| --- | --- | --- |
| `apps/web`（`web`） | React 19、Vite 8；阅读、长卷、导读、图谱和 AI 界面 | 导入 `shared-types`；只访问同源 `/api/v1`，无数据库凭据 |
| `apps/api`（`api`） | NestJS 11；公开查询、匿名签名会话、MySQL 限额和 dsh 调度 | 导入 `shared-types`；通过 mysql2 访问 RDS；worker 只拿受限公开读取地址 |
| `packages/shared-types` | 数据契约、时间与分页／查询参数校验 | 先编译为 JS 与类型声明，两个应用共用；无数据库连接、无框架依赖，不能依赖应用包 |
| `database/mysql` | 当前 MySQL 建表定义及限额账本 | 初始化空开发库；应用发布不自动修改线上 schema |
| `scripts` | 史料检索、批次准备、受审阅的发布与修订、验证 | Python 写入默认关闭；匿名 HTTP 读回独立于管理连接 |
| `content` / `resources` | 批次、审阅记录、进度、底本和出处快照 | 史料资产及发布档案；不打进应用镜像 |
| `database/legacy-postgres` | 迁移前 SQL 的历史兼容档案 | 仅用于离线兼容回归，不能部署到 MySQL |

三个 workspace 包都存在实际调用，均保留。旧登录、网页管理、上传、Supabase SDK／Edge 网关、Render 与 Pages 发布已经退出当前流程。按用户要求保留暂停的地图原型及其测试，`MAPS_ENABLED=false`；本机绘图草稿不会写入数据库。

## 本地开发

准备 Node.js 24、pnpm 10.28.1、Python 3.12 和 MySQL 8。在**空开发库**中按顺序执行 `database/mysql/001-content.sql` 与 `002-ai-quota.sql`；不要在现有生产库重放初始化 SQL。

```sh
corepack enable pnpm
pnpm install --frozen-lockfile
pnpm --filter @histree/shared-types build
python3 -m pip install -r requirements-tools.txt
cp apps/api/.env.example apps/api/.env
# 填写开发库的 MYSQL_*；默认不启用模型调用。
pnpm --filter api start:dev
# 另一个终端：
pnpm --filter web dev
```

打开 `http://localhost:5173/`。Vite 将 `/api/v1` 转发到 `127.0.0.1:3000`；浏览器和生产环境都使用根路径路由。启用本地 AI 时还需签名密钥、模型配置及对应 Origin，见 [AI 入口](docs/AI_GATEWAY.md)。不要将生产环境文件、连接凭据、模型密钥或数据备份入库。

```sh
pnpm build
pnpm lint
pnpm test
# 可选：使用隔离的本机 histree_test_* 空库，配置 MYSQL_* 后运行：
pnpm test:mysql
# 历史 SQL 导入兼容：仅在内存 PostgreSQL 执行
pnpm test:archive
pnpm test:ask-runtime
HISTREE_REMOTE_SMOKE=1 pnpm test:ask-runtime
node apps/api/dsh/guess-smoke.mjs
python3 -m unittest discover -s scripts/tests
python3 scripts/test-book-publish-chunks.py
```

## 发布与协作

PR 和 ECS 发布共用 [应用检查](.github/workflows/application-checks.yml)：编译、lint、当前回归、隔离 MySQL、历史 SQL 兼容、内容守卫、实际 Linux 镜像与无模型验收。主线发布通过 GitHub artifact 的短期下载地址送到 ECS，校验 digest 和文件清单后加载同一个镜像，运行时凭据只存在宿主机。

[ECS 操作](deploy/ecs/README.md) · [部署架构](docs/DEPLOYMENT.md) · [仓库协作规范](AGENTS.md) · [史料录入 Skill](skills/histree-history-ingest/SKILL.md) · [MySQL 切换档案](docs/MYSQL_MIGRATION.md) · [本次审阅记录](docs/REPOSITORY_REVIEW.md)

长卷图片是艺术构图，不作为历史现场或疆域复原；历史结论以条目列出的具体史料为依据。外部底本、图片和资料的来源及使用条件见各资源说明。
