# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 929, paragraphs 23–27."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 37))
specs=[
 ('tongjian-276-929-spring-summer',YEAR/'part-02/sources/library/tongjian-276-929-spring-summer','04953b74','司马光等'),
 ('tongjian-276-929-gaoyu-death',P/'sources/library/tongjian-276-929-gaoyu-death','824c0b81','司马光等'),
 ('tongjian-276-929-autumn',P/'sources/library/tongjian-276-929-autumn','824c0b81','司马光等'),
 ('xinwudaishi-066-maxisheng',YEAR/'part-02/sources/library/xinwudaishi-066-maxisheng','04953b74','欧阳修'),
 ('xinwudaishi-006-929',YEAR/'part-01/sources/library/xinwudaishi-006-929','ea985438','欧阳修'),
 ('jiuwudaishi-126-fengdao-farming',P/'sources/library/jiuwudaishi-126-fengdao-farming','824c0b81','薛居正等'),
 ('jiuwudaishi-040-929-september',P/'sources/library/jiuwudaishi-040-929-september','824c0b81','薛居正等'),
 ('xinwudaishi-024-wuzhaoyu',P/'sources/library/xinwudaishi-024-wuzhaoyu','824c0b81','欧阳修'),
 ('jiuwudaishi-133-gaoyu-variant',P/'sources/library/jiuwudaishi-133-gaoyu-variant','824c0b81','薛居正等'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-929-spring-summer','tongjian-276-929-gaoyu-death','tongjian-276-929-autumn']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0929-p023-p027',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
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
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/276.txt').read_text().splitlines()
for n in range(23, 28):
    assert Q[n]['text'] == lines[Q[n]['source_line'] - 1]
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷276·天成四年（929）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0929_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','庄宗':'李存勖','殷':'马殷','希范':'马希范','希声':'马希声','郁':'高郁','季兴':'高季昌','道':'冯道','镠':'钱镠','传瓘':'钱传瓘','重诲':'安重诲','璋':'董璋','知祥':'孟知祥'}
NEW_ALIASES={'杨昭遂':['楊昭遂'],'聂夷中':['聶夷中'],'孟容':[],'冯璩':['馮璩'],'王处回':['王處回'],'乌昭遇':['烏昭遇'],'韩玫':['韓玫']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=929, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='929年九月本段；确日未载'
    key = 'event_zztj_276_0929_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_276_0929_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{next(x["name"] for x in B["people"] if x["key"]==pk)}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。',source=source)
    return key

def relationship(a,b,kind,n,quote,note,source=None):
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
    a=next(x['name'] for x in B['people'] if x['key']==pa); b=next(x['name'] for x in B['people'] if x['key']==pb)
    matches={}
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_276_0929_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Chronological entry and independent supplements; allegations remain attributed.
ch='xinwudaishi-066-maxisheng';fd='jiuwudaishi-126-fengdao-farming';sep='jiuwudaishi-040-929-september';an='xinwudaishi-024-wuzhaoyu';variant='jiuwudaishi-133-gaoyu-variant';annal='xinwudaishi-006-929'
def past(code,title,n,start,end,actors,**kw):return ev(code,title,n,start,end,actors,year=None,when='追叙或先后相对时点；本句确年日未载',**kw)
E=past('mayin_gaoyu_background','马殷用高郁为谋主，主书记楚国赖其谋略富强',23,'初，','邻国皆疾之。',[('殷','任用谋主者'),('郁','都军判官、谋主')],stable_key='event_zztj_260_0896_ma_yin_uses_gao_yu',note='同一任用背景复用896稳定事件，不新造929再次任用；富强及邻国疾之为史述评价，不造具体邻国盟敌边。')
E=past('mayin_xifan_visit_background','庄宗入洛后，马殷遣马希范入贡',23,'庄宗入洛','希范入贡，',[('殷','遣子入贡者'),('希范','入贡者')],stable_key='event_zztj_272_0923_chuwang_sends_xifan',note='复用923既有入见事件；原贵疑遣字保留，不把此追叙算929新出使。')
E=past('zhuangzong_praises_xifan_denies_rumor','庄宗称赞马希范警敏，并质疑高郁将夺马氏权位的传闻',23,'庄宗爱','郁安能得之！”',[('庄宗','评价马希范、驳传闻者'),('希范','被评价者'),('郁','传闻所指者')],note='说话确年日未独具；比闻是传闻，非证实高郁夺位，不把入洛后的所有场景都强定同一日。')
E=past('gaojixing_rumors_mayin_ignores','高季兴以流言离间高郁与马殷，马殷不听',23,'高季兴亦','殷不听；',[('季兴','以流言离间者'),('郁','受离间对象'),('殷','不听流言者')],note='高季兴沿高季昌同人，已卒于928，故不赋929；不将流言内容作为事实。')
E=past('gaojixing_letter_xisheng','高季兴遣使致书马希声，称高郁功名并示意结交',23,'乃遣使','愿为兄弟。',[('季兴','遣使致书者'),('希声','受信者'),('郁','信中被称功名者')],note='愿为兄弟为书信中的结交示意，具体对象本句未直具，不建已结义关系；使者未名不造姓名。')
E=past('envoy_sows_gaoyu_suspicion','高季兴使者对马希声称楚政皆出高郁、是马氏子孙之忧，马希声信之',23,'使者言','希声信之。',[('希声','相信使者说法者'),('郁','被称会危及马氏者')],note='高公常云为使者转述，忧患为离间说辞；不推高郁已谋反。')
claim('event',E,'description','新楚世家记高季昌使谍离间，向希声称亡马氏者必郁，希声信之。',23,'希聲用事，諜者語希聲曰：「季昌聞楚用高郁，大喜，以為亡馬氏者必郁也。」希聲素愚，以為然，','新以谍者称，主为使者，记录口径并列；亡马氏为谍说，非后来历史事实的确认。',source=ch)
E=past('yangzhaosui_slurs_gaoyu','行军司马杨昭遂谋代高郁之任，屡向马希声谗毁高郁',23,'行军司马','日谮之于希声。',[('杨昭遂','希声妻族、谋代高郁者'),('希声','听谗者'),('郁','受谗者')],note='妻族只说明与希声妻方有关，未载具体身份；不建兄弟、岳父或姻亲端点猜测，谋代任不是已取得其职。')
E=past('xisheng_petitions_gaoyu_execution','马希声指称高郁奢僭、外交邻藩，向马殷请诛',23,'希声屡言','请诛之。',[('希声','提出指控、请诛者'),('殷','接受奏请者'),('郁','被指控者')],note='指控归于马希声，不将高郁奢僭或谋反当成已查实犯罪；奏请不等马殷同意杀人。')
E=past('mayin_rejects_killing_gaoyu','马殷称功业赖高郁之力，制止马希声请诛之言',23,'殷曰：“成','汝勿为此言！”',[('殷','拒绝请诛者'),('希声','被制止者')])
E=past('gaoyu_demoted_to_march_secretary','马希声坚持请罢高郁兵柄，高郁被左迁为行军司马',23,'希声固请','乃左迁郁行军司马。',[('希声','请罢兵柄者'),('郁','被夺兵职、左迁者')],note='高郁与先前行军司马杨昭遂不同人，未推杨随后实际继高之任；降职与次日杀人分。')
claim('event',E,'description','新楚世家同记希声信谍后遽夺高郁兵职。',23,'希聲素愚，以為然，遽奪郁兵職，','素愚为史评，兵职被夺为行动；没有补出确定降职年份。',source=ch,relation='corroborates')
E=past('gaoyu_intends_retirement','高郁对亲近者称要营西山归老，并以猘子作比',23,'郁谓所亲','能咋人矣。”',[('郁','表示拟归老者')],note='将归老是意向，不表示已经退休；猘子为比喻，不新造高郁儿子实体或父子关系。')
E=past('xisheng_forges_mayin_order_kills_gaoyu','马希声闻高郁之言益怒，次日假称马殷命令，在府舍杀高郁',23,'希声闻之','杀郁于府舍，',[('希声','矫命杀人者'),('郁','被杀者')],note='初段追叙未独具死亡年，暂null；矫以殷命是冒命，不将马殷记为下令杀人者。')
claim('event',E,'description','新楚世家同记希声闻言后矫殷令杀郁，殷尚不知。',23,'希聲聞之，矯殷令殺郁。殷老不復省事，莫知郁死，','补证冒命和殷不知；新末称明年殷薨提供相对线索，未单独以此赋本事件绝对年。',source=ch,relation='corroborates')
claim('event',E,'description','旧马希范传追叙则称希范嫉高郁，因庄宗言而杀之，与主书及新楚世家的希声归责不同。',23,'先是，希範常嫉高郁之為人，因莊宗言而殺之，','杀者希范/希声异说保留，未据旧段另造第二次高郁死亡；后续幻见和马希范卒不计入本批，纸本待核。',source=variant,relation='conflicts')
E=past('xisheng_falsely_announces_gaoyu_rebellion','马希声榜告中外，诬称高郁谋叛，并杀其族党',23,'榜谕','并诛其族党。',[('希声','榜告、诬叛并诛族党者'),('郁','被诬谋叛者')],note='诬为主书明示，不呈现为真实谋叛；族党未名未具人数，不推九族或所有亲属被杀。')
E=past('mayin_fog_queries_prison','马殷至暮尚不知高郁被杀，因当日大雾询问马步院是否有冤死者',23,'至暮','岂有冤死者乎？”',[('殷','以旧经历为比而询冤者')],note='雾与杀冤相联系是马殷解释，不确证超自然因果；孙儒渡淮是话中旧事，不新录929渡淮。')
E=past('mayin_learns_gaoyu_death_grieves','次日吏告高郁死，马殷大恸，叹政不由己、勋旧横遭冤酷',23,'明日，吏','吾亦何可久处此乎！”',[('殷','知死后悲恸者')],note='两次明日为相对时序，不编公历日；何可久处是叹语，不提前记录马殷去世或退位。')
claim('event',E,'description','新楚世家同记次日吏白，马殷拊膺大哭，并叹杀其勋旧。',23,'明日，吏以狀白，殷拊膺大哭曰：「吾荒耄如此，而殺吾勳舊！」','当事人悲叹按发言保存；不覆盖主政非己出的说法。',source=ch,relation='corroborates')
E=ev('fengdao_warns_against_complacency','冯道以昔日井陉谨慎、平路失控坠马作比，劝李嗣源治天下勿懈，帝认可',24,'九月，','上深以为然。',[('帝','与冯道谈丰年、认可劝谏者'),('道','以旧事劝戒者')],note='奉使中山与坠马为既往例证，当前事件是九月劝谏；年丰四方无事为谈话背景，不指全天下不存在战事。')
claim('event',E,'description','旧冯道传将此类延英劝谏概括在天成、长兴中，劝帝勿因清晏丰熟纵逸乐。',24,'陛下勿以清晏豐熟，便縱逸樂，兢兢業業，臣之望也。','旧没有独系929九月，以主书纪时；未把传中各次延英访问合成同一次。',source=fd,relation='corroborates')
E=ev('emperor_asks_farmers_welfare','李嗣源问冯道：丰年百姓是否赡足',24,'上又问','百姓赡足否？”',[('帝','问民生者'),('道','被问者')],note='又问无同一天明文；旧传他日明确另一日，当前纪年从主九月而非所有谈话同日。')
claim('event',E,'description','旧冯道传以他日又问记帝询天下虽熟、百姓得济否。',24,'他日又問道曰：「天下雖熟，百姓得濟否？」','他日表另日，对话不强同一场；本书未独载该问年月。',source=fd,relation='adds')
E=ev('fengdao_explains_farmers_hardships','冯道解释农家凶年流亡饥饿、丰年谷贱受损，并引聂夷中诗劝帝知农苦',24,'道曰：“农家','人主不可不知也。”',[('道','陈述农家困境、引诗者'),('聂夷中','被引诗的作者')],note='聂为诗作者而非现场进谏者，进士是主书所称；原农于四人保留，不悄改四民。农困境是冯之论述，不当本批新增全国饥荒数据。')
claim('event',E,'description','旧冯道传引《伤田家诗》作五月粜秋谷，主书作五月粜新谷，后四句旧传亦录。',24,'臣憶得近代有舉子聶夷中《傷田家詩》云：『二月賣新絲，五月糶秋穀。醫得眼下瘡，剜卻心頭肉。我願君王心，化作光明燭。不照綺羅筵，遍照逃亡屋。』','新谷与秋谷为词语异文而非繁简，引用各自保留；旧举子与主进士口径未强证明登第年，不挪全诗为主书原文。',source=fd,relation='conflicts')
E=ev('emperor_records_recites_nie_poem','李嗣源悦，命侍从录聂夷中诗，并常诵读',24,'上悦，',None,[('帝','命录诗并常诵者'),('聂夷中','其诗被录诵者')],note='常诵为反复行为非单日完成全部；侍从未名不猜人物。')
claim('event',E,'description','旧冯道传同记明宗称诗甚好，命侍臣录下，每自讽之。',24,'明宗曰：「此詩甚好。」遂命侍臣錄下，每自諷之。','同一举措补证，不另造第二次独立诏录。',source=fd,relation='corroborates')
E=ev('dongzhang_retains_fuzhou_soldiers','鄜州戍东川兵归本道，董璋擅留壮者、遣老弱归并收甲兵',25,'鄜州',None,[('璋','擅留壮卒、选返老弱并收甲兵者')],place='东川至鄜州',note='选赢老底本原字，展示依上下文写老弱，赢疑羸待纸本核；未具人数。仍收其甲兵不推所有东川军皆被缴械，留兵与回本道不是战役。')
person('孟容',26,'西川右都押牙，被论死资州税官的兄长',span(26,'癸巳，','坐自盗抵死，'))
E=ev('zizhou_tax_official_death_sentence','孟容之弟任资州税官，因自盗获死罪',26,'癸巳，','坐自盗抵死，',[],when='929年九月癸巳',place='资州',note='税官是孟容弟而非孟知祥弟，姓名未载不造实名或具体亲缘端点；抵死记罪当死，不另推死刑执行日、侵盗金额。')
E=ev('fengqu_wangchuhui_plead_tax_official','观察判官冯璩、中门副使王处回为被论死税官请免',26,'观察判官','为之请，',[('冯璩','为税官请免的观察判官'),('王处回','为税官请免的中门副使')],when='929年九月癸巳',place='西川',note='两者请求不等获准，职务主载，王处回新主体，不猜与孟容的亲属关系。')
E=ev('mengzhixiang_refuses_exception','孟知祥称即便自己的弟弟犯法亦不可贷，拒绝徇私宽免',26,'孟知祥曰',None,[('知祥','拒绝为他人弟犯法宽贷者')],when='929年九月癸巳',place='西川',note='虽吾弟是反事实举例，非其亲弟实际犯此罪；按拒绝宽免记，不猜随后现场处决。')
E=past('qianliu_varies_envoy_gifts','主书记钱镠按朝廷使者是否曲意奉承而厚薄礼遇',27,'吴越王镠','礼遇疏薄。',[('镠','被史书记有差等接待者')],place='吴越',note='传述惯常接待，无确年日或每位使者姓名；好自大为史评，不扩为贪腐定罪。')
E=past('qianliu_arrogant_letter_anchonghui','钱镠曾致书安重诲，主书记其辞礼倨傲',27,'尝遗','辞礼颇倨。',[('镠','致书者'),('重诲','受信者')],note='尝为前事不赋929九月；倨为史评，不猜原书完整措辞。')
claim('event',E,'description','新安重诲传同记钱镠寓书礼慢，重诲怒，欲借机发作。',27,'鏐遣使朝京師，寓書重誨，其禮慢。重誨怒，未有以發，','愤怒为本传史述，未凭此造永久敌对关系；明宗即位为段背景，不强致信即926即位日。',source=an,relation='adds')
E=past('wuzhaoyu_hanmei_mission','李嗣源遣供奉官乌昭遇、韩玫使吴越，二人有隙',27,'帝遣','昭遇与玫有隙，',[('帝','遣使者'),('乌昭遇','吴越使者'),('韩玫','吴越使者')],place='后唐至吴越',note='主只知于处分前，出使确年月未具；有隙不造永远敌人关系。')
E=event('hanmei_whips_wuzhaoyu','新安重诲传记韩玫恃重诲势，醉后以马鞭击乌昭遇',27,'而玫恃重誨勢，數凌辱昭遇，因醉使酒，以馬箠擊之。',[('韩玫','醉后凌辱击人者'),('乌昭遇','被鞭击者')],year=None,when='吴越使行中的补述；确年日未载',place='吴越使行',source=an,note='补书明确行为，主有隙只概叙；不补伤势、死亡或参与人数。')
E=event('wuzhaoyu_stops_qianliu_report','新安重诲传记钱镠欲奏韩玫凌辱事，乌昭遇以为辱国而阻止',27,'鏐欲奏其事，昭遇以為辱國，固止之。',[('镠','拟上奏者'),('乌昭遇','劝止上奏者')],year=None,when='使者受辱后；确年日未载',place='吴越',source=an,note='欲奏未等已经递表，阻止据本传；不把钱拟奏与后续自诉冤表混为一事。')
E=past('hanmei_accuses_wuzhaoyu','使者还，韩玫指控乌昭遇见钱镠称臣拜舞、称殿下及私告国事',27,'使还，','私以国事告镠。”',[('韩玫','提出指控者'),('乌昭遇','受指控使者'),('镠','指控中会见对象')],note='各行为都为韩玫奏言，非已查实事实；旧副使作刘玫而主新作韩玫，未将刘自动列实名别名。')
claim('event',E,'description','新安重诲传将韩玫的同一指控称为返谮。',27,'及玫還，返譖於重誨曰：「昭遇見鏐，舞蹈稱臣，而以朝廷事私告鏐。」','谮性质明示，避免图谱把指控行为当乌真实行为。',source=an,relation='corroborates')
claim('event',E,'description','旧明宗纪先述指控，后记另有浙中使还者称昭遇无臣钱镠之事，是玫诬陷。',27,'後有自浙中使還者，言昭遇無臣鏐之事，為玫所誣，人頗以為冤。','后续使者辩词为补述，未具确日不新造当年同日正式平反；本纪使副名刘玫，与主新韩玫保留人名异文待核，不新造两个确定告发者。',source=sep,relation='adds')
E=past('anchonghui_petitions_wuzhaoyu_death','安重诲奏请赐乌昭遇死',27,'安重诲奏','赐昭遇死。',[('重诲','请赐死者'),('乌昭遇','被请赐死者')],note='奏请与执行分，安不是现场行刑者；实际死由新明宗纪九月癸巳另证。')
E=event('wuzhaoyu_killed','新明宗纪记供奉官乌昭遇于九月癸巳被杀',27,'九月癸巳，殺供奉官烏昭遇。',[('乌昭遇','被杀的供奉官')],when='929年九月癸巳',place='后唐',source=annal,note='执行日期由本纪明示；旧寻赐自尽、新安传坐死御史狱方式口径另存，不假定斩首。')
claim('event',E,'description','旧明宗纪记乌昭遇下御史台，随后被赐自尽。',27,'烏昭遇下御史台，尋賜自盡。','寻为随后，不强与钱癸巳诏同一时刻；与新杀及坐死御史狱的表述并列，不猜刑具。',source=sep,relation='adds')
E=ev('qianliu_titles_removed','后唐制钱镠以太师致仕，削其余官爵',27,'癸巳，制','自馀官爵皆削之，',[('镠','被削官爵、以太师致仕者')],when='929年九月癸巳',place='后唐对吴越',note='太师仍在，不写钱完全无任何称号或已失去吴越实际控制；不自动补清年月日。')
claim('event',E,'description','旧明宗纪同日明确去钱镠元帅、尚父、吴越国王称号，授太师致仕。',27,'癸巳，製天下兵馬元帥、尚父、吳越國王錢鏐可落元帥、尚父、吳越國王，授太師致仕，責無禮也。','补被削三种称号，责任理由据诏和史述归属，不变成已查实乌称臣。',source=sep,relation='corroborates')
E=ev('wuyue_agents_ordered_arrested','朝廷令各地拘治吴越进奏官、使者、纲吏',27,'凡吴越','令所在系治之。',[],when='929年九月癸巳诏；执行确日未载',note='拘治命令非证明各地所有人员均被捕；未名人数地点不补。')
claim('event',E,'time_original','旧明宗纪另记九月乙未诏查两浙纲运进奉使，并下巡狱。',27,'乙未，詔諸道通勘兩浙綱運進奉使，並下巡獄。','主癸巳制中令拘与旧乙未后诏可能先后两令，未强作同一天日期冲突或两倍被捕人数。',source=sep,relation='adds')
E=ev('qianliu_sons_petition_ignored','钱镠令钱传瓘等子上表诉冤，朝廷均不省',27,'镠令子',None,[('镠','令诸子上表者'),('传瓘','奉命上表的儿子')],when='929年九月削爵后；表与不省确日未载',note='表明尝试申诉而非立即恢复官爵，未提前记安重诲死后的复爵；不猜未名其他子。')
relationship('镠','传瓘','父亲',27,'镠令子传瓘等上表讼冤，','钱镠→钱传瓘为父亲，复用已有同向边；不反向重复造儿子关系。')
review='卷276连续929年第23—27段、原109—113行。展示简体、原文保留底本。初段全为追叙，既有任谋主与923入贡复用稳定事件，其他确年日未具用null；高季兴已死928，离间不得标929。流言和奏请与事实分，愿兄弟非结义；杨昭遂妻族不猜具体亲缘。马殷拒请诛，后罢兵柄与矫命杀人分，猘子不造子，榜称谋叛明为诬，族党不猜姓名人数，雾因果只记马解释，明日为相对先后。新楚同希声矫命，旧马希范传归责希范，保留异说不第二次死亡，不前移后续幻见和卒。冯道旧井陉奉使是例证，不新929出使；旧他日又问不强同一场。聂夷中为被引诗作者非在场，主新谷/旧秋谷词异文原存，农四人不悄改，天下丰熟是对话背景。鄜州兵选赢老疑羸原存，展示老弱，归老留壮收甲无数量。资州税官为孟容之弟非孟知祥弟，虽吾弟为假设，抵死不猜执行日，无名弟未造。乌韩隙出使旧事、韩鞭/乌止钱欲奏为新补；称臣拜舞私告全是韩指控，新返谮、旧后使辩并存，旧刘玫/主新韩玫人名异文不自动合别名或另造确定刘。安奏与新九月癸巳实际死亡分，旧赐尽/新坐死方式并列不定斩刑。钱太师致仕仍太师，其余削非失吴越实控；拘治为命令，旧乙未诏可先后令不强同日。诸子表不省非已复爵，父边复用，纸本异文待核。第28段起尚未处理。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(23,28):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=929,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(23,28)],next_paragraph='zztj-v276-y0929-p028',next_volume=276,next_year=929,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷276连续929年第23—27段、原109—113行；高郁案、冯道农事问答、东川留兵、资州税官与吴越使者案。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(23,28)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
