# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 942 paragraphs 15–26."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,41))
specs=[(d.name,d,'03f32f35d226d0f16dc68b58596ef35b6835b720','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-942-may']:
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
main_sources = ['tongjian-283-942-may']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0942-p015-p026',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-080-942-shi-death':'卷80·晋高祖本纪·天福七年六月','jiuwudaishi-081-942-july':'卷81·晋少帝本纪·天福七年七月','xinwudaishi-009-942-succession':'卷9·晋本纪·天福七年','xinwudaishi-017-chongrui-succession':'卷17·晋家人传·石重睿','xinwudaishi-062-song-hongzhou':'卷62·南唐世家·宋齐丘出镇'}
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
lines = (ROOT / 'resources/derived/tongjian/283.txt').read_text().splitlines()
for n in range(15, 27):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-080-942-shi-death':'卷80·晋高祖本纪·天福七年六月','jiuwudaishi-081-942-july':'卷81·晋少帝本纪·天福七年七月','xinwudaishi-009-942-succession':'卷9·晋本纪·天福七年','xinwudaishi-017-chongrui-succession':'卷17·晋家人传·石重睿','xinwudaishi-062-song-hongzhou':'卷62·南唐世家·宋齐丘出镇'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '五月至七月条下及追述'
        citation = f'卷283·后晋天福七年（942；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0942_03_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=942, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='942年年初条下，具体日期未载'
    key = 'event_zztj_283_0942_' + code
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
        edge = 'participation_zztj_283_0942_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0942_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

