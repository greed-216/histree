# Histree × DeepSeek Harness 集成建议

调研日期：2026-09-29。核对仓库：`liushuang216/deepseek-harness`，提交 `4878cdabd87d4041bdaff61d04c966883b9fd07a`。第一版代码已实现，运行时与 SDK 均固定为 `0.2.0-rc.1`。使用与 fork 当前版本一致的 npm 包，不维护 dsh 内核补丁。下方先说明当前实现，再保留后续扩展设计。

## 第一版运行与验证

- 页面 `/ask`，人物/事件详情与图谱侧栏有提问入口。
- `GET /api/v1/ask/status` 检查启用状态；`POST /api/v1/ask` 返回 NDJSON 状态、会话标识、最终回答或错误。当前流式呈现检索状态，答案在引用核对通过后整体返回。
- 请求：`{ question, conversation?, context?: { kind: "person" | "event", id } }`。会话标识是随机 256 位令牌，只在当前页面内存保存，不写入地址栏；持有者可以继续该会话。匿名试用，无跨设备历史恢复。
- 每次从 Supabase 匿名客户端读取已发布内容，按 500 条分页，每表最多 10,000 条，超限明确失败。当前阶段在服务端对本次数据快照做关键词检索；尚未建立数据库全文索引。发布过滤同时由 RLS 和检索代码实施。
- 每个问题有独立临时目录、SDK 运行时和 MCP 进程。进程不继承数据库或管理凭据；MCP 只读取本次公开数据快照。会话历史由 API 管理，后续问题重新检索证据，不复用过期 citation key。
- 同时最多 2 个请求，每 IP 每小时 10 次，每会话最多 6 轮、闲置 30 分钟过期。当前配额与会话保存在单实例内存，重启会清空；多实例部署前需要共享配额与会话存储。
- 每问最多 800 字、16 次成功或尝试的业务工具调用、每次模型输出最多 2400 tokens，总执行时间 120 秒。超时/断开连接会回收专属进程组；请求完成删除临时快照与运行时日志，不持久化聊天内容。
- 原文与书名来自已发布证据。最终回答中的 `[C数字]` 必须存在于本次实际读取的证据记录，否则整条回答失败；引用链接由服务端生成，模型不能提供外部链接。存在引用不等于自动完成史学校勘。

本地要求 Node 24（系统 Node 23 缺少 dsh 入口所需的 `import.meta.main`）。配置 `apps/api/.env`：`HISTREE_ASK_ENABLED=true`、`DEEPSEEK_API_KEY`、`HISTREE_MODEL=deepseek-flash` 以及已有 Supabase URL/匿名密钥。前端设置 `VITE_ASK_API_URL=http://localhost:3001/api/v1`，不必改变普通页面的 Supabase 直连设置。

验证命令：

```sh
pnpm test
pnpm test:ask-runtime
pnpm --filter api build
pnpm --filter web lint
pnpm --filter web build
```

`test:ask-runtime` 用本地模拟模型跑真实 dsh + MCP，核验允许的工具集合，并完成搜索、读取引文、回答校验；不调用付费接口。首次真实官方模型调用已验证“朱温与敬翔是什么关系”，检索到《资治通鉴》《旧五代史》《新五代史》的对应引用。

## 部署配置

后端镜像使用 Node 24 Debian。`.dockerignore` 排除 `.env`、本地依赖、参考书库和构建产物，密钥只通过运行环境注入。问答只需 Supabase 匿名读取密钥；不要为问答配置 service role。

Render 环境：`HISTREE_ASK_ENABLED=true`、`HISTREE_MODEL=deepseek-flash`、`DEEPSEEK_API_KEY`、`SUPABASE_URL`、`SUPABASE_ANON_KEY`、`TRUST_PROXY=1`。`TRUST_PROXY` 只用于已知单层反向代理；本地保持关闭。免费实例可能冷启动，实际容量需线上验证。

