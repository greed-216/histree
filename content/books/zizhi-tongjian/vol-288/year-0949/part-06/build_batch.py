# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 949 paragraphs 33–37."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
COMMIT='00a00dec3e96e2d090e708b0dd9446e64b281f10'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-107-yang-bin-power','xinwudaishi-068-fall-year']:
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
main_sources = ['tongjian-288-949-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0949-p033-p037',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-288-949-year-end':'卷288·乾祐二年·十二月及追述','xinwudaishi-053-fengxiang-fall':'卷53·王景崇传·凤翔城破','jiuwudaishi-103-january-950-reports':'卷103·隐帝本纪·乾祐三年正月奏报','songshi-483-qingyuan-establishment':'卷483·留从效传·清源军设置','songshi-483-liu-congyuan-identity':'卷483·留从效传·兄留从愿'}
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
for n in range(33, 38):
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
    labels={'tongjian-288-949-year-end':'卷288·乾祐二年·十二月及追述','xinwudaishi-053-fengxiang-fall':'卷53·王景崇传·凤翔城破','jiuwudaishi-103-january-950-reports':'卷103·隐帝本纪·乾祐三年正月奏报','songshi-483-qingyuan-establishment':'卷483·留从效传·清源军设置','songshi-483-liu-congyuan-identity':'卷483·留从效传·兄留从愿'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐二年（949年十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0949_06_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=949, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='949年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_288_0949_' + code
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
        edge = 'participation_zztj_288_0949_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_288_0949_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘承祐','南汉主':'刘弘熙','刘晟':'刘弘熙','唐主':'李璟','从愿':'留从愿'})
