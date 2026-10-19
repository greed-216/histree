# 史料库

史料库沿用统一目录中的书目、底本版本、卷章和稳定段落 ID，按“书 → 卷章 → 原文段落”保存在数据库；阅读可用状态与人物、事件的发布/审阅状态独立，不改任何录入账本。首批选取目录角色为 foundation、chronological_primary、chronological_primary_continuation 的 26 部书；《清史稿》仍按既定范围暂缓。

## 页面与接口

- `/library`：书目与原文检索；可限定书目，按原文用字检索 2—80 字的连续字符串，繁简异体分别搜索。
- `/library/:book`：本书卷章目录。
- `/library/:book/:section`：按原顺序分批读原文，每批 40 段，可切换卷章、翻页；`paragraph` 定位参数自动加载该段所在页并高亮，不能用其他卷的段落伪造定位。
- 既有“阅读原文”入口先核对出处对应的同底本段落，再跳入书中；无法唯一核对的旧出处继续展示既有引用片段。来源页保留“在书中连续阅读”。不展示 GitHub 链接、机器编号或内部版本处理说明。

`GET /api/v1/library`、`/library/search`、`/library/:book`、`/library/:book/sections/:section` 和 `/sources/:id/location` 只读。正文按页读取，不一次下载全书。搜索只返回最多 20 条短上下文和下一页标志；查询采用参数绑定和字面量 LIKE 转义，`%`、`_` 不是用户通配符；卷章/书目及正文顺序有索引，保留数据库执行超时，不增加不准确的繁简替换或语义匹配。此版本未提供全文分词索引，原生 MySQL 的全库搜索性能须在上线前实测。

卷内正文、注文、表格、原有提示分别保存并展示。自动生成的导航标题不充作原文；书中缺字/缺图风险按卷提供简短提示。数据库的 `available` 仅表示原文可以阅读，不表示事实已经校核或全卷已完成录入。

## 数据及原文证明

`library_book` 保存书目/版本与数据集哈希，`library_asset` 去重保存底本文件标识，`library_section` 保存原顺序，`library_paragraph` 保存逐字原文、SHA-256、原文件字符范围和类型，`library_source_link` 保存可核对的旧来源到段落的映射。原文件与既有已发布快照不改、不删。

准备程序从 catalog 指定的 gzip 分段和 sections 文件读取，先核对产物哈希，再按 locator 从经过哈希核对的底本导出正文；不用经过归一化的搜索摘要或 `reading.txt` 代替原文。逐段正文哈希必须与 locator 原片段相符。来源跳转要求书名身份一致、原文字节哈希相同，并有稳定段落 ID 或唯一相同段落；不足以确定的映射暂缓，不按人物名或大致相似文本猜测。

本次本地准备结果：26 部书、376,987 个阅读段落；2,190 份旧来源可核对跳转，77 份继续使用原片段。此前原文回填中另有 2 份无明确 JSONL 行号的旧来源保留待定位。计数只是阅读覆盖，不是史实审阅进度。

## 本地运行

只写指定临时目录和隔离数据库，不读生产环境文件：

```sh
python3 scripts/prepare-reading-library.py --output /private/tmp/histree-library-preview/data
python3 scripts/import-reading-library.py /private/tmp/histree-library-preview/data/manifest.json
node scripts/import-reading-library-local.mjs
pnpm --filter api build
node scripts/test-library-data.mjs
node scripts/run-library-preview.mjs
```

原文数据库在 `/private/tmp/histree-library-preview/database`，预览默认端口 5189（占用时用 `PORT` 指定其他端口）；反馈用独立本地库。必须先导入、测试并关闭测试连接，再启动预览，避免两个本地 PGlite 进程同时打开同一库。已有相同版本不会覆盖，已有不一致版本停止；不同底本需要独立迁移设计，不用新文本覆盖旧引用。

本地导入使用实际应用读取 SQL，经参数/引号方言适配连接 PGlite，正文确实从数据库读取；不是临时读静态 JSON 展示。导入按书事务提交，完成逐段正文哈希读回后才标记可读，中断时未完成的书不开放。准备文件和本地数据库是可重建缓存，不加入 Git。

## MySQL 上线流程

原生 MySQL 的 `apps/api/mysql/migrations/20261019_library.sql` 与 `scripts/import-reading-library.py` 已准备，默认只做离线校验；显式提供 `--mysql-env` 也仍只读预检，写入需 `--apply`，缺表时还需明确 `--create-tables`。DDL 不受事务回滚保护。导入共用内容发布写锁，每本书事务写入并逐字读回，拒绝覆盖不同版本；旧出处映射只新增或复用同值记录。

上线前须验证原生 MySQL 的 DDL、事务/重跑、索引、全库搜索性能与匿名 API，再完成网站实际阅读与定位验收。验收脚本 `node scripts/test-library-mysql.mjs --mysql-env <私密文件>` 读取实际应用服务，并用事务回滚验证可选邮箱与反馈去重。原文库上线不重新发布旧人物/事件批次，也不推进任何史书的事实录入游标。
