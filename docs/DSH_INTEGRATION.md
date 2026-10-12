# dsh 集成

当前问答和猜人物在 NestJS 调度的 Node.js 24 子进程中运行 dsh。服务、工具清单和环境边界见 [AI 入口](AI_GATEWAY.md)，部署见 [ECS 操作](../deploy/ecs/README.md)。

| 文件 | 职责 |
| --- | --- |
| `apps/api/dsh/worker.mjs` | 问答 worker 生命周期、进度、引用验证 |
| `mcp.mjs` / `readonly.patch.yml` | 只读历史工具及允许清单 |
| `remote-library.mjs` | 调用本机公开 API，积累实际检索引用账本 |
| `retrieval.mjs` | 引用、来源 URL 和回答验证；内存资料用于离线测试 |
| `guess-worker.mjs` / `guess.patch.yml` | 无工具的猜人物模型，使用服务端预选资料 |
| `smoke.mjs` / `guess-smoke.mjs` | 模拟模型上的真实 dsh/MCP 与 worker 验证 |

必需原生依赖的安装脚本在 `pnpm-workspace.yaml` 明确放行；Docker builder 提供编译工具，runtime 只保留生产依赖。不能以 HTTP 状态页代替实际 harness 运行验证。

公开 API 检索有分页、数量与时间限制；未发布主体、草稿关系端点和对应证据不能进入回答。检索地址只允许固定 allowlist 查询。工具不能读取全局文件系统、执行 shell、安装插件或取得数据库写权限。

旧 Render、Pages 与 Supabase Edge 方案已移除；数据库 schema 由 `database/mysql` 管理。原 PostgreSQL 查询兼容测试属于 `pnpm test:archive`，不表示生产继续使用 PostgreSQL。