NEW_ALIASES={'周璨':[],'公孙辇':['公孫輦'],'张思练':['張思練'],'王万敢':['王萬敢'],'留从愿':['留從願']}
NEW_DESCRIPTIONS={
'周璨':'邢州人，曾任诸卫将军，失去官职后跟随王景崇西行，成为谋士。949年凤翔战事末期劝王景崇投降，王景崇自焚后也投降。生卒年未载。',
'公孙辇':'王景崇的将领。949年十二月按计划烧凤翔东门诈降，得知王景崇已自焚后投降赵晖。《新五代史》也记此事。生卒年未载。',
'张思练':'王景崇的将领。949年十二月与公孙辇烧凤翔东门诈降，派人察看府署后得知王景崇已自焚。生卒年及随后是否正式受降未载。',
'王万敢':'后汉密州刺史。949年十二月攻击南唐海州获水镇；《旧五代史》次年正月也载他在海州方向的奏报，镇名作荻水，地名及是否同次行动仍待校核。生卒年未载。',
'留从愿':'留从效的兄长。949年《通鉴》记他毒杀董思安并接任刺史，职名前地名写南州，尚待校核。《宋史》留从效传也明记有兄从愿。生卒年未载。'}
yang='jiuwudaishi-107-yang-bin-power';feng='xinwudaishi-053-fengxiang-fall';jan='jiuwudaishi-103-january-950-reports';qing='songshi-483-qingyuan-establishment';bro='songshi-483-liu-congyuan-identity';fall='xinwudaishi-068-fall-year'
add('zhou_can_joins_wang','周璨失去官职后跟随王景崇，成为他的谋士',33,'初，邢州人周璨','遂为之谋主。',[('周璨','失去诸卫将军官职后跟随王景崇西行，成为谋士'),('王景崇','叛乱后由周璨为其出谋划策')],year=None,when='王景崇西行及叛乱期间的追述，具体年月未载',place='西行途中及王景崇幕府',note='初为追述，不能因为该段排在949年十二月就把失官、西行与叛乱都定在此月。')
add('yang_requests_former_officers_capital','杨邠请求让卸任官员都到京师，以免鼓动藩镇',33,'邠奏：','宜悉遣诣京师。”',[('杨邠','认为卸任官员会鼓动藩镇，请求让他们都到京师')],year=None,when='杨邠执政期间、949年十二月再奏以前，具体起始未载',place='后汉朝廷',note='喜摇动藩臣是杨邠的判断，不认定每个卸任官员都曾煽动叛乱。')
add('former_officers_block_chancellors','卸任官员聚集京师，经常拦宰相求官',33,'既而四方云集，','日遮宰相马求官。',[],year=None,when='杨邠要求卸任官员到京师之后，具体起止未载',place='后汉京师',note='未列拦马者和宰相姓名，不擅把每次受阻都指为杨邠本人。')
add('yang_requests_two_capitals_waiting','杨邠请求将卸任官员分居两京，等待空缺补官',33,'辛卯，','以俟有阙而补之。”',[('杨邠','请求让卸任官员分居两京等待补官')],when='949年十二月条下辛卯',place='后汉朝廷、两京',note='奏请与随后漂泊失所情况区分，未列分配名单或补任结果。')
add('former_officers_displaced','史书记许多卸任官员漂泊、失去居所',33,'漂泊失所者甚众。','漂泊失所者甚众。',[],when='949年十二月条下，具体起止未载',place='后汉两京及官员往来途中',note='甚众为史书概述，不补人数、籍贯或个人名单。')
add('yang_travel_passes_abandoned','杨邠要求行人持通行凭证，因办理拥堵与民众困扰而停止',33,'邠又奏：',None,[('杨邠','要求行人领取通行凭证，造成拥堵后停止')],year=None,when='杨邠执政期间，949年十二月条下记载，具体起止未载',place='后汉各地办证官署及道路',note='过所解释为通行凭证，不造现代证件制度；乃止按上下文是停止这项要求，不指杨邠停止全部执政。')
sup('yang_travel_passes_abandoned',33,yang,'前資官不得於外方居止，自京師至諸州府，行人往來，並須給公憑。','《旧五代史》也记卸任官员不得留居外地、往来行人须领公凭。','与主书政策相互参照，公凭与过所称谓分别保留；后文旬日民扰是此书时长，不换算具体公历起止。')
sup('yang_travel_passes_abandoned',33,yang,'旬日之間，民情大擾，行路擁塞，邠乃止其事。','《旧五代史》记十来天内民众深受困扰、道路拥塞，杨邠停止此事。','旬日为该书所记经过，主书未列天数；不把政策发端强定为十二月某日。',relation='adds')
add('zhou_can_advises_surrender','赵晖加紧攻凤翔，周璨劝王景崇投降',34,'赵晖急攻凤翔，','吾更思之。”',[('赵晖','加紧攻打凤翔'),('周璨','认为河中、长安已平，劝王景崇投降'),('王景崇','表示再考虑投降建议')],when='949年十二月癸巳以前，具体劝降日未载',place='凤翔',note='蒲、雍对应此前河中、长安两镇；蜀儿不足恃为周璨判断，再考虑不等于已经投降。')
sup('zhou_can_advises_surrender',34,feng,'景崇客周璨謂景崇曰：','《新五代史》也记谋士周璨劝王景崇投降。','同一王景崇、周璨及河中京兆已败背景，未把两书详略算成两次劝告。')
add('wang_plans_feigned_surrender','王景崇计划让公孙辇、张思练诈降，自己突击城北',34,'后数日，','皆曰：“善。”',[('王景崇','计划让部将烧东门诈降，自己与周璨率牙兵突击城北'),('周璨','被列入王景崇计划的城北突击队'),('公孙辇','接受烧东门诈降的计划'),('张思练','接受烧东门诈降的计划')],when='949年十二月癸巳前一日计划次日行动',place='凤翔府署、东门及城北',note='这是部署方案，后文王景崇自焚，不写成他和周璨已实际出北门突击。')
add('gongsun_zhang_burn_east_gate','公孙辇与张思练在天亮前烧凤翔东门请降',34,'癸巳，','府牙火亦发。',[('公孙辇','按部署烧东门请降'),('张思练','与公孙辇共同烧东门请降')],when='949年十二月癸巳天亮前',place='凤翔东门',note='按前段属于诈降部署；随后府署起火，不补火的具体起点或燃烧范围。')
add('wang_jingchong_self_immolation','部将查探发现王景崇已与家人自焚',34,'二将遣人诇之，','景崇已与家人自焚矣。',[('公孙辇','派人察看府署情况'),('张思练','派人察看府署情况'),('王景崇','被发现已与家人自焚')],when='949年十二月癸巳天亮前后',place='凤翔府署',note='已自焚为查探结果，具体家属名单和是否全数死亡未列，不补姓名。')
sup('wang_jingchong_self_immolation',34,jan,'前月二十四日，收復鳳翔，逆賊王景崇舉族自燔而死。','《旧五代史》950年正月记赵晖奏报：上月二十四日收复凤翔，王景崇一家自焚而死。','前月即949年十二月，不能把正月奏报日当死亡日；举族为此书表述，主书未列家人具体名单。',relation='adds',field='time_original')
sup('wang_jingchong_self_immolation',34,feng,'而府中火起，景崇自焚矣，','《新五代史》也记府中起火、王景崇自焚。','同一结局，不能把自焚写成赵晖攻入府署后杀死王景崇。')
claim('person',people['王景崇'],'death_year','王景崇于949年十二月自焚而死。',34,'景崇已与家人自焚矣。','原文癸巳与旧史次年奏报前月二十四日分别定位，不覆盖旧人物档案字段。')
add('zhou_can_surrenders','王景崇自焚后，周璨投降',34,'璨亦降。','璨亦降。',[('周璨','在王景崇自焚后投降')],when='949年十二月癸巳王景崇自焚后',place='凤翔',note='投降不等于已被处死或已获新职，主书未记后续处置。')
event('gongsun_surrenders_zhao','《新五代史》记公孙辇最终向赵晖投降',34,'輦乃降暉。',[('公孙辇','得知王景崇自焚后投降赵晖'),('赵晖','接受公孙辇投降')],when='949年十二月凤翔府署起火、王景崇自焚后',place='凤翔',source=feng,note='新史具名记公孙辇最终投降，不因主书二将共同烧门就把张思练的后续也写成确定受降。')
add('wang_wangan_attacks_haizhou','王万敢攻打南唐海州获水镇，破坏该镇',35,'丁酉，',None,[('王万敢','以密州刺史身份攻打海州获水镇')],when='949年十二月丁酉',place='海州获水镇',note='残之指破坏、摧残，未给死亡人数；不直接改成全镇被屠或并入后汉。')
sup('wang_wangan_attacks_haizhou',35,jan,'密州刺史王萬敢奏，奉詔領兵入海州界，至荻水鎮，俘掠焚蕩，更請益兵。','《旧五代史》次年正月记王万敢在海州方向的奏报，镇名作荻水，并记俘掠焚烧。','仅作跨年地名及行动参照，是否就是949年丁酉同一次攻击尚未确定，不把正月奏报合成949年当日战果或预先录其请求增兵。',relation='adds',field='location_name')
add('southern_han_ruler_visits_yingzhou','南汉主刘晟前往英州',36,'是月，',None,[('南汉主','在十二月前往英州')],when='949年十二月，具体日未载',place='英州',note='南汉主为已于943年改名刘晟的刘弘熙，复用既有主体；如是前往，不写成英州遭进攻或有具体巡幸政策。')
add('liu_congyuan_poison_dong','留从愿毒杀刺史董思安，接替其职',37,'是岁，','而代之。',[('留从愿','毒杀董思安，接替刺史职务'),('董思安','被留从愿毒杀')],when='949年，具体月日未载',place='董思安所任州，底本州名待核',note='南州副使为选定底本原字，未据后文或宋史后年守漳州强改成漳州；鸩指用毒杀害，不补药物种类。')
relationship('留从愿','留从效','兄长',37,'留从效兄南州副使从愿，','兄从愿明确是留从效的兄长，不因原文只写名而另建从愿主体。')
claim('person',people['留从愿'],'description','《宋史》也记留从效有兄长从愿。',37,'從效無嗣，以兄從願之子紹錤、紹糸茲為子。','仅用于亲属身份核对，不提前录建隆三年留从效患病、从愿守漳州及其子被收养等后年事件。',source=bro)
claim('person',people['董思安'],'death_year','《资治通鉴》记董思安于949年被留从愿毒杀。',37,span(37,'是岁，','而代之。'),'年度末是岁只确认该年，月日与州名待核；不覆盖原人物档案。')
add('li_jing_establishes_qingyuan','李璟无法制约泉州势力，在泉州设置清源军',37,'唐主不能制，','置清源军于泉州，',[('李璟','无法制约地方势力，在泉州设置清源军'),('留从效','作为泉州刺史处于清源军设置背景中')],when='949年，具体月日未载',place='泉州',note='按主书本年年末记载；设置军镇不等于新增现代行政军区疆界，其他书编排差异保留。')
sup('li_jing_establishes_qingyuan',37,qing,'李景即建泉州為清源軍，授從效節度、泉漳等州觀察使。','《宋史》也记李璟将泉州设为清源军，授留从效节度、泉漳等州观察使。','同一设军任命叙述，但此传未明确设军年，不能作为949年日期的独立确证。',relation='adds')
sup('li_jing_establishes_qingyuan',37,fall,'留從効聞延政降唐，執王繼勳送于金陵，李景以泉州為清源軍，以從効為節度使。','《新五代史》把泉州设清源军、任留从效为节度使接在王延政降唐之后。','书中时序编排与主书949年年末条不同，末注另记王氏灭亡年；不据传记相接强定设军也在同年，不把同一任命算成两次。',relation='conflicts',field='time_original')
add('liu_congxiao_appointed_qingyuan','李璟任命留从效为清源军节度使',37,'唐主不能制，',None,[('李璟','任命留从效为清源军节度使'),('留从效','获任清源军节度使')],when='949年，具体月日未载',place='泉州、清源军',note='依据主书本年条记录任命，其他书只印证任命内容，不静默消除时间编排差异。')
claim('person',people['杨邠'],'description','《资治通鉴》评价杨邠执政苛刻，过分拘泥细节。',33,'杨邠为政苛细。','这是史家对执政风格的评价，与具体政策经过分别保存，不当成每项政令都已被证明有害。')
reviews={33:'杨邠执政概述与周璨追述不一律系949年十二月；奏请、官员求职、分居两京、漂泊和办证政策停止分开。过所、公凭解释为通行凭证，匿名官员不补名单，民扰不造具体人数。',34:'劝降、再思、诈降突围方案、烧门、查探自焚、周璨投降分开。计划出北门不写成已实施，张思练后续受降不凭同场推定。旧史次年正月奏报前月二十四日与主书十二月癸巳定位保留，举族不造名单。',35:'获水为主书底本，旧史次年荻水作地名校读及相关行动参照，尚未认定同次；不将次年奏报和增兵请求提前算成949年事件。',36:'南汉主复用刘弘熙即刘晟，避免重建改名主体；如英州解释为前往，不补未记活动。',37:'是岁年末条不借十二月作发生月。留从愿与从效兄弟方向明确，南州字形未强改漳州。毒杀和接任、设军、授节度分开；宋史与新史的内容和时序分别补证，后年传记用于核身份不提前录未来事件。'}
assert not (P/'publication.json').exists()
for n in range(33,38):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=949,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(33,38)],next_paragraph='zztj-v289-y0950-p001',next_volume=289,next_year=950,supplements=supplements,excluded_non_body=[],coverage='卷288原111—115行最后五段；949年37段待本批发布及全年度审计后才标完成。下卷289从950年开始，末附后周纪书名不作为950年事件。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(33,38)],source_issues_review='获水/荻水、南州字形待纸本校核；次年奏报严格区别实际发生年月。泉州设军在宋史、新史的传记时序与主书年末条有差别，不强造一致年份。后年从愿及其子身份仅用于核对兄弟，不提前录后年事件。王景崇家人名单与张思练最终处置未载，不补造。',plain_language_review='首次逐条检查标题、人物介绍、正文、参与角色、关系方向、时间地点与事实解释。明确人名主语，区分追述、政策请求、计划、实际结果、史家评价和跨年奏报。原字保留，未知月份或地名留说明，复用主体不改旧档案，不安排固定发布后二次改写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
