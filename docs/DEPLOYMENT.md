# 部署与内容批次

## 当前架构

- 前端与 API：北京 ECS 上的单个 Docker 镜像，包含 React/Vite 静态文件与 NestJS/dsh。Node 服务通过 `HISTREE_WEB_ROOT` 提供前端，浏览器路由使用 `/`，普通业务接口使用 `/api/v1`。
- HTTPS：宿主机 nginx；容器 `3000` 端口只绑定 `127.0.0.1`。仅在该可信代理后设置 `TRUST_PROXY=1`。
- 数据库和登录：继续使用 Supabase 项目 `ilnwjhabcqtxkkuhddyt`，本次托管迁移没有搬迁数据库或重放迁移。
- 普通阅读与管理：ECS 镜像构建时设置 `VITE_API_URL=/api/v1`，调用同源 API；公开读取保留发布状态和匿名 RLS 视图，管理写入继续要求管理员权限。未配置 API 地址的本地／备用前端保留 Supabase Data API/RPC 直读模式。
- AI：浏览器仍经 Supabase `ai-gateway` Edge Function 进行身份与共享额度校验，再访问 ECS。域名上线时补充允许的 Origin，配置见 [AI 网关](AI_GATEWAY.md)。
- 自动发布：`.github/workflows/deploy-api.yml` 构建、验证并发布前后端合并镜像。`.github/workflows/deploy.yml` 仅保留手动 GitHub Pages 备用发布。
- 构建时只使用 Supabase 公共 URL／anon key；模型密钥、gateway secret 等只放在服务端环境中，不进入前端、镜像或 Git。

镜像构建参数、ECS 私有环境文件、GitHub 变量、发布校验及回滚步骤见 [ECS 操作说明](../deploy/ecs/README.md)。

## 2026-10-08 托管迁移与域名状态

前后端合并应用提交 `e0a9bcb2` 已推送并通过 GitHub Actions 部署到 ECS，容器健康，页面深链接、静态资源、公开数据读取和浏览器刷新已验证。工作区中的其他未提交内容没有纳入本次发布。

histree.wiki 已解析至 `123.56.189.146`，Nginx 格式的阿里云已签发证书已安装。证书同时覆盖 histree.wiki 与 www.histree.wiki，目前 nginx 只配置根域名；有效至 **2027-01-06 07:59:59（北京时间）**。私钥仅 root 可读，证书包和私钥不入库。

ICP备案尚在办理，当前采用证书安装脚本的 `pending` 模式，域名 nginx 返回 HTTP 503 与“ICP备案办理中，网站尚未开放。”。服务器通过正常域名解析完成 TLS 校验；当前网络的公网连接仍在 TLS 握手阶段断开，公网可用性尚未确认。此状态不能表述为域名网站已正式上线。随后用户授权开放 IP 入口，`https://123.56.189.146/` 已转发完整前端和普通 API；域名待上线配置独立保留。IP HTTPS 使用原有自动续期证书，管理员和 AI 服务凭据校验继续生效。

备案／接入要求完成且正式上线获授权后：

1. 复用已安装的阿里云证书，以 `install-domain-certificate.sh` 的 `serve` 模式启用应用代理；不要用 Let's Encrypt 脚本覆盖它。
2. 在 Supabase 网关允许来源中补充 `https://histree.wiki`，保留已有来源；使用邮件或 OAuth 回调时同步更新 Auth 的站点与回调配置。
3. 从公网核验 TLS、首页、深链接、数据读取、登录及 AI 链路，再把状态改为正式上线。

已有 IP HTTPS 网关可运行 `bash deploy/ecs/open-ip-frontend.sh 123.56.189.146` 开放合并应用。脚本保留专用 AI 路由，校验 nginx 和深链接，并保存可回滚的原配置。AI 网关生产允许来源包含 `https://greed-216.github.io` 与 `https://123.56.189.146`；域名上线时再补充其 Origin。

阿里云证书到期前需续签并替换；现有 Certbot timer 负责旧 IP 证书，不负责这份域名证书。

## 2026-09-28 后梁首批上线

本次按用户要求将 `later-liang-907-923-v1` 接入公开阅读：6 位人物、9 个事件、19 条关系、14 条来源、85 条引用和 1 个专题。源 JSON 保留 draft 作为整理底稿；数据库发布状态由独立发布步骤控制。坐标待核实，地图不显示虚构落点。

已核对远端旧迁移至 `20260422174000`，通过 Management API 在同一事务内应用并登记 `20260928120000`、`20260928130000`、`20260928140000`。执行前核实业务内容为空，账号与角色各 1 条。今后不得重新执行一次性清理 SQL。

## 内容导入操作

```sh
python3 scripts/prepare-content-import.py \
  content/later-liang-907-923/content-batch.json /tmp/histree-release
pnpm test:content
```

生成四个文件：

- `key-map.json`：稳定 key 对应确定 UUID；跨批次相同 key 表示同一记录，不能复用为其他对象。
- `import-draft.sql`：事务导入；已存在 ID 跳过，不更新或撤回已有记录。
- `publish.sql`：只发布本批确定 ID。
- `unpublish.sql`：只下架本批确定 ID，保留数据以便修订。

审阅生成的 SQL 后，通过已登录 Supabase CLI 执行：

```sh
supabase db query --linked --file /tmp/histree-release/import-draft.sql
# 核实数量、引用及匿名草稿不可见后，再执行发布：
supabase db query --linked --file /tmp/histree-release/publish.sql
```

JSON 修改后再次导入不会自动更新已有内容，应在管理台修订，或另写经过审阅的限定 ID 更新。不是通用同步器。

## 验收

- `pnpm test`：API、迁移与 RLS、真实后梁批次重复导入和发布／下架测试。
- `pnpm --filter api build`、`pnpm --filter web lint`、`pnpm --filter web build`。
- 线上匿名核实数量、专题深链接、事件详情和出处、人物搜索及图谱。
- 应用部署后验证前端根路径／深链接、静态资源和 `/api/v1/topics`；缺失资产及 API 路由返回 404，未登录管理请求被拒绝。镜像健康、TLS 安装和公网网站上线分别核验。
