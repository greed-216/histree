"""Curate Tongjian 265, year 904, consecutive paragraphs 11–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 22))
primary = 'tongjian-265-904-late'
new_yang = 'xinwudaishi-061-yangwo-warning'
new_dowager = 'xintangshu-010-dowager'
old_october = 'jiutangshu-020-october'
old_campaign = 'jiuwudaishi-002-campaign'
old_youyu = 'jiuwudaishi-013-youyu-death'
B = {'format_version': 1, 'batch_key': 'zztj-v265-y0904-p011-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent / 'part-02/sources/library' / primary, '40fd2522', '司马光等'),
    (new_yang, P / 'sources/library' / new_yang, '8732e6a2', '欧阳修等'),
    (new_dowager, P / 'sources/library' / new_dowager, '8732e6a2', '欧阳修等'),
    (old_october, P / 'sources/library' / old_october, '8732e6a2', '刘昫等'),
    (old_campaign, P / 'sources/library' / old_campaign, '8732e6a2', '薛居正等'),
    (old_youyu, P / 'sources/library' / old_youyu, '8732e6a2', '薛居正等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary,)}
for n in range(11, 17):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/265.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温', '全忠':'朱温', '硃友恭':'朱友恭', '李彦威':'朱友恭', '渥':'杨渥', '硃友裕':'朱友裕'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_265_0904_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷265·天祐元年（904）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷265天祐元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=904):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_265_0904_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '904年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '904年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_265_0904_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_265_0904_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 11: Huainan command succession and Yang Wo's departure.
event('li_shenfu_falls_ill','李神福攻鄂州未下，病后返回广陵',11,
      '淮南将李神福攻鄂州未下，会疾病，还广陵',
      [('李神福','攻鄂州、患病返广陵者')],when='904年八月后条；确日未载',place='鄂州、广陵',
      note='鄂州尚未攻下；此句只记病返，不提前写成死亡。')
event('liu_cun_replaces_li','杨行密任舒州团练使刘存代李神福为招讨使',11,
      '杨行密以舒州团练使泌阳刘存代为招讨使。',
      [('杨行密','任命者'),('刘存','继任招讨使者'),('李神福','被替代者')],
      when='904年八月后条；确日未载',
      note='“代”承李神福，刘存的泌阳籍贯及舒州团练使是原文所载任前身份。')
event('li_shenfu_dies','李神福病返广陵后不久去世',11,
      '神福寻卒。',[('李神福','去世者')],when='病返广陵后不久；确日未载',
      note='“寻”只表相继不久，未给出日期与去世地点；不另推死亡直接病因。')
event('tai_meng_dies','宣州观察使台濛去世',11,
      '宣州观察使台濛卒',[('台濛','去世者')],when='904年八月后条；确日未载',
      note='未载病因与确日。')
event('yang_wo_xuanzhou','杨行密以子杨渥为宣州观察使',11,
      '杨行密以其子牙内诸军使渥为宣州观察使',
      [('杨行密','任命父亲'),('杨渥','由牙内诸军使改任宣州观察使者')],
      when='904年八月后条；确日未载',place='宣州',
      note='“其子”承杨行密；父子关系已用全站稳定 key 登记，本批不新建重复边。')
event('xu_wen_warns_yang_wo','徐温警告杨渥辨别召回使者，杨渥泣谢而行',11,
      '右牙都指挥使徐温谓渥曰：“王寝疾而嫡嗣出籓，此必奸臣之谋。他日相召，非温使者及王令书，慎无亟来！”渥泣谢而行。',
      [('徐温','警告者'),('杨渥','受警告并赴宣州者'),('杨行密','被谈及患病者')],
      when='杨渥赴宣州前；确日未载',place='广陵、宣州',
      note='“必有奸臣之谋”为徐温的判断，不据此确认实有奸臣；王寝疾由其言语记载。')

# 12: title change with a date discrepancy in New Tang History.
event('empress_he_dowager','唐廷九月尊何皇后为皇太后',12,
      '九月，己巳，尊皇后为皇太后。',
      [('何氏（唐昭宗皇后）','受尊为皇太后者')],
      when='904年九月己巳',
      note='《新唐书》卷十作九月庚午，干支异说单列。')

# 13: Zhu's western campaign, withdrawal, and recorded eclipse.
event('zhu_troops_yongshou','朱全忠北屯永寿、南至骆谷，凤翔邠宁兵未出',13,
      '硃全忠引兵北屯永寿，南至骆谷，凤翔、邠宁兵竟不出。',
      [('朱温','领军驻屯者')],when='904年九月辛未前；确日未载',place='永寿、骆谷',
      note='凤翔、邠宁军未出战是本段结果，不虚构交战。')
event('zhu_returns_east','朱全忠九月辛未东还',13,
      '辛未，东还。',[('朱温','东还者')],when='904年九月辛未',
      note='“东还”承朱全忠，不指定原文未载的当日终点。')
event('tenth_month_eclipse','唐天祐元年十月辛卯朔日食',13,
      '冬，十月，辛卯朔，日有食之。',when='904年十月辛卯朔',
      note='仅录史书所载日食；不推定食分与可见区域。')

# 14: reaction after Zhaozong's murder, blame and executions.
event('zhu_feigns_shock','朱全忠闻昭宗被弑后作惊哭并责朱友恭等',14,
      '硃全忠闻硃友恭等弑昭宗，阳惊，号哭自投于地，曰：“奴辈负我，令我受恶名于万代！”',
      [('朱温','表演惊哭与责备者'),('朱友恭','被责备者')],
      when='闻昭宗遇害后；确日未载',
      note='主书用“阳惊”，为伪装判断；不能据其自辩抹去第7—8段谋划与行凶记载。')
event('zhu_mourns_luoyang','朱全忠癸巳至东都临昭宗梓宫并见新帝',14,
      '癸巳，至东都，伏梓宫恸哭流悌，又见帝，自陈非己志，请讨贼。',
      [('朱温','至东都临梓宫并自辩者'),('李祚','受见的新帝')],
      when='904年十月癸巳',place='东都洛阳',
      note='“非己志”为朱全忠自陈，不当作已证实无责。')
event('zhu_accuses_guard_commanders','朱全忠甲午奏朱友恭与氏叔琮不戢兵并扰市',14,
      '甲午，全忠奏硃友恭、氏叔琮不戢士卒，侵扰市肆',
      [('朱温','上奏指控者'),('朱友恭','被指控者'),('氏叔琮','被指控者')],
      when='904年十月甲午',place='洛阳',
      note='“不戢士卒”属朱全忠上奏，不能据此取代其二人参与前段弑君的史书记录。')
event('zhu_yougong_shi_executed','朱友恭复名李彦威与氏叔琮贬官后被赐自尽',14,
      '友恭贬崖州司户，复姓名李彦威，叔琮贬白州司户，寻皆赐自尽。',
      [('朱友恭','复姓名李彦威、贬官并被杀者'),('氏叔琮','贬官并被杀者')],
      when='904年十月甲午后不久；确日未载',
      note='“寻”不换算具体天数；朱友恭与李彦威为同一人。')

# 15: court visits and later appointments; garbled day is not normalized.
event('zhang_quanyi_court','天平节度使张全义丙申来朝',15,
      '丙申，天平节度使，张全义来朝。',
      [('张全义','来朝者')],when='904年十月丙申',
      note='原TXT“节度使，张全义”标点可疑，复用张全义既有主体，不据标点另立人。')
event('zhu_four_commands_revised','唐廷丁酉复以朱全忠为宣武护国宣义天平四镇节度使',15,
      '丁酉，复以全忠为宣武、护国、宣义、天平节度使',
      [('朱温','受任四镇节度使者')],when='904年十月丁酉',
      note='四镇名单与卷264闰四月的任命不全相同，忠武改为天平；“复”仍按此次任命录。')
event('zhang_quanyi_henan','唐廷以张全义兼河南尹、忠武节度使并判六军诸卫事',15,
      '以全义为河南尹兼忠武节度使、判六军诸卫事。',
      [('张全义','受新任者')],when='904年十月丁酉',place='河南',
      note='《旧唐书》卷二十下亦记张全义本官兼河南尹与忠武节度使，但系于丙申制，日期并列。')
event('zhu_leaves_for_garrison','朱全忠乙巳辞赴镇',15,
      '乙巳，全忠辞赴镇',
      [('朱温','辞赴镇者')],when='904年十月乙巳',
      note='原TXT下一小句“良戌，至大梁”疑有讹字，未将良戌当干支或据此标注到达日。')

# 16: Zhu Youyu's death.
event('zhu_youyu_dies','镇国节度使朱友裕在梨园去世',16,
      '镇国节度使硃友裕薨于梨园。',
      [('朱友裕','去世者')],when='904年十月后条；确日未载',place='梨园',
      note='原文未给确日；《旧五代史》说卒于行，未指明梨园，不能以彼书独证地点。')

extra(new_yang,'event','event_zztj_265_0904_xu_wen_warns_yang_wo','description',
      '《新五代史》卷六十一亦记徐温告杨渥辨召回使者。',
      '非溫使者慎無應命',11,'corroborates',
      '新书的警告措辞较简，印证谈话，不证明“奸臣”确有其人。')
extra(new_yang,'person',people['杨渥'],'description',
      '《新五代史》称杨渥为杨行密长子，并记行密病而出渥为宣州观察使。',
      '渥字承天，行密長子也。行密病，出渥為宣州觀察使。',11,'adds',
      '“长子”是新书新增身份；主书仅称“其子”，不以长子信息改写原文。')
extra(new_dowager,'event','event_zztj_265_0904_empress_he_dowager','time_original',
      '《新唐书》卷十记九月庚午尊皇后为皇太后，与《通鉴》己巳不同。',
      '九月庚午，尊皇后為皇太后。',12,'conflicts',
      '同一礼仪不同干支，并列待异本校。')
extra(old_campaign,'event','event_zztj_265_0904_zhu_troops_yongshou','description',
      '《旧五代史》卷二记朱全忠八月乙巳西行、癸丑至永寿，邠军不出。',
      '癸丑，次於永壽，邠軍不出。',13,'corroborates',
      '其日期与主书未明确记日的屯永寿不同，不把两条强定为同一日。')
extra(old_october,'event','event_zztj_265_0904_tenth_month_eclipse','time_original',
      '《旧唐书》卷二十下亦记十月辛卯朔日食。',
      '十月辛卯朔，日有蝕之',13,'corroborates',
      '仅印证史书记录，不推算食分和可见区域。')
extra(old_october,'event','event_zztj_265_0904_zhu_yougong_shi_executed','description',
      '《旧唐书》记朱友恭复本姓名李彦威并与氏叔琮被赐自尽。',
      '朱友恭可復本姓名李彥威，貶崖州司戶同正。',14,'corroborates',
      '姓名与贬官可据此句，赐死须参同一来源后续句，不把罪状上奏当作已证事实。')
extra(old_october,'event','event_zztj_265_0904_zhang_quanyi_henan','description',
      '《旧唐书》记丙申制张全义兼河南尹、忠武军节度及判六军诸卫事。',
      '丙申，制天平軍節度使',15,'conflicts',
      '本地《通鉴》将全义新任置丁酉，旧书制文系丙申；正文职务可相印，日分并列。')
extra(old_youyu,'event','event_zztj_265_0904_zhu_youyu_dies','description',
      '《旧五代史》卷十三记朱友裕卒于行，印证去世但未给梨园地点。',
      '會友裕卒於行，乃班師。',16,'corroborates',
      '不以旧书无梨园地名否定主书地点，也不强定两书日分。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,17):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷265天祐元年第11—16段连续处理；多书日分异说并列，疑似讹字不换算，人物改名沿稳定 key。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=265,year=904,
    primary_source_key=primary,primary_source_keys=[primary],
    paragraphs=[Q[n]['id'] for n in range(11,17)],next_paragraph=Q[17]['id'],
    coverage='卷265天祐元年第11—16段连续处理；淮南继任、何后称太后、朱全忠退兵与处死部将、朱友裕去世。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
