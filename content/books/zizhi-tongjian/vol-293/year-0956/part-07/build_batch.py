# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 293, year 956 paragraphs 49–57."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,58))
COMMIT='46f543ceeb3df4fc512bb882ee567e6a76892890'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]

for key in ['tongjian-293-956-hunan-yangzhou-withdrawal','jiuwudaishi-116-october-956']:
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
main_sources = ['tongjian-293-956-hunan-yangzhou-withdrawal','tongjian-293-956-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v293-y0956-p049-p057',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    author={'hanshu-001-changling-burial':'班固等','houhanshu-002-yuanling-burial':'范晔等'}.get(key,author)
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
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
lines = (ROOT / 'resources/derived/tongjian/293.txt').read_text().splitlines()
for n in range(49, 58):
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if key in prior_source_registry}, []

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
    labels={'tongjian-291-954-february-march':'卷291·显德元年正月至三月','jiuwudaishi-114-february-954':'卷114·世宗本纪一·显德元年二月','jiuwudaishi-114-march-orders-954':'卷114·世宗本纪一·显德元年三月出军诏','jiuwudaishi-114-campaign-march-954':'卷114·世宗本纪一·显德元年三月亲征','xinwudaishi-64-ansiqian-killed':'卷64·后蜀世家第四·安思谦与王藻','songshi-488-changji-changwen':'卷488·外国四·交阯吴氏继位'}
    labels.update({'songshi-262-zan-jurun-identity':'卷262·昝居润传（电子总题名待校）','songshi-262-zan-jurun-qinfeng':'卷262·昝居润传·秦凤行营'})
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷293·显德三年（956年十月至年末及相关追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_293_0956_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'马在贵':'南唐楚州将领。956年四月在湾头堰被韩令坤击败，《旧五代史》记其所领万余众，未记其本人最后结局。生卒年未载。',
'王环（后蜀凤州节度使）':'镇州真定人，早年以勇力为孟知祥御者，后掌后蜀宿卫。开运末秦凤等地入蜀后，孟昶任其为凤州节度使。955年十一月凤州陷落时被后周军俘获。与914—929年楚水军将领王环分别保存，无同人证据。生卒年未载。','王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
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

