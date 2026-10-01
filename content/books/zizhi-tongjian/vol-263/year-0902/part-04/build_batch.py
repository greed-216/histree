"""Curate Tongjian 263, year 902, consecutive paragraphs 25–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 60))
primary = 'tongjian-263-902-april'
primary_summer = 'tongjian-263-902-summer'
old_five = 'jiuwudaishi-002-902-fengxiang'
new_tang = 'xintangshu-190-feng-hongduo'
new_five = 'xinwudaishi-067-902-xu-wan'

B = {'format_version': 1, 'batch_key': 'zztj-v263-y0902-p025-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-02/sources/library' / primary, '352a55e', '司马光等'),
    (primary_summer, P / 'sources/library' / primary_summer, '648c8e6', '司马光等'),
    (old_five, P / 'sources/library' / old_five, '648c8e6', '薛居正等'),
    (new_tang, P.parent / 'part-03/sources/library' / new_tang, 'e75f760', '欧阳修、宋祁等'),
    (new_five, P / 'sources/library' / new_five, '648c8e6', '欧阳修等'),
]
source_dirs = {sk: d for sk, d, _, _ in source_specs}
manifest = []
for sk, d, commit, author in source_specs:
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file=os.path.relpath(d / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, primary_summer)}
for n in range(25, 33):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/263.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠': '朱温', '全忠': '朱温', '茂贞': '李茂贞', '克用': '李克用', '珂': '王珂', '存敬': '张存敬', '叔琮': '氏叔琮', '重荣': '王重荣', '倚': '李倚', '正雅': '王正雅', '李存审': '符存审', '李继昭':'符道昭', '刘夫人':'刘夫人（李克用妻）', '曹氏':'曹氏（李存勖母）', '李继诲':'周承诲', '李彦弼':'董彦弼', '吉谏':'王宗黯', '李继徽':'杨崇本'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_263_0902_04_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷263·天复二年（902）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷263天复二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=902):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_263_0902_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '902年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '902年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_263_0902_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_263_0902_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 25: Fengxiang battles, reported speech, and encirclement.
event('maozhen_defeated_north_guoxian', '李茂贞率军于虢县北战朱全忠而败',25,
      '甲申，李茂贞大出兵，自将之，与硃全忠战于虢县之北，大败而还，死者万馀人。',
      [('李茂贞','率军败退者'),('朱温','交战对方')],when='902年六月甲申',place='虢县北',
      note='万余死者为主书数字；旧五代史记癸未大战，日期异文不强合。')
event('kong_takes_fengzhou', '孔勍丙戌出散关取凤州',25,
      '丙戌，全忠遣其将孔勍出散关攻凤州，拔之。',
      [('朱温','遣将者'),('孔勍','攻取者')],when='902年六月丙戌',place='散关、凤州')
event('zhu_encircles_fengxiang', '朱全忠丁亥至凤翔城下建五寨围城',25,
      '丁亥，全忠进军凤翔城下。全忠朝服向城而泣，曰：“臣但欲迎车驾还宫耳，不与岐王角胜也。”遂为五寨环之。',
      [('朱温','围城者')],when='902年六月丁亥',place='凤翔',
      note='“只欲迎驾”是朱全忠城下自述，不作动机已证实的事实；五寨为主书围城记载。')

# 26: Feng Hongduo after defeat; the Shang Gongnai episode is retrospective.
event('yang_invites_feng_hongduo', '杨行密遣使招抚败后欲入海的冯弘铎',26,
      '冯弘鐸收馀众沿江将入海，杨行密恐其为后患，遣使犒军，且说之曰：“公徒众犹盛，胡为自弃沧海之外！吾府虽小，足以容公之众，使将吏各得其所，如何？”',
      [('冯弘铎','败后受招者'),('杨行密','遣使招抚者')],when='902年六月葛山战后',place='长江沿岸',
      note='“恐为后患”是主书所述杨行密动机；冯弘铎并未实际入海。')
event('yang_meets_feng_dongtang', '杨行密于东塘登船慰冯弘铎并署其为副使',26,
      '弘鐸至东塘，行密自乘轻舟迎之，从者十馀人，常服，不持兵，升弘鐸舟，慰谕之，举军感悦。署弘鐸淮南节度副使，馆给甚厚。',
      [('杨行密','迎接及任命者'),('冯弘铎','受迎及任命者')],when='902年葛山战后；确日未载',place='东塘')
event('shang_gongnai_asks_runzhou', '尚公乃曾为冯弘铎求润州而杨行密不许',26,
      '初，弘鐸遣牙将丹徒尚公乃诣行密求润州，行密不许。',
      [('冯弘铎','遣使者'),('尚公乃','求润州者'),('杨行密','未允者')],
      when='初：902年以前；确年未载',place='润州',year=None,
      note='“初”为追叙，不能当作902年六月发生。')
event('yang_appoints_li_shenfu_shengzhou', '杨行密以李神福为升州刺史',26,
      '行密以李神福为升州刺史。',
      [('杨行密','任命者'),('李神福','受任者')],when='902年六月条；确日未载',place='升州')

# 27–28: Huainan expedition and Kong Jing's western campaign.
event('yang_campaigns_against_zhu', '杨行密发兵讨朱全忠并以李承嗣权知淮南军府',27,
      '杨行密发兵讨硃全忠，以副使李承嗣权知淮南军府事。',
      [('杨行密','发兵者'),('朱温','讨伐对象'),('李承嗣','权知军府者')],
      when='902年六月后、七月前；确日未载',place='淮南')
event('xu_wen_small_boats_deliver_grain', '徐温主张小艇运粮并先到宿州军中',27,
      '都知兵马使徐温曰：“运路久不行，葭苇堙塞，请用小艇，庶几易通。”军至宿州，会久雨，重载不能进，士有饥色，而小艇先至，行密由是奇温，始与议军事。',
      [('徐温','献小艇运粮议者'),('杨行密','采纳并赏识者')],
      when='902年宿州战期间',place='宿州',
      note='小艇先至不等于全军粮道打通；随后仍因粮运不继撤军。')
event('yang_abandons_suzhou_siege', '杨行密久攻宿州不克，因粮运不继撤军',27,
      '行密攻宿州，久不克，竟以粮运不继引还。',
      [('杨行密','围攻并撤军者')],when='902年宿州战期间；确日未载',place='宿州')
event('kong_takes_cheng_long', '孔勍七月取成陇二州并自故关退兵',28,
      '秋，七月，孔勍取成、陇二州，士卒无斗者。至秦州，州人城守，乃自故关归。',
      [('孔勍','攻取及退军者')],when='902年七月',place='成州、陇州、秦州、故关',
      note='主书仅称取成陇二州，秦州坚守；旧五代史称凤陇成三州皆下，留异说。')

# 29: Wei Yifan's restoration attempt and Han Wo's refusal.
event('wei_yifan_bribery_in_office', '韦贻范居相时多受赂并许人官职',29,
      '韦贻范之为相也，多受人赂，许以官。',
      [('韦贻范','受赂许官者')],when='902年韦贻范任相期间；确日未载',
      note='原文叙述其任相时的行为，未列行贿者、金额或实际授官结果。')
event('wei_yifan_debts_and_restoration', '韦贻范遭母丧后求起复，刘延美为债权人',29,
      '既而以母丧罢去，日为债家所噪。亲吏刘延美，所负尤多，故汲汲于起复，日遣人诣两中尉、枢密及李茂贞求之。',
      [('韦贻范','求起复者'),('刘延美','债权人'),('李茂贞','受求者')],
      when='902年七月甲戌前；确日未载',
      note='主书回顾韦贻范居相多受贿，具体交易未列；这里只记债务与求起复。')
event('han_wo_refuses_draft', '韩偓甲戌拒草韦贻范起复制并上疏',29,
      '甲戌，命韩偓草贻范起复制，偓曰：“吾腕可断，此制不可草！”即上疏论贻范遭忧未数月，遽令起复，实骇物听，伤国体。',
      [('韩偓','拒草并上疏者'),('韦贻范','拟起复者')],when='902年七月甲戌',
      note='“骇物听、伤国体”为韩偓疏中论点；起复制最终未颁。')
event('emperor_cancels_wei_draft', '昭宗停止草韦贻范起复制并褒韩偓',29,
      '上即命罢草，仍赐敕褒赏之。',
      [('李杰','罢草并褒奖者'),('韩偓','受褒者')],when='902年七月甲戌后')
event('maozhen_protests_han_wo', '李茂贞八月责韩偓拒草，昭宗解释采纳其疏',29,
      '八月，乙亥朔，班定，无白麻可宣。宦官喧言韩侍郎不肯草麻，闻者大骇。茂贞入见上曰：“陛下命相而学士不肯草麻，与反何异！”',
      [('李茂贞','责问者'),('李杰','答复者'),('韩偓','被责者')],when='902年八月乙亥朔',
      note='“与反何异”是李茂贞指责，不作为韩偓谋反事实。')
event('liu_yanmei_suicide', '韦贻范止求起复后刘延美投井身亡',29,
      '贻范乃止。刘延美赴井死。',
      [('韦贻范','停止求起复者'),('刘延美','投井者')],when='902年八月乙亥后；确日未载',
      note='原文先记李茂贞称安置邠州再记贻范止、刘死；不推死因细节。')

# 30–31: relief at Sanyuan and earlier creation of Wuyong forces.
event('li_maoxun_defeated_sanyuan', '李茂勋屯三原救李茂贞，康怀英孔勍击使遁去',30,
      '保大节度使李茂勋将兵屯三原，救李茂贞。硃全忠遣其将康怀英、孔勍击之，茂勋遁去。',
      [('李茂勋','救援而遁者'),('李茂贞','受援者'),('朱温','遣将者'),('康怀英','追击者'),('孔勍','追击者')],
      when='902年八月条；确日未载',place='三原',
      note='同段明言茂勋为茂贞从弟；旧五代史相关后续另有李周彝异名，未直接合并。')
rel='relationship_person_李茂贞_person_李茂勋_从兄'
B['person_relationships'].append(dict(key=rel,person_a_key=people['李茂贞'],person_b_key=people['李茂勋'],
    relation_type='从兄',description='《资治通鉴》称李茂勋为李茂贞之从弟。',status='draft'))
claim('person_relationship',rel,'description','李茂贞是李茂勋的从兄。',30,
      '茂勋，茂贞之从弟也。','原文明示同宗从弟与长幼，取反向从兄表示 A 是 B 的该关系。')
event('qian_forms_wuyong', '钱镠收孙儒余部编为武勇都',31,
      '初，孙儒死，其士卒多奔浙西，钱镠爱其骁悍，以为中军，号武勇都。',
      [('孙儒','已死原部主'),('钱镠','收编者')],when='初：孙儒死后、902年以前；确年未载',
      place='浙西',year=None,
      note='“初”标识追叙；孙儒之死及收编并非断定发生于902年。')
event('du_leng_warns_qian', '杜稜劝钱镠以土人代武勇都而未获采纳',31,
      '行军司马杜稜谏曰：“狼子野心，他日必为深患，请以土人代之。”不从。',
      [('杜稜','进谏者'),('钱镠','未采纳者')],when='初：武勇都成立后；确年未载',year=None,
      note='“狼子野心”是杜稜当时的警告，不作为对全部士卒的事实判断。')

# 32: Hangzhou rebellion, return and relief, preserving sequence.
event('xu_wan_labor_grievance', '钱镠命徐绾率武勇都治沟洫，成及请停而不从',32,
      '镠如衣锦军，命武勇右都指挥使徐绾帅众治沟洫；镇海节度副使成及闻士卒怨言，白镠请罢役，不从。',
      [('钱镠','下令并未停役者'),('徐绾','率军治沟洫者'),('成及','请停役者')],
      when='902年八月条；确日未载',place='衣锦军')
event('xu_wan_attempts_assassination', '徐绾丙戌谋席间杀钱镠不成',32,
      '丙戌，镠临飨诸将，绾谋杀镠于座，不果，称疾先出。',
      [('徐绾','谋杀未遂者'),('钱镠','被谋杀者')],when='902年八月丙戌',
      note='只记未遂，不写钱镠受伤。')
event('xu_wan_rebels_hangzhou', '徐绾丁亥入杭州纵兵焚掠并与许再思合兵',32,
      '丁亥，命绾将所部先还杭州。及外城，纵兵焚掠。武勇左都指挥使许再思以迎侯兵与之合，进逼牙城。',
      [('徐绾','纵兵者'),('许再思','合兵者'),('钱镠','命先还者')],when='902年八月丁亥',place='杭州')
event('qian_son_defends_inner_city', '钱传瑛马绰闭牙城守，潘长击退徐绾至龙兴寺',32,
      '镠子传瑛与三城都指挥使马绰等闭门拒之，牙将潘长击绾，绾退屯龙兴寺。',
      [('钱传瑛','守城者'),('马绰','守城者'),('潘长','反击者'),('徐绾','退屯者')],
      when='902年八月丁亥后',place='杭州牙城、龙兴寺')
event('qian_returns_disguised', '钱镠闻变疾返，微服夜入杭州牙城',32,
      '镠微服乘小舟夜抵牙城东北隅，逾城而入。',
      [('钱镠','微服返城者')],
      when='902年八月丁亥后夜间',place='杭州牙城',
      note='原文前句“建镠旗喜与绾战”疑电子转录损字，不据此确定成及具体行动；这里只记可逐字核实的微服夜入，待纸本校。')
event('du_jianhui_relief', '杜建徽自新城援杭州并破徐绾焚北门之谋',32,
      '武安都指挥使杜建徽自新城入援，徐绾聚木将焚北门，建徽悉焚之。建徽，稜之子也。',
      [('杜建徽','入援者'),('徐绾','欲焚北门者'),('杜稜','杜建徽之父')],
      when='902年徐绾叛乱期间',place='杭州北门')
event('gao_wei_killed_lingyin', '高渭奉父高彦命援杭州，至灵隐山遭伏被杀',32,
      '湖州刺史高彦闻难，遣其子渭将兵入援，至灵隐山，绾伏兵击杀之。',
      [('高彦','遣援者'),('高渭','被杀者'),('徐绾','设伏者')],
      when='902年徐绾叛乱期间',place='灵隐山')
event('luo_yin_wall_recalled', '钱镠筑罗城旧事中罗隐建议城楼内向，此时被追忆',32,
      '初，镠筑杭州罗城，谓僚佐曰：“十步一楼，可以为固矣。”掌书记馀杭罗隐曰：“楼不若皆内向。”至是人以隐言为验。',
      [('钱镠','筑城者'),('罗隐','进言者')],when='初：杭州罗城兴筑时；确年未载',place='杭州',year=None,
      note='此为追叙与后人回看，不把罗城兴筑或罗隐进言置于902年。')

# Only explicit genealogy, with the direction A is B's relation.
for rel, a, b, kind, n, quote, desc in [
    ('relationship_person_钱镠_person_钱传瑛_父亲','钱镠','钱传瑛','父亲',32,'镠子传瑛','钱镠是钱传瑛的父亲。'),
    ('relationship_person_杜稜_person_杜建徽_父亲','杜稜','杜建徽','父亲',32,'建徽，稜之子也','杜稜是杜建徽的父亲。'),
    ('relationship_person_高彦_person_高渭_父亲','高彦','高渭','父亲',32,'高彦闻难，遣其子渭将兵入援','高彦是高渭的父亲。'),
]:
    B['person_relationships'].append(dict(key=rel,person_a_key=people[a],person_b_key=people[b],
        relation_type=kind,description=desc,status='draft'))
    claim('person_relationship',rel,'description',desc,n,quote,'原文明示父子；关系方向为父亲指向儿子。')

extra(old_five,'event','event_zztj_263_0902_maozhen_defeated_north_guoxian','description',
      '《旧五代史》卷二记六月癸未岐军与朱军大战，主书作甲申。',
      '六月丁丑，次於虢縣。癸未，與岐軍大戰，自辰至午，殺萬餘眾',25,'conflicts',
      '月相同、干支日不同；旧五数字及战时另记，不强合为主书确日。')
extra(new_tang,'event','event_zztj_263_0902_yang_meets_feng_dongtang','description',
      '《新唐书》卷一百九十亦记杨行密东塘迎冯弘铎并表副使。',
      '行密挐飛艫，不持兵入其軍，執弘鐸手尉勉，遂以歸，表為淮南節度副使',26,'corroborates',
      '传文写行密亲至及表副使；主书写署副使，任命形式细节保留各自措辞。')
extra(old_five,'event','event_zztj_263_0902_kong_takes_cheng_long','description',
      '《旧五代史》卷二记孔勍七月取凤陇成三州，主书仅记成陇并称秦州守住。',
      '七月丙午，岐軍復出求戰，帝軍不利。是月，遣孔勍帥師取鳳、隴、成三州，皆下之',28,'conflicts',
      '两书均有凤州取城事，但月份、成陇攻取合并叙事不同；不把三州归在主书第28段同一时日。')
extra(new_five,'event','event_zztj_263_0902_xu_wan_rebels_hangzhou','description',
      '《新五代史》卷六十七明记天复二年徐绾许再思叛并焚掠杭州城郭。',
      '天復二年，封鏐越王。鏐巡衣錦城，武勇右都指揮使徐綰與左都指揮使許再思叛，焚掠城郭',32,'corroborates',
      '新五将两将并列；主书细记徐绾先纵兵、许再思随后合兵。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,33):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷263天复二年第25—32段：凤翔围城、冯弘铎归杨行密、宿州军粮、孔勍取成陇、韦贻范起复未成、李茂勋援岐、武勇都追叙、徐绾许再思杭州叛乱。追叙确年未定；两书日期与州名异文并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=263,year=902,
    primary_source_key=primary,primary_source_keys=[primary,primary_summer],
    paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],
    coverage='卷263天复二年共59个非空段落中的第25—32段连续处理；本年尚未完成。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
