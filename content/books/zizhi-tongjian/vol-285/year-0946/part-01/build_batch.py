# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 945 paragraphs 1–8."""
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
COMMIT='bd391620db0dcdfa704b6c166979a0422e9213ef'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='xinwudaishi-068-liu-replaces-wang']
for key in ['tongjian-285-945-november-december','xinwudaishi-062-feng-name','xinwudaishi-068-fall-year']:
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
main_sources = ['tongjian-285-945-november-december','tongjian-285-946-february-june']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p001-p008',
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
for n in range(1, 9):
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
        citation = f'卷285·后晋开运二年（946年正月至六月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_01_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','高祖':'石敬瑭','齐丘':'宋齐丘','冯延己':'冯延巳','延煦':'石延煦','延宝':'石延宝','李弘义':'李仁达','弘通':'李弘通','杜威':'杜重威','孙方谏':'孙方简','孫方諫':'孙方简','李彦韬':'李彦韬（后晋宣徽使）'})
NEW_ALIASES={'高越':[],'石延煦':['延煦'],'石延宝':['石延寶','延宝','延寶'],'李弘通':[],'王令周':[],'石存':[],'也厮褒':['也廝褒'],'孙深意':['孫深意'],'孙方简':['孫方簡','孙方谏','孫方諫'],'孙行友':['孫行友'],'刘延翰':['劉延翰']}
NEW_DESCRIPTIONS={'高越':'南唐水部郎中。946年正月条下记他上书指出冯延巳兄弟的过恶，李璟发怒，将他贬为蕲州司士。生卒、籍贯未载。','石延煦':'石敬瑭的孙子，石重贵养子，石延宝的兄长。946年任镇宁节度使，与赵在礼的女儿成婚；《资治通鉴》记三月庚申，《旧五代史》记四月，婚事纪月不同，分别保留。亲生父母姓名及生卒年未载。','石延宝':'石敬瑭的孙子，石重贵养子，石延煦的弟弟。946年记石延煦婚事时，史书补叙二人为石重贵养子。亲生父母姓名与收养年月、生卒年未载。','李弘通':'李仁达的弟弟。946年四月，李仁达派他领兵攻泉州；留从效废王继勋后率军击败他。生卒年未载。','王令周':'朔方节度使王令温的弟弟。拓跋彦超、石存、也厮褒三族攻灵州时被杀，王令温随后在946年四月戊午上表告急；死亡具体日未载。','石存':'946年《资治通鉴》记石存一族与拓跋彦超、也厮褒两族共同攻灵州。名字、所属部众与此役相联系，具体官号及生卒年未载。','也厮褒':'946年《资治通鉴》记也厮褒一族与拓跋彦超、石存两族共同攻灵州。具体官号及生卒年未载。','孙深意':'居狼山佛舍的尼姑。史书记她以术聚众，孙方简、孙行友自称是她的侄子并侍奉她；她去世后，孙方简继续其术，称她坐化。史书的灵验说法不视作已经验证的超自然事实；死亡年月未载。','孙方简':'《资治通鉴》称中山人，聚众于狼山，归附后晋后任东北招收指挥使，后来转投契丹并拘执刘延翰。《宋史》孙行友传写作孙方谏，记他是孙行友的兄子；《资治通鉴》记孙行友是其弟，亲属记载冲突待核。姓名字形与主体按狼山、职衔和事迹对应复用，生卒年未核。','孙行友':'与孙方简聚众于狼山，借孙深意的术及边民避乱扩展部众。《宋史》记为莫州清苑人，出身务农，后任孙方谏的副手；《资治通鉴》记为孙方简之弟，《宋史》却记孙方谏为他的兄子，亲属与籍贯表述分别保留待核。生卒年未核。','刘延翰':'天雄节度使杜重威的元随军将。946年奉命到边地买马，被孙方简拘执送给契丹；逃归后，六月壬戌抵大梁，报告孙方简拟引契丹入侵并请求备御。生卒、籍贯未载。'}
jan='946年正月条下，具体日未载';apr='946年四月条下，具体日未载';june='946年六月条下，具体日未载';past='946年相关记事之前的追述，具体年月未载'
of='jiuwudaishi-084-946-february';oa='jiuwudaishi-084-946-april';oj='jiuwudaishi-084-946-june';ss='songshi-253-sun-xingyou';nf='xinwudaishi-062-feng-name';mi='xinwudaishi-068-fall-year'
add('song_honorary_return','宋齐丘任太傅兼中书令，只朝参而不参与政务',1,'春，','政事。',[('齐丘','获任太傅兼中书令，只奉朝请、不参与政务')],when=jan,place='南唐',note='承接945年召回；奉朝请为参加朝参，不认作仍执掌宰相政务。')
add('li_jianxun_chancellor','李建勋任右仆射兼门下侍郎、同平章事',1,'以昭武','平章事。',[('李建勋','由昭武节度使任右仆射兼门下侍郎、同平章事')],when=jan,place='南唐朝廷')
add('feng_yansi_chancellor','冯延巳以中书侍郎任同平章事',1,'与中书','平章事。',[('冯延己','以中书侍郎任同平章事')],when=jan,place='南唐朝廷',note='延己沿用全站冯延巳主体与既有别名，摘录保留己字。')
add('historian_evaluates_li_feng','《资治通鉴》评价李建勋熟悉吏事而少决断，冯延巳善文辞却结党',1,'建勋练习','朋党。',[('李建勋','被史书评价熟悉吏事但懦怯少决断'),('冯延己','被史书评价善文辞却狡佞、好大言、结党')],when='946年正月任官条附人物评价，不是单日行动',place='南唐',note='明确为史书评价，不把价值判断写成现代客观检测结论。')
add('gao_accuses_feng_brothers','高越上书指出冯延巳兄弟的过恶',1,'水部郎中','过恶，',[('高越','以水部郎中身份上书指出冯氏兄弟过恶'),('冯延己','与其兄弟受到高越指责')],when=jan,place='南唐',note='本句未详列每项指控，不虚补贪污金额或罪案；另一兄弟此句未名，不凭记忆增参与。')
add('li_demotes_gao','李璟发怒，将高越贬为蕲州司士',1,'唐主怒，','司士。',[('唐主','因高越上书发怒并将他贬官'),('高越','被贬为蕲州司士')],when=jan,place='南唐至蕲州')
add('li_establishes_xuanzheng','李璟在宫中设宣政院，由常梦锡掌机密事务',1,'初，唐主','机密，',[('唐主','在宫中设宣政院'),('常梦锡','以翰林学士、给事中身份领宣政院，掌机密')],when=past,year=None,place='南唐宫中',note='初字追述设院及职掌，不能直接定为946年正月新设。')
sup('li_establishes_xuanzheng',1,nf,'夢錫直宣政殿，專掌密命，','《新五代史》记常梦锡值宣政殿，专掌密命。','宣政殿与宣政院表述各保留，不能凭两字不同推定必是两套机构；该书在李璟即位后的叙述中记职掌。',relation='adds')
add('historian_praises_chang_yan','《资治通鉴》称常梦锡、严续忠直无私',1,'与中书','无私。',[('常梦锡','与严续被史书称为忠直无私'),('严续','以中书侍郎身份被称为忠直无私')],when=past,year=None,place='南唐',note='人物评价保留来源，不强定为某次公开表彰。')
add('li_asks_chang_help_yan','李璟请求常梦锡帮助严续对抗结党者',1,'唐主谓','之。”',[('唐主','认为严续中立但才能不足，要求常梦锡扶助'),('常梦锡','受命扶助严续'),('严续','被李璟评价并指定由常梦锡扶助')],when=past,year=None,place='南唐',note='李璟对严续才能与党争的判断是讲话内容，不转作客观结论。')
add('chang_leaves_xuanzheng','常梦锡不久被撤去宣政院职务',1,'未几，','宣政院，',[('常梦锡','在李璟讲话后不久被撤去宣政院职务')],when='李璟请求常梦锡扶助严续之后不久，具体年月未载',year=None,place='南唐')
add('yan_moves_chizhou','严续被调出朝廷，任池州观察使',1,'续亦出','观察使。',[('严续','被调出朝廷任池州观察使')],when='常梦锡罢宣政院职务前后，具体年月未载',year=None,place='池州')
add('chang_withdraws_drinks','常梦锡称病饮酒，不再参与朝廷政事',1,'梦锡于是','朝廷事。',[('常梦锡','罢职后称病、纵酒，不再参与朝廷政事')],when='常梦锡罢宣政院职务以后，具体年月未载',year=None,place='南唐',note='移疾为称病，不诊断疾病真假或酒量。')
relationship('严可求','严续','父亲',1,'续，可求之子也。','按明确父子身份写严可求是严续的父亲，不倒置方向。')
add('feb_solar_eclipse','史书记946年二月壬戌朔日食',2,'二月，',None,[],when='946年二月壬戌朔',place='后晋，观测具体地点未载',note='记录史书天象，不自行换算公历或推覆盖区域。')
sup('feb_solar_eclipse',2,of,'二月壬戌朔，日有蝕之。','《旧五代史》同记二月壬戌朔日食。','两书纪日一致。')
add('zhao_wealth_from_ten_commands','史书记赵在礼历任十镇，多有贪暴，财富为诸帅之最',3,'晋昌','之最。',[('赵在礼','历任十镇，受到贪暴聚财的史书评价')],when='946年婚事条前介绍此前历镇经历，具体起止年未载',year=None,place='赵在礼此前所任诸镇',note='不凭十镇数字补十个未列出的镇名；贪暴与最富是史书概述。')
add('shi_arranges_yanxu_marriage','石重贵看中赵在礼的财富，为石延煦娶赵家女儿',3,'帝利其富，','其女。',[('帝','看中赵在礼财富，为养子安排婚事'),('延煦','以镇宁节度使身份娶赵在礼之女'),('赵在礼','女儿与石延煦成婚')],when='946年三月庚申',place='后晋',note='女儿未具名，不造姓名；主书记婚事动机，不把女儿婚后封号补出。')
sup('shi_arranges_yanxu_marriage',3,oa,'皇子延煦與晉昌軍節度使趙在禮結婚，命宗正卿石光贊主之。','《旧五代史》在四月记石延煦与赵在礼结婚，由宗正卿石光赞主持。','《资治通鉴》三月庚申与该书四月条纪月不同；不猜测订婚和婚礼分别发生，也不覆盖主书时间。',relation='conflicts',field='time_original')
add('zhao_marriage_cost','赵在礼为婚事花费十万缗，官府花费比他多出数倍',3,'在礼自费','过之。',[('赵在礼','婚事自费十万缗')],when='946年石延煦婚事，具体支出日未载',place='后晋',note='县官指朝廷官府而非某一县官个人；不据数倍算出确定总金额。')
add('shi_adopts_two_grandsons','石重贵收养石敬瑭的孙子石延煦、石延宝为儿子',3,'延煦及弟',None,[('帝','收养石延煦、石延宝为子'),('延煦','是石敬瑭孙子、石重贵养子'),('延宝','是石敬瑭孙子、石重贵养子'),('高祖','是二人的祖父')],when='946年婚事条补叙收养关系，具体收养年月未载',year=None,place='后晋')
for name in ['延煦','延宝']:
 relationship('帝',name,'养父',3,'延煦及弟延宝，皆高祖诸孙，帝养以为子。','石重贵是二人的养父，不能写成亲生父亲。')
 relationship('高祖',name,'祖父',3,'延煦及弟延宝，皆高祖诸孙，帝养以为子。','石敬瑭是二人的祖父，未具名亲生父亲，不造中间主体。')
