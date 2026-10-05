# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 289, year 950 paragraphs 36–42."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,84))
COMMIT='197cc3dbf958eccdbfaf129b605c39322b104431'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-289-950-intercalary-month','xinwudaishi-066-pushezhou','xinwudaishi-062-chen-hui-later']:
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
main_sources = ['tongjian-289-950-intercalary-month','tongjian-289-950-november-start']
B = {'format_version': 1, 'batch_key': 'zztj-v289-y0950-p036-p042',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
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
lines = (ROOT / 'resources/derived/tongjian/289.txt').read_text().splitlines()
for n in range(36, 43):
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
    for a,b in [('主書','《资治通鉴》'),('補','补'),('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-103-november-950':'卷103·隐帝本纪·乾祐三年十一月','jiuwudaishi-124-wang-yin-origin':'卷124·王殷传·籍贯与驻澶州','tongjian-289-950-november-start':'卷289·乾祐三年·十月至十一月','xinwudaishi-064-shu-royal-titles':'卷64·后蜀世家·王室册封','jiuwudaishi-086-jin-empress-exile':'卷86·高祖皇后李氏·流放及病逝的引书注文','jiuwudaishi-103-september-950':'卷103·隐帝本纪·乾祐三年九月','jiuwudaishi-103-october-950':'卷103·隐帝本纪·乾祐三年十月'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷289·乾祐三年（950年十月至十一月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_289_0950_06_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=globals().get("NEW_BIRTH_YEARS",{}).get(name),death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=950, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='950年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_289_0950_' + code
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
        edge = 'participation_zztj_289_0950_' + code + '_' + pk
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
    a=ALIASES.get(a,a); b=ALIASES.get(b,b)
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'史书记{a}是{b}的{kind}',quote,source=source)
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
        row=dict(key=f'relationship_zztj_289_0950_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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






ALIASES.update({'帝':'刘承祐','蜀主':'孟昶','唐主':'李璟','吴越王':'钱弘俶','希广':'马希广','希萼':'马希萼','希崇':'马希崇','彦瑫':'刘彦瑫','硃进忠':'朱进忠','张晖':'张晖（马希广将）','王殷':'王殷（后汉后周将）'})
NEW_ALIASES={'张晖（马希广将）':[],'朱进忠':['硃进忠','朱進忠'],'孟骈':['孟駢'],'马光赞':['馬光贊'],'王殷（后汉后周将）':[]}
NEW_DESCRIPTIONS={
'张晖（马希广将）':'马希广的马军指挥使。950年从另一条路线攻朗州，得知刘彦瑫战败后驻益阳；遭进攻时骗部下留城，自己逃回长沙。与博州守将、后晋使者等同名人物尚无同人证据，分开建档。生卒年未载。',
'朱进忠':'马希萼的指挥使。950年率兵三千攻益阳，随后建议马希萼亲自率军攻潭州。电子底本也写硃进忠，统一简体姓名，原文保留。生卒年未载。',
'孟骈':'马希广的僚属。950年奉命劝马希萼不要向南唐称臣，遭到处死威胁，申说两军交战仍应允许使者往来后获释。生卒年未载。',
'马光赞':'马希萼的儿子。950年十一月，马希萼率军向长沙进发，留下他守朗州。生卒年和母亲身份未载。',
'王殷（后汉后周将）':'瀛州籍将领。950年以侍卫步军都指挥使身份奉命驻澶州防备契丹，后来参与后周建国。《旧五代史》记他自称出生在魏州开元寺，籍贯与出生地分开。与晚唐后梁同名王殷分开建档，生卒年本批未录。'}
new='jiuwudaishi-103-november-950';origin='jiuwudaishi-124-wang-yin-origin';chu='xinwudaishi-066-pushezhou';tang='xinwudaishi-062-chen-hui-later'
add('liu_yantao_proposes_lang','刘彦瑫请求率水陆军直攻朗州',36,'刘彦瑫言于希广曰：','以解大王之忧。”',[('刘彦瑫','请求万余兵与一百五十艘战舰，计划攻朗州擒马希萼'),('马希广','听取直攻朗州的建议')],when='950年十月条下，具体进言日未载',place='楚国朝廷',description='刘彦瑫向马希广声称朗州兵力不足，楚国都府兵力占优，请给他万余兵和一百五十艘战舰，直攻朗州、擒取马希萼。',note='兵不满万、马不满千和都府十万是进言中的估计，不当作独立核实的兵力普查；请求数量不等于实际全部发给。')
add('liu_yantao_command_lang','马希广任命刘彦瑫统率攻朗州的军队',36,'王悦，','朗州行营都统。',[('马希广','任命刘彦瑫为战棹都指挥使、朗州行营都统'),('刘彦瑫','获任两项指挥职务')],when='950年十月条下，进言之后，具体任命日未载',place='楚国朝廷')
add('lang_locals_reward_block','朗州父老犒劳刘彦瑫军队，随后用竹木断其归路',36,'彦瑫入朗州境，','以断其后。',[('刘彦瑫','进入朗州，重赏前来犒军的父老')],when='950年十月条下，刘彦瑫进军朗州时，具体日未载',place='朗州境内水路',description='朗州父老带牛酒犒军，声称盼望都府军队已久，刘彦瑫重赏他们。战舰经过后，史书记这些父老运竹木截断军队后路。',note='父老的话不当作全体百姓民意调查；原文未明说马希萼预先安排的诈降，未补幕后策划人。')
add('ma_xie_intercepts_mei','马希萼派六千兵与百艘战舰在湄州迎战',36,'是日，','逆战于湄州。',[('马希萼','派朗州兵与相关各族军队迎战')],when='950年十月条下，刘彦瑫进军当天，具体日期未载',place='湄州',note='六千兵与百艘战舰是书载数量，不补实际将领；是日未有干支，不虚构公历日期。')
add('liu_yantao_fire_defeat','刘彦瑫在湄州火攻遇风向改变，败退时归路被断',36,'彦瑫乘风','士卒战及溺死者数千人。',[('刘彦瑫','火攻遇风向逆转，自军起火，败退时水路已断')],when='950年十月条下，湄州交战当天，具体日期未载',place='湄州及退军水路',description='刘彦瑫顺风放火烧敌方战舰，风向很快改变，火反烧己方。他退军时江路已经被截断，史书称数千士卒战死或溺死。',note='数千为概数，战死与溺死合计，不写成全数溺死；不造精确人数或风向。')
sup('liu_yantao_fire_defeat',36,chu,'劉彥瑫以舟兵趨武陵，攻希萼。彥瑫敗於湄洲，','《新五代史》也记刘彦瑫率舟兵攻武陵，在湄洲战败。','湄州与湄洲原字保留；传记未单列年月，也没有说明火攻风向和伤亡，不能作为细节的独立确证。')
add('ma_xiguang_rewards_after_defeat','马希广得知战败后哭泣，大量赏赐金帛给士卒',36,'希广闻之，','取悦于士卒。',[('马希广','得知败讯后哭泣，并增加给士卒的赏赐')],when='950年十月条下，湄州败讯传到以后，具体日未载',place='长沙',note='平日罕赏为史书背景概述，不另造一场早年事件；本句没有赏赐数额或效果。')
add('ma_xiguang_refuses_kill_xichong','有人告马希崇煽动谋反，马希广拒绝杀弟',36,'或告天策左司马','何以见先王于地下！”',[('马希广','拒绝杀死被人指控谋反的弟弟'),('马希崇','被未具名的人指控散布流言、谋反')],when='950年十月条下，具体指控与答复日未载',place='楚国朝廷',description='有人向马希广指控天策左司马马希崇散布流言、谋反迹象明显，请求杀他。马希广说自己若害死弟弟，无法面对已故父亲，因此拒绝。',note='反状已明为指控者的说法，不将本句直接当独立证实；未具名者不创建人物，未把地下见父写成真实行为。')
add('zhang_hui_retreats_yiyang','张晖从另一条路攻朗州，闻刘彦瑫战败后退守益阳',37,'马军指挥使张晖','退屯益阳。',[('张晖','攻至龙阳，闻败后退屯益阳')],when='950年十月条下，湄州战败后，具体日未载',place='龙阳、益阳',note='以楚马军指挥使身份单独识别，未据姓名合并博州守将或后晋使者。')
add('zhu_jinzhong_attacks_yiyang','马希萼派朱进忠等率三千兵急攻益阳',37,'希萼又遣','急攻益阳，',[('马希萼','派朱进忠等进攻益阳'),('硃进忠','率三千兵急攻益阳')],when='950年十月条下，张晖退屯益阳后，具体日未载',place='益阳',note='等所指其他将领未具名，不补人物；兵数为书载。')
add('zhang_hui_deceives_flees','张晖谎称出城夹击敌军，实际逃回长沙',37,'张晖绐其众曰：','遁归长沙。',[('张晖','骗部下留城，自己经竹头市逃回长沙')],when='950年十月条下，益阳遭攻时，具体日未载',place='益阳、竹头市、长沙',note='拟出敌后夹攻是欺骗部下的说辞，未作为实际战术执行；原文没有逃归随行人数。')
add('lang_troops_take_yiyang','朗州军攻破无人主事的益阳，史书称九千余士卒死亡',37,'朗兵知城中无主，',None,[],when='950年十月条下，张晖逃离之后，具体日未载',place='益阳',note='士卒九千余为书载概数，不扩成平民死亡或精确人数；无主指缺少主将，不说城中空无一人。')
# Add a fresh original citation to the already published release, without repeating its participants.
release_key='event_zztj_289_0950_qian_releases_zha'
release=next(x for f in (ROOT/'content').rglob('content-batch.json') if f.parent!=P for x in json.loads(f.read_text())['events'] if x['key']==release_key)
B['events'].append(dict(release,status='draft'));reused.add(release_key);used.setdefault(38,[]).append(release_key)
claim('event',release_key,'description','《资治通鉴》在十一月条之前再次记钱弘俶将查文徽送回南唐。',38,'吴越王弘亻叔归查文徽于唐，','与此前献庙释放和七月换俘关联，作为返国的后续记载，不创建第二次无证据的释放；本句没有归国确日。')
E['zha_returns']=release_key
sup('zha_returns',38,tang,'景送先進還越，越亦歸景文徽。','《新五代史》也记双方互还俘虏，吴越归还查文徽。','同一换俘背景，传记未给实际归国日期，不造新交换。')
add('zha_illness_retirement','查文徽患失语病，以工部尚书身份退休',38,'文徽得喑疾，',None,[('查文徽','患失语病后，以工部尚书身份退休')],when='950年十月条下，归南唐后，具体患病与退休日未载',place='南唐',note='喑疾按失语理解，不诊断现代具体病因；以工部尚书致仕不另造本句未明说的实任尚书上任。')
add('november_eclipse','史书记950年十一月甲子朔发生日食',39,'十一月，',None,[],when='950年十一月甲子朔',place='后汉纪年记载，观测地点未载',note='记载日食，未进行天文反算，不补食分或全球可见区域；朔为该月初一。')
sup('november_eclipse',39,new,'十一月甲子朔，日有食之。','《旧五代史》同样记十一月甲子朔日食。','同一纪日文字，不作为现代天文计算。')
add('zhao_tingyin_death','后蜀太师、中书令宋忠武王赵廷隐去世',40,'蜀太师、',None,[('赵廷隐','以所载太师、中书令、宋忠武王身份去世')],when='950年十一月条下，具体死亡日未载',place='后蜀',note='本句未单列日，不把上一句日食甲子直接套死亡日；忠武为谥称，未造生前获谥。')
claim('person',people['赵廷隐'],'death_year','《资治通鉴》在950年十一月条下记赵廷隐去世。',40,Q[40]['text'],'为既有赵廷隐补充死亡出处，不改写旧人物档案或猜测确日。')
add('meng_pian_warns_ma','马希广派孟骈劝马希萼不要向南唐称臣',41,'楚王希广遣','何异袁谭求救于曹公邪！”',[('马希广','派孟骈向马希萼劝说'),('孟骈','以父兄旧仇与历史类比劝阻向南唐称臣'),('马希萼','受到孟骈劝说')],when='950年十一月条下，辛未出兵之前，具体出使日未载',place='楚、朗州',note='袁谭曹公是使者的比喻，不将古人加入950年事件；父兄之仇为劝说理由，本句不足独立重建早期仇怨事件。')
add('ma_xie_threatens_meng','马希萼欲杀孟骈，听其申辩后释放',41,'希萼将斩之，','乃释之，',[('马希萼','威胁处死使者，听其申辩后释放'),('孟骈','申说交战期间使者仍应往来，随后获释')],when='950年十一月条下，孟骈出使期间，具体日未载',place='朗州',note='将斩是意图，实际结果为释放，不能建立孟骈死亡事件。')
add('ma_xie_breaks_brother','马希萼让孟骈传话，宣布与马希广断绝情义',41,'使还报曰：','非地下不相见也！”',[('马希萼','命孟骈把决裂的话带回'),('孟骈','带回马希萼的答复'),('马希广','成为决裂答复的对象')],when='950年十一月条下，孟骈获释之后，具体日未载',place='朗州至长沙',note='地下不相见是决裂话语，不是两人实际见面、死亡或幽冥事件。')
add('zhu_urges_ma_lead','朱进忠建议马希萼亲自率军攻潭州',41,'硃进忠请','自将兵取潭州，',[('硃进忠','建议马希萼亲自率兵攻潭州'),('马希萼','听取亲征建议')],when='950年十一月辛未出兵之前，具体进言日未载',place='朗州',note='进言阶段不当作已经攻取潭州，后续出兵另录。')
add('ma_guangzan_defends_lang','马希萼留下儿子马光赞守朗州',41,'辛未，','守朗州，',[('马希萼','出征前留下儿子守朗州'),('马光赞','受命留守朗州')],when='950年十一月辛未',place='朗州',note='光赞为希萼之子，不指马希广之子；未给守军兵数。')
relationship('马希萼','马光赞','父亲',41,'希萼留其子光赞守朗州，','其子直接指马希萼的儿子，方向为马希萼是马光赞的父亲；母亲身份与出生年未载。')
add('ma_xie_marches_changsha','马希萼发兵向长沙进军，自称顺天王',41,'悉发境内之兵',None,[('马希萼','发动境内军队向长沙进军，自称顺天王')],when='950年十一月辛未',place='朗州至长沙方向',note='悉发为来源概述，不填精确总兵数；趣为趋向，进军不等于本日攻占长沙。')
sup('ma_xie_marches_changsha',41,chu,'希萼舟兵沿江而上，自號「順天將軍」，','《新五代史》记马希萼舟兵沿江而上，自号顺天将军。','顺天将军与《资治通鉴》顺天王不同，保留名号异说；传记未单列十一月辛未，不能据此改主书时间。',relation='conflicts')
add('wang_yin_tun_chan','刘承祐命王殷率兵驻澶州防备契丹',42,'诏侍卫步军',None,[('帝','下诏派王殷驻兵澶州防备契丹'),('王殷','以侍卫步军都指挥使、宁江节度使身份奉命驻澶州')],when='950年十一月条下，《旧五代史》记辛未',place='澶州',note='本句没有单列日，旧本纪明确辛未作为补证；防备不等于本段已有具体交战。王殷沿瀛州、侍卫军职和旧传经历识别，与晚唐后梁同名人分开。')
sup('wang_yin_tun_chan',42,new,'辛未，詔侍衛步軍都指揮使王殷將兵屯澶州。','《旧五代史》将王殷驻澶州的命令明确系于十一月辛未。','补充确切纪日，不把上一段楚国辛未自动移给所有相邻事件。',relation='adds',field='time_original')
sup('wang_yin_tun_chan',42,origin,'乾祐末，遷侍衛步軍都指揮使，領夔州節度使，會契丹寇邊，遣殷領兵屯澶州。','《旧五代史》王殷传也记乾祐末奉命屯澶州，但兼领节度使写夔州。','传记夔州与《资治通鉴》宁江的官号差异保留，不创造另一个同名将领或猜测官号改授日。',relation='conflicts')
claim('person',people['王殷（后汉后周将）'],'description','《旧五代史》记王殷籍贯为瀛州。',42,'王殷，瀛州人。','与主书瀛州籍贯对应，后述出生地另有原文；祖籍、籍贯与出生地不混写。',source=origin)
claim('person',people['王殷（后汉后周将）'],'description','《旧五代史》记王殷自称出生于魏州开元寺。',42,'殷自言生於魏州之開元寺，','自言为传记转述，不补生日或出生年；不据此将瀛州籍贯改作魏州。',source=origin)
reviews={36:'进言中的兵力比较与请求数量是话语，不等于核实军力或已获配额；火攻失利、归路截断和战溺合计按原文，父老犒军不是全体民意。马希崇谋反是指控者话语，不当作此句独立确证。',37:'张晖按楚马军指挥使单独建档，不并博州守将或晋使者。谎称夹击与实际逃归分开，九千余为史书记士卒死亡概数，不扩成平民人数。',38:'归查文徽关联已发布换俘释放事件，追加返国引用而不重复建事件。喑疾不诊断现代病名，工部尚书致仕不补实任日期。',39:'十一月甲子朔日食有旧本纪对应，未做现代天文反算。',40:'赵廷隐死亡年新增事实引用，未知确日不套前段甲子，不覆盖旧人物档案；宋忠武王为书中称号，不造生前获谥。',41:'使者话语、欲杀与实际释归、决裂宣言、亲征建议、留子守城、辛未进军依次录。光赞父亲是希萼；顺天王与新史顺天将军名号差异保留，未提前写长沙失陷。',42:'后汉后周王殷与晚唐后梁同名人分档，籍贯瀛州与自言生魏州开元寺分别记。旧本纪辛未补纪日，旧传夔州节度使与主书宁江官号差异保留。'}
assert not (P/'publication.json').exists()
for n in range(36,43):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=289,year=950,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(36,43)],next_paragraph=Q[43]['id'],next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷289原41—47行连续七段；发布后首42/83正文已录，余41段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(36,43)],source_issues_review='新五代史湄洲与通鉴湄州原字保留，顺天将军与顺天王名号不同；旧五代史王殷传夔州与通鉴宁江官号差异保留。赵廷隐死记回查新旧史未找到足以独立补具体日期的对应句，未强补。纸本与转录异文待核。',plain_language_review='首次逐条核对标题、人物、事件、角色、关系方向、时间地点与引用说明，展示现代白话，引用保持原字；请求、指控与实际结果分开，不用简略史书代称作展示主语。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
