"""Curate Tongjian 265, year 905, consecutive paragraphs 35–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 61))
primary_autumn = 'tongjian-265-905-autumn'
old_sep = 'jiutangshu-020-905-september'
old_campaign = 'jiuwudaishi-002-xiangyang-campaign'
new_zhao = 'xinwudaishi-041-zhaokuangning'
new_sep = 'xintangshu-010-september'
new_wuzhou = 'xintangshu-010-wuzhou'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0905-p035-p040',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_autumn, P / 'sources/library' / primary_autumn, '0ad8e2bd', '司马光等'),
    (old_sep, P / 'sources/library' / old_sep, '0ad8e2bd', '刘昫等'),
    (old_campaign, P.parent / 'part-05/sources/library' / old_campaign, '49927098', '薛居正等'),
    (new_zhao, P / 'sources/library' / new_zhao, '0ad8e2bd', '欧阳修等'),
    (new_sep, P / 'sources/library' / new_sep, '0ad8e2bd', '欧阳修等'),
    (new_wuzhou, P / 'sources/library' / new_wuzhou, '0ad8e2bd', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_autumn,)}
for n in range(35, 41):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '祐':'李祐（蔡王）', '禔':'李禔', '全师朗':'王宗朗', '师朗':'王宗朗', '仁规':'刘仁规'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0905_06_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐二年（905）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷265天祐二年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=905):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0905_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '905年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '905年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0905_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0905_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 35: Campaign, flight, dialogue and court enfeoffments. The primary TXT is visibly damaged near its end.
event('yang_takes_seven_prefectures', '杨师厚攻下唐、邓等七州',35,
      '杨师厚攻下唐、邓、复、郢、随、均、房七州，硃全忠军于汉北。',
      [('杨师厚','攻下七州的将领'),('朱温','屯军汉北者')],
      when='905年八月至九月前；确日未载',place='唐、邓、复、郢、随、均、房七州',
      note='七州是逐一列明的战果；《旧五代史》系于八月，主书本句未载确日。')
event('yang_builds_bridge_crosses_han', '杨师厚作阴谷口浮梁并渡汉',35,
      '九月，辛酉，命师厚作浮梁于阴谷口，癸亥，引兵渡汉。',
      [('杨师厚','造浮梁并领兵渡汉者')],
      when='905年九月辛酉造浮梁、癸亥渡汉',place='阴谷口',
      note='造桥与渡汉为两日动作，保留原日序；《旧五代史》卷二把造梁系甲子，日分不同。')
event('yang_defeats_zhao_on_han', '杨师厚汉滨击败赵匡凝军',35,
      '甲子，赵匡凝将兵二万陈于汉滨，师厚与战，大破之，遂傅其城下。',
      [('赵匡凝','率兵迎战而败者'),('杨师厚','击败赵匡凝军者')],
      when='905年九月甲子',place='汉滨',
      note='“二万”为主书记载的赵匡凝军规模，不据此推断死伤数。')
event('zhao_kuangning_flees_guangling', '赵匡凝焚府城后沿汉奔广陵',35,
      '是夕，匡凝焚府城，帅其族及麾下士沿汉奔广陵。',
      [('赵匡凝','焚府城并奔广陵者')],
      when='905年九月甲子夜',place='广陵',
      note='“是夕”承甲子；广陵为目的地，不把沿途节点虚构。')
event('yang_enters_xiangyang', '杨师厚乙丑入襄阳',35,
      '乙丑，师厚入襄阳', [('杨师厚','入襄阳者')],
      when='905年九月乙丑',place='襄阳')
event('zhu_follows_into_xiangyang', '朱全忠继至襄阳',35,
      '丙寓，全忠继至。', [('朱温','继杨师厚至襄阳者')],
      when='905年九月；主书底本作“丙寓”，《旧唐书》作丙寅',place='襄阳',
      note='“丙寓”是底本疑讹字，未经纸本校正；《旧唐书》及《旧五代史》作丙寅，不能悄改主书原字。')
event('zhao_meets_yang_xingmi', '赵匡凝至广陵与杨行密对答',35,
      '匡凝至广陵，杨行密戏之曰：“君在镇，岁以金帛输硃全忠，今败，乃归我乎？”匡凝曰：“诸侯事天子，岁输贡赋乃其职也，岂输贼乎！今日归公，正以不从贼故耳。',
      [('赵匡凝','答杨行密者'),('杨行密','询问赵匡凝者')],
      when='赵匡凝奔广陵后；确日未载',place='广陵',
      note='主书TXT引语后发生乱码且缺句末引号，只引可辨的原字；《新五代史》另载双方对话及“行密厚遇之”，不把乱码补写进主书快照。')
event('two_imperial_brothers_enfeoffed', '唐廷封皇弟禔、祐为颍王、蔡王',35,
      '封皇弟禔为颍王，祐为蔡王。',
      [('李禔','受封颍王者'),('祐','受封蔡王者')],
      when='905年九月；《新唐书》系丙寅',
      note='主书TXT此前有乱码，封王文字仍可辨；《新唐书》卷十另载同封。蔡王李祐与905年已遇害的德王李祐同名，分开建实体。')
for row in B['people']:
    if row['key']=='person_李祐（蔡王）':
        row['aliases']=['蔡王祐','李祐（蔡王）']
        row['description']='天祐二年受封蔡王的唐皇弟；与此前遇害的德王李祐同名异人。'

# 36: Capture of Jingnan and appointment actions are distinct from Xiangyang battle.
event('zhao_kuangming_abandons_jingnan', '赵匡明率众弃荆南奔成都',36,
      '丁卯，荆南节度使赵匡明帅众二万，弃城奔成都。',
      [('赵匡明','率众弃城奔成都者')],
      when='905年九月丁卯',place='成都',
      note='“二万”是所率众数；不推为蜀方增兵或阵亡数。')
event('yang_made_xiangyang_liuhou', '朱全忠以杨师厚为山南东道留后',36,
      '戊辰，硃全忠以杨师厚为山南东道留后',
      [('朱温','授任者'),('杨师厚','受任留后者')],
      when='905年九月戊辰',place='山南东道',
      note='留后与下文“寻表”为节度使分录，不能同日化。')
event('zhu_advances_to_jiangling', '朱全忠引兵击江陵',36,
      '引兵击江陵。', [('朱温','领兵进攻者')],
      when='905年九月戊辰后；确日未载',place='江陵')
event('wang_jianwu_surrenders_jingnan', '荆南牙将王建武遣使迎降',36,
      '至乐乡，荆南牙将王建武遣使迎降。',
      [('王建武','遣使迎降者'),('朱温','受降方')],
      when='朱全忠进军乐乡后；确日未载',place='乐乡',
      note='迎降为王建武之举，不能直接等同所有荆南官兵意愿。')
event('he_gui_made_jingnan_liuhou', '朱全忠以贺瑰为荆南留后',36,
      '全忠以都将贺瑰为荆南留后。',
      [('朱温','授任者'),('贺瑰','受任荆南留后者')],
      when='905年九月；确日未载',place='荆南')
event('yang_later_xiangyang_jiedushi', '朱全忠表杨师厚为山南东道节度使',36,
      '全忠寻表师厚为山南东道节度使。',
      [('朱温','上表推荐者'),('杨师厚','被表任者')],
      when='杨师厚任留后后不久；确日未载',place='山南东道',
      note='“表”是上表，不直接等于朝廷已在同日下诏任命。')

# 37: Shu's Jinzhou campaign, surrendered commander, renaming and administrative transfer.
event('feng_xingxi_abandons_jinzhou', '冯行袭弃金州奔均州',37,
      '王宗贺等攻冯行袭，所向皆捷。丙子，行袭弃金州，奔均州。',
      [('王宗贺','进攻者'),('冯行袭','弃金州者')],
      when='905年九月丙子',place='金州',
      note='主书记王宗贺军此前进展顺利，丙子冯行袭奔均州；不推算战斗死伤。')
event('quan_shilang_surrenders_jinzhou', '全师朗以金州降王建',37,
      '其将全师朗以城降。',
      [('王宗朗','以原名全师朗降城者')],
      when='冯行袭弃金州后；确日未载',place='金州',
      note='“其将”承冯行袭；全师朗随后被王建改名王宗朗，为同一人，稳定key只建一个。')
event('wang_jian_renames_and_appoints_zonglang', '王建更全师朗名王宗朗并补金州观察使',37,
      '王建更师朗姓名曰王宗朗，补金州观察使',
      [('王建','改名并补任者'),('王宗朗','原名全师朗、受任者')],
      when='金州受降后；确日未载',place='金州',
      note='姓名变化不是父子或养子关系，未据此新建亲属边。')
event('three_prefectures_attached_jinzhou', '王建割渠、巴、开三州隶金州',37,
      '割渠、巴、开三州以隶之。',
      [('王建','调整州属者')],
      when='金州观察使补任后；确日未载',place='渠、巴、开三州',
      note='“之”承前金州观察使治属，具体边界和坐标未据此绘制。')
for row in B['people']:
    if row['key']=='person_王宗朗':
        row['aliases']=['全师朗','师朗']
        row['description']='本名全师朗，金州降王建后改名王宗朗，补金州观察使。'

# 38: A new plan for the southern suburban rite, not an executed rite.
event('southern_rite_rescheduled', '唐廷改拟十一月癸酉亲郊',38,
      '乙酉，诏更用十一月癸酉亲郊。',
      when='905年九月乙酉下诏；拟十一月癸酉行礼',place='南郊',
      note='仍是改期诏书，不写祭礼已经举行；《旧唐书》作十一月十九日。')

# 39: Wuzhou capture, appointments, Jiyang action and counterattack.
event('tao_chen_capture_wuzhou', '陶雅、陈璋拔婺州并执沈夏',39,
      '淮南将陶雅、陈璋拔婺州，执刺史沈夏以归。',
      [('陶雅','攻下婺州者'),('陈璋','攻下婺州者'),('沈夏','被俘刺史')],
      when='905年九月本段；确日未载',place='婺州',
      note='《新唐书》卷十把杨行密陷婺州、执沈夏系六月；月份异说单列，不混淆两次战斗。')
event('yang_xingmi_appoints_tao_chen', '杨行密授陶雅、陈璋江南诸州军职',39,
      '杨行密以雅为江南都招讨使，歙、婺、衢、睦观察使，以璋为衢、婺副招讨使。',
      [('杨行密','授任者'),('陶雅','受任江南都招讨使兼观察使者'),('陈璋','受任衢婺副招讨使者')],
      when='婺州攻克后；确日未载',place='歙、婺、衢、睦',
      note='逐一保留官职，不能据官衔直接推断各州实际占领范围。')
event('fang_xi_defeats_chen_and_advances', '方习于暨阳击败陈璋并进攻婺州',39,
      '璋攻暨阳，两浙将方习败之。习进攻婺州。',
      [('陈璋','攻暨阳而败者'),('方习','击败陈璋并进攻婺州者')],
      when='陶雅、陈璋拔婺州后；确日未载',place='暨阳、婺州',
      note='“进攻婺州”不写已夺回婺州。')

# 40: Liu Jin's death and succession at Haozhou, with an explicit father relation.
event('liu_jin_dies', '濠州团练使刘金去世',40,
      '濠州团练使刘金卒', [('刘金','去世的濠州团练使')],
      when='905年九月后条；确日未载',place='濠州')
event('liu_rengui_oversees_haozhou', '杨行密以刘金子刘仁规知濠州',40,
      '杨行密以金子仁规知濠州。',
      [('杨行密','任命者'),('刘仁规','刘金之子、受任知濠州者')],
      when='刘金去世后；确日未载',place='濠州',
      note='“金子仁规”承前刘金之子刘仁规；“知濠州”不是团练使世袭的明证。')
rel='relationship_zztj_265_0905_liu_jin_father_liu_rengui'
B['person_relationships'].append(dict(key=rel,person_a_key=people['刘金'],person_b_key=people['刘仁规'],
                                       relation_type='父亲',description='刘金是刘仁规的父亲。',status='draft'))
claim('person_relationship',rel,'description','刘金是刘仁规的父亲。',40,'刘金卒，杨行密以金子仁规知濠州',
      '“金子仁规”承上句刘金，明确父子方向。')

# Separate books record the same episode and expose source errors rather than silently repairing them.
extra(old_sep,'event','event_zztj_265_0905_yang_builds_bridge_crosses_han','description',
      '《旧唐书》卷二十下记辛酉伐竹木为浮梁、癸亥渡江。',
      '辛酉，楊師厚於襄州西六十里陰谷江口伐竹木為浮梁。癸亥，梁成，引軍渡江',35,'corroborates',
      '旧书补浮梁用料和位置，仍未校地图坐标。')
extra(old_sep,'event','event_zztj_265_0905_yang_defeats_zhao_on_han','time_original',
      '《旧唐书》卷二十下同系甲子汉滨之战。',
      '甲子，趙匡凝率勁兵二萬，陣于江之湄。師厚一戰敗之',35,'corroborates',
      '旧书另记当夜赵匡凝逃亡，保留主书事件顺序。')
extra(old_sep,'event','event_zztj_265_0905_zhu_follows_into_xiangyang','time_original',
      '《旧唐书》卷二十下作丙寅朱全忠继至；主书TXT作“丙寓”。',
      '丙寅，全忠繼至',35,'conflicts',
      '主书疑讹字不悄悄改写，旧书提供丙寅异文。')
extra(new_zhao,'event','event_zztj_265_0905_zhao_meets_yang_xingmi','description',
      '《新五代史》卷四十一补杨行密厚遇赵匡凝。',
      '行密厚遇之',35,'adds',
      '该句在主书TXT乱码处缺失；未将新书摘录冒充主书原字。')
extra(new_sep,'event','event_zztj_265_0905_two_imperial_brothers_enfeoffed','time_original',
      '《新唐书》卷十系封弟禔、祐于九月丙寅。',
      '丙寅，封弟禔為潁王，祐蔡王',35,'corroborates',
      '主书TXT封王句可辨但句前损坏；新书确认两人封号和日分。')
extra(old_campaign,'event','event_zztj_265_0905_zhao_kuangming_abandons_jingnan','description',
      '《旧五代史》卷二也记赵匡明弃城奔蜀。',
      '留後趙匡明棄城上峽奔蜀',36,'corroborates',
      '旧书不单独证主书二万人数或丁卯日。')
extra(old_campaign,'event','event_zztj_265_0905_he_gui_made_jingnan_liuhou','description',
      '《旧五代史》卷二记贺瑰权领荆州。',
      '帝以都將賀瑰權領荊州',36,'corroborates',
      '旧书写权领，与主书“留后”称谓并列。')
extra(old_sep,'event','event_zztj_265_0905_southern_rite_rescheduled','description',
      '《旧唐书》卷二十下记乙酉敕改用十一月十九日行郊礼。',
      '乙酉，敕先擇十月九日有事郊丘，備物之間，有所未辦，宜改用十一月十九日',38,'corroborates',
      '公历日未换算，主书用干支记拟定之日。')
extra(new_wuzhou,'event','event_zztj_265_0905_tao_chen_capture_wuzhou','time_original',
      '《新唐书》卷十记六月杨行密陷婺州并执沈夏；《通鉴》置于九月后条。',
      '楊行密陷婺州，執刺史沈夏',39,'conflicts',
      '新书没有在该句点名陶雅、陈璋，只能补机构与月份异说。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(35,41):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐二年第35—40段连续处理；第35段TXT损坏，原字及异文并列；蔡王祐与已故德王李祐分体。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=905,
    primary_source_key=primary_autumn,primary_source_keys=[primary_autumn],
    paragraphs=[Q[n]['id'] for n in range(35,41)],next_paragraph=Q[41]['id'],
    coverage='卷265天祐二年第35—40段连续处理；汉滨襄阳之战、荆南金州、郊礼改期、婺州战事与濠州继任。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
