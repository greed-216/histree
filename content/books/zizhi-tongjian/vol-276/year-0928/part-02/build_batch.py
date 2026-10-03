# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 9–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 53))
specs=[
 ('tongjian-276-late-927-opening',YEAR.parent/'year-0927/part-04/sources/library/tongjian-276-late-927-opening','e00f3e22','司马光等'),
 ('tongjian-276-court-disputes',P/'sources/library/tongjian-276-court-disputes','3059d229','司马光等'),
 ('tongjian-276-salt-wars',P/'sources/library/tongjian-276-salt-wars','f890926e','司马光等'),
 ('xinwudaishi-043-kongxun-marriage',P/'sources/library/xinwudaishi-043-kongxun-marriage','f890926e','欧阳修'),
 ('jiuwudaishi-090-huawenqi',P/'sources/library/jiuwudaishi-090-huawenqi','f890926e','薛居正等'),
 ('jiuwudaishi-091-wangjianli',P/'sources/library/jiuwudaishi-091-wangjianli','f890926e','薛居正等'),
 ('xinwudaishi-054-zhengjue-retirement',P/'sources/library/xinwudaishi-054-zhengjue-retirement','f890926e','欧阳修'),
 ('jiuwudaishi-039-february',YEAR/'part-01/sources/library/jiuwudaishi-039-february','c991ab36','薛居正等'),
 ('jiuwudaishi-039-march',YEAR/'part-01/sources/library/jiuwudaishi-039-march','c991ab36','薛居正等'),
 ('xinwudaishi-006-928',YEAR/'part-01/sources/library/xinwudaishi-006-928','c991ab36','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-late-927-opening','tongjian-276-court-disputes','tongjian-276-salt-wars']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p009-p010',
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
for n in range(9, 11):
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
        citation = f'卷276·天成三年（928）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0928_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','重诲':'安重诲','循':'孔循','温琪':'华温琪','建立':'王建立','弘昭':'朱弘昭','硃弘昭':'朱弘昭','珏':'郑珏','德妃':'王德妃（李嗣源妃）'}
