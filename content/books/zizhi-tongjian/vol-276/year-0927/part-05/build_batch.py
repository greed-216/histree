# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 927, paragraphs 19–25."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 26))
specs=[
 ('tongjian-276-late-927-opening',YEAR/'part-04/sources/library/tongjian-276-late-927-opening','e00f3e22','司马光等'),
 ('xinwudaishi-028-zhouxuanbao',P/'sources/library/xinwudaishi-028-zhouxuanbao','cf38d77b','欧阳修'),
 ('jiuwudaishi-038-december-records',P/'sources/library/jiuwudaishi-038-december-records','cf38d77b','薛居正等'),
 ('xinwudaishi-006-927-opening',ROOT/'content/books/zizhi-tongjian/vol-275/year-0927/part-01/sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-late-927-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0927-p019-p025',
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
for n in range(19, 26):
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
        citation = f'卷276·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0927_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','吴主':'杨溥','知询':'徐知询','知诰':'李昪','汉主':'刘岩','王氏':'王氏（吴太妃）','濛':'杨濛','澈':'杨澈','珙':'杨珙'}
NEW_ALIASES={'王氏（吴太妃）':[],'杨珙':['楊珙'],'周玄豹':[],'马缟':['馬縞'],'周令武':[]}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成二年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='927年十二月本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_276_0927_' + code
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
        edge = 'participation_zztj_276_0927_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0927_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
old='jiuwudaishi-038-december-records';new='xinwudaishi-006-927-opening';feng='xinwudaishi-028-zhouxuanbao'
E=ev('wu_wang_dowager_empress','吴主杨溥尊太妃王氏为皇太后',19,'丙子','皇太后，',[('吴主','尊号授予者'),('王氏','太妃、获尊皇太后者')],when='927年十一月丙子',place='吴',note='只按太妃及尊号识别王氏，不凭此句断定她是杨溥生母或建立母子关系。')
E=ev('xuzhixun_deputy_two_commands','徐知询任诸道副都统、镇海宁国节度使兼侍中',19,'以徐知询','兼侍中，',[('知询','诸道副都统、镇海宁国节度使兼侍中获授者')],when='927年十一月丙子',place='吴',note='本段官衔与上一段新史所补辅国大将军金陵尹区分；不据此认定已代徐知诰在广陵执吴政。')
E=ev('libian_commander_inside_outside','徐知诰加都督中外诸军事',19,'加徐知诰',None,[('知诰','都督中外诸军事加授者')],when='927年十一月丙子',place='吴',note='姓名沿用李昪稳定key，展示史载徐知诰；与前段太尉兼侍中分授，不另造人物。')
E=ev('mengzhixiang_chengdu_wall_labor','孟知祥征发民丁二十万修成都城',20,'十二月',None,[('孟知祥','征发民丁修城者')],when='927年十二月戊寅朔',place='成都',note='二十万为原载民丁数，不当兵力；修城动作不等城墙已于同日竣工，无坐标推断。')
for code,name,title,start,end in [
 ('yangmeng_changshan','濛','常山王','吴主立兄','常山王，'),
 ('yangche_pingyuan','澈','平原王','弟鄱阳公','平原王，'),
 ('yanggong_jianan','珙','建安王','兄子南昌公',None),
]:
 E=ev(code,'吴主杨溥封'+ALIASES[name]+'为'+title,21,start,end,[(name,'获封'+title+'者')],place='吴',note='原公号及新王号是同一主体；本句未具干支，不强定戊寅朔。')
relationship('濛','吴主','兄长',21,'吴主立兄庐江公濛为常山王，','原明兄，A是B兄长；复用既有杨濛至杨溥关系key，不重建反向边。')
relationship('吴主','澈','兄长',21,'吴主立兄庐江公濛为常山王，弟鄱阳公澈为平原王，','吴主之弟澈，按统一方向吴主是澈兄长；不反向另建弟弟边。')
relationship('吴主','珙','叔父',21,Q[21]['text'],'兄子明确吴主兄之子，吴主为叔父；未明其父是哪位兄，不能由相邻的杨濛推父子。')
E=ev('zhouxuanbao_predicts_siyuan','周玄豹曾对李嗣源作贵不可言的相术预言',22,'初','贵不可言，',[('周玄豹','晋阳相者、预言话语所归者'),('帝','被相者')],year=None,when='初追叙，李嗣源即位之前，确年日未载',place='晋阳',note='这是史书所记预言话语，不作为相术能力或预言真实有效的客观证明。')
claim('event',E,'description','新赵凤传记安重诲曾使他人与李嗣源易服试周玄豹，周识出李嗣源后言其贵不可言。',22,'明宗為內衙指揮使，重誨欲試玄豹，乃使佗人與明宗易服，而坐明宗於下坐，召玄豹相之，玄豹曰：「內衙，貴將也，此不足當之。」乃指明宗於下坐曰：「此是也！」因為明宗言其後貴不可言。','补记相术故事的叙述经过，前事确年未明；不把传闻试验视作现代可证能力。',source=feng)
E=ev('siyuan_plans_summon_zhouxuanbao','李嗣源即位后欲召周玄豹到阙',22,'帝即位','欲召诣阙。',[('帝','计划召见者'),('周玄豹','拟被召者')],year=None,when='李嗣源即位之后，本段未明召见计划的确年日',place='后唐朝廷',note='欲召为计划，不能录成周已到京；即位背景不是927发生的新即位事件。')
E=ev('zhaofeng_warns_fortuneteller_summon','赵凤劝阻召周玄豹，担心争问吉凶及妄言致祸',22,'赵凤曰','非所以靖国家也。”',[('赵凤','劝阻者'),('帝','受谏者')],year=None,when='李嗣源即位后召见计划时，确年日未载',place='后唐朝廷',note='已验是赵凤所说话语，族灭是其警示，不推周已致人族灭或全京人已经聚集。')
claim('event',E,'description','新赵凤传同述赵凤以召术士会使众人奔走吉凶、转相惑乱为由进谏，并记明宗不再召周玄豹。',22,'鳳諫曰：「好惡，上所慎也。今陛下神其術而召之，則傾國之人，皆將奔走吉凶之說，轉相惑亂，為患不細。」明宗遂不復召。','印证劝阻及未再召结果，不外推周已入京。',source=feng,relation='corroborates')
E=ev('zhouxuanbao_retirement_and_gifts','李嗣源就授周玄豹光禄卿致仕，厚赐金帛',22,'帝乃',None,[('帝','就授及赏赐所归者'),('周玄豹','光禄卿致仕及金帛受赐者')],year=None,when='召见计划受劝阻之后，确年日未载',place='周玄豹所在，本句未具地',note='就除致仕，不能据光禄卿衔记已赴京履职；厚赐未载具体数量。')
E=ev('magao_proposes_separate_parent_temple','马缟请在七庙外另立亲庙，援引汉光武故事',23,'中书舍人','亲庙；',[('马缟','中书舍人、提议者')],note='请是建议；汉光武是援引先例，不建927汉光武活动或现代宗庙位置。')
E=ev('ministers_propose_huang_not_di','中书门下奏请祖先称皇不称帝，援引汉孝德孝仁皇例',23,'中书门下','称皇不称帝。',[],note='中书门下群体未具人名，不虚构宰相发言；建议不等实际执行。')
E=ev('siyuan_wants_ancestor_emperor_titles','李嗣源欲为祖先兼称帝',23,'帝欲','帝欲兼称帝，',[('帝','欲兼称帝者')],note='欲是意向，不作为最终追尊诏令已经发出。')
E=ev('ministers_cite_tang_temple_examples','群臣援引德明玄元兴圣皇帝立庙京师的先例',23,'群臣乃','皆立庙京师；',[],note='京师立庙是援引的前代先例，不是本次李嗣源最终令立庙地点。')
E=ev('siyuan_ancestral_temple_yingzhou','李嗣源令在应州旧宅立亲庙',23,'帝令','应州旧宅，',[('帝','令立庙者')],place='应州旧宅',note='最终令立于应州旧宅与群臣先例京师区分；旧新纪另具丙午，不将全段提案都强定为同日。')
claim('event',E,'description','旧明宗纪记丙午追尊四庙，以应州旧宅为庙。',23,'丙午，追尊四廟，以應州舊宅為廟。','补实际追尊立庙诏令的十二月丙午，不扩张至前面各项讨论的确日。',source=old,relation='corroborates')
claim('event',E,'time_original','旧明宗纪补记927年十二月丙午。',23,'丙午，追尊四廟，以應州舊宅為廟。','旧原月头十二月，丙午仅赋对应诏令；保留主书本句未具日。',source=old)
E=ev('siyuan_ancestors_posthumous_titles','李嗣源追谥自高祖考妣以下为皇帝皇后，墓称陵',23,'自高祖',None,[('帝','祖先追尊所归者')],place='应州亲庙及祖先墓地',note='本句祖先未具名，未由帝号先例误造亲属；墓曰陵为称谓不推新建全部陵墓。')
quote=(sources[new]/'source.txt').read_text();start=quote.index('丙午，追尊祖考');end=quote.index('立廟于應州。',start)+len('立廟于應州。')
claim('event',E,'description','新明宗纪在十二月丙午记追尊：高祖聿孝恭、庙号惠祖，刘氏孝恭昭；曾祖敖孝质、毅祖，张氏孝质顺；祖琰孝靖、烈祖，何氏孝靖穆；考孝成、德祖，妣刘氏孝成懿，并立庙应州。',23,quote[start:end],'补具体名号列表，考本句未具名；只补同一追尊主体事实，不据缺名猜造新人物及血缘链。',source=new)
claim('event',E,'time_original','新明宗纪亦记927年十二月丙午追尊祖考及妣。',23,'丙午，追尊祖考為皇帝，妣為皇后：','该句接十二月条，补实际追尊日期；不据此给其他议论同日。',source=new,relation='corroborates')
E=ev('liuyan_visits_kangzhou','南汉主刘岩到康州',24,'汉主',None,[('汉主','到康州者')],place='康州',note='如为到往，不扩为征讨或新建都；本句未具日，沿十二月段落位置记录。')
E=ev('wei_dai_border_grain_price','927年蔚代缘边粟每斗不超过十钱',25,'是岁',None,[],when='927年年度总述，无具体月日',place='蔚州、代州缘边',note='原记地区、斗与钱单位，未换算重量货币或全国价格；低价不等全国或每户富裕。')
E=event('zhoulingwu_border_report','周令武替任归阙，奏报山北安宁及雁门以北粮价',25,'己卯，蔚州刺史周令武得代歸闕，帝問北州事，令武奏曰：「山北甚安，諸蕃不相侵擾。雁門已北，東西數千里，鬥粟不過十錢。」',[('周令武','蔚州刺史、替任归阙奏报者'),('帝','问北州事者')],source=old,when='927年十二月己卯',place='后唐朝廷，奏报山北雁门以北',note='旧独补奏报者与日；安宁、数千里及价格是周的报告，不直接扩大为通鉴蔚代全国实测样本。')
review='连续19—25段逐句校核。丙子吴王氏尊后、知询诸道副都统镇海宁国侍中、知诰加都督分事，不重前段新太尉金陵尹。王氏仅太妃语境，不明母谁不建母边。戊寅朔成都民丁二十万是修城征发不是兵数或竣工。三封王无干支不强戊寅；濛兄澈弟统一兄长方向、复用濛溥边；珙兄子仅杨溥叔父，不猜其父。周玄豹初前事null，召见计划即位后未明年null、赵话语不作相术已证，未到京；新补易服故事和不复召，主就除致仕赐金不当履任。宗庙提议、称号意向、援唐例与最终应州令分阶段；旧新丙午仅对应追尊立庙，不赋前面讨论；新补祖先名谥列表，考不具名不造血缘谱。刘岩到康州不推战争。粟价年度地方记载，旧周令武己卯归阙奏山北安宁雁门北粮价为报告，不推全国价格富裕；鬥原字保留单位展示斗。展示简体、摘录保留底本，纸本及异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19,26):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(19,26)],next_paragraph='zztj-v276-y0928-p001',next_volume=276,next_year=928,supplements=supplements,excluded_non_body=[],coverage='卷276连续19—25段、原文件24—30行；927年末任官、修城、封王、术士召见、宗庙追尊、康州及边地粮价。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(19,26)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
