# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 288, year 949 paragraphs 27–32."""
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
COMMIT='7852147b76d0b357a666a03e1c8d219918bae3dc'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-288-949-august-december','jiuwudaishi-102-september-949','jiuwudaishi-110-return-court-949']:
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
main_sources = ['tongjian-288-949-august-december']
B = {'format_version': 1, 'batch_key': 'zztj-v288-y0949-p027-p032',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-102-october-949':'卷102·隐帝本纪·乾祐二年十月','jiuwudaishi-102-december-949':'卷102·隐帝本纪·乾祐二年十二月','liaoshi-005-hebei-949':'卷5·世宗纪·天禄三年十月','xinwudaishi-018-liu-yun-identity':'卷18·汉家人传·刘赟亲支'}
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
for n in range(27, 33):
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
    labels={'jiuwudaishi-102-october-949':'卷102·隐帝本纪·乾祐二年十月','jiuwudaishi-102-december-949':'卷102·隐帝本纪·乾祐二年十二月','liaoshi-005-hebei-949':'卷5·世宗纪·天禄三年十月','xinwudaishi-018-liu-yun-identity':'卷18·汉家人传·刘赟亲支'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷288·乾祐二年（949年九月至十二月）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_288_0949_05_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'刘承祐','吴越王':'钱弘俶','弘亻叔':'钱弘俶','希广':'马希广','刘崇':'刘崇（刘知远弟）'})
NEW_ALIASES={'刘赟':['劉赟','劉贇'],'白福进':['白福進'],'史万山':['史萬山']}
NEW_DESCRIPTIONS={
'刘赟':'刘崇的儿子，刘知远喜爱他，把他当作自己的儿子。《新五代史》记948年任徐州节度使，949年《通鉴》记以武宁节度使身份获加同平章事。后续经历随主书年代续录，生卒年尚未录入。',
'白福进':'后汉颍州将领。949年十二月在正阳击败渡淮进攻的南唐军。生卒年与其他职务未载，未因名字相似与何福进等人合并。',
'史万山':'后汉深州刺史。《辽史》记天禄三年、即949年十月辽军侵入河北时被杀。生年及此前经历尚未录入。'}
NEW_DEATH_YEARS={'史万山':949}
sept='jiuwudaishi-102-september-949';octo='jiuwudaishi-102-october-949';dec='jiuwudaishi-102-december-949';guo='jiuwudaishi-110-return-court-949';liao='liaoshi-005-hebei-949';yun='xinwudaishi-018-liu-yun-identity'
# Each grant has its own subject and original date; shared clauses remain exact excerpts.
groups=[
('09_yisi','乙巳，','兼中书令。','九月乙巳',[('郭威','兼侍中'),('史弘肇','兼中书令')]),
('09_xinhai','辛亥，','杨邠右仆射。','九月辛亥',[('窦贞固','司徒'),('苏逢吉','司空'),('苏禹珪','左仆射'),('杨邠','右仆射')]),
('09_yimao','乙卯，','刘崇兼中书令。','九月乙卯',[('高行周','守太师'),('安审琦','守太傅'),('符彦卿','守太保'),('刘崇','兼中书令')]),
('09_jiwei','己未，','并兼侍中。','九月己未',[('刘信','兼侍中'),('慕容彦超','兼侍中'),('刘铢','兼侍中')]),
('09_xinyou','辛酉，','李彝殷兼中书令。','九月辛酉',[('冯晖','兼中书令'),('李彝殷','兼中书令')]),
('10_renshen','冬，十月，','刘赟同平章事；','十月壬申',[('孙方简','同平章事'),('刘赟','同平章事')]),
('10_renwu','壬午，','楚王希广太尉；','十月壬午',[('钱弘俶','尚书令'),('马希广','太尉')]),
('10_bingxu','丙戌，','高保融兼侍中。','十月丙戌',[('高保融','兼侍中')])]
for code,start,end,date,actors in groups:
 for i,(name,rank) in enumerate(actors):
  canonical=ALIASES.get(name,name)
  add('grant_'+code+'_'+str(i),canonical+'获加'+rank,27,start,end,[(name,'获加'+rank)],when='949年'+date,place='后汉朝廷及相关节镇',note='按同一加官句分录各主体，加衔不直接等于亲赴大梁或改任原节镇；原官号、守字和兼字按各书记载保留。')
