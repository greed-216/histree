# Histree · 历史之树

从专题阅读历史，通过人物、事件和关系图谱梳理脉络，沿着引用回到具体史料。

**[访问网站（ECS IP）](https://123.56.189.146/)** · **[备用阅读站（GitHub Pages）](https://greed-216.github.io/histree/)** · **[正式域名（备案办理中）](https://histree.wiki/)** · **[网站索引](docs/SITE_INDEX.md)** · [GitHub 仓库](https://github.com/greed-216/histree)

## 从这里开始

当前内容建设聚焦五代十国，可从以下专题进入：

| 入口 | 内容 |
| --- | --- |
| [907 年](https://greed-216.github.io/histree/topics/year-907) | 围绕唐梁之际的人物、事件与史料阅读 |
| [后梁时期（907—923）](https://greed-216.github.io/histree/topics/later-liang-907-923) | 梁晋争霸、继承与后唐建立的历史脉络 |
| [人物](https://greed-216.github.io/histree/people) / [事件](https://greed-216.github.io/histree/events) | 查阅条目、参与关系与具体出处 |
| [关系图谱](https://greed-216.github.io/histree/graph) | 沿人物与事件的联系继续探索 |
| [搜索](https://greed-216.github.io/histree/search) | 查找人物、事件和专题 |

史料摘录、史家评价与专题解释分别记录；存在异文或尚待核实的内容，在引用与核对说明中保留差异。内容批次及其核读记录见 [content](content)。

## 项目结构

采用 pnpm workspace，前端为 React + TypeScript + Vite，后端为 NestJS，数据库与登录使用 Supabase。

```text
apps/web/              网站前端
apps/api/              API 与管理接口
packages/shared-types/ 前后端共享类型
supabase/              数据库配置与迁移
content/               历史内容批次、核读记录与修订
resources/             史料资源目录与素材说明
scripts/               内容导入、资源索引与验证脚本
docs/                  产品、内容与部署文档
```

## 本地启动

准备 Node.js 24、pnpm 10.28.1，以及已配置数据库结构的 Supabase 开发项目。

```sh
git clone https://github.com/greed-216/histree.git
cd histree
pnpm install --frozen-lockfile
cp apps/web/.env.example apps/web/.env.local
```

编辑 `apps/web/.env.local`：

```dotenv
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_ANON_KEY
# 使用本地 API 时保留；仅运行公开阅读前端时删除这一行。
VITE_API_URL=http://localhost:3000/api/v1
```

```sh
pnpm --filter web dev
```

打开 [本地网站](http://localhost:5173/histree/)（实际端口以 Vite 输出为准）。未设置 `VITE_API_URL` 时，公开阅读直接查询 Supabase；数据可见范围由数据库发布状态和 RLS 策略控制。

管理写入需要启动 API。在另一个终端执行：

```sh
cp apps/api/.env.example apps/api/.env
# 填写与前端同一开发项目的 Supabase URL、anon key 和 service role key。
pnpm --filter api start:dev
```

API 默认地址为 `http://localhost:3000`，业务接口位于 `/api/v1`。管理操作需要管理员账号。服务角色密钥只放在后端环境变量中，不能配置为 `VITE_*` 或提交到仓库。

数据库和内容准备参见 [部署说明](docs/DEPLOYMENT.md) 与 [数据整理规范](docs/DATA_PREPARATION.md)。迁移包含历史内容清理操作，执行前应审阅 SQL，并使用独立开发数据库。

## 常用检查

```sh
pnpm test
pnpm --filter api build
pnpm --filter web lint
pnpm --filter web build
```

前端构建输出位于 `apps/web/dist`，与 NestJS API 一起打入 `apps/api/Dockerfile` 构建的镜像，由 [ECS 工作流](.github/workflows/deploy-api.yml) 在相关改动推送 `main` 后测试、构建并部署。ECS nginx 负责 HTTPS，应用容器提供根路径页面和 `/api/v1` 接口；数据库、登录及 AI 身份／额度网关继续使用 Supabase。GitHub Pages 工作流保留为手动备用发布。构建、运行环境和回滚见 [ECS 操作说明](deploy/ecs/README.md)，架构及上线验收见 [部署说明](docs/DEPLOYMENT.md)。

截至 2026-10-08，合并应用已部署，histree.wiki 的阿里云证书已安装；ICP备案仍在办理，域名配置为 HTTP 503 待上线页面。服务器端 TLS 验证通过，当前网络的公网 TLS 握手仍失败，公网可用性尚未确认。IP 入口 `https://123.56.189.146/` 已按用户授权开放完整前端与普通 API；域名入口继续待上线。应用部署、证书安装、IP 访问与域名正式上线分别验收。

## 文档导航

- [网站索引](docs/SITE_INDEX.md)：公开页面、详情地址和管理入口。
- [内容方向](docs/CONTENT_FOCUS.md)：当前五代十国建设范围。
- [产品路线图](docs/PRODUCT_ROADMAP.md)：长期规划；当前进展以文首更新及代码为准。
- [内容模型](docs/CONTENT_MODEL.md) / [数据整理规范](docs/DATA_PREPARATION.md)：条目、关系、来源与引用的组织方式。
- [部署说明](docs/DEPLOYMENT.md) / [ECS 操作说明](deploy/ecs/README.md)：架构、镜像发布、证书安装、回滚和上线验收。
- [907 年核读记录](content/year-0907/README.md) / [后梁专题](content/later-liang-907-923/README.md)：内容批次与依据。
- [资源说明](resources/README.md)：史料文件与资源组织。

## 许可证

项目代码使用 [MIT License](LICENSE)。史料、图像及其他外部资源的来源与使用条件，请另行查阅对应资源说明。
