# AI 入口与数据边界

浏览器通过同源 `/api/v1/ask`、`/api/v1/ask/guess/*` 直接访问 NestJS。`/api/v1/ask/session` 签发 24 小时 HMAC 匿名令牌，后续请求发送 `x-histree-anonymous`。签名密钥只在服务器；旧 Bearer 登录和 Edge 服务凭据入口被拒绝。

| 配置 | 作用 |
| --- | --- |
| `HISTREE_ASK_ENABLED` / `DEEPSEEK_API_KEY` / `HISTREE_MODEL` | 控制模型可用性与模型选择 |
| `HISTREE_GATEWAY_SECRET` | 至少 32 字符；签匿名会话，轮换后旧会话失效 |
| `HISTREE_ALLOW_ANONYMOUS` | 默认 true；false 关闭 AI 匿名访问 |
| `HISTREE_AI_ALLOWED_ORIGINS` | 允许的浏览器 Origin 列表，本地开发需添加 Vite Origin |
| `MYSQL_*` | 服务端 MySQL 连接，ECS 使用内网地址 |

身份来自签名令牌，不能信任浏览器提供的 actor。请求只接受指定接口与 JSON 形状，限制请求体，校验 Origin；问答对话与游戏同时绑定 actor。会话与对话仍在内存，发布／重启会结束进行中的会话。

MySQL `ai_gateway_quota` 使用 UTC 自然小时及事务行锁：ask 每身份 10／全站 200，guess 80／1600，session 1／1000；失败不执行模型，限额拒绝回滚双方计数。签匿名令牌不等于真实用户认证；全站限额限制调用成本。

线索模式的 `POST /api/v1/ask/guess/clues/start`、`act`、`feedback` 只读取预备题库或保存难度反馈，不调用模型，因此不检查或消耗 AI 小时额度；提问模式、问史料与匿名令牌签发维持上述额度。线索请求仍须通过签名身份、Origin、JSON 和请求体大小校验，保留跨身份隔离、一小时游戏时效、500 局会话容量与单局 80 次猜姓名保护。

状态接口不调用模型、不扣业务限额。`/api/v1/health` 验证 MySQL 就绪，与 AI 是否开启独立。浏览器不自动重试收费请求。

## dsh worker

NestJS 调度独立子进程，环境只包含必需的模型配置、临时目录与只读检索地址。worker 通过本机 `/api/v1/read/:name` 执行 allowlist 中的受限查询，不持有数据库凭据、签名密钥或发布权限；不能调用任意 SQL、写入限额或读取草稿。

数据库读取保留已发布主体及关系端点过滤。检索账本只记录实际取得的引用，回答必须关联这些引用；出错、资料不足或没有有效出处时不能伪装成有证据的答案。

`readonly.patch.yml` 限定问答工具集合，`guess.patch.yml` 禁用游戏模型的工具调用。运行真实 harness 的模拟模型测试：

```sh
pnpm test:ask-runtime
HISTREE_REMOTE_SMOKE=1 pnpm test:ask-runtime
node apps/api/dsh/guess-smoke.mjs
```

这些测试通过本地模拟模型与公开读取服务验证 MCP、引用及退出行为，不产生付费调用。真实模型评测必须显式选择运行，不能纳入自动部署验收。