sup('grant_09_yisi_0',27,sept,'九月乙己，樞密使郭威檢校太師、兼侍中，','《旧五代史》也记郭威加检校太师、兼侍中，底本日干支写乙己。','乙己为选定底本字形，《通鉴》作乙巳；保留底本，不将己和巳静默改字。',relation='adds')
sup('grant_09_xinhai_3',27,sept,'楊邠加右僕射，依前兼樞密使。','《旧五代史》记杨邠加右仆射后仍兼任枢密使。','依前是仍任旧职，不据加衔认为辞去枢密使。',relation='adds')
add('ministers_consider_regional_rewards','朝廷大臣担心只赏留京执政者会引起藩镇不满',27,'诸大臣议，','恐籓镇觖望。',[],when='949年九月扩大加恩范围之前，具体议事日未载',place='后汉朝廷',note='这是大臣们的担忧，不证明每个藩镇已经抗议；诸大臣未列发言人姓名。')
sup('ministers_consider_regional_rewards',27,sept,'且外慮諸侯以朝廷有私於親近也，於是議及四方侯伯，普加恩焉。','《旧五代史》也记朝臣担心诸侯认为朝廷偏私亲近者，因此议及四方藩镇。','同一扩大加恩过程，匿名议论不补具体提案者。')
for code in ['grant_10_renshen_0','grant_10_renshen_1']:
 sup(code,27,octo,'冬十月庚午朔，契丹入寇。是日，定州孫方簡、徐州劉赟並加同平章事，','《旧五代史》记孙方简、刘赟加同平章事在十月庚午朔。','《通鉴》记十月壬申，按各书分别保留日期，不创建两次相同加衔。',relation='conflicts',field='time_original')
