# Histree 图片对象存储

生产素材存储在北京地域的私有 OSS Bucket `histree`。应用只公开 `public/images/<sha256>.<ext>` 中的图片；草稿、原始素材、备份和其他路径不通过此接口公开。将图片放入这个目录即表示它可在网站展示，不能上传隐私材料。

网页读取地址为 `/api/v1/media/images/<sha256>.<ext>`。API 通过 OSS 内网流式读取并返回图片，URL 不包含密钥或临时签名，可以长期保存在人物、故事、分镜等记录中。Bucket 保持私有，无需公开 Bucket 或开启浏览器直传 CORS。当前生产版没有网页上传接口，素材由受控命令行工具上传。

## 服务器配置

在现有 `/opt/histree/runtime.env` 中增加以下非密钥配置，保留原有数据库、模型等配置：

```dotenv
HISTREE_OSS_BUCKET=histree
HISTREE_OSS_REGION=oss-cn-beijing
HISTREE_OSS_INTERNAL=true
HISTREE_OSS_CREDENTIAL_TYPE=ecs_ram_role
HISTREE_OSS_ROLE_NAME=HistreeOssImagesRole
```

为 Histree ECS 绑定实例角色 `HistreeOssImagesRole`，信任主体为 `ecs.aliyuncs.com`。仅授权 [oss-policy.json](../deploy/ecs/oss-policy.json) 指定的图片目录读写权限；不授予删除、列举、Bucket 管理或其他云资源权限。不要更换服务器已有角色；已有角色时应先审阅其权限及使用方。SDK 通过 IMDSv2 获取和刷新 STS 凭证，应用与镜像中不保存账号 AccessKey。

## 上传图片

支持 PNG、JPEG、WebP、GIF，每张不超过 5 MiB。工具检查文件头而非信任扩展名或声明的 MIME；SVG 不允许进入此公开接口。图片按内容哈希命名、禁止覆盖，完全相同的图片可重复执行上传。图片格式检测不代替人工内容审阅。

构建 API 后，先只读检查：

```sh
pnpm --filter api build
node apps/api/dist/modules/storage/storage.cli.js check /absolute/path/panel.webp
```

在 ECS 受控会话中，将已审核素材复制到容器临时目录后上传：

```sh
docker cp /private/path/panel.webp histree-api:/tmp/panel.webp
docker exec histree-api node apps/api/dist/modules/storage/storage.cli.js upload /tmp/panel.webp
```

输出包含 `key`、`url`、`sha256`、`bytes` 和 `contentType`。相同内容复用同一 URL；修改图片会产生新 URL，避免一年 immutable 缓存造成旧图残留。退出受控会话后可删除本次临时上传副本，保留原始创作材料。

本地工具也支持 `HISTREE_OSS_CREDENTIAL_TYPE=sts`（配合 `OSS_ACCESS_KEY_ID`、`OSS_ACCESS_KEY_SECRET`、`OSS_SECURITY_TOKEN`）或 `access_key`（专用最小权限 RAM 用户）。只放在私密 shell 环境或忽略的环境文件中，绝不交给前端。生产优先使用 ECS 实例角色。

## 验证与回滚

1. 运行 OSS 边界与 HTTP 测试及 API 构建。
2. 上传一张已审核图片，读取同源 URL，校验图片字节 SHA-256 和 Content-Type、Cache-Control、nosniff。
3. 校验不存在的图片返回 404；OSS 故障返回 503 且不缓存；其他目录不可读取；网页上传仍为 404。
4. 执行现有生产发布验证，检查数据库就绪、阅读深链接和长卷图片哈希。

发生故障时通过现有 release 流程切回上一应用镜像；保留 OSS 图片和原有运行配置，图片不会因应用回滚被删除。此能力不创建数据库表、不修改史料及原文发布记录。首版由 ECS 代理图片流量；流量增长后可在保持 URL 稳定的前提下引入专用图片域名和 CDN。

官方参考：[初始化及 V4 签名](https://www.alibabacloud.com/help/en/oss/initialization-10)、[凭证与 ECS 角色](https://www.alibabacloud.com/help/en/oss/node-js-configure-access-credentials)。
