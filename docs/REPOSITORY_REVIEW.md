# 2026-10-11 仓库审阅与清理

基于 GitHub main `6cd6fa94` 的独立工作区，核对实际生产镜像 `51933b3a…`、ECS current-release 与 nginx。原工作区存在大量历史资料改动，未并入此清理；`content/` 与 `resources/` 没有修改。

| 问题 | 处理 |
| --- | --- |
| 线上 MySQL 实现尚未同步到主线 | 纳入已验证的数据实现，并保留最新主线游戏／前端行为 |
| 登录、网页后台、上传及写接口已停用但仍驻留 | 删除路由、模块、SDK、管理 Guard 和无消费的写入类型；公开专题／出处拆为 CatalogModule |
| MySQL 藏在 SupabaseService 命名和旧运行分支后 | 直接注入 MysqlModule/MysqlService，去掉旧 Auth、Edge 和 PostgreSQL 运行 fallback |
| 共享包直接导出 TS，生产依赖目录会触发 Node 加载限制 | 编译成 JS 和类型声明；先构建共享包，再构建两个应用 |
| Docker 包含所有开发／前端依赖 | pnpm deploy 打包 API 生产依赖，runtime 以非 root 运行 |
| pnpm 新安装跳过必需原生构建 | 明确三个 dsh 原生依赖的安装脚本，实际模拟 harness 验证 |
| CI 只测旧 PostgreSQL，Pages／Render／Deno 流程仍在 | PR 与 ECS 共用一个 Linux 镜像流程，增加隔离 MySQL；旧 SQL 单独离线兼容，删除旧发布 |
| 健康依赖 AI 开关，验收失败没有完整回滚 | 增加 MySQL 就绪接口，发布锁及成功／启动失败／后续验收失败回滚测试 |
| 发布不会确认长图版本，容易装回旧前端 | 生成本次 release manifest，实际 SPA／深链接及长卷 SHA-256 纳入验收 |
| 资料发布、修订和验收仍读旧源库 | MySQL 默认连接、独立匿名 HTTP 读回、旧值守卫、100 条分块及新旧审计兼容 |
| README／规范／操作指南与部署不一致 | 更新包职责、开发步骤、AI／ECS 配置和 AGENTS；过时步骤明确归档 |

三个 workspace 包都有用途，保留 web、api、shared-types，依赖方向见 README。按用户明确选择保留暂停地图的代码、绘图数据和测试，开关保持关闭。历史 PostgreSQL SQL 逐文件字节保持一致地移入档案；旧发布及来源档案不重建。

## 验证与交付边界

本地使用 Node 24 验证冻结安装、共享包与两应用构建、web lint、API HTTP／签名／查询回归、长图／图谱／地图回归、原 SQL 导入兼容、真实 dsh/MCP 模拟服务、内容守卫与回滚分支。生产依赖包单独验证可以加载 compiled API/shared-types。

GitHub 的 application-checks 进一步执行空的 `histree_test_*` MySQL 8 服务和实际 linux/amd64 镜像；结果以 PR Checks 为准。测试不消耗生产限额或付费模型，不连接生产库写入。

此清理通过独立 PR 交付，未合并 main 或部署到生产。main 合并后现有部署开关会触发已配置的 ECS 发布流程；数据库 DDL、史料发布和证书模式不随应用自动执行。
