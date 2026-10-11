# 猜人物

页面在 `/ask`，使用签名匿名会话与 MySQL 事务限额。服务端从已发布人物和出处选择候选；游戏 token 绑定调用身份。年代、难度和身份筛选有数量／容量限制，候选池缓存按 generation 更新。

游戏的模型 worker 不开放工具，只有预选的公开史料；姓名判定使用登记姓名、别名和字及明确兼容形式，不凭子串判赢，不把含姓名的是非提问自动当猜名。

`apps/api/src/modules/ask/guess.service.spec.ts` 验证游戏流程、缓存与归属，`node apps/api/dsh/guess-smoke.mjs` 在模拟模型上验证真实 worker。`guess-era-eval.mjs --live` 是显式付费评测，不纳入部署流程。详见 [AI 入口](AI_GATEWAY.md)。
