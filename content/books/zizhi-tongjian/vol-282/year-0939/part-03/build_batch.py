# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 282, year 939 paragraphs 21–27."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,42))
specs=[(d.name,d,'c95625692d30c3a868c0e61b35b6fb0ce80c9c44','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-282-939-spring-summer','jiuwudaishi-088-wang-tingyin']:
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
main_sources = ['tongjian-282-939-spring-summer','tongjian-282-939-intercalary']
B = {'format_version': 1, 'batch_key': 'zztj-v282-y0939-p021-p027',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-078-july':'卷78·晋高祖纪·天福四年七月','jiuwudaishi-078-intercalary-july':'卷78·晋高祖纪·天福四年闰七月','xinwudaishi-051-an-chongrong':'卷51·安重荣传'}
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
lines = (ROOT / 'resources/derived/tongjian/282.txt').read_text().splitlines()
for n in range(21, 28):
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
    labels={'jiuwudaishi-078-july':'卷78·晋高祖纪·天福四年七月','jiuwudaishi-078-intercalary-july':'卷78·晋高祖纪·天福四年闰七月','xinwudaishi-051-an-chongrong':'卷51·安重荣传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '七月条下' if n<=25 else '闰七月条下'
        citation = f'卷282·后晋天福四年（939；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_282_0939_03_{len(B["claims"])+1:04d}'
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=939, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when=('939年七月条下，具体日期未载' if n<=25 else '939年义武缺帅后、王廷胤调任前，具体月日未载')
    key = 'event_zztj_282_0939_' + code
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
        edge = 'participation_zztj_282_0939_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_282_0939_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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




ALIASES.update({'王威':'王威（王处直之子）'})
july='jiuwudaishi-078-july';inter='jiuwudaishi-078-intercalary-july';an='xinwudaishi-051-an-chongrong';wang='jiuwudaishi-088-wang-tingyin'
add('july_eclipse','七月初一发生日食',21,'秋，',None,[],when='939年七月庚子朔',description='《资治通鉴》记，七月初一发生日食。',note='庚子朔是原纪年中的月初一；不补食分、观测地或现代日期。')
sup('july_eclipse',21,july,'秋七月庚子朔，日有食之。','《旧五代史》同样记七月庚子朔发生日食。','两书纪日相合；没有另建同一天的第二次日食。')
add('an_soldier_background','史书追述安重荣出身军伍，并批评他的作风',22,'成德节度使','恃勇骄暴，',[('安重荣','被史书记为出身军伍、恃勇骄暴的成德节度使')],year=None,when='安重荣此前的经历与作风概述，具体日期未载',description='《资治通鉴》记，成德节度使安重荣出身军伍，性情粗率，并用恃勇骄暴评价他的作风。',note='出身与性格概述不是939年发生的单次行动；评价明确归史书，不作为无来源判断。')
sup('an_soldier_background',22,an,'重榮起於軍卒，暴至富貴，','《新五代史》也记安重荣出身军卒，迅速取得富贵。','这是经历概述，不补具体起家年或首次晋升日期。')
add('an_power_speech','安重荣声称兵强马壮就能成为天子',22,'每谓人曰：','兵强马壮则为之耳。”',[('安重荣','多次声称军力强盛就能成为天子')],year=None,when='安重荣此前多次言论，具体日期未载',note='这是安重荣的政治主张，不意味着他已经称帝或史书认可其主张。')
sup('an_power_speech',22,an,'嘗謂人曰：「天子寧有種邪？兵強馬壯者為之爾！」雖懷異志，而未有以發也。','《新五代史》也记安重荣发表类似言论，并称他虽有异志，当时尚未发动。','两书记述相近；未把本段备马和不满提前录为公开反叛。')
add('an_shoots_dragon','安重荣射中幡竿龙首，自认为有天命',22,'府廨有','以是益自负。',[('安重荣','射中幡竿上的龙首，并把结果解释为自己有天命')],year=None,when='安重荣此前射箭的追述，具体日期未载',description='安重荣官署有高数十尺的幡竿。他声称如果能射中竿上的龙首，就证明自己有天命；一箭射中后，他更加自负。',note='天命是安重荣对射箭结果的解释；不据此认可超自然征兆。')
add('shi_warns_an_replacement','石敬瑭曾告诫安重荣，秘琼若拒绝交接，不要武力夺镇',22,'帝之遣','恐为患滋深。”',[('帝','告诫安重荣不要以武力强夺秘琼所据军镇'),('安重荣','受命接替秘琼时得到皇帝告诫'),('秘琼','是交接告诫所涉及的原守将')],year=None,when='安重荣接替秘琼之前的追述，非939年新任命',description='石敬瑭派安重荣接替秘琼时曾告诫：如果秘琼不肯交接，就另给安重荣一个军镇，不要武力夺取，以免事态扩大。',note='接任与到镇已在937年批次记录；本条只新增当时的告诫，不重复建立任命或战斗。')
add('an_calls_shi_timidity','安重荣把石敬瑭的交接告诫视为怯懦',22,'重荣由是','士马之众乎！”',[('安重荣','认为石敬瑭惧怕秘琼，并以自身地位和兵力自负'),('帝','被安重荣评价为怯懦')],year=None,when='安重荣听到交接告诫后的言论，具体日期未载',description='安重荣因此认为石敬瑭怯懦，并声称：皇帝连秘琼都畏惧，更何况拥有将相地位和众多兵马的自己。',note='怯懦属于安重荣的评价；没有记成皇帝实际害怕安重荣的独立事实。')
add('an_collects_outlaws_horses','安重荣因奏请受限制而不满，招集亡命者并购买战马',22,'每所奏请','有飞扬之志。',[('安重荣','因奏请受到执政者限制而不满，招集亡命者、购买战马')],year=None,when='七月调任皇甫遇之前的持续动向，起止日期未载',description='《资治通鉴》记，安重荣的奏请常超过分限，受到执政者审核和限制。他心怀不满，招集亡命者、购买战马，并生出不安于现状的野心。',note='前因与筹备按史书表述；没有把意图和备马写成已经发动叛乱，也不补具体兵马数量。')
add('huangfu_moves_zhaoyi','石敬瑭将安重荣的姻亲皇甫遇调任昭义节度使',22,'帝知之，',None,[('帝','得知安重荣的动向后调任皇甫遇'),('皇甫遇','由义武节度使调任昭义节度使'),('安重荣','其姻亲皇甫遇被皇帝调离义武')],when='939年七月甲辰',place='义武、昭义',description='石敬瑭得知安重荣的动向。义武节度使皇甫遇与安重荣是姻亲，皇帝在甲辰将皇甫遇调任昭义节度使。',note='原文前后相连，保留政治背景；姻家未明具体婚配双方，不推父女、岳父或连襟。')
relationship('皇甫遇','安重荣','姻亲',22,'义武节度使皇甫遇与重荣姻家，','皇甫遇与安重荣存在婚姻亲属关联，具体婚配双方未载；姻亲按对称关系保留。')
sup('huangfu_moves_zhaoyi',22,july,'甲辰，以定州節度使皇甫遇為潞州節度使、檢校太尉，','《旧五代史》也记七月甲辰将皇甫遇从定州调到潞州，并加检校太尉。','与《资治通鉴》的义武、昭义调任相互补证；州名和军镇名分别保留，没有补现代坐标。')
add('min_north_palace_fire','闽国北宫起火，宫殿几乎全部烧毁',23,'乙巳，',None,[],when='939年七月乙巳',place='闽国北宫',note='本段未载纵火人或火灾原因；后文怀疑纵火属于猜疑，不能倒填为本条已经查实。')
add('xue_presents_edicts','薛融等呈上整理的编敕，朝廷颁行',24,'戊申，',None,[('薛融','与其他官员呈上整理的编敕')],when='939年七月戊申',description='薛融等呈上整理完成的编敕，朝廷随后颁行。',note='等表示还有其他参与者，但本句未列姓名；不自行补出共同编订者。')
sup('xue_presents_edicts',24,july,'戊申，御史中丞薛融等上詳定編敕三百六十八道，分為三十一卷。','《旧五代史》补记薛融当时为御史中丞，编敕共368道、分为31卷。','数量与官职来自独立出处；没有编造编敕条文或把31卷当368卷。',relation='adds')
add('shi_bans_private_coins','石敬瑭禁止私人铸钱，改由官府专铸',25,'丙辰，',None,[('帝','下诏禁止私人铸钱，改由官府专铸')],when='939年七月丙辰；《旧五代史》另记七月戊申',description='石敬瑭下诏称，此前允许公私铸钱，但私铸钱多掺铅锡，钱体小、薄、残缺，因此禁止私人铸钱，改由官府专铸。《资治通鉴》记诏令在七月丙辰，《旧五代史》记在戊申，两书纪日不同。',note='保留938年允许铸钱之后的政策变化，不覆盖前期事件。钱币缺陷是诏令所陈理由，不泛指全部私人钱币都相同。')
sup('shi_bans_private_coins',25,july,source_span(july,'戊申，御史中丞','今後私鑄錢下禁依舊法。」'),'《旧五代史》把禁私铸钱诏令列在七月戊申编敕呈上条的同日，与《资治通鉴》的丙辰有异。','是日承接七月戊申条；两书政策内容相近，纪日差异尚未裁定，不新增第二道确定不同的禁铸诏令。',relation='conflicts',field='time_original')
add('yang_accuses_sang','杨光远上疏指责桑维翰任免不公，并经营商铺与民争利',26,'西京留守','与民争利；',[('杨光远','以上疏方式指责桑维翰'),('桑维翰','被杨光远指责任免不公及经营商铺与民争利')],when='939年桑维翰外任之前，具体月日未载',description='西京留守杨光远上疏，指责中书侍郎、同平章事桑维翰任免官员不公，并在两都经营商铺、与民争利。',note='这是杨光远提出的指控；没有把上疏内容写成已经查明的罪名，也不补具体商铺地址和获利数字。')
add('sang_moves_zhangde','石敬瑭将桑维翰调任彰德节度使、兼侍中',26,'帝不得已，',None,[('帝','在杨光远指责后调任桑维翰'),('桑维翰','由中书侍郎、同平章事外任彰德节度使、兼侍中')],when='939年闰七月壬申',place='彰德',description='杨光远上疏后，石敬瑭在闰七月壬申将桑维翰调任彰德节度使、兼侍中。《资治通鉴》将皇帝的处置描述为不得已。',note='史书叙述处置背景，但没有记录正式审判或定罪；闰七月的月份由《旧五代史》明确补证。')
sup('sang_moves_zhangde',26,inter,'閏七月庚午朔，百官不入閣，雨沾服故也。壬申，以中書侍郎平章事、集賢殿大學士桑維翰為檢校司空、兼侍中、相州彰德軍節度使，','《旧五代史》明确记闰七月壬申任桑维翰为相州彰德军节度使，并加检校司空、兼侍中。','编年上下文明确闰七月，补官衔和州名；不把此前上疏当作已证实犯罪。',relation='adds')
add('wang_wei_refuge','史书追述王处直之子王威因王都夺权逃往契丹',27,'初，','亡在契丹，',[('王威','因王都夺权逃往契丹'),('王处直','其子王威因王都夺权出逃'),('王都','夺权事件促使王威出逃')],year=None,when='939年义武缺帅以前的追述，具体日期未载',place='契丹',description='《资治通鉴》追述，王处直的儿子王威为避王都夺权之祸，逃往契丹。《旧五代史》也称他为王威；是否与早期记载的王郁有关，尚待进一步校核。',note='两书本处均写威，未据家族或逃往契丹等近似经历自动合并王郁；没有把追述定为939年新出逃。')
sup('wang_wei_refuge',27,wang,'處直為養子都所篡，時威北走契丹，契丹納之。','《旧五代史》补记王都为王处直的养子，夺权后王威北逃，契丹接纳了他。','王都的既有身份继续复用；王威与王郁是否有关保持待考。',relation='adds')
relationship('王处直','王威','父亲',27,'义武节度使王处直子威，','王处直是本处所称王威的父亲；不据同父信息将王威自动并入王郁。')
add('khitan_requests_wang_wei','耶律德光要求后晋让王威承袭父亲旧地',27,'至是，','如我朝之法。”',[('契丹主','派使者要求王威按契丹制度承袭父亲旧地'),('王威','成为契丹要求承袭义武的候选人'),('帝','收到契丹关于义武节度使人选的要求')],place='义武、契丹',note='这是义武缺帅后的请求，不是已任命王威为节度使；使者姓名未载，不另建人物。')
sup('khitan_requests_wang_wei',27,wang,'至是契丹遣使諭高祖云：「欲使王威襲先人土地，如我蕃中之制。」','《旧五代史》同样记契丹要求王威承袭先人土地。','两书请求内容相合，均未写请求已获批准。')
add('shi_rejects_direct_succession','石敬瑭拒绝直接让王威承袭节度使，提出逐级任用',27,'帝辞以','渐加进用。”',[('帝','以中原逐级升迁制度为由拒绝直接承袭，提出逐级任用'),('王威','被提出先赴后晋、再逐级任用的方案')],description='石敬瑭以中原官员须从刺史、团练、防御使逐级升迁到节度使为由拒绝，提出先让王威来到后晋，再逐步任用。',note='此处是皇帝用来拒绝请求的制度理由和替代方案；没有证据表明王威已经赴晋或实际得到其中任一官职。')
add('khitan_retorts_promotion','耶律德光反问石敬瑭，从节度使到天子是否也按阶级升迁',27,'契丹主怒，','亦有阶级邪！”',[('契丹主','对拒绝不满，再派使者反问石敬瑭即位是否也按阶级升迁'),('帝','受到耶律德光使者转达的反问')],note='反问是外交施压言辞，不录为实际官员任免或二人当面会谈。')
add('shi_bribes_proposes_tingyin','石敬瑭厚赂契丹，并提议改由王廷胤接任义武',27,'帝恐其','以厌其意。',[('帝','担心争执扩大，厚赂契丹并提议王廷胤任义武节度使'),('王廷胤','被提议从彰德调任义武节度使')],place='义武、契丹',description='石敬瑭担心争执不断扩大，厚赂契丹，并提议让王处直兄长的孙子、彰德节度使王廷胤接任义武，以平息契丹的不满。',note='厚赂是实际行动，提议调任与下面独立出处确认的任命分开；没有补贿赂金额。')
relationship('王处直','王廷胤','叔祖父',27,'以处直兄孙彰德节度使廷胤为义武节度使','原文明确王廷胤是王处直兄长的孙子，因此王处直是王廷胤的叔祖父；按方向约定记录。')
add('khitan_anger_eases','厚赂及更换人选后，契丹的怒意有所缓和',27,'契丹怒稍解。',None,[('契丹主','在厚赂及更换人选的交涉后怒意有所缓和')],description='《资治通鉴》记，石敬瑭厚赂契丹并提出王廷胤人选后，契丹的怒意有所缓和。',note='稍解表示有所缓和，没有扩大成争议完全消除或正式签订新盟约。')
E['wang_tingyin_appointed_yiwu']=event('wang_tingyin_appointed_yiwu','王廷胤由彰德调任义武节度使',27,'以彰德軍節度使王庭允為義武軍節度使。',[('王廷胤','由彰德节度使调任义武节度使'),('帝','任命王廷胤为义武节度使')],source=inter,when='939年闰七月壬申',place='义武',description='《旧五代史》明确记，闰七月壬申，王廷胤由彰德节度使调任义武节度使。该书在此写作王庭允，沿用已有王廷胤主体。',note='《资治通鉴》此处只记皇帝提出人选；实际调任及日期由《旧五代史》本纪补证。王庭允沿既有传记核对的别名处理。')
sup('wang_tingyin_appointed_yiwu',27,wang,'契丹怒稍息，遂連升庭允，俾鎮中山，且欲塞其意也。','《旧五代史》王庭胤传也记，契丹怒意缓和后，朝廷让王廷胤镇守中山，以平息契丹的不满。','传记印证实际任官与交涉背景；具体日期仍引用同书本纪，不把传记当独立于本纪的完全确证。')
reviews={21:'七月庚子朔日食，两书纪日相合，未补观测地点和现代日期。',22:'军伍出身、性格评价、政治言论、射箭及接替秘琼时的告诫是背景追述，未强定939年。接任已有937年记录，本次仅增告诫与评价。安重荣招人备马不等于已反叛；皇甫遇甲辰调任和姻亲关系分别录，婚配双方未知。',23:'北宫火灾几乎烧尽宫殿，原因及纵火人本段未载。',24:'薛融等呈编敕、朝廷颁行；旧史补368道31卷与御史中丞职务，未补匿名共同编订者。',25:'禁私人铸钱、官府专铸；与938年允许铸钱的政策形成后续变化。通鉴丙辰、旧史戊申纪日不同，保留异说，不另造两道确定诏令。',26:'杨光远上疏指控与桑维翰外任分录，未把指控视作已定罪。旧史明确闰七月壬申并补检校司空及相州彰德官命。',27:'王威旧事、契丹请求、皇帝拒绝、替代方案、外交反问、厚赂与提议、怒意缓和分别录。旧史本纪确认王廷胤实际调任并给出日期；复用其已核别名。王威与王郁关系未明，保留待考，未自动合并。王处直父亲与叔祖父的方向有明确文本支持。'}
assert not (P/'publication.json').exists()
for n in range(21,28):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=282,year=939,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(21,28)],next_paragraph=Q[28]['id'],next_volume=282,next_year=939,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第21—27段，原26—32行；七月及闰七月政事，939年剩余14段待录。',source_issues_review='禁私铸钱诏令纪日丙辰与戊申有异；王威与王郁是否有关尚待核实。王廷胤别名王庭允沿已核传记复用。书内本纪与传记并读，不算完全独立书证；纸本及版本异文仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,28)],plain_language_review='首次逐条检查标题、介绍、正文、参与角色、关系、时间地点与事实说明；主语及动作明确，追述不强定年、请求不写成任命、指控不写成定罪、天命言论不写成事实；原文摘录保留底本字形。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
