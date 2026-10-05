# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 948 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,70))
COMMIT='b9977b40cd7afc61ddc81473948ffdd463d53ee9'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-948-march','jiuwudaishi-101-march-close-948','jiuwudaishi-101-april-dingzhou-948']:
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
main_sources = ['tongjian-288-948-march','tongjian-288-948-march-april-conflict']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0948-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
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
lines = (ROOT / 'resources/derived/tongjian/288.txt').read_text().splitlines()
for n in range(9, 17):
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
    labels={'songshi-262-li-tao-dismissal':'卷262·李涛传·免相','tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐元年（948年三月至四月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0948_03_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=948, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='948年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0948_' + code
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
        edge = 'participation_zztj_288_0948_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0948_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'李涛':'李涛（后晋宋初官员）','王继勋':'王继勋（李守贞将）','王玉':'王玉（陕州都监）'})
NEW_ALIASES={'赵修己':['趙修己'],'总伦':['總倫'],'王继勋（李守贞将）':['王继勋（平陆将领）'],'罗金山':['羅金山'],'李仁裕':[],'王玉（陕州都监）':['王玉（后汉陕州都监）']}
NEW_DESCRIPTIONS={
 '赵修己':'浚仪人，擅长术数。李守贞镇滑州时任司户参军，随后随李守贞移镇。948年叛乱前多次劝其不要轻动，未获采纳，称病回乡。生卒年未载，未将后周同名司天官的经历无证并入。',
 '总伦':'李守贞门下僧人，以方术预言李守贞将成为皇帝，受到其相信。《新五代史》也记总伦以方术影响李守贞，预言均按说话者的主张记录。生卒年未载。',
 '王继勋（李守贞将）':'平陆人，李守贞部将。948年李守贞自称秦王后，派他率兵占据潼关。与闽国王氏宗族成员和宋代同名人物分开，未作无证合并。生卒年未载。',
 '罗金山':'云州人，948年任滑州马军都指挥使，奉诏率本部兵驻守同州，使同州未被李守贞起兵吞并。生卒年未载。',
 '李仁裕':'《资治通鉴》引948年李彝殷奏文，称李仁裕原任绥州刺史，此前被羌族首领杀害。该首领姓名有疑字，奏文所述相对时间未换算具体死亡年，相关信息尚待其他史料补核。',
 '王玉（陕州都监）':'948年任陕州都监，《旧五代史》称陕州兵马监押。四月辛巳向朝廷奏报收复潼关，实际作战日和是否本人指挥未具明文。与其他年代同名王玉分开，生卒年未载。'}
close='jiuwudaishi-101-march-close-948';apr='jiuwudaishi-101-april-dingzhou-948';song='songshi-262-li-tao-dismissal';new='xinwudaishi-052-li-shouzhen-revolt';tiger='xinwudaishi-052-zonglun-tiger-omen';yang='jiuwudaishi-107-yang-bin-power';m='948年三月，具体日未载'
add('yang_blocks_minister_appointments','苏逢吉等频繁调补官吏，杨邠阻止许多奏请',9,'苏逢吉等为相，','逢吉等不悦。',[('苏逢吉','与其他宰相调补官吏，对奏请遭阻不满'),('杨邠','认为浪费国用，阻止许多任官奏请')],when=m,place='后汉朝廷',note='虚费国用是杨邠的判断，不直接作为独立财政审计结果；不补官吏人数或金额。')
add('li_tao_proposes_transfer_pivotal_officials','李涛建议杨邠、郭威出镇，将枢密事务交苏逢吉等',9,'中书侍郎兼户部尚书、','皆可委也。”',[('李涛','上疏建议调两枢密到要害大镇，将机务交两苏'),('杨邠','被建议出镇'),('郭威','被建议出镇'),('苏逢吉','被建议承担枢密事务'),('苏禹珪','被建议承担枢密事务')],when=m,place='后汉朝廷',description='李涛认为关西纷扰、外部防御紧急，建议让功臣杨邠和郭威出任要害藩镇，将皇帝身边的枢密事务交给苏逢吉、苏禹珪。',note='这是建议，未写成两人已调出京。官贵而家未富为李涛奏文的说法。李涛沿用后晋宋初官员主体，与晚唐同名人物分开。')
add('yang_guo_complain_to_empress_dowager','杨邠、郭威向李太后哭诉，请求留过山陵事务',9,'杨邠、郭威闻之，','乞留过山陵。”',[('杨邠','向太后哭诉出镇建议，提出暂留的请求'),('郭威','共同哭诉，称不愿避开关西事务'),('李氏（刘知远妻）','听取两名枢密官的哭诉')],when=m,place='后汉宫廷',note='哭诉所述功勋、被弃之感属于两人主张。请求留过山陵事务不等于任命两人为山陵使。')
add('empress_dowager_rebukes_li_chengyou','李太后斥责刘承祐听人言排斥功臣',9,'太后怒，','此宰相所言也。”',[('李氏（刘知远妻）','责问皇帝为何听人建议排斥功臣'),('刘承祐','回答是宰相建议')],when=m,place='后汉宫廷',note='李太后是刘知远妻、刘承祐母亲；天子已是刘承祐，不沿用刘知远。')
add('li_tao_accepts_sole_responsibility','刘承祐责问宰相，李涛称奏疏由自己独立提出',9,'因诘责宰相。','他人无预。”',[('刘承祐','责问宰相'),('李涛','称奏疏是自己提出，其他人未参与')],when=m,place='后汉朝廷',note='独为奏疏是李涛的回答，不把未具名宰相都当作参与策划的确定人物。')
add('li_tao_dismissed','李涛被罢免宰相职务，勒令回私宅',9,'丁丑，',None,[('李涛','被罢免政事，勒归私宅')],when='948年三月丁丑',place='后汉朝廷',note='免相与后续其他官衔不同，不写为已被处死或流放。')
sup('li_tao_dismissed',9,close,'丁丑，中書侍郎兼戶部尚書、平章事李濤罷免，勒歸私第。','《旧五代史》同记丁丑李涛被免相、勒归私第。','同名身份沿用已经核对的后晋宋初官员，不合入887年李涛。')
sup('li_tao_dismissed',9,song,'隱帝不能決，白於太后，太后召邠等諭之，反為所構，免相歸第。','《宋史》记刘承祐不能决定，先向太后说明，太后召杨邠等劝谕，李涛反被构陷，免相回家。','《通鉴》叙杨邠、郭威先向太后哭诉，程序顺序与宋史不同；构陷是宋史的评价，保留独立异说。',relation='conflicts')
add('four_commands_report_rebellion','邠、泾、同、华四镇报告李守贞与永兴、凤翔同反',10,'是日，',None,[('李守贞','被四镇报告与两地一同反叛')],when='948年三月丁丑',place='邠州、泾州、同州、华州至后汉朝廷',note='是日承接上段丁丑，为报告日，不是各地起兵同时发生的证明；不新增无证盟友关系。')
add('li_shouzhen_fears_after_du_execution','李守贞得知杜重威被杀后恐惧，产生异志',11,'始，','有轻朝廷之志。',[('李守贞','因杜重威死而惧，自恃战功和士卒支持，轻视新朝廷'),('杜重威','其已被处死成为李守贞恐惧的背景')],when='948年正月杜重威被处死后、李守贞起兵之前',place='河中',note='自认为朝廷新建、皇帝年少及执政资历浅是史述李守贞判断，不转成客观能力结论。')
sup('li_shouzhen_fears_after_du_execution',11,new,'高祖崩，杜重威死，守貞懼，不自安，以謂漢室新造，隱帝初立，天下易以圖，','《新五代史》同记高祖去世、杜重威死后，李守贞不安，认为新朝容易谋取。','只印证心理背景，不把其判断当作叛乱必然成功。')
add('li_shouzhen_prepares_revolt','李守贞招纳亡命、养死士，整修城防和兵器',11,'乃招纳亡命，','昼夜不息。',[('李守贞','招人准备叛乱，修城壕、备甲兵')],when='948年起兵之前，具体日未载',place='河中',note='备战已进行，但没有人数和修城工期，不补数字。')
add('li_shouzhen_contacts_khitan_intercepted','李守贞遣使携蜡丸书联络契丹，多次被边吏截获',11,'遣人间道',None,[('李守贞','派人走小路联络契丹，使者多次被截获')],when='948年起兵准备期间，具体日未载',place='河中至契丹方向',note='企图联络不等于契丹已承诺援助，使者与边吏未具姓名，不虚构。')
sup('li_shouzhen_contacts_khitan_intercepted',11,new,'又遣人間以蠟丸書遺吳、蜀、契丹，使出兵以牽漢。','《新五代史》补记李守贞用蜡丸书联络吴、蜀和契丹，意在让它们出兵牵制后汉。','此书把联络放在推秦王、授爵之后，主书此段写备战时联络契丹，次序和对象不同；请求不等于三方已出兵。',relation='adds')
add('zhao_xiuji_serves_li','赵修己在李守贞镇滑州时任司户参军，随后随镇',12,'浚仪人赵修己，','累从移镇，',[('赵修己','擅术数，任司户参军，随李守贞移镇'),('李守贞','任赵修己为司户参军')],year=None,when='李守贞镇滑州至移镇河中期间，具体起年未载',place='滑州及李守贞各任所',note='从移镇是随主将迁任，不将这段早年任职强定948年。')
add('zhao_xiuji_warns_and_retires','赵修己多次劝李守贞勿动，未被听取后称病归乡',12,'为守贞言：','称疾归乡里。',[('赵修己','多次劝阻，未获听从，称病回乡'),('李守贞','不听赵修己劝告')],when='948年李守贞公开起兵前，具体日未载',place='河中至浚仪',note='时命不可是术数判断，按赵修己的话记录；称疾不等于确认他患具体疾病。')
add('zonglun_predicts_li_emperor','僧人总伦预言李守贞必为天子，李守贞相信',12,'僧总伦，','守贞信之。',[('总伦','以方术迎合李守贞，预言其将称帝'),('李守贞','相信预言')],when='948年起兵之前，具体日未载',place='河中',note='预测按僧人的主张记录，不写成李守贞已称帝或预言应验。')
sup('zonglun_predicts_li_emperor',12,new,'而門下僧總倫以方術陰干守貞，為言有非常之相，守貞乃決計反。','《新五代史》也记总伦以方术影响李守贞，说其有非常之相，李守贞决定反叛。','动机联系归史书，不把相术当作事实证明。')
add('li_shouzhen_shoots_tiger_painting','李守贞射中画虎，接受将佐祝贺并更加自负',12,'又尝会将佐','守贞益自负。',[('李守贞','在宴会中以射虎图试福，射中后更加自负')],year=None,when='李守贞自称秦王之前的宴会追叙，具体年月未载',place='李守贞宴会处',description='李守贞宴请将佐，指《舐掌虎图》说若自己有非凡福分便当射中虎舌，随后一箭命中，左右祝贺，他更加自负。',note='命中是史载动作，但不能证明超自然福分；宴会未具年月，不套三月丁丑。')
sup('li_shouzhen_shoots_tiger_painting',12,tiger,'守貞指畫虎圖曰：「吾有天命者中其掌。」引弓一發中之，將吏皆拜賀，守貞益以自負。','《新五代史》也记射画虎获祝贺，但射击目标写虎掌，且用天命措辞。','主书目标是虎舌，新史目标是虎掌，细节并列保留，不静默统一。',relation='conflicts')
add('zhao_offers_imperial_clothing_li','赵思绾据长安后奉表，将御衣献给李守贞',12,'会赵思绾据长安，','奉表献御衣于守贞，',[('赵思绾','夺城后送表和御衣给李守贞'),('李守贞','接受赵思绾献表御衣')],when='948年三月赵思绾据长安之后，具体日未载',place='长安至河中',note='御衣为原文称呼，不等于朝廷承认李守贞皇位。')
sup('zhao_offers_imperial_clothing_li',12,new,'而趙思綰先以京兆反，遣人以赭黃衣遺守貞，守貞大喜，','《新五代史》补称所献衣服是赭黄衣，李守贞很高兴。','衣服颜色是该书细节，不换成无来源的正式册封礼制。',relation='adds')
add('li_shouzhen_claims_qin_prince','李守贞自称秦王',12,'守贞自谓','乃自称秦王。',[('李守贞','认为天意人心相合，自称秦王')],when='948年三月，具体日未载',place='河中',note='自称秦王不是已当皇帝，也不是后汉授封。天人协契归其自我判断。')
sup('li_shouzhen_claims_qin_prince',12,new,'景崇與思綰遣人推守貞為秦王，守貞拜景崇等官爵。','《新五代史》记王景崇、赵思绾遣人推李守贞为秦王，他给王景崇等授官爵。','主书记自称，新史补他人推戴及授官，但放在后汉已经出兵后，叙次不同，不据此改主书日期。',relation='adds')
add('wang_jixun_seizes_tongguan','李守贞派王继勋率兵占据潼关',12,'遣其骁将','将兵据潼关，',[('李守贞','派平陆部将王继勋占据潼关'),('王继勋','率兵占据潼关')],when='948年三月，具体日未载',place='潼关',note='王继勋单独限定李守贞将身份，与闽国王氏宗族主体分开。')
add('li_shouzhen_grants_zhao_governorship','李守贞授赵思绾晋昌节度使',12,'以思绾',None,[('李守贞','自行授赵思绾官职'),('赵思绾','接受李守贞授晋昌节度使')],when='948年三月，具体日未载',place='河中、长安',note='是叛乱方授官，后汉已改军号永兴，叛方仍称晋昌，不提前覆盖朝廷军号。')
add('zhang_requests_tongzhou_defense','张彦威侦察李守贞动向，请求预备同州防守',13,'同州距','奏请先为之备。',[('张彦威','任匡国节度使，侦察李守贞并请先防备'),('李守贞','其动向受到邻镇侦察')],when='948年李守贞起兵之前，具体日未载',place='同州、河中',note='同州距河中最近为本段相对地理判断，不生成未经核实的距离公里数。')
add('luo_jinshan_garrisons_tongzhou','后汉命罗金山率部戍守同州',13,'诏滑州','将部兵戍同州。',[('罗金山','以滑州马军都指挥使身份率部戍同州')],when='948年李守贞起兵之前，具体日未载',place='滑州至同州',note='奉诏及后文防守结果相连，未载兵数，不补几千或几万。')
claim('person',people['罗金山'],'description','罗金山是云州人。',13,'金山，云州人也。','籍贯不当作当前驻守地，展示简体，引用原字保留。')
add('tongzhou_not_absorbed','李守贞起兵后未能吞并同州',13,'故守贞起兵，','同州不为所并。',[('李守贞','起兵后未能吞并同州'),('罗金山','此前率兵守同州，构成史述原因')],when='948年李守贞起兵之后，具体日未载',place='同州',note='主书明确防守结果及此前驻兵因果，不推战死人数或未载交战细节。')
add('li_yiyin_requests_qiang_campaign','李彝殷屯兵边境，奏请讨此前杀李仁裕的羌族首领',14,'定难节度使','请讨之。”',[('李彝殷','屯兵边境，提出讨伐请求'),('李仁裕','在奏文中被称为此前被杀的绥州刺史')],when=m,place='定难军边境',description='李彝殷在边境屯兵，奏称羌族首领此前杀害绥州刺史李仁裕并反叛离去，请求讨伐。首领姓名含疑字，暂不规范为确定人名。',note='所述杀害及时间来自李彝殷奏称，未独立确证。去三载前表述待核，不直接换算死年；原文疑字保持，首领未具可确定姓名，不建虚构主体。')
add('qingzhou_requests_reinforcement','庆州请求增兵防备',14,'庆州上言：','请益兵为备。”',[],when=m,place='庆州',note='这是增兵请求，不写成朝廷已经批准、援军已经到达。')
add('han_halts_li_yiyin_campaign','后汉以司天判断为由，制止李彝殷先动兵',14,'诏以司天言，',None,[('李彝殷','其主动出兵请求被朝廷制止')],when=m,place='后汉朝廷、定难军',note='今岁不利先举兵是司天意见和诏令所据理由，不作实际军事胜败预测；司天官未具姓名。')
add('wang_yu_reports_tongguan_recovery','王玉奏报收复潼关',15,'夏，',None,[('王玉','以陕州都监身份向朝廷奏报收复潼关')],when='948年四月辛巳奏报，实际作战日未载',place='潼关、后汉朝廷',note='辛巳是奏报日，不当作战斗发生日；未载是否王玉亲自统军，不补其作战角色。')
sup('wang_yu_reports_tongguan_recovery',15,apr,'夏四月辛巳，陜州兵馬監押王玉奏，收復潼關。','《旧五代史》同记四月辛巳收复潼关奏报，写王玉职为陕州兵马监押。','都监与兵马监押表述分别保留，姓名和同次报告对应同一主体。',relation='adds')
add('liu_plans_promote_pivotal_officials','刘承祐与左右商议进用杨邠、郭威，以表明自己无意排斥',16,'帝与左右谋，','共劝之。',[('刘承祐','因太后动怒，谋划进一步进用两枢密官'),('杨邠','成为拟进一步进用的枢密官'),('郭威','成为拟进一步进用的枢密官')],when='948年四月壬午任官之前，具体日未载',place='后汉宫廷',note='左右欲夺二苏之权为史书记述，没有具名，不擅自把史弘肇或王章列为参与劝说者。')
add('yang_bin_becomes_chancellor','杨邠任宰相，仍兼枢密使',16,'壬午，','枢密使如故，',[('杨邠','任中书侍郎兼吏部尚书、同平章事，仍任枢密使')],when='948年四月壬午',place='后汉朝廷',note='新增宰相职位并不取消原枢密职务；不与李涛提议出镇混淆为被调离京师。')
sup('yang_bin_becomes_chancellor',16,apr,'壬午，以樞密使楊邠為中書侍郎兼吏部尚書、平章事，使如故；','《旧五代史》同记壬午杨邠拜相、枢密职仍旧。','本纪正文独立补证，官名略有省写，不更改主体。')
add('guo_wei_pivotal_commissioner','郭威由副枢密使升为枢密使',16,'以副枢密使郭威','为枢密使，',[('郭威','由副职升为枢密使')],when='948年四月壬午',place='后汉朝廷',note='晋升而非出镇，不提前记为后周皇帝。')
sup('guo_wei_pivotal_commissioner',16,apr,'以副樞密使郭威為樞密使，加檢校太尉；','《旧五代史》同记郭威由副枢密使升枢密使，并补加检校太尉。','官衔补充来自同次任命，日期沿壬午条。',relation='adds')
add('wang_zhang_receives_chancellor_rank','三司使王章加同平章事',16,'又加三司使','王章同平章事。',[('王章','以三司使身份加同平章事')],when='948年四月壬午',place='后汉朝廷',note='同平章事为加衔，未写王章因此免三司职。')
sup('wang_zhang_receives_chancellor_rank',16,apr,'三司使王章加檢校太尉、同平章事。','《旧五代史》同记王章加同平章事，另补检校太尉。','只补同次官衔，不造离任或出镇行为。',relation='adds')
add('yang_controls_court_decisions','刘承祐把任官和奏事交杨邠裁决，政务开始迟滞',16,'凡中书除官，','遂成凝滞。',[('刘承祐','将任官、诸司奏事交杨邠斟酌'),('杨邠','掌握政事裁决，未决事项不能执行')],when='948年四月任宰相后持续形成，具体日未载',place='后汉朝廷',description='刘承祐将中书任官和各司奏事交杨邠斟酌。此后政事多由杨邠裁决，其他宰相受到限制，未获其决定的事项无人敢执行，导致政务迟滞。',note='政务停滞是史书对制度运行的叙述，不补现代审批时长统计。')
sup('yang_controls_court_decisions',16,yang,'及邠居相位，帝一以委之，凡南衙奏事，中書除命，先委邠斟酌，如不出邠意，至於一簿一掾，亦不聽從。','《旧五代史》杨邠传也记皇帝把奏事任官交他斟酌，连小官也须合其意。','传记概述没有逐次日期，不把全部制度实践压成壬午当天。')
add('yang_restricts_appointments','杨邠限制任官，强调仓储兵力，轻视文章礼乐',16,'三相每进拟用人，','往往有自汉兴至亡不沾一命者。',[('杨邠','限制任官，认为仓储充实和军备强为急务'),('苏逢吉','与苏禹珪的任官做法受到杨邠反对'),('苏禹珪','与苏逢吉的任官做法受到杨邠反对')],year=None,when='杨邠任相后制度实践及汉兴至亡的回顾，具体持续年月未逐项载明',place='后汉朝廷',description='杨邠要求任官符合自己的意见，认为仓储和兵力比文章礼乐更紧要，反对苏逢吉、苏禹珪任官过多，因此难以任用士人。史书回顾称有些人从后汉建立到灭亡都未获任命。',note='自汉兴至亡是史家回顾，不能当作948年已发生后汉灭亡；杨邠评价与史述不作为全体官员无才的结论。')
sup('yang_restricts_appointments',16,yang,'邠雖長於吏事，不識大體，常言：「爲國家者，但得帑藏豐盈，甲兵強盛，至於文章禮樂，並是虛事，何足介意也。」','《旧五代史》也记杨邠强调财储军备、轻视文章礼乐，并评价他擅吏事却不识大体。','能力评价归该书；引用保留底本爲、於等字形。',relation='adds')
add('yang_stops_hereditary_and_office_entry','杨邠停止门荫及百司入仕渠道',16,'凡门廕','悉罢之。',[('杨邠','停止原文所称门荫和百司入仕渠道')],year=None,when='杨邠任相之后，具体实施年月未载',place='后汉朝廷',note='门荫是凭父祖官位获得入仕资格，百司指各司入仕渠道；不扩成全国所有官职和科举一律取消。')
add('historians_assess_appointment_impasse','史书记杨邠任官弊病及当时人对两苏的责备',16,'虽由邠之愚蔽，',None,[],year=None,when='史家对后汉任官制度的总结及所记时人评论，非单日事件',place='史家评论',note='这是史家评价与所载时人意见，不当作948年朝廷颁行的处分或奏章。')
reviews={9:'苏任官杨抑、李出镇建议、杨郭哭诉、太后责帝、帝责相、李独承、丁丑免相分录；宋史先帝白太后程序不同，保留。李涛复用后晋宋初规范主体，不合887同名。',10:'是日承三月丁丑，只是四镇报告日，不造共同发兵同日或固定盟约。',11:'杜死亡后恐惧、自视朝廷弱、招人修城备甲、蜡丸联络被获分录；新史联络吴蜀契丹叙次不同，请求未当实际援军。',12:'赵修己早任未知年，多劝称疾归；僧预言按言说，射虎未知年，主舌新掌异说；献御衣、自秦王、王继勋据潼、授赵晋昌分录。王继勋限定平陆将，与闽族同名分开。',13:'侦察请备、罗奉诏戍守、同州未被并分录；云州籍贯不写为现驻军；无兵数和额外交战。',14:'李屯边请求、庆求兵、朝廷以司天言止分；首领名有私用疑字，不强规范建人。李仁裕被杀与相对时间属奏称，死年不推算。',15:'四月辛巳王玉奏报日，不等实际复关作战日；旧职兵马监押、主都监保留，未造本人作战身份。',16:'帝谋、壬午杨相兼枢、郭正枢、王章加衔、杨专决迟滞、任官限制、门荫百司停、史评分录。汉兴至亡为史家回顾，不记948灭汉。左右匿名不强指具体权臣，杨评价及对二苏指责归说话者/史书。'}
assert not (P/'publication.json').exists()
for n in range(9,17):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=948,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=288,next_year=948,supplements=supplements,excluded_non_body=[],coverage='卷288原15—22行连续八段，本卷16/69；卷287已19段，全年35/88，尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],source_issues_review='免相程序主宋不同；主虎舌新虎掌；秦王推戴、联络对象与叙次保留。羌族首领名疑字及李仁裕死年暂不推定。李涛和王继勋同名者按已核身份分开，奏报日、拟议任命与实任区别。',plain_language_review='首次逐条核对人物、标题、事件正文、时间、角色及事实说明；明确言说和史评归属、书卷定位和代词主体，引用原字保留。不把提议当执行、奏报当作战日、回顾汉亡当948事实，不设发布后二次文案重写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
