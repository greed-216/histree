# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 283, year 943 paragraphs 9–16."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,43))
COMMIT='d0492098592de640119d51b379b17908f65b59b0'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-283-943-early-b','xinwudaishi-009-943-return','xinwudaishi-062-jing-brothers','xinwudaishi-062-feng-name','xinwudaishi-068-min-li-empress']:
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
main_sources = ['tongjian-283-943-early-b','tongjian-283-943-south-han','tongjian-283-943-april-may']
B = {'format_version': 1, 'batch_key': 'zztj-v283-y0943-p009-p016',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-south-han':'卷283·天福八年·南汉继位','tongjian-283-943-april-may':'卷283·天福八年·四五月及追述','jiuwudaishi-081-943-march':'卷81·晋少帝本纪·天福八年三月','xinwudaishi-065-liu-bin-death':'卷65·南汉世家·刘玢被杀','xinwudaishi-065-liu-sheng-accession':'卷65·南汉世家·刘晟继位'}
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
lines = (ROOT / 'resources/derived/tongjian/283.txt').read_text().splitlines()
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
    labels={'tongjian-283-943-south-han':'卷283·天福八年·南汉继位','tongjian-283-943-april-may':'卷283·天福八年·四五月及追述','jiuwudaishi-081-943-march':'卷81·晋少帝本纪·天福八年三月','xinwudaishi-065-liu-bin-death':'卷65·南汉世家·刘玢被杀','xinwudaishi-065-liu-sheng-accession':'卷65·南汉世家·刘晟继位'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '三月至四月条下及追述'
        citation = f'卷283·后晋天福八年（943；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_283_0943_02_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=943, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='943年年初条下，具体日期未载'
    key = 'event_zztj_283_0943_' + code
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
        edge = 'participation_zztj_283_0943_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_283_0943_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'石重贵','唐主':'李璟','元宗':'李璟','景遂':'徐景遂','景达':'徐景达','李景达':'徐景达','冯延己':'冯延巳','延己':'冯延巳','延鲁':'冯延鲁','汉主':'刘弘度','殇帝':'刘弘度','弘熙':'刘弘熙','弘昌':'刘弘昌','弘杲':'刘弘杲','曦':'王延羲','钟氏':'钟氏（李璟妻）','贤妃尚氏':'尚氏（王延羲贤妃）'})
NEW_ALIASES={'查文徽':[],'杜昌业':['杜昌業'],'王彦俦':['王彥儔'],'吴怀恩':['吳懷恩'],'刘思潮':['劉思潮'],'谭令禋':['譚令禋'],'林少强':['林少強','林少彊'],'林少良':[],'何昌廷':[],'尚保殷':[],'尚氏（王延羲贤妃）':['尚氏','尚氏（王延羲妃）']}
NEW_DESCRIPTIONS={
'查文徽':'休宁人，南唐官员。943年李璟即位后，史书记他与陈觉、冯延巳、冯延鲁、魏岑互相引荐，不久与魏岑同任枢密副使。当时五人被称为五鬼，称呼按史书记载保留。生卒年尚未核。',
'杜昌业':'南唐江州观察使。943年冯延鲁升中书舍人、勤政殿学士后，他批评仅因言语合意便授高官会使日后功臣难以获得适当奖赏。生卒年尚未核。',
'王彦俦':'上蔡人，南唐池州节度使。史书说他对当地贬官管束过严，但尊重被贬为池州判官的常梦锡。具体年月和生卒年尚未核。',
'吴怀恩':'番禺人，南汉内常侍。刘弘度即位后，他与越王刘弘昌多次劝谏，刘弘度没有听从。具体劝谏年月和生卒年未载。',
'刘思潮':'南汉力士。943年在刘弘熙安排下，由陈道庠召入晋王府练习手搏；随后参与杀死刘弘度，刘弘熙即位后受到赏赐。《新五代史》还记刘思潮等获封功臣。生卒年尚未核。',
'谭令禋':'南汉力士，943年在刘弘熙安排下，由陈道庠召入晋王府练习手搏。史书将他列于五名力士中；陈道庠、刘思潮等随后杀死刘弘度，但本段没有逐一说明所有力士当时的动作。生卒年尚未核。',
'林少强':'南汉力士，943年与刘思潮等在晋王府练习手搏。《资治通鉴》作林少强，《新五代史》作林少彊。与林少良同姓名相近，但本段未明确亲属关系，暂不建兄弟关系。生卒年尚未核。',
'林少良':'南汉力士，943年与刘思潮等在晋王府练习手搏。与林少强同姓名相近，但本段未明确亲属关系，暂不建兄弟关系。生卒年尚未核。',
'何昌廷':'南汉力士，943年在刘弘熙安排下，由陈道庠召入晋王府练习手搏。史书将他列于五名力士中，本段未逐一说明他在杀死刘弘度时的动作。生卒年尚未核。',
'尚保殷':'闽国金吾使，尚氏的父亲。943年条下记王延羲纳其女并立为贤妃。具体日期和生卒年尚未核。',
'尚氏（王延羲贤妃）':'尚保殷的女儿，王延羲的贤妃。943年条下记王延羲纳她、立为贤妃；史书称她受宠，王延羲醉中依她的意思杀人或赦免。具体日期、个人名字和生卒年尚未核。'}
march=dict(when='943年三月条下，具体日期未载',place='南唐')
# 9: appointments distinguish holding an honorary title from entering the central office.
add('zhao_ying_jinchang','石重贵任赵莹为晋昌节度使，兼中书令',9,'三月，','为晋昌节度使兼中书令；',[('帝','任赵莹为晋昌节度使兼中书令'),('赵莹','由中书令出任晋昌节度使兼中书令')],when='943年三月己卯朔',place='后晋')
add('sang_central_shizhong','石重贵召桑维翰入朝任侍中',9,'以晋昌节度使',None,[('帝','召桑维翰入朝任侍中'),('桑维翰','由晋昌节度使兼侍中入朝任侍中')],when='943年三月己卯朔',place='后晋',note='之前在藩镇兼侍中与此次入朝任侍中区分，旧纪所附胡注支持职务变化。')
old='jiuwudaishi-081-943-march';new='xinwudaishi-009-943-return'
sup('zhao_ying_jinchang',9,old,'三月己卯朔，以中書令、監修國史趙瑩為晉昌軍節度使，','《旧五代史》也记三月己卯朔赵莹出任晋昌军节度使，此前兼监修国史。','仅补其此前职衔，不据这句自动延续其监修职务。',relation='adds')
sup('sang_central_shizhong',9,old,'以晉昌軍節度使桑維翰為侍中、監修國史。','《旧五代史》还记桑维翰此次兼监修国史。','史书正文支持新增职务，附注为后人引文，不能冒充五代诏书。',relation='adds')
sup('sang_central_shizhong',9,new,'晉昌軍節度使桑維翰為侍中。','《新五代史》也记桑维翰由晋昌军节度使任侍中。','同年三月己卯条下。')
sup('zhao_ying_jinchang',9,new,'三月己卯朔，趙瑩罷。','《新五代史》把赵莹离开中央相位简记为罢。','罢相不等于免去全部官职，与主书出任节度使并列。')
# 10: accession, proposals and personnel changes; earlier advice is retrospective.
add('jing_accession','李璟正式即位为南唐皇帝',10,'唐元宗','即位，',[('唐主','正式即位为南唐皇帝')],note='与上批二月李璟监国区分；元宗为后世庙号，主体仍复用李璟。',**march)
add('jing_pardon_baoda','李璟实行大赦，改元保大',10,'大赦，','改元保大。',[('唐主','即位后大赦并改元保大')],**march)
add('han_requests_next_year_era','韩熙载请求等到下一年改元，李璟没有听从',10,'秘书郎','不从。',[('韩熙载','任秘书郎，请求等下一年再改元'),('唐主','没有接受延后改元的建议')],note='逾年指跨到下一年，不译为一年多后；不把未接受的建议记成已改下一年。',**march)
add('song_empress_dowager','李璟尊母亲宋氏为皇太后',10,'尊皇后','曰皇太后，',[('唐主','尊先帝宋皇后为皇太后'),('宋氏（南唐李昪后）','被尊为皇太后')],note='母亲身份由上批主书与新史明确，不造新的宋氏主体。',**march)
add('zhong_empress','李璟立钟氏为皇后',10,'立妃','为皇后。',[('唐主','立钟氏为皇后'),('钟氏','由妃被立为皇后')],**march)
succ='xinwudaishi-062-jing-brothers'
sup('jing_accession',10,succ,'昪卒，嗣位，改元保大。','《新五代史》也记李昪死后李璟继位。','仅补当前继位，不提前记录本段之后的秋季封王。')
sup('jing_pardon_baoda',10,succ,'昪卒，嗣位，改元保大。','《新五代史》也记改元保大。','此句未给大赦，补证范围仅限改元。')
sup('song_empress_dowager',10,succ,'尊母宋氏為皇太后，','《新五代史》明确李璟尊母亲宋氏为皇太后。','同一母亲与太后。')
sup('zhong_empress',10,succ,'妃鍾氏為皇后。','《新五代史》也记立钟氏为皇后。','鍾氏原字保留，展示钟氏。')
add('jing_rebukes_feng_visits','冯延巳一天多次入宫报告事务，李璟责问为何这样烦扰',10,'唐主未听政，','何为如是其烦也！”',[('冯延己','在李璟尚未正式听政时一天多次入宫报告事务'),('唐主','责问冯延巳为何频繁报告')],note='日至数四保留为一天多次，不造每次独立奏事和具体内容。',**march)
add('jing_consults_court','李璟初即位时尊重臣下，经常邀请公卿讨论治国',10,'唐主为人谦谨，','数延公卿论政体，',[('唐主','不直呼大臣姓名，并经常与公卿讨论治国')],note='谦谨为史书评价；不名大臣是不直呼姓名，不改写为不知道姓名。长期概述没有具体次数。',**march)
add('jianxun_warns_jing_advisers','李建勋称赞李璟宽仁，又担心没有正直辅臣会守不住基业',10,'李建勋谓人曰：','但恐不能守先帝之业耳。”',[('李建勋','向人称赞新君，并担心缺少正直辅臣')],note='这是李建勋的评价和担忧，不当作将来亡国已发生；谈话对象未具名。',**march)
add('qiqiu_taibao_zhongshu','李璟任宋齐丘为太保兼中书令',10,'唐主以镇南','为太保兼中书令，',[('唐主','任宋齐丘为太保兼中书令'),('宋齐丘','由镇南节度使任太保兼中书令')],**march)
add('zhou_zong_shizhong','李璟任周宗为侍中',10,'奉化节度使','为侍中。',[('唐主','任周宗为侍中'),('周宗','由奉化节度使任侍中')],**march)
claim('event',E['qiqiu_taibao_zhongshu'],'description','李璟因宋齐丘、周宗是先朝功臣，顺应众望召他们为相，但政事仍自行决定。',10,'唐主以齐丘、宗先朝勋旧，故顺人望召为相，政事皆自决之。','按史书所述任命理由与决策方式记录，不推宋齐丘已实际独揽政事。')
add('jingsui_yanwang','李璟将徐景遂由寿王改封燕王',10,'徙寿王','为燕王，',[('唐主','将景遂改封燕王'),('景遂','由寿王改封燕王')],note='复用此前徐景遂稳定key，不因姓氏变化新建李景遂。',**march)
add('jingda_ewang','李璟将李景达由宣城王改封鄂王',10,'宣城王','为鄂王。',[('唐主','将景达改封鄂王'),('景达','由宣城王改封鄂王')],note='复用徐景达稳定key及上批同人核对，不新建重复人物。',**march)
sup('jingsui_yanwang',10,succ,'封弟壽王景遂為燕王，','《新五代史》也记李璟将弟弟景遂封为燕王。','保留兄弟身份的补证；不把秋季改齐王提前。')
sup('jingda_ewang',10,succ,'宣城王景達鄂王，','《新五代史》也记将宣城王景达改封鄂王。','句式承前封弟，不提前后续改燕王。')
add('mengxi_prior_advice','李璟任齐王时，常梦锡常直言纠正他的过失',10,'初，唐主为齐王，','终以谅直多之。',[('常梦锡','直言纠正齐王的过失'),('唐主','起初生气，最终因常梦锡诚实正直而看重他')],year=None,when='李璟任齐王并知政事期间，具体年月未载',place='南唐',note='初为追述；不把这些劝谏套成943年即位后的新事。')
add('jing_promises_mengxi_academician','李璟即位后，答应让常梦锡任翰林学士',10,'及即位，','许以为翰林学士，',[('唐主','答应让常梦锡任翰林学士'),('常梦锡','得到任翰林学士的承诺')],note='许为答应，是否已正式授职由新史另引，不只凭此句推已完成授职。',**march)
sup('jing_promises_mengxi_academician',10,'xinwudaishi-062-feng-name','景以馮延巳、常夢錫為翰林學士，','《新五代史》直接记李璟任常梦锡为翰林学士。','与通鉴答应任职分别保留表述，未给授职日，不补同日。',relation='adds')
add('mengxi_chizhou_demoted','常梦锡因封驳制书，被贬为池州判官',10,'齐丘之党疾之，','贬池州判官。',[('常梦锡','因封驳制书被贬为池州判官')],when='943年李璟即位后，具体日期未载',place='池州',note='史书说宋齐丘党羽嫉恨常梦锡，但未列具体处分者；封驳为对制书提出异议并退回，不省略成无缘由贬官。')
add('yanchou_respects_mengxi','王彦俦严管池州贬官，却仍尊重常梦锡',10,'池州多迁客，',None,[('王彦俦','管束池州贬官过严，但对常梦锡仍如其在朝时一样尊重'),('常梦锡','被贬池州后仍受到王彦俦尊重')],year=None,when='常梦锡被贬池州后的概述，具体年月未载',place='池州',note='几不聊生是史书所说其他贬官的困境，不造具体名单。')
# 11–12: officials and contemporary criticism.
add('jing_employs_chen','李璟认为陈觉有才，委以任用',11,'宋齐丘待','遂委任之。',[('宋齐丘','一直厚待陈觉'),('唐主','认为陈觉有才，委以任用'),('陈觉','因得到李璟认可而获任用')],when='943年李璟即位后的记载，具体日期未载',place='南唐',note='本句未给具体新职，不能将后文枢密使任命硬套本句。')
add('five_officials_connections','陈觉等五人互相引荐，被当时人称为五鬼',11,'冯延己、','唐人谓觉等为“五鬼”。',[('冯延己','依附陈觉并与同僚互相引荐'),('延鲁','依附陈觉并与同僚互相引荐'),('魏岑','依附陈觉并与同僚互相引荐'),('陈觉','得到三位齐王府旧僚依附'),('查文徽','与陈觉等互相引荐')],when='943年李璟即位后的记载，具体日期未载',place='南唐',note='侵蠹政事为史书评价，五鬼是当时人的称呼；不据共同政务建立无证据盟友关系。')
add('yanlu_zhongshu_academician','冯延鲁升中书舍人、勤政殿学士',11,'延鲁自','勤政殿学士，',[('延鲁','由礼部员外郎升中书舍人、勤政殿学士')],when='943年李璟即位后，具体日期未载',place='南唐')
add('du_changye_criticizes_reward','杜昌业批评凭言语合意授高官，担心以后难以奖赏功臣',11,'江州观察使','何以赏之！”',[('杜昌业','听说冯延鲁升官后，批评任官方式')],when='943年冯延鲁升官后，具体日期未载',place='南唐',note='仅记录杜昌业的批评，不当作已证此任命完全只因一句话。')
add('wei_cha_deputy_pivot','李璟任魏岑、查文徽为枢密副使',11,'未几，','皆为枢密副使。',[('唐主','任魏岑与查文徽为枢密副使'),('魏岑','获任枢密副使'),('查文徽','获任枢密副使')],when='943年上述任官不久，具体日期未载',place='南唐')
sup('wei_cha_deputy_pivot',11,'xinwudaishi-062-feng-name','魏岑、查文徽為副使。','《新五代史》也记魏岑与查文徽任枢密副使。','前句陈觉为枢密使确定副使职务，不提前录后续十二月政令。')
add('wei_attacks_chen_mourning','陈觉母亲去世期间，魏岑揭发他的过失，排斥他',11,'岑既得志，',None,[('陈觉','母亲去世，处于服丧期间'),('魏岑','在陈觉母亲去世时揭发其过失并排斥他')],when='943年魏岑获任枢密副使后，具体日期未载',place='南唐',note='过恶是史书描述被揭发内容，本段未列具体事情；母亲未具名不造人物，摈斥不自动写成朝廷已罢免。')
add('dingyuan_army_haozhou','南唐在濠州设置定远军',12,'唐置',None,[],when='943年三月条下，具体日期未载',place='濠州',note='设置军镇，不补节度使任命、编制人数或地点坐标。')
# 13: preserve distinct attack planning, execution and succession.
past=dict(year=None,when='刘弘度在位期间，具体年月未载',place='南汉')
add('bin_neglects_government','《资治通鉴》记刘弘度奢侈放纵，不亲理政务',13,'汉殇帝','不亲政事。',[('汉主','史书称其奢侈放纵、不亲理政务')],note='骄奢为史书评价，殇帝为后世谥号，主体复用刘弘度。',**past)
add('bin_drinks_during_mourning','刘岩尚未安葬时，刘弘度奏乐酣饮并夜间与倡女出行',13,'高祖在殡，','倮男女而观之。',[('汉主','在父亲尚未安葬时奏乐饮酒，夜间与倡女便服出行，让男女裸体供他观看')],note='高祖为南汉刘岩，不是后晋石敬瑭；在殡对应942年父亲死亡与安葬之间，但具体日期不补。',**past)
add('bin_kills_dissenters','史书记刘弘度杀死忤逆心意的身边人，旁人不敢劝谏',13,'左右忤意','无敢谏者；',[('汉主','史书称其杀死不合心意的身边人')],note='人数、被杀者身份及次数未载，不造具名死者。',**past)
add('bin_ignores_hongchang_wu','刘弘昌与吴怀恩多次劝谏，刘弘度不听',13,'惟越王','不听。',[('弘昌','与吴怀恩多次劝谏刘弘度'),('吴怀恩','任内常侍，与刘弘昌多次劝谏'),('汉主','没有听从两人的劝谏')],**past)
add('bin_searches_court_visitors','刘弘度猜忌弟弟们，宴会入门前命人对群臣宗室脱衣搜身',13,'常猜忌','然后入。',[('汉主','命宦官守门，对入宴的群臣宗室脱衣搜身')],note='未逐一列弟弟或搜身对象，不外推搜到武器或所有人均已涉谋反。',**past)
add('hongxi_uses_entertainment','刘弘熙想谋害刘弘度，以歌舞享乐取悦并助长其放纵',13,'晋王弘熙','以成其恶。',[('弘熙','准备对刘弘度下手，以歌舞享乐取悦他'),('汉主','受到刘弘熙安排的娱乐取悦')],note='欲图为企图，未发生杀害；成其恶为史书评价，保留来源归属。',**past)
add('fighters_train_jin_mansion','刘弘熙命陈道庠召五名力士到晋王府练习手搏',13,'汉主好手搏，','汉主闻而悦之。',[('弘熙','命陈道庠召力士到晋王府练习手搏'),('陈道庠','召刘思潮等五名力士练习手搏'),('刘思潮','在晋王府练习手搏'),('谭令禋','在晋王府练习手搏'),('林少强','在晋王府练习手搏'),('林少良','在晋王府练习手搏'),('何昌廷','在晋王府练习手搏'),('汉主','听说练习手搏而高兴')],year=None,when='943年三月杀害刘弘度前，训练开始年月未载',place='晋王府',note='五人姓名明载，只据此记录训练；不将所有训练者自动列为行凶动作已确认的参与人。')
add('changchun_banquet','刘弘度在长春宫与诸王宴饮、观看手搏，醉酒散宴',13,'丙戌，','汉主大醉。',[('汉主','在长春宫宴饮、看手搏并醉酒')],when='943年三月丙戌',place='长春宫',note='诸王未逐一具名，不默认所有已录宗室参加宴饮；手搏不添现代比赛规则。')
add('hongxi_orders_bin_killed','刘弘熙派陈道庠、刘思潮等扶刘弘度离席，并杀死他',13,'弘熙使','因拉杀之，',[('弘熙','派陈道庠、刘思潮等扶住并杀死刘弘度'),('陈道庠','奉命扶住并杀死刘弘度'),('刘思潮','奉命扶住并杀死刘弘度'),('汉主','醉酒后遭杀害')],when='943年三月丙戌罢宴后',place='南汉',note='拉杀不具体补扼颈或断肢等手法；新史寢门地点另引用，主书未给精确行凶门名。')
add('bin_attendants_killed','陈道庠、刘思潮等杀死刘弘度身边的人',13,'弘熙使','尽杀其左右。',[('陈道庠','杀死刘弘度身边的人'),('刘思潮','杀死刘弘度身边的人')],when='943年三月丙戌杀害刘弘度时',place='南汉',note='左右未列人数或姓名，不能用尽杀推定吴怀恩也遇害。')
add('hongchang_visits_chamber','刘弘昌次日率弟弟们到寝殿哭临，迎立刘弘熙',13,'明旦，','迎弘熙即皇帝位，',[('弘昌','率弟弟们到寝殿哭临，迎立刘弘熙'),('弘熙','受到刘弘昌等迎立')],when='943年三月丙戌次日早晨',place='南汉寝殿',note='临为哭临，并非进入寝殿称帝；不根据相邻干支推成另一个公历日期。诸弟未逐一具名。')
add('hongxi_accession_sheng','刘弘熙即位，更名刘晟，改元应乾',13,'迎弘熙','改元应乾。',[('弘熙','即皇帝位、更名晟并改元应乾')],when='943年三月丙戌次日',place='南汉',note='更名事实连接原刘弘熙主体，不新建刘晟；新史洪熙字形保留。')
add('hongchang_taiwei_marshal','刘弘熙任刘弘昌为太尉兼中书令、诸道兵马都元帅，知政事',13,'以弘昌','知政事，',[('弘熙','任刘弘昌为太尉兼中书令、诸道兵马都元帅'),('弘昌','受任诸职并知政事')],when='943年三月刘弘熙即位时',place='南汉')
add('honggao_deputy_marshal','刘弘熙任刘弘杲为副元帅，参与政事',13,'循王弘杲','参预政事。',[('弘熙','任刘弘杲为副元帅参与政事'),('弘杲','由循王任副元帅参与政事')],when='943年三月刘弘熙即位时',place='南汉')
add('assassins_rewarded','陈道庠、刘思潮等得到丰厚赏赐',13,'陈道庠及',None,[('陈道庠','刘弘熙即位后得到丰厚赏赐'),('刘思潮','刘弘熙即位后得到丰厚赏赐')],when='943年三月刘弘熙即位后',place='南汉',note='赏赐数额未给，不推其官职已获提升。')
bin_source='xinwudaishi-065-liu-bin-death';sheng_source='xinwudaishi-065-liu-sheng-accession'
sup('fighters_train_jin_mansion',13,bin_source,'陰遣陳道庠養勇士劉思潮、譚令禋、林少彊少良、何昌廷等，習為角觝以獻玢。','《新五代史》也列五名勇士，写训练角觝以献给刘玢。','林少彊与主书林少强对应；玢对应刘弘度，不把手搏角觝差异简化成现代特定项目。')
sup('hongxi_orders_bin_killed',13,bin_source,'玢醉起，道庠與思潮等隨至寢門拉殺之，','《新五代史》记陈道庠、刘思潮等随醉酒的刘玢到寝门杀死他。','新史补地点与时序，不把所有五位训练者动作逐一实证。',relation='adds')
sup('bin_attendants_killed',13,bin_source,'盡殺其左右。','《新五代史》也记尽杀刘玢身边的人。','未列死者与数量，不推吴怀恩死亡。')
sup('hongxi_accession_sheng',13,sheng_source,'晟，初名洪熙，封晉王。既弒玢，遂自立，改元曰應乾，','《新五代史》记刘晟原名洪熙，封晋王，杀刘玢后自立改元应乾。','主书迎立与新史自立两种叙述并列，不补新史没有的同日迎立细节。')
sup('hongchang_taiwei_marshal',13,sheng_source,'以洪昌為兵馬元帥，知政事，','《新五代史》也记刘洪昌任兵马元帅、知政事。','洪昌为刘弘昌字形异文；此句不补太尉和中书令。')
sup('honggao_deputy_marshal',13,sheng_source,'洪杲副元帥，','《新五代史》也记刘洪杲任副元帅。','洪杲对应刘弘杲，不从后文提前录入其被杀。')
sup('assassins_rewarded',13,sheng_source,'劉思潮等封功臣。','《新五代史》还记刘思潮等获封功臣。','只明确刘思潮等，不补所有人的具体爵号。',relation='adds')
claim('person',people['刘弘度'],'death_year','刘弘度于943年三月丙戌被杀。',13,'弘熙使道庠、思潮等掖汉主，因拉杀之，','承接本段丙戌宴会，既有主体与更名玢的事实已在942年录入，保持稳定key。')
claim('person',people['刘弘度'],'description','《新五代史》记刘玢被杀时年二十四，谥号殇。',13,'玢立二年，年二十四，謚曰殤。','立二年为跨年纪年，不推已满24个月；年龄按史载，不反推出生年。',source=bin_source,relation='adds')
claim('person',people['刘弘熙'],'name','刘弘熙即位后更名晟，即刘晟。',13,'迎弘熙即皇帝位，更名晟，改元应乾。','独立姓名事实连接同一主体，不更改已发布档案或新建人物。')
relationship('汉主','弘熙','兄长',13,'玢立二年，年二十四，謚曰殤。弟晟立。','新史明确晟为玢之弟，玢是已录刘弘度、晟是原刘弘熙；不另建反向弟弟重复边。',source=bin_source)
# 14–16: Min consort, eclipse and South Tang appointment.
add('shang_min_consort','王延羲纳尚保殷之女尚氏，立为贤妃',14,'闽主曦','立为贤妃。',[('曦','纳尚保殷之女并立为贤妃'),('贤妃尚氏','被王延羲纳入宫中，立为贤妃')],when='943年三月条下，具体日期未载',place='闽国',note='贤妃与皇后李氏是不同主体；不因妃位新建妻子关系或推婚礼日期。')
relationship('尚保殷','贤妃尚氏','父亲',14,'闽主曦纳金吾使尚保殷之女，立为贤妃。','原文明确父女，尚保殷任金吾使；不推姓尚即其他尚氏亲属。')
add('shang_influences_punishment','史书记王延羲酒醉时，按尚氏的意思杀人或赦免',14,'妃有殊色，',None,[('曦','酒醉时按尚氏的意思杀人或赦免'),('贤妃尚氏','受到宠爱，影响王延羲醉中的杀赦决定')],year=None,when='尚氏受宠期间的概述，具体年月未载',place='闽国',note='殊色、嬖为史书美貌与宠爱描述，未列具体杀赦对象，不添死者或次数。')
sup('shang_min_consort',14,'xinwudaishi-068-min-li-empress','賢妃尚氏有色而寵。','《新五代史》也记贤妃尚氏因姿容受到宠爱。','此句用于确认尚贤妃主体，不提前录后文皇后妒忌及944年杀王事件。')
add('april_solar_eclipse','《资治通鉴》记四月戊申朔发生日食',15,'夏，',None,[],when='943年四月戊申朔',place='观测地点未载',note='记史载日食，不据此补现代天文计算、观测范围或君主行为。')
add('jianxun_zhaowu','李璟任李建勋为昭武节度使，镇守抚州',16,'唐以',None,[('唐主','任李建勋为昭武节度使'),('李建勋','由中书侍郎、同平章事出任昭武节度使，镇守抚州')],when='943年四月条下，具体日期未载',place='抚州',note='唐主此处是新即位李璟，不再是前批李昪；不自动认为同平章事职衔此后全部免去。')
reviews={9:'己卯朔赵莹出任与桑维翰入朝为不同动作；旧纪补监修国史，旧纪附胡注与本纪正文分清，新史罢相不等免全部官。',10:'三月李璟正式即位、赦改元、韩熙载请求跨年、尊母立后、任官与两王改封分别录；直呼姓名与任职承诺按含义处理。常梦锡旧劝为追述，池州管束为概述日期为空。新史当前任命补证，后续秋季任命不提前。',11:'陈觉委任未具体职，五鬼是当时称呼、侵蠹为史评价；冯延鲁升官、杜昌业意见、两枢密副使和魏排陈分开。母亲不具名不造人，揭发内容不补。',12:'濠州定远军设置不补军额、将领和坐标。',13:'刘弘度玢、刘弘熙晟复用旧主体。殡中娱乐与猜忌为在位追述，训练开始未知日期为空；丙戌宴、杀君、杀左右、次日哭临迎立、更名改元与两任官奖励分开。五力士只明确训练，不把全部行凶动作强赋给所有人。新史寝门地点、年龄谥号和功臣为独立补证。林少强少良不造未明亲属；兄弟方向明确。',14:'尚氏与李皇后区分，父女明确；贤妃不改成皇后或妻子。醉中杀赦为概述，不造死者。新史仅补贤妃受宠，不提前后文杀王。',15:'四月戊申朔史载日食，不作现代换日及天文范围推算。',16:'唐主为李璟，李建勋昭武与镇抚州明确，不推未载职衔撤免。'}
assert not (P/'publication.json').exists()
for n in range(9,17):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=283,year=943,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,17)],next_paragraph=Q[17]['id'],next_volume=283,next_year=943,supplements=supplements,excluded_non_body=[],source_contexts=[dict(source_key='xinwudaishi-065-liu-sheng-accession',note='仅引继位、当前任官和封功臣，后续刘弘杲被杀及冬改元留后续连续段落。')],coverage='连续第9—16段，原57—64行；三月至四月及追述，后接第17段殷军攻福州。',source_issues_review='姓名异体、林少强与少彊、刘氏更名复用、日食原纪日均保原文；人物评价与发言者观点有标明，纸本待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,17)],plain_language_review='首次检查全部标题正文、人物介绍、参与角色、关系方向与事实说明。唐主已从李昪切换李璟，汉主为刘弘度，未知日期追述与计划、执行分开，原文保留。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
