# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 1–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 58))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 if directory.name=='xinwudaishi-051-ancongjin':continue
 specs.append((directory.name,directory,'871075e5','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))

specs.append(('xinwudaishi-051-ancongjin',YEAR.parent.parent/'vol-277/year-0930/part-03/sources/library/xinwudaishi-051-ancongjin','5ae2febe','欧阳修'))

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-january-april']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0933-p001-p010',
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
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(1, 11):
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
        citation = f'卷278·长兴三年（933）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0933_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','从荣':'李从荣','延钧':'王延钧','闽主':'王延钧','璘':'王延钧','继鹏':'王继鹏','知祥':'孟知祥','李敏':'李敏（闽臣）','彝超':'李彝超','从进':'安从进','赵季良':'赵季良','张知业':'张业'}
NEW_ALIASES={'刘昫':['劉昫','刘煦','劉煦'],'李敏（闽臣）':['闽臣李敏'],'吴勖':['吳勖'],'裴杰':['裴傑'],'程侃':[],'拓跋承谦':['拓跋承謙','拓拔承谦','拓拔承謙'],'孙超':['孫超'],'杨通信':['楊通信'],'李彝超':['李彜超'],'安重益':[]}

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

def event(code, title, n, quote, actors, when=None, note='', year=933, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='933年正月本段；确日未独载' if n<=2 else '933年二月本段；确日未独载' if n<=7 else '933年三月本段；确日未独载'
    key = 'event_zztj_278_0933_' + code
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
        edge = 'participation_zztj_278_0933_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_278_0933_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive ten body paragraphs in the next volume of the same year.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
jan='jiuwudaishi-044-933-january';feb='jiuwudaishi-044-933-february';mar='jiuwudaishi-044-933-march';apr='jiuwudaishi-044-933-april';oldmin='jiuwudaishi-134-min-emperor';newmin='xinwudaishi-068-min-emperor';renfu='jiuwudaishi-132-renfu';yichao='jiuwudaishi-132-yichao';warning='jiuwudaishi-132-warning';oldliang='jiuwudaishi-138-liangzhou';newliang='xinwudaishi-074-liangzhou';congjin='xinwudaishi-051-ancongjin'
E=ev('congrong_shangshuling','正月戊子李从荣加守尚书令、兼侍中',1,'春，正月，戊子，','兼侍中。',[('上','加官者'),('从荣','秦王、受加官者')],when='933年正月戊子',place='后唐朝廷')
claim('event',E,'description','旧明宗纪同戊子记秦王从荣加守尚书令、兼侍中，仍河南尹、判六军诸卫事。',1,'戊子，秦王從榮加守尚書令、兼侍中，依前河南尹，判六軍諸衛事。','依前的原任不是本次重授，不复建此前河南尹或判六军任命。',source=jan,relation='corroborates')
E=ev('liuxu_chancellor','正月庚寅刘昫任中书侍郎、同平章事',1,'庚寅，',None,[('上','任宰相者'),('刘昫','端明殿学士、受相职者')],when='933年正月庚寅',place='后唐朝廷',note='归义为主籍称，不作官号；旧煦与主昫同日同端明殿学士任相匹配，不因字形造两人。')
claim('event',E,'description','旧明宗纪同庚寅记端明殿学士、兵部侍郎刘煦为中书侍郎、平章事。',1,'庚寅，以端明殿學士、尚書兵部侍郎劉煦為中書侍郎、平章事。','煦不是昫的繁简对应，按同职同日同事识别为同一主体，底本异字保留，纸本待核。',source=jan,relation='corroborates')
ev('min_dragon_report_palace','闽有人称真封宅见龙，王延钧改宅名为龙跃宫',2,'闽人有言','曰龙跃宫。',[('闽主','依据龙见传言改宅名者')],place='闽真封宅、龙跃宫',note='有言为传闻，不把见龙写成已证自然事实；未名报告者不虚造。')
E=ev('min_emperor_accession','王延钧赴宝皇宫受册，备仪卫入府称帝',2,'遂诣宝皇宫受册，','即皇帝位，',[('闽主','宝皇宫受册、入府称帝者')],place='闽宝皇宫、王府',note='宗教受册为史述仪式，不把宝皇建成人类父亲或确有神授；称帝与此前闽王任分。')
claim('event',E,'description','新闽世家同记王鏻称帝、在宝皇受册，以真封宅黄龙传言改元。',2,'鏻乃即皇帝位，受冊於寶皇，以黃龍見真封宅，改元為龍啟，國號閩。','新书鏻对应王延钧，按同一主体识别，黄龙为新书所述不写独立自然确认。新未独933正月日，不另套陈守元之前预言六十年已兑现。',source=newmin,relation='corroborates')
E=ev('min_name_era_amnesty','王延钧称国号大闽，大赦，改元龙启',2,'国号大闽，','改元龙启；',[('闽主','宣国号、赦令及改元者')],place='闽',note='主大闽、新闽字称各留；改元不等朝廷承认皇帝称号。')
claim('event',E,'description','旧闽传记延钧自称帝、国号大闽、改元龙启。',2,'未幾，自稱帝，國號大閩，改元龍啟，然猶稱藩於朝廷。','旧先记932乞封不报后未几，新另一朝贡叙层不在本段重造请求；旧清泰元年遇弒与后主续935相异不提前本年死，待后段校核。',source=oldmin,relation='corroborates')
E=ev('min_yanjun_name_lin','王延钧在本段更名璘',2,'更名璘。','更名璘。',[('闽主','改名者')],place='闽',note='主璘、新鏻为字形异说，不凭改名造第二君主；新此前已回称鏻，不拿其写法推精确改名时间。')
claim('person',people['王延钧'],'aliases','王延钧在通鉴本段更名王璘；新史以王鏻称此君。',2,'更名璘。','已有王延钧稳定key沿用，王璘、王鏻作可检索别名；不与其他璘姓王人物混同。')
claim('person',people['王延钧'],'aliases','新五代史以王鏻称王延钧，与主王璘字形异说并列。',2,'鏻乃即皇帝位，受冊於寶皇，','同一君主同一宝皇受册事件识别，主璘、新鏻字形保留，不以新回称推更名确日。',source=newmin,relation='adds')
E=ev('min_ancestor_five_temples','王延钧追尊父祖，建立五庙',2,'追尊父祖，','立五庙。',[('闽主','追尊祖先、建庙者')],place='闽',note='主未逐列祖名爵，不补五代未名先人；追尊是身后礼，非祖父本年即位。')
claim('event',E,'description','新闽世家记追谥王审知昭武孝皇帝、庙号太祖，立五庙。',2,'追謚審知為昭武孝皇帝，廟號太祖，立五廟，','具体父名谥号据新补；审知已925卒，不建933复生或他亲自称帝事件。',source=newmin,relation='adds')
ev('min_limin_left_chancellor','王延钧任李敏为左仆射、门下侍郎、同平章事',2,'以其僚属李敏','为左仆射、门下侍郎，',[('闽主','任僚属相职者'),('李敏','闽僚属、获左仆射及门下侍郎者')],place='闽',note='同平章事是原并句同时适用李敏与继鹏；闽臣李敏与唐昭宗李杰旧名李敏不同，使用李敏（闽臣）限定，不用旧帝UUID。')
claim('event',B['events'][-1]['key'],'description','李敏与王继鹏两人均同平章事。',2,'并同平章事；','并字承前两人，不只给继鹏，也不意味着两人共享一个人物实体。')
ev('min_jipeng_right_chancellor','王延钧任子王继鹏为右仆射、中书侍郎、同平章事',2,'其子节度使继鹏','并同平章事；',[('闽主','任子相职者'),('继鹏','节度使、获右仆射及中书侍郎者')],place='闽',note='节度使原职，主未本句列军镇，不猜新授某军；尚未本年登帝。')
relationship('闽主','继鹏','父亲',2,'其子节度使继鹏','王延钧→王继鹏父亲，按已应用关系方向修正复用既有key；若无则按明确其子建立。')
ev('min_wuxu_secretariat','王延钧以亲吏吴勖为枢密使',2,'以亲吏吴勖','为枢密使。',[('闽主','任亲吏者'),('吴勖','亲吏、获枢密使者')],place='闽',note='吴勖不能因吏字猜某宦官或父子关系，姓吴非吴国籍证据。')
ev('tang_envoys_haimen','后唐册礼使裴杰、程侃抵达海门',2,'唐册礼使裴杰','适至海门，',[('裴杰','后唐册礼使、抵海门者'),('程侃','后唐册礼使、同抵海门者')],place='海门',note='适至为抵达，不据此猜此次唐正式册封闽帝；使者出发日期未独载。')
ev('min_retains_peijie','闽主任裴杰为如京使',2,'闽主以杰','为如京使；',[('闽主','任留唐来使者'),('裴杰','受如京使者')],place='闽',note='是否自愿原未明，不猜降闽心理；如京使是新职不是又出发赴京已成。')
ev('min_refuses_cheng_return','程侃坚请北还，闽主不许',2,'侃固求北还，','不许。',[('程侃','坚持请北还者'),('闽主','不许其还者')],place='闽',note='请求与拒绝皆明，不把请还当已回到洛阳，也不猜终身被囚。')
ev('min_neighbors_cautious','史述闽主因国小地僻谨事四邻，境内较安',2,'闽主自以国小地僻，',None,[('闽主','被述谨事四邻者')],year=None,when='称帝前后持续政策概述；起止年未独载',place='闽',note='常为概述不强定始于正月；四邻未具体列，不造永久四国盟友关系。差安不等从此再无内乱。')
ev('meng_local_five_appointments','二月戊申孟知祥以墨制任赵季良等五镇节度使',3,'二月，戊申，',None,[('知祥','地方以墨制除补者'),('赵季良','五镇受任者之一')],when='933年二月戊申',place='两川五镇',note='此为孟地方任命，与932请表及三月乙酉朝廷制授分；主本句只赵季良等，具体五军留后身份可回此前932和本批后文。')
E=ev('liangzhou_petition_sunchao','凉州大将拓跋承谦及耆老上表，请授孙超节度使',4,'凉州大将', '为节度使。',[('拓跋承谦','代表凉州上表者'),('孙超','权知留后、被请求授节度者')],place='凉州、后唐朝廷',note='上表求不等本主句已批准；未知耆老姓名可由新旧补，未据姓拓跋与夏州仁福强连亲。')
claim('event',E,'description','旧回鹘传记孙超遣拓拔承谦及僧道士耆老杨通信等至京师。',4,'唐長興四年，涼州留後孫超遣大將拓拔承謙及僧道士耆老楊通信等至京師，','拓拔与主拓跋同职同使命识同人，杨通信补为使团耆老，未强定主问答即杨说。',source=oldliang,relation='adds')
a=person('杨通信',4,'凉州赴京请命使团耆老', '及僧道士耆老楊通信等至京師，',source=oldliang)
edge='participation_zztj_278_0933_liangzhou_petition_yangtongxin';B['person_events'].append(dict(key=edge,person_key=a,event_key=E,role='使团耆老',status='draft'));claim('person_event',edge,'role','杨通信为凉州赴京使团中的耆老。',4,'及僧道士耆老楊通信等至京師，','同团不推其为主对话的发言者或孙超亲属。',source=oldliang,relation='adds')
ev('liangzhou_envoy_account','李嗣源问孙超身份，使者称孙超及凉州郓人为旧戍卒后代',4,'上问使者：',None,[('上','问留后出身者'),('孙超','使者解释出身的对象')],place='后唐朝廷',note='二千五百是使者所言唐旧戍人数，不当933现有军队数量；郓人先后死亡为回顾，不在933复录全军阵亡。主未指明发言姓名，不能自行指为承谦。')
E=event('sunchao_approved','旧新五代史补记李嗣源授孙超凉州节度使',4,'明宗拜孫超節度使。',[('上','批准授职者'),('孙超','获节度使者')],source=oldliang,when='旧新史长兴四年（933）请命后；授职确月日未独载',place='凉州',note='补书批准动作独立于主请表，主只求不得当已授；新与旧非完全独立见证。')
claim('event',E,'description','新四夷附录同记明宗拜孙超节度使。',4,'明宗乃拜孫超節度使。','新还将问答归承谦，并以唐亡后阻隔叙述，主黄巢时始隔与新层次各留，不篡主原文。',source=newliang,relation='corroborates')
claim('event',used[4][1],'description','新四夷附录将向明宗解释世家的问答归于拓拔承谦。',4,'明宗問孫超等世家，承謙曰：','新明确说话人可补主匿名使者，但只作为新书记载归属，未声称主直接列名；张义朝与主义潮字异仍仅回顾例，不造933其募兵新事。',source=newliang,relation='adds')
ev('xifan_wuan_wuping_zhongshuling','二月乙卯马希范任武安、武平节度使，兼中书令',5,'乙卯，',None,[('上','授任者'),('马希范','获武安武平及中书令者')],when='933年二月乙卯',place='武安、武平',note='与932武安兼侍中是后续加任，不当同一授职。旧二月另记静江副使马希范转鄂州与主不合，未用该任替换主。')
E=ev('renfu_dies','二月戊午定难节度使李仁福去世',6,'戊午，','李仁福卒；',[('李仁福','定难节度使、去世者')],when='通鉴933年二月戊午',place='定难军',note='死亡据主具体日，旧传长兴四年三月卒另列异说，不改主或猜公历日。')
claim('event',E,'description','旧仁福传称长兴四年三月李仁福卒于镇。',6,'長興四年三月，卒於鎮。','主二月戊午、旧传三月死亡月差异并列；旧明宗纪三月安从进奏死是奏闻而非必实际死日，分别记录层次。',source=renfu,relation='adds')
E=ev('yichao_local_succession','二月庚申定难军立李彝超为留后',6,'庚申，',None,[('李彝超','李仁福之子、军中拥立留后者')],when='933年二月庚申',place='定难军',note='军中拥立与后唐移任延州、最后追认不同阶段，不提前朝廷正式定难节度授任。')
claim('event',E,'description','旧彝超传记仁福死后三军立彝超为帅。',6,'仁福卒，三軍立為帥，','旧无此句日，以主庚申为纪时；旧下矫父奏为另一次伪奏不得当真父活着，当前仅取立帅补。',source=yichao,relation='corroborates')
relationship('李仁福','彝超','父亲',6,'军中立其子彝超为留后。','李仁福→李彝超父亲，明确其子；未依据拓跋族同姓推具体先祖世次。')
claim('person',people['李彝超'],'description','旧传称李彝超为李仁福次子，曾任左都押衙、防遏使。',6,'彜超，仁福之次子也。歷本州左都押衙、防遏使，','彜/彝字形及同父同任识别；次子不自动推未名兄长姓名或生年，前职回顾不定933新授。',source=yichao,relation='adds')
claim('event',E,'description','旧明宗纪三月记安从进奏李仁福死、彝超自称留后。',6,'延州節度使安從進奏，夏州節度使李仁福卒，其子彝超自稱留後。','奏报层次和军中拥立称法并列，不把三月奏日当二月庚申立日；自称不等父子血缘假的。',source=mar,relation='corroborates')
E=ev('meng_shu_king','二月癸亥后唐授孟知祥东西川节度使，封蜀王',7,'癸亥，',None,[('上','朝廷授节与封王者'),('知祥','获两川节度与蜀王封者')],when='933年二月癸亥',place='东西川',note='蜀王非已经皇帝，后934建蜀不提前；墨制地方官任与朝廷王爵不同。')
claim('event',E,'description','旧明宗纪同二月癸亥记孟知祥为剑南东、西两川节度使，封蜀王。',7,'癸亥，以西川節度使孟知祥為劍南東、西兩川節度使，封蜀王。','主略东西川、新衔剑南地理军名同任；无须新建一位孟蜀王。',source=feb,relation='corroborates')
ev('renfu_report_and_tang_fears','史述河西诸镇曾报李仁福潜通契丹，朝廷担忧联兵南侵',8,'先是，','会仁福卒，',[],year=None,when='先是，李仁福在世时的报告与担忧；起年未独载',place='河西诸镇、后唐朝廷',note='皆言为诸镇报告，恐为朝廷担忧；不建立已证实通敌、已联兵或已吞河右侵关中事件，也不让已死仁福933之后新通契丹。')
E=ev('yichao_moved_zhangwu','三月癸未朝廷改李彝超为彰武留后',8,'三月，癸未，','以其子彝超为彰武留后，',[('上','移任令者'),('彝超','由夏州地方留后被调往彰武者')],when='通鉴933年三月癸未',place='拟赴彰武、延州',note='彰武军治延州，发命不等本人已到任；旧本纪戊子与主癸未差异保。')
claim('event',E,'description','旧明宗纪记三月戊子授李彝超延州留后。',8,'以夏州左都押衙、四州防遏使李彝超為延州留後，','旧承前戊子、主癸未不同日，军名与治州同职；不强并作同干支也不造两次互换。',source=mar,relation='corroborates')
E=ev('congjin_moved_dingnan','三月癸未朝廷调安从进为定难留后',8,'徙彰武节度使安从进','为定难留后，',[('上','调任者'),('从进','彰武节度使、拟入定难留后者')],when='通鉴933年三月癸未',place='拟赴定难、夏州',note='留后与正节度分，调任与后来攻夏州分，不能写已取代李彝超控全夏州。')
claim('event',E,'description','旧明宗纪三月戊子记安从进由延州节度使转夏州留后。',8,'戊子，以延州節度使安從進為夏州留後，','主彰武与定难军名、旧延州夏州治名同人同移，日期差异另留。',source=mar,relation='corroborates')
claim('person',people['安从进'],'description','新传称安从进为振武索葛部人。',8,'安從進，振武索葛部人也。','索葛为史载部属称，按原文，不套现代民族唯一对应，未据祖父骑将猜出生地。',source=congjin,relation='corroborates')
E=ev('army_escorts_congjin','朝廷命药彦稠领五万兵、安重益监军，送安从进赴定难',8,'仍命静难节度使药彦稠','送从进赴镇。',[('上','发军令者'),('药彦稠','静难节度使、领兵护送者'),('安重益','宫苑使、监军者'),('从进','被援送新镇者')],when='通鉴933年三月癸未任命同段；行军出发日未独载',place='静难至定难',note='命兵五万为主计划调发数，不当战场实到清点人数；旧本纪同安重益、旧彝传作安从益疑字，不自行创造第二监军或改原字。')
claim('event',E,'description','旧明宗纪亦命邠州节度使药彦稠与宫苑使安重益援送安从进。',8,'仍命邠州節度使藥彥稠、宮苑使安重益帥師援送從進赴鎮。','邠州为静难治州名；旧本句未载五万不能说两书都核五万。',source=mar,relation='corroborates')
claim('event',E,'description','旧彝超传护送者作药彦稠、宫苑使安从益。',8,'詔邠州節度使藥彥稠、宮苑使安從益等率師援送從進赴鎮，','主旧纪安重益与旧传从益异字同官同使命，先沿主重益主体保原字；未强把从益列无疑别名，纸本待核。',source=yichao,relation='adds')
# The main text names the five appointees collectively; the old annal supplies their offices.
oldtxt=(sources[mar]/'source.txt').read_text();liststart=oldtxt.index('乙酉，以西川节度') if '乙酉，以西川节度' in oldtxt else oldtxt.index('乙酉，以西川節度')
listend=oldtxt.index('從孟知祥之請也。',liststart)+len('從孟知祥之請也。');five=oldtxt[liststart:listend]
E=ev('court_five_governors','三月乙酉后唐正式制授赵季良等五镇节度使',9,'乙酉，',None,[('上','朝廷正式下制者'),('赵季良','五镇制授受任者之一')],when='933年三月乙酉',place='武泰、武信、保宁、宁江、昭武五镇',note='始下制与孟二月墨制分，主未逐列五人由旧同日名职补。不能把932请授就写当时已正授。')
claim('event',E,'description','旧明宗纪同乙酉列赵季良黔南、李仁罕遂州、赵廷隐阆州、张知业夔州、李肇利州节度使，称从孟知祥之请。',9,five,'五军治州军名对应；旧张知业沿已有张业，前宁江留后同人，未因知字造新人。旧检校太保太傅司徒并留原文，未将检校衔误作入朝实掌三公。',source=mar,relation='adds')
for name,role in [('李仁罕','武信留后转遂州节度使'),('赵廷隐','保宁留后转阆州节度使'),('张知业','宁江留后转夔州节度使'),('李肇','昭武留后转利州节度使')]:
 pk=person(name,9,role,five,source=mar);edge='participation_zztj_278_0933_court_five_'+pk;B['person_events'].append(dict(key=edge,person_key=pk,event_key=E,role=role,status='draft'));claim('person_event',edge,'role',ALIASES.get(name,name)+'：'+role+'。',9,five,'旧同日五任名单明确，主体沿已存稳定key；此为朝廷正任，不重复地方墨制阶段。',source=mar,relation='adds')
E=ev('tang_warns_four_prefectures','三月丁亥朝廷敕夏银绥宥将士吏民，以顺命得福、抗命覆族劝服调任',10,'丁亥，','覆族之祸。”',[('上','发布敕谕者'),('彝超','被要求赴延安新镇者')],when='通鉴933年三月丁亥',place='夏、银、绥、宥',note='年少未能防边为诏词理由而非本站能力结论；李从缺字严沿既有李继曮/李从严案例说明，王都李匡宾为过去警示，不造933覆族或使死人当期行动。')
claim('event',E,'description','旧彝超传敕谕以李从严、高允韬识变归朝为福，以王都、李宾抗移而亡为戒。',10,'彼或要覆族之殃，則王都、李賓足為鑒戒；彼或要全身之福，則允韜、從嚴可作規繩。','旧李宾与主李匡宾对应此前史事，仅作敕例不重建；主从字后缺字保留，旧李从严身份取现有李继曮别名，不认另一个李从严。',source=warning,relation='corroborates')
E=ev('yichao_reports_retained','四月李彝超上言被军士百姓拥留，尚未能赴新镇',10,'夏，四月，','未得赴镇，',[('彝超','上言未赴任者')],when='通鉴933年四月；本句未独日',place='夏州、拟赴延州',note='为军民拥留是其上言理由，不能当现代核实无主观抗命；实际是否自立与抗拒后续逐段核。')
claim('event',E,'description','旧明宗纪四月戊申记彝超奏已受延州留后恩命，因军民拥隔未赴。',10,'夏四月戊申，李彝超奏：「奉詔除延州留後，已受恩命訖，三軍百姓擁隔，未遂赴任。」','主月记、旧具体戊申补；受诏不等已接管延州，也不把四月当三月敕日。',source=apr,relation='adds')
E=ev('tang_urges_yichao','朝廷遣使催李彝超赴镇',10,'诏遣使趣之。','诏遣使趣之。',[('上','遣使催赴者'),('彝超','被催赴任者')],when='933年四月上言后；遣使确日未独载',place='后唐朝廷至夏州',note='催令不等被催者已抵延安。主未名使者，旧纪补苏继颜，旧传另一字先留待核，不猜使命已经成功。')
claim('event',E,'description','旧明宗纪记遣阁门使苏继颜赍诏促彝超赴任。',10,'帝遣閣門使蘇繼顏齎詔促彝超赴任。','主匿名与旧姓名补；旧彝传另作苏继彦，纸本未校，不另造苏继彦实体。',source=apr,relation='adds')
reviews={1:'正月戊子秦加守尚书令兼侍中、庚寅刘昫入相分。同日同端明殿学士旧刘煦字异识一人，煦不是昫的繁简规则；归义作籍称，既有官职不重授。',2:'龙见为闽人传言、改宅名；宝皇受册称帝、国号赦改元、改名、父祖五庙、李敏及继鹏二相、吴枢密、唐二使到海门、裴新职、程还请拒与常谨事邻概述分。闽李敏与昭宗旧名李敏不同人，限定主体不套旧帝别名。王延钧更璘、新鏻异字留，儿子王继鹏父亲关系检查方向修正再复用。旧未几称帝和新仪式补，不提前旧清泰元年遇弒或后935死；新后国计薛文杰等未来展开暂不抢录。',3:'二月戊申孟墨制五镇是地方任，与932请表及三月朝廷正式下制分；主仅赵季良等，其余姓名先不猜本句明列。',4:'请孙超任、问答回顾与补书正式授任分。孙超遣使团、杨通信耆老由旧补，新问答归承谦注明单书归属，主使者匿名保。拓跋/拓拔同使命一人，不与夏州李族凭姓猜亲。二千五百为唐旧戍数量，主黄巢阻隔与新唐亡层次保，非933新募2500人。张义潮/义朝只问答回顾不建933其募兵。',5:'二月乙卯武安武平兼中书令明确，与932武安兼侍中不同后续任。旧二月另记马希范鄂州授任与主差异未直接同作补证，不覆主。',6:'李仁福主二月戊午卒、军立彝超庚申；旧仁福传三月卒异月并列，旧三月奏闻不能当实际死日。彝超次子前押衙防遏由旧补，父亲有向、彜/彝字形同。旧三军立帅取同事，矫父奏另动作未作父亲真奏。',7:'二月癸亥孟获两川节度及蜀王与旧同日互核，封王不提前934称帝。',8:'先是潜通契丹为诸镇报告、吞河右侵关中为朝廷恐，均不当已证通敌或既成侵略，起年null不使亡者复生。三月癸未主移任两人、护送军令分，旧纪戊子异日留；主兵五万仅主命数。安从进索葛身份新补，不猜现代民族。安重益主旧纪一致、旧传从益异字留不静改或再建。',9:'三月乙酉朝廷正式制授与孟二月墨制分。旧同日五名单及治州、前军留后衔补，张知业沿已有张业，检校太保等非实任中央三公。',10:'三月丁亥敕四州与四月李上言、再催分，年轻不能御为帝敕理由，不定出生年。旧具体四月戊申补，受命仍未赴不当已到任。旧苏继颜与传苏继彦差异未造双使；诏从缺字严用既有李继曮别名旧李从严识但保原，王都李匡宾旧例不复建当期覆族。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,11):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=933,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,11)],next_paragraph='zztj-v278-y0933-p011',next_volume=278,next_year=933,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷278连续933年首10段，原36—45行；年初授职、闽称帝仪制及使事、蜀地方五镇墨制与朝廷授王正任、凉州请命、楚加任、夏州父卒子立及移镇护送敕催。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,11)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
