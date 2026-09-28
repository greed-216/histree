# 第一版专题阅读交付（2026-09-28）

## 本次范围

已实现专题首页 → 章节导读 → 人物／事件全文 → 时间脉络 → 关系说明与具体出处 → 图谱往返。内容方向已调整为五代十国；旧历史样例已退出业务数据，测试使用隔离的虚构记录。

- `/`：专题入口与搜索。
- `/topics/:slug`：专题；章节与关联条目从数据库读取。
- `/people/:id`、`/events/:id`：独立阅读页；保留原图谱路径 `/graph/:id`。
- `/search?q=关键词&kind=person`：姓名、别名、标签、时代、概述及专题搜索；查询保留在 URL。
- `/admin`：原有条目和关系编辑，增加发布状态、人物生卒、事件结束年与阶段编辑。
- `/admin/editorial`：专题章节编排、来源库、人物／事件／关系的陈述与引用管理。
- GitHub Pages 的 `404.html` 保留深链接路径、查询参数和锚点后返回应用。

本版搜索在已加载的小规模数据中完成。专题时间线展示关联事件及阶段，不包含多人生命周期对照、时间切片或完整历史地图。

## 数据与发布规则

新增 `topic` 表；人物、事件、三类关系、陈述和专题支持 `draft` / `published`。

1. 阅读功能迁移增加发布状态，新建内容默认草稿。后续一次性清理迁移清空全部旧内容，保留账号、权限及表结构。
2. 公共 API 使用匿名数据库客户端；浏览器直读模式也单独使用不保存登录态的匿名客户端。管理员登录不会改变前台公开视图。
3. RLS 限制公开读取：草稿不可见；关系两端都需发布；关系隐藏时，它的陈述与出处也隐藏。
4. 管理台通过带 `AdminGuard` 的 `/api/v1/editorial/:table` 读取草稿。公开 API 不提供草稿预览。
5. 发布专题时检查关联条目存在且已发布。后来下架条目，专题保留导读并显示条目正在修订。
6. 保存引用必须选择有效来源、有效挂载对象，并填写具体陈述、字段和卷／篇／页码定位。已被引用的来源不能直接删除。
7. 节点／关系的发布状态由编辑决定；本版不强制每个条目都有事实级引用，也没有独立的多人审核流程。未整理出处会明确显示待补充。

## 内容与启用顺序

旧三国、春秋战国样例、商鞅专题和配图不再作为业务内容；新的五代十国内容须经过来源核对后导入。`scripts/fixtures/reading.sql` 仅供内存数据库及浏览器模拟测试，禁止导入 Supabase。

1. 先确认远端迁移历史。保留过去已经应用的迁移文件，不能在已有库重新运行包含 DROP TABLE 的初始迁移。
2. 本轮待部署的结构迁移为 `20260928120000_editorial_reading.sql`，不再包含专题种子。
3. `20260928130000_clear_legacy_content.sql` 是一次性的旧内容清空迁移，新环境完整重放后内容为空。必须在首次导入五代十国内容前应用并记录；新内容导入后不要重复执行。远端通过 REST 清理数据不等于迁移版本已登记。
4. 再应用 `20260928140000_event_geography.sql`，增加原始纪年、今地对应、定位精度及说明，校验坐标成对和取值范围。数据库准备完成后再部署 API 和前端。前端 `VITE_API_URL` 应以 `/api/v1` 结尾；Supabase 服务角色密钥只放在后端。
5. 未配置 API 时，前台可匿名直读 Supabase；后台写入仍需要 API。
6. 空库应显示整理中状态。新内容先存草稿，在匿名窗口验证不可见，审核发布后再验证阅读和引用链。

后续上线操作见 `DEPLOYMENT.md`；本文保留首轮实现与验证记录。云端清理结果见 `CONTENT_RESET.md`。

## 本地验证

```sh
pnpm install --frozen-lockfile
pnpm test
pnpm --filter api build
pnpm --filter web build
pnpm --filter web lint
```

`pnpm test` 包含后端测试和 PGlite PostgreSQL 迁移/RLS 集成测试。测试在内存数据库中执行所有迁移，覆盖迁移后内容为空且账号权限保留、默认草稿、匿名写拒绝、隐藏端点与边、隐藏关系出处、管理员草稿读取、专题下架。

### 浏览器验证（隔离 fixture）

在所有迁移完成并验证空库后，加载虚构测试 fixture，浏览器测试拦截测试 API，不读取或修改线上内容：

```sh
HISTREE_FIXTURE_PATH=/tmp/histree-fixture.json pnpm test:publication
VITE_API_URL=http://127.0.0.1:4319/api/v1 \
VITE_SUPABASE_URL=http://127.0.0.1:4319 \
VITE_SUPABASE_ANON_KEY=local-test-key \
pnpm --filter web exec vite --host 127.0.0.1 --port 5175
```

另一个终端运行：

```sh
pnpm exec playwright install chromium
pnpm test:reading
# 已安装 Google Chrome 时也可用：
PLAYWRIGHT_CHROME_CHANNEL=chrome pnpm test:reading
```

截图默认写到 `/tmp/histree-screenshots`。浏览器测试覆盖专题→详情→出处→图谱、阶段展示、别名搜索、空结果、失败重试、390px 手机布局、后台专题/来源/引用表单。表单网络响应使用 fixture，数据库权限由独立 PostgreSQL 测试验证；这不等同于远端部署验收。
