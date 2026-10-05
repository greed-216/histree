# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 945 paragraphs 11–18."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,24))
COMMIT='7fdbc991f6904ba3ca54b43df9788457ad6b8e5f'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-945-august-november','xinwudaishi-009-945','xinwudaishi-068-li-ren-da','jiuwudaishi-084-945-september','xinwudaishi-065-hongya-death']:
 prior=next(x for f in (ROOT/'content').rglob('content-batch.json') for x in json.loads(f.read_text())['sources'] if x['key']==key)
 commit,relative=prior['url'].split('/blob/')[1].split('/',1)
 specs.append((key,(ROOT/relative).parent,commit,prior['author']))

# Reuse already published source identities, including the earlier Zhou Gui biography.
prior_source_registry={x['key']:x for f in sorted((ROOT/'content').rglob('content-batch.json')) if f.parent != P for x in json.loads(f.read_text())['sources']}
normalized=[]
for key,path,commit,author in specs:
 if key in prior_source_registry:
  archived=prior_source_registry[key]['url'].split('/blob/',1)[1];commit,relative=archived.split('/',1);old_path=(ROOT/relative).parent
  assert (old_path/'source.txt').read_bytes()==(path/'source.txt').read_bytes(),key
  path=old_path
 normalized.append((key,path,commit,author))
specs=normalized

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-285-945-august-november','tongjian-285-945-november-december']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0945-p011-p018',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=record.get('edition_note','选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/285.txt').read_text().splitlines()
for n in range(11, 19):
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
for revision in sorted((ROOT/'content/revisions').glob('*/aliases.json')):
    if not (revision.parent/'publication.json').exists():continue
    for corrected in json.loads(revision.read_text()).get('people',[]):
        if corrected['name'] in registry:registry[corrected['name']]=dict(registry[corrected['name']],aliases=corrected['after'])