ALIASES.update({'唐主':'李昪','寿王景遂':'徐景遂','景遂':'徐景遂','重睿':'石重睿','重贵':'石重贵','曦':'王延羲','延政':'王延政','刘太后':'刘氏（石敬瑭太妃）','皇后':'永宁公主（石敬瑭妻）'})
NEW_DESCRIPTIONS={
'石重睿':'石敬瑭的幼子。942年石敬瑭病中让他拜见冯道，并由宦者抱入冯道怀中；史书解释为托付之意。石敬瑭去世后，大臣以多事为由拥立石重贵，石重睿未能继位。生卒年未载。',
'林守亮':'闽国将领。942年受王延羲派遣进入尤溪，配合袭建州的计划。七月尤口战败后逃回。生卒年未载。',
'黄敬忠':'闽国大明宫使。942年屯兵尤口，准备配合袭击建州；七月丁酉听从占者所言而按兵不动，遭包洪实等水陆夹攻后被杀。出生年未载。',
'包洪实':'王延政部将。942年与陈望率水军抵御福州军，七月丁酉在尤口引兵登岸，水陆夹攻并取胜。生卒年未载。',
'陈望':'王延政部将。942年与包洪实率水军抵御福州军，七月丁酉在尤口与对方交战。生卒年未载。'}
NEW_ALIASES={'石重睿':[],'林守亮':[],'黄敬忠':['黃敬忠'],'包洪实':['包洪實'],'陈望':['陳望']}
old='jiuwudaishi-080-942-shi-death';july='jiuwudaishi-081-942-july';new='xinwudaishi-009-942-succession';family='xinwudaishi-017-chongrui-succession';song='xinwudaishi-062-song-hongzhou'
add('song_stops_court_attendance','宋齐丘卸去尚书省事务后，不再入朝拜谒',15,'唐丞相、','不复朝谒。',[('宋齐丘','卸去尚书省事务后不再入朝')],when='942年五月条下，具体日期未载',place='南唐',note='承接本年前批罢省，未造第二次辞省务。')
add('li_bian_offers_hongzhou','李昪派李景遂慰问宋齐丘，答应让他出镇洪州，宋齐丘才入朝',15,'唐主遣','始入朝。',[('唐主','派人慰问并答应让宋齐丘出镇洪州'),('寿王景遂','奉命慰问宋齐丘'),('宋齐丘','获出镇承诺后入朝')],when='942年五月条下，具体日期未载',place='南唐',note='承诺与后面丙午正式节度使任命分开；复用徐景遂稳定人物，时期称李景遂。')
add('li_bian_song_banquet_dispute','李昪与宋齐丘酒宴争执，宋齐丘承认说过君主难以共安乐',15,'唐主与之宴，','今日杀臣可矣。”',[('唐主','在宴上质问宋齐丘'),('宋齐丘','自称有功并承认曾说君主难以共安乐')],when='942年宋齐丘重新入朝后，具体日期未载',place='南唐',description='宋齐丘在酒宴上声称李昪中兴靠自己的努力。李昪反问他是否说过自己像勾践、难以共享安乐，宋齐丘承认此言，并说皇帝今日可以杀他。',note='乌喙与勾践是争执中的比喻，不当作生理诊断；杀臣可矣不是已经执行的杀人命令。')
add('li_bian_apologizes_song','李昪次日亲笔下诏向宋齐丘致歉',15,'明日，','老相怨，可乎！”',[('唐主','亲笔致歉并提及旧日交情'),('宋齐丘','收到皇帝致歉诏书')],when='942年上述酒宴的次日，具体日期未载',place='南唐',note='子嵩为宋齐丘字，诏中褊性是李昪的自述，不另建立人物。')
add('song_zhennan_governor','李昪任宋齐丘为镇南节度使',15,'丙午，',None,[('唐主','任宋齐丘为镇南节度使'),('宋齐丘','获任镇南节度使')],when='942年五月丙午',place='洪州')
sup('song_zhennan_governor',15,song,'昪僭號，未幾，齊丘以病罷相，出為洪州節度使。','《新五代史》概述宋齐丘在李昪时以病罢相，出任洪州节度使。','传记没有精确月日，罢相与主书罢尚书省职的说法有别，保留概述，不把新史全部前后叙事强定为五月丙午。',relation='adds')
add('shi_entrusts_chongrui','石敬瑭病中让石重睿拜冯道，再由宦者抱入冯道怀中',16,'帝寝疾，',None,[('石敬瑭','让幼子拜冯道并由宦者抱入冯道怀中'),('重睿','奉父命拜冯道并被抱入怀中'),('冯道','单独见病中的皇帝，接受幼子拜见')],when='942年石敬瑭病中、六月去世以前，具体日期未载',description='石敬瑭病中，冯道单独入见。皇帝让幼子石重睿出来拜冯道，又命宦者将孩子抱入冯道怀中。《资治通鉴》认为皇帝大概希望冯道辅立石重睿。',note='其意盖欲是史家解释，不写成已颁明确立储诏令或已经举行继位。')
sup('shi_entrusts_chongrui',16,family,'高祖雖不言，左右皆知其以重睿託道也。','《新五代史》记石敬瑭没有明说，但左右认为他是将石重睿托付给冯道。','仍是旁人对举动的理解，不冒称已发现明确立储诏书。')
relationship('石敬瑭','重睿','父亲',16,'帝寝疾，一旦，冯道独对。帝命幼子重睿出拜之，','幼子重睿明示石敬瑭是石重睿的父亲，方向明确。')
add('shi_jingtang_dies','石敬瑭去世',17,'六月，',None,[('石敬瑭','去世')],when='942年六月乙丑')
sup('shi_jingtang_dies',17,old,'乙丑，帝崩於保昌殿，壽五十一。','《旧五代史》补记石敬瑭死于保昌殿，享年五十一。','同日死亡的地点与史载年龄独立补充，不据年龄自行换算出生年。',relation='adds')
add('ministers_choose_chonggui','冯道与景延广认为国家多难，应立成年君主，拥立石重贵',18,'道与天平','为嗣。',[('冯道','与景延广商议拥立石重贵'),('景延广','与冯道商议拥立石重贵'),('重贵','被大臣拥立为继承人')],when='942年六月乙丑，石敬瑭去世当日',note='长君为成年君主，不凭此推出精确年龄或把拥立与父亲托孤愿望混为同一决定。')
sup('ministers_choose_chonggui',18,family,'高祖崩，晉大臣以國家多事，議立長君，而景延廣已陰許立出帝，重睿遂不得立。','《新五代史》补记景延广此前已暗中答应立石重贵，石重睿因此未能继位。','暗许的具体日期未载，补证其拥立背景，不造另一次正式即位。',relation='adds')
add('shi_chonggui_succeeds','石重贵即皇帝位',18,'是日，','即皇帝位。',[('重贵','在石敬瑭去世当日即皇帝位')],when='942年六月乙丑')
sup('shi_chonggui_succeeds',18,new,'七年六月乙丑，高祖崩，皇帝即位于柩前。','《新五代史》记石重贵在六月乙丑于灵柩前即位。','本纪传主为晋出帝石重贵，皇帝不误认已经去世的石敬瑭。')
sup('shi_chonggui_succeeds',18,old,'遺制齊王重貴於柩前即皇帝位，','《旧五代史》称遗制命齐王石重贵在柩前即位。','旧史遗制说与通鉴拥立、托幼子意图及新史评价分别保留，不据一书盖过其他记载。',relation='adds')
add('jing_controls_capital_speech','景延广自认为有拥立之功，开始掌权，禁止都下两人交谈',18,'延广以为','毋得偶语。',[('景延广','认为拥立有功，开始掌权并禁止都下百姓两人交谈')],when='942年石重贵即位后，具体日期未载',description='《资治通鉴》记景延广认为石重贵即位是自己的功劳，开始掌权，禁止都下百姓两人相互交谈。',note='偶语按双人交谈解释，不推已经发生某次具体抓捕或死刑。')
add('shi_summons_liu_advisor','石敬瑭病危时下旨召刘知远入朝辅政',19,'初，','刘知远入辅政，',[('石敬瑭','病危时召刘知远入朝辅政'),('刘知远','被召入朝辅政')],when='942年石敬瑭病危、去世以前，具体日期未载',note='初为临终追述，召令与刘知远实际入朝不同；底本河东度使漏字保留。')
add('chonggui_blocks_liu_order','石重贵压下召刘知远辅政的旨意，刘知远因此怨恨',19,'齐王寝之；',None,[('重贵','压下召刘知远辅政的旨意'),('刘知远','因召令被压下而怨恨石重贵')],when='942年石敬瑭病危时，具体日期未载',note='此时仍称齐王，行为在即位以前；史载怨恨不直接建终身敌对关系。')
add('liu_grand_empress_dowager','石重贵尊刘皇太后为太皇太后',20,'丁卯，','曰太皇太后，',[('重贵','尊刘皇太后为太皇太后'),('刘太后','获尊太皇太后')],when='942年六月丁卯',note='承接五月被尊皇太后的刘太妃，身份异说继续保留，不建立确定生母边。')
add('shi_empress_dowager','石重贵尊石敬瑭皇后为皇太后',20,'皇后',None,[('重贵','尊先帝皇后为皇太后'),('皇后','由皇后获尊皇太后')],when='942年六月丁卯',note='复用永宁公主即石敬瑭妻主体；尊号不改其稳定key，也不推出石重贵生母身份。')
add('wang_yanzheng_besieges_tingzhou','王延政围攻汀州',21,'闽富沙王','围汀州，',[('延政','以富沙王身份围攻汀州')],when='942年六月条下，具体起兵日期未载',place='汀州',note='下文七月不克而归是同次围攻的结果，不再造第二场四十二战围城。')
add('wang_yanxi_sends_tingzhou_aid','王延羲调漳州、泉州兵五千救汀州',21,'闽主曦','五千救之。',[('曦','派漳泉兵五千救援汀州')],when='942年六月汀州受围时，具体日期未载',place='汀州',note='五千为派出兵数，不补两州分摊比例。')
add('lin_enters_youxi','王延羲派林守亮进入尤溪',21,'又遣其将','入尤溪，',[('曦','派林守亮进入尤溪'),('林守亮','奉命进入尤溪')],when='942年六月条下，具体日期未载',place='尤溪')
add('huang_jingzhong_youkou','黄敬忠屯兵尤口，准备乘虚袭建州',21,'大明宫使','欲乘虚袭建州；',[('黄敬忠','屯兵尤口，准备乘虚袭击建州')],when='942年六月条下，具体日期未载',place='尤口',note='欲为计划，不写已成功攻克建州。')
add('huang_shaopo_supports_two_armies','黄绍颇率步兵八千，为两支军队声援',21,'国计使',None,[('黄绍颇','率八千步兵声援林守亮和黄敬忠军')],when='942年六月条下，具体日期未载',place='闽国',note='八千步卒与漳泉五千援汀兵分别按原文保留，不自动合并为同场一万三千人。')
add('liu_taifei_dies','太皇太后刘氏去世',22,'秋，',None,[('刘太后','去世')],when='942年七月壬辰')
sup('liu_taifei_dies',22,july,'壬辰，太皇太后劉氏崩，高祖之庶母也。','《旧五代史》同记七月壬辰刘氏去世，称她为石敬瑭庶母。','旧纪此处正文也称庶母，与五月所引注生母差异继续保留。')
sup('liu_taifei_dies',22,new,'秋七月壬辰，皇祖母劉氏崩，輟視朝三日。','《新五代史》同记刘氏七月壬辰去世，皇帝停止视朝三日。','皇祖母为石重贵朝尊称，所附生母解释属于注文，不据此建立无争议血亲。',relation='adds')
add('wang_yanzheng_leaves_tingzhou','王延政攻汀州四十二战仍未攻克，退军返回',23,'闽富沙王','不克而归。',[('延政','围攻汀州未果，退军返回')],when='942年七月条下，具体撤军日未载',place='汀州',note='四十二为史载交战次数，不拆四十二条无日期无详情战斗事件。')
add('bao_chen_command_navy','包洪实、陈望率水军抵御福州军，在尤口相遇',23,'其将包洪实、','遇于尤口。',[('包洪实','率水军抵御福州军'),('陈望','与包洪实率水军到尤口交战')],when='942年七月丁酉',place='尤口')
add('huang_waits_for_divination','黄敬忠听占者说时刻不利，按兵不动',23,'黄敬忠将战，','按兵不动；',[('黄敬忠','准备交战时因占者说时刻不利而停兵')],when='942年七月丁酉',place='尤口',note='占者未具名，时刻不利为其判断，不当作客观事实。')
add('bao_attacks_youkou','包洪实等引兵登岸，水陆夹攻，杀黄敬忠并俘斩二千',23,'洪实等引兵','俘斩二千级，',[('包洪实','引兵登岸，水陆夹攻并取胜'),('黄敬忠','在水陆夹攻中被杀')],when='942年七月丁酉',place='尤口',note='俘斩为合称，不推二千人全被杀或另加二千俘虏。陈望前句同率军明示，参与细节仍未单独推定。')
add('lin_huang_shaopo_retreat','林守亮、黄绍颇战败后逃回',23,'林守亮、',None,[('林守亮','尤口战败后逃回'),('黄绍颇','尤口战败后逃回')],when='942年七月丁酉战败后',place='闽国',note='回到何处未载，不补确切路线或私通敌军。')
add('shi_chonggui_general_pardon','石重贵颁布大赦',24,'庚子，',None,[('重贵','颁布大赦')],when='942年七月庚子',note='大赦为诏令，不意味着所有罪类无条件免除或安从进已经归降。')
sup('shi_chonggui_general_pardon',24,july,'襄州安從進如能果決輸誠，並從釋放。','《旧五代史》补记赦令称安从进如能归降，也予以释放。','如能是有条件承诺，未把安从进写成已经归降或已经被释放。',relation='adds')
add('jing_receives_chancellor_guard_title','石重贵加景延广同平章事，兼侍卫马步都指挥使',25,'癸卯，',None,[('重贵','加授景延广职衔'),('景延广','获同平章事并兼侍卫马步都指挥使')],when='942年七月癸卯')
sup('jing_receives_chancellor_guard_title',25,july,'癸卯，鄆州天平軍節度使兼侍衛馬步都虞候景延廣加特進、同中書門下平章事，充侍衛親軍都指揮使。','《旧五代史》补明景延广原任天平节度使和侍卫马步都虞候，同日加特进、同中书门下平章事，任侍卫亲军都指挥使。','同次加官的完整名号补证，不另造一次同职任命。',relation='adds')
add('feng_requests_privy_council','冯道等三次上表，请求恢复枢密使，并让出原由中书承担的职务',26,'勋旧皆欲','以枢密旧职让之；',[('冯道','与其他大臣三次上表请求恢复枢密使')],when='942年七月条下，三次上表各自日期未载',note='勋旧皆欲为史书概述，不补所有人名单；三表次数明确，但不造三次无具体日期的独立请求。')
add('shi_refuses_privy_council','石重贵拒绝恢复枢密使的请求',26,'帝',None,[('重贵','拒绝冯道等恢复枢密使的请求')],when='942年七月三次上表后，具体日期未载',note='本段帝为新即位石重贵，不误认石敬瑭。')
sup('shi_refuses_privy_council',26,july,'表凡三上，不允。','《旧五代史》同记冯道等三次上表，未获准许。','此前罢置背景只是传记解释，本批未重造过去废枢密使事件。')
claim('person',people['石敬瑭'],'death_year','石敬瑭于942年六月乙丑去世。',17,'六月，乙丑，帝殂。','死亡事实独立引用，既有主体基础字段本批不覆盖。')
claim('person',people['刘氏（石敬瑭太妃）'],'death_year','刘太皇太后于942年七月壬辰去世。',22,'秋，七月，壬辰，太皇太后刘氏殂。','沿用前批刘太妃主体，母系异说不影响同人及死亡日识别。')
for row in B['people']:
 if row['name']=='黄敬忠':
  row['death_year']=942
  claim('person',row['key'],'death_year','黄敬忠于942年七月丁酉尤口交战中被杀。',23,'洪实等引兵登岸，水陆夹攻之，杀敬忠，俘斩二千级，','本段丁酉与黄敬忠身份明确，出生年未载。')