NEW_ALIASES={'王德妃（李嗣源妃）':['王德妃']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成三年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='928年三月本段；确日未载', note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_276_0928_' + code
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
        edge = 'participation_zztj_276_0928_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0928_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
kong='xinwudaishi-043-kongxun-marriage';hua='jiuwudaishi-090-huawenqi';wang='jiuwudaishi-091-wangjianli';zheng='xinwudaishi-054-zhengjue-retirement';feb='jiuwudaishi-039-february';mar='jiuwudaishi-039-march';new='xinwudaishi-006-928'
E=ev('anzhonghui_trusts_kongxun','安重诲亲信孔循',9,'枢密使','安重诲亲信之。',[('重诲','亲信孔循者'),('循','枢密使同平章事、被亲信者')],year=None,when='孔循二月乙未出镇之前的背景，确年未载',place='后唐朝廷',note='狡佞为主史家评价，亲信为叙述关系，不建立永恒盟友边或新增枢密任命。')
claim('event',E,'description','新孔循传同记安重诲亲信孔循，对其话语多听用。',9,'循為人柔佞而險猾，安重誨尤親信之，凡循所言，無不聽用。','保留评价与听用的史书叙述性质，未视为所有历次政策均完全照办的实测统计。',source=kong,relation='corroborates')
E=ev('siyuan_proposes_anzhonghui_daughter_marriage','李嗣源欲为皇子娶安重诲女',9,'帝欲','娶重诲女，',[('帝','婚事提议者'),('重诲','拟嫁女之父')],year=None,when='孔循出镇前追叙，确年日未载',place='后唐朝廷',note='皇子未具名，不能自动指定李从厚；欲为计划，不建婚姻已成或另造未具名人物。')
E=ev('kongxun_dissuades_anzhonghui_marriage','孔循以安重诲居近密为由，劝其勿与皇子为婚',9,'循谓','不宜复与皇子为婚。”',[('循','劝阻婚议者'),('重诲','受劝者')],year=None,when='孔循出镇前追叙，确年日未载',place='后唐朝廷',note='孔循判断为话语，不等制度法律禁止枢密与皇室通婚。')
E=ev('anzhonghui_declines_marriage','安重诲辞去皇子娶其女的婚议',9,'重诲辞','重诲辞之。',[('重诲','辞婚议者')],year=None,when='前述婚议之后，确年日未载',place='后唐朝廷',note='不建安女与皇子实际妻夫边；新同述止婚，身份复用。')
claim('event',E,'description','新孔循传称明宗曾欲为皇子娶安女，孔循劝止后安重诲听信，婚议停止。',9,'明宗嘗欲以皇子娶重誨女，重誨以問循，循曰：「公為機密之臣，不宜與皇子婚。」重誨信之，乃止。','同一提议劝阻结果，新未为本次皇子具名。',source=kong,relation='corroborates')
E=ev('anonymous_warns_kongxun','有人提醒安重诲，称孔循善离间人，不宜留机密之地',9,'久之','不可置之密地。”',[('重诲','听取提醒者')],year=None,when='久之前述婚议之后，确年日未载',place='后唐朝廷',note='或未具名不虚构劝告者；对孔的指责是话语，不升级为所有事件因果已证。')
E=ev('kongxun_contacts_wangdefei','孔循知有人提醒安重诲后，暗遣人结王德妃，求嫁其女',9,'循知之','求纳其女；',[('循','暗遣接近及求婚者'),('德妃','被接近者')],year=None,when='孔循出镇前的婚事追叙，确年日未载',place='后唐宫廷',note='王德妃限定李嗣源后宫身份，区别吴太妃王氏；女指孔循女，但本段未具名，不先建立已婚边。')
E=ev('wangdefei_requests_kong_daughter_conghou','王德妃请求李从厚娶孔循女',9,'德妃请','为从厚妇，',[('德妃','提出婚请者'),('李从厚','拟娶者'),('循','拟嫁女之父')],year=None,when='孔循出镇前婚事追叙，确年日未载',place='后唐宫廷',note='妇为所请目标，未当本段已举行婚礼；李从厚稳定key不建其他皇子代称。')
E=ev('siyuan_approves_kong_daughter_marriage','李嗣源同意李从厚娶孔循女的请求',9,'德妃请','帝许之。',[('帝','同意婚请者'),('李从厚','获准娶者')],year=None,when='孔循出镇前婚议获准，确年日未载',place='后唐宫廷',note='许为批准婚事，未提前后文十一月实际纳妃；新传以妻皇子概述结果，不据概述定婚礼在二月。')
claim('event',E,'description','新孔循传称孔循暗中遣人向明宗请求嫁女，明宗以李从厚娶之，安重诲因此恶孔循并使其出忠武。',9,'而循陰使人白明宗，求女妻皇子，明宗即以宋王從厚娶循女。重誨始惡其為人，出循為忠武軍節度使，','新传合婚事结果与出镇概述，不具王德妃媒介与婚礼确日；主获准与后段实际纳妃区分，不创造提前婚礼。',source=kong)
E=ev('kongxun_zhongwu_eastern_capital','孔循出任忠武节度使，兼东都留守、同平章事',9,'重诲大怒','东都留守。',[('循','忠武节度使兼东都留守同平章事出镇者'),('重诲','主书所记因婚事大怒者')],when='928年二月乙未',place='忠武、东都',note='主记大怒及调职，怒是反应不自动造主谋已证细节；出镇保留使相而新纪孔循罢指枢密职位。')
claim('event',E,'description','旧明宗纪同日称枢密使兼东都留守孔循任许州节度使、兼东都留守。',9,'乙未，以樞密使兼東都留守孔循為許州節度使兼東都留守，','忠武与许州为镇军、治州记法；不是东都留守新授第二次任命。',source=feb,relation='corroborates')
claim('event',E,'description','新明宗纪二月乙未记孔循罢。',9,'乙未，孔循罷。','通看前后任官语境为罢枢密，主保同平章出镇，不推所有官衔均被削尽。',source=new,relation='corroborates')
E=ev('huawenqi_enters_court_requests_stay','秦州节度使华温琪入朝，请留阙下',9,'秦州节度使','请留阙下，',[('温琪','秦州节度使、入朝请留者')],year=None,when='岁馀前的入朝追叙，确年日未载',place='秦州至后唐朝廷',note='不能因插入928二月乙未后就强当天入朝；旧传从明宗即位叙来，尚不能直接确定本动作年。')
claim('event',E,'description','旧华温琪传称明宗即位后，华温琪因入朝而愿留阙，明宗嘉许。',9,'明宗即位，因入朝，願留闕，明宗嘉而許之，','印证入朝留阙，但未为具体入朝另给年日；不重造明宗即位事件。',source=hua,relation='corroborates')
E=ev('huawenqi_left_xiaowei_monthly_grants','李嗣源嘉许华温琪留阙，授左骁卫上将军并每月另赐钱谷',9,'帝嘉之','月别赐钱谷。',[('帝','嘉许任官与赐钱谷所归者'),('温琪','左骁卫上将军、每月钱谷受赐者')],year=None,when='上述入朝获许后、岁馀之前，确年日未载',place='后唐朝廷',note='按原明确左骁卫，与前批张筠左右卫异文无关；赐钱谷无数，不推具体俸禄额度。')
claim('event',E,'description','旧华传同记左骁卫上将军及逐月另赐钱粟。',9,'除左驍衛上將軍，逐月別賜錢粟，以豐其家。','粟与主谷名词补证，丰其家为旧所述授赐目的，不扩大实际家产数。',source=hua,relation='corroborates')
E=ev('siyuan_requests_major_post_huawenqi','过了一年多，李嗣源要求给华温琪择一重镇',9,'岁馀','宜择一重镇处之。”',[('帝','要求择重镇者'),('温琪','拟安置重镇者')],year=None,when='华温琪留阙任官岁馀后，确年日未载',place='后唐朝廷',note='岁馀只相对间隔，不借928位置倒算入朝926或927；要求非实际已授新节镇。')
E=ev('anzhonghui_claims_no_vacancy_hua','安重诲以无空缺回应安置华温琪',9,'重诲对以','重诲对以无阙。',[('重诲','以无空缺答奏者')],year=None,when='华温琪留阙岁馀后的答奏，确年日未载',place='后唐朝廷',note='无阙是答奏理由，不作全国实际岗位普查。')
E=ev('siyuan_repeatedly_requests_hua_post','李嗣源他日又屡次提及华温琪外任',9,'他日','帝屡言之，',[('帝','再次要求安置者')],year=None,when='上述无阙答奏之后他日，确年日未载',place='后唐朝廷',note='屡言不虚构重复次数和日期。')
E=ev('anzhonghui_says_only_his_post_available','安重诲不悦，称唯枢密使可以替代',9,'重诲愠曰','惟枢密使可代耳。”',[('重诲','不悦答话者')],year=None,when='上述屡次要求时，确年日未载',place='后唐朝廷',note='语气及发言内容是史载，不作正式辞职或提名华任枢密的任命文书。')
E=ev('siyuan_agrees_hua_hypothetical','李嗣源答亦可，安重诲无以对',9,'帝曰','重诲无以对。',[('帝','答亦可者'),('重诲','无以应答者')],year=None,when='上述枢密可代答话之后，确年日未载',place='后唐朝廷',note='对话不等安已免枢密或华已获任枢密；不得建立实际上下级替代结果。')
claim('event',E,'description','旧华传同述安重诲称可替者唯枢密院使，明宗答可，安不能答。',9,'重誨素強愎，對曰：「臣累奏未有闕處，可替者，唯樞密院使而已。」明宗曰：「可。」重誨不能答。','印证同段对话，未推出正式改任。',source=hua,relation='corroborates')
E=ev('huawenqi_fears_stays_home','华温琪闻对话后畏惧，数月不出',9,'温琪闻之','数月不出。',[('温琪','畏惧、数月不出者')],year=None,when='上述对话之后数月，确年日未载',place='所居本句未具',note='惧不作现代诊断；不提前旧传之后华州实际新任。')
claim('event',E,'description','旧华传将华温琪的畏惧写为怕权臣之怒，数月不出。',9,'溫琪聞其事，懼為權臣所怒，幾致成疾，由是數月不出。','补所惧原因与几致成疾语气，不当确定病种或已重病诊断。',source=hua)
E=ev('anzhonghui_accuses_wangjianli','安重诲告王建立与王都交结、有异志',9,'重诲恶','有异志。',[('重诲','告发者'),('建立','被告发成德节度使同平章事'),('王都','告发所涉交结对象')],year=None,when='三月辛亥召见之前的互告背景，确年日未载',place='后唐朝廷、成德',note='有异志是安的奏报，不作为王建立反叛已证；旧传后述王都反不能提前此处认全事实已证。')
E=ev('wangjianli_accuses_anzhonghui_requests_audience','王建立奏称安重诲专权，请入朝面陈',9,'建立亦奏','面言其状，',[('建立','奏请者'),('重诲','被指专权者')],year=None,when='三月辛亥前互告，确年日未载',place='成德至后唐朝廷',note='专权是其告发内容，不等正式判决；请求与实际入朝分阶段。')
E=ev('siyuan_summons_wangjianli','李嗣源召王建立入朝',9,'帝召之','帝召之。',[('帝','召入朝者'),('建立','被召者')],year=None,when='三月辛亥之前，确年日未载',place='成德至后唐朝廷',note='召令不与之后已至同一个动作，未具确日不强辛亥。')
claim('event',E,'description','旧王建立传称安重诲与王建立不协，明宗担心王被陷，征其赴阙。',9,'安重誨素與建立不協，知其事，奏之。明宗慮陷建立，尋征赴闕，','旧所述虑被陷为动机；相邻括注引通鉴不算独立来源印证，王都后反背景不提前标本段已读。',source=wang)
E=ev('wangjianli_reports_anzhang_marriage_power','王建立入朝，告安重诲与张延朗结婚、互相表里弄威福',9,'既至','弄威福。',[('建立','入朝面告者'),('重诲','被告者'),('张延朗','宣徽使判三司、被告者')],year=None,when='入朝后、三月辛亥召见前，确年日未载',place='后唐朝廷',note='结婚及弄威福属于王奏内容，未独核双方具体婚亲，不由告发直接新建姻亲边或判其谋反。')
E=ev('siyuan_proposes_anzhang_outside_wang_replace','李嗣源拟将安重诲、张延朗外调，以王建立代安重诲',9,'三月，辛亥','张延朗亦除外官。”',[('帝','外调换人提议者'),('重诲','拟外调者'),('张延朗','拟外调者'),('建立','拟代枢密者')],when='928年三月辛亥',place='后唐朝廷',note='帝此处谈拟调，后慰抚而实际王相任，不能建王已取代枢密或安张当天已出镇。')
E=ev('anzhonghui_defends_requests_reason','安重诲陈述长期侍奉与天下无事，要求说明外调罪由',9,'重诲曰：“臣披荆棘','臣愿闻其罪！”',[('重诲','陈辩并求罪由者'),('帝','受陈辩者')],when='928年三月辛亥',place='后唐朝廷',note='披荆棘数十年、天下无事是安的话语，不作无任何地方战乱的客观结论；不是安已认罪。')
E=ev('siyuan_leaves_tells_zhuhongzhao','李嗣源不悦而起，将此事告诉朱弘昭',9,'帝不怿','以语宣徽使硃弘昭，',[('帝','不悦离席告事者'),('弘昭','宣徽使、听事者')],when='928年三月辛亥本次争议',place='后唐朝廷',note='硃与朱繁简异体沿已有主体，不新建硃弘昭；本次告诉不等正式处分诏。')
E=ev('zhuhongzhao_advises_keep_anzhonghui','朱弘昭以李嗣源素待安重诲如左右手为由，劝三思',9,'弘昭曰','愿垂三思。”',[('弘昭','劝三思者'),('帝','受劝者')],when='928年三月辛亥本次争议',place='后唐朝廷',note='小忿与左右手为朱的评价和比喻，不证明安所有争议都无责。')
E=ev('siyuan_reassures_anzhonghui','李嗣源随后召安重诲慰抚',9,'帝寻召','慰抚之。',[('帝','召慰者'),('重诲','受慰抚者')],when='928年三月辛亥争议之后寻，具体时刻未载',place='后唐朝廷',note='寻表紧接不扩年；慰抚不是安遭解除职务后正式复官。')
E=ev('wangjianli_requests_return_town','次日王建立辞归镇，李嗣源以此前求分忧的话挽留',9,'明日','今复去何之！”',[('建立','辞归镇者'),('帝','质问挽留者')],when='928年三月辛亥后的明日，原未另具干支',place='后唐朝廷',note='不自行算干支或公历；辞归为请求，不能录已实际返回成德。')
E=ev('zhengjue_requests_retirement','郑珏请求致仕',9,'会门下','郑珏请致仕；',[('珏','门下侍郎刑部尚书同平章事、求致仕者')],when='928年三月己未致仕前，确日未载',place='后唐朝廷',note='请与己未实际致仕分事，官衔概录不造三次新授。')
claim('event',E,'description','新郑珏传记其因病聋及孔循罢枢密后不自安而请求去职，并四次上章。',9,'又病聾，孔循罷樞密使，珏不自安，亟以疾求去職。明宗數留之，珏章四上，','病聋按史载症状不作现代诊断，因不自安为新传动机说明；章四上只补求去频次，不编四日期。',source=zheng)
E=event('siyuan_repeatedly_retains_zhengjue','新郑珏传记明宗多次挽留郑珏',9,'明宗數留之，',[('帝','挽留者'),('珏','被留者')],source=zheng,when='郑珏致仕之前，新本句未另具年日',year=None,place='后唐朝廷',note='补请求至致仕之间多次挽留，未编次数日期，单句缺年不强绑定己未。')
E=ev('zhengjue_retires_left_pushe','郑珏以左仆射致仕',9,'己未','左仆射致仕，',[('珏','左仆射致仕者')],when='928年三月己未',place='后唐朝廷',note='致仕不是死亡或惩罪罢官；郑珏珏/旧玨同人复用。')
claim('event',E,'description','旧明宗纪同日记郑珏左仆射致仕，加开府仪同三司及食邑五百户。',9,'己未，以宰臣鄭玨為開府儀同三司、左僕射致仕，加食邑五百戶。','玨与主珏字形并存，旧加荣衔食邑为本次待遇，非未来实际收税户数。',source=mar,relation='corroborates')
claim('event',E,'description','新明宗纪三月己未记郑珏罢。',9,'己未，鄭珏罷。','罢相与主左仆射致仕叙法相合，不推全官爵削尽。',source=new,relation='corroborates')
claim('event',E,'description','新郑珏传补左仆射致仕时赐郑州庄一处。',9,'乃拜左僕射致仕，賜鄭州莊一區。','补退居庄赐，未给地理坐标、面积或庄园收入；后卒不提前录。',source=zheng)
E=ev('wangjianli_right_pushe_chancellor_finance','王建立任右仆射兼中书侍郎、同平章事、判三司',9,'癸亥',None,[('建立','右仆射中书侍郎同平章事判三司获任者')],when='928年三月癸亥',place='后唐朝廷',note='实际任相理财，不是前面拟替安的枢密使已获任；判三司是所判职责，不强等新设置三司使官名。')
claim('event',E,'description','旧明宗纪同日补王建立充集贤殿大学士。',9,'癸亥，以前鎮州節度使王建立為右僕射兼中書侍郎、平章事、集賢殿大學士、判三司。','同一任命职衔补充，镇州成德为治州军镇名称，不造另人。',source=mar)
claim('event',E,'description','旧王建立传将判三司具写为判盐铁户部度支，并记充集贤殿大学士。',9,'拜右僕射兼中書侍郎、平章事、判鹽鐵戶部度支，充集賢殿大學士。','印证所判事务，传夹注引通鉴不算独立三次确证；未取其后天成四年出青州或晚卒提前。',source=wang,relation='corroborates')
claim('event',E,'description','新明宗纪三月癸亥同记王建立尚书右仆射、同中书门下平章事。',9,'癸亥，成德軍節度使王建立為尚書右僕射、同中書門下平章事。','新简官衔是同事概录，不能因省中书侍郎判三司便断定不存在。',source=new,relation='corroborates')
E=ev('meng_dong_repeated_salt_dispute','孟知祥屡与董璋争盐利',10,'孟知祥','争盐利，',[('孟知祥','盐利争议者'),('董璋','盐利争议者')],year=None,when='汉州设三场之前的反复盐利争议，确年日未载',place='西川与东川',note='屡是持续背景，不编次数和单次冲突日期，也不造双方永久敌对边。')
E=ev('dongzhang_attracts_east_salt_merchants','董璋诱使商旅将东川盐贩入西川',10,'璋诱','东川盐入西川，',[('董璋','引导贩盐商旅者')],year=None,when='汉州设三场之前，确年日未载',place='东川至西川',note='诱为主书所述引导，不推贩盐违法或存在具体货运线路坐标。')
E=ev('mengzhixiang_hanzhou_three_tax_posts','孟知祥在汉州设三场，对商旅贩盐重征',10,'知祥患之','三场重征之，',[('孟知祥','汉州设场重征者')],when='928年三月本段，确日未载',place='汉州',note='三场未具名，不能编名称或边界；患之按主动机，不给税率百分比。')
E=ev('hanzhou_tax_annual_revenue','汉州三场重征后，岁得钱七万缗',10,'岁得','岁得钱七万缗，',[],year=None,when='设三场后的年度收入记载，具体统计年未载',place='汉州三场',note='岁得是年收入叙述，不直接说928全年实收七万；未换算现代货币或扩大为西川总收入。')
E=ev('merchants_stop_east_salt_travel','重征后商旅不再前往东川',10,'商旅不复',None,[],year=None,when='汉州三场重征后的结果，确年日未载',place='汉州、东川与西川盐贸易',note='不复之为本段商旅去向变化，未推全国贸易终止或永久禁盐法律。')
review='连续9—10段逐句校核。孔循亲信、帝拟安女婚、孔劝安辞、匿名提醒、孔结王德妃求嫁女、王请从厚和帝许均出镇前追叙，确年null；女未具名、获准非完婚，新孔传合妻与出镇概述不提前十一月实际婚礼。新王德妃限定李嗣源妃区别吴王氏。乙未孔出忠武同平章兼东都，旧许州、新罢枢密同事记法，非全官爵削。华入朝请留及左骁月赐为岁馀之前追叙null，不倒算年；择重镇、安无阙、帝屡言、安愠说枢密可代、帝答、华怕数月不出均null，不当枢密已换或现代诊断、后华州任命不提前。安王互告与入朝前未日null，异志、专权、安张结婚威福为告发不证反叛或造姻亲；旧王传虑陷补动机、夹通鉴注不算独立证，王都后反语境不提前读。三月辛亥帝拟调安张王代、安陈辩、帝不悦告朱、朱谏、帝慰抚分阶段；无实换枢密外镇，天下无事仅安话。明日王辞归为请非已走、不算干支。郑请、旧新致仕己未、新留与四章、赐郑庄分事，留确年未明null；旧玨主珏同人，食邑非实收户、后卒不提前。癸亥王相财实任、新简职与旧盐铁户部度支集贤補，未称已新设三司使。两川屡争、董诱贩为前背景null；孟汉州三场重征当前条928未日，三场名税率不编；岁得七万和商旅止东川是制度后概述null，非928固定全年度实收全国总收入。简体展示、原字摘录，纸本异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(9,11)],next_paragraph='zztj-v276-y0928-p011',next_volume=276,next_year=928,supplements=supplements,excluded_non_body=[],coverage='卷276连续928年第9—10段、原文件41—42行；婚事争议、孔出镇、华留阙、安王互告和三月朝议、郑致仕王入相、两川盐利。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(9,11)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
