# 图片压缩、目录录入与发布

本文件在准备图片、录入故事或优化说故事加载时读取。命令从已核对的当前仓库根目录执行；详细产品契约见该检出的 `docs/STORIES.md`，OSS 配置与受控上传命令见 `docs/OBJECT_STORAGE.md`。本流程不要求修改云权限、启用 CDN 或更换域名。

## 1. 准备可追溯素材

- 原画、提示词和分镜保存到项目 `design/stories/<批次或故事>/`；检验产物保存到 `artifacts/<本次任务>/`。图片二进制不因录入而加入 Git，使用 OSS 保存线上素材。
- 记录原画像素尺寸与 SHA256，按真实像素测量每格 `crop`。图中有字幕时，裁切只取插图；网页使用独立 caption，不重复显示嵌入字幕。
- 原画只读保留；从同一 crop 输出单格图与封面。编码压缩、裁切和缩放属于已授权的网页素材处理，不需要重新生成画作。

## 2. 用现有脚本生成 WebP

依赖 Pillow 与 `cwebp`。先检查可用性；缺依赖时按当前环境的安装权限处理，不切换成付费生图来做压缩。

```sh
python3 -c 'from PIL import Image; print(Image.__version__)'
cwebp -version
python3 scripts/prepare-story-images.py \
  --catalog /absolute/task/story-draft.json \
  --source-dir /absolute/task/originals \
  --output /absolute/task/web-images \
  --update-catalog
```

`story-draft.json` 使用 `{"stories":[...]}`，各故事至少包含原画 `image` 和带 crop 的 panels，正常录入时还应有完整脚本字段。脚本按目录中的原画 SHA256，在 source-dir 递归匹配 PNG；裁切严格使用已审核的坐标，不覆盖原画。

**处理新增或指定故事时，优先用仅包含本次故事的临时目录文件。** 脚本会处理传入 catalog 的全部故事，也需要它们全部对应的原图；不要拿仅有新画的目录去跑全站 catalog。完成后按稳定 slug 将本次新增／修订条目合并回 `apps/web/src/data/stories.json`，不能用部分草稿覆盖整个故事库。

当前编码基线：

| 用途 | 输入与尺寸 | 编码 |
| --- | --- | --- |
| 单格 | 原画 crop，保留原始裁切像素 | WebP，quality 86，picture preset，method 6，sharp YUV |
| 封面 | 第一格，最长边不超过 360px | WebP，quality 80，同类编码参数 |

输出为内容哈希命名的 `.webp` 和 `manifest.json`。manifest 包含原画哈希、crop、编码质量、输出尺寸、字节数和哈希。`--update-catalog` 更新传入草稿的 `cover` 与 `panels[].image`，**不会上传 OSS**。

检查实际图片：主体不能被切错，线条、颜色、人物五官及纸纹应清楚，封面能辨认主体。当前 `scripts/test-stories.mjs` 校验衍生图不超过 160 KiB、封面边长不超过 360px、单格尺寸与 crop 一致。超出时检查源图、裁切或编码方案，不能只删掉体积校验。优化已有故事时也核对原画 URL 和哈希未变。

## 3. 字段与链接

沿用 `apps/web/src/lib/stories.ts` 和现有目录记录，不创建平行结构：

- `image`：完整原画的 URL、尺寸、SHA256，保留“看整页原画”入口。
- `cover`：小封面的 URL、width、height、sha256、bytes。
- `panels[]`：顺序编号、title、caption、alt、原图 crop，以及独立单格的 `image` 元数据（URL、width、height、sha256、bytes）。编号随实际格数，不假定八格。
- `introduction`、`afterword`：开场、解释段落、takeaway 和 sourceNote。结尾必须通过正常翻页可见，不藏在长页面下方。
- `people`：核对身份后填入站内稳定 ID，必要时为本故事无歧义的简称填 aliases。不要以搜索结果第一条代替身份核对，尤其区分淮阴韩信与韩王信。
- `sourceLinks`：站内原文使用 `/library/<book>/<section>?paragraph=<id>#paragraph-<id>`；不在站内的古籍可链接已核对的外部原文。若现有域名校验未允许来源域名，需单独评估和更新校验，不能写入不可通过的记录。
- `docs/stories/<slug>.json`：原文篇章、摘引、定位／版本信息、原画哈希、寓言／史传属性和改编边界。既有校核记录不被压缩操作覆盖。

新增故事会自动参与既有随机入口，无需另建随机故事表或触发事实库发布器。

## 4. 上传与公开校验

通过 `docs/OBJECT_STORAGE.md` 的现有受控工具上传原画、单格 WebP 与封面，只使用已授权的 `public/images/*`。当前素材上限 5 MiB／张，校验真实文件头与 MIME，内容哈希命名不可覆盖。目录保存同源 `/api/v1/media/images/<sha256>.webp`，不保存签名 URL、AccessKey 或临时凭证。

少量素材使用已有 storage CLI；批量可打包传输后调用同一 `OssImages` 上传逻辑复用连接与凭证，禁止临时授予更大权限。复制临时目录进容器时确认运行用户能读取本次公共素材，避免复制了宿主机 700 目录后找不到文件；不更改服务或私密配置权限。

每张本次素材先核对上传返回的 SHA256、大小和 MIME，再匿名读取公开 URL 比对实际字节哈希。全部成功后才把引用这些 URL 的目录带入正式发布；失败素材不使用占位图替代。

## 5. 加载和发布验收

当前阅读器由 `StoryArtwork.tsx` 读取 WebP 单格或封面，不自动读取 `story.image` 原画。`useStoryPreload.ts` 与 `story-preload.ts` 实现开场前六格、之后后五格的窗口，最多两个低优先级后台请求；已完成复用，跳页替换等待队列，离开后停止启动排队任务。正在下载的至多两张小图可完成，不能声称已强制取消。

```sh
pnpm test:stories
pnpm --filter web lint
pnpm --filter web build
```

- 用实际页面检查本次故事的全部页：1440×693、390×844、360×640、844×390。画面、图下注文和翻页栏在视口内，不引入文档滚动或裁切；确认图片已完成加载，不能只查元素存在。
- 修改预加载逻辑时验证窗口、并发、去重、失败、跳页与退出。用独立缓存环境／本地预览请求日志确认真实请求：开场只取预期单格，翻页补充下一格，不下载原始 PNG；不要给 immutable 资源加随机查询串来伪装缓存命中。
- 正常新增故事不必重写加载器或每次重测整个历史库；运行现有目录检查并验收本次相关故事。改阅读组件或图片路径时扩大到受影响的故事。
- 上线范围已授权时走现有 PR、CI、ECS 流程，核对实际运行镜像与健康状态，然后在公网确认 WebP、人物／原文链接、随机换篇及阅读布局。未经真实发布不能报告已上线。

测速区分单张文件、缓存命中和完整首屏；说明测试网络与样例，不把一次 curl 结果当所有用户的固定延迟。CDN 是否接入取决于本次任务、访问地域、访问量和带宽，不能因录入故事自动开通。未来可用独立静态域名直回源 OSS，现有后端接 OSS 不构成技术障碍。