relationship('延煦','延宝','兄长',3,'延煦及弟延宝，皆高祖诸孙，帝养以为子。','弟字明示长幼，石延煦是石延宝兄长。')
add('wang_writes_li_friendship','王继勋致信李仁达，希望修好',4,'唐泉州','李弘义。',[('王继勋','以泉州刺史身份致信修好'),('李弘义','以威武节度使身份收信')],when='946年四月出兵前，具体日未载',place='泉州至福州',note='李弘义复用已记录改名的李仁达；不是另一位同名人士。')
add('li_angry_quanzhou_parity','李仁达因泉州过去隶属威武军，对王继勋以平等礼节往来生气',4,'弘义以','抗礼。',[('李弘义','认为泉州原属威武军，不满王继勋以平等礼节相待'),('王继勋','书信礼节引起李仁达不满')],when='946年四月出兵前，具体日未载',place='福州',note='不据故隶推946年泉州仍实际受威武军管辖。')
add('li_hongtong_attacks_quanzhou','李仁达派弟弟李弘通领一万人攻泉州',4,'夏，',None,[('李弘义','派弟李弘通领兵攻泉州'),('弘通','领一万人攻泉州')],when=apr,place='福州至泉州',note='一万为史载兵力概数，不视作现代精确清点。')
relationship('李弘义','弘通','兄长',4,'遣弟弘通将兵万人伐之。','原文明示弟弘通，李仁达是李弘通兄长。')
add('feng_holds_tuoba','冯晖在灵州留下拓跋彦超，使其他部落不敢侵扰',5,'初，','为寇，',[('冯晖','在灵州留下党项酋长拓跋彦超'),('拓跋彦超','被留在灵州')],when='冯晖此前镇灵州时，具体年月未载',year=None,place='灵州',note='留于州下不扩写为有明确刑名的监禁；此处初字是追述。')
add('feng_releases_tuoba','冯晖将离任时放拓跋彦超离开',5,'及将','纵之。',[('冯晖','将离任时释放拓跋彦超'),('拓跋彦超','获准离开灵州')],when='冯晖离任朔方之前，具体日未载',year=None,place='灵州')
add('wang_applies_law_without_conciliation','王令温接任朔方，以中原法律约束羌、胡，未加安抚',5,'前彰武','绳之。',[('王令温','代冯晖镇朔方，未安抚羌胡而以中原法律约束')],when='王令温接任朔方以后，具体日未载',year=None,place='朔方',note='中国法在此为史文中原王朝法律，避免误解为现代法律；不得虚补所施具体刑罚。')
add('tribes_rebel_and_raid','羌、胡部众因王令温施政不满，纷纷叛乱抢掠',5,'羌、胡','寇钞。',[('王令温','施政引起羌胡不满')],when='王令温镇朔方以后、946年告急以前，具体年月未载',year=None,place='朔方',note='此为史书叙述的因果；未将所有羌胡群体永久定义为敌对。')
add('three_clans_attack_lingzhou','拓跋彦超、石存、也厮褒三族共同攻灵州',5,'拓跋彦超','灵州，',[('拓跋彦超','率所属部众共同攻灵州'),('石存','所属部众参与攻灵州'),('也厮褒','所属部众参与攻灵州')],when='王令温接任后、946年四月戊午告急以前，具体年月日未载',year=None,place='灵州')
add('wang_lingzhou_killed','王令温的弟弟王令周在灵州受攻时被杀',5,'拓跋彦超','令周。',[('王令周','在三族共同攻灵州时被杀'),('王令温','弟弟在受攻时被杀')],when='王令温接任后、946年四月戊午告急以前，死亡具体年月日未载',year=None,place='灵州',note='不将三族共同责任细分为某一具名凶手。')
relationship('王令温','王令周','兄长',5,'杀令温弟令周。','原文明示弟令周，王令温是王令周兄长。')
add('wang_reports_emergency','王令温上表报告灵州危急',5,'戊午，',None,[('王令温','上表告急')],when='946年四月戊午',place='灵州至后晋朝廷',note='戊午是告急日，不硬套为攻城或死亡日。')
# 6: source titles preserve textual typo without treating it as another office.
add('liu_asks_wang_step_down','留从效指出王继勋赏罚失当、士兵不肯作战，要求他退位反省',6,'泉州都','自省。”',[('留从效','劝王继勋退位，声称士兵因赏罚不当不肯力战'),('王继勋','被留从效要求退位反省')],when=apr,place='泉州',note='底本都都挥使疑为转录错误，引用保留；展示用军将称呼，不建立讹字官职。士卒不战原因是留从效讲话。')
add('liu_deposes_wang','留从效罢去王继勋，令他退居私宅，自掌泉州军政',6,'乃废','军府事，',[('留从效','废王继勋，代掌军府'),('王继勋','失去泉州刺史职，退居私宅')],when=apr,place='泉州')
sup('liu_deposes_wang',6,mi,'留從効聞延政降唐，執王繼勳送于金陵，','《新五代史》记留从效在听闻王延政降唐后，拘执王继勋送往金陵。','主书先废归私第、后李璟召还金陵；该书合记拘执送金陵，处置步骤不同分别保留，纪年差异沿用此前建州异说。',relation='adds')
add('liu_defeats_li_hongtong','留从效率兵大败李弘通',6,'勒兵','破之。',[('留从效','整兵迎击，大败李弘通'),('弘通','领兵攻泉州，被留从效击败')],when=apr,place='泉州')
add('li_appoints_liu_quanzhou','李璟获悉泉州变动，任留从效为泉州刺史',6,'表闻','刺史，',[('唐主','收到奏报后任命留从效'),('留从效','获任泉州刺史')],when='946年四月泉州战后，具体日未载',place='泉州',note='新史该处即授清源军节度使，主书后文另记清源军时再录，不提前替换当前刺史职。')
sup('li_appoints_liu_quanzhou',6,mi,'李景以泉州為清源軍，以從効為節度使。','《新五代史》在王继勋送金陵后即记泉州为清源军、留从效任节度使。','该书将官制变化压缩叙述，与主书本段先任刺史、后来另建清源军次序不同，独立引用，不将当前任官改为清源节度使。',relation='adds')
add('li_recalls_wang_jinling','李璟召王继勋回金陵',6,'召继勋','金陵，',[('唐主','召王继勋回金陵'),('王继勋','被召回金陵')],when='946年四月泉州变动后，具体日未载',place='泉州至金陵')
add('li_garrisons_quanzhou','李璟派将领带兵驻守泉州',6,'遣将','泉州。',[('唐主','派未具名将领带兵驻泉州')],when='946年四月泉州变动后，具体日未载',place='泉州',note='将领未名不造主体，不把驻军等同于全面占领闽中五州。')
add('wang_jicheng_moves_hezhou','王继成由漳州刺史调任和州刺史',6,'徙漳州','刺史，',[('王继成','由漳州调任和州刺史')],when=apr,place='漳州至和州')
add('xu_moves_qizhou','许文稹由汀州刺史调任蕲州刺史',6,'汀州刺史',None,[('许文稹','由汀州调任蕲州刺史')],when=apr,place='汀州至蕲州')
# 7: extensive retrospective frontier history; source belief is not proof of supernatural events.
add('locals_build_langshan_fort','狼山居民筑堡躲避契丹侵扰',7,'定州西北','胡寇。',[],when='孙方简聚众之前，具体年月未载',year=None,place='狼山',note='定州西北二百里为史载方位距离，不换现代经纬度。')
add('sun_shenyi_attracts_followers','孙深意住狼山佛舍，借术与预言得到远近信奉',7,'堡中有','之。',[('孙深意','居佛舍，以术与所言之事吸引信众')],when='孙深意去世以前，具体年月未载',year=None,place='狼山',note='言事颇验与妖术惑众是史書叙述，不声称超自然能力已被证实。')
add('sun_brothers_serve_nun','孙方简、孙行友自称孙深意之侄，戒酒肉并谨慎侍奉',7,'中山人','甚谨。',[('孙方简','自称孙深意侄子，与孙行友戒酒肉侍奉'),('孙行友','与孙方简侍奉孙深意'),('孙深意','被二人自称为姑辈亲属并侍奉')],when='孙深意去世以前，具体年月未载',year=None,place='狼山',note='自言是亲属声称，不建立孙深意与二人的已确证姑侄关系。')
# Explicit disagreement belongs to the common entities, with no competing settled relationship added.
claim('person',people['孙行友'],'description','《宋史》称孙行友为莫州清苑人，写孙方谏为他的兄子，与《资治通鉴》孙方简之弟的记载不同。',7,'孫行友，莫州清苑人，世業農。初，定州西二百里有狼山者，當易州中路，舊有城堡，邊人賴之以避寇。山中蘭若有尼，姓孫氏，名深意，有術惑眾。行友兄子方諫名之為姑帥，事之甚謹。','狼山、姑帥孙深意与后续官职事迹对应同组人物；方简方谏字形与亲属关系保留异说待核，主书中山与宋莫州清苑表述不强作同地。',source=ss,relation='conflicts')
relationship('孙方简','孙行友','兄长',7,'中山人孙方简及弟行友，自言深意之侄，','按《资治通鉴》弟字记方向；《宋史》记孙方谏为孙行友兄子，另有冲突引用，该关系并非各书一致确证。')
B['person_relationships'][-1]['description']='《资治通鉴》记孙方简是孙行友的兄长；《宋史》记为孙行友的兄子，亲属关系有异说，待进一步校核。'
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《宋史》孙行友传记孙方谏为孙行友的兄子，与《资治通鉴》兄弟关系不同。',7,'行友兄子方諫名之為姑帥，事之甚謹。','以同一狼山聚众事迹对应孙方简主体，但该书叔侄与主书兄弟有冲突；在关系说明并列呈现，未另建竞争的已确定叔侄关系。',source=ss,relation='conflicts')
add('sun_shenyi_dies','孙深意去世',7,'深意卒，','深意卒，',[('孙深意','在狼山去世')],when='孙方简继行其术以前，具体年月未载',year=None,place='狼山',note='死亡明确，日期未载，不设death_year为946。')
add('sun_continues_nun_rituals','孙方简继续孙深意的术，称她坐化并按生前方式供奉，信众渐多',7,'方简嗣','日兹。',[('孙方简','继续其术、称孙深意坐化并供奉'),('孙深意','去世后成为供奉对象')],when='孙深意去世后，具体年月未载',year=None,place='狼山',note='坐化是孙方简的说法，不取代去世事实。')
add('border_people_suffer_levies_raids','后晋与契丹断交后，北边百姓受繁重赋役及盗寇侵扰',7,'会晋与','其业。',[],when='后晋与契丹断交后，具体年月未载',year=None,place='后晋北边',note='以前已录断交主体事件，此处录对边民的后续影响，不重复另造断交事件。')
add('sun_group_fortifies_temple','孙方简、孙行友率乡里强壮者据寺筑寨自保',7,'方简、行友','自保。',[('孙方简','与孙行友率乡里豪健者据寺筑寨'),('孙行友','参与率众据寺自保')],when='后晋与契丹断交后，具体年月未载',year=None,place='狼山')
add('sun_intercepts_khitan_supplies','孙方简率众袭击来侵契丹兵，夺得兵器、牲畜和军资，更多人携家投靠',7,'契丹入寇，','益众。',[('孙方简','率众截击契丹军并获得军资，吸引避难者')],when='孙方简归附后晋之前，具体年月未载',year=None,place='狼山及边地',note='本段总叙多次行动，不重复945年已单独记载的狼山某次胜仗。')
sup('sun_intercepts_khitan_supplies',7,ss,'每契丹軍來，必率其徒襲擊之，鎧仗、畜產所得漸多，人益依以避難焉。','《宋史》也记孙方谏率众袭击契丹军，逐渐取得甲仗畜产，吸引更多避难者。','该传叙述归朝以后行动，主段叙述归朝以前；只补长期行动模式，不强合成同一日战斗。',relation='adds')
add('sun_group_grows_and_raids','孙方简部众渐至千余家，后来成为群盗',7,'久之，','群盗。',[('孙方简','部众扩至千余家，史书记其成为群盗')],when='狼山据寨后的长期变化，具体年月未载',year=None,place='狼山',note='千余家是户数概数，不换为精确军队人数。')
add('sun_submits_to_jin','孙方简担心官府讨伐，转而归附后晋',7,'惧为','朝廷。',[('孙方简','因惧官府讨伐而归附后晋')],when='孙方简聚众后、946年再降契丹以前，具体年月未载',year=None,place='狼山至后晋朝廷')
add('sun_receives_recruitment_command','后晋希望借孙方简抵御契丹，授他东北招收指挥使',7,'朝廷亦',None,[('孙方简','被后晋任命为东北招收指挥使')],when='孙方简归附后晋后，具体年月未载',year=None,place='狼山')
sup('sun_receives_recruitment_command',7,ss,'方諫懼主帥捕逐，乃表歸朝，因署為東北面招收指揮使，且賜院額曰「勝福」。','《宋史》记孙方谏惧遭主帅捕逐，上表归朝，被署东北面招收指挥使，寺院获赐胜福之额。','补归朝与官号及赐额，未将此后边界游奕使、行友副职或宋初经历提前本年。',relation='adds')
# 8: actual capture and returned report, versus feared future invasion.
add('sun_raids_khitan_territory','孙方简不时入契丹境抢掠，多有杀获',8,'方简时','杀获。',[('孙方简','进入契丹境抢掠并杀获')],when='946年投契丹以前，具体年月未载',year=None,place='契丹边境',note='由进攻境外行为记录，不正当化或补统计死者数量。')
add('sun_demands_and_defects','孙方简不断索求，后晋稍未满足便率全寨投契丹',8,'既而','契丹，',[('孙方简','因要求未满足，率寨投契丹')],when='946年六月条前后，具体日未载',place='狼山至契丹')
sup('sun_demands_and_defects',8,oj,'狼山招收指揮使孫方簡叛，據狼山歸契丹。','《旧五代史》在六月记狼山招收指挥使孙方简叛晋、据狼山归契丹。','六月条首庚申为朔日，非该句单独给出的叛变日，不据此套庚申。')
add('sun_offers_guide','孙方简请求为契丹入侵后晋领路',8,'请为','入寇。',[('孙方简','向契丹请求作乡导入侵后晋')],when='946年投契丹后，具体日未载',place='契丹至后晋边境',note='只记录请求，不将后续大举入侵提前视作本段已经完成。')
add('north_famine_and_bandits','河北大饥，死亡众多，兖郓沧贝一带盗贼蜂起，官府不能制止',8,'时河北','不能禁。',[],when='946年六月条前后，具体起止未载',place='河北及兖、郓、沧、贝',note='以万数为史书概述，不算为精确总死亡数；峰起底本字形保留。')
sup('north_famine_and_bandits',8,oa,'時河南、河北大饑，殍名甚眾，沂、密、兗、鄆寇盜群起，所在屯聚，剽劫縣邑，吏不能禁。','《旧五代史》四月也记河南、河北大饥，沂密兖郓盗贼群起、抢掠县邑，官府不能制止。','两书月份和列举地区不同，各保留，不能据此断定仅限这几州或同一天。',relation='adds')
add('du_sends_liu_buy_horses','杜重威派刘延翰到边地买马',8,'天雄节度','于边，',[('杜威','派元随军将刘延翰到边地买马'),('刘延翰','奉命赴边地买马')],when='946年六月壬戌返回之前，具体日未载',place='天雄军至边地',note='元随为随从军将身份，不误读为元朝将领。')
add('sun_captures_liu','孙方简拘执刘延翰，把他送给契丹',8,'方简执之，','契丹。',[('孙方简','拘执买马的刘延翰并献给契丹'),('刘延翰','被拘执并送往契丹')],when='946年六月壬戌以前，具体日未载',place='边地至契丹')
add('liu_escapes_and_warns','刘延翰逃归，于六月壬戌抵大梁，报告孙方简拟引契丹入侵并请备御',8,'延翰逃归，',None,[('刘延翰','逃归抵大梁，报告孙方简欲借饥荒引契丹入侵')],when='946年六月壬戌抵大梁，逃脱日未载',place='契丹至大梁',note='壬戌是抵梁并陈报日；引契丹入寇是报告的计划，不当作本段已经入侵。')
reviews={1:'宋官荣衔奉朝请非执政；冯己巳既有别名复用。人物评价与高越指控区分。初字设院、讲话、撤职、出观察使及称疾都追述，年未定。宣政殿院不同称保留。严父关系方向。',2:'日食纪日同旧本纪，不算现代观测地。',3:'婚事主三月庚申旧四月并列，不猜订婚婚礼。县官指政府、数倍不算确定值。两个皇子是高祖孙且帝养子，父母未名；祖父养父兄长分方向，不造未名妻或亲父。',4:'弘义复用李仁达改名，礼争为所述动机，兵万保留概数；李弘通弟关系明确。',5:'初字留拓跋、离镇释放、王不抚为追述，告急以前有攻城杀弟。戊午只告急日，三族共同攻不可拆具名凶手。',6:'都都挥底本疑字不建官号；话语与实际废任作战分开。主先刺史后清源军新合记节度，军额后续另录；新执送金陵与主废归第召回步骤并列，不提前后世逐驻军。',7:'初期狼山聚众均追述不强946。妖术灵验为史书及信众评价，坐化为孙称，自言侄不确证姑侄。孙简谏按狼山职迹对应，主弟宋兄子关系冲突；姑帅尼孙无确死年。千余家为户数不变兵数，945已录单战不重复。',8:'六月旧本纪补孙叛但朔日非叛变确日。夺刘与逃归陈报分开，壬戌抵梁日。请求乡导和欲引侵为意图非已侵；大饥地区月份跨书保留，元随非元朝。'}
assert not (P/'publication.json').exists()
for n in range(1,9):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285原31—38行连续八段，946年共56段，本批之后仍有48段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],source_contexts=[dict(source_key=main_sources[0],note='复用945年末快照中946年第一段，只录本年正月；旧段不重复。'),dict(source_key=main_sources[1],note='只录946年第2—8段；快照末第9—10段留上下文，下批继续。'),dict(source_key=ss,note='补狼山人物、早期聚众与职衔和亲属异说，不提前录该传后晋灭亡以后汉周宋时期经历。'),dict(source_key=mi,note='复用留从效与王继勋处置的补证，后续清源军、逐驻军和蔡氏使周不提前录。')],source_issues_review='婚事三月四月、孙简谏姓名与兄弟叔侄、宣政殿院、泉州官制压缩记述各自保留待核，未将所有追述强定946。都都挥底本疑字与纸本待核。',plain_language_review='首次逐项阅读人物、标题、说明、参与角色、亲属方向和事实说明，简体完整主语。评价、指控、亲属自称、计划、奏报和已发生处置分开；逐字引用保留原文，不以排版或搜索摘要替代出处。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