for name,extra in [('荝剌',['荝刺']),('耶律倍',['李赞华','李贊華'])]:
    if name in registry:registry[name]=dict(registry[name],aliases=list(dict.fromkeys(registry[name]['aliases']+extra)))
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    for a,b in [('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷285·后晋开运二年（945年九月至十一月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0945_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={'王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
NEW_ALIASES={'王威（王处直之子）':['王威']}

ALIASES.update({'景通':'李璟','徐知诰':'李昪','徐诰':'李昪','元瓘':'钱传瓘','钱元瓘':'钱传瓘','闽主':'王继鹏','蜀主':'孟昶','汉主':'刘岩','梁均王':'朱友贞'})



ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

# Follow already verified merges so hidden legacy entities are never revived.
registry_by_key={r['key']:r for r in registry.values()}
for plan_file in sorted((ROOT/'content/revisions').glob('*/plan.json')):
 audit_file=plan_file.parent/'publication.json'
 if not audit_file.exists():continue
 plan=json.loads(plan_file.read_text());audit=json.loads(audit_file.read_text())
 if not (audit.get('verified') and audit.get('canonical_person_id') and audit.get('hidden_duplicate_person_id')):continue
 canonical=registry_by_key.get(plan.get('canonical_key'));duplicate=registry_by_key.get(plan.get('duplicate_key'))
 if canonical and duplicate:
  canonical=dict(canonical,aliases=list(dict.fromkeys(canonical.get('aliases',[])+plan.get('aliases_to_add',[]))))
  registry[canonical['name']]=canonical
  for alias in [duplicate['name']]+duplicate.get('aliases',[]):ALIASES[alias]=canonical['name']

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=945, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='945年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_285_0945_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=description or title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='采用史书记载的地点名称，地理坐标尚未核实。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按《资治通鉴》及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_285_0945_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'与{a}存在原文明示的亲属关系',quote,source=source)
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
        row=dict(key=f'relationship_zztj_285_0945_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=event(code,title,n,span(n,start,end),actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
ALIASES.update({'帝':'石重贵','高祖':'石敬瑭','唐主':'李璟','汉主':'刘弘熙','刘晟':'刘弘熙','弘佐':'钱弘佐','王建':'王建（高丽）','武':'王武（高丽）','王翻':'王翷','何昌延':'何昌廷','宋太后':'宋氏（南唐李昪后）','李彦韬':'李彦韬（后晋宣徽使）','弘义':'李仁达'})
NEW_ALIASES={'王崇文':[],'王武（高丽）':['王武（高麗）'],'袜啰':['襪囉'],'郭仁遇':[],'杜昭达':['杜昭達'],'程昭悦':['程昭悅'],'慎温其':['慎溫其']}
NEW_DESCRIPTIONS={'王崇文':'南唐百胜军节度使。945年建州陷落后受任永安节度使，《资治通鉴》记他治理宽简，建州百姓渐安。生卒年本段未载。','王武（高丽）':'高丽王建之子。父亲去世后自称权知国事，上表告丧；945年十一月戊戌获得后晋所授大义军使、高丽王。郭仁遇出使要求攻契丹，返回后王武又以其他理由推辞。其生卒年本次未核，不凭同名合并其他王武。','袜啰':'史书称为胡僧，曾替高丽王建向石敬瑭请求合攻契丹以取回渤海，后来又向石重贵进言。郭仁遇实地出使后对其所述高丽兵力作出不同判断。生卒、族属与其他译名本段未载。','郭仁遇':'后晋通事舍人。945年奉命出使高丽，要求王武攻契丹；到当地后认为高丽兵力很弱、不能与契丹为敌，随后返回。生卒年本段未载。','杜昭达':'杜建徽的孙子，吴越内都监使。曾与阚璠接受程昭悦的钱财结交；945年十一月乙卯被钱弘佐杀死。《资治通鉴》将谋立钱仁俊的说法记为程昭悦诬告和制造证据，未当作确实谋反。出生年本段未载。','程昭悦':'钱塘富人，通过财物结交杜昭达、阚璠，得以接近钱弘佐。后来谋排阚璠，诬告阚璠、杜昭达拥立钱仁俊，使两人遇害、钱仁俊失官被囚，并清除百余权位与自己相当或被自己忌恨的人。生卒年本段未载。','慎温其':'衢州人，钱仁俊故吏。被程昭悦拷打逼迫作证时坚持不屈，得到钱弘佐赏识，擢为国官。《宋史》慎知礼传记其父温其有词学，后仕钱俶至元帅府判官。生卒年未载。'}
NEW_DEATH_YEARS={'杜昭达':945}
sep='945年九月条下，具体日未载';oct='945年十月条下，具体日未载';nov='945年十一月条下，具体日未载';prior='阚璠、杜昭达被杀之前的追述，具体年月日未载'
os='jiuwudaishi-084-945-september';oo='jiuwudaishi-084-945-october';hy='xinwudaishi-065-hongya-death';mi='xinwudaishi-068-li-ren-da';ny='xinwudaishi-009-945';kg='xinwudaishi-074-goryeo';wk='xinwudaishi-067-du-kan-deaths';sw='songshi-277-shen-wenqi'
add('zhang_garrisons_hengzhou','后晋派张彦泽驻守恒州',11,'乙卯，',None,[('张彦泽','以彰德节度使身份受命驻守恒州')],when='945年九月乙卯',place='恒州',note='戍为驻守，不认作正式授恒州节度使。')
sup('zhang_garrisons_hengzhou',11,os,'乙卯，詔相州節度使張彥澤率兵屯恒州。','《旧五代史》同记乙卯张彦泽率兵屯恒州。','相州与彰德军为同镇职衔，两书主将与纪日一致。')
# 12: separate victims, previously stable identities and speech versus facts.
for code,name in [('liu_sichao','刘思潮'),('lin_shaoqiang','林少强'),('lin_shaoliang','林少良'),('he_changyan','何昌延')]:
 add('han_kills_'+code,f'刘晟杀死{name}',12,'汉主杀','何昌延。',[('汉主',f'杀死{name}'),(name,'被刘晟杀死')],when=sep,place='南汉',note='本段汉主复用更名刘晟的刘弘熙主体；未逐人给出独立日。何昌延与943年同组力士何昌廷按对应成员识别，延廷字形异文待纸本核。')
 claim('person',people[ALIASES.get(name,name)],'death_year',f'{name}于945年被刘晟杀死。',12,'汉主杀刘思潮、林少强、林少良、何昌延。','本段明确死亡；何昌延廷字形异文保留引用与说明，不另建同组成员的重复主体。')
sup('han_kills_liu_sichao',12,hy,'又殺劉思潮等五人。','《新五代史》记刘晟在杀刘弘雅之后又杀刘思潮等五人。','《资治通鉴》此处列四名，《新五代史》说五人但未逐名，不能据此补出第五名被杀者。',relation='conflicts')
claim('person',people['何昌廷'],'aliases','《资治通鉴》945年该组力士被杀条将何昌廷写作何昌延。',12,'汉主杀刘思潮、林少强、林少良、何昌延。','与943年同列刘思潮、林少强、林少良等力士对应，保留延廷异文并待纸本核，不把别名写成已校定正字。')
add('han_sends_wang_fan_yingzhou','刘晟因王翷曾参与拥立刘弘昌的谋议，将他调为英州刺史',12,'以左仆射王翻','英州刺史，',[('汉主','因王翷曾参与先帝立弘昌谋议而将其调离朝廷'),('王翻','由左仆射调为英州刺史')],when=sep,place='南汉至英州',note='此句高祖为南汉刘岩，不能误解为后晋石敬瑭；旧谋议已录，不当作945年新一次拥立。')
add('han_kills_wang_fan_before_arrival','王翷尚未到英州，就被刘晟赐死',12,'未至，','赐死。',[('汉主','在王翷到任前赐死'),('王翻','赴英州尚未到任便被赐死')],when=sep,place='赴英州途中，具体地点未载',note='未至不等于已治英州，王翻复用王翷姓名异文主体。')
sup('han_kills_wang_fan_before_arrival',12,hy,'以右僕射王翻為英州刺史，使人殺之於路。','《新五代史》也记王翻被调英州并在途中遇杀，但原职写右仆射。','主书左仆射与新史右仆射异说并列，途中被杀与到任有别。',relation='conflicts')
claim('person',people['王翷'],'death_year','王翷于945年赴英州未到任时被赐死。',12,'未至，赐死。','死亡基于本段连续叙述，引用之外使用既有规范姓名。')
add('han_court_fears_purge','南汉接连诛杀后，朝野都害怕无法保全自身',12,'内外皆',None,[],when=sep,place='南汉',note='内外皆惧是史书概述，不造具名请罪者或用现代调查比例表达。')
# 13–15.
add('jin_establishes_zhenan_chenzhou','后晋在陈州设镇安军',13,'冬，',None,[],when='945年十月癸巳',place='陈州')
sup('jin_establishes_zhenan_chenzhou',13,oo,'癸巳，升陳州為節鎮，以鎮安軍為軍額。','《旧五代史》同日记陈州升节镇，以镇安军为军额。','行政军额设立，不推为建新城。')
add('song_empress_dies','南唐宋太后去世',14,'唐元敬',None,[('宋太后','在南唐去世')],when=oct,place='南唐',note='元敬为主书称呼，复用李昪皇后宋氏；未凭其他非本引文材料补个人名字。')
claim('person',people['宋氏（南唐李昪后）'],'death_year','南唐宋太后于945年十月条下记为去世。',14,'唐元敬宋太后殂。','本段死亡记事明确，具体日未载，未覆盖旧档案。')
add('wang_yanzheng_arrives_jinling','王延政抵达金陵',15,'王延政','金陵，',[('王延政','从闽地抵达金陵')],when=oct,place='金陵')
sup('wang_yanzheng_arrives_jinling',15,mi,'遷延政族於金陵，','《新五代史》记王延政一族被迁到金陵。','该书迁族属于破建州后叙事，纪年写保大四年，与主书945仍有差异；本次不提前取该书鄱阳王封号。',relation='adds')
add('li_appoints_wang_yulin','李璟任王延政为羽林大将军',15,'唐主以为','大将军。',[('唐主','任王延政为羽林大将军'),('王延政','在南唐获授羽林大将军')],when=oct,place='金陵')
add('li_executes_yang_sigong','南唐斩杀杨思恭，向建州百姓表示交代',15,'斩杨思恭','建人。',[('杨思恭','在南唐处置建州战后事务时被斩杀')],when=oct,place='南唐，具体行刑地点未载',note='承接南唐战后处置，行刑者未具名；不把谢建人解为已证明全城一致接受。')
claim('person',people['杨思恭'],'death_year','杨思恭于945年建州战后处置中被斩杀。',15,'斩杨思恭以谢建人。','未写具体行刑日地，不凭上下文金陵就把刑场定位金陵。')
add('wang_chongwen_appointed_yongan','南唐任王崇文为永安节度使',15,'以百胜','节度使。',[('王崇文','由百胜节度使改任永安节度使')],when=oct,place='建州')
add('wang_chongwen_governs_leniently','王崇文以宽简方式治理建州，百姓逐渐安定',15,'崇文治',None,[('王崇文','以宽简方式治理建州')],when='王崇文任永安节度使之后，具体起止年月未载',year=None,place='建州',note='治理后果为史书概述，不写成任命当天已完全安定。')
# 16: earlier proposal, renewed mission, temporary succession and observations.
add('goryeo_wang_earlier_conquests','史书记高丽王建曾以战争吞并邻国',16,'初，高丽','强大，',[('王建','曾出兵吞并邻国，史书在此形容其势力强大')],when='王建在位时的追述，具体年月未载',year=None,place='高丽周边',note='这里强大是前段背景描述，后文郭仁遇实地认为兵弱，两层记载都保留；未列国名不补战役。')
add('waluo_proposes_joint_attack','袜啰替王建向石敬瑭提议合攻契丹、夺回渤海',16,'因胡僧袜啰','取之。”',[('袜啰','替高丽王建向石敬瑭传达合攻契丹请求'),('王建','借袜啰提出合攻契丹请求'),('高祖','收到高丽方面请求')],when='石敬瑭在位时，具体年月未载',year=None,place='高丽至后晋',note='渤海为婚姻之邦是王建提议中的说法，未具名配偶不建立跨国婚姻人物关系；高祖在此是石敬瑭。')
add('shi_jingtang_no_reply_goryeo','石敬瑭没有答复高丽的合攻请求',16,'高祖不报。','高祖不报。',[('高祖','没有答复王建通过袜啰提出的合攻请求')],when='石敬瑭在位时，具体年月未载',year=None,place='后晋朝廷',note='不报是没有答复，不等于有明文斩杀使者或宣布绝交。')
add('waluo_renews_proposal','后晋与契丹交恶后，袜啰再次提出高丽合攻建议',16,'及帝与','言之。',[('袜啰','在晋契丹交恶后再次提出合攻建议'),('帝','听到袜啰再次提出建议')],when='石重贵与契丹交恶后，具体年月未载',year=None,place='后晋朝廷')
add('shi_plans_goryeo_diversion','石重贵想让高丽扰契丹东边，分散契丹兵力',16,'帝欲','兵势。',[('帝','计划让高丽进扰契丹东边，以分散兵力')],when='石重贵听到高丽合攻建议后，具体年月未载',year=None,place='后晋、高丽、契丹东部',note='欲使为计划，不能写成高丽已攻契丹。')
add('goryeo_wang_death_report','王建去世，儿子王武暂掌国事并上表告丧',16,'会建卒，','告丧。',[('王建','去世后由儿子暂掌国事并向后晋报丧'),('武','父亲去世后自称权知国事，上表告丧')],when='王建去世及高丽报丧的追述；本段未分别给死亡和报丧年月日',year=None,place='高丽至后晋',note='会建卒是追述，不能用十一月册命日作王建死亡日；其他史书纪年另列，待进一步核对消息传播与实际日期。')
sup('goryeo_wang_death_report',16,kg,'開運二年，建卒，子武立。','《新五代史》记王建在开运二年去世、王武继位。','该书将死与继位系945；主书本段为追叙并未分死亡、消息抵达与册命。暂保留具体书证，待其他记载核年，不仅凭此改人物死亡年。',relation='adds',field='time_original')
relationship('王建','武','父亲',16,'会建卒，子武自称权知国事，上表告丧。','本句明确王武是王建之子，关系方向为高丽王建是王武的父亲。')
add('jin_confers_goryeo_wangwu','后晋任王武为大义军使，封高丽王',16,'十一月，','高丽王，',[('帝','任王武大义军使，封高丽王'),('武','获后晋任命与册封')],when='945年十一月戊戌',place='后晋朝廷至高丽',note='中国册命与高丽国内权知国事是不同阶段，未凭冊命认为此日才继位。'.replace('冊','册'))
sup('jin_confers_goryeo_wangwu',16,ny,'十一月戊戌，封王武為高麗國王。','《新五代史》本纪同记十一月戊戌封王武为高丽王。','同日册命，不作为高丽内部继位日。')
add('guo_dispatched_goryeo','石重贵派郭仁遇出使高丽，要求进攻契丹',16,'遣通事舍人','契丹。',[('帝','派通事舍人郭仁遇要求高丽攻击契丹'),('郭仁遇','出使高丽传达进攻契丹的要求')],when='945年十一月戊戌条下',place='后晋至高丽',note='谕使击为传达要求，不能当成高丽已执行。')
add('guo_observes_goryeo_weakness','郭仁遇到高丽后认为其兵力很弱，不敢与契丹为敌',16,'仁遇至其国，','为敌。',[('郭仁遇','到高丽后认为当地兵力弱，先前王建的说法夸大')],when='郭仁遇出使高丽期间，具体年月日未载',year=None,place='高丽',note='兵极弱与袜啰夸诞为本段出使后的判断，不据此补兵力数，也不写成高丽史上从未有军力。')
add('guo_returns_wangwu_excuses','郭仁遇返回后，王武又以其他理由推辞',16,'仁遇还，',None,[('郭仁遇','从高丽返回'),('武','在郭仁遇返回后又以其他理由解释未攻契丹')],when='郭仁遇出使返回后，具体年月日未载',year=None,place='高丽与后晋',note='原文未载其他理由内容，不补具体国难、财力或已签订条约。')
# 17: executions first in narrative, then retrospective lead-up.
add('qian_kills_du_zhaoda','钱弘佐杀死吴越内都监使杜昭达',17,'乙卯，','杜昭达，',[('弘佐','杀内都监使杜昭达'),('杜昭达','被钱弘佐杀死')],when='945年十一月乙卯',place='吴越',note='诛为史书用词，后段记罪名出于诬告，不据诛字认定谋反属实。')
sup('qian_kills_du_zhaoda',17,wk,'殺內都監杜昭達、統軍使闞璠，','《新五代史》同记钱弘佐杀杜昭达、阚璠。','本纪未列日，具体日分别来自主书；不把此句当作两人同日死。')
add('qian_kills_kan_fan','钱弘佐杀死阚璠',17,'己未，','阚璠。',[('弘佐','杀内牙上统军使、明州刺史阚璠'),('阚璠','被钱弘佐杀死')],when='945年十一月己未',place='吴越',note='两人分别乙卯己未遇害，不能合成同日一次行刑。')
sup('qian_kills_kan_fan',17,wk,'殺內都監杜昭達、統軍使闞璠，由是國中皆畏恐。','《新五代史》也记杀阚璠，并说国内因此畏惧。','只补同人死亡及该书评价，不凭简述补具体刑场。')
relationship('杜建徽','杜昭达','祖父',17,'昭达，建徽之孙也，','本句明确杜昭达为杜建徽孙子；方向杜建徽是杜昭达祖父，未造中间父母主体。')
add('du_kan_described_as_greedy','史书称杜昭达、阚璠都贪财',17,'昭达，','好货。',[('杜昭达','被史书评价为贪财'),('阚璠','被史书评价为贪财')],when=prior,year=None,place='吴越',note='好货为史书评价，不补具体贪污案件或金额。')
add('cheng_buys_access','程昭悦用财物结交杜昭达、阚璠，得以侍奉钱弘佐',17,'钱塘富人','左右。',[('程昭悦','用财物结交杜昭达、阚璠以接近钱弘佐'),('杜昭达','接受程昭悦财物结交'),('阚璠','接受程昭悦财物结交')],when=prior,year=None,place='钱塘、吴越朝廷')
add('cheng_favored_kan_discontent','钱弘佐对程昭悦的宠遇超过旧将，阚璠不满',17,'昭悦为人','不能平。',[('程昭悦','得到超过旧将的宠遇'),('弘佐','宠信程昭悦'),('阚璠','对程昭悦的宠遇不满')],when=prior,year=None,place='吴越朝廷',note='狡佞是史书评价；阚不满不等同已举兵反叛。')
add('cheng_apologizes_kan_threatens','程昭悦向阚璠叩头谢罪，阚璠称原想杀他，如今放弃',17,'昭悦知之，','释然。”',[('程昭悦','向阚璠叩头谢罪'),('阚璠','责问后称曾想杀程昭悦，如今不再追究')],when=prior,year=None,place='吴越',note='始决欲杀为阚璠所说意图，不建已经谋杀程昭悦事实。')
add('cheng_plans_remove_kan','程昭悦因害怕而谋划排除阚璠',17,'昭悦惧，','王亦恶之。',[('程昭悦','因惧怕阚璠而计划排除他'),('阚璠','被史书称专横固执，并受钱弘佐与众人厌恶'),('弘佐','厌恶阚璠')],when=prior,year=None,place='吴越',note='厌恶是史书描述的态度，未据此推每人都参与诬告。')
add('cheng_seeks_hu_cover_transfer','程昭悦与胡进思商量一同外任刺史，以免阚璠怀疑',17,'昭悦欲出','进思许之，',[('程昭悦','建议胡进思与阚璠都外任，以掩饰排阚计划'),('胡进思','同意程昭悦提出的外任安排')],when=prior,year=None,place='吴越',note='私议是商量阶段，正式任命另录。')
add('kan_assigned_mingzhou','吴越任阚璠为明州刺史',17,'乃以璠','刺史，',[('阚璠','被任命为明州刺史')],when=prior,year=None,place='明州',note='任命年月未载，不能把它套在后来行刑己未当日。')
add('hu_assigned_huzhou','吴越任胡进思为湖州刺史',17,'进思为','刺史。',[('胡进思','被任命为湖州刺史')],when=prior,year=None,place='湖州')
add('kan_accepts_after_hu_advice','阚璠对外任发怒，经胡进思劝说后接受任命',17,'璠怒曰：','受命。',[('阚璠','把外任视作被抛弃，经胡进思劝说后受命'),('胡进思','劝阚璠接受大州刺史任命')],when=prior,year=None,place='吴越')
add('hu_retained_at_court','吴越又以其他理由留胡进思，未让他赴湖州',17,'既而复',None,[('胡进思','在湖州任命后又被留在朝廷')],when=prior,year=None,place='吴越朝廷',note='其他理由原文未明，不补实际病因或诏令原文。')
# 18: forged accusation, confinement, purges and coercion of a witness.
add('qian_renjun_mother_du_aunt','史书记钱仁俊之母是杜昭达的姑母',18,'内外马步','姑也。',[('钱仁俊','其母被明确记为杜昭达的姑母'),('杜昭达','其姑母是钱仁俊之母')],when='未定年月的亲属说明',year=None,place='吴越',note='母亲未具名，不造占位主体，也不把这层姑母之子关系随意改成叔侄。')
add('cheng_falsely_accuses_du_kan','程昭悦诬告阚璠、杜昭达要拥立钱仁俊作乱',18,'昭悦因谮','作乱，',[('程昭悦','诬告阚璠、杜昭达谋拥立钱仁俊'),('阚璠','被诬告谋拥立钱仁俊'),('杜昭达','被诬告谋拥立钱仁俊'),('钱仁俊','被诬告为拥立计划对象')],when='945年阚璠、杜昭达被杀前，具体日未载',place='吴越',note='谮明确为诬告，不把罪名当成实际已发动叛乱。')
add('cheng_fabricates_case_in_prison','程昭悦将阚璠、杜昭达下狱，通过审讯制造罪证',18,'下狱','成之。',[('程昭悦','把两人下狱，制造罪证'),('阚璠','下狱被制造罪证'),('杜昭达','下狱被制造罪证')],when='945年两人被杀前，具体日未载',place='吴越',note='锻炼成之在此为罗织制造罪证，不能译成正常军事训练。')
add('qian_renjun_removed_confined','阚璠、杜昭达死后，钱仁俊被夺官，囚于东府',18,'璠、昭达既诛，','东府。',[('钱仁俊','在诬告案后被夺官并关在东府')],when='945年十一月阚杜被杀之后，具体日未载',place='吴越东府',note='幽为囚禁，不当作已处死。东府沿用史载名称，不补现代坐标。')
add('cheng_purges_rivals','程昭悦借追查阚杜党羽，诛杀或流放百余被他忌恨或权位相当的人',18,'于是昭悦治','侧目。',[('程昭悦','追查阚杜党羽，诛杀流放权位相当或被他忌恨的人')],when='945年阚杜被杀之后，具体日未载',place='吴越',note='诛放百余是两类处置合计概数，不能写成百余人全部杀死；未名受害者不虚构。')
add('cheng_spares_hu_jinsi','程昭悦认为胡进思憨直，清除权臣时唯独留下他',18,'胡进思重厚','存之。',[('程昭悦','认为胡进思憨直，因此留下他'),('胡进思','在清除权臣时被留下')],when='945年程昭悦清除权臣时，具体日未载',place='吴越',note='戆是程的判断，重厚寡言为史书描述，不写成现代医学或智力诊断。')
add('cheng_tortures_shen_for_testimony','程昭悦抓慎温其，拷打逼他证明钱仁俊有罪',18,'昭悦收仁俊','备至。',[('程昭悦','抓钱仁俊故吏慎温其，拷打逼其作证'),('慎温其','被抓并拷打逼迫作证')],when='945年程昭悦清查钱仁俊案件时，具体日未载',place='吴越',note='要求证罪是逼供目的，不能写成慎已经证明钱仁俊确有罪。')
add('shen_refuses_false_testimony','慎温其受拷打仍坚持不屈',18,'温其坚守','不屈。',[('慎温其','在逼供中坚守不屈')],when='945年钱仁俊案件中，具体日未载',place='吴越')
add('qian_promotes_shen','钱弘佐赞赏慎温其，将他擢为国官',18,'弘佐嘉之，',None,[('弘佐','赞赏慎温其不屈，任其为国官'),('慎温其','受钱弘佐赏识，获任国官')],when='945年慎温其受拷打不屈后，具体日未载',place='吴越',note='国官保留史载泛称，不补未经证实的具体官名；衢州为籍贯。')
claim('person',people['慎温其'],'description','《宋史》慎知礼传记其父慎温其有词学，后来仕钱俶，官至元帅府判官。',18,'慎知禮，衢州信安人。父溫其，有詞學，仕錢俶，終元帥府判官。','同姓父名与衢州籍贯对应作补证；后仕钱俶非945钱弘佐当场授判官，不把未来官职提前。',source=sw)
for name,n,quote in [('杜昭达',17,'乙卯，吴越王弘佐诛内都监使杜昭达，'),('阚璠',17,'己未，诛内牙上统军使明州刺史阚璠。')]:
 claim('person',people[name],'death_year',name+'于945年十一月被钱弘佐杀死。',n,quote,'死亡纪日按两人各自事件保留，诬告与实际处罚分清。')
reviews={11:'彰德相州对应同职，戍恒非授恒节度。',12:'汉主复用刘弘熙更名晟；何昌延廷同组对应异文待核。主四名新五人不补第五者。左仆射新右仆射并列；高祖此句刘岩。王调英未到即死，旧谋议非本年新谋。',13:'陈州升节镇与镇安军军额同日两书补。',14:'宋太后复用宋氏南唐李昪后，元敬称呼按底本，不虚补个人名。',15:'王到金陵、授羽林、杨斩、王崇文任永安与后续宽治分开。杨行刑地未载不套金陵；新史迁族纪年946异说承前，不提前鄱阳王封号。',16:'初字后为前事，王早战、袜传请求、高祖不答、石重贵想分兵均未定年月。王死亡、国内暂知与后晋十一月册命分开，死年新史945补独立引用但主体未强定；父亲方向高丽王建→王武，不与蜀王同名合并。实地兵弱与前述强大是不同叙述，未补人数。',17:'两将死亡乙卯己未分开，后文追述贿结宠遇与排外任不套行刑日。杜孙关系直用祖父，不造中间人。阚欲杀程为言辞而非已杀。胡同意外任后又被留，未补未知理由。',18:'姑母未名不造人，诬告与制造罪证明确，不认谋反确实。钱被夺官囚禁非被杀。诛放百余为两类处置概数，程以胡戆是主观判断。慎逼供未屈与弘佐擢国官分开，宋父温其传补后仕钱俶，不提前判官任期。'}
assert not (P/'publication.json').exists()
for n in range(11,19):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=945,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(11,19)],next_paragraph=Q[19]['id'],next_volume=285,next_year=945,supplements=supplements,excluded_non_body=[],coverage='卷285原16—23行连续第11—18段，九月至十一月及追述，发表后945年累计53/58段，尚余5段。',source_contexts=[dict(source_key=key,note=note) for key,note in [(main_sources[0],'只录11—16段；之前与之后原文留档不重复。'),(main_sources[1],'只录17—18段吴越事件，不把之后十二月和946标题正文提前。'),(hy,'只取刘思潮等五人及王翻途中死，未提前陈道庠邓伸未来记事。'),(mi,'只补王延政族迁金陵，不提前鄱阳王；该书946纪年异说沿用。'),(kg,'王建死与王武继位纪年独立列，未来王武卒与王昭立等不提前录。'),(sw,'补同地父名和后仕钱俶，未建其子整篇传记事件。')]],source_issues_review='何昌延廷同组成员异文待纸本；南汉被杀四名与新五人、王翷左右仆射、新史迁族946与主945异说并列。高丽王建死亡与告丧册命分别，死亡纪年待扩展校核。现代姓名译法与坐标未凭外部记忆补入。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,19)],plain_language_review='首次逐项阅读标题、介绍、事件、参与、关系与事实说明，简体白话且主语明确。诬告逼供、未执行计划、过去追述、实际处罚和后续政治效果分开；原文逐字保留。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
