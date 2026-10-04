# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 5–8."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,78))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'2ec8cf50','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-279-934-february',YEAR/'part-01/sources/library/tongjian-279-934-february','570df7a6','司马光等'),('jiuwudaishi-045-934-transfers',YEAR/'part-01/sources/library/jiuwudaishi-045-934-transfers','570df7a6','薛居正等'),('xinwudaishi-064-meng-emperor',YEAR.parent.parent/'vol-278/year-0934/part-02/sources/library/xinwudaishi-064-meng-emperor','a2ffb86d','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-february','tongjian-279-934-army']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p005-p008',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key.startswith('songshi-262-'):record=dict(record,section_title='卷262·赵上交传',citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(5, 9):
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
    if source.startswith('songshi-262-'):record=dict(record,citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷279·清泰元年（934；二、三月闵帝应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'潞王':'李从珂','王':'李从珂','洋王':'李从璋','从璋':'李从璋','硃':'朱弘昭','朱':'朱弘昭','冯':'冯赟','金':'相里金','晖':'尹晖','蜀主':'孟知祥','帝':'李从厚'}
NEW_ALIASES={'马胤孙':['馬胤孫','马裔孙','馬裔孫'],'赧诩':['赧詡'],'朱廷乂':['硃廷乂'],'相里金':['相裏金'],'薛文遇':[],'尹晖':['尹暉'],'楚匡祚':[],'孙汉韶':['孫漢韶']}

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

