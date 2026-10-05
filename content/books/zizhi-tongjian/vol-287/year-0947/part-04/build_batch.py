# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 25–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,76))
COMMIT='44b0593aeab837b5fbc1263a74f880f3ba1b4acb'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-jinzhou-north-return','jiuwudaishi-100-june-arrivals','xinwudaishi-067-qian-zong-succession']:
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
main_sources = ['tongjian-287-947-jinzhou-north-return','tongjian-287-947-june-july-governors']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p025-p032',
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
lines = (ROOT / 'resources/derived/tongjian/287.txt').read_text().splitlines()
for n in range(25, 33):
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
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷287·天福十二年（947年六月至七月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_04_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_287_0947_' + code
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
        edge = 'participation_zztj_287_0947_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_287_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','契丹主':'耶律阮','太后':'述律平','伟王':'伟王（契丹）','李彦韬':'李彦韬（后晋宣徽使）','麻荅':'麻答','崇':'刘崇（刘知远弟）','唐主':'李璟','弘倧':'钱弘倧','弘亻叔':'钱弘俶','刘鐸':'刘铎'})
NEW_ALIASES={'樊晖':['樊暉'],'刘铎':['劉鐸']}
NEW_DESCRIPTIONS={'樊晖':'947年任奉国军都虞候，随王继弘驻相州，与王继弘杀高唐英。六月庚辰获任磁州刺史。《旧五代史》王继宏传作樊暉，本纪相关杀人条作楚暉，字形差异保留待核。生卒年未载。','刘铎':'947年任马步都指挥使。安国节度使高奉明离镇前，请麻答安排刘铎为节度副使、主持军府事务。生卒年未载。'}
j='jiuwudaishi-100-june-arrivals';july='jiuwudaishi-100-july-transfers';wang='jiuwudaishi-125-wang-jihong';lv='liaoshi-005-june-vanguard';ls='liaoshi-005-shulu-confrontation';lt='liaoshi-005-tianlu-titles';zd='liaoshi-076-zhao-yanshou-death';qian='xinwudaishi-067-qian-zong-succession';t='947年六月，具体日未载'
add('qian_hongzong_succeeds','钱弘倧继承吴越王位',25,'丙寅，',None,[('弘倧','继承吴越王位')],when='947年六月丙寅',place='吴越',note='实际袭位区别此前钱弘佐遗命指定掌两军。')
sup('qian_hongzong_succeeds',25,qian,'佐卒，弟倧以次立。','《新五代史》同记钱佐死后，弟弟钱倧继位。','补书未给干支日；前段简写俶继位与此段倧先立的层次已核，不跳过钱弘倧。')
add('liu_amnesty','刘知远下诏大赦',26,'戊辰，','帝下诏大赦。',[('帝','下诏大赦')],when='947年六月戊辰',place='大梁')
sup('liu_amnesty',26,j,'應天福十二年六月十五日昧爽已前，天下見禁罪人','《旧五代史》戊辰诏文指定天福十二年六月十五日昧爽以前的在押罪人。','本纪诏文另有除十恶五逆等限制，主书概述大赦不解释为无条件赦免所有人。',relation='adds')
add('liu_preserves_khitan_appointments','刘知远保留契丹所任节度使及将吏的职任',26,'凡契丹所除','不复变更。',[('帝','宣布保留契丹所任官员的现职')],when='947年六月戊辰条下',place='后汉诸军镇',note='记此次安职政策，不推任何官员此后永不被更换。')
sup('liu_preserves_khitan_appointments',26,j,'契丹所授職任，不議改更。','《旧五代史》同记不议更改契丹所授职任。','复用同一政策，未将后续具体任免全部归到此日。')
add('liu_restores_tokyo_han_title','刘知远恢复汴州东京称号，定国号汉并沿用天福纪年',26,'复以汴州','余未忍忘晋也。”',[('帝','恢复东京称号，改国号汉，沿用天福纪年并说明未忍忘晋')],when='947年六月戊辰条下',place='汴州东京',note='未忍忘晋为刘知远对纪年选择的自述，国号与年号分别记；不将国号汉与刘岩南汉混合。')
sup('liu_restores_tokyo_han_title',26,j,'宜以國號為大漢，年號依舊稱『天福』','《旧五代史》诏文也定国号大汉，并沿用天福年号。','主书汉与补书大汉为各自称谓，均沿同一后汉政权。')
add('liu_restores_three_commands','刘知远恢复青州、襄州、汝州三处节度建制',26,'复青、','汝三节度。',[('帝','恢复三处节度建制')],when='947年六月戊辰条下；《旧五代史》记己巳复节镇',place='青州、襄州、汝州',note='主书第三州作汝，旧史作安；名称及诏日分别保留，不默改为同一地点。')
sup('liu_restores_three_commands',26,j,'己巳，詔青州、襄州、安州復為節鎮','《旧五代史》记己巳恢复青州、襄州、安州节镇。','第三州安州与主书汝州有异，旧书记己巳，与主书大赦条下分层保留。',relation='conflicts')
add('liu_chong_hedong_chancellor','刘崇获任河东节度使、同平章事',26,'壬申，',None,[('帝','任命刘崇为河东节度使、同平章事'),('崇','由北京留守获任河东节度使、同平章事')],when='947年六月壬申',place='太原河东',note='复用刘知远之弟刘崇，不与萧县同名人混合。')
sup('liu_chong_hedong_chancellor',26,j,'壬申，北京留守劉崇加同平章事。','《旧五代史》同日记刘崇加同平章事。','此句只独立支持加同平章事，不扩充成补书也明确同日任河东节度使。')
add('shulu_mobilizes_ruan_vanguard','述律平发兵抵抗耶律阮，耶律阮以伟王为前锋',27,'契丹述律太后','相遇于石桥。',[('太后','得知耶律阮自立，发兵抵抗'),('契丹主','任伟王为前锋'),('伟王','率前锋与太后军相遇于石桥')],when='947年耶律阮北归期间，主书置六月叙事中，具体日未载',place='石桥',note='伟王复用未定姓名的契丹王爵主体；不据别书前锋为安端就未经核定直接合并。')
sup('shulu_mobilizes_ruan_vanguard',27,lv,'至泰德泉，遇李胡軍，戰敗之。上遣郎君勤德等詣兩軍諭解。','《辽史》六月条另记前锋在泰德泉击败李胡军，耶律阮遣人向两军解释。','本段上文前锋为安端、刘哥；地名和参战者与主书石桥叙事不同，不强拼为同一场交战或合并伟王身份。',relation='adds')
add('li_yantao_serves_shulu','李彦韬随石重贵北迁后，受述律平任为排陈使',27,'初，晋侍卫','太后以为排陈使。',[('李彦韬','以原晋侍卫马军都指挥使身份随石重贵北迁，后任排陈使'),('太后','将李彦韬置于麾下，任为排陈使')],when='947年晋主北迁后、契丹内争以前，具体任命日未载',place='契丹境内',note='晋主指后晋石重贵；此为背景追叙，复用后晋宣徽使李彦韬，不与已死亡的温韬所用旧名混合。')
add('li_yantao_surrenders_shulu_defeat','李彦韬向伟王投降，述律平军随后大败',27,'彦韬迎降','太后兵由是大败。',[('李彦韬','迎降伟王'),('伟王','接受李彦韬投降'),('太后','军队战败')],when='947年耶律阮北归内争期间，具体日主书未载',place='石桥及其后战场',note='由是是史家对投降与败军的因果解释，不虚构作战细节。')
sup('li_yantao_surrenders_shulu_defeat',27,ls,'太后、李胡整兵拒於橫渡，相持數日。用屋質之謀，各罷兵趨上京。','《辽史》闰七月记太后与李胡在横渡拒军，相持后采用屋质之谋，双方罢兵往上京。','补书对峙、调停及月份与主书败军叙述层次不同；保留完整异叙，不能用补书确认主书李彦韬投降的每个细节。',relation='conflicts')
add('ruan_confines_shulu','耶律阮将述律平幽禁于耶律阿保机墓地',27,'契丹主幽','于阿保机墓。',[('契丹主','幽禁述律平'),('太后','被幽禁于阿保机墓地')],when='947年契丹内争之后；旧史记七月，辽史置闰七月',place='耶律阿保机墓地',note='主书未给具体月份，后置六月条中不能排除后续月份；墓地、木叶山及祖州按各书原称保留。')
sup('ruan_confines_shulu',27,july,'是月，契丹永康王烏裕囚祖母舒嚕氏於木葉山。','《旧五代史》七月条记耶律阮将祖母述律平囚于木叶山。','烏裕、舒嚕沿既有规范主体；月份与主书叙事位置分别保留。',relation='adds',field='time_original')
sup('ruan_confines_shulu',27,ls,'既而聞太后、李胡復有異謀，遷於祖州。','《辽史》记罢兵后又听说太后、李胡有异谋，将二人迁至祖州。','复有异谋是获闻的说法；迁祖州与主书幽墓叙述并列，不默改拘禁经过。',relation='adds')
relationship('太后','契丹主','祖母',27,'烏裕囚祖母舒嚕氏於木葉山','《旧五代史》明确述律平是耶律阮的祖母，方向表示述律平相对于耶律阮的身份。',source=july)
add('ruan_tianlu_emperor_title','耶律阮改元天禄，采用天授皇帝称号',27,'改元天禄，','自称天授皇帝，',[('契丹主','改元天禄，采用天授皇帝称号')],when='947年内争后；《辽史》记九月丁卯柴册礼',place='契丹朝廷',note='主书未明示确月，辽史将相关礼仪置九月；自称与群臣上尊号的表述分别引用。')
sup('ruan_tianlu_emperor_title',27,lt,'丁卯，行柴冊禮，群臣上尊號曰天授皇帝。大赦，改大同元年為天祿元年。','《辽史》九月丁卯记柴册礼、群臣上天授皇帝尊号，并改天禄元年。','补书给出礼仪日期及群臣上号，不把主书未载的月份固定为六月。',relation='adds',field='time_original')
add('gao_xun_privy_appointment','耶律阮任高勋为枢密使',27,'以高勋','为枢密使。',[('契丹主','任高勋为枢密使'),('高勋','获任枢密使')],when='947年；《辽史》记九月任南院枢密使',place='契丹朝廷')
sup('gao_xun_privy_appointment',27,lt,'高勛為南院樞密使。','《辽史》在九月礼仪任官条下记高勋为南院枢密使。','补明南院与纪时，主书未分南北院，不推两个独立任命。',relation='adds')
add('ruan_rule_rebellions_evaluation','《资治通鉴》评述耶律阮用晋臣、诸部反叛及其数年未暇南侵',27,'契丹主慕',None,[('契丹主','史书记其用晋臣、讨诸部叛乱，并解释未暇南侵')],when='947年继位后数年，具体各事发生日未载',year=None,place='契丹诸部',note='此段为跨年总结，史家将酒色、轻慢、反叛与未暇南侵相联系；不把全部叛乱或数年经过压到947年六月。',description='《资治通鉴》记耶律阮喜爱中原风俗、任用晋朝官员，又批评他沉于酒色、轻慢酋长。史家认为诸部因此多次反叛，他忙于讨伐，数年间无暇南侵。此处保留为跨年评述，具体叛乱仍按后文逐段录入。')
add('deguang_station_wang_fan_xiangzhou','耶律德光令王继弘、樊晖率奉国兵驻相州',28,'初，契丹主德光','高唐英善待之。',[('耶律德光','命奉国兵驻相州'),('王继弘','以奉国都指挥使身份率兵驻相州'),('樊晖','以都虞候身份率兵驻相州'),('高唐英','善待驻军将领')],when='947年耶律德光去世以前，具体驻军日未载',place='相州',note='初为此前驻军背景；南宫是王继弘籍贯，不是此次驻军地点。')
sup('deguang_station_wang_fan_xiangzhou',28,wang,'為奉國指揮使，從契丹主至相州，遂令以本軍戍守。','《旧五代史》王继宏传也记其以奉国指挥使率本军驻相州。','主书王继弘、补书王继宏沿既有同人别名，不另建人物。')
add('gao_supplies_xiangzhou_garrison','高唐英向相州驻军提供铠甲兵器',28,'戍兵无铠仗，','倚信如亲戚。',[('高唐英','向缺乏装备的驻军提供铠甲兵器，信任其将领'),('王继弘','其驻军获得高唐英供应')],when='947年驻相州以后、请降以前，具体日未载',place='相州',note='如亲戚是信任程度的比喻，不建血缘或姻亲关系。')
add('gao_tangying_requests_surrender','高唐英闻刘知远南下，派使者请求归降',28,'唐英闻帝南下，','举镇请降。',[('高唐英','举镇请降刘知远')],when='947年刘知远南下后、使者返还以前，具体日未载',place='相州',note='请降是实际遣使请求，尚未等到回报，不能写成已完成正式归附手续。')
add('wang_fan_kill_gao','王继弘、樊晖在请降使者返回前杀高唐英',28,'使者未返，','继弘、晖杀唐英。',[('王继弘','与樊晖杀高唐英'),('樊晖','与王继弘杀高唐英'),('高唐英','在使者返回前被杀')],when='947年六月，具体日未载',place='相州')
sup('wang_fan_kill_gao',28,wang,'使未回，繼宏與指揮使樊暉等共殺唐英','《旧五代史》王继宏传同记使者未回时，王继宏与樊晖等杀高唐英。','樊暉与主书樊晖字形相合，补书明确共同杀人。')
sup('wang_fan_kill_gao',28,j,'是月，契丹所命相州節度使高唐英為屯駐指揮使王繼宏、楚暉所殺。','《旧五代史》六月本纪也记高唐英被王继宏及楚晖所杀。','本纪楚暉与该书王继宏传樊暉、主书樊晖存在姓名差异，分别保留，不自动添加未经核定的楚晖别名。',relation='conflicts')
add('wang_jihong_claims_gao_fickle','王继弘自称留后，并向刘知远指称高唐英反覆',28,'继弘自称留后，','告云唐英反覆，',[('王继弘','自称留后，遣使以高唐英反覆为说辞')],when='947年六月高唐英被杀后，具体日未载',place='相州至刘知远朝廷',note='反覆是王继弘向朝廷提出的指控，不认定高唐英确已背叛。')
add('liu_recognizes_wang_jihong','刘知远任王继弘为彰德留后',28,'诏以继弘','为彰德留后。',[('帝','正式任王继弘为彰德留后'),('王继弘','自称留后之后获朝廷任命')],when='947年六月，具体日未载',place='相州彰德军',note='正式诏任与自称留后分开；后来正式节度使授命另依后文，不提前写为本日任节度使。')
add('fan_hui_cizhou_appointment','樊晖获任磁州刺史',28,'庚辰，','以晖为磁州刺史。',[('樊晖','获任磁州刺史')],when='947年六月庚辰',place='磁州')
add('gao_fengming_leaves_liuduo','高奉明安排刘铎暂掌安国军府，自己返回恒州',28,'安国节度使高奉明','身归恒州。',[('高奉明','得知高唐英死后不安，请麻答安排刘铎掌军府，自己返恒州'),('麻荅','受高奉明请求安排刘铎掌军府'),('刘鐸','以马步都指挥使身份获署节度副使，主持军府事务')],when='947年六月高唐英被杀后，具体日未载',place='安国军至恒州',note='不安为史家心理描述；知军府事是暂掌事务，不误写刘铎已获正式节度使。')
add('liu_sends_jingnan_message','刘知远派使者向荆南传话',28,'帝遣使','告谕荆南。',[('帝','派使者告谕荆南')],when=t,place='大梁至荆南',note='告谕具体内容未载，只记遣使传话，不虚构文书全文。')
add('gao_conghui_requests_yingzhou','高从诲上表祝贺并索求郢州，刘知远拒绝',28,'高从诲上表贺，','帝不许。',[('高从诲','上表祝贺并请求获得郢州'),('帝','拒绝高从诲索求郢州')],when=t,place='荆南、郢州（索求地）',note='索求与拒绝分别明确，不写成郢州已经归荆南。')
add('gao_conghui_rejects_envoy','高从诲拒绝接受刘知远派来的加恩使者',28,'及加恩使至，',None,[('高从诲','拒绝接受加恩使者')],when='947年六月，告谕与索州之后，具体日未载',place='荆南',note='拒而不受按此次使者及加恩记，不扩展为永久拒绝所有后汉外交。')
add('li_jing_plans_north_campaign','李璟宣称中原为旧地，任李金全统领北方经略',29,'唐主闻','议经略北方。',[('唐主','闻契丹主死及萧翰弃汴，宣布经略北方'),('李金全','由左右卫圣统军等职获任北面行营招讨使')],when='947年耶律德光去世及萧翰离汴之后，具体命令日未载',place='南唐至中原（拟经略方向）',note='本朝故地为李璟诏书的政治声称，不当历史归属的唯一结论；议经略不等于已出兵。')
add('li_jing_abandons_north_march','李璟得知刘知远已入大梁，未敢出兵北方',29,'闻帝已入',None,[('唐主','闻刘知远入大梁后未敢出兵')],when='947年六月刘知远入大梁之后，具体得讯日未载',place='南唐',note='实际没有出兵与此前经略计划分录，不虚构南唐与后汉已经交战。')
add('ma_xiguang_chu_title','马希广获任天策上将军等职，并受封楚王',30,'秋，七月，',None,[('帝','授马希广官职并封楚王'),('马希广','获任天策上将军、武安节度使等，受封楚王')],when='947年七月甲午',place='楚国武安军',note='朝廷授封与五月楚将佐实际拥立区别，不建成第二次继位。')
sup('ma_xiguang_chu_title',30,july,'行潭州大都督、天策上將軍，充武安軍節度、湖南管內觀察使、江南諸道都統，封楚王','《旧五代史》七月甲午条也记马希广获天策上将军等职并封楚王。','补书详细官职与主书概述对应，不将同一授封建成两次。')
add('zhao_yanshou_death_rumor','有人传赵延寿已死，郭威建议借吊祭调整赵匡赞的军镇',31,'或传赵延寿','从之。',[('郭威','据死讯传闻提出遣使吊祭、起复移镇以安抚赵匡赞'),('帝','接受郭威建议'),('赵匡赞','成为拟吊祭、起复移镇的对象')],when='947年七月，具体传闻与建议日未载',place='后汉朝廷、河中',note='或传仅为传闻，郭威认为会感恩是预期；不把此处记作赵延寿已经实际死亡或所有安抚效果都已发生。')
add('du_li_submit_request_transfer','杜重威、李守贞奉表归附，杜重威同时请求调镇',31,'会鄴都留守、','重威仍请移它镇。',[('杜重威','以邺都留守、天雄节度使身份奉表归附，请求移镇'),('李守贞','以天平节度使身份奉表归附')],when='947年七月丙申调任前，具体奉表日未载',place='邺都天雄军、天平军至后汉朝廷',note='此次奉表与后文拒绝移镇分开，不因后续反叛取消此时归命记载。')
add('gao_xingzhou_visits_court','高行周入朝',31,'归德节度使','高行周入朝，',[('高行周','以归德节度使身份入朝')],when='947年七月丙申调任前，具体入朝日未载',place='大梁')
add('du_reassigned_guide','杜重威被调任归德节度使',31,'丙申，','徙重威为归德节度使，',[('帝','调杜重威到归德军'),('杜重威','接到归德节度使任命')],when='947年七月丙申',place='天雄军至归德军',note='本条为移镇任命，后文拒而不受另录，不当已经赴任。')
sup('du_reassigned_guide',31,july,'杜重威為宋州節度使，加守太尉','《旧五代史》丙申条也记杜重威改任宋州节度使，并加守太尉。','宋州与归德军的州名军号分别保留，补加官不改写主书原职。',relation='adds')
add('gao_replaces_du_tianxiong','高行周接替杜重威掌天雄军',31,'以行周代之；','以行周代之；',[('帝','以高行周接替杜重威'),('高行周','被任为邺都留守、天雄军主帅')],when='947年七月丙申',place='归德军至邺都天雄军',note='代之承杜重威原职；补书明确邺都留守，不推已经完成到镇交接。')
sup('gao_replaces_du_tianxiong',31,july,'高行周為鄴都留守，加守太傅','《旧五代史》同条记高行周任邺都留守，加守太傅。','补明原文代之的职任，不另建人物。',relation='adds')
add('li_shouzhen_huguo_transfer','李守贞改任护国节度使，加兼中书令',31,'守贞为护国','加兼中书令；',[('帝','任李守贞掌护国军，加兼中书令'),('李守贞','由天平军调护国军，加兼中书令')],when='947年七月丙申',place='天平军至河中护国军')
sup('li_shouzhen_huguo_transfer',31,july,'李守貞為河中節度使，加兼中書令','《旧五代史》同条记李守贞任河中节度使，加兼中书令。','州名河中与军号护国对应，各书分别引证。')
add('zhao_kuangzan_jinchang_transfer','赵匡赞被调任晋昌节度使',31,'徙护国节度使','为晋昌节度使。',[('帝','将赵匡赞调任晋昌军'),('赵匡赞','接到由护国军调晋昌军的任命')],when='947年七月丙申',place='河中护国军至晋昌军',note='调任命令不当已经赴任；旧史赵赞沿既有赵匡赞姓名，不因简称另建主体。')
sup('zhao_kuangzan_jinchang_transfer',31,july,'以河中節度使、檢校太尉趙贊為晉昌軍節度使','《旧五代史》同条记赵赞调晋昌军节度使。','补书赵赞与主书赵匡赞身份职任相接，沿同一主体。')
add('zhao_yanshou_actual_death','赵延寿后来在契丹去世',31,'后二年，',None,[('赵延寿','后来在契丹去世，区别947年死讯传闻')],when='《资治通鉴》947年条追述后二年（949）；《辽史》记天禄二年（948）',year=949,place='契丹',note='后二年与当年传闻明确区分；主书结构年份按其叙述949年，辽史天禄二年948年作为异说保留，未合并为确定日期。')
sup('zhao_yanshou_actual_death',31,zd,'天祿二年薨。','《辽史》赵延寿传记天禄二年去世，即948年。','本批《辽史》卷5明示947年改天禄元年，故二年为948；与主书后二年的949有异，保留两书年代，不改原文。',relation='conflicts',field='time_original')
add('qian_hongchu_joins_chancellery','钱弘倧令弟弟钱弘俶参与相府事务',32,'吴越王弘倧',None,[('弘倧','任弟弟参与相府事务'),('弘亻叔','以台州刺史身份参与相府事务')],when='947年七月，具体任命日未载',place='吴越相府、台州（原任职地）',note='弘亻叔为底本拆分字形，沿此前已核钱弘俶主体，不另建人物；同参相府事不当已经继王位。')
relationship('弘倧','弘亻叔','兄长',32,Q[32]['text'],'原文其弟明确钱弘俶是钱弘倧的弟弟，方向表示钱弘倧是钱弘俶的兄长；不推同母。')
reviews={25:'丙寅实际袭位与此前遗命分别录入，补新史同一继位，不跳过弘倧。',26:'大赦、保职、东京国号纪年、恢复节度、刘崇任命分录；青襄汝与旧青襄安、戊辰与己巳分别保留。',27:'李彦韬复用后晋主体，伟王身份未强合安端；李胡战、太后横渡对峙调停、迁祖州与主书败军幽墓分别保留，六月叙事不硬定全部发生月；天禄礼仪与高勋任命补辽九月；数年统治评述不压947。',28:'驻军背景、供铠、请降、杀人、自称留后指控、正式任命、樊晖授官、高奉明离镇及荆南往来依序录；亲戚比喻不造亲属，楚暉樊暉异文保留。',29:'南唐本朝故地为诏书声称，任将经略是计划，闻后汉入汴后实际未出兵。',30:'七月甲午朝廷授官封王区别五月楚内部拥立，同一补书授封不重复建事件。',31:'死讯传闻、郭威建议、奉表、入朝、丙申四镇任命与赵延寿后来死亡分别录；任命不等于到任，死年主949与辽948保留。',32:'弘亻叔拆字沿钱弘俶既有主体，同参相府不当继位；其弟支持兄长方向，未推同母。'}
assert not (P/'publication.json').exists()
for n in range(25,33):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph=Q[33]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原30—37行连续八段，本卷累计32/75；947年跨卷尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(25,33)],source_issues_review='汝安节镇、樊楚姓名、契丹内争过程与月份、赵延寿死年分别保留；伟王未合安端；李彦韬不与温韬混同，拆字钱弘俶沿已核主体。',plain_language_review='首次逐项核对人物、事件、参与角色、关系方向、时间地点、出处和事实说明；明确传闻、政治声称、自称、预测、任命及实际执行，引用不改字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
