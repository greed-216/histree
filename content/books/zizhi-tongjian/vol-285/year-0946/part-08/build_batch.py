# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 946 paragraphs 51–56."""
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
COMMIT='f475a8bdeb3fc70a41e5ca601f675229b6c6bfc4'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-285-946-captive-emperor','jiuwudaishi-089-sang-captive','xinwudaishi-009-946']:
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
main_sources = ['tongjian-285-946-captive-emperor']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p051-p056',
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
for n in range(51, 57):
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
        citation = f'卷285·后晋开运三年（946年十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_08_{len(B["claims"])+1:04d}'
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
ALIASES.update({'帝':'石重贵','契丹主':'耶律德光','太后':'永宁公主（石敬瑭妻）','延煦':'石延煦','延宝':'石延宝','王从珂':'李从珂','先帝':'石敬瑭','解里':'解里（契丹传诏者）','李筠':'李筠（后晋控鹤指挥使）'})
NEW_ALIASES={'解里（契丹传诏者）':['解裏（契丹傳詔者）'],'阎丕':['閻丕']}
NEW_DESCRIPTIONS={'解里（契丹传诏者）':'《资治通鉴》946年十二月记耶律德光派他向被拘的石重贵传话。该年八月另记一名契丹将解里被斩，两者身份无法直接统一，暂时分别建档，待异文和职务校核。生卒年未载。','阎丕':'景延广的从事。《新五代史》记946年末随景延广到封丘见耶律德光，一同被锁，景延广解释他只是因职随行后获释。生卒年、籍贯未载。'}
dec='946年十二月';j='jiuwudaishi-085-946-captive';sg='jiuwudaishi-089-sang-captive';nw='xinwudaishi-009-946';jg='xinwudaishi-029-jing-capture';sn='songshi-484-li-jun-name'
add('zhang_kills_sang','张彦泽在夜间杀死桑维翰',51,'是夕，','杀桑维翰。',[('张彦泽','杀死桑维翰'),('桑维翰','被张彦泽杀害')],when=dec+'是夕，具体纪日各书不同',place='大梁',note='承前段是夕，不能直接推为甲戌当夜；旧本纪甲戌夜、旧传十八日夜、新纪壬申分别登记。')
sup('zhang_kills_sang',51,j,'是夜，開封尹桑維翰、宣徽使孟承誨皆遇害。','《旧五代史》本纪在甲戌条下记桑维翰和孟承诲当夜遇害。','本纪与通鉴分叙孟、桑遇害不完全同序，保留纪日差异。',relation='conflicts',field='time_original')
sup('zhang_kills_sang',51,sg,'十八日夜，為彥澤所害，時年四十九。','《旧五代史》桑维翰传记他十八日夜被张彦泽杀害，时年四十九。','年龄按传记保留，不自行反算出生年；本纪与传记日期另列。',relation='conflicts',field='time_original')
sup('zhang_kills_sang',51,nw,'壬申，張彥澤犯京師，殺開封尹桑維翰。契丹滅晉。','《新五代史》本纪把入京、杀桑维翰和灭晋概述系于壬申。','不把概述日期覆盖通鉴分段时序或旧传纪日。',relation='conflicts',field='time_original')
claim('person','person_桑维翰','death_year','桑维翰在946年十二月被张彦泽杀害，具体日各书记载有差异。',51,span(51,'是夕，','杀桑维翰。'),'死亡年明确；不直接改动此前发布的人物档案。')
add('zhang_disguises_sang_suicide','张彦泽用带子缠住桑维翰颈部，向耶律德光谎报为自缢',51,'以带加颈，','云其自经。',[('张彦泽','伪装死状并报告自缢'),('桑维翰','尸体被伪装为自缢'),('契丹主','收到自缢报告')],when=dec+'桑维翰遇害后',place='大梁',note='先杀后伪称自缢，不把传报当真实死因。')
add('khitan_orders_sang_family_care','耶律德光称自己无意杀桑维翰，命优厚抚恤其家',51,'契丹主曰：',None,[('契丹主','否认有意杀桑，命抚恤其家'),('桑维翰','家属获命抚恤')],when=dec+'收到桑死报告后',place='契丹行营',note='无意杀为耶律德光本人表态，未由此判定全部责任归属。')
add('gao_fu_surrender_at_camp','高行周、符彦卿到契丹牙帐投降',52,'高行周、','牙帐降。',[('高行周','到契丹牙帐投降'),('符彦卿','到契丹牙帐投降')],when=dec+'入京后条下，具体日未载',place='契丹牙帐')
add('khitan_questions_fu_yangcheng','耶律德光因阳城战败责问符彦卿',52,'契丹主以','诘之。',[('契丹主','以此前阳城之战责问符彦卿'),('符彦卿','受到责问')],when=dec+'符彦卿投降后',place='契丹牙帐',note='阳城战为此前事件，复用人物、不重复创建战役。')
add('fu_explains_loyalty_is_released','符彦卿称当时只知尽力效忠晋主，耶律德光笑着释放他',52,'彦卿曰：',None,[('符彦卿','解释此前为晋主尽力，听候处置'),('契丹主','听后笑着释放符彦卿')],when=dec+'符彦卿受责问时',place='契丹牙帐',note='今日死生惟命是服从处置表态，未发生处死。')
add('shi_sons_return_with_letter','石延煦、石延宝从契丹牙帐返回，带回耶律德光给石重贵的手诏',53,'己卯，','赐帝手诏，',[('延煦','从契丹牙帐返回'),('延宝','从契丹牙帐返回'),('契丹主','赐石重贵手诏'),('帝','收到手诏')],when=dec+'己卯',place='契丹牙帐至大梁开封府')
sup('shi_sons_return_with_letter',53,j,'己卯，皇子延煦、延寶自帳中回，得敵詔慰撫，帝表謝之。','《旧五代史》同记己卯两位皇子从牙帐返回，获诏慰抚，石重贵上表谢恩。','与主书对应的行程、日期和谢恩并列引用。')
add('jie_li_delivers_food_promise','耶律德光派解里向石重贵传话，保证让他有饭可吃',53,'且遣解里','啖饭之所。”',[('契丹主','派使者传达慰抚'),('解里','向石重贵传话'),('帝','受到保证有饭可吃的慰抚')],when=dec+'己卯',place='大梁开封府',note='传话孙为政治称呼，不造血缘；传诏解里与八月已死同名将领暂分档。')
add('shi_relaxes_thanks','石重贵听到慰抚后稍感安心，上表谢恩',53,'帝心稍安，',None,[('帝','稍安心并上表谢恩')],when=dec+'己卯',place='开封府')
add('khitan_questions_seal_authenticity','契丹认为所献传国宝雕琢不精且不符史书记载，要求石重贵交出真宝',54,'契丹以','使献真者。',[('契丹主','诏问传国宝真伪，要求交真宝'),('帝','被要求解释宝玺来源')],when=dec+'两子返回后的记载，具体日未载',place='契丹行营与开封府',note='不与前史相应未具体说明尺寸文字，不补细节；疑伪为契丹判断。')
add('shi_explains_seal_remade','石重贵奏称旧传国宝可能随李从珂自焚损毁，所献是石敬瑭重新制作，契丹停止追问',54,'帝奏：',None,[('帝','解释献宝来历，否认隐匿'),('李从珂','在奏答中被提及自焚'),('先帝','在奏答中被说明为宝玺制作者'),('契丹主','停止追问')],when=dec+'宝玺真伪被诏问时',place='开封府与契丹行营',note='旧宝去向不知、俱烬是石重贵推测，不当实际出土或毁损已证；制作追述未强定946。')
sup('shi_explains_seal_remade',54,j,'先帝受命，旋制此寶，在位臣僚，備知其事。臣至今日，敢有隱藏','《旧五代史》也记录石重贵称石敬瑭受命后制作此宝，否认隐匿。','保留奏答性质，不新造确切制作年月或制作者工匠。')
add('shi_requests_roadside_welcome_rejected','石重贵打算和李太后到前路迎接耶律德光，张彦泽先报告，耶律德光不准',55,'帝闻','契丹主不许。',[('帝','打算与太后前往迎接'),('太后','被拟议一起迎接'),('张彦泽','事先报告迎接计划'),('契丹主','不准这一迎接安排')],when=dec+'闻耶律德光将渡河时',place='大梁至渡河前路',note='将渡为消息中的计划，不补实际渡河日。')
sup('shi_requests_roadside_welcome_rejected',55,j,'豈有兩個天子道路相見！今賜所佩刀子，以慰爾心。','《旧五代史》记拒见理由为不宜两个天子道路相见，并赐所佩刀子慰抚。','这是别书补充的答复，不能替换通鉴拒绝受降仪式的另一说辞。',relation='adds')
add('khitan_rejects_surrender_ritual','有关官员拟让石重贵衔璧牵羊、大臣载棺郊迎，耶律德光称是奇兵取京，拒绝仪式',55,'有司又欲','亦不许。',[('帝','被拟安排以降服仪式郊迎'),('契丹主','拒绝受降礼仪')],when=dec+'契丹主入京前',place='大梁郊外（计划地点）',note='舆榇是载棺示听罪，与真正死亡不同；礼仪没有获准，不写已实施。')
add('khitan_retains_jin_offices_rites','耶律德光诏令后晋文武官员照旧任职，朝廷制度采用汉礼',55,'又诏晋','并用汉礼。',[('契丹主','诏令官职如旧并沿用汉礼')],when=dec+'入京前诏令',place='后晋朝廷',note='记录诏令内容，不据此断言所有官员日后永久保职。')
add('khitan_rejects_imperial_procession','有关官员准备法驾迎接，契丹方面以统兵无暇采用太常仪卫为由拒绝',55,'有司欲备','皆却之。',[('契丹主','通过答复拒绝法驾仪卫安排')],when=dec+'入京前',place='大梁',note='答复中的吾主表明通过部属回复，未新造具名答复人。')
add('khitan_sends_troops_capture_jing','耶律德光此前到相州后，派兵赶往河阳捕景延广',55,'先是契丹主','捕景延广。',[('契丹主','在相州派兵捕景延广'),('景延广','成为抓捕对象')],when=dec+'追述耶律德光到相州时',place='相州至河阳',note='先是为追述，不把派兵放在仪礼拒绝之后。')
add('jing_meets_khitan_fengqiu','景延广来不及藏匿，到封丘见耶律德光',55,'延广苍猝','于封丘。',[('景延广','无暇逃藏，前往封丘'),('契丹主','在封丘见景延广')],when=dec+'契丹军追捕期间',place='封丘')
add('khitan_accuses_jing','耶律德光责问景延广导致双方君主失和，并追问十万横磨剑的说法',55,'契丹主诘','安在！”',[('契丹主','责问失和并追问旧日说辞'),('景延广','受到责问')],when=dec+'封丘相见时',place='封丘',note='因果为耶律德光指责，不当全部战争原因已证；十万剑为前言，不新造兵器清点。')
add('qiao_presents_record_jing_confesses','乔荣与景延广对质，出示当初记下的话；景承认八项后伏地请死，被锁',55,'召乔荣，',None,[('契丹主','召乔荣对质并锁景延广'),('乔荣','出示此前记下的话'),('景延广','承认八项，伏地请死后被锁')],when=dec+'封丘相见时',place='封丘',note='凡十条是质问总项，八筹是已承认八项；未写全部十项已服，不把请死当处决。')
sup('qiao_presents_record_jing_confesses',55,jg,'召喬瑩質其前言，延廣初不服，瑩從衣領中出所藏書，延廣乃服。','《新五代史》称乔莹从衣领中取出所藏记录，景延广才承认。','乔莹沿已有别名对应乔荣；纸条证据与既有前事衔接，不另造同名使者。',relation='adds')
event('yan_pi_chained_then_released','《新五代史》记阎丕随景延广到封丘，同被锁后获释',55,'乃與從事閻丕馳騎見德光於封丘，并丕見鎖。延廣曰：「丕，臣從事也，以職相隨，何罪而見鎖？」丕乃得釋。',[('阎丕','因职随行，同被锁后获释'),('景延广','解释阎丕只是随职而来'),('契丹主','听后释放阎丕')],source=jg,when=dec+'景延广到封丘时，具体日未载',place='封丘',note='补证只取拘捕和释放阎丕，不提前录传中陈桥自杀及后汉追赠。')
add('officials_stay_fengchan_last_day','后晋百官在十二月最后一天宿于封禅寺',56,'丙戌晦，',None,[],when=dec+'丙戌晦',place='封禅寺',note='百官是集体且本句未列人名，不猜名单；晦为月末，未自行换算公历。')
sup('officials_stay_fengchan_last_day',56,j,'丙戌晦，百官宿封禪寺。','《旧五代史》同记丙戌晦百官宿封禅寺。','月末纪日与地点一致。')
reviews={51:'杀桑、伪装死因、抚恤分记；通鉴是夕、旧本纪甲戌夜、旧传十八日夜、新纪壬申并列，不反算生年。',52:'投降、阳城旧战质问和释放分记，不重复战役；死生听命不是已死。',53:'两子返帐、解里传话、稍安谢恩；同名传诏者与八月已死契丹将暂分主体，孙是政治礼辞。',54:'宝真伪为契丹质疑；焚毁旧宝是石重贵推测，先帝制作追述不当946新制。',55:'迎见、受降仪式、法驾均为未获准计划；派兵捕景为先是追述，八项认供非十项全服，锁拘不是请死已执行。新史补阎丕获释，未提前录景死亡。',56:'月末宿寺，未编百官名单。'}
assert not (P/'publication.json').exists()
for n in range(51,57):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(51,57)],next_paragraph='zztj-v286-y0947-p001',next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷285原81—86行连续六段，946年最后六段；发布验证后才标年完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(51,57)],source_issues_review='桑死亡纪日异说并列；传诏解里与已死将领分档；宋史李筠原名片段已归档，对应前段的别名补充留待独立修订；八筹不写十项全服。',plain_language_review='逐项首次检查展示字段、身份时间与原文；主语明确，计划和执行、推测和事实区分；旧内容不扩大重写。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
