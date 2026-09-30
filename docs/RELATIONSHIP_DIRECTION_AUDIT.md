# 人物关系方向检查

检查日期：2026-09-30。检查后已按约定修正11条线上关系，并通过匿名读回验证。原始检查结果如下；旧发布批次保留，修正记录见 [relations.json](../content/revisions/2026-09-30-relationship-direction/relations.json)。

范围：本地29个 content-batch.json，按稳定 key 去重后53条关系；Supabase匿名读回53条公开关系、398位人物。逐条按 UUID 比对：53条端点和关系类型完全一致，无缺失、无额外线上关系。李存勖—ruler→李嗣源的一条描述存在措辞差异：本地“本批记录”，线上“记载涉及”；关系含义一致。

统一约定：`A —关系→ B` 表示“A是B的该关系”。对称关系使用无箭头连线。反向阅读按关系类型推导，不生成第二条存储记录；仅在性别有证据时把父母的反向关系显示为儿子/女儿，否则使用子女。

## 检查结果

| 类别 | 数量 |
| --- | --- |
| 方向符合约定 | 40 |
| 方向相反 | 2 |
| 保持对称 | 2 |
| 可按原文细化 | 7 |
| 类型需统一 | 2 |

## 需处理的记录

| 当前记录 | 建议表示 | 原文依据 | 定位 |
| --- | --- | --- | --- |
| 朱瑄 —从父弟→ 朱瑾 | 朱瑾 —从父弟→ 朱瑄 | 蔡州节度使秦宗权纵兵四出，侵噬邻道。天平节度使硃瑄，有众三万，从父弟瑾，勇冠军中。宣武节度使硃全忠为宗权所攻，势甚窘，求救于瑄，瑄遣瑾将兵救之，败宗权于合乡。全忠德之，与瑄约为兄弟。 | 卷256·中和四年（884）·zztj-v256-y0884-p003·原文件第8行 |
| 朱温 —约为兄弟→ 朱瑄 | 朱温 —约为兄弟— 朱瑄 | 蔡州节度使秦宗权纵兵四出，侵噬邻道。天平节度使硃瑄，有众三万，从父弟瑾，勇冠军中。宣武节度使硃全忠为宗权所攻，势甚窘，求救于瑄，瑄遣瑾将兵救之，败宗权于合乡。全忠德之，与瑄约为兄弟。 | 卷256·中和四年（884）·zztj-v256-y0884-p003·原文件第8行 |
| 李克用 —兄弟→ 李克修 | 李克用 —兄长→ 李克修 | 八月，李克用奏请割麟州隶河东，又奏请以弟克修为昭义节度使，皆许之。由是昭义分为二镇，进克用爵陇西郡王。克用奏罢云蔚防御使，依旧隶河东，从之。 | 卷256·中和四年（884）·zztj-v256-y0884-p007·原文件第12行 |
| 乐彦祯 —父子→ 乐从训 | 乐彦祯 —父亲→ 乐从训 | 义昌节度使兼中书令王鐸，厚于奉养，过魏州，侍妾成列，服御鲜华，如承平之态。魏博节度使乐彦祯之子从训，伏卒数百人于漳南高鸡泊，围而杀之，及宾僚从者三百馀人皆死，掠其资装侍妾而还。彦祯奏云为盗所杀，朝廷不能诘。 | 卷256·中和四年（884）·zztj-v256-y0884-p016·原文件第21行 |
| 李昌言 —兄弟→ 李昌符 | 李昌言 —兄长→ 李昌符 | 凤翔节度使李昌言病，表弟昌符知留后。昌言薨，制以昌符为凤翔节度使。 | 卷256·中和四年（884）·zztj-v256-y0884-p020·原文件第25行 |
| 赵犨 —姻亲→ 朱温 | 赵犨 —姻亲— 朱温 | 犨德硃全忠之援，与全忠结婚 | 卷256·光启元年（885）·zztj-v256-y0885-p023·原文件第51行 |
| 董氏（王潮母） —母子→ 王潮 | 董氏（王潮母） —母亲→ 王潮 | 王潮兄弟扶其母董氏崎岖从军 | 卷256·光启元年（885）·zztj-v256-y0885-p024·原文件第52行 |
| 杨守亮 —兄弟→ 杨守信 | 杨守亮 —兄长→ 杨守信 | 与弟信皆为杨复光假子 | 卷256·光启二年（886）·zztj-v256-y0886-p028·原文件第88行 |
| 李全忠 —父子→ 李匡威 | 李全忠 —父亲→ 李匡威 | 八月，盧龍節度使李全忠薨，以其子匡威為留後。 | 卷256·光启二年（886）·zztj-v256-y0886-p035·维基文库固定版第189行 |
| 诸葛爽 —父子→ 诸葛仲方 | 诸葛爽 —父亲→ 诸葛仲方 | 立爽子仲方为留后 | 卷256·光启二年（886）·zztj-v256-y0886-p042·原文件第102行 |
| 高骈 —从子→ 高杰 | 高杰 —从子→ 高骈 | 骈召其从子前左金吾卫将军杰密议军事 | 卷257·光启三年（887）·zztj-v257-y0887-p007·原文件第12行 |
| 黄巢 —统属→ 朱温 | 黄巢 —统属者→ 朱温 | 诸葛爽以工北行营兵顿栎阳，黄巢将砀山硃温屯东渭桥，巢使温诱说之，爽遂降于巢。 | 卷二百五十四·唐纪七十 |
| 李存勖 —ruler→ 李嗣源 | 李存勖 —主君→ 李嗣源 | 帝密召李嗣源於帳中謀之曰：「梁人志在吞澤潞，不備東方，若得東平，則潰其心腹。東平果可取乎？」嗣源自胡柳有渡河之慚，常欲立奇功以補過，對曰：「今用兵歲久，生民疲弊，苟非出奇取勝，大功何由可成！臣願獨當此役，必有以報。」帝悅。壬寅，遣嗣源將所部精兵五千自德勝趣鄆州。比及楊劉，日已暮，陰雨道黑，將士皆不欲進，高行周曰：「此天讚我也，彼必無備。」夜，渡河至城下，鄆人不知，李從珂先登，殺守卒，啟關納外兵，進攻牙城，城中大擾。癸卯旦，嗣源兵盡入，遂拔牙城，劉遂嚴、燕顒奔大梁。嗣源禁焚掠，撫吏民，執知州事節度副使崔簹、判官趙鳳送興唐。帝大喜曰：「總管真奇才，吾事集矣。」即以嗣源為天平節度使。 | 同光元年闰四月袭郓州段 |