GitHub 仓库变量 `VITE_ASK_API_URL` 指向后端地址并以 `/api/v1` 结尾，Pages workflow 构建时读取。这个变量只包含服务地址。若后端或密钥未就绪，页面显示未开放，并保留普通搜索入口。

## 结论

第一版做“有出处的站内问答”：沿用 Supabase 的人物、事件、关系、事实与史料引用，通过只读 MCP 工具提供给 dsh，网站自行呈现回答、引用和图谱入口。无需先建设独立向量数据库，也不需要修改 dsh 内核。

dsh 负责让模型按问题调用工具、保留会话、组织回答；检索范围、排序、数据权限与史料定位由 Histree 负责。

## 已核实的能力

| 能力 | dsh 当前实现 | Histree 用法 |
| --- | --- | --- |
| 文件检索 | glob 文件名匹配、grep 正则匹配，按文件和行号返回；通过 read 获取上下文 | 可用于内部史料整理；公众问答先用专门检索接口 |
| 网络检索 | web_search、web_fetch；DeepSeek、Exa、Perplexity 搜索提供者 | 后续作为可选补充；站内问答默认不联网扩充证据 |
| 外部数据 | MCP 工具调用，支持 stdio、Streamable HTTP；资源列表、模板与读取 | 新增 Histree MCP，只查已发布数据 |
| 语义检索 | 本次检查未发现开箱即用的文档分块、embedding 与向量知识库管线 | 如需语义召回，后续由 Histree 实现并作为工具接入 |
| 后端集成 | TypeScript SDK 启动 dsh 子进程，以 stdio JSON-RPC 驱动会话并接收事件 | 在 Histree 后端或独立 Node worker 使用 |

MCP 只是调用协议，不会自动创建或索引知识库；连接资源也不会自动将全文放入模型上下文。

## 部署结构

```text
Histree 网页：问史料 / 引用卡片 / 人物与图谱入口
  → Histree API：身份校验、会话归属、配额、流式响应
    → Node worker：dsh TypeScript SDK + 固定版本的受限运行配置
      → Histree MCP：只读检索工具
        → Supabase：已发布实体、关系、事实、出处
        → 后续史料段落索引
```

GitHub Pages 继续托管前端。dsh 需要服务端 Node 进程，不能放到静态页面中执行。仓库已有 Render API 配置，可先评估在同一容器内运行 worker；运行时版本、内存、冷启动和请求时间需实际压测，不把配置文件视为线上容量证明。模型密钥只在服务端配置。

不直接嵌入 dsh 自带 Web 控制台：当前浏览器认证对应单个 operator，不提供 Histree 所需的多用户会话权限模型。网站前端保留自己的界面和登录流程。

## 第一版工具

| 拟新增工具 | 输入 | 返回 |
| --- | --- | --- |
| search_entries | 关键词、类型、年份范围、结果数量 | 人物/事件/专题 ID、摘要、匹配依据 |
| get_entry | 类型、实体 ID | 详情、参与事件与可用证据数量 |
| get_relations | 实体 ID、关系类型、深度 1–2 | 有上限的节点和边；只遍历已发布实体与关系 |
| get_evidence | 实体或关系 ID | claim ID、原文、书名、卷次、已有 GitHub 原文 URL |

所有工具由服务端校验参数并限定数量。数据库查询使用参数绑定和发布状态过滤；不开放任意 SQL、任意文件路径、任意 URL。对外工具的运行进程不持有编辑权限或 Supabase service role 密钥。dsh 配置按允许列表只装载所需工具，去掉 shell、文件写入、插件安装、浏览器操作等能力；只在提示词里禁止是不够的。`sdk-minimal` 默认仍有高权限 shell，不能直接作为公开服务配置。

当前 SearchPage 是前端下载人物、事件、专题后做字符串包含匹配，不是服务端搜索索引。第一版将名称、别名、标题、摘要检索移到服务端，并增加证据检索；先以规范名/别名精确匹配优先，再做关键词匹配。不假设 Postgres 默认英文分词对中文史料适用。

