# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 41–48."""
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
COMMIT='b4d5619c4b0564063398c9e7df3a0b4b109d63d7'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-287-947-hengzhou-uprising','jiuwudaishi-100-august-hengzhou']:
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
main_sources = ['tongjian-287-947-hengzhou-uprising','tongjian-287-947-august-administration']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p041-p048',
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
for n in range(41, 49):
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
        citation = f'卷287·天福十二年（947年八月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_06_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'刘知远','麻荅':'麻答','刘鐸':'刘铎','李荣':'李筠（原名李荣）','希广':'马希广','希萼':'马希萼','希崇':'马希崇'})
NEW_ALIASES={'张令柔':['張令柔'],'马希崇':['馬希崇'],'周廷诲':['周廷誨']}
NEW_DESCRIPTIONS={'张令柔':'后汉捕盗使者。《旧五代史》《新五代史》记为郓州捕贼使臣或使者。947年严厉捕盗法令施行后，杀害平阴十七个村庄的居民；《新五代史》记死者数百人。生卒年未载。','马希崇':'马希广的庶弟、马希萼的弟弟。947年任楚天策左司马，秘密致信马希萼指责继位安排，又向他报告马希广的言行并约为内应。生卒年尚未录入。','周廷诲':'楚侍从都指挥使。947年奉马希广命率水军迎接前来奔丧的马希萼，并建议杀死马希萼，马希广没有同意。生卒年未载。'}
aug='jiuwudaishi-100-august-hengzhou';old='jiuwudaishi-108-su-fengji';new='xinwudaishi-030-su-criminal-policy';ma='xinwudaishi-066-ma-xie-mourning';li='songshi-484-li-yun-bozhou'
t='947年八月，具体日未载'
add('yang_gun_returns_north','杨衮得知麻答被逐，当天从邢州北返',41,'杨衮至邢州，','即日北还，',[('杨衮','抵达邢州后闻讯，当天北返')],when='947年八月恒州起兵后，杨衮闻讯当日',place='邢州至北方',note='即日指闻讯当日，未载干支，不能直接写为恒州八月壬午起兵当日。')
add('yang_an_flees','杨安在麻答被逐后逃离',41,'杨安亦','遁去，',[('杨安','逃离')],when='947年八月恒州起兵后，具体日未载',place='邢、洺一带',note='依前段活动地域说明，未载具体逃离终点。')
add('li_yin_submits','李殷率部归降后汉',41,'李殷以',None,[('李殷','率所部归降')],when='947年八月恒州起兵后，具体日未载',place='邢、洺一带')
add('xue_anguo_commission','薛怀让获任安国节度使',42,'庚寅，','安国节度使。',[('薛怀让','获任安国节度使')],when='947年八月庚寅',place='后汉朝廷、邢州安国军')
sup('xue_anguo_commission',42,aug,'庚寅，以洺州團練使薛懷讓為邢州節度使。','《旧五代史》也记庚寅任薛怀让为邢州节度使，任前职名写为洺州团练使。','安国为邢州军号，两书以军名与州名分别表述；该书任前团练使与通鉴前段防御使不同，保留原职异文。',relation='adds')
add('liu_duo_xingzhou_surrenders','刘铎得知麻答逃走，举邢州归降',42,'刘鐸闻','举邢州降；',[('刘鐸','闻麻答逃离后，举州归降')],when='947年八月麻答逃离后，具体日未载',place='邢州')
add('xue_enters_kills_liu_duo','薛怀让假称巡检进入邢州，杀害已归降的刘铎',42,'怀让诈云巡检，','怀让杀鐸，',[('薛怀让','假称巡检，率军入城并杀刘铎'),('刘鐸','开门接纳薛怀让，被杀害')],when='947年八月刘铎归降后，具体杀害日未载',place='邢州',note='庚寅只明确任命日期，不将本段后续杀害绑定该日。')
sup('xue_enters_kills_liu_duo',42,aug,'懷讓乘其無備，遣人紿鐸云：「奉詔襲契丹，請置頓於郡。」鐸開門迎之，即為懷讓所害，時人冤之。','《旧五代史》记薛怀让假称奉诏袭契丹，请求在邢州设行军停驻处，刘铎开门后遭杀害。','诈入所用说辞与通鉴巡检不同，分别保留；此书对时人称冤的记载作为评价引用。',relation='adds')
add('xue_reports_recapture_unpunished','薛怀让把杀刘铎报作收复邢州，朝廷知情未追究',42,'以克复闻。',None,[('薛怀让','以收复邢州奏报'),('刘鐸','被杀事件没有获得朝廷追究')],when='947年八月，奏报及知情日未由《通鉴》具体注明',place='邢州至后汉朝廷',note='朝廷知而不问只表明未追究，不推刘知远亲自授意杀人。')
sup('xue_reports_recapture_unpunished',42,aug,'是日，薛懷讓奏，收復邢州，殺偽命節度副使、知州事劉鐸。','《旧五代史》将薛怀让奏报收复邢州、杀刘铎记在八月己酉。','己酉是奏报的纪日，不能据此断言刘铎在己酉当日遇害。',relation='adds')
add('hengzhou_restored_zhenzhou','恒州、顺国军恢复镇州、成德军旧名',43,'辛卯，','镇州成德军。',[],when='947年八月辛卯',place='恒州（恢复名镇州）')
sup('hengzhou_restored_zhenzhou',43,aug,'辛卯，詔恒州復為鎮州，順國軍復為成德軍。','《旧五代史》同记辛卯恢复镇州与成德军名称。','州名和军号分别恢复，不把两个名称当两个新设州。')
add('bai_formally_chengde','白再荣获朝廷正式任命为成德留后',43,'乙未，','成德留后。',[('白再荣','获正式任命为成德留后')],when='947年八月乙未',place='镇州成德军',note='区别上一批地方诸军推为权知留后；此次是朝廷正式授任。')
sup('bai_formally_chengde',43,aug,'乙未，以護聖左廂都指揮使、恩州團練使白再榮為鎮州留後。','《旧五代史》也记乙未任白再荣为镇州留后。','成德为镇州军号，任职记录相合。')
add('he_li_later_reward','恒州起兵逾年后，何福进与李筠才获授地方官职',43,'逾年，',None,[('何福进','获任曹州防御使'),('李荣','获任博州刺史')],year=None,when='947年恒州起兵逾年之后，具体年份未定',place='曹州、博州',note='逾年为后续追述，未载确年；不将此任命前移到947年，也不猜测当时授任皇帝。',description='《资治通鉴》记恒州起兵逾年之后，何福进才任曹州防御使，李荣任博州刺史。李荣即后来改名的李筠；具体授任年份尚未确定。')
sup('he_li_later_reward',43,li,'授再榮留後，筠博州刺史。筠以賞薄不悅。','《宋史》李筠传记授白再荣留后、李筠博州刺史，并记李筠认为赏赐薄而不悦。','此传把授官接在送款汉祖与赏军之后，但未单列任命年月；与通鉴逾年叙述次序不同，不据此确定947年或948年。该句没有何福进官职。',relation='conflicts')
add('han_death_penalty_thieves','后汉规定盗贼不论赃物多少都处死，并派使者追捕',44,'敕：','仍分命使者逐捕。',[],when=t,place='后汉各地',note='敕令与追捕安排确有记载；赃多少不影响死刑，不能拓展为所有犯罪都处死。')
sup('han_death_penalty_thieves',44,aug,'丙申，詔天下凡關賊盜，不計贓物多少，案驗不虛，並處死。','《旧五代史》记八月丙申下诏，盗案查验属实者不计赃物多少，一律处死。','补书提供法令纪日与案验不虚条件；此日只用于法令，不套用后续各地捕杀日期。',relation='adds')
add('su_drafts_collective_execution','苏逢吉起草法令，拟将盗贼及邻保全族处斩',44,'苏逢吉自草诏，','皆全族处斩。”',[('苏逢吉','起草株连盗贼及四邻同保全族的法令')],when=t,place='后汉朝廷',note='这是草拟内容，随后遭反对并删全族，不写为已执行全族处斩。')
sup('su_drafts_collective_execution',44,old,'逢吉自草詔意云：「應有賊盜，其本家及四鄰同保人，並仰所在全族處斬。」','《旧五代史》也记苏逢吉草诏拟令盗贼本家及四邻同保全族处斩。','作为草拟法令补证，不能将拟议范围写成全部实际行刑对象。')
add('su_removes_clan_word','众人反对族诛与株连邻保，苏逢吉最终删去“全族”',44,'众以为：','但省去“全族”字。',[('苏逢吉','争执后被迫删去全族二字')],when=t,place='后汉朝廷',note='只明确删全族；不能推断所有邻保连坐都取消。')
sup('su_removes_clan_word',44,new,'逢吉恡以為是，不得已，但去族誅而已。','《新五代史》也记苏逢吉坚持己见，最终被迫去掉族诛规定。','原文恡字照录；只印证族诛草案受阻，不推导后续法令不存在任何连坐。')
add('zhang_kills_pingyin_villagers','张令柔杀害平阴十七个村庄的居民',44,'由是捕贼使者',None,[('张令柔','以捕盗使者身份杀害平阴多个村庄居民')],when='947年严厉捕盗法令施行后，具体日未载',place='平阴',note='结合新五代史十七村民数百人，十七修饰村庄数量，不是十七名居民；死亡精确人数未载。',description='《资治通鉴》记捕盗使者张令柔杀害平阴十七个村庄的居民。《新五代史》补记死者数百人，具体人数未载。')
sup('zhang_kills_pingyin_villagers',44,new,'張令柔盡殺平陰縣十七村民數百人。','《新五代史》记张令柔杀害平阴县十七个村庄的居民，死者数百人。','数百为史载约数，十七为村数；保留约数，不创建精确死亡计数。',relation='adds')
sup('zhang_kills_pingyin_villagers',44,old,'時有鄆州捕賊使臣張令柔盡殺平陰縣十七村民，良由此也。','《旧五代史》记张令柔为郓州捕贼使臣，杀害平阴十七个村庄居民，并把此事与苏逢吉法令相联系。','该书未载数百的死亡人数；因果归属是该书史家叙述，不能证明每名被害者均曾被判盗罪。',relation='adds')
add('su_kills_prisoners_before_han','刘知远命苏逢吉整顿狱事祈福，苏却杀尽囚犯',45,'在河东幕府，','逢吉尽杀狱囚还报。',[('帝','在河东时命苏逢吉静狱以祈福'),('苏逢吉','杀尽狱囚后回报')],year=None,when='苏逢吉在河东幕府时，具体年份未载',place='河东',note='刘知远的静狱命令不等于命令处死全部囚犯；这是建国前往事，不能填947年。')
sup('su_kills_prisoners_before_han',45,old,'高祖命逢吉靜獄，以祈福祐，逢吉盡殺禁囚以報。','《旧五代史》也记刘知远命苏逢吉静狱祈福，苏杀尽禁囚以报。','同一追叙未明确年月，不补生卒年或处刑人数。')
add('liu_delegates_military','后汉初建，刘知远将军务交给杨邠与郭威',45,'及为相，','帝悉以军旅之事委杨邠、郭威，',[('帝','把军务委给杨邠、郭威'),('杨邠','受委处理军务'),('郭威','受委处理军务')],when='947年后汉初建时，具体日未载',place='后汉朝廷')
add('liu_delegates_civil','刘知远将各部门日常政务交给苏逢吉与苏禹珪',45,'百司庶务','苏禹珪。',[('苏逢吉','受委处理各部门政务'),('苏禹珪','受委处理各部门政务')],when='947年后汉初建时，具体日未载',place='后汉朝廷')
add('su_ministers_discretion','《资治通鉴》评价两位宰相决事迅速，但用人任意',45,'二相决事，','无敢言者。',[('苏逢吉','被记为凭己意决事、任免'),('苏禹珪','被记为凭己意决事、任免'),('帝','倚重信任两位宰相')],when='947年后汉初建时，具体各案日未载',place='后汉朝廷',note='这是史家对政务与用人的概述，不虚构具体被任免者、官职或案件。')
add('su_seeks_wealth','《资治通鉴》记苏逢吉公开索求财物',45,'逢吉尤贪诈，','无所顾避。',[('苏逢吉','被史书记为公开索求财物')],year=None,when='苏逢吉任相期间，具体各事年份未载',place='后汉',note='史家评价与行为概述并列，未载金额、索求对象及每案日期。')
add('su_ignores_stepmother_mourning','苏逢吉在继母去世后不守丧',45,'继母死，','不为服；',[('苏逢吉','继母死后不服丧')],year=None,when='具体年份未载',place='地点未详',note='继母未具名，不虚构人物姓名，未据传记排列指定947年。')
add('su_causes_halfbrother_death','苏逢吉秘密告知郭威，借别的事杖杀庶兄',45,'庶兄自外至，',None,[('苏逢吉','因庶兄未经告知便见其子而发怒，借别事害兄'),('郭威','《资治通鉴》记他受到苏逢吉秘密告知')],year=None,when='具体年份未载',place='地点未详',note='主书记密语郭威，未明言郭威亲自行刑。庶兄与诸子未具名，不新建匿名人物或补死亡年份。')
sup('su_causes_halfbrother_death',45,old,'乃密白高祖，誣以他事杖殺之。','《旧五代史》记苏逢吉秘密告知刘知远，以别事诬陷庶兄并杖杀。','秘密告知对象与通鉴的郭威不同，属于异说；刘知远和郭威均不能据此被认定为亲自行刑者。',relation='conflicts')
add('ma_xichong_letter','马希崇秘密致信马希萼，指责刘彦瑫等废长立少',46,'楚王希广庶弟','以激怒之。',[('希崇','秘密致信并指控继位安排，试图激怒兄长'),('希萼','收到弟弟的密信'),('刘彦瑫','受到密信中违命与废长立少指控')],when='947年马希广继位后，具体日未载',place='楚',note='违先王命为马希崇信中指控，不作为已证实的遗命事实；狡险为史家评价。')
relationship('希广','希崇','兄长',46,span(46,'楚王希广庶弟','以激怒之。'),'庶弟明确长幼，方向表示马希广是马希崇的兄长。')
relationship('希萼','希崇','兄长',46,span(46,'楚王希广庶弟','以激怒之。'),'阴遗兄希萼书明确兄长关系，方向表示马希萼是马希崇的兄长。')
add('ma_xie_arrives_mourning','马希萼来为马希范奔丧，八月乙巳到趺石',46,'希萼自永州','至趺石，',[('希萼','从永州来奔丧，到达趺石')],when='947年八月乙巳',place='永州至趺石',note='丧主据前文马希范死亡确定；趺石地名照底本，《新五代史》作砆石。')
sup('ma_xie_arrives_mourning',46,ma,'希範之卒，希萼自朗州來奔喪。','《新五代史》记马希萼从朗州来为马希范奔丧。','出发地与通鉴永州不同，各自保留；此书未列乙巳纪日，不作为纪日独立确证。',relation='conflicts')
add('ma_xie_disarmed_lodged','刘彦瑫建议派水军迎马希萼，令其部众卸甲并限制会面',46,'彦瑫白','不听入与希广相见。',[('刘彦瑫','向马希广建议派水军迎接'),('希广','派周廷诲等率水军，限制马希萼会面'),('周廷诲','率水军迎接马希萼'),('希萼','被安排住碧湘宫，未获与马希广见面')],when='947年八月乙巳抵达后，具体日未另载',place='趺石、碧湘宫',note='逆为迎接并戒备，此句未载实际交战；成服于其次为在所住之处服丧，不写成获入府见希广。',description='刘彦瑫建议马希广派周廷诲等率水军迎接马希萼，令永州将士卸甲入城。马希萼被安置在碧湘宫，于所住之处服丧，未获准与马希广相见。')
sup('ma_xie_disarmed_lodged',46,ma,'乃以兵迎希萼於砆石，止之於碧湘宮，厚賂以遣之。','《新五代史》也记以兵迎马希萼，将其留在碧湘宫，再厚赠遣回。','该书地点写砆石，通鉴写趺石，保留字形差异，地理坐标未核。',relation='adds')
add('zhou_proposes_killing_ma_xie','周廷诲建议杀马希萼，马希广不忍杀兄而拒绝',46,'希萼求示还朗州，','宁分潭、朗而治之。”',[('希萼','请求返回朗州'),('周廷诲','建议马希广杀兄'),('希广','不忍杀兄，表示宁愿分治潭、朗')],when='947年八月奔丧期间，具体日未载',place='楚',note='杀人提议未执行；宁分而治是拒杀时的意愿，不能作为已经分国的结果。求示还原字保留，解释作请求回朗州。')
relationship('希萼','希广','兄长',46,span(46,'希广曰：','宁分潭、朗而治之。”'),'吾何忍杀兄明确兄长为马希萼；复用既有人物与方向关系，不另建逆向边。')
sup('zhou_proposes_killing_ma_xie',46,ma,'張少敵、周廷誨曰：「王能與之則已，不然宜早除之。」','《新五代史》记张少敌与周廷诲都建议，若不能让位便应早除马希萼。','该书增加张少敌与让位前提，通鉴只记周廷诲劝杀；此为提议，不是实际杀害。',relation='adds')
add('ma_xie_sent_back_langzhou','马希广厚赠马希萼，遣其返回朗州',46,'乃厚赠希萼，','遣还朗州。',[('希广','厚赠兄长并遣回朗州'),('希萼','获赠后被遣回朗州')],when='947年八月奔丧之后，具体日未载',place='楚至朗州')
add('ma_xichong_intelligence','马希崇向马希萼报告马希广言行，约定作内应',46,'希崇常为',None,[('希崇','侦察、报告马希广言行，约作内应'),('希萼','获得马希崇提供的情报与内应承诺'),('希广','言行遭弟弟侦察与报告')],when='947年继位争执后开始，持续期间及具体日未载',place='楚',note='常为报告是持续行为，约为内应是承诺，不提前写成后来的政变已经发生。')
add('khitan_takes_jin_horses','契丹灭后晋时驱走二万匹战马',47,'契丹之灭晋也，','归其国。',[],when='947年契丹灭后晋时，具体日未载',place='后晋至契丹',note='这是八月条内追述灭晋之事；二万是史载数目，不绑定八月购马命令。')
add('han_buys_horses','后汉军队缺马，下令在河南未遭劫掠的各道购买民马',47,'至是汉兵乏马，',None,[],when=t,place='河南诸道未遭剽掠者',note='市指购买，不能写成无偿强征全部民马；河南为历史地域，非现代省界。')
sup('han_buys_horses',47,aug,'是月，遣使諸道和市戰馬。','《旧五代史》记八月遣使到诸道购买战马。','该书未限定河南未经剽掠地区；可补购马月份，不能推定各道购买数量或价格。',relation='adds')
add('qian_formal_wuyue_commission','钱弘倧获授吴越王及东南兵马都元帅等职',48,'制以',None,[('钱弘倧','获授吴越王、东南兵马都元帅、镇海镇东节度使兼中书令')],when=t,place='后汉朝廷、吴越',note='区别此前六月钱弘倧实际继位与遗命掌军，此处是后汉朝廷授官命令，未载具体日。')
reviews={41:'撤兵与归降分录，即日仅指杨衮闻讯当日。',42:'庚寅任官、刘铎举州降、薛诈入杀害、报克复与知而不问分清；己酉仅为旧史奏报日，说辞与任前职名异文保留。',43:'恢复州军名、乙未正式授任与地方暂掌区别；逾年授何李官职确年未载为null，宋传叙事次序并列，不指定授任皇帝。',44:'全族处斩为草案，反对后只删全族；17为村数，新史数百为死亡约数；法令丙申不套杀民日期。',45:'静狱令与苏尽杀囚区分，往事确年未载为null；军旅与庶务委任、史家评价与家事分录；杀兄密告郭威与密告高祖异说保留，未认定郭威亲自行刑。',46:'希崇指控遗命不当已证实事实；永州与朗州、趺石与砆石异文保留；卸甲住宫禁见、杀议被拒、赠归与情报内应分录，分治愿望不当已分国。',47:'契丹灭晋带走马与后汉八月购买民马分开，河南不用现代省界。',48:'正式朝廷授官区别六月实际继位，未虚构授官干支。'}
assert not (P/'publication.json').exists()
for n in range(41,49):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(41,49)],next_paragraph=Q[49]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原46—53行连续八段，本卷累计48/75；947年跨卷累计140/167，尚未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(41,49)],source_issues_review='杀刘铎诈入说辞、苏逢吉杀兄密告对象、马希萼奔丧出发地及趺砆字形保留异说；何李逾年授官确年未定。平阴十七为村数，数百为史载约数。',plain_language_review='首次检查人物、事件、参与、关系及事实说明，明确主语；草案、提议与实际结果分开，追叙确年未知为null，逐字摘录保持原字。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
