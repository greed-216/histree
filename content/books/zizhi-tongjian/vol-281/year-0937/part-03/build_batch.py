# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 13–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,60))
specs=[(d.name,d,'94c388fa1ac8e511dfa82745e180e6448bed6177','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-wuyue','xinwudaishi-008-lu-date']:
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
main_sources = ['tongjian-281-937-wuyue']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p013-p028',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-076-937-march':'卷76·晋高祖纪·天福二年三月','jiuwudaishi-076-937-april':'卷76·晋高祖纪·天福二年四月','jiuwudaishi-076-937-may':'卷76·晋高祖纪·天福二年五月','xinwudaishi-065-jiao-gongxian':'卷65·南汉世家'}
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
lines = (ROOT / 'resources/derived/tongjian/281.txt').read_text().splitlines()
for n in range(13, 29):
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
    labels={'jiuwudaishi-076-937-march':'卷76·晋高祖纪·天福二年三月','jiuwudaishi-076-937-april':'卷76·晋高祖纪·天福二年四月','jiuwudaishi-076-937-may':'卷76·晋高祖纪·天福二年五月','xinwudaishi-065-jiao-gongxian':'卷65·南汉世家'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '三月条下' if n<20 else '四月条下' if n<24 else '五月条下' if n<28 else '六月条下'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'李氏（徐知诰尊奉的母亲）':'徐知诰尊奉的母亲，原称明德太妃。937年被追尊为王太后。此段没有说明其具体家世，亲属关系仍需补证。',
'皎公羡':'交州将领。《资治通鉴》记载他在937年杀死安南节度使杨廷艺并取代其职务。',
'钱弘僔':'吴越王钱元瓘的儿子。937年四月被立为世子。',
'林鼎':'吴越官员。937年以镇海节度判官身份掌管教令。'}
NEW_ALIASES={'李氏（徐知诰尊奉的母亲）':[], '皎公羡':['皎公羨'], '钱弘僔':['弘僔'], '林鼎':[]}
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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=937, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when=('937年三月' if n<20 else '937年四月' if n<24 else '937年五月' if n<28 else '937年六月')+'，具体日期未记载'
    key = 'event_zztj_281_0937_' + code
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
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_281_0937_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_281_0937_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
add('li_congke_remains_found','有人找到李从珂的脊背和大腿遗骨并献出',13,'或得','献之，',[('唐主','死后遗骨被找到并献出')],note='唐潞王为李从珂，已在936年去世；献骨者未具名，不补造人物。')
add('li_congke_royal_burial','石敬瑭下诏以王礼安葬李从珂遗骨',13,'庚申，',None,[('帝','下诏以王礼安葬李从珂'),('唐主','遗骨被命以王礼安葬')],when='937年三月庚申',place='徽陵南',note='庚申是诏令日期，不直接当作实际下葬日。')
sup('li_congke_royal_burial',13,'jiuwudaishi-076-937-march','中書奏：「準敕。故庶人三月七日以王禮葬，其妻男等並以禮葬，請輟其日朝參一日。」從之。','《旧五代史》补记中书奏报三月七日以王礼安葬，并将其妻子、儿子以礼安葬，请停朝参一日。','本纪故庶人对应已被追降的李从珂；与《通鉴》庚申诏令分别保存，不混同命令日和下葬日。妻男未具名，不把此前亡者写成在场。',relation='adds',field='time_original')
add('jin_envoy_to_shu','石敬瑭派使者向孟昶告知即位并谈及姻亲关系',14,'帝遣使','且叙姻好；',[('帝','派使者告知即位并谈及姻亲关系'),('蜀主','后蜀接受使者的君主')],place='晋至蜀',note='“姻好”未在本段列明具体婚姻，不凭此新增夫妻或姻亲边。')
add('shu_equal_reply','孟昶以两国对等的礼仪回复石敬瑭',14,'蜀主复书，',None,[('蜀主','以对等国礼复书'),('帝','复书对象')],description='孟昶回复石敬瑭，使用两国对等的礼仪。这里的“敌国礼”指地位对等的国家礼仪，不表示双方已经交战。')
add('fan_prepares_rebellion','范延光集结士兵、整修兵器，并召辖内刺史到魏州',15,'范延光','将作乱。',[('范延光','集结士兵、整修兵器，召辖内刺史到魏州准备作乱')],place='魏州',note='准备与正式起兵分开；未具名刺史不补造人物。')
add('sang_supports_bian_move','桑维翰建议迁都大梁，以便应对范延光',15,'会帝谋','掩耳也。”',[('帝','谋划迁都大梁'),('桑维翰','说明大梁的交通财用及应对范延光的军事便利')],place='大梁',description='石敬瑭谋划迁都大梁。桑维翰称大梁水陆交通便利、物资充足，距离魏州不超过十驿；若范延光起事，朝廷能够迅速出兵。',note='距离和交通优势为桑维翰提出的理由，不换算成现代公里数；假设迅速出兵不记录为已发生的作战。')
add('shi_announces_bian_tour','石敬瑭以漕运不足为由下诏东巡汴州',15,'丙寅，',None,[('帝','下诏以洛阳漕运不足为由东巡汴州')],when='937年三月丙寅',place='洛阳至汴州',note='《通鉴》认为漕运理由是托词，作为史家判断保留；东巡诏令不直接等同于永久迁都已经完成。')
sup('shi_announces_bian_tour',15,'jiuwudaishi-076-937-march','取今月二十六日巡幸汴州','《旧五代史》所载诏书宣布于当月二十六日巡幸汴州。','这是诏书计划日期，实际出发另由庚辰记录；补证使用诏书正文，不把旁引《通鉴》的注释当独立证明。',relation='adds')
add('li_jing_declines_heir','徐知诰立徐景通为王太子，徐景通坚决辞让',16,'吴徐知诰','固辞不受。',[('徐知诰','立儿子徐景通为王太子'),('景通','坚决辞让王太子之位')],description='徐知诰立儿子徐景通为王太子，徐景通坚决辞让。人物沿用后来的名字李昪、李璟对应的稳定主体。',note='辞让与任命分别说明，不把辞让直接写成已经正式成为王太子。')
add('xu_wen_posthumous_wuwang','徐知诰追尊徐温为太祖武王',16,'追尊考','曰太祖武王，',[('徐知诰','追尊徐温为太祖武王'),('徐温','去世后被追尊为太祖武王')],note='追尊发生在齐王阶段，不与后来受禅后的帝号混同；不根据“考”改写已存收养关系。')
add('li_mother_posthumous_queen','徐知诰追尊明德太妃李氏为王太后',16,'妣明德太妃','曰王太后。',[('徐知诰','追尊明德太妃李氏为王太后'),('李氏（徐知诰尊奉的母亲）','由明德太妃被追尊为王太后')],note='本段明确妣李氏，但未说明其完整家世；与此前陈夫人不凭尊母称谓合并，暂不新增有争议的亲属边。')
add('li_bian_renames_gao','徐知诰改名为徐诰',16,'壬申，',None,[('徐知诰','将名字由知诰改为诰')],when='937年三月壬申',note='改名仍复用李昪的稳定主体，不建立新人物。')
add('shi_leaves_luoyang','石敬瑭从洛阳出发',17,'庚辰，','帝发洛阳，',[('帝','从洛阳出发东巡')],when='937年三月庚辰',place='洛阳')
sup('shi_leaves_luoyang',17,'jiuwudaishi-076-937-march','庚辰，車駕離京。','《旧五代史》也记载石敬瑭于庚辰离京。','本纪前文宣布巡幸汴州，离京为实际出发而不是另一个巡行计划。')
add('zhang_congbin_luoyang_inspector','石敬瑭留下张从宾担任东都巡检使',17,'留前朔方',None,[('帝','留下张从宾负责东都巡检'),('张从宾','由前朔方节度使被任命为东都巡检使')],when='937年三月庚辰',place='洛阳',note='这是巡检任命，不提前写成后来的叛乱或指挥魏州征讨。')
add('liu_yan_recovery_amnesty','刘岩病愈后发布赦令',18,'汉主',None,[('汉主','病愈后发布赦令')],place='南汉',note='病愈和赦令有原文明示的原因关系，不推断疾病名称。')
add('jiao_kills_yang_tingyi','皎公羡杀死杨廷艺并取代其职务',19,'交州将',None,[('皎公羡','杀死杨廷艺并取代其职务'),('杨廷艺','以安南节度使身份被杀')],place='交州',note='杀人和取代职务均由原文明示，不把后来吴权及白藤之战提前到此事件。')
sup('jiao_kills_yang_tingyi',19,'xinwudaishi-065-jiao-gongxian','十年，交州牙將皎公羨殺楊廷藝自立，','《新五代史》南汉世家也记载皎公羡杀杨廷艺自立。','此句位于大有纪年序列，十年与937年相符；同段随后吴权及南汉出兵为后续叙事，不因合段全部定在937年。')
claim('person',people['杨廷艺'],'death_year','杨廷艺于937年被皎公羡杀死。',19,Q[19]['text'],'主书明确该年条下被杀，事实引用补充死年；既有主体的旧档案不直接覆盖。')
add('shi_arrives_bian','石敬瑭到达汴州',20,'夏，四月，','帝至汴州；',[('帝','到达汴州')],when='937年四月丙戌',place='汴州')
sup('shi_arrives_bian',20,'jiuwudaishi-076-937-april','甲申，駕入汴州。','《旧五代史》记石敬瑭于四月甲申进入汴州。','与《通鉴》丙戌有日期差异，分别保留，不自行换算或覆盖。',relation='conflicts',field='time_original')
add('jin_april_amnesty','石敬瑭在汴州发布大赦',20,'丁亥，',None,[('帝','发布大赦')],when='937年四月丁亥',place='汴州')
sup('jin_april_amnesty',20,'jiuwudaishi-076-937-april','應天福二年四月五日昧爽已前，諸道州府見禁囚徒，大辟已下，罪無輕重，並釋放。','《旧五代史》所载赦令要求释放天福二年四月五日清晨以前各地在押囚徒。','“大辟已下”包含死刑，不误译为仅免轻罪；原文日期为赦令界限，不等于所有人均已实际获释。',relation='adds')
event('jin_april_tax_relief','石敬瑭赦令免除旧欠租税，并减免受灾地区租税',20,source_span('jiuwudaishi-076-937-april','天福元年已前，','量與蠲免租稅。'),[('帝','下令免除旧欠租税')],source='jiuwudaishi-076-937-april',when='937年四月丁亥赦令',description='石敬瑭在赦令中免除天福元年及以前的欠税。赦令还要求检查荥阳县沿途桑麦受虫害和旱灾的地区，酌情减免租税。',note='旧欠税免除与受灾地区酌免不是同一口径，不写成全年度全国免税。')
E['jin_april_tax_relief']='event_zztj_281_0937_jin_april_tax_relief'
sup('jin_april_tax_relief',20,'jiuwudaishi-076-937-april','昨者，行至鄭州滎陽縣界，路旁見有蟲食及旱損桑麥處，委所司差人檢覆，量與蠲免租稅。','赦令要求核查荥阳桑麦虫害和旱损，再酌情减免租税。','这是检查和减免的命令，不补造具体减免比例和执行结果。',relation='adds')
add('wuyue_restores_kingdom','钱元瓘恢复吴越建国制度，沿用同光时期旧例',21,'吴越王元瓘','如同光故事。',[('钱元瓘','恢复吴越建国制度，沿用同光时期旧例')],place='吴越',note='“复建国”依原文保留为制度恢复，不作为另一个全新国家首次建立或新获疆土。')
add('wuyue_april_amnesty','钱元瓘赦免吴越境内罪人',21,'丙申，','赦境内，',[('钱元瓘','发布境内赦令')],when='937年四月丙申',place='吴越')
add('qian_hongzun_heir','钱元瓘立儿子钱弘僔为世子',21,'立其子','为世子。',[('钱元瓘','立钱弘僔为世子'),('钱弘僔','被立为吴越世子')],when='937年四月丙申',place='吴越')
relationship('钱元瓘','钱弘僔','父亲',21,span(21,'吴越王元瓘','为世子。'),'“其子弘僔”指本段吴越王钱元瓘，父亲指向钱弘僔。')
add('wuyue_three_chancellors','曹仲达、沈崧和皮光业被任命为丞相',21,'以曹仲达','为丞相，',[('曹仲达','被任命为吴越丞相'),('沈崧','被任命为吴越丞相'),('皮光业','被任命为吴越丞相')],place='吴越',note='三人同任官不自动建立私人盟友关系，未给三人分别推具体左右职称。')
add('lin_ding_edicts','镇海节度判官林鼎掌管教令',21,'镇海节度判官',None,[('林鼎','以镇海节度判官身份掌管教令')],place='吴越',note='掌教令是职责，不自行增加丞相官衔。')
add('yang_tan_shizhong','杨光远兼任侍中',22,'丁酉，',None,[('杨光远','以宣武节度使身份加兼侍中')],when='937年四月丁酉',note='杨光远沿用原名杨檀的稳定主体，不因改名新建。')
sup('yang_tan_shizhong',22,'jiuwudaishi-076-937-april','丁酉，宣武軍節度使、侍衛親軍使楊光遠加兼侍中。','《旧五代史》也记杨光远同日加兼侍中，并补充其侍卫亲军使身份。','任官日期和对象相同，独立保留出处。',relation='adds')
add('min_ziwei_palace','王继鹏修建紫微宫，并以水晶装饰',23,'闽主作','倍于宝皇宫。',[('闽主','修建紫微宫，以水晶装饰')],place='闽',description='王继鹏修建紫微宫，以水晶装饰。史书称其土木规模比宝皇宫大一倍，保留为史载的比较描述。',note='原文规模描述不换算成面积、预算或考古测量结果；此时闽主为王继鹏。')
add('min_spies_officials','王继鹏派使者到各州探查隐秘过失',23,'又遣使',None,[('闽主','派使者到各州探查隐秘过失')],place='闽各州',note='使者未具名，不凭“隐慝”创造已确定的具体犯罪或判决。')
add('li_bian_khitan_strategy','徐诰采纳宋齐丘建议，计划联合契丹争取中原',24,'五月，','欲结契丹以取中国，',[('徐诰','采纳宋齐丘建议，计划联合契丹争取中原'),('宋齐丘','提出联合契丹的建议')],description='徐诰采纳宋齐丘的建议，计划与契丹结好以争取中原。这是政治意图，不等于双方已经组成军事联盟或发动战争。',note='此处中国按当时中原政权语境解释，不直接等同现代国家疆域。')
add('li_bian_maritime_mission','徐诰派使者携美女和珍玩渡海与契丹修好',24,'遣使以','泛海修好，',[('徐诰','派使者携美女和珍玩渡海修好')],place='吴至契丹海路',note='使者及随行女子未具名，不推婚姻关系，路线坐标未核。')
add('khitan_replies_to_qi','耶律德光派使者回报徐诰',24,'契丹主亦',None,[('契丹主','派使者回报徐诰'),('徐诰','回使所报对象')],note='回使证明外交往来，不单凭此建立军事同盟关系。')
add('bian_daning_palace','石敬瑭将汴州牙城暂称大宁宫',25,'丙辰，',None,[('帝','下令将汴州牙城暂称大宁宫')],when='937年五月丙辰',place='汴州牙城',note='权署为暂定名称，不直接认定永久迁都制度已全部完成。')
sup('bian_daning_palace',25,'jiuwudaishi-076-937-may','敕：行闕宜以大寧宮為名。','《旧五代史》也记将行阙称为大宁宫。','本纪位于张昭远丙辰奏议之后，奏议与诏令可作背景和决定分别记录。')
event('zhang_zhao_palace_names','张昭建议给汴州行宫设统一宫名',25,'請準故事，於汴州衙城門權掛一宮門牌額，則其餘齋閣並可取便為名。',[('张昭远','以御史中丞身份建议为汴州行宫设统一宫名')],source='jiuwudaishi-076-937-may',when='937年五月丙辰',place='汴州',note='主体沿张昭（五代宋初）已校核稳定名；姓名和官职来自同段开头，建议与敕令分开。')
add('fan_linqing_prince','石敬瑭封范延光为临清郡王以安抚他',26,'壬申，',None,[('帝','进封范延光以安抚他'),('范延光','被进封为临清郡王')],when='937年五月壬申',note='封爵是已发生的任命，安抚为《通鉴》说明的目的，不据此推双方疑虑已经消除。')
sup('fan_linqing_prince',26,'jiuwudaishi-076-937-may','壬申，天雄軍節度使、守太傅、兼中書令、興唐尹範延光進封臨清王，加食邑三千戶；','《旧五代史》写进封临清王并增加食邑三千户。','临清王与主书临清郡王的称号写法分别保存，食邑户数不当作实际控制人口。',relation='adds')
add('shi_ancestors_posthumous','石敬瑭追尊四代祖先为皇帝、皇后',27,'追尊四代','为帝后。',[('帝','追尊四代祖先为皇帝、皇后')],note='这是追尊，不表示这些祖先在生前都曾实际统治后晋。')
sup('shi_ancestors_posthumous',27,'xinwudaishi-008-lu-date','丁丑，追尊祖考為皇帝，妣為皇后：高祖璟謚曰孝安，廟號靖祖，祖妣秦氏謚曰孝安元；曾祖郴謚曰孝簡，廟號肅祖，祖妣安氏謚曰孝簡恭；祖昱謚曰孝平，廟號睿祖，祖妣來氏謚曰孝平獻；考紹雍謚曰孝元，廟號獻祖，妣何氏謚曰孝元懿。','《新五代史》明确追尊日为五月丁丑，并列石璟、石郴、石昱、石绍雍及秦氏、安氏、来氏、何氏的谥号和庙号。','本段主书未列姓名和确日，补证单独保存，避免把丁丑和下文己卯混同；未扩造祖先生平。',relation='adds',field='time_original')
add('tang_heads_burial_allowed','石敬瑭允许亲友收葬太社所藏唐室罪人首级',27,'己卯，','听亲旧收葬。',[('帝','下诏允许亲友收葬所藏首级')],when='937年五月己卯',note='只记录允许收葬，不能把所有首级写成已被领走；史书沿用“罪人”称呼，不重新裁定罪名。')
sup('tang_heads_burial_allowed',27,'jiuwudaishi-076-937-may','己卯，詔太社內先收掌唐朝罪人首級等，宜令骨肉或先舊僚屬收葬，其喪葬儀註不得過制。','《旧五代史》同记己卯诏令，并要求葬仪不得超过规定。','首级对象是所藏旧首，不把史称罪人解释为当前重新处刑。',relation='adds')
add('lou_served_liang','娄继英过去曾任朱友贞的内诸司使',27,'初，武卫上将军','为内诸司使，',[('娄继英','过去曾为朱友贞担任内诸司使'),('梁均王','娄继英过去所事的君主')],year=None,when='追述后梁朱友贞时期，具体任职起止未载',note='此为过去任职，不写成937年才在后梁任官；梁均王对应朱友贞。')
add('lou_buries_zhu_head','娄继英请求收葬朱友贞的首级并安葬',27,'至是，',None,[('娄继英','请求收取朱友贞的首级并安葬'),('梁均王','去世后首级被收葬')],when='937年五月己卯允许收葬之后，实际收葬日未载',note='“其首”指前文梁均王朱友贞，与命令允许收葬分开；亡者是被葬对象，未写成在场参与。')
add('xu_jingqian_dies','吴国诸道副都统徐景迁去世',28,'六月，',None,[('徐景迁','以吴国诸道副都统身份去世')],when='937年六月',note='原文明确六月去世，无独立干支日，不自行换算。')
claim('person',people['徐景迁'],'death_year','徐景迁于937年六月去世。',28,Q[28]['text'],'主书明确年月，新增死年事实；已发布旧人物档案保持原样。')
for name,n,start,end in [('李氏（徐知诰尊奉的母亲）',16,'妣明德太妃','曰王太后。'),('皎公羡',19,'交州将',None),('钱弘僔',21,'吴越王元瓘','为世子。'),('林鼎',21,'镇海节度判官',None)]:
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'简介按原文明示的身份和行动整理，不补未知生卒、家世和官职。')
reviews={13:'献骨与庚申王礼葬诏分开，旧史补三月七日葬及妻男礼葬，不混命令日和执行日。',14:'姻好不建未证婚姻，敌国礼解释为对等国礼，不推已交战。',15:'范准备作乱、迁都讨论与丙寅东巡诏分开；桑十驿为言辞，旧史诏书正文独立引用，不将旁引通鉴当另一证明。',16:'徐景通辞太子不写任职已受；徐温及李氏追尊不和后来的帝号混同；李氏家世与陈夫人关系待核，改名复用李昪。',17:'庚辰实际出发与张从宾巡检任官分别记录，旧史同出发日。',18:'刘岩病愈赦令明确，不补疾病。',19:'皎杀杨并取代为主线，新史十年在大有纪年序列同937，后续白藤战不提前到937。',20:'主到汴丙戌与旧甲申异日并列，赦令同丁亥；旧赦补囚徒释放命令、欠税及受灾量免，不推执行完成。',21:'吴越复建国为制度恢复，赦、立世子、三相、林鼎职责分录。钱弘僔父亲边明示；三相不建同场私人关系。',22:'杨光远沿杨檀主体，旧同日加侍中，原宣武身份与吴卢文进不混。',23:'宫殿规模为史载比较，不换面积，闽主王继鹏；匿名探查使不补名罪。',24:'结契丹以取中原是意图，派海使和回使是行动，不建无证军事同盟。',25:'暂称大宁宫与永久都城制度分开，旧补张昭奏议，沿已校核张昭远同人。',26:'封爵与安抚目的分开，旧临清王及食邑三千另保。',27:'追尊四代为死后称号，新补丁丑姓名谥庙号，不错给己卯；允许收首与娄实际葬首分，梁均王朱友贞，过去任职年份不强定。',28:'徐景迁六月卒年明确，人物复用且死年只补事实，不改旧档案。'}
assert not (P/'publication.json').exists()
for n in range(13,29):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(13,29)],next_paragraph=Q[29]['id'],next_volume=281,next_year=937,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第13—28段（原第18—33行），从李从珂王礼葬、晋蜀往来到东巡汴州、吴越与闽、契丹外交、祖先追尊及徐景迁去世。937年尚未完成。',source_issues_review='每段与原TXT行号逐字一致，本范围未见私用字；主书复用既有完整段落快照，导出范围不计作已录范围。新增旧史三段本纪正文及新史南汉世家段落传主已核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(13,29)],plain_language_review='所有新增标题、人物介绍、事件说明、参与角色和事实解释在首次整理时逐条使用现代白话；引用原字不改。复用人物保留既有档案，未解决的家世和异说单独列出，不另设发布后二次文字审阅。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