def event(code, title, n, quote, actors, when=None, note='', year=956, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='956年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_293_0956_' + code
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
        edge = 'participation_zztj_293_0956_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_293_0956_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 if kw.get('source'):
  t=(sources[kw['source']]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);quote=t[a:b]
 else:quote=span(n,start,end)
 E[code]=event(code,title,n,quote,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)












ALIASES.update({'帝':'柴荣','上':'柴荣','太祖皇帝':'赵匡胤','唐主':'李璟','契丹主':'耶律璟','弘亻叔':'钱弘俶'})
NEW_ALIASES={'陈抟':['陳摶'],'陈处尧':['陳處堯'],'赵季文':['趙季文']}
NEW_DESCRIPTIONS={'陈抟':'真源人，华山隐士。956年应柴荣召见，劝皇帝以治理天下为务，不必求飞升与炼金术，获准还山。《宋史》另记其辞谢谏议大夫任命。生卒年本段未载。','陈处尧':'南唐兵部郎中。956年李璟派其携厚礼渡海向契丹求援，契丹没有出兵，并将他留住。他后来多次当面指责契丹君主而未受处罚，具体日期未载。','赵季文':'后蜀弓箭库使。956年平定陵、荣二州史书称为獠的群体叛乱。具体战斗日期、个人籍贯与生卒年未载。'}
nov='jiuwudaishi-116-november-956';dec='jiuwudaishi-116-december-956';oct='jiuwudaishi-116-october-956';song='songshi-457-chentuan-956'
add('zhaokuangyin_dingguo_command','柴荣任赵匡胤为定国节度使、殿前都指挥使',49,'甲申，','兼殿前都指挥使。',[('帝','授赵匡胤节度与殿前指挥职务'),('太祖皇帝','获任定国节度使、殿前都指挥使')],when='956年十月甲申',place='后周朝廷',note='这里的太祖皇帝是《通鉴》对后来宋太祖赵匡胤的称呼，不指已故周太祖郭威。')
sup('zhaokuangyin_dingguo_command',49,oct,'甲申，宣授今上同州節度使兼殿前都指揮使，','《旧五代史》同记十月甲申授赵匡胤同州节度使、殿前都指挥使。','今上是该书对宋太祖赵匡胤的称呼；两书分别保留军号定国与治所同州的称法。')
add('zhaokuangyin_recommends_zhaopu','赵匡胤推荐赵普为节度推官',49,'太祖皇帝表',None,[('太祖皇帝','上表推荐赵普'),('赵普','以渭州军事判官身份被推荐为节度推官')],when='956年十月赵匡胤获任定国节度使条所记，推荐日未独载',place='渭州至节度幕府',note='表是推荐，不凭本句断言另有已完成任命诏或到任日期。')
add('zhang_reports_lichongjin_disloyal','张永德密报李重进有二心，柴荣不信',50,'张永德与李重进','帝不之信。',[('张永德','因与李重进不和，秘密指控其不忠'),('李重进','遭张永德怀疑指控'),('帝','不相信这项指控')],when='956年十月条之后、十一月条之前，具体日未载',place='后周军营及朝廷',description='张永德与李重进不和，秘密上表说李重进有二心，柴荣没有相信。指控本身有记载，但不能因此把李重进记为已证实谋反。')
add('lichongjin_visits_zhang_camp','李重进单骑到张永德营中宴谈，化解猜疑',50,'时二将','众心亦安。',[('李重进','单骑赴营，宴饮时劝张永德不要互相疑忌'),('张永德','与李重进宴谈后解除疑虑')],when='956年两将猜疑之后，具体日未载',place='张永德军营',description='两将各拥重兵，史书称众人担忧。李重进单骑来到张永德营中，从容宴饮，指出两人都是皇室至亲，不应互疑，张永德因此释疑，众心也安。肺腑指皇室亲近关系，不据这句话新建两人血缘或结义关系。')
add('lij ing_wax_letter'.replace(' ',''),'李璟以蜡书诱李重进，李重进将书呈报柴荣',50,'唐主闻之，',None,[('唐主','用厚利与反间言辞写信诱李重进'),('李重进','将收到的蜡书呈报')],when='956年两将关系缓和之后、孙晟被杀之前，具体日未载',place='南唐至后周军营',description='李璟得知两将情况，以蜡书许厚利诱李重进，书中有谤毁与反间言辞。李重进将书上奏，不能把收信等同接受诱约或已与南唐结盟。')
add('sunzhong_retained_daliang','柴荣厚待留在大梁的孙晟、钟谟，询问南唐情况',51,'初，','事陛下无二心。”',[('帝','在大梁接待留使，并询问南唐情况'),('孙晟','称李璟畏惧柴荣神武、无二心'),('钟谟','与孙晟一同留在大梁')],year=None,when='956年十一月杀孙晟之前的接待过程，各次召见年月未载',place='大梁',note='初为追述多次接待，孙晟回答是使者的说辞，不当李璟内心无二的确证。')
add('sunsheng_refuses_disclosure','柴荣因南唐蜡书责问孙晟，孙晟拒说军政虚实',51,'及得唐蜡书，','默不对。',[('帝','因蜡书责问使者此前说辞'),('孙晟','抗辞请死，拒答南唐虚实')],when='956年十一月乙巳处刑以前，具体责问日未载',place='后周朝廷')
add('sunsheng_executed','柴荣命曹翰再问孙晟，孙晟拒答后被处死',51,'十一月，乙巳，','乃就刑。',[('帝','下令再问并处死孙晟'),('曹翰','送孙晟到右军巡院，饮谈问讯后传达死命'),('孙晟','始终拒答，整衣冠南向拜后就刑')],when='956年十一月乙巳',place='大梁右军巡院',note='请死与实际处刑分开；临刑言辞是史书记载，不扩充其未说出的动机。')
sup('sunsheng_executed',51,nov,'乙巳，江南進奉使孫晟下獄死，','《旧五代史》同记十一月乙巳孙晟下狱死。','该书简记结果，没有复述曹翰问讯和临刑对白，不把省略视为否定。')
claim('person',people['孙晟'],'death_year','孙晟于956年十一月乙巳在后周被处死。',51,span(51,'十一月，乙巳，','乃就刑。'),'作为带出处的死亡事实，不覆写已有生平档案。')
add('sunsheng_followers_killed','孙晟的百余名随从也被杀',51,'并从者百馀人','皆杀之，',[('帝','命令处死孙晟后，其百余随从也被杀')],when='956年十一月孙晟被杀时',place='后周，随从处刑具体场所未载',note='百余是史载概数，随从未具名，不造精确人数名单，也不强定均死于右军巡院。')
add('zhongmo_demoted','钟谟被贬为耀州司马',51,'贬钟谟','耀州司马。',[('钟谟','在孙晟被杀后遭贬耀州司马')],when='956年十一月孙晟被杀条所记',place='耀州')
sup('zhongmo_demoted',51,nov,'江南進奉使鐘謨責授耀州司馬。','《旧五代史》同记钟谟被贬耀州司马。','同条乙巳下记，但主书没有给独立到任日。')
add('zhongmo_recalled','柴荣后悔杀孙晟，召钟谟并任卫尉少卿',51,'既而帝怜晟',None,[('帝','感念孙晟忠节，后悔杀使，召回钟谟授官'),('钟谟','被召回获任卫尉少卿')],year=None,when='956年十一月杀孙晟之后，具体召回授官年日未载',place='耀州至后周朝廷',note='既而只有先后，不为回召硬定乙巳或当年当天。')
add('chentuan_counsels_governance','陈抟劝柴荣治理天下，不要求飞升与炼金术',52,'帝召华山','安用此为！”',[('帝','召见华山隐士，询问飞升与黄白术'),('陈抟','劝皇帝以治理天下为务')],when='956年十一月戊申遣还以前，具体召见日未载',place='华山至后周朝廷',note='黄白之术指炼金银等术，不作为实际炼成金银或飞升事实。')
sup('chentuan_counsels_governance',52,song,'周世宗好黃白術，有以摶名聞者，顯德三年，命華州送至闕下。留止禁中月餘，從容問其術，摶對曰：「陛下為四海之主，當以致治為念，奈何留意黃白之事乎？」','《宋史》记显德三年召陈抟到朝廷、留禁中月余，并载其劝柴荣重治理轻黄白术。','留月余为召见过程的持续时间，不从遣还日倒推出精确起日。')
add('chentuan_declines_office','陈抟拒绝柴荣所授谏议大夫',52,'世宗不之責，','固辭不受。',[('帝','没有责罚陈抟，命其为谏议大夫'),('陈抟','坚辞谏议大夫任命')],source=song,when='《宋史》显德三年（956年）召见期间，具体日未载',place='后周朝廷',note='此事为《宋史》独立补充；任命提出与本人接受分开，未记已经到任。')
add('chentuan_returns_mountain','柴荣放陈抟还山，命地方长官经常问候',52,'戊申，',None,[('帝','放隐士还山并令长官存问'),('陈抟','获准返回山中')],when='956年十一月戊申',place='后周朝廷至华山')
sup('chentuan_returns_mountain',52,nov,'戊申，放華山隱者陳摶歸山。帝素聞摶有道術，征之赴闕，月餘放還舊隱。','《旧五代史》同记十一月戊申放陈抟还山。','道术是柴荣此前所闻，不作为炼金成功的科学事实。')
sup('chentuan_returns_mountain',52,song,'既知其無他術，放還所止，詔本州長吏歲時存問。','《宋史》也记放还陈抟并命地方长官定时问候。','不同文字的问候频率分别保留，不编造已发生的每次问候。')
add('zhangyongde_inspector_general','柴荣任张永德为殿前都点检',53,Q[53]['text'],None,[('帝','任命张永德'),('张永德','获任殿前都点检')],when='956年十二月壬申',place='后周朝廷')
sup('zhangyongde_inspector_general',53,dec,'壬申，以滑州節度使兼殿前都指揮使、駙馬都尉張永德為殿前都點校。','《旧五代史》同日记张永德升任殿前都点校，并列此前职衔。','原文字为点校，与《通鉴》点检称法并列，不静默改引文。')
add('xiacai_wall_labor','后周征发多州数万丁夫修筑下蔡城',54,Q[54]['text'],None,[],when='956年十二月条所记，具体征发日未载',place='陈、蔡、宋、亳、颍、兖、曹、单等州至下蔡',description='后周分派宦官征发陈、蔡、宋、亳、颍、兖、曹、单等州数万丁夫，在下蔡筑城。人数是概数，宦官未具名，不补具体征发名单或竣工日期。')
sup('xiacai_wall_labor',54,dec,'發陳、蔡、宋、亳、潁、曹、單等州丁夫城下蔡。','《旧五代史》也记从多州征发丁夫筑下蔡城。','该书所列州少兖，且无数万数字；按各书分别保留，不把省略当成相反的精确人数。')
add('lij ing_stops_harmful_farming'.replace(' ',''),'李璟下令停止淮南最害民的营田',55,'是岁，','罢之。',[('唐主','命停止淮南营田中对民众危害尤其重者')],when='956年，具体月日未载',place='淮南',note='害民尤甚者是选择性停止，不能解释成南唐所有营田或全部税收取消。')
add('chenchuyao_seeks_liao_aid','李璟派陈处尧渡海向契丹求兵',55,'遣兵部郎中','乞兵。',[('唐主','派兵部郎中携厚礼求援'),('陈处尧','携厚礼渡海向契丹求兵')],when='956年，具体出使月日未载',place='南唐至契丹',note='遣使求援不等结盟成功或契丹已经派兵，重币未记金额。')
add('liao_detains_chenchuyao','契丹没有为南唐出兵，并留住陈处尧',55,'契丹不能','不遣。',[('陈处尧','求援未成且被契丹留住')],when='956年出使求援之后，具体留置日未载',place='契丹',note='不能为之出兵是史载结果，不擅填拒援原因或具名拘禁执行者。')
add('chenchuyao_rebukes_liao_ruler','陈处尧久留后多次当面责问契丹君主，未被治罪',55,'处尧刚直',None,[('陈处尧','因久留忿怼，多次当面指责契丹君主'),('契丹主','没有因这些责问治罪陈处尧')],year=None,when='956年出使后久留期间，具体各次责问年日未载',place='契丹',note='久之跨时概述，不把各次责问固定在956年；刚直口辩为史家评价，未造具体言辞。')
add('zhaojiwen_suppresses_lingrong','赵季文平定后蜀陵、荣二州叛乱',56,Q[56]['text'],None,[('赵季文','以弓箭库使身份领军平叛')],when='956年年末总记，具体战日未载',place='后蜀陵州、荣州',note='獠为史书对当地群体的称谓，不据此确定现代民族；叛军姓名人数未载。')
add('qianhongyi_stops_disruptive_levy','钱弘亿劝谏后，钱弘俶停止扰民征括',57,Q[57]['text'],None,[('弘亻叔','进行扰民征括，收到劝谏后停止'),('钱弘亿','以判明州身份上手疏切谏')],when='956年年末总记，具体日未载',place='吴越及明州',description='《通鉴》记吴越王钱弘俶征括境内，给民众造成很多劳扰，判明州钱弘亿亲笔上疏切谏，征括随后停止。底本文字“民捕”的具体对象尚待校核，因此这里不擅写成征民船、捕鱼或捕人。',note='弘亻叔按吴越在位君主身份复用钱弘俶，字形异常保留原引文；民捕未校，不补征括具体对象。')
reviews={49:'太祖皇帝为赵匡胤，不是郭威；定国军号与旧史同州称法并存，赵普上表推荐不当作独立到任证。',50:'密报二心是张永德指控，柴荣不信；单骑解疑与蜡书诱约、呈报分阶段，肺腑不创建二将血缘关系。',51:'初为旧接待，问讯拒答、十一月乙巳处刑与百余随从杀、钟谟贬逐和后来召授拆开。既而召回日期不明留null，孙晟的忠节评价标源。',52:'飞升黄白术是问询，不认可神术为事实；宋补授谏议而拒，留月余不算起日。戊申放还旧史同日，宋958赐茶帛留待后年。',53:'十二月壬申授职，点校与点检字样各保原文。',54:'多州数万丁夫为概数，城是筑城动作，不写竣工日；旧史少列兖保留差别。',55:'停最害民营田不是全部废除，求援与未出兵留使分开，久之责问年不明留null；反间与外援意图不当成功事实。',56:'獠保留史称，现代民族、战日和人数未载，不补。',57:'弘亻叔按在位者钱弘俶识别，民捕异常字不擅改民船，不确定征括具体对象；钱弘亿劝谏及停止可确定。'}
assert not (P/'publication.json').exists()
for n in range(49,58):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=293,year=956,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(49,58)],next_paragraph='zztj-v293-y0957-p001',next_volume=293,next_year=957,supplements=supplements,excluded_non_body=[],coverage='原54—62行最后九段；956年跨卷审计通过后才记整年完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(49,58)],source_issues_review='弘亻叔字形异常按身份识别钱弘俶；民捕对象待校，引用原保，不擅改民船。殿前都点校与点检各保本字。接待与久留追述不强定本年，纸本及异文待核。',plain_language_review='首次逐条检查标题人物、事件角色和事实解释。指控、劝谏、神术传闻、求援与实际行动分清；匿名随从丁夫不造名单，未知日留空，内部简称不展示，原文按快照逐字核验。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
