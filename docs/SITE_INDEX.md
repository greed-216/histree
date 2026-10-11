# 网站索引

[访问 Histree](https://123.56.189.146/) · [返回 README](../README.md)

| 页面 | 路径 | 用途 |
| --- | --- | --- |
| 探索首页 | `/` | 时间长卷、专题与阅读入口 |
| 历史长卷 | `/timeline/scroll` | 跨时代长图与年代窗口 |
| 时间线 | `/timeline` | 按年查看已发布事件 |
| 导读 | `/learn` | 五代／后周导读及章节 |
| 专题 | `/topics/:slug` | 专题章节与关联人物、事件 |
| 人物／事件 | `/people` / `/events` | 列表；`/:id` 阅读条目 |
| 图谱 | `/graph` / `/graph/:id` | 搜索入口、关系探索 |
| 搜索 | `/search` | 已发布内容检索 |
| 出处 | `/sources/:id` / `/evidence/:subject/:id` | 来源、引文与定位 |
| AI | `/ask` | 有出处问答与猜人物，签名匿名访问 |

登录和网页管理已撤下。地图原型按用户要求保留但 `MAPS_ENABLED=false`，`/map`、`/map/edit`、`/map/annotations` 跳至图谱；不把隐藏功能标为已上线。

页面以 `apps/web/src/App.tsx` 为准，采用根路径路由与同源 API。正式域名的可用性由实际 nginx/备案状态决定。
