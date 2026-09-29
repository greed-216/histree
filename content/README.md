# 历史内容录入

## 从这里继续

当前主书为 **《资治通鉴》**，编年录入从 **884年**继续。唯一进度入口是 [yearly-progress.json](yearly-progress.json)，其中精确记录下一卷、年、段落；不再维护“朱温专题下一年”等平行游标。

```text
books/
  zizhi-tongjian/
    index.json
    source-index.json              # 本书现有引用，包括历史批次
    vol-255/year-0884/
      paragraphs.json              # 每段原文、行号、状态、对应事件
      part-01/
        content-batch.json         # 连续段落的审核和发布单元
        coverage.json              # 本批覆盖范围和下一段
        sources/                   # 原文快照与哈希
        publication.json           # 发布与匿名读回审计
    vol-256/year-0884/paragraphs.json
  jiuwudaishi/source-index.json
  xinwudaishi/source-index.json
  wuyue-beishi/source-index.json
  shu-taowu/source-index.json
```

## 录入规则

1. 按主书原文顺序处理每一段，各地同时发生的事一并整理，不围绕某个人筛选。大段可拆成多个事件，每个事件都返回具体段落。
2. 段落状态区分待整理、已审、已发布；本卷结束不代表这一年结束。884年跨卷255、256。
3. 追叙不强定为当年事件；段内跨月拆开。疑似转录错误记入核对说明，不悄悄改底本。
4. 人物、事件、关系是全站共用实体。按姓名、别名及关系端点核对身份，增添另一部书的出处时复用实体。
5. 其他书的原文按书归档，补充引用须记录它支持/质疑的主体和《通鉴》段落；不要把几部书拼成一份无来源正文。
6. source-index.json 是出处导航，不替代主书段落进度，也不自行表示已发布。

## 旧批次

`later-liang-907-923/`、`year-0907/`、`late-tang-zhu-wen-early/` 是既有发布档案，不再作为新增资料的组织模板。保留原文件和既有UUID以维护审计及固定Git引用；引用已按五部书重新建立 source-index.json。旧朱温专题只代表选录，不能宣称852—883年《通鉴》已录完。

重建出处索引：`python3 scripts/index-book-claims.py`。批次规范见 [DATA_PREPARATION.md](../docs/DATA_PREPARATION.md)。

## 其他书的补证格式

每条补充引文仍作为 fact_claim 单独存储，source 指向该书；在批次 coverage.json 的 supplements 中登记对应关系，例如：

```json
{
  "claim_key": "补充引用的稳定key",
  "source_book": "jiuwudaishi",
  "primary_paragraph_id": "zztj-v255-y0884-p008",
  "subject_key": "沿用的实体key",
  "relation": "adds"
}
```

relation 可为 corroborates（相互印证）、adds（补充细节）、conflicts（存在异说）。异说分别保留，不覆盖主书说法。发布预检检查该映射与引用主体及本批主书段落一致。