def event(code, title, n, quote, actors, when=None, note='', year=934, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='934年三月条下；确日未独载' if n==8 else '934年二月条下；确日未独载'
    key = 'event_zztj_279_0934_' + code
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
        edge = 'participation_zztj_279_0934_' + code + '_' + pk
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
    corrections={}
    import uuid
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
    people_ids={str(uuid.uuid5(namespace,x['key'])):x['key'] for x in registry.values()}
    for revision in sorted((ROOT/'content/revisions').glob('*/relations.json')):
        if not (revision.parent/'publication.json').exists():continue
        for revision_row in json.loads(revision.read_text()).get('relations',[]):corrections[revision_row['key']]=revision_row['after']
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if x['key'] in corrections:
                c=corrections[x['key']];x=dict(x,person_a_key=people_ids[c['person_a']],person_b_key=people_ids[c['person_b']],relation_type=c['relation_type'])
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_279_0934_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




# Consecutive paragraphs 5–8. Allegations and orders do not imply completed acts.
ev('congzhang_ordered_fengxiang','朝廷命李从璋权知凤翔',5,'潞王既与','权知凤翔。',[('从璋','洋王、获令权知凤翔者'),('潞王','已与朝廷猜阻的原凤翔节度使')],place='凤翔',note='接前段调潞王河东，李从璋为接管安排；未当已经进入凤翔接任。')
ev('congzhang_chonghui_retrospective','追叙李从璋此前代安重诲镇河中，并欲杀之',5,'从璋性','欲杀之；',[('从璋','此前代镇、欲杀者'),('安重诲','被取代并受威胁者')],year=None,when='前代安重诲镇河中的追叙；此句未独载年月',place='河中',note='性粗率乐祸为史家评语，欲杀与既有安重诲遇害事件不当同一完成动作。')
ev('congke_rejects_replacement_and_consults','李从珂厌恶李从璋来代，因兵弱粮少向将佐问计',5,'潞王闻其来，','谋于将佐，',[('潞王','疑惧问计者'),('从璋','令其厌恶的拟接管者')],place='凤翔',note='闻其来是得知接管安排，与后段洋王到关西即还区分；未名将佐不猜。')
ev('fengxiang_retinue_urges_refusal','凤翔将佐劝李从珂不受离镇调令',5,'皆曰：','不可受也。”',[('潞王','被劝拒绝调令者'),('朱','被将佐称掌政者'),('冯','被将佐称掌政者')],note='离镇必无全理是将佐论辞，不当已证明朝廷必将杀潞王。未名将佐不补名单。')
ev('ma_yinsun_advises_obedience','马胤孙劝李从珂临丧赴镇、遵从君命',5,'王问观察判官','众哂之。',[('潞王','问经京路线者'),('马胤孙','观察判官、劝遵君命者')],note='主滴河籍字疑，新传字庆先、棣州商河核身份，滴河不自动更正或换坐标。众哂为反应，不作马医学诊断。')
ev('congke_sends_manifesto','李从珂移檄邻道，声称将入朝清君侧并求援',5,'王乃移檄','愿乞灵邻籓以济之。”',[('潞王','发檄求援者'),('朱','被檄指控者'),('冯','被檄指控者')],place='凤翔、邻道',note='杀长立少、专制等是檄文指控，不把每项当独立已核事实；将入朝是宣称与意图，未当已到京师。')
ev('congke_seeks_wang_sitong_alliance','李从珂欲争取处在东出道上的王思同',5,'潞王以西都留守','尤欲与之相结，',[('潞王','谋争取者'),('王思同','西都留守、被争取对象')],place='长安',note='欲相结不是已经结盟，不建立盟友边。')
ev('congke_sends_nanyi_zhu_envoys','李从珂遣赧诩、朱廷乂等相继赴长安游说王思同',5,'遣推官','不从则令就图之。',[('潞王','遣使并授意者'),('赧诩','推官、往长安使者'),('朱廷乂','押牙、往长安使者'),('王思同','被游说与诱威对象')],place='长安',note='主赧诩姓名字形暂未独立核定，原字及待考保；饵美妓、不从就图是授意，不当王已受诱或已被暗杀。')
ev('wang_sitong_refuses_rebellion','王思同向将吏表示不愿与凤翔同反',5,'思同谓将吏曰：','流千古之丑迹乎！”',[('王思同','拒绝同反的发言者')],place='长安',note='借使事成事败是王的假设论证，不当共同叛乱已经发生。')
ev('wang_sitong_detains_envoys','王思同拘执赧诩等并向朝廷报告',5,'遂执诩等，','以状闻。',[('王思同','拘使及报告者'),('赧诩','明确被拘使者')],place='长安',note='等未逐人点名，朱廷乂不凭前名单直接填已被拘；此时不提前记王被杀。')
ev('congke_envoys_mixed_response','李从珂使者多被邻道拘执，其他邻镇持两端',5,'时潞王使者','依阿操两端，',[('潞王','所遣使者及求援受阻的主事者')],note='概述未名邻镇不逐一补参与者，操两端不是已投朝廷或潞王。')
ev('xiangli_jin_supports_congke','陇州防御使相里金倾心支持李从珂',5,'惟陇州防御使','倾心附之，',[('相里金','陇州防御使、支持者'),('潞王','受支持者')],place='陇州、凤翔',note='本段明确附之，可录此时政治支持事件，不派生永久血亲或结义。')
ev('xiangli_sends_xue_wenyu','相里金遣薛文遇往来凤翔计事',5,'惟陇州防御使','往来计事。',[('相里金','遣判官者'),('薛文遇','判官、往来计事者'),('潞王','计事对象')],place='陇州、凤翔',note='薛为相里判官，未将后来枢密直学士提前成本时官职。')
claim('person',people['相里金'],'description','相里金为并州人。',5,'金，并州人也。','籍贯保史称，不转换现代地理坐标。')
ev('court_discusses_fengxiang_campaign','朝廷商议讨伐凤翔',5,'朝廷议','讨凤翔。',[],note='议讨与任帅、实际攻城分；未给会议参加人名单，不编。')
ev('kang_proposes_campaign_command','康义诚因不欲出外而请求王思同、侯益领征军',5,'康义诚不欲出外，','行营马步军都虞侯。',[('康义诚','担忧失军权、提出人选者'),('王思同','拟统帅人选'),('侯益','羽林都指挥使、拟都虞侯人选')],note='请以为人选提议，侯益下句拒行，不记已出征；恐失军权是史述动机。')
ev('hou_yi_declines_campaign','侯益认为军情将变，称疾不出征',5,'益知军情','辞疾不行。',[('侯益','称疾不行者')],note='军情将变是其判断；称疾不确诊疾病，不把次后兵变已发生于此。')
ev('hou_yi_posted_shangzhou','执政因侯益拒行，将其出为商州刺史',5,'执政怒之，','商州刺史。',[('侯益','被出任商州刺史者')],place='商州',note='执政未在本句逐人指名，不把前文朱冯机械均列为签发者。')
q=span(5,'辛卯，','皆为偏裨。')
for code,name,title,role in [('wang','王思同','王思同任西面行营马步军都部署','行营统帅'),('yao','药彦稠','药彦稠任王思同副部署','前静难节度使、副部署'),('chang','苌从简','苌从简任马步都虞侯','前绛州刺史、马步都虞侯'),('yin','尹晖','尹晖列征凤翔偏裨','严卫步军左厢指挥使、偏裨'),('yang','杨思权','杨思权列征凤翔偏裨','羽林指挥使、偏裨')]:
 event('campaign_office_'+code,'二月辛卯'+title,5,q,[(name,role)],when='934年二月辛卯',note='原职为身份，今征军职另录，不当当日已攻城；主刺吏/都虞候为底字异写，展示沿史通行刺史/都虞侯。')
claim('person',people['尹晖'],'description','尹晖为魏州人。',5,'晖，魏州人也。','沿主全名，繁体尹暉为检索别名；不编生年。')
ev('wang_chuhui_shumishi','孟知祥任中门使王处回为枢密使',6,'蜀主以',None,[('蜀主','任命者'),('王处回','原中门使、新枢密使')],place='蜀',note='主未独日，前新蜀世家在即位后概述任命，无二月确日不补。')
ev('wang_sitong_chancellor_campaign','二月丁酉王思同加同平章事、知凤翔行府',7,'丁酉，','知凤翔行府；',[('王思同','获加衔、知行府者')],when='934年二月丁酉',place='凤翔行府（任职名）',note='凤翔仍未陷，知行府为征讨行府职位，不当已有入城治镇。')
ev('anyanwei_campaign_supervisor','二月丁酉安彦威任西面行营都监',7,'以护国节度使','西面行营都监。',[('安彦威','原护国节度使、新行营都监')],when='934年二月丁酉',note='护国原镇保，不另当新授；旧西面兵马都监同层补证。')
ev('army_compares_wang_congke','史叙王思同御军无法，求富贵的将士倾向李从珂',7,'思同虽有','心皆向之。',[('王思同','被史书评述统御者'),('潞王','被将士倾向、老于行阵者')],year=None,when='征凤翔期间的概述；比较与倾向具体起讫未载',note='忠义、御军与徼幸是史书评述，不编具名倾向将士名单，不当已经全部投降。')
ev('chongji_ordered_detained','朝廷诏遣楚匡祚拘李重吉，幽禁宋州',7,'诏遣殿直','幽于宋州。',[('楚匡祚','殿直、奉诏拘执者'),('李重吉','亳州团练使、被拘幽者')],place='宋州',note='主记诏遣及拘幽，旧庚子楚奏已监送系军院可补执行；不提前录后段处决及取财。')
ev('congzhang_returns_from_guanxi','李从璋行至关西，闻凤翔拒命后返回',7,'洋王从璋',None,[('从璋','听拒命而还者')],place='关西',note='到关西并返回不同已到凤翔履任；关西为史称范围，不给精确点。')
ev('five_governors_request_joint_campaign','三月安彦威等五节度使奏请合兵讨凤翔',8,'三月，','奏合兵讨凤翔。',[('安彦威','护国节度使、合兵奏者'),('张虔钊','山南西道节度使、合兵奏者'),('孙汉韶','武定节度使、合兵奏者'),('张从宾','彰义节度使、合兵奏者'),('康福','静难节度使、合兵奏者')],place='凤翔（讨伐目标）',note='奏合兵与下一段实际攻城分开；不根据后文添作此时已降蜀。')
relationship('李存进','孙汉韶','父亲',8,'汉韶，李存进之子也。','李存进→孙汉韶为父亲；新义儿传上承李存进、记子汉韶明宗时复本姓，姓氏不同不否定父子。')
old='jiuwudaishi-045-934-transfers';march='jiuwudaishi-045-934-march-armies';ma='xinwudaishi-055-ma-yinsun';oldma='jiuwudaishi-127-ma-yisun';jin='jiuwudaishi-090-xiangli-jin';son='xinwudaishi-036-sun-hanshao';shu='xinwudaishi-064-meng-emperor'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='同人同职及行动核对；原字保留，纸本待校。'):
 claim('event','event_zztj_279_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('congzhang_ordered_fengxiang',old,'以前河中節度使、洋王','權知鳳翔軍軍府事。','旧闵帝纪二月己卯宣授条记洋王李从璋权知凤翔军府事。',5,relation='adds',note='旧明确与前段三镇宣授同己卯，主本段未独日；权知不是已经接管成功。')
supp('ma_yinsun_advises_obedience',ma,'潞王將舉兵反，','然從珂心獨重之。','新马胤孙传同记被问经京路线、劝遵君命并临丧赴镇；众笑而从珂心重之。',5,relation='adds',note='新明确劝臣子之忠及从珂心重，主众哂；新先述与韩昭胤等谋议已定，是补书叙述，不把具名将吏自动填为主泛称全体。')
claim('person',people['马胤孙'],'description','马胤孙字庆先，棣州商河人。',5,'馬胤孫字慶先，棣州商河人也。','字籍新明载；主滴河字可疑，保原字待校，展示籍沿独立新传，不改源TXT。',source=ma,relation='adds')
claim('person',people['马胤孙'],'aliases','旧马裔孙与主、新马胤孙为同一人，字庆先、棣州商河籍相合。',5,'馬裔孫，字慶先，棣州商河人。','两传字籍及废帝翰林宰相履历相合保异名；不靠繁简自动推避讳原因，不提前录后来任相。',source=oldma,relation='adds')
supp('xiangli_sends_xue_wenyu',jin,'應順元年，為隴州防禦使，','末帝深德之。','旧相里金传记应顺元年任陇州防御使，独遣薛文遇往来凤翔计事。',5)
claim('person',people['相里金'],'description','相里金字奉金，并州人。',5,'相裏金，字奉金，并州人也。','旧本传字籍补，里/裏字形作别名，不新建相裏金。',source=jin,relation='adds')
supp('campaign_office_wang',old,'丁酉，王思同','充西面行營都部署；','旧闵帝纪在丁酉一并记王思同加同平章事、充西面行营都部署；主前辛卯任帅、今丁酉加衔分期保。',5,relation='conflicts',note='旧将任帅与加衔同载丁酉，主辛卯任帅丁酉加衔，日期层次异说不压成一条。')
supp('campaign_office_yao',old,'以前邠州節度使','為副部署。','旧闵帝纪丁酉条下记药彦稠为副部署，主辛卯任副。',5,relation='conflicts')
supp('wang_chuhui_shumishi',shu,'中門使王處回','為樞密使，','新蜀世家在孟知祥称帝后同记中门使王处回为枢密使，未独日。',6)
supp('wang_sitong_chancellor_campaign',old,'丁酉，王思同','充西面行營都部署；','旧同丁酉记王思同加同平章事并充西面都部署。',7,relation='adds')
supp('anyanwei_campaign_supervisor',old,'以河中節度使安彥威','為西面兵馬都監，','旧丁酉条同记安彦威以河中节度任西面兵马都监；主护国对应河中军治。',7)
supp('chongji_ordered_detained',old,'庚子，殿直楚匡祚','係於軍院。','旧闵帝纪二月庚子楚匡祚奏已经监取李重吉至宋州，系于军院。',7,relation='adds',note='庚子是奏执行之日，不硬当拘捕起日；后句杀重吉是后事，此次不提前录。')
supp('five_governors_request_joint_campaign',march,'興元節度使張虔釗奏，','會合討鳳翔。','旧闵帝纪三月甲辰段下记兴元张虔钊奏会合讨凤翔。',8,relation='adds',note='主五人合兵奏概述，新旧分日分军，旧此句只明张；不将五人全定甲辰同奏。')
supp('five_governors_request_joint_campaign',march,'丁未，洋州孫漢韶奏，','同議進軍。','旧闵帝纪三月丁未孙汉韶奏，已到兴元与张虔钊同议进军。',8,relation='adds',note='孙到兴元与合议有独日期，不等已经攻陷凤翔；洋州对应武定军，不另造孙新任官。')
claim('person',people['孙汉韶'],'description','孙汉韶在明宗时恢复本姓，为洋州节度使。',8,'子漢韶，明宗時復本姓，為洋州節度使。','新义儿传上承李存进（前段明确存进战殁），子汉韶对应主父子。复姓只明明宗时不编确年；现用孙汉韶，不因父李姓另造李汉韶。',source=son,relation='adds')
reviews={5:'洋王权知与既赴任分，前代河中欲杀为追叙未定年。潞王将佐劝拒、马劝从、檄中指控和入朝意图均保发言层，不当全部实证。赧诩暂无可靠补证保疑字，朱廷乂硃写沿简；欲结王不是已经结盟，诱威图杀不当已实现。王拘诩等不猜朱亦已被拘。相里金附与薛计事明；康提议、侯拒行出商、辛卯五将任命分，旧丁酉任帅副与主辛卯差异保。马旧裔新胤以字籍履历同人，主滴河不擅更正。',6:'蜀中门使王处回授枢密使，旧职保，不当同日新授中门。新蜀世家同职补无独日不编。',7:'丁酉王加同平章知行府、安任都监分；御军及将士倾向为概述未定年，不当已降。楚拘重吉及宋幽与后段杀害分；旧庚子楚奏说明已监送，不误奏日为捕日。洋王到关西即返，不当凤翔已交接。',8:'三月五节度合兵奏与下一段攻城分；旧甲辰张、丁未孙到兴元与合议分日期补证不统一五人同日。孙汉韶此前字面未见主体，新义儿明确李存进子明宗时复本姓，建同一人父边。孙此前官历仅身份补不新增回溯任命日期；降蜀及死亡待后续主线。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5,9):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(5,9)],next_paragraph='zztj-v279-y0934-p009',next_volume=279,next_year=934,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷279连续934年第5—8正文段，原10—13行；凤翔拒命、求援与讨伐任帅及三月合兵奏。第9段实际攻城仍待录，本年89正文段尚未全部处理。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(5,9)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
