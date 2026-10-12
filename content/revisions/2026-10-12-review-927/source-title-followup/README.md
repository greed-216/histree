# 来源标题网页修正

网页组件会给来源标题添加书名号，因此仅将新来源的 title 从《旧五代史·崔协传世系》改为旧五代史·崔协传世系。原补充批次、固定来源全文和首次发布哈希保留。

首次 PATCH 已提交，但回读保护检查把 API 中随 title 派生的 label 当作独立列而失败。初始计划、预检和失败审计分别保留在 initial-* 文件。随后只读查询原生 MySQL source 行，确认所有非 title、updated_at 的原生列不变；当前计划仅移除不存在于数据库的派生 label。再次预检、旧值守卫（旧 title 不存在时零写入）及匿名回读通过，publication-mysql.json 为最终核验。实际刷新网页后显示单层《旧五代史·崔协传世系》，见 round-117/browser-audit.json。