## 实施注意

- 两条方向修正保留原 key、UUID 及出处，调整端点，不因 key 中的姓名顺序而创建新关系。
- 七条亲属关系可按现有原文细化：父子3条、母子1条、兄弟3条。“兄长”与“哥哥”是一组显示别名，统一用“兄长／弟弟”即可。现有4条兄长记录方向正确。
- “约为兄弟”指结义关系，不能推定血缘或长幼；“姻亲”没有记载具体婚配成员，不能转换为丈夫／妻子。当前无夫妻关系记录。
- “假父”7条和“养父”7条保留史料身份区别；反向分别用“假子／养子”，展示假父时说明为史载收为假子的关系。
- 派遣者2条、任用者2条、统属者1条、主君1条方向符合约定，但须保留描述中的具体事件、时期，不能作为终身身份。
- 统属1条建议统一为统属者；ruler1条建议统一为主君。后者现有引用直接支持923年关系，描述中的908年需另加书证或收窄说明。
- 当前图谱对所有关系都画箭头；关系清单采用“A → B：关系”，详情页只显示关系词。需同步改成完整句子，并对对称关系关闭箭头。
- 已发布批次的 publication.json 绑定内容哈希，不能直接改旧 JSON 后重跑发布。修正应作为独立审计记录，核对线上旧值后更新，保留旧批次及史料快照。

## 全量记录