reviews={15:'卸省不朝、派慰问与出镇承诺、宴争、次日致歉和五月丙午正式镇南任命分期；新史以病罢相出洪州为概述，职名与精确日不强行统一。',16:'幼子拜冯道抱入怀中是举动，托孤意图为史书解释，不写成已经立储诏令；石重睿父亲方向明确。',17:'六月乙丑石敬瑭死，旧纪补保昌殿及年龄，不自行换算出生年或提前山陵。',18:'冯道景延广议立成年君主、拥立和石重贵即位、景自认功掌权禁偶语分开。旧纪遗制说、新史暗许说与主书解释分别引用，不虚构统一动机。',19:'高祖病危召刘知远与齐王压下旨意为临终追述，保同年但不套即位后；底本河东度使漏字保原，不以怨恨造终身敌对。',20:'丁卯刘氏与石敬瑭妻李氏尊号分开，复用稳定主体，不推石重贵生母。',21:'汀州围城、漳泉五千援兵、林守亮入尤溪、黄敬忠屯尤口欲袭建及黄绍颇八千声援分别录，计划不写已攻克，两兵数不自动相加。',22:'七月壬辰刘氏死有新旧补证；庶母和所引注生母继续保异，皇祖母是尊称不确立无争议血缘。',23:'四十二战未克退归为前段同次围城结果，不拆无详情42次战；丁酉尤口相遇、占者话停兵、水陆攻黄死及俘斩合称、林守亮和黄绍颇逃回分别录。',24:'七月庚子大赦是诏令，旧纪安从进如归降得赦为条件，不当实际归降。',25:'七月癸卯景加官有旧纪全称，不重造前掌权为同一任命。',26:'冯道三表求复枢密与帝不许分开，不补各疏日期或以前废置另造当年事实。'}
assert not (P/'publication.json').exists()
for n in range(15,27):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=283,year=942,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(15,27)],next_paragraph=Q[27]['id'],supplements=supplements,excluded_non_body=[],source_contexts=[],coverage='连续第15—26段，原20—31行，五月至七月及临终追述。后接张遇贤起事第27段，全年40正文尚未完成。',source_issues_review='继承意图、旧纪遗制与新史暗许说分别注明；刘太妃母系异说延续保留。闽战主线本批无对应新旧史细节命中，原文逐项保留，不伪造补证；电子底本纸本及异文待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(15,27)],plain_language_review='首次逐条检查人物、标题、事件说明、参与动作、时间与关系方向，现代白话解释原文；托付意图、方案、命令及实际行动分清，俘斩数和不同兵力不机械相加。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
