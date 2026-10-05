# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 287, year 947 paragraphs 1–8."""
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
COMMIT='52874e45c7cb04fd601bd528e1c87122d4b092b3'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-099-heyang-april']:
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
main_sources = ['tongjian-287-947-may-opening','tongjian-287-947-southern-march']
B = {'format_version': 1, 'batch_key': 'zztj-v287-y0947-p001-p008',
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
        citation = f'卷287·天福十二年（947年五月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_287_0947_01_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'刘知远','兀欲':'耶律阮','延寿':'赵延寿','崇':'刘崇（刘知远弟）','希范':'马希范','希广':'马希广','希萼':'马希萼'})
NEW_ALIASES={'李骧':['李驤'],'蔚进':['蔚進'],'马希萼':['馬希萼'],'袁友恭':[],'刘彦瑫':['劉彥瑫'],'杨涤':['楊滌']}
NEW_DESCRIPTIONS={
'李骧':'真定人，任河东幕僚。947年五月甲午任太原少尹，协助北京留守。生卒年未载。',
'蔚进':'太原人，原任牙将。947年五月甲午任马步指挥使，协助北京留守。生卒年未载。',
'马希萼':'马希范的弟弟、马希广的兄长。947年马希范死时，任武平节度使、知永州事，部分将领主张拥立他，但最终马希广继位。生卒年尚未录入。',
'袁友恭':'楚国都押牙。947年马希范去世后的继承争议中，与张少敌主张立较年长的马希萼。生卒年未载。',
'刘彦瑫':'楚国长直都指挥使。947年与李弘皋等主张拥立马希广，五月乙未称马希范遗命，拥立马希广。生卒年未载。',
'杨涤':'楚国小门使。947年马希范死后，与刘彦瑫等主张拥立马希广。生卒年未载。'}
j='jiuwudaishi-100-may-march';old='jiuwudaishi-099-heyang-april';ls='liaoshi-005-shizong-accession';chu='xinwudaishi-066-ma-xiguang-succession';t='947年五月，具体日未载'
add('ruan_invites_zhao_ministers','耶律阮召赵延寿、张砺、和凝、李崧、冯道到住处饮酒',1,'五月，乙酉塑，','于所馆饮酒。',[('兀欲','召赵延寿及晋朝官员饮酒'),('延寿','受邀饮酒'),('张砺','受邀饮酒'),('和凝','受邀饮酒'),('李崧','受邀饮酒'),('冯道','受邀饮酒')],when='947年五月乙酉（主书底本塑，《旧五代史》作朔）',place='恒州，耶律阮所馆',note='底本塑字保留在引用；旧史同日作朔。所馆为住处，不推现代精确建筑坐标。')
add('ruan_lures_imprisons_zhao','耶律阮以妻子想见赵延寿为由引他入内，随后称赵谋反、已将其拘押',1,'兀欲妻素','适已锁之矣。”',[('兀欲','引赵延寿入内，随后宣布已拘押'),('延寿','相信见妹的说法，入内后被拘押')],when='947年五月乙酉',place='恒州，耶律阮住处',note='妻以兄事延寿是按兄长礼待，不证明两人血缘兄妹；燕王谋反为耶律阮的指控，不当已证实谋反事实。')
sup('ruan_lures_imprisons_zhao',1,j,'天福十二年夏五月乙酉朔，契丹所署大丞相、政事令、東京留守、燕王趙延壽為永康烏裕所縶','《旧五代史》同记五月乙酉朔赵延寿被永康王拘押。','烏裕与主书兀欲沿已有耶律阮主体；补书朔与主书塑为字形差异，引用分别保留。')
add('ruan_disputes_zhao_authority','耶律阮声称曾获耶律德光许掌南朝军国，否认另有临终遗诏给赵延寿',1,'又曰：“先帝在汴时，','岂理邪！”',[('兀欲','以先前授权与无别遗诏的说法质疑赵延寿'),('延寿','被质疑擅掌南朝军国事务')],when='947年五月乙酉',place='恒州',note='一筹、许掌事务及别无遗诏是耶律阮的声称，不独立证明真实遗命内容；与前卷赵自称受诏并列。')
add('ruan_spares_zhao_supporters','耶律阮下令释放赵延寿亲党，不再追问',1,'下令：','皆释不问。”',[('兀欲','下令不追问赵延寿亲党')],when='947年五月乙酉',place='恒州',note='亲党未名，不自动释放全部被俘晋官或创建未载同盟关系。')
add('ruan_receives_homage_at_daixian','耶律阮隔一日到待贤馆受蕃汉官员拜贺，并称若赵延寿行此礼将围之',1,'间一日，',None,[('兀欲','到待贤馆受贺，并以围攻假设威吓'),('张砺','听耶律阮谈赵若行礼将被围的假设')],when='947年五月乙酉后间一日，具体干支未载',place='恒州待贤馆',note='燕王果于此礼上、铁骑围之是未发生的假设，不新建包围赵仪式事件；间一日不自行换算干支或公历。')
add('ruan_proclaims_accession_edict','数日后耶律阮召集蕃汉官员，宣布遗制称永康王应在中京即位',2,'后数日，','可于中京即皇帝位。”',[('兀欲','集臣宣告称自己可即位的遗制')],when='947年五月受贺后数日，具体日未载',place='恒州府署',note='遗制中的太后钟爱、群情允归是文书声称，不证明太后确实同意；主书此处是宣制，不把引文可即位写成当天已行全部仪式。')
sup('ruan_proclaims_accession_edict',2,j,'既而烏裕召蕃漢臣僚於鎮州牙署，矯其主遣詔，命烏裕嗣位','《旧五代史》记耶律阮召臣，称其矫造遗诏命自己继位。','主書叙宣遗制，旧史明确判断为矫诏，保留真实性差异，不宣布已经找到真正原诏。',relation='conflicts')
sup('ruan_proclaims_accession_edict',2,ls,'夏四月丁丑，太宗崩於欒城。戊寅，梓宮次鎮陽，即皇帝位於柩前。','《辽史》记耶律阮四月戊寅在镇阳柩前即位，与主書五月下宣制、受贺叙事时间不同。','各书仪式和日期层次分别保留，不把不同礼仪一律视为同一日或第二次继位。',relation='conflicts')
add('ruan_begins_mourning_then_music','宣布遗制后开始举哀服丧，随后改吉服见群臣，内廷歌吹不绝',2,'于是始举哀',None,[('兀欲','先举哀成服，后改吉服见群臣，内廷恢复歌乐')],when='947年五月宣制后，具体间隔未载',place='恒州府署与内廷',note='后文不复行丧与歌吹为史书记述，不推实际服丧天数或疾病心理原因。')
sup('ruan_begins_mourning_then_music',2,j,'於是發哀成服。','《旧五代史》同记宣诏后发哀成服。','补书只支持本句举哀，不能凭此独立验证主書后文改吉服的全部细节。')
add('wang_yan_jianxiong_appointment','刘知远任命王晏为建雄节度使',3,'辛巳，',None,[('帝','任命王晏为建雄节度使'),('王晏','从原防御使职获任建雄节度使')],when='947年辛巳；《旧五代史》置四月条下',place='晋州建雄军',note='本段虽置五月开篇后，却未另明示月；补書在四月末记辛巳，月份分別保留。主书绛州防御使与旧史晋州官衔写法不同。')
sup('wang_yan_jianxiong_appointment',3,old,'以陜府馬步軍副都指揮使兼絳州防禦使王晏為晉州節度使','《旧五代史》四月辛巳条记王晏从陕府马步军副都指挥使兼绛州防御使任晋州节度使。','补书职衔补明军号与州名，不把本段重置到确定五月辛巳。',relation='adds')
add('han_generals_propose_hebei_first','刘知远召群臣议进取，将领建议出井陉攻镇魏，先定河北',4,'帝集群臣','则河南拱手自服。',[('帝','召集群臣讨论进军方向')],when=t,place='后汉朝廷；井陉、镇州、魏州、河北（拟进军方向）',note='诸将未名，河南拱手自服是方案预期，不当已经发生归附。')
add('guo_rejects_hebei_shangdang_routes','郭威反对先攻河北及经石会上党，建议取道陕晋，刘知远赞同',4,'帝欲自石会','卿言是也。”',[('帝','原拟石会经上党，听取郭威后赞同改道'),('郭威','分析兵少路迂和粮饷风险，建议取道陕晋')],when=t,place='后汉朝廷；河北、上党、陕州、晋州（拟路线）',note='万无一失、不出两旬定洛汴是郭威预测，不记为已完成战果；实际出兵路线另见丙申。')
add('su_proposes_tianjing_mengjin','苏逢吉等以史弘肇已屯上党，建议由天井到孟津',4,'苏逢吉等曰：','为便。”',[('苏逢吉','以史弘肇已在上党为依据提出路线建议')],when=t,place='后汉朝廷；天井、孟津（拟路线）',note='等未名，不把全部臣僚自动建为建议者；方案与最终采用路线分开。')
add('astronomers_route_advice_accepted','司天以太岁在午为由建议经晋绛到陕，刘知远采纳',4,'司天奏：','帝从之。',[('帝','采纳司天所提晋绛抵陕路线')],when=t,place='后汉朝廷；晋州、绛州、陕州（拟路线）',note='占星理由是当时奏说，不视为路线安全的科学证明；司天官未名，不猜具体人物。')
add('liu_announces_may_twelfth_departure','刘知远下诏定五月十二日离北京，并通知诸道',4,'辛卯，',None,[('帝','下诏宣布五月十二日发北京')],when='947年五月辛卯（下诏日）；拟五月十二日出发',place='太原北京至诸道',note='诏令日期与预定出发日分开，实际出发见丙申段。')
sup('liu_announces_may_twelfth_departure',4,j,'辛卯，詔取五月十二日車駕南幸。','《旧五代史》同记辛卯诏定五月十二日南幸。','主書北京出发与补書南幸为同一计划，不建重复启程。')
add('liu_chong_beijing_regent','刘知远任命刘崇为北京留守',5,'甲午，','为北京留守，',[('帝','任命弟弟留守北京太原'),('崇','从太原尹任北京留守')],when='947年五月甲午',place='太原北京',note='复用刘知远弟、后名旻的刘崇，不与萧县同名人合并。')
sup('liu_chong_beijing_regent',5,j,'甲午，以判太原府事劉崇為北京留守','《旧五代史》同日记判太原府事刘崇任北京留守。','与主書太原尹原职描述相接，复用同一次留守任命。')
add('li_cungui_deputy_regent','刘知远任命李存瑰为北京副留守',5,'以赵州','为副留守，',[('帝','任命李存瑰为副留守'),('李存瑰','从赵州刺史任北京副留守')],when='947年五月甲午',place='太原北京',note='存瑰与此前主体李瓌、李瑰别名沿既有同人记录；庄宗从弟亲属据本段，不补具体父亲。')
relationship('李存勖','李存瑰','从兄',5,span(5,'以赵州',None),'庄宗指李存勖，存瑰为其从弟；方向表示李存勖是李存瑰的从兄，不补未载父系连接。')
add('li_xiang_taiyuan_deputy','刘知远任命河东幕僚李骧为太原少尹',5,'河东幕僚','为少尹，',[('帝','任命李骧为少尹'),('李骧','从河东幕僚获任少尹，协助留守')],when='947年五月甲午',place='太原北京',note='真定为籍贯，不是此次任职地点。')
add('wei_jin_commands_beijing_troops','刘知远任命蔚进为马步指挥使，协助留守',5,'牙将太原', '以佐之。',[('帝','任命蔚进掌北京马步军'),('蔚进','从牙将任马步指挥使，协助留守')],when='947年五月甲午',place='太原北京',note='太原既是本段蔚进籍贯也是留守地点，未另补具体军营。')
add('liu_xi_leaves_luoyang_again','刘晞再次弃洛阳，逃往大梁',6,'是日，',None,[('刘晞','再次离洛阳逃往大梁')],when='947年五月甲午',place='洛阳至大梁',note='前卷先逃许州、后获护送回洛阳，本段再逃大梁，复用人物但不合并为同一次撤离。')
add('ma_xifan_entrusts_xiguang_government','马希范喜爱弟弟马希广，令其处理内外诸司事务',7,'武安节度副使','使判内外诸司事。',[('希范','喜爱同母弟，令其处理诸司事务'),('希广','任武安节度副使等职，处理内外诸司事务')],when='947年马希范去世之前，具体授理事年日未载',year=None,place='楚国军府',note='本句为生前职掌背景，未标任命年，不把此前理事始日强定947年五月。性谨顺、爱之为史家描述。')
relationship('马希范','马希广','兄长',7,span(7,'武安节度副使','使判内外诸司事。'),'同母弟明确兄弟长幼，复用既有兄长关系；不由此猜母亲名字。')
add('ma_xifan_dies','楚王马希范去世，将佐商议继承人',7,'壬辰夜，','将佐议所立。',[('希范','去世，引发将佐继承议论')],when='947年五月壬辰夜',place='楚国军府',note='楚文昭王为史书称谓，死亡与后续选立分记。')
add('zhang_yuan_support_ma_xie','张少敌、袁友恭以马希萼较年长为由，主张立他',7,'都指挥所张少敌，','请立之。',[('张少敌','主张立年长的马希萼'),('袁友恭','主张立年长的马希萼'),('希萼','以武平节度使、知永州事身份被建议继位')],when='947年五月壬辰夜之后、乙未拥立之前',place='楚国军府；永州（马希萼任职地）',note='都指挥所为底本原字，未据疑字新建机构；请立是方案，未写成马希萼已经继位。')
add('liu_and_others_support_xiguang','刘彦瑫、李弘皋、邓懿文、杨涤主张立马希广',7,'长直都指挥使','皆欲立希广。',[('刘彦瑫','以长直都指挥使身份主张立马希广'),('李弘皋','以天策府学士身份主张立马希广'),('邓懿文','主张立马希广'),('杨涤','以小门使身份主张立马希广'),('希广','被部分将佐主张为继承人')],when='947年五月壬辰夜之后、乙未拥立之前',place='楚国军府',note='欲立是主张，实际拥立另录乙未；同场立场相同不额外建立终身同盟关系。')
add('zhang_warns_succession_risk','张少敌警告若立马希广，须妥善处理年长刚强的马希萼，否则社稷有危',7,'张少敌曰：','彦瑫等不从。',[('张少敌','警告继承争议风险，要求考虑应对马希萼'),('刘彦瑫','未接受张少敌警告')],when='947年五月继承讨论时，具体日未载',place='楚国军府',note='不为都尉之下是张的预判，不把未来冲突提前记为已发生。')
add('tuoba_proposes_defer_older_brother','拓跋恒建议遣使礼让年长的马希萼，刘彦瑫等认为军政已在手而拒绝',7,'天策府学士拓跋恒曰：','异日吾辈安所自容乎！”',[('拓跋恒','建议以礼先让年长者'),('刘彦瑫','以军政在手与日后处境为由反对让位')],when='947年五月继承讨论时，具体日未载',place='楚国军府',note='三十五郎指马希广、三十郎指马希萼；天与不取是辩论用语，不是天命已获证明。')
sup('tuoba_proposes_defer_older_brother',7,chu,'希範卒，常數勸希廣以位奉其兄希萼，希廣不從。','《新五代史》记马希范死后，拓拔常多次劝马希广奉位给兄长马希萼，未被接受。','新史拓拔常与主書拓跋恒同职同事，姓名异写与劝说次数分别保留，不猜避讳原因。',relation='adds')
relationship('马希萼','马希广','兄长',7,'希範卒，常數勸希廣以位奉其兄希萼','新史明确希萼是希广的兄长；主书继承讨论也区分较年长者，不凭共父推全部兄弟长幼。',source=chu)
add('ma_xiguang_hesitates_then_enthroned','马希广不能自决，刘彦瑫等称马希范遗命，于乙未拥立他',7,'希广懦弱，','共立之。',[('希广','未能自决，随后被拥立'),('刘彦瑫','与支持者称遗命并拥立马希广')],when='947年五月乙未（拥立），前期犹豫具体日未载',place='楚国军府',note='懦弱为史家评价，称遗命是将佐说法，不认定真实遗命已存。')
add('zhang_tuoba_withdraw_from_office','张少敌叹祸始于此，与拓跋恒都称病不出',7,'张少敌退',None,[('张少敌','对拥立结果忧虑，称病不出'),('拓跋恒','称病不出')],when='947年五月乙未拥立后，具体日未载',place='楚国军府',note='称疾为提出有病，不据此作真实医学诊断；祸始此为张的预判。')
add('liu_leaves_taiyuan_south','刘知远从太原出发，经阴地关进入晋绛',8,'丙申，',None,[('帝','实际从太原启程，经阴地关南下')],when='947年五月丙申',place='太原、阴地关、晋州、绛州',note='实际启程与辛卯诏令分开；原地名保留，不推准确现代道路坐标。')
sup('liu_leaves_taiyuan_south',8,j,'丙申，帝發河東，取陰地關路幸東京。','《旧五代史》同日记刘知远从河东启程，取阴地关路往东京。','东京在此为计划目的地，不写成丙申已经抵达。')
reviews={1:'塑字引用保留，旧史朔独立校读；妻以兄事不推血亲；诱入拘押、谋反指控、授权争论、释亲党和受贺假设分别录入。',2:'宣遗制与旧史矫诏判断并列，辽四月柩前即位与主五月仪式分层；钟爱允归不当已证事实，举哀后改吉服分记。',3:'辛巳原月未明，旧四月末条定位保留，不把卷开五月直接当该条发生月。',4:'各路线建议、预判、占星奏说与最终诏定十二日分别录入，不把预计两旬定洛汴当实际成果。',5:'刘崇复用后名旻主体，李存瑰别名沿既有实体；原籍与职地分清，庄宗从弟关系方向明确。',6:'是日承甲午，刘晞再次弃城区别前卷逃许州、获护送回城。',7:'生前职掌追叙未知年，同母弟复用关系；楚继承双方建议、警告、称遗命拥立与称疾不出分录；拓拔常恒异写保留。',8:'丙申实际出发与十二日计划分记，旧书东京为目的地不认当日已至。'}
assert not (P/'publication.json').exists()
for n in range(1,9):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=287,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(1,9)],next_paragraph=Q[9]['id'],next_volume=287,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷287原6—13行连续八段，本卷累计8/75；947年跨卷未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,9)],source_issues_review='塑朔、辛巳月份定位、契丹遗制真实性和继位仪式日期分别保留；楚继承者与拓跋姓名异说不消除；仅已知关系方向，不补母系或父系连接。',plain_language_review='首次逐项核对全部新增人物、事件、角色、关系、时间地点、出处和事实说明，明确指控、自称、预判、计划及实际行动；关系事实写双方姓名和方向，避免关系对象等内部表达，原文保持底本字形。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