| key | 当前关系 | 结论 | 批次 |
| --- | --- | --- | --- |
| `relationship_person_杨师立_person_郝蠲_派遣者` | 杨师立 —派遣者→ 郝蠲 | 方向符合约定 | [content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json) |
| `relationship_person_刘汉宏_person_娄赉_派遣者` | 刘汉宏 —派遣者→ 娄赉 | 方向符合约定 | [content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json) |
| `relationship_person_li_keyong_person_li_siyuan_养父` | 李克用 —养父→ 李嗣源 | 方向符合约定 | [content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json](../content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json) |
| `relationship_person_li_keyong_person_李存信_养父` | 李克用 —养父→ 李存信 | 方向符合约定 | [content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json](../content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json) |
| `relationship_person_li_keyong_person_李存进_养父` | 李克用 —养父→ 李存进 | 方向符合约定 | [content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json](../content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json) |
| `relationship_person_li_keyong_person_李存贤_养父` | 李克用 —养父→ 李存贤 | 方向符合约定 | [content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json](../content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json) |
| `relationship_person_li_keyong_person_李存孝_养父` | 李克用 —养父→ 李存孝 | 方向符合约定 | [content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json](../content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json) |
| `relationship_person_朱瑄_person_朱瑾_从父弟` | 朱瑄 —从父弟→ 朱瑾 | 方向相反 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_zhu_wen_person_朱瑄_约为兄弟` | 朱温 —约为兄弟→ 朱瑄 | 保持对称 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_li_keyong_person_李克修_兄弟` | 李克用 —兄弟→ 李克修 | 可按原文细化 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_田令孜_person_王建_假父` | 田令孜 —假父→ 王建 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_田令孜_person_韩建_假父` | 田令孜 —假父→ 韩建 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_田令孜_person_张造_假父` | 田令孜 —假父→ 张造 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_田令孜_person_晋晖_假父` | 田令孜 —假父→ 晋晖 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_田令孜_person_李师泰_假父` | 田令孜 —假父→ 李师泰 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_乐彦祯_person_乐从训_父子` | 乐彦祯 —父子→ 乐从训 | 可按原文细化 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_李昌言_person_李昌符_兄弟` | 李昌言 —兄弟→ 李昌符 | 可按原文细化 | [content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json) |
| `relationship_person_田令孜_person_匡祐_养父` | 田令孜 —养父→ 匡祐 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0885/part-02/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0885/part-02/content-batch.json) |
| `relationship_person_赵犨_person_zhu_wen_姻亲` | 赵犨 —姻亲→ 朱温 | 保持对称 | [content/books/zizhi-tongjian/vol-256/year-0885/part-03/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0885/part-03/content-batch.json) |
| `relationship_person_董氏（王潮母）_person_王潮_母子` | 董氏（王潮母） —母子→ 王潮 | 可按原文细化 | [content/books/zizhi-tongjian/vol-256/year-0885/part-03/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0885/part-03/content-batch.json) |
| `relationship_person_杨复光_person_杨守亮_假父` | 杨复光 —假父→ 杨守亮 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0886/part-03/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0886/part-03/content-batch.json) |
| `relationship_person_杨复光_person_杨守信_假父` | 杨复光 —假父→ 杨守信 | 方向符合约定 | [content/books/zizhi-tongjian/vol-256/year-0886/part-03/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0886/part-03/content-batch.json) |
| `relationship_person_杨守亮_person_杨守信_兄弟` | 杨守亮 —兄弟→ 杨守信 | 可按原文细化 | [content/books/zizhi-tongjian/vol-256/year-0886/part-03/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0886/part-03/content-batch.json) |
| `relationship_person_李全忠_person_李匡威_父子` | 李全忠 —父子→ 李匡威 | 可按原文细化 | [content/books/zizhi-tongjian/vol-256/year-0886/part-04/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0886/part-04/content-batch.json) |
| `relationship_person_诸葛爽_person_诸葛仲方_父子` | 诸葛爽 —父子→ 诸葛仲方 | 可按原文细化 | [content/books/zizhi-tongjian/vol-256/year-0886/part-05/content-batch.json](../content/books/zizhi-tongjian/vol-256/year-0886/part-05/content-batch.json) |
| `relationship_person_高骈_person_高杰_从子` | 高骈 —从子→ 高杰 | 方向相反 | [content/books/zizhi-tongjian/vol-257/year-0887/part-01/content-batch.json](../content/books/zizhi-tongjian/vol-257/year-0887/part-01/content-batch.json) |
| `rel_early_朱诚_朱温_父亲` | 朱诚 —父亲→ 朱温 | 方向符合约定 | [content/late-tang-zhu-wen-early/content-batch.json](../content/late-tang-zhu-wen-early/content-batch.json) |
| `rel_early_王氏（朱温母）_朱温_母亲` | 王氏（朱温母） —母亲→ 朱温 | 方向符合约定 | [content/late-tang-zhu-wen-early/content-batch.json](../content/late-tang-zhu-wen-early/content-batch.json) |
| `relationship_person_朱全昱_person_zhu_wen_兄长` | 朱全昱 —兄长→ 朱温 | 方向符合约定 | [content/late-tang-zhu-wen-early/content-batch.json](../content/late-tang-zhu-wen-early/content-batch.json) |
| `rel_early_朱存_朱温_兄长` | 朱存 —兄长→ 朱温 | 方向符合约定 | [content/late-tang-zhu-wen-early/content-batch.json](../content/late-tang-zhu-wen-early/content-batch.json) |
| `rel_early_黄巢_朱温_统属` | 黄巢 —统属→ 朱温 | 类型需统一 | [content/late-tang-zhu-wen-early/content-batch.json](../content/late-tang-zhu-wen-early/content-batch.json) |
| `relationship_zhu_wen_yougui` | 朱温 —父亲→ 朱友珪 | 方向符合约定 | [content/later-liang-907-923/content-batch.json](../content/later-liang-907-923/content-batch.json) |
| `relationship_zhu_wen_youzhen` | 朱温 —父亲→ 朱友贞 | 方向符合约定 | [content/later-liang-907-923/content-batch.json](../content/later-liang-907-923/content-batch.json) |
| `relationship_keyong_cunxu` | 李克用 —父亲→ 李存勖 | 方向符合约定 | [content/later-liang-907-923/content-batch.json](../content/later-liang-907-923/content-batch.json) |
| `relationship_cunxu_siyuan` | 李存勖 —ruler→ 李嗣源 | 类型需统一 | [content/later-liang-907-923/content-batch.json](../content/later-liang-907-923/content-batch.json) |
| `relationship_person_钱镠_person_钱传镣_父亲` | 钱镠 —父亲→ 钱传镣 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_钱镠_person_钱传瓘_父亲` | 钱镠 —父亲→ 钱传瓘 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_杨涉_person_杨凝式_父亲` | 杨涉 —父亲→ 杨凝式 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_刘仁恭_person_刘守光_父亲` | 刘仁恭 —父亲→ 刘守光 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_苏循_person_苏楷_父亲` | 苏循 —父亲→ 苏楷 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_曲裕_person_曲颢_父亲` | 曲裕 —父亲→ 曲颢 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_刘守文_person_刘延祐_父亲` | 刘守文 —父亲→ 刘延祐 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_王建_person_王宗懿_父亲` | 王建 —父亲→ 王宗懿 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_zhu_wen_person_朱友璋_父亲` | 朱温 —父亲→ 朱友璋 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_zhu_wen_person_朱友雍_父亲` | 朱温 —父亲→ 朱友雍 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_zhu_wen_person_朱友徽_父亲` | 朱温 —父亲→ 朱友徽 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_zhu_wen_person_朱友文_养父` | 朱温 —养父→ 朱友文 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_刘守文_person_刘守光_兄长` | 刘守文 —兄长→ 刘守光 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_刘守光_person_刘守奇_兄长` | 刘守光 —兄长→ 刘守奇 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_li_keyong_person_张承业_任用者` | 李克用 —任用者→ 张承业 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_zhu_wen_person_敬翔_任用者` | 朱温 —任用者→ 敬翔 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_高季昌_person_倪可福_统属者` | 高季昌 —统属者→ 倪可福 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
| `relationship_person_杨渥_person_许玄应_主君` | 杨渥 —主君→ 许玄应 | 方向符合约定 | [content/year-0907/content-batch.json](../content/year-0907/content-batch.json) |
