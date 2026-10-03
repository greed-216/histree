# 部署与内容批次

## 当前架构

- 前端：GitHub Pages，推送 `main` 后由 `.github/workflows/deploy.yml` 测试、构建并发布。
- 数据库和登录：Supabase 项目 `ilnwjhabcqtxkkuhddyt`。
- AI 计算后端：北京 ECS 上的 NestJS + dsh，通过 Supabase `ai-gateway` Edge Function 访问。部署顺序和密钥配置见 [AI 网关](AI_GATEWAY.md)。
- GitHub 未配置 `VITE_API_URL` 时，公开页面直接使用 Supabase 匿名客户端；管理台写入需要另行部署 API 并配置该变量，以 `/api/v1` 结尾。
- 服务角色密钥仅用于后端，不得配置为 `VITE_*` 或提交到 Git。

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
- 后端部署后还需验证 `/api/v1/topics` 及未登录访问管理接口被拒绝；Pages 成功不能代替后端部署成功。
