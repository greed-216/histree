# AI 业务入口

浏览器调用 Supabase `functions/v1/ai-gateway`，Edge 验证调用身份、检查共享额度并转发到 ECS。NestJS 的问答、游戏和状态接口都要求 `HISTREE_GATEWAY_SECRET` 服务凭据；不依赖隐藏地址或 CORS 鉴权。ECS 合并镜像中的普通阅读通过同源 NestJS API 访问 Supabase 发布视图／RPC；未配置 API 地址的备用前端仍直接使用 Data API / RPC 和 RLS。

## 身份与额度

当前默认允许匿名。浏览器第一次提交前请求 `POST /session`，得到有效一天的随机签名匿名令牌，保存在 localStorage；每个浏览器独立身份，不收集客户端 IP。问答与游戏会话绑定该身份，持有别人的会话 token 也不能访问。

匿名身份可通过清理浏览器数据重建，因此不是强用户认证。数据库另有全站成本上限。未来接入登录后，浏览器自动发送 Supabase access token，Edge 用 Auth 验证后取得 user ID，错误 token 不降级到匿名。设置 `HISTREE_ALLOW_ANONYMOUS=false` 可要求登录；登录/退出或匿名令牌到期后应重新开始 AI 会话。

按自然小时原子扣减：问答每身份 10 次、全站 200 次；游戏每身份 80 次、全站 1600 次；匿名会话签发全站 1000 次。额度函数仅 service_role 可调用，拒绝时不扣减全站额度；数据库故障时停止转发。额度不等于计费结算：转发失败或 ECS 忙碌也可能消耗请求额度，不自动重试。调整上限需修改额度函数并经迁移部署。

ECS 仍保留现有并发及进程内保护，会话仍在单实例内存。重启会丢会话；本次不实现多实例会话存储。

## 配置

Edge secrets：

- `HISTREE_ECS_API_URL`：HTTPS 地址，以 `/api/v1` 结尾。
- `HISTREE_GATEWAY_SECRET`：随机生成的至少 32 字符服务凭据，与 ECS 相同。不要配置为 VITE_*。
- `HISTREE_ALLOWED_ORIGINS`：逗号分隔；代码默认 `https://greed-216.github.io`，当前生产配置为 `https://greed-216.github.io,https://123.56.189.146`，支持已开放的 IP 前端。
- `HISTREE_ALLOW_ANONYMOUS`：默认允许；`false` 要求认证。

Edge 使用平台内置 `SUPABASE_URL`、`SUPABASE_ANON_KEY`、`SUPABASE_SERVICE_ROLE_KEY`。service role 只用于额度 RPC，绝不转发到 ECS；ECS 的检索保持匿名发布视图。

浏览器只配置 `VITE_SUPABASE_URL` 和 `VITE_SUPABASE_ANON_KEY`。问答和游戏不再使用 VITE_ASK_API_URL 或 VITE_API_URL；普通阅读与管理接口的 VITE_API_URL 配置独立，ECS 合并镜像设置为 `/api/v1`。域名上线时，在 `HISTREE_ALLOWED_ORIGINS` 中添加 `https://histree.wiki`，保留已有允许来源；本地预览的 Origin 未获允许时，AI 入口会被拒绝。

Edge 必须 `verify_jwt=false`：匿名是当前产品行为，函数内部仍验证所有提供的用户令牌。白名单仅包含 session、ask、ask/status、ask/guess/status、ask/guess/start、ask/guess/act；不允许任意代理 URL、查询参数或管理路由。

ECS 只接受 Edge 服务凭据及由 Edge 构造的 actor；客户端自定义身份、Authorization 和转发 IP 头不会被透传。服务凭据通过 HTTPS，支持在 Edge secrets 和 ECS 环境中协调轮换。

## 部署顺序

1. 单独审阅并应用 `20261003120000_ai_gateway_quota.sql`，登记迁移；不重放旧迁移或历史清理 SQL。
2. 在 ECS 私密 `/opt/histree/runtime.env` 和 Supabase Edge secrets 配置同一个 gateway secret；不要打印或提交。服务凭据没有传入 dsh 进程。
3. 配置 Edge 的 ECS HTTPS 地址，部署 `supabase functions deploy ai-gateway --project-ref ilnwjhabcqtxkkuhddyt --use-api`。
4. 更新前端到 Edge 入口；前后端切换期间暂停 AI 使用。部署带 GatewayGuard 的 API 后，旧页面直连会被拒绝，需要刷新。
5. 验证 Edge 两个 status 返回 available、非法路径返回 404、错误 Origin 返回 403、无凭据 ECS status 返回 401。用模拟模型核验流式转发、取消和跨身份会话隔离；真实模型请求另行计入使用成本。

不要通过完整 `supabase db push` 部署这个单独变更，以免误应用其他迁移。生产发布需协调数据库、Edge、ECS 合并应用和 nginx／证书；Pages 仅作为手动备用发布。普通前端迁移到 ECS 不改变 AI 网关的身份、额度或服务凭据边界。

## 本地与测试

运行 Node 24、pnpm 和 Deno 2。先设置本地 API gateway secret，再配置 Edge 本地环境文件（不要提交）。本地 Docker 内访问 API 用 `http://host.docker.internal:3000/api/v1`；设置 `HISTREE_LOCAL_DEV=true` 仅在本地运行时允许这一主机，生产地址必须 HTTPS。允许来源添加实际 Vite origin。

测试：`pnpm test:gateway`、`pnpm --filter api test --runInBand`、API build、web lint/build。额度回归在 PGlite 执行真实迁移；Edge 回归覆盖签名、用户令牌、路由限制、请求长度、配额故障与流式取消。

等待 ECS 响应头最多 15 秒；收到响应头后保留完整流式时限。上游业务总超时 120 秒、Edge 130 秒、浏览器游戏 140 秒，给托管函数时限留出余量。Edge 不缓冲 NDJSON，不自动重试付费请求。平台断开连接行为仍需部署后验证。

## 运行诊断

响应与 ECS 请求共用 `X-Histree-Request-Id`。Edge 记录上游开始、返回状态及等待时间；错误日志区分身份、额度和上游阶段，只记录错误类型，不记录正文、匿名令牌、用户 ID 或服务凭据。

2026-10-03 发布验证中，两个状态接口和全部 ECS 直连拦截通过；实际 Edge 问答首包约 2.6 秒，约 24 秒完成并返回四条引用。期间也出现过上游阶段 130 秒超时，随后请求恢复；原因尚未确认，不能把状态接口可用等同于跨境流式链路稳定。保留请求日志继续定位，付费请求仍不自动重试。

日志核查确认超时发生于 Edge 的 `upstream` 阶段，始终没有收到 ECS 响应头；对应时段 ECS 没有 HTTP 接收记录。GET 和不用模型的 POST 都可发生，证据指向 HTTPS 连接/传输环节，不支持归因于中文、流式格式、数据库规模或模型生成耗时。具体网络原因尚未确认；15 秒首包保护仅缩短失败等待，不构成网络根治或安全重试保证。

为精确关联 ECS 接收记录，备份 `/etc/nginx/conf.d/histree.conf` 后运行 `python3 scripts/configure-ai-gateway-logs.py`，通过 `nginx -t` 才 reload；失败时恢复备份。`/var/log/nginx/histree-ai.log` 仅记录请求 ID、路径、状态和代理耗时，不记录凭据、正文、actor 或客户端 IP。现有证书、鉴权与路由保持不变；后续常规 ECS 发布会保留这些配置。
