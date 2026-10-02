"""Curate Tongjian 266, year 907, consecutive paragraphs 31–44."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 62))
primary = 'tongjian-266-907-may'
summer = 'tongjian-266-907-summer'
old_princes = 'jiuwudaishi-003-princes'
new_su = 'xinwudaishi-035-suxun'
new_chu = 'xinwudaishi-066-chu-liucun'
B = {'format_version': 1, 'batch_key': 'zztj-v266-y0907-p031-p044',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-04/sources/library' / primary, '8077dd4f', '司马光等'),
    (summer, P / 'sources/library' / summer, 'ef31b763', '司马光等'),
    (old_princes, P / 'sources/library' / old_princes, 'ef31b763', '薛居正等'),
    (new_su, P / 'sources/library' / new_su, 'ef31b763', '欧阳修等'),
    (new_chu, P / 'sources/library' / new_chu, 'ef31b763', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, summer)}
for n in range(31, 45):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/266.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '梁王':'朱温', '晋王':'李克用', '吴王镠':'钱镠', '朱友貞':'朱友贞', '劉存':'刘存', '秦彥暉':'秦彦晖'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/year-0907/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_266_0907_05_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷266·开平元年（907）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷266开平元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=907, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_266_0907_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        if key not in {row['key'] for row in B['events']}:
            row = dict(legacy_events[reuse_key], status='draft')
            B['events'].append(row)
        reused.add(key)
        desc = title + '。'
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '907年本段条；确日未载', dynasty='唐', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '907年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_266_0907_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def relation(key, n, quote, note):
    assert quote in Q[n]['text']
    row = legacy_relations[key]
    if key not in {item['key'] for item in B['person_relationships']}:
        B['person_relationships'].append(dict(row, status='draft'))
        reused.add(key)
    claim('person_relationship',key,'description',row['description'],n,quote,note)

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_266_0907_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 31: Honors to imperial kin; Zhu Youwen remains an adopted son from p21.
event('zhu_princes','后梁封朱全昱及诸子为王',31,
      '乙酉，立皇兄全昱为广王，子友文为博王，友珪为郢王，友璋为福王，友贞为均王，友雍为贺王，友徽为建王。',
      when='907年五月乙酉',note='“子友文”按前文养子身份解读；诸王封号逐一依本段。',reuse_key='event_0907_zhu_princes')
for name in ('朱温','朱全昱','朱友文','朱友珪','朱友璋','朱友贞','朱友雍','朱友徽'):
    person(name,31,'后梁宗室封王名单中的人物',Q[31]['text'])
for key in ('relationship_person_朱全昱_person_zhu_wen_兄长',
            'relationship_person_zhu_wen_person_朱友文_养父',
            'relationship_person_zhu_wen_person_朱友璋_父亲',
            'relationship_person_zhu_wen_person_朱友雍_父亲',
            'relationship_person_zhu_wen_person_朱友徽_父亲'):
    relation(key,31,Q[31]['text'],'依据“皇兄”“子”及第21段友文养子身份，复用已有方向和类型。')
extra(old_princes,'event','event_0907_zhu_princes','description',
      '《旧五代史》卷三也记五月乙酉封朱全昱、友文、友珪、友璋、友雍、友徽为王；本段未列友贞。',
      '乙酉，立皇兄全昱為廣王，皇子友文為博王，友珪為郢王，友璋為福王，友雍為賀王，友徽為建王。',31,'conflicts',
      '与《通鉴》相比少友贞一名；只记录两书名单差异，不判断是脱漏还是异时授封。')

# 32-34: Court organization and the start of the Luzhou campaign.
event('jianchang_palace','后梁改东都旧第为建昌宫',32,
      '辛卯，以东都旧第为建昌宫，改判建昌院事为建昌宫使。',
      when='907年五月辛卯',place='东都旧第',
      note='旧第改宫及院事改使为同日制度动作，不推定建昌院始设于当年。')
extra(old_princes,'event','event_zztj_266_0907_jianchang_palace','description',
      '《旧五代史》卷三也记建昌院改建昌宫，并补述其早期掌四镇兵马仓库籍。',
      '辛卯，以東都舊第為建昌宮，改判建昌院事為建昌宮使。初，帝創業之時，以四鎮兵馬倉庫籍繁，因總置建昌院以領之',32,'adds',
      '“初”是旧书追叙，不据此将建昌院初设定于907年。')
event('luzhou_order','康怀贞奉命会魏博兵攻潞州',33,
      '壬辰，命保平节度使康怀贞将兵八万会魏博兵攻潞州。',
      when='907年五月壬辰',place='潞州',
      note='八万是主书所记出兵数，未作现代可核统计；围城过程接第39段。',reuse_key='event_0907_luzhou_siege')
event('chongzheng_takes_military_council','后梁废枢密院并将其职事归崇政院',34,
      '甲午，诏废枢密院，其职事皆入于崇政院，以知院事敬翔为院使。',
      [('敬翔','由知崇政院事改任院使')],when='907年五月甲午',
      note='第19段敬翔知崇政院事；本段才记废枢密院并转职事。')

# 35-36: Forced retirement and Chuzhou submission.
event('su_retired','苏循、张祎等被勒致仕，苏楷归田',35,
      '戊戍，诏循及刑部尚书张祎等十五人并勒致仕，楷斥归田里。',
      when='907年五月戊戍（原文；干支字形待核）',
      note='“戊戍”保留电子底本写法，疑应校为“戊戌”；不静默改字。',reuse_key='event_0907_su_retired')
claim('event','event_0907_su_retired','description','苏循父子此后到河中依附朱友谦。',35,
      '循父子乃之河中依硃友谦。','“硃”为底本字形，规范实体朱友谦；没有确载到达日期。')
extra(new_su,'event','event_0907_su_retired','description',
      '《新五代史》卷三十五记敬翔反对任用苏循父子，两人归田后依朱友谦。',
      '敬翔尤惡之，謂太祖曰：「梁室新造，宜得端士以厚風俗，循父子皆無行，不可立於新朝。」於是父子皆勒歸田里，乃依朱友謙於河中。',35,'corroborates',
      '新史前段记朱温即位宴会；后段跨更晚年份，本次只据直接相关语句补证。')
event('chuzhou_surrender','卢约以处州降吴越',36,
      '卢约以处州降吴越。',when='907年五月戊戍后、六月前；确日未载',place='处州',
      note='一段一句，不扩写卢约此前身份或吴越后续统治。',reuse_key='event_0907_chuzhou_surrender')

# 37: Separate campaign, battlefield deaths, and the later execution by Yang Wo's officers.
event('chu_huainan_campaign','秦彦晖、黄璠击败刘存等淮南水军并取岳州',37,
      '存等走，黄璠自浏阳引兵绝江，与彦晖合击，大破之，执存及知新，裨将死者百馀人，士卒死者以万数，获战舰八百艘。威以馀众遁归，彦晖遂拔岳州。',
      when='907年六月',place='越堤、浏阳口、岳州',
      note='“死者以万数”等为主书战损叙述，非现代精确统计；刘存、陈知新被俘后另见本段。',
      reuse_key='event_0907_chu_huainan')
claim('event','event_0907_chu_huainan','description','刘存、陈知新被俘后拒绝事楚，马殷命处死二人。',37,
      '殷释存、知新之缚，慰谕之。二人皆骂曰：“丈夫以死报主，肯事贼乎！”遂斩之。',
      '《新五代史》卷六十六作战死，死因异文并列，不把两种经过合并。')
claim('event','event_0907_chu_huainan','description','杨渥任刘存为西南面都招讨使，令水军攻楚。',37,
      '弘农王以鄂岳观察使刘存为西南面都招讨使',
      '“弘农王”为杨渥；出兵任命与战败过程为本段同一战役链。')
event('xu_xuanying_executed','张颢、徐温在败战后处死许玄应',37,
      '许玄应，弘农王之腹心也，常预政事，张颢、徐温因其败，收斩之。',
      when='907年六月败战后；确日未载',
      note='许玄应在淮南内部被处死，不同于刘存、陈知新的战场及楚方处置。',
      reuse_key='event_0907_xu_executed')
extra(new_chu,'event','event_0907_chu_huainan','description',
      '《新五代史》卷六十六亦记秦彦晖、黄璠合击刘存并取岳州。',
      '存等退走，黃璠以瀏陽舟截江合擊，大敗之，劉存及陳知新戰死，彥暉取岳州。',37,'corroborates',
      '同段也有死亡经过差异，另立冲突引用；不把两书叙事完全视作相同。')
extra(new_chu,'event','event_0907_chu_huainan','description',
      '《新五代史》记刘存、陈知新战死；《通鉴》记二人被俘后遭斩。',
      '劉存及陳知新戰死',37,'conflicts',
      '死因异文保留；新史将此战接在鄂州战事之后，叙事时间亦待校。')

# 38-40: Hongzhou, the prolonged Luzhou siege, and relief for Zezhou.
event('hongzhou_attack','楚军会彭玕攻洪州未克',38,
      '楚王殷遣兵会吉州刺史彭玕攻洪州，不克。',
      when='907年六月后条；确日未载',place='洪州',
      note='主书只记会攻未克，不推成洪州易手。',reuse_key='event_0907_hongzhou')
event('luzhou_siege','康怀贞围攻潞州，晋军救援',39,
      '康怀贞至潞州，晋昭义节度使李嗣昭、副使李嗣弼闭城拒守。怀贞昼夜攻之，半月不克，乃筑垒穿蚰蜓堑而守之，内外断绝。',
      when='907年壬辰发兵后；围城历半月以上',place='潞州',
      note='五月发兵见第33段；“半月不克”后改为筑垒围困，不把救援写成当时已解围。',
      reuse_key='event_0907_luzhou_siege')
claim('event','event_0907_luzhou_siege','description','晋王任周德威为行营都指挥使，率多部赴援潞州。',39,
      '晋王以蕃、汉都指挥使周德威为行营都指挥使，帅马军都指挥使李嗣本、马步都虞候李存璋、先锋指挥使史建瑭、铁林都指挥使安元信、横冲指挥使李嗣源、骑将安金全救潞州。',
      '原文列出救援诸将；救援不等于此时已经解围。')
claim('event','event_0907_luzhou_siege','description','李嗣弼为李克修之子，李嗣本本姓张，史建瑭为史敬思之子。',39,
      '嗣弼，克修之子；嗣本，本姓张；建瑭，敬思之子；金全，代北人也。',
      '亲属与本姓为段末说明，尚未单独创建可能混淆的关系；后续可按稳定身份增补。')
event('zezhou_relief','后梁遣范居实救援遭晋军进攻的泽州',40,
      '晋兵攻泽州，帝遣左神勇军使范居实将兵救之。',
      when='907年潞州围城后条；确日未载',place='泽州',
      note='本句只记晋军进攻与梁军出援，不记交战结果。',reuse_key='event_0907_zezhou')

# 41-44: Autumn appointments, Jiangling defense, and Jinghai succession.
event('hanjian_promotion','后梁加韩建守司徒、同平章事',41,
      '甲寅，以平卢节度使韩建守司徒、同平章事。',
      when='907年七月前甲寅；确月待核',
      note='本段出现在“秋，七月”之前，不能直接归入七月。',reuse_key='event_0907_hanjian')
event('jiangling_defense','高季昌断粮击退雷彦恭及楚军',42,
      '武贞节度使雷彦恭会楚兵攻江陵，荆南节度使高季昌引兵屯公安，绝其粮道；彦恭败，楚兵亦走。',
      when='907年七月前条；确日未载',place='江陵、公安',
      note='只据本段记断粮、败走；不推定联盟持续或精确边界。',reuse_key='event_0907_jiangling')
event('liushouguang_lulong','后梁授刘守光卢龙节度使、同平章事',43,
      '秋，七月，甲午，以守光为卢龙节度使、同平章事。',
      when='907年七月甲午',place='卢龙',
      note='前句囚父、自称留后为先事；本段明确日期对应后梁授官。',
      reuse_key='event_0907_liushouguang_confirmed')
claim('event','event_0907_liushouguang_confirmed','description','刘守光囚禁父亲后自称卢龙留后，并向后梁请命。',43,
      '刘守光既囚其父，自称卢龙留后，遣使请命。',
      '“既”表示先于七月甲午授官；不在此段重定囚父之日。')
event('quhao_jinghai','曲裕死后，曲颢受任静海节度使',44,
      '静海节度使曲裕卒，丙申，以其子权知留后颢为节度使。',
      when='907年七月丙申授任；曲裕卒日未载',place='静海',
      note='底本作曲裕、颢；姓名与其他史籍异名尚待逐一校核，先复用已发布主体。',reuse_key='event_0907_quhao')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(31,45):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷266开平元年第31—44段连续处理；《旧五代史》宗室名单及《新五代史》刘存死因异文并列，追叙与确日分开。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=266,year=907,
    primary_source_key=primary,primary_source_keys=[primary,summer],
    paragraphs=[Q[n]['id'] for n in range(31,45)],next_paragraph=Q[45]['id'],
    coverage='卷266开平元年第31—44段连续处理；宗室封王、建昌宫、潞州围城、楚淮南水战及秋季任命。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