## 用户怎么使用

- 搜索页增加“问史料”，例如“907 年哪些人参与了唐梁禅代？”
- 人物或事件页提供“围绕此条目提问”，携带实体 ID；图谱选中人物后也可进入。
- 回答下方展示证据卡：书名、卷次、原文、相关人物/事件、查看 GitHub 原文。
- 可追问“这些人有什么关系？”或“其他史书有没有不同说法？”；只对检索到的材料作答。
- 未录入、未找到原文、材料互有异说，要明确说明。区分史料直接记载、网站整理和模型推断。

模型仅输出本次工具返回的 citation ID，后端核验 ID 并生成链接，不让模型自由拼接出处 URL。核验 ID 存在只能防止虚构引用，不能证明引文支持结论；验收仍须逐条检查答案与引文的对应关系。

## 是否建设知识库

已有 Supabase 数据已是结构化知识底座；应先复用，避免重复录入。增加原文检索时，建立可重建的段落索引，而不是把全部 PDF 一次塞给模型。

建议第二阶段从 907–923 年相关《资治通鉴》《旧五代史》《新五代史》开始，按卷、年、段落组织。段落记录稳定 ID、书籍/版本、卷次、原文、检索用繁简归一文本、原文件路径、固定提交、行号或页码、文件 hash、人物关联、年代范围与年代确定程度。保留原文不改写；传记横跨多年，不能简单按文件名归到单一年份。PDF 需先提取文本，扫描页需 OCR，保留页码并检查识别质量。

初期对段落做关键词、别名与年代过滤。若“意思接近但用词不同”的问题确实漏检，再加入 embedding 和向量召回，与关键词结果合并排序。向量索引必须由原始段落派生，更新或撤稿时同步失效；它不替代原文和出处。

## 会话与验收

SDK 当前没有单会话关闭、单 prompt 取消方法；进程内会话会保留到进程关闭。第一版以短会话为单位使用受控 worker，服务端维护用户到会话的归属，同一会话串行处理；超时或取消时结束专属 worker 并回收。不要在共享所有用户的进程里用杀进程实现某个用户的取消。后续再按压测结果优化池化和持久化。

通过 SDK 的事件/通知回调转为网站流式输出；不能把 prompt 接收成功当作答案完成。断线重试需避免重复产生付费请求。设置问题长度、会话轮数、工具调用、输出 token、总执行时间和并发上限，实际模型调用费用需运行后计量。

首批验收用 20–30 个有标准出处的问题，覆盖姓名别名、年份过滤、人物关系、多书比较、资料不足和跨用户会话隔离。记录检索命中、引文支持程度、响应时间和 token 用量。上线前检验仅有允许的工具，未发布材料不可检索，普通关键词搜索在问答失败时仍可用。

## 调研依据

以下链接固定到本次检查的提交：

- [TypeScript SDK](https://github.com/liushuang216/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/sdk/client/README.md)
- [SDK server 与会话限制](https://github.com/liushuang216/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/sdk/server/README.md)
- [MCP 配置](https://github.com/liushuang216/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/mcp/mcp-client/README.md)
- [文件检索](https://github.com/liushuang216/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/fs/tool-fs-search/README.md)
- [网络工具](https://github.com/liushuang216/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/web/tool-web/README.md)
- [浏览器身份模型](https://github.com/liushuang216/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/client/connection/README.md)
- [sdk-minimal 默认能力](https://github.com/liushuang216/deepseek-harness/blob/4878cdabd87d4041bdaff61d04c966883b9fd07a/packages/bundle/sdk-minimal/README.md)

dsh 处于 developer preview，当前文档明确提示接口可能出现破坏性变化。集成时固定运行时、SDK 和插件版本，升级后重跑检索与引用验收。
