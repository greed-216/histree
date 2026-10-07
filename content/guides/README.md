# 历史导读

`five-dynasties.json` 保存总览阶段，`later-zhou.json` 保存后周六章的编辑导读、阅读问题和已发布实体 key。`entity-overrides.json` 回指已经发布的文案勘误，避免从早期档案带回旧标题。

运行 `python3 scripts/prepare-history-guides.py`，从发布档案生成 `apps/web/src/data/history-guides.json` 与 `audit.json`。事件、人物和关系共用线上 UUID，原文引用保持底本字形。构建器检查发布审计、关键事件年代、引用及图谱端点；更改导读后须逐段核对叙述是否由所选史料支持，并匿名检查线上条目。

全站导读目录为 `/learn`，按时期、主题、人物和问题筛选。`catalog.json` 注册已整理的阅读路径，不把当前录入范围当作网站范围；新增内容可以指向新时期导读或已有数据库专题。五代总览为 `/learn/five-dynasties`，后周及六章位于 `/learn/five-dynasties/later-zhou`。旧后周地址保留重定向。首页展示入口。默认图谱只展示精选史事及实际录入的关系；双击展开线上邻接子图，可以返回本章精选。章节正文与小结是编辑概括，不能把策略、评价或异说改成已发生事实。数据面覆盖范围与导读完成范围分别说明。

这版导读随前端发布，不新增数据库实体或移动编年游标。后续编辑同一组内容文件即可扩充导读；不把批次目录按专题重新组织。数据库专题目录与搜索仍使用既有条目，政权入口是查阅入口，尚不是完整政权导读。

验证：前端 build/lint、所选批次验证、`public-readback.json`、浏览器章节翻页、原文折叠、节点探索及手机布局。959年引用年号修订记录见 `content/revisions/2026-10-07-959-citation-era/`。
