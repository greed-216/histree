"""Curate consecutive Tongjian vol. 269, 915 paragraphs 29–33."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 34))
main = 'tongjian-269-915-winter'
new_03 = 'xinwudaishi-003-915-winter'
old_73 = 'jiuwudaishi-073-wen-tao'
new_63 = 'xinwudaishi-063-shu-fire'
old_09 = 'jiuwudaishi-009-liu-yan-title'
new_65 = 'xinwudaishi-065-liu-yan-title'
specs = [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-08/sources/library' / main, 'b1919250', '司马光等'),
    (new_03, P / 'sources/library' / new_03, '2f3733ce', '欧阳修'),
    (old_73, P / 'sources/library' / old_73, '2f3733ce', '薛居正等'),
    (new_63, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-08/sources/library' / new_63, 'b1919250', '欧阳修'),
    (old_09, P / 'sources/library' / old_09, '2f3733ce', '薛居正等'),
    (new_65, P / 'sources/library' / new_65, '2f3733ce', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p029-p033',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_dirs = {key: path for key, path, _, _ in specs}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
for n in range(29, 34):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in (source_dirs[main] / 'source.txt').read_text(), n
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=main, relation='adds'):
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明元年（915）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0915_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'王宗鐸': '王宗铎', '李彦韬': '温韬', '温昭图': '温韬', '宗绾': '王宗绾'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
    if name == '王宗俦':
        row['aliases'] = ['王宗儔']
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '姓名按既有主体规范；原文和摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=915):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0915_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '915年本段条；确日未载', dynasty='五代十国',
               description=title + '。', phases=[], location_name=place,
               location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown',
               location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',
               status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote,
          note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', row['time_original'], n, quote,
          '段内追叙，确年待考。' if year is None else '按主书段落次序；未把干支换算成公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0915_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key




# p029: the source gives the act of changing era without spelling out the new name here.
event('liang_changes_era', '后梁于十一月乙丑改元', 29,
      '乙丑，改元',
      [('朱友贞','在位时后梁改元的皇帝')],
      when='915年十一月乙丑；本句未列新年号', place='后梁朝廷',
      note='底本与另一《通鉴》电子文本在此均只作“改元”，并非本地截断；本年卷题为贞明元年，不能冒称该句逐字写出“贞明”。')
claim('event','event_zztj_269_0915_liang_changes_era','description',
      '《新五代史》卷三也记十一月乙丑改元。',29,
      '十一月乙丑，改元。',
      '新书本纪在“贞明元年”年题下记此事，也未在本句重写新年号。',new_03,'corroborates')
# p030: Shu armies advance along several routes; preserve changes of fortune and identities.
event('shu_guozhen_defeat', '王宗翰克固镇后在泥阳川战败，退保鹿台山', 30,
      '己巳，蜀王宗翰引兵出青泥岭，克固镇，与秦州将郭守谦战于泥阳川。蜀兵败，退保鹿台山。',
      [('王宗翰','率蜀军克固镇、在泥阳川失利后退保鹿台山的将领'),('郭守谦','在泥阳川抵御蜀军的秦州将')],
      when='915年十一月己巳；未换算公历日', place='青泥岭、固镇、泥阳川、鹿台山',
      note='克固镇与泥阳川战败是同次行军的不同结果，不能只记胜或只记败。')
event('shu_jinsha_valley_victory', '王宗绾在金沙谷击败秦州兵，擒李彦巢', 30,
      '辛未，王宗绾等败秦州兵于金沙谷，擒其将李彦巢等，乘胜趣秦州。',
      [('王宗绾','在金沙谷获胜后趋秦州的蜀将'),('李彦巢','在金沙谷被俘的秦州将')],
      when='915年十一月辛未；未换算公历日', place='金沙谷、秦州',
      note='“等”表示另有未具名参战者，未据此补人名或确数。')
event('shu_takes_jiezhou', '王宗铎克阶州，刺史李彦安投降', 30,
      '兴州刺史王宗鐸克阶州，降其刺史李彦安。',
      [('王宗铎','原文作王宗鐸，率蜀军克阶州的兴州刺史'),('李彦安','向蜀军投降的阶州刺史')],
      when='915年蜀军攻秦州期间；确日未载', place='阶州',
      note='王宗鐸是既有人物王宗铎的繁体写法；不因字形另建UUID。')
claim('person',people['王宗铎'],'aliases','《资治通鉴》原文将王宗铎写作王宗鐸。',30,
      '兴州刺史王宗鐸克阶州',
      '繁简字形待补入已发布人物别名；主体继续复用王宗铎UUID。')
event('shu_takes_chengzhou', '王宗绾攻克成州并擒刺史李彦德', 30,
      '甲戌，王宗绾克成州，擒其刺史李彦德。',
      [('王宗绾','攻克成州的蜀将'),('李彦德','在成州被擒的原刺史')],
      when='915年十一月甲戌；未换算公历日', place='成州',
      note='主书明确“擒”，不改写为主动投降。')
event('qinzhou_yields_to_shu', '李继崇遣子李彦秀奉牌印降蜀，王宗俦获推为秦州留后', 30,
      '蜀军至上染坊，秦州节度使李继崇遣其子彦秀奉牌印迎降。宗绛入秦州，表排陈使王宗俦为留后。',
      [('李继崇','遣子奉牌印迎降的秦州节度使'),('李彦秀','奉父命携牌印迎降的李继崇之子'),('王宗俦','被表为秦州留后的蜀方排陈使')],
      when='915年蜀军进至上染坊后；确日未载', place='上染坊、秦州',
      note='底本“宗绛入秦州”疑为人名讹字，不能确定是王宗绾或另人，故不建该句行动主体；“王宗俦”身份明确。')
for a,b,relation,description,quote in [
    (people['李继崇'],people['李彦秀'],'父亲','李继崇是李彦秀的父亲。','李继崇遣其子彦秀奉牌印迎降')]:
    rk=f'relationship_{a}_{b}_{relation}'
    B['person_relationships'].append(dict(key=rk,person_a_key=a,person_b_key=b,relation_type=relation,description=description,status='draft'))
    claim('person_relationship',rk,'description',description,30,quote,
          '“其子”直接说明亲属方向；不由姓名字辈推断。')
claim('person',people['王宗俦'],'aliases','王宗俦在《新五代史》原文作王宗儔。',30,
      '遣王宗儔等攻岐',
      '新书概记同年蜀攻岐，繁体字形用于同一新人物的检索别名，不据此推断其在秦州的具体官衔。',new_63,'corroborates')
event('liu_zhijun_defects_to_shu', '刘知俊从围邠州军中出走，投向蜀军', 30,
      '刘知俊攻霍彦威于邠州，半岁不克，闻秦州降蜀，知俊妻子皆迁成都。知俊解围还凤翔，终惧及祸，夜帅亲兵七十人，斩关而出，庚辰，奔于蜀军。',
      [('刘知俊','久围邠州未克，后率亲兵离凤翔投蜀的岐将'),('霍彦威','邠州守方，遭刘知俊久围')],
      when='915年十一月庚辰投蜀；邠州围攻已延续约半年', place='邠州、凤翔、蜀军',
      note='邠州围攻已在前段记开始，此处重点为解除围攻与投蜀；“妻子皆迁成都”是闻秦州降蜀后的已然状态，不预设主动随行。')
claim('event','event_zztj_269_0915_liu_zhijun_defects_to_shu','description',
      '《新五代史》卷六十三概记刘知俊因家属在蜀而自岐来投。',30,
      '梁叛將劉知俊在岐，於是特以其族來。',
      '新书未详凤翔出走的夜次和七十亲兵；这些细节只据主书。',new_63,'corroborates')
event('shu_takes_fengzhou', '王宗绾会王宗瑶攻下凤州', 30,
      '王宗绾自河池、两当进兵，会王宗瑶攻凤州，癸未，克之。',
      [('王宗绾','自河池、两当进兵并会攻凤州的蜀将'),('王宗瑶','会合王宗绾攻凤州的蜀将')],
      when='915年十一月癸未；未换算公历日', place='河池、两当、凤州',
      note='主书本段称癸未克凤州；与前段任命攻凤州先后衔接。')
claim('event','event_zztj_269_0915_shu_takes_fengzhou','description',
      '《新五代史》卷六十三概记蜀军取秦、凤、阶、成四州。',30,
      '遣王宗儔等攻岐，取其秦、鳳、階、成四州',
      '新书为合并概述，并未给各州日次和主书所列全部将领。',new_63,'corroborates')
# p031: Wen Tao changes allegiance and receives a new name; a published duplicate needs later merge.
event('wen_tao_defects_to_liang', '温韬以李彦韬名率耀、鼎二州归梁', 31,
      '岐义胜节度使、同平章事李彦韬知岐王衰弱，十二月，举耀、鼎二州来降。彦韬即温韬也。',
      [('温韬','主书称李彦韬，率耀、鼎二州归梁的岐将')],
      when='915年十二月；确日未载', place='耀州、鼎州',
      note='主书明说“彦韬即温韬”；本批复用温韬UUID，既有李彦韬重复人物另作合并审计，不在本批再建第三人。')
claim('person',people['温韬'],'aliases','温韬在归梁前用名李彦韬。',31,
      '彦韬即温韬也。',
      '原文直陈同一人；需合并历史重复人物UUID并保留旧声明，发布后执行有界修订。')
claim('event','event_zztj_269_0915_wen_tao_defects_to_liang','description',
      '《旧五代史》卷七十三温韬传也记其事李茂贞时名彦韬，归梁后更名昭图。',31,
      '事李茂貞，名彥韜，後降於梁，更名昭圖。',
      '旧书追述姓名阶段，不把传记后段盗陵或被诛提前录到915年。',old_73,'corroborates')
event('liang_renames_wen_tao_and_prefectures', '后梁改耀、鼎州及义胜军名，复温韬姓并改名昭图', 31,
      '乙未，诏改耀州为崇州，鼎州为裕州，义胜军为静胜军，复彦韬姓温氏，名昭图，官任如故。',
      [('朱友贞','下诏改州军名并赐温韬新名的后梁皇帝'),('温韬','恢复温姓、改名昭图且官任如故的降梁将领')],
      when='915年十二月乙未；未换算公历日', place='耀州／崇州、鼎州／裕州、义胜军／静胜军',
      note='地名是同一时期的改称，不在地图上误标为新增三处地理实体；“昭图”为改名，非另人。')
claim('person',people['温韬'],'aliases','温韬归梁后改名温昭图。',31,
      '复彦韬姓温氏，名昭图',
      '与李彦韬同一主体；既有重复人物待有界合并。')
claim('event','event_zztj_269_0915_liang_renames_wen_tao_and_prefectures','description',
      '《新五代史》卷三称耀州温昭图叛岐归梁。',31,
      '耀州溫昭圖叛于岐，來附。',
      '新书以归梁后名回称，不能据此断归梁前已名昭图。',new_03,'corroborates')
# p032: Shu's December pardon, next year's announced era, and Wuxing Circuit.
event('shu_amnesty_and_next_era', '蜀十二月丁未大赦，宣布次年改元通正', 32,
      '丁未，蜀大赦；改明年元曰通正。',
      [('王建','在位时蜀颁大赦并宣布次年改元通正的蜀主')],
      when='915年十二月丁未宣布；通正作为下一年年号', place='蜀',
      note='此处只是宣布明年改元，不能把916年的通正纪年提前算作915年。')
event('shu_establishes_wuxing_circuit', '蜀置武兴军于凤州，王宗鲁获任节度使', 32,
      '置武兴军于凤州，割文、兴二州隶之，以前利州团练使王宗鲁为节度使。',
      [('王建','在位时蜀设武兴军并任命节度使的蜀主'),('王宗鲁','从前利州团练使获任武兴军节度使的蜀将')],
      when='915年十二月丁未条；确日依本段记述', place='凤州、文州、兴州',
      note='文、兴二州隶武兴军为行政安排；不推定边界坐标。')
# p033: Liu Yan's request, refusal, and cessation of tribute.
event('liu_yan_requests_nanyue_title', '刘岩请封南越王并加都统，后梁未允', 33,
      '是岁，清海、建武节度使兼中书令刘岩，以吴越王镠为国王而己独为南平王，表求封南越王及加都统，帝不许。',
      [('刘岩','以钱镠封号为对照向后梁请南越王及都统的岭南节度使'),('朱友贞','未准刘岩请封的后梁皇帝')],
      when='915年是岁；确月日未载', place='岭南、后梁朝廷',
      note='主书称刘岩现为南平王；旧五代史后年仍作南平王，新五代史称南海王，封号异文并列。钱镠仅为请求中的对照，不推定参与上表。')
claim('event','event_zztj_269_0915_liu_yan_requests_nanyue_title','description',
      '《旧五代史》卷九后年仍称广州节度使刘岩为南平王。',33,
      '廣州節度使、南平王劉岩',
      '旧书是917年削爵条，不能单独证明915年封号，但可证书中南平王称谓；不据后年削爵预记915年。',old_09,'adds')
claim('event','event_zztj_269_0915_liu_yan_requests_nanyue_title','description',
      '《新五代史》卷六十五称末帝即位后刘龑承兄爵，封南海王，与主书南平王异。',33,
      '末帝即位，悉以隱官爵授龑，龑封南海王。',
      '新书“龑”为刘岩后名；南海王／南平王封号差异保留，待纸本及册命核。',new_65,'conflicts')
claim('person',people['刘岩'],'aliases','刘岩在《新五代史》中以刘龑之名记载。',33,
      '末帝即位，悉以隱官爵授龑',
      '新书用后名龑回称此人，不能反推915年已改名；既有刘岩UUID待补刘龑别名。',new_65,'adds')
event('liu_yan_ends_liang_tribute', '刘岩向僚属表示不再远事后梁，此后贡使中断', 33,
      '岩谓僚属曰：“今中国纷纷，孰为天子！安能梯航万里，远事伪庭乎！”自是贡使遂绝。',
      [('刘岩','表示不再向后梁进贡的岭南节度使')],
      when='915年请封未获准后；确月日未载', place='岭南',
      note='“自是贡使遂绝”为主书后续概述，不把之后每一年都重复录作915年事件。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(29, 34):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第29—33段连续处理；改元短句保原文，蜀军多线战事分录，宗绛疑字不强合并；李彦韬已按同人证据并入温韬并匿名读回。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(29, 34)], next_paragraph=None,
    coverage='卷269贞明元年十一月至年末第29—33段；梁改元、蜀取秦凤、温韬归梁、刘岩断贡。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[29]['id'],'note':'“乙丑，改元”底本短句与另本一致；新五代史本纪亦无年号字样，年题贞明元年，不能把该句误称缺文。'},
      {'paragraph_id':Q[30]['id'],'note':'“宗绛入秦州”人名疑字未定，不创设王宗绛或擅改为王宗绾；王宗鐸按既有王宗铎繁简同人。'},
      {'paragraph_id':Q[31]['id'],'note':'主书明“彦韬即温韬”，旧批次重复人物的一条参与和一条声明已迁至温韬，重复人物已隐藏；见content/revisions/2026-10-02-wen-tao-li-yantao/publication.json。'},
      {'paragraph_id':Q[32]['id'],'note':'通正为下一年所用，915年只有宣布改元，不提前改纪年。'},
      {'paragraph_id':Q[33]['id'],'note':'刘岩封号通鉴／旧五代史作南平王，新五代史作南海王；后名刘龑与既有刘岩同人，封号与改名年份待纸本核。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
