# 迁移前 PostgreSQL 档案

这里保留历史 SQL，供 `pnpm test:archive` 验证旧批次的稳定 ID、引用结构与原查询契约。只在 PGlite 内存库执行。生产已经迁到 MySQL，不使用 Supabase CLI、Auth、Edge 或这些 SQL 部署。

旧的删除／清空内容迁移是一次性历史操作，不得重放到当前数据库。当前 schema 是 `database/mysql`；后续结构变更以独立 MySQL migration 审阅，不随应用发布执行。
