# MySQL schema

MySQL 8 初始化空开发库：按文件名顺序执行 `001-content.sql`、`002-ai-quota.sql`。第一份是实际切换使用的八张业务表定义、外键、检查约束与防自因果触发器；第二份是事务 AI 限额账本。不含业务记录、用户或凭据。

这些是初始化基线，不是现有生产库的增量迁移。后续 schema 修改新增显式增量文件并独立预检／授权，不能重放基线。应用工作流不自动执行 DDL。

`pnpm test:mysql` 只接受本机、名字匹配 `histree_test_*` 的空库，验证当前原生查询和并发限额；不接受 RDS host 或生产库名。


`003-guess-bank.sql` 是新增游戏表的独立迁移（`guess_bank`、`guess_difficulty_feedback`），不更新史料。对已有库先确认两表均不存在，再单独执行；应用不自动建表。正常部署前需要此迁移，并运行 `node scripts/prepare-guess-bank.mjs --apply` 预热持久题库。准备命令默认只读统计；运行时也会在后台补齐新增人物，已调整难度不会被初始化覆盖。

`pnpm test:mysql` 额外在独立测试库建立 15,022 名合成人物，通过实际 Nest HTTP 开局测量冷启动及连续开局 P50/P95，并覆盖反馈去重、阈值、调档、旧版本反馈和重启后的持久性。所有模型请求均禁止；测试不连接生产库。

统一有序清单由 `scripts/mysql-schema.mjs` 提供（`pnpm schema:plan`），包含原文、反馈及新内容结构迁移，不再按单一目录猜顺序。`--bootstrap-test` 只初始化空的本机 `histree_test_*` 数据库。当前生产环境增量仍须单独预检，不能重放基线。

`005-content-structure.sql` 新增证据、年代与校核覆盖侧表、内容版本以及目录索引；不改已有事实字段。依赖此前全部表。执行、回填与应用上线顺序见 `docs/CONTENT_STRUCTURE.md`；应用不自动执行迁移。
