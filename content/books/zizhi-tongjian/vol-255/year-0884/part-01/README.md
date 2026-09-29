# 《资治通鉴》卷255·884年·第1—7段

以主书连续段落为单位，涵盖正月到三月条：鹿晏弘任官、乐行达赐名、杨师立被征与起兵、李克用东援、唐廷讨东川、瓦子寨、婺州争夺。没有因与朱温无关而跳过段落。

共22位人物、12个事件、32条参与、2条派遣关系、84条引用。复用朱温、李克用、黄巢、钱镠；其他人物录入时检查现有姓名及别名。乐行达/乐彦祯合并一人。位置仅保留古地名，无坐标推定。

- 主来源：仓库《通鉴》卷255完整快照，SHA-256见manifest；引用含卷、年、段落ID与原文件行号。
- 第3段夹叙高仁厚讨韩秀升的前事；不另立为884年事件。“因其不发兵遏”疑脱文，保留底本而不扩写。
- 第5段跨二、三月，拆分拒代起兵、陈敬瑄受命、杨师立移檄、削爵讨伐四件事。十五万人为杨师立檄文自称数目。
- 第6、7段处在三月条下，未记具体日；不能套用前段甲子日。
- 第7段拆成三件事；钱镠一方出兵不等于钱镠本人亲自领军。
- [在线参校卷255](https://zh.wikisource.org/wiki/資治通鑑/卷255)，本批未新增其他书的补充引文。未校影印纸本。

本批仅完成连续七段。下一段为 **zztj-v255-y0884-p008：高骈从子高澞上疏吕用之罪状**，还包括舒州等地后续事，需区分“后月馀”“久之”等时间层次。884年还跨卷256，不标整年完成。

```sh
python3 content/books/zizhi-tongjian/vol-255/year-0884/part-01/build_batch.py
python3 scripts/prepare-book-import.py content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json
python3 scripts/publish-book-batch.py content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json
# 完成校核后发布：
python3 scripts/publish-book-batch.py content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json --apply
```

发布脚本先预检、插入草稿、核对，再分表发布和匿名读回。REST不是整批事务；中断可核查审计后重跑。复用记录只引用、不覆盖；生成的发布/撤回SQL也排除复用对象。不要重新运行通用SQL生成器覆盖过滤后的SQL。
