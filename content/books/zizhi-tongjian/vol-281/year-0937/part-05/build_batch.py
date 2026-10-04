# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 35–42."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,60))
specs=[(d.name,d,'7ab11539b383300ef1f618b97db115f4d85186a1','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-rebellion','jiuwudaishi-076-qian-death-report','xinwudaishi-008-lu-date','xinwudaishi-051-fan-rebellion','jiuwudaishi-095-zhou-gui']:
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
main_sources = ['tongjian-281-937-rebellion','tongjian-281-937-july-warfare','tongjian-281-937-july-aftermath']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p035-p042',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-091-fu-death':'卷91·符彦饶传','jiuwudaishi-095-bai-death':'卷95·白奉进传','jiuwudaishi-097-zhang-death':'卷97·张从宾传','songshi-262-li-tao-petition':'卷262·李涛传','songshi-262-li-tao-age':'卷262·李涛传','xinwudaishi-051-wen-brothers':'卷51·娄继英传','xinwudaishi-051-wen-deaths':'卷51·娄继英传'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/281.txt').read_text().splitlines()
for n in range(35, 43):
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
    labels={'jiuwudaishi-091-fu-death':'卷91·符彦饶传','jiuwudaishi-095-bai-death':'卷95·白奉进传','jiuwudaishi-097-zhang-death':'卷97·张从宾传','songshi-262-li-tao-petition':'卷262·李涛传','songshi-262-li-tao-age':'卷262·李涛传','xinwudaishi-051-wen-brothers':'卷51·娄继英传','xinwudaishi-051-wen-deaths':'卷51·娄继英传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '七月条下'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'宋廷浩':'后晋巡检使。937年七月，张从宾进攻汜水关时将他杀害。',
'温延浚':'温韬的儿子、温延沼的弟弟。937年在许州响应范延光，后来投奔张从宾，被张从宾杀害。',
'温延沼':'温韬的儿子，温延浚、温延衮的兄长。937年在许州响应范延光，曾阻止兄弟杀害娄继英，后来被张从宾杀害。',
'温延衮':'温韬的儿子、温延沼的弟弟。937年在许州响应范延光，后来投奔张从宾，被张从宾杀害。',
'马万':'后晋奉国左厢都指挥使。937年滑州军乱时，在卢顺密劝说后参与擒获符彦饶，随后被任命为义成节度使。',
'张晖（博州守将）':'937年负责博州的守将，向杨光远献城投降。原文未在此处说明具体官衔和家世。',
'李涛（后晋史馆修撰）':'后晋史馆修撰。937年以张全义重建洛阳的功绩为由，请求减轻对张继祚家族的牵连。',
'王晖（安州威和指挥使）':'后晋安州威和指挥使。937年杀死安远节度使周瑰，自行掌管军府，准备根据范延光胜败决定依附或逃往吴国。'}
NEW_ALIASES={n:[] for n in NEW_DESCRIPTIONS}
NEW_ALIASES.update({'温延浚':['溫延濬'],'温延沼':['溫延沼'],'温延衮':['溫延衮','溫延袞'],'马万':['馬萬'],'张晖（博州守将）':['張暉（博州守将）'],'李涛（后晋史馆修撰）':['李濤（后晋史馆修撰）'],'王晖（安州威和指挥使）':['王暉（安州威和指挥使）']})
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=937 if name in ['宋廷浩','温延浚','温延沼','温延衮'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=937, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='937年七月'+'，具体日期未记载'
    key = 'event_zztj_281_0937_' + code
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
        edge = 'participation_zztj_281_0937_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_281_0937_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})
ALIASES.update({'延浚':'温延浚','延沼':'温延沼','延衮':'温延衮','张晖':'张晖（博州守将）','李涛':'李涛（后晋史馆修撰）','王晖':'王晖（安州威和指挥使）'})
# 35: actual assault, proposed withdrawal and successful remonstrance.
add('zhang_kills_song_tinghao','张从宾攻汜水关，杀死巡检使宋廷浩',35,'秋，七月，','杀巡检使宋廷浩。',[('张从宾','进攻汜水关并杀死宋廷浩'),('宋廷浩','以巡检使身份被杀')],place='汜水关')
sup('zhang_kills_song_tinghao',35,'xinwudaishi-008-lu-date','秋七月，從賓陷汜水關，殺巡檢使宋廷浩。','《新五代史》也记张从宾在七月攻陷汜水关、杀宋廷浩。','这是本纪正文，不将旧本纪旁注转引的通鉴文字当作另一独立证据。')
add('shi_plans_jinyang_escape','石敬瑭准备率轻骑避往晋阳',35,'帝戎服，','将奔晋阳以避之。',[('帝','穿上军服、整备轻骑，准备避往晋阳')],place='大梁至晋阳的计划路线',note='准备避走，不代表已经离开大梁或已经到晋阳。')
add('sang_stops_shi_retreat','桑维翰劝石敬瑭等待，石敬瑭停止避走计划',35,'桑维翰叩头',None,[('桑维翰','劝石敬瑭稍等，不轻易离开'),('帝','听劝后停止避走计划')],place='大梁',description='桑维翰叩头劝谏，认为叛军虽声势强盛，却难以持久，请石敬瑭稍作等待。石敬瑭因此停止避往晋阳的计划。',note='叛军不能持久是桑维翰当时的判断，不写成此刻已被击败。')
# 36: solicitation, thwarted attempt and mutually hostile allies.
add('fan_wax_letters_recruit','范延光以蜡丸密信招引娄继英、尹晖及温氏三兄弟响应',36,'范延光遣使','皆应之。',[('范延光','以蜡丸密信招引失去职位或处境不如意者'),('娄继英','在大梁响应招引'),('尹晖','在大梁响应招引'),('延浚','在许州响应招引'),('延沼','在许州响应招引'),('延衮','在许州响应招引')],place='大梁、许州',note='“失职者”不是现代失职处分的固定名词；《资治通鉴》此时仍列二人官衔，保留政治处境与官职记载，不自行解释为全部已罢官。')
for child in ['延浚','延沼','延衮']:relationship('温韬',child,'父亲',36,span(36,'温韬之子','皆应之。'),'原文明示温韬之子，方向为温韬是该人的父亲；三个儿子分别建立关系。')
for younger in ['延浚','延衮']:relationship('延沼',younger,'兄长',36,'延沼與其弟延濬、延衮募不逞之徒千人，期以攻許。','《新五代史》明确延沼为兄，延浚和延衮为弟；不按《资治通鉴》列名顺序推长幼。',source='xinwudaishi-051-wen-brothers')
sup('fan_wax_letters_recruit',36,'xinwudaishi-051-wen-brothers','及范延光反，繼英有弟為魏州子城都虞候，延光遣人以蠟書招繼英，繼英乃遣延沼入魏見延光，延光大喜，與之信箭，使陰圖許。','《新五代史》补记娄继英派温延沼到魏州见范延光，范延光交给温延沼信箭，命他秘密谋取许州。','这段补充联络经过，不把娄继英未具名的弟弟另起姓名，也不把持信箭写成已经夺得许州。',relation='adds')
add('wen_raise_thousand_xu','范延光命温氏兄弟夺取许州，温氏聚集千人',36,'延光令延浚','聚徒已及千人。',[('范延光','命温氏兄弟夺取许州'),('延浚','参与聚集千人准备夺取许州'),('延沼','参与准备夺取许州'),('延衮','参与准备夺取许州')],place='许州',note='千人是三兄弟所聚总人数，夺取许州为计划，没有写成已攻占。')
add('lou_yin_flee_exposure','娄继英、尹晖的密谋泄露后逃走',36,'继英、晖事泄，','皆出走，',[('娄继英','密谋泄露后逃走'),('尹晖','密谋泄露后逃走')],place='大梁')
add('shi_wax_letter_edict','石敬瑭下令赏捕密探、杀范延光密探并禁止蜡书上报',36,'壬子，','勿以闻。',[('帝','下令奖励捕获密探者、处死密探并禁止蜡书上报'),('范延光','其密探成为诏令惩处对象')],when='937年七月壬子',description='石敬瑭下诏称范延光的奸谋诬及忠良，命此后捕获范延光密探时赏捕获者、杀密探，并禁止蜡书，不必再向皇帝奏报。',note='“诬污忠良”是诏令的说法，不据此判定每个响应者都是无辜者；“禁蜡书”保留为禁止蜡书，不扩成所有书信均禁止。')
add('yin_killed_en_route_wu','尹晖准备逃往吴国，途中被杀',36,'晖将奔吴，','为人所杀。',[('尹晖','准备逃往吴国，尚未到达时被杀')],place='赴吴途中，具体地点未记载',note='杀人者未具名，不造凶手；没有写成已投奔吴国。')
sup('yin_killed_en_route_wu',36,'xinwudaishi-008-lu-date','壬子，右衞大將軍尹暉叛奔于吳，不克，伏誅。','《新五代史》记七月壬子尹晖逃往吴国未成，被处死。','《资治通鉴》未在被杀句单列纪日，《新五代史》壬子作为独立纪时补证保留；《资治通鉴》“为人所杀”与《新五代史》“伏诛”表述分别保留。',relation='adds',field='time_original')
add('lou_seeks_wen_refuge','娄继英逃到许州，依附温氏兄弟',36,'继英奔许州，','依温氏。',[('娄继英','逃到许州依附温氏'),('延浚','娄继英依附的温氏兄弟之一'),('延沼','娄继英依附的温氏兄弟之一'),('延衮','娄继英依附的温氏兄弟之一')],place='许州')
add('chang_prevents_wen_attack','苌从简严密戒备，温氏兄弟无法起兵',36,'忠武节度使','延浚等不得发，',[('苌从简','严密戒备许州'),('延浚','因戒备严密无法起兵'),('延沼','因戒备严密无法起兵'),('延衮','因戒备严密无法起兵')],place='许州')
add('wen_plot_kill_lou_stopped','温氏兄弟想杀娄继英自证清白，温延沼阻止',36,'欲杀继英','延沼止之，',[('延浚','温氏一方谋杀娄继英以自证清白'),('延沼','阻止杀害娄继英'),('延衮','温氏一方谋杀娄继英以自证清白'),('娄继英','被谋杀而尚未遇害')],place='许州',note='“欲杀”是计划，温延沼反对，不把所有兄弟写成一致同意并已杀娄继英。')
sup('wen_plot_kill_lou_stopped',36,'xinwudaishi-051-wen-deaths','溫氏兄弟謀殺繼英以自歸，延沼以其女故不忍。','《新五代史》说温延沼顾念自己的女儿，未忍杀娄继英。','此前同传明文女儿是娄继英儿媳；这里只说明阻止理由，不补女儿姓名或生卒。',relation='adds')
claim('person',people['温延沼'],'biography','《新五代史》记温延沼的女儿嫁给娄继英的儿子，因此温延沼阻止杀娄继英。',36,'繼英子婦，溫延沼女也，','婚姻关系在本句明确；阻止杀害的理由另见同传下一段。不把未具名女儿另编姓名。',source='xinwudaishi-051-wen-brothers')
add('wen_lou_join_zhang','温氏兄弟与娄继英一同投奔张从宾',36,'欲杀继英','遂同奔张从宾。',[('延浚','与娄继英一起投奔张从宾'),('延沼','与娄继英一起投奔张从宾'),('延衮','与娄继英一起投奔张从宾'),('娄继英','与温氏兄弟一起投奔张从宾'),('张从宾','接受投奔的叛军首领')],place='张从宾军中')
sup('wen_lou_join_zhang',36,'xinwudaishi-051-wen-deaths','張從賓反於洛陽，延沼兄弟乃與繼英俱投從賓於汜水。','《新五代史》补记投奔地点为汜水。','投奔地点来自独立传记，不把许州的招募地点当投奔地点。',relation='adds')
add('lou_instigates_wen_execution','娄继英劝张从宾捕杀温氏三兄弟',36,'继英知其谋，',None,[('娄继英','知道温氏曾想杀自己，劝张从宾捕杀温氏兄弟'),('张从宾','捕获并杀死温氏三兄弟'),('延浚','被张从宾捕杀'),('延沼','被张从宾捕杀'),('延衮','被张从宾捕杀')],place='张从宾军中',note='三温指同段温韬三个儿子。捕杀不等于两人的谋杀计划已经实施。')
sup('lou_instigates_wen_execution',36,'xinwudaishi-051-wen-deaths','繼英知溫氏之初欲殺己也，反譖延沼兄弟於從賓，從賓殺之。','《新五代史》也记娄继英得知温氏曾想杀自己，转向张从宾谗告，张从宾杀温氏兄弟。','“谗告”归于《新五代史》表述，不另补具体罪名。')
# 37: quarrel, violent killing, mutiny suppression and judicial order.
add('bai_executes_five_looters','白奉进处死五名夜间劫掠军士',37,'白奉进在滑州，','奉进皆斩之；',[('白奉进','处死五名夜间劫掠军士'),('符彦饶','其所属两名军士被处死')],place='滑州',description='白奉进在滑州捕获五名夜间劫掠军士，三人属自己部队、两人属符彦饶部队，全部处死。')
sup('bai_executes_five_looters',37,'jiuwudaishi-095-bai-death','凡獲五盜，三在奉進本軍，二在彥饒麾下，尋命俱斬之。','《旧五代史》白奉进传也记五人分属两军，被白奉进处死。','人数与所属相符，独立传记正文，不使用旁引《资治通鉴》。')
add('bai_fu_quarrel','符彦饶不满白奉进越过自己处刑，二人发生争执',37,'彦饶以其','彦饶不留；',[('符彦饶','因白奉进未经告知处死本军士兵而发怒'),('白奉进','次日道歉，争执后怀疑符彦饶参与反叛')],place='滑州牙署',description='符彦饶因白奉进未经告知处死自己的军士而发怒。次日白奉进带几名骑兵来道歉，认为违法军士不应区分所属；争执后反问符彦饶是否想与范延光一同反叛，随即起身，符彦饶没有挽留。',note='反叛指控是白奉进的质问，不据此证明符彦饶已经和范延光通谋。次日只相对前一日，不补干支。')
add('fu_guards_kill_bai','符彦饶帐下军士捕杀白奉进',37,'帐下甲士大噪，','杀之。',[('白奉进','被符彦饶帐下军士捕杀'),('符彦饶','捕杀发生在其帐下部队')],place='滑州牙署',note='直接杀人者是帐下军士，《资治通鉴》未写符彦饶本人动手或明确下令；不从怒气推断命令。')
sup('fu_guards_kill_bai',37,'jiuwudaishi-095-bai-death','其帳下介士大噪，擒奉進殺之。','《旧五代史》白奉进传也记符彦饶帐下军士捕杀白奉进。','传记前句明确彦饶不留，帐下所属与《资治通鉴》一致。')
add('bai_death_troops_disorder','白奉进随骑呼喊报信，滑州诸军武装喧乱',37,'从骑走出，','喧噪不可禁止。',[('白奉进','被杀引发随骑报信与诸军喧乱')],place='滑州',note='白奉进作为已死事件对象参与，不写成死后指挥；不创造匿名报信骑兵姓名。')
add('lu_dissuades_ma_mutiny','卢顺密劝马万擒符彦饶，制止他参与军乱',37,'奉国左厢','勿复疑也！”',[('马万','惶惑中准备率步兵参与军乱，受到劝阻'),('卢顺密','劝马万共同擒符彦饶，强调家属和赏罚'),('符彦饶','卢顺密主张擒获的对象')],place='滑州',description='马万原准备率步兵参与军乱。卢顺密劝他共同擒符彦饶送交皇帝，提醒军士家属都在大梁，并表示服从者受赏、违命者被杀。卢顺密判断符彦饶与魏州通谋，这属于他在劝说中的判断。',note='距行宫二百里是卢顺密言辞，保留传统里数，不换算现代公里；通谋不据言辞认作已证事实。')
add('lu_kills_disobedient_soldiers','卢顺密杀死数名呼喊跳跃的军士，压住骚乱',37,'万部兵尚有','众莫敢动。',[('卢顺密','杀数名呼喊跳跃的马万部军士'),('马万','其所属部分军士被卢顺密处死')],place='滑州',note='数人没有精确人数，不推算。')
add('ma_lu_fang_capture_fu','马万、卢顺密和方太攻牙城，擒获符彦饶',37,'万不得已','执彦饶，',[('马万','跟随卢顺密攻牙城擒符彦饶'),('卢顺密','率军攻牙城擒符彦饶'),('方太','与二人共同擒符彦饶'),('符彦饶','被攻入牙城的军队擒获')],place='滑州牙城')
add('fang_escorts_fu','方太率部押送符彦饶去大梁',37,'万不得已','令太部送大梁。',[('方太','率部押送符彦饶去大梁'),('符彦饶','被方太押送')],place='滑州至大梁')
add('shi_orders_fu_execution','石敬瑭下令在班荆馆处死符彦饶，不追究其兄弟',37,'甲寅，',None,[('帝','下令处死符彦饶，不追究其兄弟'),('符彦饶','被命在班荆馆处死')],when='937年七月甲寅',place='班荆馆',note='免问兄弟为司法处理，不补未具名兄弟主体；《资治通鉴》位置与他书赤冈异说保留。')
sup('shi_orders_fu_execution',37,'jiuwudaishi-091-fu-death','遣裨校方太拘送闕下，行及赤岡南，高祖遣中使害於路左。','《旧五代史》符彦饶传记方太押送途中到赤冈南，石敬瑭派中使将符彦饶杀死。','与《资治通鉴》班荆馆保留地点差异。该传“第二字”疑字和章节问题提示不在当前摘录，不改底本也不引用其父子叙述。',relation='conflicts')
sup('shi_orders_fu_execution',37,'xinwudaishi-008-lu-date','甲寅，戍將奉國指揮使馬萬執符彥饒歸于京師，命殺之于赤岡。〈彥饒雖有縱軍之罪，被誣以反而見殺，故不書誅，曰「命殺」，嫌萬擅殺。〉','《新五代史》记甲寅命杀符彦饶于赤冈，并评述他被诬为反叛者。','赤冈与《资治通鉴》班荆馆分列，评价归欧阳修的书法说明；不把《资治通鉴》质问和《新五代史》否定压成统一确定结论。',relation='conflicts')
# 38: political loyalty, discipline, appointments, victories and limited clemency.
add('yang_rejects_troop_enthronement','杨光远率军趋滑州，拒绝军士拥立自己',38,'杨光远自白皋','其下乃不敢言。',[('杨光远','从白皋率军趋滑州，拒绝军士拥立')],place='白皋至滑州',description='杨光远从白皋率军趋滑州。军士听说滑州军乱，想拥立他为主；杨光远斥责这种想法，表示现在改图便是真正反叛，军士不敢再说。',note='晋阳之降是杨光远对过去行为的解释，不在当前再造一场投降。')
add('liu_advises_shi_crisis','刘知远建议石敬瑭以恩安抚将相，由自己严管军士',38,'时魏、孟、滑','枝叶不伤矣。”',[('帝','在三镇动乱后向刘知远问计'),('刘知远','建议恩抚将相、严管军士以稳定京城')],place='大梁',description='魏州、孟州、滑州接连动乱，石敬瑭向刘知远问计。刘知远以晋阳旧事和当前兵力、契丹关系安慰他，建议皇帝以恩安抚将相，自己以军纪管束士兵。',note='天命和鼠辈等是刘知远言辞，不能据此作为历史成败的客观因果；晋阳旧事不强记在937年。')
add('liu_strict_guard_discipline','刘知远严设军纪，宿卫军队不敢触犯',38,'知远乃严设','无敢犯者。',[('刘知远','对宿卫军队严设军纪')],place='大梁',note='遵守情况是史书概述，不添加具体未列军法条文。')
add('liu_executes_paper_money_thief','刘知远杀死偷一包纸钱的军士',38,'有军士盗纸钱','由是众皆畏服。',[('刘知远','不接受宽释请求，处死盗纸钱军士')],place='大梁',description='一名军士偷了一包祭祀用纸钱，被主管者捕获。左右请求宽释，刘知远说要惩罚偷窃之心、不计物品价值，最终将其处死。史书记载军士因此畏惧服从。',note='纸钱是祭祀用品，不解释为流通纸币；数量为一幞，不补价值。')
add('yang_july_chief_command','杨光远被任命为魏府行营都招讨使并主持行府',38,'乙卯，','兼知行府事，',[('杨光远','被任命为魏府行营都招讨使并主持行府')],when='937年七月乙卯')
sup('yang_july_chief_command',38,'xinwudaishi-008-lu-date','乙卯，楊光遠為魏府行營都招討使。','《新五代史》也记乙卯任命杨光远为魏府行营都招讨使。','都招讨任命与六月四面部署分别保存。')
add('gao_henan_tokyo_appointment','高行周被任命为河南尹和东京留守',38,'以昭义节度使','东京留守，',[('高行周','由昭义节度使被任命为河南尹，兼任《资治通鉴》所记东京留守')],when='937年七月乙卯',note='原书称东京留守，《旧五代史》称东都留守，分别引用，不直接把东京改成东都。')
sup('gao_henan_tokyo_appointment',38,'jiuwudaishi-076-qian-death-report','以昭義節度使高行周為河南尹、東都留守，充西面行營諸軍都部署；','《旧五代史》记高行周为河南尹、东都留守，并充西面行营诸军都部署。','《旧五代史》本纪甲寅条下，《资治通鉴》乙卯，且东都与东京名称不同，日期和称谓差异保留。',relation='conflicts')
add('du_zhaoyi_cavalry_commander','杜重威被任命为昭义节度使及侍卫马军都指挥使',38,'以杜重威','侍卫马军都指挥使，',[('杜重威','被任命为昭义节度使及侍卫马军都指挥使')],when='937年七月乙卯')
add('hou_heyang_appointment','侯益被任命为河阳节度使',38,'以侯益','河阳节度使。',[('侯益','被任命为河阳节度使')],when='937年七月乙卯',place='河阳')
add('ma_yicheng_appointment','石敬瑭根据奏报任命马万为义成节度使',38,'帝以渭州','义成节度使。',[('帝','根据奏报任命马万'),('马万','被任命为义成节度使')],note='《资治通鉴》电子本写渭州奏事，前后情境及旧本纪为滑州军乱，地名疑字保留，不用渭州作为已核地点。')
sup('ma_yicheng_appointment',38,'jiuwudaishi-076-qian-death-report','以馬萬為滑州節度使；','《旧五代史》记甲寅条下任命马万为滑州节度使。','滑州为义成军治所，官职地名可对应；《资治通鉴》未在此句单列日干支，不额外设乙卯为确切任命日。',relation='adds')
add('lu_guozhou_appointment','卢顺密被任命为果州团练使',38,'丙辰，','果州团练使，',[('卢顺密','被任命为果州团练使')],when='937年七月丙辰',place='果州')
add('fang_zhaozhou_appointment','方太被任命为赵州刺史',38,'方太为','赵州刺史；',[('方太','被任命为赵州刺史')],when='937年七月丙辰',place='赵州')
add('lu_zhaoyi_liuhou','石敬瑭得知主要功劳在卢顺密，改任他为昭义留后',38,'既而知皆顺密','昭义留后。',[('帝','得知平定滑州军乱的主要功劳在卢顺密，改任其职'),('卢顺密','被改任为昭义留后')],when='937年七月丙辰任果州团练使之后，具体改任日未明确',place='昭义军')
add('yang_defeats_feng_sun_river','杨光远诱冯晖、孙锐渡河，在半渡时将其击败',38,'冯晖、孙锐','晖、锐走还魏。',[('冯晖','率军到六明镇，半渡受击后退回魏州'),('孙锐','率军到六明镇，半渡受击后退回魏州'),('杨光远','诱叛军渡河，在半渡时攻击')],place='六明镇附近渡河处',description='冯晖、孙锐率军到六明镇，杨光远诱其渡河，在一半渡河时进攻。叛军大败，多人溺死，史书记录斩首三千；冯晖、孙锐逃回魏州。',note='三千是斩首数，不含明确未计数的溺死者，不记为全部伤亡数；半渡是战术时机，不等于一万人必已渡河。')
sup('yang_defeats_feng_sun_river',38,'xinwudaishi-051-fan-rebellion','光遠得諜者，詢得其謀，誘銳等渡河，半濟而擊之，兵多溺死，銳、暉退走入魏，閉壁不復出。','《新五代史》补记杨光远从密探得知对方谋划，诱其半渡后攻击；孙锐、冯晖退回魏州闭城。','《新五代史》该段以六月起兵开篇，串述后续战事，不能因此把当前战斗改定为六月。',relation='adds')
add('du_hou_recapture_sishui','杜重威、侯益击败张从宾万余军，收复汜水关',38,'杜重威、侯益','遂克汜水。',[('杜重威','率军与侯益击败张从宾军'),('侯益','与杜重威共同击败张从宾军'),('张从宾','其万余军队被击败')],place='汜水关',description='杜重威、侯益率军到汜水，遇到张从宾万余军，与之作战，将对方俘获、斩杀殆尽，随后收复汜水关。',note='万余为敌军规模，俘斩殆尽为史家概述，不造精确俘虏数或杀人数。')
sup('du_hou_recapture_sishui',38,'jiuwudaishi-076-qian-death-report','杜重威等奏：「收下汜水關，破賊千人。張從賓及其殘黨奔投入河。','《旧五代史》记杜重威等奏报收复汜水关，击破叛军千人，张从宾及残党逃入河中。','《旧五代史》奏报“破贼千人”与《资治通鉴》万余军、俘斩殆尽口径不同，保留差异，不相加为总伤亡。',relation='adds')
sup('du_hou_recapture_sishui',38,'xinwudaishi-008-lu-date','辛酉，杜重威克汜水關。','《新五代史》记杜重威于七月辛酉收复汜水关。','作为独立作战纪日补证，《资治通鉴》本句没有单列干支，不自行换算公历。',relation='adds',field='time_original')
add('zhang_drowns_flight','张从宾败逃时骑马渡河，溺水而死',38,'从宾走，','溺死。',[('张从宾','败逃时骑马渡河，溺水而死')],place='汜水败逃途中的河道，具体河名未明确',note='溺死与捕后被处刑区分；不从附近地名猜具体渡口。')
sup('zhang_drowns_flight',38,'jiuwudaishi-097-zhang-death','高祖命杜重威、侯益分兵討之，從賓大敗，乘馬入河，溺水而死焉。','《旧五代史》也记张从宾战败后骑马入河溺死。','本传正文独立补证，不把其过去任官串定为937年。')
add('zhang_allies_executed','张延播、张继祚、娄继英被捕送大梁处死，并牵连家族',38,'获其党张延播','灭其族。',[('张延播','被捕送大梁处死，并牵连家族'),('张继祚','被捕送大梁处死，其家族处罚随后部分减轻'),('娄继英','被捕送大梁处死，并牵连家族')],place='大梁',note='三人并列，不把全族处死的概述覆盖后句对张继祚家族的有限免罪；匿名捕获者不补为某将亲自抓获。')
sup('zhang_allies_executed',38,'xinwudaishi-051-wen-deaths','從賓敗，繼英為杜重威所殺。','《新五代史》娄继英传记他在张从宾败后被杜重威杀死。','《资治通鉴》概述送大梁后处死，新传归杀害于杜重威，执行主体和过程分别保存，不改《资治通鉴》为当场被亲手杀。',relation='adds')
add('li_tao_limits_zhang_clan_punishment','李涛请求免除张全义家族牵连，处罚缩至张继祚妻子儿女',38,'史馆修撰李涛','乃止诛继祚妻子。',[('李涛','以张全义重建洛阳的功绩请求免除家族牵连'),('张全义','其旧功被作为减轻家族牵连的理由'),('张继祚','其家族的连坐范围被缩小'),('帝','接受减轻家族牵连的请求')],place='大梁',description='李涛以张全义重建洛阳的功绩请求免除对其家族的牵连。石敬瑭随后将连坐处刑范围限于张继祚的妻子儿女，其他族人免于牵连。',note='“止诛”表示仅处死妻子儿女，不是停止处死妻子儿女；此前张继祚本人已被处死，免族不是赦免他。')
sup('li_tao_limits_zhang_clan_punishment',38,'songshi-262-li-tao-petition',source_span('songshi-262-li-tao-petition','晉天福初，','從之。'),'《宋史》记李涛任考功员外郎、史馆修撰，曾上疏请只处罚张继祚妻子儿女，石敬瑭接受。','该段“张从赏”为本电子本异文，结合全义、继祚、盟津洛阳虎牢叛乱确认对应张从宾，保留摘录不另建张从赏主体。其后任官经历不都定在937年。',relation='adds')
claim('person',people['李涛（后晋史馆修撰）'],'description','后晋史馆修撰李涛与此前吴将李涛分开识别。《宋史》记此人在建隆二年去世、年六十四，年龄记载与887年已统兵的吴将不相容。',38,source_span('songshi-262-li-tao-age','宋初，','贈右僕射。'),'此来源仅用于当前人物身份区分，不提前建立宋初事件，也不据年龄自行填写精确生年。',source='songshi-262-li-tao-age')
claim('person',people['李涛（后晋史馆修撰）'],'biography','《资治通鉴》称李涛是李回的族曾孙，即同族的曾孙辈亲属。',38,'涛，回之族曾孙也。','回按李涛同姓上下文写为李回，具体族谱尚待核实；不把族曾孙画成直系曾祖父关系，不与吴将李涛合并。')
# 39–42: routine summons, surrender, Anzhou violence and failed reconciliation.
add('shi_summons_luoyang_officials','石敬瑭命东都留守司百官赴当前驻地',39,'诏东都',None,[('帝','命东都留守司百官赴行在')],place='东都至大梁行在',note='行在为皇帝当前驻地，结合此前驻大梁上下文，不等同于百官已经全部到达。')
add('zhang_hui_surrenders_bo','杨光远奏报博州守将张晖献城投降',40,'杨光远奏',None,[('杨光远','奏报博州守将献城投降'),('张晖','以博州守将身份献城投降')],place='博州',note='张晖与同卷冯晖、安州王晖分开；知博州仅说明主持州事，不补未载官衔。')
sup('zhang_hui_surrenders_bo',40,'xinwudaishi-008-lu-date','壬申，楊光遠克博州。','《新五代史》记七月壬申杨光远取得博州。','《资治通鉴》具体说明守将献城，《新五代史》本纪用克字，不强加一场攻城战；壬申为《新五代史》纪日补证。',relation='adds',field='time_original')
add('wang_hui_kills_zhou_gui','安州王晖杀死安远节度使周瑰，自掌军府',41,'安州威和','自领军府，',[('王晖','听说范延光起兵，杀周瑰并自行掌管军府'),('周瑰','以安远节度使身份被王晖杀害')],place='安州')
sup('wang_hui_kills_zhou_gui',41,'jiuwudaishi-095-zhou-gui','先是，威和指揮使王暉領部下兵屯於安陸，瑰至鎮，待之甚厚。俄聞範延光叛於魏博，張延賓寇於汜水，暉以瑰高祖之元臣也，幸國朝方危，遂害瑰於理所，自總州事，','《旧五代史》周瑰传补记王晖原率兵驻安陆，在周瑰治所将其杀害，自掌州事。','王晖据其安州职务识别，未与蜀地同名人合并。传记“张延宾”与《资治通鉴》张从宾有异文，保留原字，不增同名主体。',relation='adds')
sup('wang_hui_kills_zhou_gui',41,'xinwudaishi-008-lu-date','丙子，安州屯防指揮使王暉殺其節度使周瓌，','《新五代史》记七月丙子安州屯防指挥使王晖杀周瑰。','威和与屯防为两书职务称谓，周瓌与规范名周瑰作字形异文匹配；不覆盖《资治通鉴》职衔。',relation='adds',field='time_original')
add('wang_hui_contingent_plan','王晖打算范延光胜则依附，败则逃往吴国',41,'欲俟延光胜','败则渡江奔吴。',[('王晖','按范延光胜败筹划依附或逃往吴国'),('范延光','其胜败被王晖作为下一步行动条件')],place='安州至吴国的计划路线',note='两项是条件计划，不写成王晖已经依附或已经渡江。')
add('li_jinquan_sent_anzhou','石敬瑭派李金全率千骑赴安州巡检',41,'帝遣右领军','如安州巡检，',[('帝','派李金全率千骑赴安州'),('李金全','以右领军上将军身份率千骑巡检安州')],place='大梁至安州',note='千骑是一千骑兵，不写成一千人另加一千匹以外的第二支军队。')
add('shi_promises_wang_pardon','石敬瑭许诺赦免王晖，并任他为唐州刺史',41,'许赦王晖',None,[('帝','许诺赦免王晖，并任其为唐州刺史'),('王晖','得到赦免及唐州刺史的承诺')],place='安州、唐州',note='许赦为招抚承诺，不表示王晖已经接受、到任或被全面司法免罪。')
add('fan_executes_sun_clan','范延光将失败归罪于孙锐，对孙锐及其家族处刑',42,'范延光知事不济，','归罪于孙锐而族之，',[('范延光','将失败归罪于孙锐并对其家族处刑'),('孙锐','与家族一起被范延光处死')],place='魏州',note='族表示牵连家族的死刑，未明范围，不编造家族人数与姓名。')
add('fan_petitions_pardon','范延光派使者上表请罪',42,'遣使奉表','待罪，',[('范延光','派使者上表请罪')],place='魏州至朝廷',note='上表待罪不等于已获赦免或军队已降。')
add('shi_rejects_fan_petition','杨光远转奏范延光请罪，石敬瑭不接受',42,'戊寅，',None,[('杨光远','转奏范延光的请罪表'),('帝','拒绝接受范延光请罪'),('范延光','请罪未获接受')],when='937年七月戊寅转奏',note='戊寅是转奏纪日，不自动当成孙锐被杀或初次遣使日。')
# Every new profile and each new/reused death assertion has individual evidence.
profiles={
'宋廷浩':(35,'秋，七月，','杀巡检使宋廷浩。'),
'温延浚':(36,'范延光遣使',None),
'温延沼':(36,'范延光遣使',None),
'温延衮':(36,'范延光遣使',None),
'马万':(37,'奉国左厢','令太部送大梁。'),
'张晖（博州守将）':(40,'杨光远奏',None),
'李涛（后晋史馆修撰）':(38,'史馆修撰李涛','乃止诛继祚妻子。'),
'王晖（安州威和指挥使）':(41,'安州威和','败则渡江奔吴。')}
for name,(n,start,end) in profiles.items():
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'简介按本段身份与行动整理；温氏长幼另由《新五代史》同传明文补证，马万任官另见本批第38段。限定名用于区别同名人，不添加会碰撞的裸名别名。')
for raw,n,quote in [('宋廷浩',35,span(35,'秋，七月，','杀巡检使宋廷浩。')),('尹晖',36,'晖将奔吴，为人所杀。'),('温延浚',36,'继英知其谋，劝从宾执三温，皆斩之。'),('温延沼',36,'继英知其谋，劝从宾执三温，皆斩之。'),('温延衮',36,'继英知其谋，劝从宾执三温，皆斩之。'),('白奉进',37,'帐下甲士大噪，擒奉进，杀之。'),('符彦饶',37,span(37,'甲寅，',None)),('张从宾',38,'从宾走，乘马渡河，溺死。'),('张延播',38,'获其党张延播、继祚、娄继英，送大梁，斩之，灭其族。'),('张继祚',38,'获其党张延播、继祚、娄继英，送大梁，斩之，灭其族。'),('娄继英',38,'获其党张延播、继祚、娄继英，送大梁，斩之，灭其族。'),('周瑰',41,'安州威和指挥使王晖闻范延光作乱，杀安远节度使周瑰，自领军府，'),('孙锐',42,'范延光知事不济，归罪于孙锐而族之，')]:
 name=ALIASES.get(raw,raw);claim('person',people[name],'death_year',f'{name}于937年七月条所记事件中死亡。',n,quote,'本年《资治通鉴》明示死亡，具体死因见对应事件；既有主体旧档案不覆写，补独立死年事实。')
reviews={35:'张攻关杀宋与帝避晋阳准备分开，桑谏后止没有实际逃往。新晋纪独立确认七月攻关杀宋，不以旧纪转引通鉴重复证明。',36:'蜡丸招引、响应、千人夺许计划、曝光逃走、壬子禁谍诏、尹被杀、温娄投张及被杀分录。温父子明示，《新五代史》延沼兄长，未从列名顺序猜。族刑、女儿婚姻与阻止理由保留具体范围未知。',37:'夜掠五人归属三二明确，白谢罪争执中质问反叛不定通谋；帐下杀白未认符亲手。卢劝马、杀数人、三将擒符押送及甲寅敕斩分录。班荆馆与赤冈异说，《新五代史》被诬评价独立保留。',38:'拥立被拒、刘恩威建议和军法实际执行分开，纸钱非流通货币。高东京/旧东都、任官日期不同；渭州疑滑州留原字。半渡斩三千不计总伤亡。杜侯胜、张溺死、三党族刑及李涛缩族分录；止诛不是停止处刑。后晋李涛以宋传年龄另识，与吴将不混。',39:'百官赴行在为命令，不写已全部到达。',40:'张晖博州守将单独身份，主献城、《新五代史》克字不补攻城；壬申新纪独立日期。',41:'安州王晖与蜀王晖分开，周身份沿原主体。杀人自掌为事实，随范胜败的依附/逃吴为意图，千骑巡检是发令，赦免和唐刺是承诺。',42:'范归罪族孙、上表请罪、戊寅杨转奏与帝拒绝分别记录，不推孙处死日或范获赦。'}
assert not (P/'publication.json').exists()
for n in range(35,43):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(35,43)],next_paragraph=Q[43]['id'],next_volume=281,next_year=937,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第35—42段（原第40—47行），七月汜水战事、温氏与娄继英、滑州乱与符彦饶死亡、朝廷任官平叛、博州献城、安州起乱、范延光请罪未成。937年尚未完成。',source_issues_review='逐行回查《资治通鉴》；第38段渭州疑滑州、东京与旧东都分别说明。旧符传章节提示及第二字疑文不用于家世引用，死亡摘录仍完整可回查。新娄传、旧张白符传与宋262李涛传传主和卷号已核；宋张从赏疑异文不另造人。新导出快照包含后续未录段落，仅计本批连续范围。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(35,43)],plain_language_review='首次整理逐条核对新展示文案、角色、身份、时间和关系方向；引用保留原字，补证分别记录。旧内容全面文案审阅仍停在935年，不设固定第二轮重写。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
