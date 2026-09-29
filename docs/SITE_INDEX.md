# 网站索引

[访问 Histree](https://greed-216.github.io/histree/) · [返回项目 README](../README.md)

## 公开阅读

| 页面 | 入口 | 用途 |
| --- | --- | --- |
| 专题探索 | [首页](https://greed-216.github.io/histree/) | 选择专题，开始阅读 |
| 907 年 | [进入专题](https://greed-216.github.io/histree/topics/year-907) | 阅读唐梁之际的人物、事件与出处 |
| 后梁时期（907—923） | [进入专题](https://greed-216.github.io/histree/topics/later-liang-907-923) | 梳理梁晋争霸与后唐建立 |
| 人物 | [人物列表](https://greed-216.github.io/histree/people) | 浏览人物，进入生平与相关事件 |
| 事件 | [事件列表](https://greed-216.github.io/histree/events) | 浏览事件，查看参与者和引用 |
| 图谱 | [关系图谱](https://greed-216.github.io/histree/graph) | 探索人物、事件之间的联系 |
| 搜索 | [站内搜索](https://greed-216.github.io/histree/search) | 按关键词查找人物、事件与专题 |

## 条目与史料详情

这些页面需要具体条目的标识，通常从专题、列表、图谱或引用卡片进入。下表路径以网站根目录 `/histree` 为前缀，冒号部分为实际值的占位符。

| 路径 | 内容 |
| --- | --- |
| `/topics/:slug` | 专题导读及关联内容 |
| `/people/:id` | 人物详情 |
| `/events/:id` | 事件详情 |
| `/graph/:id` | 具体节点的关系探索 |
| `/sources/:id` | 来源信息及关联引用 |
| `/evidence/:subject/:id` | 指定对象的证据与出处 |

## 管理入口

管理功能需要管理员权限，写入依赖已配置的后端 API。

| 页面 | 入口 | 用途 |
| --- | --- | --- |
| 管理台 | [打开管理台](https://greed-216.github.io/histree/admin) | 维护人物、事件与关系 |
| 内容编辑 | [打开编辑页](https://greed-216.github.io/histree/admin/editorial) | 整理专题、来源、陈述与发布状态 |

## 开发中与暂未开放的入口

- **问史料 `/ask`**：当前工作区已有页面与后端接入改动，尚有未提交内容；是否可用取决于相关代码发布及服务端配置，此处不作为已上线功能。
- **地图 `/map`**：当前 `MAPS_ENABLED = false`，地图及 `/map/edit`、`/map/annotations` 会转到图谱。后续开放时再更新本索引。

## 维护索引

页面路径以 [前端路由](../apps/web/src/App.tsx) 为准，网站前缀见 [路由入口](../apps/web/src/main.tsx) 和 [Vite 配置](../apps/web/vite.config.ts)。新增或撤下专题、调整页面路径后，请同步更新本页与 README 的入口。
