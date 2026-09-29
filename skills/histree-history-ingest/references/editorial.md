# 史料校核参考

## 按段处理

从 `content/yearly-progress.json` 的 `active_cursor.next_paragraph` 开始，读取对应 `content/books/zizhi-tongjian/vol-*/year-*/paragraphs.json` 与 `resources/derived/tongjian/{卷}.txt`。核对卷首与年首边界：一个年份可能跨卷。每段先列行动、主语、时间和地点，再决定事件颗粒度。不能只摘已知人物。

- `初` 可追叙前事；`后月馀`、`久之` 不能直接定成年条所在年份。若确年不明，事件 `start_year`、`end_year` 留 `null`，在 `time_original` 与核对说明解释。卷255第8段舒州事件是例子。
- 跨月拆事件，如卷255第5段；干支日保留原样，不自行换算公历。
- 当事人檄文、奏章、回信中的兵数、原因或辩解，写为“某人声称”。卷255第14段朱全忠否认知情是回信中的说法，与第13段围驿叙述并列。
- 疑似 OCR 或转录错误保留在底本快照，记入核对说明，避免用疑字推定地点或数字，如卷255第11段“充州”。可靠异文要有自己的来源与位置。
- 背景时长不能转为开始日期；卷255第10段的“几三百日”只支持到884年陈州解围时已近三百日。

## 实体和引用

人物、事件、参与和关系各自要有 `fact_claim`。摘录必须存在于来源快照，且**确实支持整理后的说法**；结构验证只能检查摘录是否存在。`citation` 至少含卷、年和段落 ID；manifest 记录来源文件 SHA-256。来源的 `edition` 要说明电子版本与校核范围。

对同名者核实时代、别名和关系后再复用，不因同名直接合并，也不因异体字直接分裂。复用对象写入 `reused-keys.json`，发布预检会查姓名别名、关系端点与已有数据库记录。时间不明或原文未确认的关系不要补成终身盟友、父子或事件因果。地图位置只有史载地名时，坐标为 `null`、`location_precision` 为 `unknown`。

为另一书的补证创建独立 claim 和 source，在 `coverage.json.supplements` 按下例连接主书段落：

```json
{
  "claim_key": "claim_...",
  "source_book": "jiuwudaishi",
  "primary_paragraph_id": "zztj-v255-y0884-p013",
  "subject_key": "event_zztj_255_0884_shangyuan_attack",
  "relation": "adds"
}
```

`relation` 可取 `corroborates`、`adds`、`conflicts`。不要给同一人物或事件另建副本；异说分别保留。
