# 元行钦赐名别名

《资治通鉴》卷269贞明元年第18段记元行钦获赐姓名李绍荣。保持既有人物 UUID，增补“元行欽”“李绍荣”“李紹榮”用于繁简检索；原文与既有批次不改。

`aliases.json` 记录原值、目标值、人物 UUID 和已发布事实声明。`python3 scripts/revise-person-aliases.py aliases.json` 为只读预检；加 `--apply` 后已通过匿名读回，审计见 `publication.json`。
