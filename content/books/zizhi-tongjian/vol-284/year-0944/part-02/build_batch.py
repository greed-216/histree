# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 284, year 944 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,45))
COMMIT='33c4505fd076635fd33c0ce1412ecfa289823f13'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['jiuwudaishi-082-944-march','xinwudaishi-068-min-li-empress']:
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
main_sources = ['tongjian-284-944-march-april']
B = {'format_version': 1, 'batch_key': 'zztj-v284-y0944-p009-p016',
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
lines = (ROOT / 'resources/derived/tongjian/284.txt').read_text().splitlines()
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
    for a,b in [('旧纪','《旧五代史》本纪'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
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
        month = '三月条下及追述'
        citation = f'卷284·后晋天福九年、后称开运元年（944；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_284_0944_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=944, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='944年三月条下，具体日期未载'
    when=when.replace('主书','《资治通鉴》').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_284_0944_' + code
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
        edge = 'participation_zztj_284_0944_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_284_0944_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','汉主':'刘弘熙','契丹主':'耶律德光','闽主':'王延羲','曦':'王延羲','李后':'李氏（王延羲后）','尚贤妃':'尚氏（王延羲贤妃）','殷主':'王延政','弘昌':'刘弘昌','硃文进':'朱文进','延喜':'王延喜'})
NEW_ALIASES={'尹居璠':[],'魏从朗':['魏從朗'],'钱达':['錢達'],'吴成义':['吳成義'],'鲍思润':['鮑思潤'],'程文纬':['程文緯'],'许文稹':['許文稹','许文缜','許文縝'],'陈偓':['陳偓']}
NEW_DESCRIPTIONS={
'尹居璠':'后晋德州刺史。944年契丹北归期间，麻答攻陷德州，尹居璠被擒。《旧五代史》四月条载沧州奏报此事；被俘不记为死亡。生卒年未载。',
'魏从朗':'闽国控鹤指挥使，史书记为朱文进、连重遇的党人。王延羲游西园饮醉后将他杀死，具体年月未载。未将党人直接解释为永久盟友关系。',
'钱达':'闽国拱宸马步使。944年三月乙酉，受朱文进、连重遇指使，在王延羲探望李真的途中将其在马上杀死。生卒年未载。',
'吴成义':'殷国统军使。944年闽国政变后受王延政命率兵讨伐朱文进，未能攻克。后续福建战事尚随主书继续录入。生卒年未载。',
'鲍思润':'闽国枢密使。944年朱文进掌权后，被授予同平章事职衔。生卒年未载。',
'程文纬':'闽国左军使，944年朱文进掌权后任漳州刺史。《新五代史》相同政局的漳州守将写程贇，是否同人异名待核，未直接合并。生卒年未载。',
'许文稹':'同安人，汀州刺史。944年朱文进掌权后率郡投降朱文进。《新五代史》对应汀州守将作許文縝，保留姓名字形异文；该书后文投降王延政为另一阶段，不混为当前投降对象。生卒年未载。',
'陈偓':'南汉户部侍郎。944年三月条下被任命为同平章事。生卒年未载。'}
han='xinwudaishi-065-hongchang-death';minz='xinwudaishi-068-zhu-wenjin';mine='xinwudaishi-068-min-li-empress';old='jiuwudaishi-082-944-march';apr='jiuwudaishi-082-944-april';liao='liaoshi-004-944-march'
# 9: an order to visit a tomb, arrival at the palace, assassination; independent summer dating.
add('hongchang_tomb_order','刘弘熙命越王刘弘昌前往海曲拜谒烈宗陵',9,'汉主命','于海曲，',[('汉主','命越王刘弘昌拜谒烈宗陵'),('弘昌','受命前往海曲拜谒烈宗陵')],when='944年三月条下的记载，具体月日主书未列；新史记乾和二年夏',place='海曲烈宗陵',note='命前往不等于已经完成祭陵；新史称襄帝陵，分别保留原称。')
add('hongchang_arrives_changhua','刘弘昌到达昌华宫',9,'至昌华宫，','至昌华宫，',[('弘昌','到达昌华宫')],when='944年上述出行期间，确切日期未载',place='昌华宫',note='至宫明确，不据此补此前是否已经完成拜谒陵墓。')
add('hongchang_assassinated','刘弘熙派人在昌华宫杀死刘弘昌',9,'汉主命',None,[('汉主','派人杀死刘弘昌'),('弘昌','在昌华宫被杀')],when='944年，主书三月条下记述，新史记乾和二年夏',place='昌华宫',note='使盗为派人行刺，不把杀人者未具名强补某个宫廷官员；不因主书排列位置就断言发生于三月。')
sup('hongchang_assassinated',9,han,'二年夏，遣洪昌祠襄帝陵於海曲，至昌華宮，晟使盜刺殺之。','《新五代史》记乾和二年夏，刘晟派刘洪昌祭襄帝陵，至昌华宫时让人刺杀。','乾和二年对应944年；晟洪昌沿用已核刘弘熙刘弘昌主体。夏季纪时独立保留，烈宗与襄帝陵原称分开。',relation='adds',field='time_original')
claim('person',people['刘弘昌'],'death_year','刘弘昌于944年被刘弘熙派人杀于昌华宫；《新五代史》记于乾和二年夏。',9,'二年夏，遣洪昌祠襄帝陵於海曲，至昌華宮，晟使盜刺殺之。','既有主体不覆盖基线，独立增加死亡事实；不补确切日。',source=han,relation='adds')
sup('hongchang_assassinated',9,han,'而洪昌最賢，龑素所欲立者，晟尤忌之，故先及害。','《新五代史》解释刘晟尤其忌惮被刘龑考虑立为继承人的刘弘昌，因此先害他。','这是传记给出的原因和评价，作为该书说明保留，不写成已独立证实的唯一心理动机。',relation='adds')
# 10: actual withdrawal, plunder, a garrison and a captured official; date of report differs.
add('khitan_two_routes_home','耶律德光从澶州分两路北归，分别经过沧德、深冀',10,'契丹主自','而归。',[('契丹主','分军沿两条路线北归')],when='944年三月澶州交战之后，具体日期未载',place='澶州、沧州、德州、深州、冀州',note='实际北归与此前乙亥小校声称撤军的报告分别记，不把两个阶段强定同一天。')
add('khitan_plunders_northward','契丹北归途中焚烧抢掠，史书记破坏波及千里',10,'所过焚掠，','民物殆尽。',[],when='944年三月北归期间，具体日期未载',place='契丹北归沿途',note='方广千里为史书范围概述，不绘成精确边界，不据殆尽补绝对人口或财产总额。')
add('zhao_yanzhao_beizhou_regent','契丹留赵延照为贝州留后',10,'留赵延照','留后。',[('契丹主','留赵延照主持贝州'),('赵延照','受任贝州留后')],when='944年三月契丹北归时，主书未列日',place='贝州')
sup('zhao_yanzhao_beizhou_regent',10,old,'甲申，契丹車帳已過貝州，以趙延昭守貝州。','《旧五代史》记三月甲申契丹车帐已过贝州，令赵延昭守贝州。','此书记甲申，辽史壬午分别保留，不强改主书未载的任命日。',relation='adds',field='time_original')
sup('zhao_yanzhao_beizhou_regent',10,liao,'壬午，留趙延昭守貝州，徙所俘戶于內地。','《辽史》记三月壬午留赵延昭守贝州，并迁俘户入内地。','与旧纪甲申日不同，独立保存；文本可能承袭其他史书，不算无条件独立确证。',relation='conflicts',field='time_original')
E['khitan_moves_captive_households']=event('khitan_moves_captive_households','《辽史》记契丹将俘获民户迁往内地',10,'壬午，留趙延昭守貝州，徙所俘戶于內地。',[],source=liao,when='944年三月壬午',place='契丹内地，具体州县未载',note='只知迁入内地，不强填辽阳或具体人数，不将俘户迁移自动记为全部死亡。')
add('mada_captures_dezhou','麻答攻陷德州，擒获刺史尹居璠',10,'麻答陷',None,[('麻答','攻陷德州并擒刺史'),('尹居璠','德州失守时被契丹擒获')],when='944年契丹北归期间，主书在三月条下记述，旧史四月奏报',place='德州',note='报告日与陷城日分开；尹居璠被擒不等于被杀。')
sup('mada_captures_dezhou',10,apr,'滄州奏，契丹陷德州，刺史尹居璠為敵所執。','《旧五代史》四月条下有沧州奏报德州陷落、尹居璠被擒。','四月是奏报所在条，未必是实际陷城月；该句未具名麻答，只支持城陷与被擒。',relation='adds')
# 11: familial alliance, earlier conduct, attempted succession and the dated assassination.
add('zhu_lian_family_alliance','朱文进与连重遇担心被讨伐，两家联姻自保',11,'闽拱宸都指挥使','相与结婚以自固。',[('硃文进','因担心被讨伐，与连重遇家联姻'),('连重遇','因担心被讨伐，与朱文进家联姻')],year=None,when='939年杀王继鹏之后、944年政变之前的追述，具体年月未载',place='闽国',note='结婚指双方家庭结为姻亲，不是两位男性成为夫妻；康宗被杀已在939年录入，不重建另一死亡。')
sup('zhu_lian_family_alliance',11,mine,'連重遇殺昶，懼為國人所討，與朱文進連姻以自固。','《新五代史》也记连重遇杀王昶后，因担心被讨而与朱文进联姻。','昶沿用王继鹏主体；连姻同样支持姻亲，不提供结婚的子女姓名。')
relationship('硃文进','连重遇','姻亲',11,'相与结婚以自固。','双方家族联姻，支系和婚配者未具名，记录对称姻亲，不建夫妻关系或虚构子女。')
add('xi_kills_wei_conglang','王延羲游西园时饮醉，杀控鹤指挥使魏从朗',11,'闽主曦','因醉杀控鹤指挥使魏从朗。',[('曦','游西园饮醉后杀魏从朗'),('魏从朗','被王延羲杀死')],year=None,when='944年政变前的追述，确切年月未载',place='闽国西园',note='尝为先前行为，魏死亡年不强定944；从朗为朱连党人，不建无时间边界的永久盟友。')
claim('person',people['魏从朗'],'death_year','魏从朗被王延羲在西园饮醉后杀死，确切年份未载。',11,'尝游西园，因醉杀控鹤指挥使魏从朗。','死亡动作明确但追述未确年，death_year留空。')
add('xi_poem_toward_zhu_lian','王延羲饮酒时诵诗并向朱文进、连重遇举杯，两人哭拜表忠',11,'又尝酒酣','二人大惧。',[('曦','饮酒时诵白居易诗并向二人举杯，不回应表忠'),('硃文进','与连重遇哭拜表忠，随后害怕'),('连重遇','与朱文进哭拜表忠，随后害怕')],year=None,when='944年政变前另一次饮酒的追述，年月未载',place='闽国',note='诗中情不能料是诗句，臣子事君父为表忠，不建白居易现场参与或君臣血缘父子边。')
add('li_empress_succession_plan','李皇后嫉妒尚贤妃受宠，想杀王延羲、立王亚澄',11,'李后妒','立其子亚澄，',[('李后','想杀王延羲、立王亚澄'),('王亚澄','被李皇后计划立为君主')],year=None,when='944年三月政变之前的追述，具体日期未载',place='闽国',note='欲为计划，不登记王亚澄已即位；嫉妒为史书所叙动机，不将尚贤妃记为实际行刺参与者。')
sup('li_empress_succession_plan',11,mine,'李氏妬尚妃之寵，欲圖曦而立其子亞澄，','《新五代史》也记李氏想害王曦并立其子亚澄。','两书均为意图叙述，不将欲图写为李氏已亲手行刺。')
relationship('李后','王亚澄','母亲',11,'李后妒尚贤妃之宠，欲弑曦而立其子亚澄，','其子承接李后，两书李氏欲图曦立其子亚澄一致，母子方向明确；不据此补出生年份。')
add('li_empress_warns_zhu_lian','李皇后派人告诉朱文进、连重遇，王延羲对他们不满',11,'使人告二人','奈何？”',[('李后','派人向二人传话称皇帝不满他们'),('硃文进','收到李皇后传话'),('连重遇','收到李皇后传话')],year=None,when='944年三月政变前，具体日期未载',place='闽国',note='主人不平为传话内容，不能直接据此确认王延羲已有处死二人诏令。')
add('li_zhen_illness','李真患病',11,'会后父','有疾，',[('李真','患病')],when='944年三月乙酉探病前，患病具体日期未载',place='李真家宅',note='有疾明确，不补病名、病因或死亡。')
relationship('李真','李后','父亲',11,'会后父李真有疾，','父亲关系明确，复用942年已录方向与key。')
add('xi_visits_li_zhen','王延羲前往李真家探病',11,'乙酉，','问疾。',[('曦','前往李真家探病'),('李真','被皇帝探望的病者')],when='944年三月乙酉',place='李真家宅',note='如真第问疾为前往探病，不据后文遇刺保证已完成会面和诊疗。')
add('qian_da_kills_xi','朱文进、连重遇指使钱达，在马上杀死王延羲',11,'文进、重遇使','于马上，',[('硃文进','与连重遇指使钱达行刺'),('连重遇','与朱文进指使钱达行刺'),('钱达','杀死马上的王延羲'),('曦','在马上被钱达杀死')],when='944年三月乙酉',place='探望李真途中，具体路段未载')
sup('qian_da_kills_xi',11,mine,'六年三月，曦出遊，醉歸，重遇等遣壯士拉於馬上而殺之，','《新五代史》记永隆六年三月王曦出游醉归，连重遇等派壮士杀于马上。','同为944年三月，主书探病与新史出游醉归场景并列，未将新史无名壮士直接等同本句具名钱达以外另一刺客。',relation='conflicts')
claim('person',people['王延羲'],'death_year','王延羲于944年三月乙酉被朱文进、连重遇指使钱达杀死。',11,'乙酉，曦如真第问疾。文进、重遇使拱宸马步使钱达弑曦于马上，','死亡明确，复用已有主体，既有档案基线不覆盖。')
add('zhu_lian_assembly_justification','朱文进、连重遇召集百官，宣称王氏失德，应另立有德者',11,'召百官集朝堂，','众莫敢言。',[('硃文进','与连重遇召集百官，宣布更立君主的理由'),('连重遇','与朱文进召集百官并说明更立君主的理由')],when='944年三月乙酉行刺后',place='闽国朝堂',note='天厌王氏与宜择有德是政变者宣称，不能当作本站对王氏灭亡的天命结论。')
add('lian_elevates_zhu','连重遇推朱文进升殿，群臣拜称臣，朱文进自称闽主',11,'重遇乃推','文进自称闽主，',[('连重遇','推朱文进升殿，率群臣称臣'),('硃文进','被推升殿，自称闽主')],when='944年三月乙酉行刺后',place='闽国朝堂',note='实际即位者为朱文进，不混成李皇后原计划的王亚澄即位。')
sup('lian_elevates_zhu',11,minz,'乃掖朱文進升殿，率百官北面而臣之。','《新五代史》也记连重遇扶朱文进升殿，率百官向他称臣。','以开运元年上下文校为944年，不把另段明年机械解释为945年。')
add('zhu_kills_wang_clan','朱文进捕杀王延喜等五十余名王氏宗族成员',11,'悉收王氏宗族','皆杀之。',[('硃文进','捕杀王延喜等王氏宗族成员'),('延喜','与五十余名宗族成员遭杀')],when='944年三月政变后，确切日未载',place='福州',note='新史明确福州内王氏子弟，王延政等在外宗族仍在，不能说所有王氏宗族已绝。')
sup('zhu_kills_wang_clan',11,minz,'王氏子弟在福州者無少長皆殺之。','《新五代史》明确被杀王氏子弟范围为在福州者。','支持地域范围，未给五十余人数，不用这句单独支持主书具体人数。',relation='adds')
claim('person',people['王延喜'],'death_year','王延喜在944年朱文进政变后被杀。',11,'悉收王氏宗族延喜以下少长五十馀人，皆杀之。','具名被杀明确，确切行刑日未载。')
add('xi_burial_posthumous_title','闽国安葬王延羲，给予长谥，庙号景宗',11,'葬闽主曦，','庙号景宗。',[('曦','被安葬，获长谥及景宗庙号')],when='944年上述遇害后，确切安葬日未载',place='闽国，陵名本句未载',description='闽国安葬王延羲，谥为睿文广武明圣元德隆道大孝皇帝，庙号景宗。',note='原文分别列谥号和庙号，景宗不当作另一在位姓名或新人物。')
claim('person',people['王延羲'],'description','《新五代史》此处将景宗写在“謚曰”之后，主书明确其为庙号。',11,'謚曰景宗。','保存原文謚字，不静默更改；称谓形式差异待纸本校核，不把本句当作另一完整谥号。',source=mine,relation='conflicts')
add('lian_commands_six_armies','朱文进让连重遇主管六军',11,'以重遇','总六军。',[('硃文进','让连重遇主管六军'),('连重遇','受命主管六军')],when='944年三月政变后，具体日期未载',place='闽国')
sup('lian_commands_six_armies',11,minz,'文進以重遇判六軍諸衞事，','《新五代史》也记朱文进让连重遇判六军诸卫事。','保留具体职掌，不自动写成独立皇帝或全权继承人。')
add('zheng_yuanbi_refuses','郑元弼抗辞不屈，被黜归乡里',11,'礼部尚书、','黜归田里，',[('郑元弼','以礼部尚书、判三司身份抗辞不屈，被黜归乡里')],when='944年三月政变后，确切日未载',place='闽国',note='抗辞不屈未给具体原话，不虚造奏疏；黜归不等于已经逃到殷国。')
add('zhu_kills_zheng_yuanbi','郑元弼打算逃往建州，朱文进将他杀死',11,'将奔建州，','文进杀之。',[('郑元弼','准备逃往建州，被朱文进杀死'),('硃文进','杀死郑元弼')],when='944年上述被黜后，具体日期未载',place='地点未载',note='将奔为尚待行动，不登记已抵建州后被捕；旧救刘赞条与本次死亡是不同事件。')
claim('person',people['郑元弼'],'death_year','郑元弼于944年朱文进掌权后，被朱文进杀死。',11,'礼部尚书、判三司郑元弼抗辞不屈，黜归田里，将奔建州，文进杀之。','具名动作明确，确切死日与地点未载。')
add('zhu_releases_palace_women','朱文进下令放出宫女，停止营造，以改变王延羲的政策',11,'文进下令，','以反曦之政。',[('硃文进','下令放出宫女并停止营造')],when='944年三月掌权后，具体日期未载',place='闽国',note='原文是下令，不补全部宫女已安置返家或所有工程具体竣工状态。')
add('yin_orders_wu_campaign','王延政派吴成义率兵讨伐朱文进',11,'殷主延政遣','讨文进，',[('殷主','派吴成义率兵讨伐朱文进'),('吴成义','以统军使身份率兵讨伐')],when='944年三月政变后，具体日期未载',place='闽国、殷国')
add('wu_campaign_fails','吴成义讨伐朱文进，未能攻克',11,'殷主延政遣','不克。',[('吴成义','讨伐朱文进，未能攻克')],when='944年上述讨伐期间，具体日期未载',place='朱文进所守区域，具体交战地点未载',note='不克只记未攻取，不自行补兵数伤亡或全军覆没。')
for code,title,start,end,name,role,place in [
('bao_chancellor','朱文进授予鲍思润同平章事职衔','文进加枢密使','同平章事，','鲍思润','由枢密使加同平章事','闽国'),
('huang_quanzhou','朱文进任命黄绍颇为泉州刺史','以羽林统军使','为泉州刺史，','黄绍颇','由羽林统军使任泉州刺史','泉州'),
('cheng_zhangzhou','朱文进任命程文纬为漳州刺史','左军使','为漳州刺史。','程文纬','由左军使任漳州刺史','漳州')]:
 add(code,title,11,start,end,[('硃文进','任命掌权后的官员'),(name,role)],when='944年三月政变后，确切任命日未载',place=place)
sup('huang_quanzhou',11,minz,'以黃紹頗守泉州，','《新五代史》也记黄绍颇守泉州。','只支持驻守，不补主书原羽林统军使职衔或具体任命日。')
sup('cheng_zhangzhou',11,minz,'程贇守漳州，','《新五代史》在对应政局中将漳州守将写作程贇。','主书程文纬与新史程贇姓名差异待核，不直接新增重复程赟或认定已证异名。',relation='conflicts')
add('xu_surrenders_to_zhu','汀州刺史许文稹率郡投降朱文进',11,'汀州刺史',None,[('许文稹','以同安籍贯汀州刺史身份率郡降朱文进'),('硃文进','接受汀州归降')],when='944年三月政变后，确切日未载',place='汀州',note='之承接当前闽主朱文进，不误作此时已经降王延政；新史后文降殷属另一阶段。')
claim('person',people['许文稹'],'name','《新五代史》相同朱文进政局的汀州守将作許文縝。',11,'許文縝守汀州，','相同官州及后续漳泉汀归属场景按同人保留稹縝姓名异文，不改原文；后文投降殷不提前。',source=minz,relation='adds')
# 12–16: return order, Tai prefecture captured, local recruitment, relief and a Han appointment.
add('three_garrisons_return_order','后晋命太原、恒州、定州军队各回本镇',12,'丁亥，',None,[('帝','下诏让三镇军队各回本镇')],when='944年三月丁亥',place='太原、恒州、定州',note='诏令不等于所有部队已返回，不据三镇从人物库机械添加未具名将领。')
add('ma_captures_taizhou','马全节攻取契丹泰州',13,'辛卯，',None,[('马全节','进攻契丹泰州并攻取')],when='944年三月辛卯',place='泰州',note='泰州史载名称，未核坐标，不混成后世同名州。')
sup('ma_captures_taizhou',13,old,'辛卯，定州馬全節攻泰州，拔之，俘其兵士二千人，雜畜戎仗稱是。','《旧五代史》记马全节攻泰州，俘兵二千，并取得牲畜和兵器。','称是为同规模形容，不给牲畜和兵器强填各二千件。',relation='adds')
add('seven_households_soldier_order','后晋登记乡兵，令每七户共出兵器并供养一名兵',14,'敕天下',None,[('帝','下令登记乡兵，由每七户提供兵器和供养一名兵')],when='944年三月条下，具体日期主书未载',place='后晋各地',note='每七户共同负担，不写每户出七人；下诏登记不等于已有明确七万总额，后文军号另处理。')
sup('seven_households_soldier_order',14,old,'癸巳，北京留守、兼中書令劉知遠封太原王，餘如故。是日，詔天下抽點鄉兵，凡七戶出一士，六戶資之，仍自具兵仗，以「武定」為軍號。','《旧五代史》将抽乡兵诏记在三月癸巳，说明七户出一人、其余六户供给，自具兵器，并记武定军号。','癸巳承接本纪是日，军号已见于该书，与主书后续宣布军号的条文分开保留；不在本段另造确切全国人数。',relation='adds')
add('qin_relief_defeats_shu','秦州兵援救阶州，经黄阶岭，在西平击败蜀军',15,'秦州兵',None,[],when='944年三月条下，具体日期未载',place='秦州、黄阶岭、西平、阶州',note='领军者未具名，不自动添加秦州或阶州刺史；本条明确击败，不能由救字推已收复全州。')
add('chen_wo_chancellor','刘弘熙任命户部侍郎陈偓为同平章事',16,'汉以',None,[('汉主','任陈偓为同平章事'),('陈偓','由户部侍郎任同平章事')],when='944年三月条下，具体日期未载',place='南汉',note='偓为底本明确姓名，未见足证不直接与其他陈渥陈濯合并。')
reviews={9:'受命祭陵、至宫和被刺杀分开，不造已经祭成。新史乾和二年夏纪时独立引用；洪昌弘昌与晟弘熙沿用主体，不强将主书三月排列认作真实死月。',10:'实际两路北归和焚掠、赵贝州留后及俘户内迁、麻答陷德擒尹分开。旧纪甲申与辽史壬午异日并列；旧史四月滄奏是报告条，与主三月北归情境分清。尹未写死。',11:'朱连联姻为家族姻亲不是夫妻。杀魏诵诗与后计划均追述未知年。李后欲立亚澄非已即位，实际朱上位。探病行刺与新史醉归异说；福州宗族五十余被杀不扩大到全部王族。葬谥庙号、连六军、郑拒黜将奔而被杀、宫女营造诏令、吴讨不克和三任官及许投朱逐项录。程文纬程贇待核不强合；许稹縝按同州同政局姓名异文保留，后降殷不提前。',12:'三镇返军诏不强作执行完毕。',13:'泰州攻拔与俘二千有旧纪补，不伪精确牲畜兵器数量。',14:'七户出一人六户资之与自具兵仗旧纪癸巳军号独立补，主书后来军号诏未提前认已录。',15:'秦兵救阶经黄阶岭战西平，未具名将领不造主体或收复全州。',16:'汉主刘弘熙，陈偓本字不猜同其他陈姓人物，任官明确无日期。'}
assert not (P/'publication.json').exists()
for n in range(9,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=284,year=944,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=284,next_year=944,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key=minz,note='仅引用朱文进掌权和早期任官，后续漳泉反朱、许降殷及朱连之死留待后续主线，不提前。'),dict(source_key=han,note='仅补弘昌遇害，后续弘泽被毒杀随十月段落另录。'),dict(source_key=apr,note='只补德州失守的四月奏报，四月其他政务未提前。'),dict(source_key=old,note='复用三月快照，只补赵守贝、泰州战及乡兵诏，不提前处理太常丞王绪等补传疑点。')],coverage='卷284原14—21行连续第9—16段，三月及追述；下接第17段四月德州恢复，944全年尚未完成。',source_issues_review='弘昌乾和二年夏纪时、赵贝州守任甲申壬午、闽主探病醉归场景及景宗谥庙形式保留；程文纬程贇待核，许稹縝异文保留，后降殷不提前。联姻支系未知不造配偶。纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],plain_language_review='首次逐项检查标题、正文、人物、参与角色、关系与事实说明，主语明确。联姻、计划即位、实际掌权、命令执行、奏报月份及追述分别处理，原文保持。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
