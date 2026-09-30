# 历史数据整理规范

## 当前组织方式

以《资治通鉴》为主书，使用 `content/books/zizhi-tongjian/vol-{卷}/year-{年}/part-{批}/`；按原文连续段落录入，其他书证按书建立索引并关联主书段落与同一实体。唯一续录位置见 `content/yearly-progress.json`。旧专题批次保留为发布档案，不再作为新增目录模板。详见 [content/README.md](../content/README.md)。

书本批次使用 `scripts/prepare-book-import.py` 生成排除复用对象的SQL，`scripts/publish-book-batch.py` 默认为只读预检，`--apply` 发布后匿名读回。下文通用格式仍适用。

## 使用方式

复制 `templates/content-batch.json`，填写本批次的草稿。它是内容整理与交接格式，不能直接 POST。`scripts/prepare-content-import.py` 可校验批次并生成草稿导入、发布和下架 SQL；稳定 key 映射为确定 UUID，重复导入跳过已存在记录，不覆盖管理台后续编辑。先审阅 SQL，再通过受信任的数据库管理连接执行。

首批后梁数据位于 `content/later-liang-907-923/`，包含 6 位人物、9 个事件、一个专题。不要把测试 fixture 或旧迁移里的样例当作内容来源。

## 各数组的记录字段

必填字段加粗。所有 key 在同一批次内唯一，并在后续修订时保持不变。人名变化放 aliases，不创建重复人物。

| 数组 | 记录字段 |
| --- | --- |
| people | **key、name、description**；aliases 数组、era、birth_year、death_year、biography；status 固定 draft |
| events | **key、title、description**；start_year、end_year、time_original、dynasty、phases；地点字段见下；status 固定 draft |
| person_events | **key、person_key、event_key、role**；status 固定 draft |
| person_relationships | **key、person_a_key、person_b_key、relation_type、description**；status 固定 draft |
| sources | **key、title、source_type、edition**；author、url、note |
| claims | **key、subject_table、subject_key、field_path、claim_text、source_key、citation、note**；status 固定 draft |
| topics | **key、slug、title、description、sections**；每章含 heading、body、node_keys 数组；status 固定 draft |

- 年份用整数；未知用 JSON null，不用 0；原始纪年写入 time_original，不擅自换算月日。当前展示精度为年。
- phases 是数组，每项含 title、description，可附 start_year、end_year。
- source_type 使用 primary / reference / scholarship / digital / media；电子文本明确写电子版本，不能冒充核对过的纸本。
- subject_table 使用 person / event / person_relationship / person_event / event_causality。对应 people/events 等数组中对象的 key。
- citation 写卷次、纪年、篇章或段落。note 按“原文：…；核对说明：…”保存片段与疑点。field_path 指明支持的字段，例如 biography、start_year、location_name。
- 关系方向：`person_a —relation_type→ person_b` 表示 person_a 是 person_b 的该关系。兄长、父亲等用具体角色；对称关系保留对称类型。逆向表述由界面生成，不重复录入。历史修正见 `content/revisions/`，沿用原关系 key/UUID。
  - `甲 —父亲→ 乙`：甲是乙的父亲；`乙 —儿子→ 甲`：乙是甲的儿子。只有史料支持乙的性别时才写儿子，否则反向阅读用子女。
  - 原文明示长幼、身份时，用兄长／弟弟、丈夫／妻子；仅称兄弟、夫妻时保留对称类型，不补推长幼。反向阅读兄长用弟妹、弟弟用兄姐，避免推断另一人的性别。
  - 后台保存前检查完整关系句子，并与原文主语、宾语逐一对应；不要为反向阅读新增重复记录。
- 人物关系的有效时段先明确写进 description，并用对应 claim 支撑；当前没有关系起止年的结构化字段，不能据此生成历史阵营时间切片。
- 没有证据的事件先后顺序不录为因果；第一批不要求填写 event_causality。
- 没有审核完成的内容不发布；批次格式本身不代表事实已核对。

## 事件地点格式

第一版一个事件记录一个主要发生地点；多地战役可用 phases 叙述其他地点，不把多地移动伪装成精确路线。独立地点表、多地点关系和行军轨迹留待后续实际需要。

```json
{
  "key": "event_001",
  "title": "填写已核对的事件名称",
  "description": "说明发生了什么，以及结果。",
  "start_year": null,
  "end_year": null,
  "time_original": "保存史料原始纪年",
  "location_name": "史料中的历史地名",
  "location_modern_name": "核对后的今地对应",
  "location_lat": null,
  "location_lng": null,
  "location_precision": "unknown",
  "location_note": "说明定位依据、不确定性及对应时期。",
  "status": "draft"
}
```

- 坐标采用 WGS84 十进制度数；纬度 -90 到 90、经度 -180 到 180，成对填写或同时 null。
- location_precision：site 已定位城址／遗址；approximate 概略位置；region 区域代表点；unknown 待核对。
- 精度不是 AI 自评分。现代城市中心只能标概略位置，不能据此宣称古城址。无法可靠定位就保留空坐标。
- 定位的原文依据、古今对应或坐标来源分别作为 event 的 fact_claim，field_path 使用 location_name / location_modern_name / location_lat 等。
- 专题地图使用现代底图提供方位参考；不表示五代十国疆域或古代河道。同坐标事件在同一标记内选择。

## 发布前检查

1. key 无重复，所有关联 key 都存在；按姓名和别名检查同人异名。
2. 事件开始年不晚于结束年；不详时间保留空值。
3. 经纬度成对且范围合法，定位精度与说明一致。
4. 人物、时间、地点及关系等核心说法均有具体出处；不同解释分开记录。
5. 管理台保存草稿并核对预览；关联条目发布后再发布专题。

## 当前实现与部署

专题可按人物、年份范围筛选；年份范围采用事件时间区间相交，时间不详的事件始终保留。没有坐标的事件可选择和阅读，但不落点。人物筛选依据已公开的 person_event；关系加载失败时，其他阅读功能保留。

新增字段在 `20260928140000_event_geography.sql`，只改结构、不插入内容。上线前需要按版本顺序完成此前尚未部署的阅读结构及一次性旧内容清理迁移，再应用此迁移；第一次导入新内容后不得再次运行清理迁移。
