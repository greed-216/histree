# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 946 paragraphs 31–38."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,57))
COMMIT='11bd80a1278ae2081bb275997aefcffa5b947ddc'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-946-october-november','xinwudaishi-062-chen-jue-fuzhou']:
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
main_sources = ['tongjian-285-946-october-november','tongjian-285-946-november-december']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p031-p038',
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
for n in range(31, 39):
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
        citation = f'卷285·后晋开运三年（946年十一月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_05_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=946, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='946年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_285_0946_' + code
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
        edge = 'participation_zztj_285_0946_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_285_0946_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','杜威':'杜重威','李达':'李仁达','契丹主':'耶律德光','刘重进':'刘重进（契丹通事）'})
NEW_ALIASES={'田行皋':[],'耿彦珣':['耿彥珣'],'萧翰':['蕭翰'],'刘重进（契丹通事）':['刘重进','劉重進']}
NEW_DESCRIPTIONS={'田行皋':'后蜀施州刺史。946年十一月条下记他叛变，后蜀派供奉官耿彦珣率兵讨伐；原文未给平定结果及生卒年。','耿彦珣':'后蜀供奉官。946年十一月条下记奉命领兵讨伐施州刺史田行皋。生卒年、籍贯及平叛结果未载；不同名的陈彦珣不据近名合并。','萧翰':'契丹将领。946年十一月条下记他与通事刘重进带兵绕到晋军后方，截断粮道及归路，进至栾城接受驻军投降。《资治通鉴》称他是契丹主耶律德光的舅舅，《辽史》保存了不同的亲属说法并质疑相关姓名起源说；具体亲属关系暂待核对。生卒年本批未核。','刘重进（契丹通事）':'契丹通事。946年十一月条下记与萧翰率百骑及其他士卒绕到晋军后方，断粮道及归路，进至栾城。与后汉、后周任节度使的同名刘重进是否同人尚未确认，暂分别识别；生卒年未载。'}
nov='946年十一月';j='jiuwudaishi-085-946-november';nt='xinwudaishi-062-chen-jue-fuzhou';lk='liaoshi-116-xiao-kinship'
add('li_youzou_temporary_admin','李守贞受命暂掌幽州行府事务',31,'十一月，',None,[('李守贞','受命权知幽州行府事')],when=nov+'丁酉',place='后晋幽州行府',note='行府事务是后晋安排，不能据此称后晋已经夺回幽州或李守贞实际入城。')
sup('li_youzou_temporary_admin',31,j,'丁酉，詔李守貞知幽州行府事。','《旧五代史》也记十一月丁酉命李守贞知幽州行府事。','原文未记此时已控制幽州。')
add('du_stops_outside_yingzhou','杜重威等到瀛州，见城门大开、寂静无人，不敢进入',32,'己亥，','不敢进。',[('杜威','率军至瀛州城外，不敢进城')],when=nov+'己亥',place='瀛州',note='寂若无人是晋军所见的描述，不等于城内无人或已投降。')
add('du_orders_liang_pursuit','杜重威听说高谟翰已暗中出城，派梁汉璋率二千骑追赶',32,'闻契丹将','追之，',[('杜威','派二千骑追击'),('高谟翰','被晋军听说已先率兵潜出'),('梁汉璋','奉命率二千骑追击')],when=nov+'己亥条下',place='瀛州城外',note='高谟翰潜出为晋军所闻；二千是追兵数量，不是契丹总兵数。')
add('liang_dies_nanyangwu','梁汉璋在南阳务遇契丹军，战败身亡',32,'遇契丹于','败死。',[('梁汉璋','追击时在南阳务战败身亡')],when=nov+'己亥条下',place='南阳务',note='具体战日只由段首限定，不自行换算日期；死亡事实有旧本纪独立印证。')
sup('liang_dies_nanyangwu',32,j,'師次瀛州城下，貝州節度使梁漢璋戰死。','《旧五代史》也记十一月瀛州进军时，贝州节度使梁汉璋战死。','该本纪仅按月叙述，地点用瀛州城下概述战役范围；不覆盖通鉴所记具体南阳务。')
claim('person','person_梁汉璋','death_year','梁汉璋于946年十一月追击契丹军时战死。',32,span(32,'威遣梁汉璋','败死。'),'依据本段与旧本纪，不直接改写复用人物档案字段。')
add('du_retreats_after_liang_defeat','杜重威等听到梁汉璋战败后，带军向南撤退',32,'威等闻之，','而南。',[('杜威','因追兵战败而南撤')],when=nov+'己亥条下',place='瀛州南行')
sup('du_retreats_after_liang_defeat',32,j,'杜威等以漢璋之敗，遂收軍而退。','《旧五代史》同记杜重威因梁汉璋战败撤军。','将撤退与后续转向恒州分开，不合为一次直线南归。')
add('du_loots_surrendering_counties','束城等县请求归降，杜重威军仍焚屋、掳掠妇女后离开',32,'时束城',None,[('杜威','所部焚毁请求投降县份房舍并掳掠妇女')],when=nov+'南撤途中，具体日未载',place='束城等数县',note='原文未给另外县名、户数和掳掠人数，不虚补；请求归降不等于已经建立县政管理。')
add('wuyue_enters_fuzhou_zengpu','吴越援兵到福州，从罾浦南暗中进入城内',33,'己酉，','州城。',[],when=nov+'己酉',place='罾浦南至福州',note='本句没有具名援军指挥者，虽此前派张赵，不把二人实际入城无证据地添入。')
add('tang_occupies_dongwu_gate','南唐兵占据东武门，李仁达与吴越援兵抵抗不利',33,'唐兵进据','不利。',[('李达','与吴越兵共同抵抗南唐进军而不利')],when=nov+'己酉条下',place='福州东武门',note='李达沿李仁达稳定主体及已经发布别名复用；不利不能自动写全部守军被歼。')
add('fuzhou_isolated_after_dongwu','福州内外联系断绝，城内形势更加危险',33,'自是',None,[],when=nov+'己酉战后',place='福州',note='这是城防态势，不提前写次年攻城结果。')
add('li_sends_wang_jianfeng','李璟派信州刺史王建封协助攻打福州',34,'唐主遣','福州。',[('唐主','派遣王建封增援攻城'),('王建封','以信州刺史身份赴福州助攻')],when=nov,place='信州至福州')
add('tang_commanders_compete','南唐监军争权、部分将领不听命，争功使攻城军进退失调',34,'时王崇文','不相应。',[('王崇文','虽为元帅，未能协调各方'),('陈觉','与其他监军争权'),('冯延鲁','与其他监军争权'),('魏岑','与其他监军争权'),('留从效','不听统一指挥并争功'),('王建封','不听统一指挥并争功')],when=nov,place='福州攻城军',note='这是史书对军中分歧的叙述；不另造诸将之间的长期敌对关系。')
sup('tang_commanders_compete',34,nt,'覺等爭功，進退不相應，','《新五代史》也记陈觉等争功、进退失调。','该传连叙后续败退，本批只补当下统帅失调，不提前录入其后全军败退及处分。')
add('tang_fails_due_disunity','南唐攻城军士气分散，未能攻克福州',34,'由是将士','不克。',[],when=nov,place='福州',note='解体在此指军心涣散，不据此写军队正式解散；因果按史书叙述限定。')
add('du_changye_returns_to_central','李璟任杜昌业为吏部尚书，兼判省事',34,'唐主以江州','判省事。',[('唐主','任命杜昌业回朝掌职'),('杜昌业','由江州观察使任吏部尚书、判省事')],when=nov,place='江州至南唐朝廷')
add('du_changye_prior_jiangzhou','杜昌业此前由兵部尚书、判省事外任江州',34,'先是昌业','出江州，',[('杜昌业','此前由中央职务外任江州')],when='946年回朝前的追述，具体年月未载',year=None,place='南唐朝廷至江州',note='不把先前外任直接定为946年十一月。')
add('du_changye_laments_depleted_treasury','杜昌业回朝查账，感叹几年间府库耗去一半，担忧能否持续',34,'及还，',None,[('杜昌业','阅账后感叹府库耗费并担忧')],when=nov+'回朝后，具体日未载',place='南唐朝廷',note='耗去一半是杜昌业据簿籍发出的判断，时间仅未数年；不推算起始年与库存金额。')
add('khitan_advances_yi_ding_heng','耶律德光率契丹军从易、定向恒州大举进兵',35,'契丹主','恒州。',[('契丹主','率军自易定向恒州进军')],when=nov,place='易州、定州至恒州')
add('du_plans_south_from_wuqiang','杜重威军到武强，听说契丹进兵，打算经冀、贝南撤',35,'杜威等至','而南。',[('杜威','听到敌军来袭，打算由冀贝南下')],when=nov,place='武强、冀州、贝州',note='将是打算，后文改变路线，不能写已经走完冀贝南撤。')
sup('du_plans_south_from_wuqiang',35,j,'行次武強，聞契丹入寇，欲取直路，自冀、貝而南。','《旧五代史》也记杜重威行至武强，想经冀贝向南。','原文欲为计划，不把路线当已完成行程。')
add('zhang_persuades_du_hengzhou','张彦泽来会晋军，陈说可以击败契丹，杜重威改向恒州并让他为前锋',35,'彰德节度使','为前锋。',[('张彦泽','从恒州来会，陈说可破敌并任前锋'),('杜威','采纳意见，转向恒州')],when=nov,place='恒州、武强至恒州')
sup('zhang_persuades_du_hengzhou',35,j,'會張彥澤領騎自鎮定至，且言契丹可破之狀，於是大軍西趨鎮州。','《旧五代史》也记张彦泽带骑兵会军后，晋军转向镇州。','主书恒州、旧本纪镇州沿不同地名称谓保留；不将其言可破当已经获胜。')
add('zhang_contests_zhongdu_bridge','张彦泽率骑兵争夺中度桥，契丹烧桥后退',35,'甲寅，','焚桥而退。',[('杜威','率军至中度桥'),('张彦泽','率骑兵争桥'),('契丹主','所部先据桥，后焚桥退去')],when=nov+'甲寅',place='中度桥',note='中度按本段底本；中渡是他书常见字形，不自动改原字。')
add('jin_khitan_camp_across_hutuo','晋军与契丹军分别驻扎在滹沱河两岸',35,'晋兵与','而军。',[],when=nov+'甲寅争桥后',place='滹沱河两岸')
add('khitan_considers_withdrawal','契丹军因争桥失利，担心晋军渡河与恒州合击，商议退兵',35,'始，契丹','议引兵还。',[],when=nov+'争桥失利后',place='滹沱河及恒州',note='恐与议是史书所叙判断和计划，不能写已经北撤。')
add('khitan_stays_after_jin_fortifies','契丹军听说晋军筑垒准备久驻，决定不撤',35,'及闻',None,[],when=nov+'两岸对峙时',place='滹沱河两岸',note='长期驻防计是晋军筑垒的史载意图，不补工事规模。')
add('tian_rebels_shizhou','后蜀施州刺史田行皋叛变',36,'蜀施州','皋叛，',[('田行皋','以施州刺史身份叛变')],when=nov+'条下，具体日未载',place='施州')
add('geng_sent_against_tian','后蜀派供奉官耿彦珣领兵讨伐田行皋',36,'遣供奉官',None,[('耿彦珣','奉命率兵讨伐田行皋'),('田行皋','遭后蜀派兵讨伐')],when=nov+'条下，具体日未载',place='后蜀至施州',note='原句没有直接点名下令者，未无证据补孟昶参与；也未载讨伐胜负。')
add('jin_commanders_neglect_planning','史书记载杜重威及诸将日常相互迎合、饮酒作乐，少议军事',37,'杜威虽','罕议军事。',[('杜威','被史书记为性懦怯，与诸将少议军事')],when=nov+'中度对峙时',place='晋军行营',note='性懦怯是史家评价；未具名的偏裨不据前批任职表全添进宴饮事件。')
add('li_gu_proposes_bridge_raid','李谷劝杜重威、李守贞架桥渡河，与恒州约定夜袭夹击契丹',37,'磁州刺史','虏必遁逃。”',[('李谷','以磁州刺史兼北面转运使身份提出架桥夜袭'),('杜威','听取李谷建议'),('李守贞','听取李谷建议')],when=nov,place='晋军行营、滹沱河与恒州',note='这是建议；木架薪土桥、举火、夜袭和敌退均未在本句记作已经实施。')
add('du_rejects_li_gu_plan','诸将赞同李谷建议，杜重威独自反对，并让李谷南下督运粮食',37,'诸将皆',None,[('杜威','反对架桥夜袭，让李谷南下督粮'),('李谷','被派往怀州、孟州督军粮')],when=nov,place='晋军行营至怀州、孟州',note='诸将未具名不泛化每个已知将领；反对不自动推为此时已经决定投降。')
add('khitan_cuts_supply_route','契丹军正面牵制晋军，萧翰、刘重进绕西山到后方断粮道和归路',38,'契丹以大兵','及归路。',[('萧翰','率兵绕到晋军后方断粮路'),('刘重进','以通事身份与萧翰共同领兵')],when=nov,place='晋军正面、西山至后方粮道',note='百骑另加原文赢卒，未给士卒数；赢疑羸但底本保留，展示只说其他士卒，不造精锐或羸弱确定评价。')
add('jin_foragers_captured','晋军出外采薪者被掳，逃回的人称契丹兵多，使军中恐惧',38,'樵采者','军中忷惧。',[],when=nov+'粮道被截后',place='晋军营外及营中',note='契丹众盛是逃回者所称，不作实际敌军数量统计；皆按本段遭遇者范围理解。')
add('luancheng_garrison_surrenders','萧翰等到栾城，千余驻军来不及防备而投降',38,'翰等至','降之。',[('萧翰','领兵到栾城接受驻军投降'),('刘重进','与萧翰同领进至栾城的部队')],when=nov,place='栾城',note='千余为概数；刘重进根据本段翰等承接共同领兵，未造城内具名守将。')
add('khitan_tattoos_releases_captives','契丹在被俘晋民脸上刺奉敕不杀四字，放他们向南走',38,'契丹获晋民','南走。',[],when=nov+'截粮期间',place='晋军后方至南行道路',note='原文没有给获俘人数，亦未说明四字由谁亲自下诏，不新增虚构皇帝诏令。')
add('grain_carriers_abandon_carts','运粮民夫路遇获释俘虏，丢弃车辆惊慌逃散',38,'运夫在道','惊溃。',[],when=nov+'获俘民众南走后',place='晋军运输道路',note='车数、损失粮数和死伤未载，不凭此推算全军已无一粒粮。')
claim('person','person_萧翰','family_relations','《资治通鉴》称萧翰是契丹主耶律德光的舅舅；具体亲属关系仍待核对。',38,span(38,'翰，',None),'本句契丹主承接946年耶律德光；与辽史保存的异说并列，暂不建确定亲属连线。')
claim('person','person_萧翰','family_relations','《辽史》保存一种说法，称萧翰是述律皇后的兄子；该书还质疑这种说法所解释的后族姓氏起源。',38,'有謂述律皇后兄子名蕭翰者，為宣武軍節度使，其妹復為皇后，故后族皆以蕭為姓。其說與紀不合，故陳大任不取。','这是有谓的转述并附质疑，不能直接定为正确血缘；与通鉴舅说共同记录疑问，不自动换成表兄弟关系。',source=lk,relation='conflicts')
reviews={31:'幽州行府职不证明后晋夺幽州；旧本纪丁酉同。',32:'城寂无人只是军前观感；高谟翰撤出为所闻。梁汉璋二千骑追败死与旧本纪战死印证；旧瀛州范围不覆盖具体南阳务。束城等请求投降仍遭焚掠，不补县名及人数。',33:'己酉援兵潜入不具名统帅；李达复用李仁达别名。东武门不利与封锁分别，不录后续解围。',34:'王建封增援与军中失调分开；新史只补争功，后续全军败退未提前。杜昌业此次任命与先前外任年份未定分开，府库一半是其账后感叹。',35:'杜重威由武强欲南转恒州、张前锋、争桥、焚桥、两岸对峙及契丹先议退后留分阶段；中度中渡底本字形分别。',36:'后蜀两人按姓名身份查无已录同人，陈彦珣非近名合并；不补皇帝参与及平叛结果。',37:'史家怯懦评价及日常疏于军议保持来源身份；架桥夜袭只为建议，杜否决后李去督粮未写桥成。',38:'刘重进通事与后汉后周节度使同名未证同人，暂单列。百骑及赢卒疑字不猜其数和兵质。舅说与辽史有谓兄子及批评原文并列待核，不建确定亲属连线。'}
assert not (P/'publication.json').exists()
for n in range(31,39):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(31,39)],next_paragraph=Q[39]['id'],next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285原61—68行连续八段，发布后946年累计38/56，余18段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(31,39)],source_contexts=[dict(source_key=main_sources[0],note='只续录31—35段，前29—30不重复。'),dict(source_key=main_sources[1],note='只录36—38段，十二月密奏、告急、王清战死及降营留下一批。'),dict(source_key=nt,note='只补争功失调，后续南唐敗退与处分不提前。'),dict(source_key=lk,note='保存亲属说法及批评原文，不能把有谓当已确认谱系。')],source_issues_review='萧翰亲属说、赢卒疑字、中度中渡字形及通事刘重进同名问题保留待核；具体战日未转公历。',plain_language_review='首次检查标题、事件说明、角色、时间、事实说明和核对说明；具体行动、建议、传闻和史家评价分开，原文摘录逐字保留。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