sup('grant_10_renwu_0',27,octo,'壬午，兩浙錢宏俶加守尚書令，湖南馬希廣加守太尉。','《旧五代史》同记十月壬午钱弘俶加守尚书令、马希广加守太尉。','宏俶对应既有钱弘俶，守字为旧史所载，不改写主书原句。')
sup('grant_10_bingxu_0',27,octo,'丙戌，荊南高保融加檢校太師、兼侍中；','《旧五代史》同记高保融兼侍中，并记加检校太师。','日期、主体相合，补充检校太师，不把兼侍中改成实际掌中书事务。',relation='adds')
claim('event',E['grant_09_yisi_0'],'historical_commentary','《资治通鉴》记有人赞许郭威与他人分享功劳，同时批评朝廷因一人立功而向各地广授爵位。',27,span(27,'议者以为：'),'这是史书所引匿名评论，不当作量化评估，也不补评论者姓名或发言日。')
relationship('刘崇','刘赟','父亲',27,'崇子曰贇，','崇为后汉高祖弟刘崇，贇为武宁、徐州节度使刘赟，与萧县刘崇和楚王赟分开。',source=yun)
relationship('刘知远','刘赟','养父',27,'崇子曰贇，高祖愛之，以為己子。','高祖为刘知远；按史书把侄子当己子的记载登记养父关系，未补收养程序或时间，生父仍为刘崇。',source=yun)
claim('person',people['刘赟'],'description','《新五代史》记刘赟于乾祐元年、即948年任徐州节度使。',27,'乾祐元年，拜贇徐州節度使。','作为刘赟身份背景补证，不把这次任命改成949年，也不另建重复旧年度事件。',source=yun)
add('qian_chu_tax_free_reclamation','钱弘俶招募百姓垦荒，免收所垦田的税',28,'吴越王弘亻叔','由是境内无弃田。',[('钱弘俶','鼓励百姓垦荒，免收所垦田的税')],when='949年十月条下，具体实施起止未载',place='吴越',note='免税范围承接垦荒田，不扩为所有税赋永久免除；境内无弃田是史书概括，不当作可核统计。')
add('qian_chu_punishes_tax_scheme','有人请求查漏登记壮丁以增赋，钱弘俶在国门杖责他',28,'或请纠民遗丁',None,[('钱弘俶','杖责请求查漏壮丁增赋并自掌其事的人')],when='949年十月条下，具体日未载',place='吴越国门，具体城门未载',note='遗丁按遗漏登记的壮丁理解，不指孤儿；或请未载请求者姓名，不补具体官员。国人皆悦为史书评价。')
add('ma_xizhan_repeatedly_mediates','马希瞻多次派使者劝马希萼、马希广停止争斗',29,'楚静江节度使马希瞻','屡遣使谏止，不从。',[('马希瞻','多次派使者劝两位兄长停止争斗'),('马希萼','未接受停止争斗的劝告'),('马希广','未接受停止争斗的劝告')],year=None,when='马希萼、马希广争斗期间、949年十月马希瞻死前，具体起止未载',place='楚国，具体派使往来地点未载',note='屡遣是反复劝阻，不按一次发使推为两人已和平；兄表明马希萼、马希广都年长于马希瞻。')
relationship('马希萼','马希瞻','兄长',29,'以兄希萼、希广交争，','兄同时修饰希萼和希广；沿用已知亲属主体，不从官职推排行。')
relationship('马希广','马希瞻','兄长',29,'以兄希萼、希广交争，','马希广是马希瞻的兄长，不把与马希萼的长幼方向倒置。')
add('ma_xizhan_dies','马希瞻背部生疽后去世',29,'知终覆族，',None,[('马希瞻','背部生疽后去世')],when='949年十月丁亥',place='楚国，具体死亡地点未载',note='知终覆族为史书对其忧虑的叙述，不把忧虑直接当成经医学证实的疽病原因。')
sup('ma_xizhan_dies',29,dec,'湖南奏，靜江軍節度使馬希贍以今年十月十八日卒。','《旧五代史》十二月记湖南奏报，马希贍于当年十月十八日去世。','以同一静江节度使、楚国及死亡时间对应马希瞻，瞻与贍异字并列；十月十八日是死亡日，十二月是奏报月。',relation='adds',field='time_original')
claim('person',people['马希瞻'],'death_year','马希瞻于949年十月去世。',29,span(29,'知终覆族，'),'死亡据主书丁亥及旧史奏报的十月十八日相互参照；原日保留，不自行换算公历或覆盖旧人物档案。')
add('khitan_raids_hebei','辽军侵入河北杀掠，各地守将闭城自守',30,'契丹寇河北，','帝忧之。',[('刘承祐','因辽军游骑到贝州和邺都北境而忧虑')],when='949年十月条下，具体出兵日未载',place='河北、贝州及邺都北境',note='闭城自守不等于所有州城都已被攻陷；没有主将姓名，不指定耶律阮亲自率军。')
sup('khitan_raids_hebei',30,liao,'冬十月，遣諸將率兵攻下貝州高老鎮，徇地鄴都、南宮、堂陽，','《辽史》天禄三年十月记诸将攻下贝州高老镇，并在邺都、南宫、堂阳一带进军。','已回查天禄三年949年标题；天禄四年自将南伐属950年，不混作本次战事。',relation='adds')
sup('khitan_raids_hebei',30,octo,'契丹陷貝州高老鎮，南至鄴都北境，又西北至南宮、堂陽，殺掠吏民。','《旧五代史》也记辽军攻下高老镇，杀掠邺都北境及南宫、堂阳一带吏民。','与主书记河北杀掠同一时段，不能推成辽军已攻下邺都城。',relation='adds')
event('shi_wanshan_killed','《辽史》记辽军在河北战事中杀死深州刺史史万山',30,'殺深州刺史史萬山，',[('史万山','在辽军进攻河北时被杀')],when='949年十月（辽天禄三年），具体日未载',place='深州相关战事，具体被杀地点未载',source=liao,note='这是辽史独立补记的人物与处置，深州刺史为官职，不据此认定深州城已陷或被杀时正在深州城内。')
add('han_sends_guo_wang_north','刘承祐派郭威督军御辽，王峻监军',30,'己丑，',None,[('刘承祐','派郭威督诸将御辽，王峻监军'),('郭威','以枢密使身份督诸将御辽'),('王峻','以宣徽使身份监军')],when='949年十月己丑',place='后汉朝廷至河北行营',note='此为派遣，不强定同日已到邺都或邢州。')
sup('han_sends_guo_wang_north',30,octo,'遣樞密使郭威率師巡邊，仍令宣徽使王峻參預軍事。','《旧五代史》也记派郭威率军巡边，王峻参与军务。','主书监军与旧史参预军务称谓分别保留，不擅定独立指挥权。')
add('khitan_withdraws_after_crossing','辽军得知后汉军渡河后撤去',31,'十一月，','乃引去。',[],when='949年十一月，具体撤军日未载',place='河北',note='史书明记得知渡河后撤军，未记这时发生双方大战，不写成后汉已在决战中击败辽军。')
add('guo_wei_arrives_yedu','郭威军到达邺都，命王峻分兵前往镇州、定州',31,'辛亥，','趣镇、定。',[('郭威','率军到邺都，命王峻分兵赴镇州、定州'),('王峻','奉命分兵前往镇州、定州')],when='949年十一月辛亥',place='邺都至镇州、定州',note='镇、定为州名；命令前往不写成两州已被收复或辽军已在当地被歼。')
add('guo_wei_arrives_xingzhou','郭威到达邢州',31,'戊午，',None,[('郭威','到达邢州')],when='949年十一月戊午',place='邢州',note='仅记录到达；旧史周太祖纪编在十月十九日，月份差异并列。')
sup('guo_wei_arrives_xingzhou',31,guo,'其月十九日，帝至邢州，遣王峻前軍趨鎮、定。','《旧五代史》周太祖纪在十月段中记十九日郭威到邢州，并派王峻前军赴镇州、定州。','《通鉴》记十一月戊午到邢州、先在邺都下令分军，两书日期和下令位置详略有别，不静默统一。',relation='conflicts',field='time_original')
add('tang_attacks_zhengyang','南唐军渡过淮河，进攻正阳',32,'唐兵渡淮，','攻正阳。',[],when='949年十一月条下，具体渡河及进攻日未载',place='淮河、正阳',note='未列南唐主将与出兵数量，不因李璟在位就写成他亲自领兵。')
add('bai_fujin_defeats_tang','颍州将白福进在正阳击败南唐军',32,'十二月，',None,[('白福进','以颍州将领身份击败攻正阳的南唐军')],when='949年十二月，具体交战日未载',place='正阳',note='主书未列战果人数，不把击败写成全歼或攻占南唐州城。')
sup('bai_fujin_defeats_tang',32,dec,'潁州奏，破淮賊於正陽。','《旧五代史》十二月也记颍州奏报在正阳击败南唐军。','旧史本句未列白福进姓名，支持战场与胜负，不单凭匿名奏报独立确认将领身份。')
reviews={27:'二十项加官分别保留姓名、原官号、守兼与纪日。刘崇为刘知远弟，非萧县同名人；刘赟与楚王赟分开，以新史亲支补证父子、养父关系。主书壬申与旧史十月初一并列；乙己底本字不静默改。匿名议者评价与授官事实分开。',28:'垦荒免税不扩大成全部税赋永久免除；遗丁解释为漏登记壮丁，不猜请求人身份或假设所有户籍已核清，国人皆悦为史书评价。',29:'反复劝和起止未知，背疽死亡不造现代病因。瞻/贍字形按同一静江节度使及时间对应；旧史十二月奏报十月十八日，不混成十二月死亡。两位兄长的方向沿用或新增具体关系。',30:'辽军杀掠、守城与后汉派将分开；高老镇与邺都北境不等于邺都城被占。辽史只用天禄三年949年段，避开四年950年的皇帝亲征。史万山死亡地点未载，不凭刺史职务推城陷。',31:'得知渡河后退兵不是已发生决战。邺都到达、命分军、邢州到达分别记录；旧史十月十九日与主书十一月戊午并列，未擅合月份。',32:'南唐渡淮攻正阳与后汉十二月击败分开；白福进只据具名主书记身份，旧史匿名奏报不当独立姓名确证。不新造主将、战果人数或现代坐标。'}
assert not (P/'publication.json').exists()
for n in range(27,33):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=288,year=949,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(27,33)],next_paragraph=Q[33]['id'],next_volume=288,next_year=949,supplements=supplements,excluded_non_body=[],coverage='卷288原105—110行连续六段，949年累计首32/37段，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(27,33)],source_issues_review='旧史孙方简、刘赟加官十月初一与主书壬申不同，郭威邢州到达十月十九日与主书十一月戊午不同，保留异说。马希瞻/贍按官职及死亡时间对应；乙己为底本原字。辽史三年、四年年界已回查，本批仅录949年河北侵袭。吴越政策及白福进身份未检到对应二十四史具名补证，未把后年、相似姓名记录强行合并。纸本与地理待核。',plain_language_review='首次逐条检查全部展示字段与事实解释，明确姓名主语及加官各主体，区分担忧、评价、命令和实际到达及战果。繁简转换限展示，摘录保持底本。年份或日期不明保留说明，不虚构病因、兵力、战果、税率或死亡地点；复用人物关系与旧档案不改写。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
