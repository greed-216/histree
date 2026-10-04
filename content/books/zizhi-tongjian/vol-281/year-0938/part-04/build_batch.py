# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 938 paragraphs 17–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,43))
specs=[(d.name,d,'f4605adf63bfe6985ea9b40a7251f2d598ff17b8','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-938-palace-and-policy']:
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
main_sources = ['tongjian-281-938-palace-and-policy']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0938-p017-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-077-august':'卷77·晋高祖纪·天福三年八月','jiuwudaishi-077-september':'卷77·晋高祖纪·天福三年九月','liaoshi-004-jin-investiture':'卷4·太宗纪·会同元年十一月','liaoshi-076-zhao-siwen':'卷76·赵思温传'}
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
for n in range(17, 21):
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
    labels={'jiuwudaishi-077-august':'卷77·晋高祖纪·天福三年八月','jiuwudaishi-077-september':'卷77·晋高祖纪·天福三年九月','liaoshi-004-jin-investiture':'卷4·太宗纪·会同元年十一月','liaoshi-076-zhao-siwen':'卷76·赵思温传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '八月至九月跨月条' if n==20 else '八月条下，含追叙'
        citation = f'卷281·后晋天福三年（938；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0938_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'赵延照':'赵思温的儿子。《资治通鉴》记载，他在后晋任祁州刺史，并受父亲委托向石敬瑭转达幽州归附的请求。相关行动的具体年份未载。',
'朱宪（后晋内职官）':'后晋内职官，汴州人。938年被石敬瑭派往广晋城，劝范延光归降。生卒年未载。',
'李式（范延光节度副使）':'范延光的节度副使。938年范延光在考虑归降时，向他表示相信石敬瑭不杀自己的承诺。生卒年未载。',
'范守图':'范延光的儿子。938年九月乙巳，杨光远将他和范守英送往大梁。生卒年和兄弟长幼未载。',
'范守英':'范延光的儿子。938年九月乙巳，杨光远将他和范守图送往大梁。生卒年和兄弟长幼未载。',
'韦勋（后晋册礼使）':'后晋使臣。《辽史》记载，938年十一月壬子与冯道一起为契丹皇太后册上尊号。《旧五代史》所载使团安排不同，另保留引用。',
'卢重（后晋给事中）':'后晋给事中。《辽史》记载，938年十一月丙寅与刘昫一起为契丹皇帝册上尊号。《旧五代史》所载使团安排不同，另保留引用。'}
NEW_ALIASES={'赵延照':['趙延照'],'朱宪（后晋内职官）':['朱宪','硃宪','硃憲'],'李式（范延光节度副使）':['李式'],'范守图':['范守圖'],'范守英':[],'韦勋（后晋册礼使）':['韦勋','韋勛'],'卢重（后晋给事中）':['卢重','盧重']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=938 if name in ['武彦和','王氏（守卫军使王宏之子）'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=938, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='938年八月条下，具体日期未记载'
    key = 'event_zztj_281_0938_' + code
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
        edge = 'participation_zztj_281_0938_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_281_0938_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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


ALIASES.update({'唐主':'李昪','刘煦':'刘昫','太后':'述律平','应天太后':'述律平','延照':'赵延照','硃宪':'朱宪（后晋内职官）','李式':'李式（范延光节度副使）','守图':'范守图','守英':'范守英','韦勋':'韦勋（后晋册礼使）','卢重':'卢重（后晋给事中）'})
add('shi_offers_liao_titles','石敬瑭向契丹皇帝及太后上尊号',17,'八月，','及太后，',[('帝','向契丹皇帝及太后上尊号'),('契丹主','接受后晋所上尊号的契丹皇帝'),('太后','接受后晋所上尊号的契丹皇太后')],when='938年八月，具体日期未载',note='上尊号的安排和使者实际行礼分开，八月此句没有列完整尊号。')
add('jin_investiture_envoys','石敬瑭任命冯道、刘昫为赴契丹的册礼使',17,'戊寅，','为契丹主册礼使，',[('帝','任命赴契丹的册礼使'),('冯道','被任命为契丹太后册礼使'),('刘煦','以左仆射身份被任命为契丹皇帝册礼使')],when='938年八月戊寅',note='刘煦复用已有刘昫主体；职衔、时代与任使对象相合，别名已登记，不另建同人。')
sup('jin_investiture_envoys',17,'jiuwudaishi-077-august','八月戊寅，以左僕射劉句為契丹冊禮使，左散騎常侍韋勛副之，給事中盧重為契丹皇太后冊禮使。','《旧五代史》记八月戊寅以左仆射刘句为契丹册礼使、韦勋为副使、卢重为太后册礼使。','左仆射刘句与主书刘煦、辽史刘昫对应，电子底本字形分别保留；太后使与副使的安排不同，不用此条覆盖冯道任使的记载。',relation='conflicts')
add('jin_envoys_carry_regalia','后晋使团携仪仗和车驾前往契丹行礼',17,'备卤薄、','契丹主大悦。',[('冯道','赴契丹执行册礼使命'),('刘煦','赴契丹执行册礼使命'),('契丹主','接待后晋册礼使团，史书记他十分高兴')],year=None,when='938年八月任使之后，主书未列实际行礼日期',description='后晋使团准备卤簿、仪仗和车驾，前往契丹行礼。《资治通鉴》记耶律德光十分高兴。',note='任命日不直接作为到达或行礼日；卤薄保留底本摘录，展示写仪仗专名卤簿。')
ls='liaoshi-004-jin-investiture'
event('liao_mother_investiture','冯道、韦勋为契丹太后册上尊号',17,source_span(ls,'壬子，','應天皇太后。'),[('冯道','为契丹太后册上尊号'),('韦勋','与冯道一起为契丹太后册上尊号'),('太后','在开皇殿接受尊号')],source=ls,when='《辽史》会同元年十一月壬子（938）',place='开皇殿',description='《辽史》记载，契丹太后在开皇殿接受册礼，冯道、韦勋为她册上“广德至仁昭烈崇简应天皇太后”的尊号。',note='是实际册礼日期补充，不改八月任使时间；该书与旧五代史使团分工不同。')
event('liao_emperor_investiture','刘昫、卢重为契丹皇帝册上尊号',17,source_span(ls,'丙寅，','嗣聖皇帝。'),[('刘煦','为契丹皇帝册上尊号'),('卢重','与刘昫一起为契丹皇帝册上尊号'),('契丹主','在宣政殿接受尊号')],source=ls,when='《辽史》会同元年十一月丙寅（938）',place='宣政殿',description='《辽史》记载，耶律德光在宣政殿接受册礼，刘昫、卢重为他册上“睿文神武法天启运明德章信至道广敬昭孝嗣圣皇帝”的尊号。',note='册礼晚于任使；刘昫沿用既有主体，长尊号繁简转换只用于展示。')
add('shi_subordinate_diplomatic_ritual','石敬瑭对契丹采用称臣和父皇帝等外交礼节',17,'帝事契丹甚谨，','拜受诏敕。',[('帝','上表称臣，称耶律德光为父皇帝，拜受契丹诏敕'),('契丹主','被石敬瑭称为父皇帝')],year=None,when='石敬瑭在位期间的交往追述，具体起止日期未载',description='石敬瑭谨慎对待契丹，上表称臣，称耶律德光为“父皇帝”；契丹使者到来时，他在别殿拜受诏敕。',note='父皇帝是外交称谓，不建血亲或养父关系；持续礼节不硬定八月戊寅。')
add('jin_annual_and_extra_gifts','后晋除每年输送金帛外，还向契丹君臣赠送礼物',17,'岁输金帛','皆有赂遗。',[('帝','安排年度金帛及额外赠送'),('应天太后','收到后晋赠礼'),('韩延徽','收到后晋赠礼'),('赵延寿','收到后晋赠礼')],year=None,when='石敬瑭在位期间的交往追述，具体起止日期未载',description='后晋除每年输送金帛三十万外，还在庆吊和岁时往来中赠送珍异物品。受赠者包括契丹太后、元帅太子、伟王、南北二王、韩延徽和赵延寿等人。',note='三十万沿用原文未具单位，不换算现代金额；未具姓名的王及太子只写史载称号，不猜认人物。')
add('shi_handles_liao_reproaches','石敬瑭以谦卑言辞回应契丹责让',17,'小不如意，','谢之。',[('帝','面对契丹方面的责让，以谦卑言辞致歉')],year=None,when='石敬瑭在位期间的交往追述，具体日期未载',note='史书概述双方交往，不把相邻列举的每个人都认作某一次责让者。')
add('jin_envoys_report_humiliation','后晋使者报告在契丹遭遇不逊言辞，朝野以为耻辱',17,'晋使者至契丹，','与契丹无隙。',[('帝','听到使者报告后仍维持谨慎对契丹的态度')],year=None,when='石敬瑭在位期间的交往追述',description='后晋使者报告契丹方面态度骄倨、言辞不逊，朝野认为耻辱。史书接着概述石敬瑭始终谨慎对待契丹，两国在他在位期间没有发生决裂。',note='朝野以为耻是史书对反应的概述；无隙不扩写为不存在任何责让、矛盾或摩擦。')
add('jin_gifts_shortfall','后晋有时以百姓困窘为由，未足额输送金帛',17,'然所输金帛','不能满数。',[('帝','有时以百姓困窘为由，未足额输送金帛')],year=None,when='石敬瑭在位期间的交往追述',description='《资治通鉴》评价所输金帛相当于数县租赋，并记后晋有时以百姓困窘为由，未能足额输送。',note='数县租赋是史书评述，不提供确定县数或现代财政比例。')
add('liao_changes_diplomatic_address','耶律德光后来让石敬瑭改用儿皇帝的书信称谓',17,'其后契丹主',None,[('契丹主','多次让石敬瑭停止上表称臣，改用书信称儿皇帝'),('帝','被要求改用儿皇帝的书信称谓')],year=None,when='此后，具体年月未载',description='耶律德光后来多次让石敬瑭停止上表称臣，只用书信称“儿皇帝”，按家人之间的礼节往来。',note='其后不强定938年；外交称父子不建立亲属关系。')
add('liao_youzhou_nanjing','契丹将幽州称为南京，并任赵思温为留守',18,'初，','为留守。',[('契丹主','将幽州称为南京，任命赵思温为留守'),('赵思温','被任命为留守')],year=None,when='契丹获得幽州后的追叙，主书未列具体年份',place='幽州、南京',note='初提示追叙，不把任命硬定938年八月；后唐降将身份保留，不推当日才投降。')
sup('liao_youzhou_nanjing',18,'liaoshi-076-zhao-siwen',source_span('liaoshi-076-zhao-siwen','天顯十一年，','尋改臨海軍節度使。'),'《辽史》赵思温传记载，太原战事结束后，赵思温改任南京留守、卢龙军节度使等职，随后又任临海军节度使。','赵思温留守任命有补证，但该传没有给任命单列年月，不把天显十一年救太原的日期覆盖后续全部任官。')
add('zhao_yanzhao_qizhou','石敬瑭任赵延照为祁州刺史',18,'思温子延照','为祁州刺史。',[('帝','任命赵延照为祁州刺史'),('延照','在后晋被任命为祁州刺史')],year=None,when='幽州归附请求之前的追叙，具体年月未载',place='祁州',note='赵延照为赵思温之子，沿用原文姓名，不与其他赵氏将领合并。')
relationship('赵思温','延照','父亲',18,span(18,'思温子延照','为祁州刺史。'),'思温子延照明确赵思温是赵延照的父亲。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','赵思温是赵延照的父亲。',18,'子延照、延靖，官至使相。','《辽史》也明确列延照为赵思温之子；官至使相是生涯概述，不据此新增938年升使相事件。',source='liaoshi-076-zhao-siwen',relation='corroborates')
add('zhao_siwen_offers_youzhou','赵思温托赵延照请求让幽州归附后晋，石敬瑭拒绝',18,'思温密令',None,[('赵思温','秘密让儿子转达幽州归附请求'),('延照','受父亲委托向石敬瑭转达请求'),('帝','拒绝幽州归附的请求')],year=None,when='幽州留守任命之后的追叙，具体年月未载',place='幽州',description='赵思温秘密让赵延照向石敬瑭说，契丹方面的态度终会改变，并请求让幽州归附后晋。石敬瑭没有答应。',note='契丹情势终变是赵思温判断；请求未获接受，不写成幽州已经归还。')
add('liao_sends_envoys_south_tang','契丹派使者前往南唐',19,'契丹遣使诣唐，','契丹遣使诣唐，',[('契丹主','派遣使者前往南唐'),('唐主','契丹使者到访的南唐君主')],note='唐指当时徐诰的南唐，不与已灭亡的后唐混同；匿名使者不补姓名。')
add('song_qiqiu_suggests_envoy_plot','宋齐丘建议贿赂后杀害契丹使者，以离间契丹与后晋',19,'宋齐丘',None,[('宋齐丘','建议先厚赠使者，再于淮北秘密派人杀害'),('唐主','收到宋齐丘离间契丹与后晋的建议')],place='淮北',description='宋齐丘建议徐诰厚赠契丹使者，等使者到淮北后秘密派人杀害，借此离间契丹与后晋。',note='原文只有建议和意图，没有写采纳或实际杀害，不建立已杀使者的结果。')
add('feng_hui_surrenders_from_guangjin','冯晖从广晋出战后归降，报告范延光粮尽困窘',20,'壬午，','食尽穷困；',[('杨光远','上奏报告冯晖归降'),('冯晖','从广晋出战后归降，报告城中粮尽困窘'),('范延光','据冯晖报告，处于粮尽困窘之中')],when='938年八月壬午上奏条下',place='广晋',note='壬午是上奏日，不另认作可独立确认的出战日；粮尽为冯晖报告。冯晖复用既有前澶州刺史主体，不与限定为泸州刺史的同名主体混同。')
sup('feng_hui_surrenders_from_guangjin',20,'jiuwudaishi-077-august','壬午，魏府軍前奏，前澶州刺史馮暉自逆城來歸。','《旧五代史》也记八月壬午，魏府军前报告前澶州刺史冯暉归降。','馮暉与主书冯晖在职务、地点、日期和后续义成任命相合，复用同人；仅对引用保留暉字。')
add('feng_hui_yicheng','石敬瑭任冯晖为义成节度使',20,'己丑，','义成节度使。',[('帝','任命冯晖为义成节度使'),('冯晖','被任命为义成节度使')],when='938年八月己丑',place='义成军')
sup('feng_hui_yicheng',20,'jiuwudaishi-077-august','己丑，以前澶州刺史馮暉為檢校太保，充義成軍節度使。','《旧五代史》也记八月己丑任冯晖为义成军节度使，并补充检校太保职衔。','检校太保按原书补充，不误作军队驻地。')
add('guangjin_siege_stalemate','杨光远围攻广晋一年多，仍未攻下',20,'杨光远攻广晋，','岁馀不下，',[('杨光远','围攻广晋一年多仍未攻下'),('范延光','据守广晋')],year=None,when='范延光归降前的持续围攻，具体起止日期未载',place='广晋',note='岁馀为持续时间，不硬定一次战斗日期；此句不说范延光在此时已被击败。')
add('zhu_xian_promises_fan_safety','石敬瑭派朱宪劝范延光归降，承诺不杀他并移任大镇',20,'帝以师老民疲，','吾无以享国。”',[('帝','因军队久战、百姓疲惫，派人承诺归降后不杀范延光并移任大镇'),('硃宪','进入广晋劝范延光归降'),('范延光','收到移任大镇和保全性命的承诺')],place='广晋',description='石敬瑭因军队久战、百姓疲惫，派内职官朱宪进入广晋劝范延光归降，承诺将他移任大镇，并保证不杀他。',note='这是承诺，不证明后来终身安全；硃宪展示规范为朱宪，职务和汴州籍贯来自同段。')
add('fan_removes_defenses_hesitates','范延光表示相信不杀承诺，撤去守备却仍迟疑',20,'延光谓节度副使','迁延未决。',[('范延光','向李式表示相信皇帝承诺，撤去守备仍迟疑'),('李式','听范延光表示相信不杀承诺')],place='广晋',note='这是范延光的判断，不证明石敬瑭最终兑现终身承诺；撤守备仍未决，不等于此时已经完成正式归降。')
add('liu_churang_persuades_fan','刘处让再次入城劝说，范延光才决定归降',20,'宣徽南院使','延光意乃决。',[('刘处让','以宣徽南院使身份再次入广晋劝范延光'),('范延光','经再次劝说后决定归降')],place='广晋',note='决定归降与奉表、宣诏分别记录；本句没有给刘处让入城单列日期。')
add('fan_sons_sent_daliang','杨光远将范守图、范守英送往大梁',20,'九月，乙巳朔，','诣大梁。',[('杨光远','将范延光两个儿子送往大梁'),('守图','被送往大梁'),('守英','被送往大梁')],when='938年九月乙巳朔',place='大梁',note='原文只写送二子，不补人质身份、强制方式或长幼次序。')
relationship('范延光','守图','父亲',20,span(20,'九月，乙巳朔，','诣大梁。'),'延光二子守图、守英明确父亲方向，不推长幼。')
relationship('范延光','守英','父亲',20,span(20,'九月，乙巳朔，','诣大梁。'),'延光二子守图、守英明确父亲方向，不推长幼。')
add('fan_submits_surrender_memorial','范延光派牙将上表请求处分',20,'己酉，','奉表待罪。',[('范延光','派牙将上表待罪')],when='938年九月己酉',note='待罪是请求皇帝处分，不等于已被判处某罪。')
sup('fan_submits_surrender_memorial',20,'jiuwudaishi-077-september','九月己酉，宮苑使焦繼勛自軍前押範延光牙將馬諤賫歸命請罪表到闕。','《旧五代史》补充牙将名为马谔，由宫苑使焦继勋从军前带着归降请罪表到朝廷。','主书侧重派牙将奉表，旧史侧重表到朝廷；不据此把同日发出和到达都认作确定。只作事件补充，人物生涯另待主线涉及。')
add('fan_surrender_pardoned','范延光率众穿素服候诏，获宣诏赦免',20,'壬子，','宣诏释之，',[('范延光','率部众穿素服在牙门等候，获诏赦免'),('帝','下诏赦免范延光及其部众')],when='938年九月壬子',place='广晋牙门',note='诏释说明此次赦免，不推所有后来行为都获免责。')
sup('fan_surrender_pardoned',20,'jiuwudaishi-077-september','壬子，延光領部下將士素服於本府門俟命，有詔釋罪。','《旧五代史》也记九月壬子范延光率部众穿素服候命，并获诏赦罪。','两书纪日及行动相合，服色不改译成官员任服。')
claim('person',people['朱宪（后晋内职官）'],'description','朱宪是后晋内职官，汴州人，曾被派入广晋劝范延光归降。',20,Q[20]['text'],'籍贯来自段末，职务和行动来自前文；硃宪不因字形另建主体。')
sup('liao_youzhou_nanjing',18,ls,'升幽州為南京，南京為東京。','《辽史》在会同元年十一月记升幽州为南京，并将原南京改为东京。','《通鉴》此处追叙没有列年份，辽史补充正式升改的纪时；赵思温传将留守任命接在太原战事之后，是否沿用后来的都城名仍待版本校核，不把两段时序强行统一。',relation='adds',field='time_original')
for name in ['韦勋（后晋册礼使）','卢重（后晋给事中）']:
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],17,'八月戊寅，以左僕射劉句為契丹冊禮使，左散騎常侍韋勛副之，給事中盧重為契丹皇太后冊禮使。','该书证明官职及使臣身份；实际十一月册礼分工另据《辽史》引用，两书差异保留。',source='jiuwudaishi-077-august')
reviews={17:'八月上尊号及任使与实际册礼分开；辽史十一月补行礼日及参与，旧史使团分工异说、刘句/刘煦/刘昫字形保留。长期礼节、赠礼、责让、耻辱反应与后改称儿皇帝均为追述，年份留空；政治父子不建亲属，匿名诸王不猜姓名。',18:'初提示幽州留守、祁州刺史及归附请求追叙，年月留空。赵思温复用，赵延照新建父子方向明确；辽史证留守及父子身份，其他生涯未另作本年事件。',19:'唐为徐诰的南唐；使者到访与宋齐丘离间建议分开，建议不写成实际暗杀。',20:'壬午上奏、己丑任冯晖、长期围城、朱宪承诺与范延光迟疑、刘处让再劝、九月送二子、奉表、宣诏赦免分别录入。旧史证冯暉归降任职及九月奉表赦免；父亲方向明确，不推二子长幼或人质。'}
assert not (P/'publication.json').exists()
for n in range(17,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=938,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(17,21)],next_paragraph=Q[21]['id'],next_volume=281,next_year=938,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第17—20段，原83—86行；后晋契丹册礼和长期交往、赵思温归附请求、南唐离间建议、冯晖归降和范延光正式归降。938年未完成。',source_issues_review='原文逐字回查，旧五代史卷77及辽史卷4、76卷题传主已核；使团分工、姓名字形及任使/行礼日期分别说明。电子本纸本未核，长期追述日期留空。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(17,21)],plain_language_review='首次整理逐条检查主语、角色、事件和解释，政治称谓与血缘、计划与执行、奏报与确定事实分别说明，引文原字不改。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
