# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 51–53."""
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
specs=[(d.name,d,'184c40b49cc874d45b3c000680968fee2ef8f443','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-july-aftermath']:
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
main_sources = ['tongjian-281-937-july-aftermath','tongjian-281-937-min-and-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p051-p053',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-134-accession':'卷134·僭伪列传·李昪','xinwudaishi-062-accession':'卷62·南唐世家','xinwudaishi-068-wang-jigong':'卷68·闽世家'}
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
for n in range(51, 54):
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
    labels={'jiuwudaishi-134-accession':'卷134·僭伪列传·李昪','xinwudaishi-062-accession':'卷62·南唐世家','xinwudaishi-068-wang-jigong':'卷68·闽世家'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '九月至十月跨月条' if n==51 else '十月条下，含时日未明的后续记载'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'徐知证':'徐氏宗室。937年十月，徐诰即位后封他为江王。《新五代史》也记载这一封爵。',
'张延翰':'吴国、南唐官员。原任吴国同平章事，937年十月与张居咏、李建勋一同被任命为南唐同平章事。',
'张居咏':'吴国、南唐官员。原任吴国门下侍郎，937年十月与张延翰、李建勋一同被任命为南唐同平章事。',
'王继恭':'闽国官员，937年以威武节度使身份奉闽王命向后晋报告继位并请求设立邸舍。《资治通鉴》称他为闽王王继鹏的弟弟，《新五代史》称为儿子，亲属身份存在异说。'}
NEW_ALIASES={'徐知证':['徐知證'],'张延翰':['張延翰'],'张居咏':['張居詠'],'王继恭':['王繼恭']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=937 if name in ['武彦和','王氏（守卫军使王宏之子）'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=937, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='937年十月，具体日期未记载'
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
          '按《资治通鉴》及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
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
ALIASES.update({'唐主':'李昪','齐王诰':'李昪','吴主':'杨溥','让皇':'杨溥','璘':'杨璘','玠':'徐玠','琏':'杨琏','珙':'杨珙','王后宋氏':'齐王妃（徐知诰妻）','景通':'李璟','闽主':'王继鹏','继恭':'王继恭'})
# 51: transfer of seals precedes the October accession.
add('yang_lin_delivers_seals','杨溥命杨璘将皇帝玺绶奉送齐国',51,'丙寅，','奉玺绶于齐。',[('吴主','命江夏王杨璘奉送玺绶'),('璘','以江夏王身份奉送皇帝玺绶'),('齐王诰','齐国统治者，接受玺绶的一方')],when='937年九月丙寅',note='丙寅承接前段九月，不因同段后文十月而挪到十月；命奉玺绶不补运输抵达日。')
sup('yang_lin_delivers_seals',51,'xinwudaishi-062-accession','十月，溥遣攝太尉楊璘傳位於昪，','《新五代史》把杨溥派杨璘传位的记载列在十月，称杨璘为摄太尉。','《资治通鉴》奉玺绶列九月丙寅，《新五代史》十月传位为概述，月份与官衔分别保留，不把两书强定为同一运输日。',relation='conflicts',field='time_original')
add('li_bian_accession_jinling','徐诰在金陵即皇帝位并大赦、改元升元',51,'冬，十月，甲申，','国号唐。',[('齐王诰','在金陵即皇帝位，宣布大赦并改元升元')],when='937年十月甲申',place='金陵',description='徐诰在金陵即皇帝位，宣布大赦，改元升元。《资治通鉴》此处写国号唐；新旧《五代史》写初号齐，国号的时间记载存在差异。',note='即位为已发生，与八月诏禅位、此前劝进分别录入。徐诰统一主体为李昪，不把后来的复姓改名提前到本日。')
sup('li_bian_accession_jinling',51,'xinwudaishi-062-accession','十月，溥遣攝太尉楊璘傳位於昪，國號齊，改元昇元。','《新五代史》记十月传位，初立国号齐，改元升元。','国号齐与《资治通鉴》此处唐的差异保留。昇元和升元按各底本摘录，不因字形不同建立两个年号。',relation='conflicts')
sup('li_bian_accession_jinling',51,'jiuwudaishi-134-accession',source_span('jiuwudaishi-134-accession','偽吳天祚三年，','時晉氏天福二年也。'),'《旧五代史》记吴天祚三年即后晋天福二年，杨溥禅位后国号大齐，改元升元，定都金陵。','该书与《资治通鉴》当条唐国号有异；原文偽字为该书的立场用语，展示说明不用它对政权作价值判断。',relation='conflicts')
add('li_bian_posthumous_xu_wen_emperor','徐诰追尊徐温为武皇帝',51,'追尊太祖武王','曰武皇帝。',[('齐王诰','追尊徐温为武皇帝'),('徐温','原太祖武王，死后被追尊')],when='937年十月甲申即位后',note='太祖武王结合此前册齐和徐温追尊记录识别，不把死者作为当年在位皇帝。')
sup('li_bian_posthumous_xu_wen_emperor',51,'xinwudaishi-062-accession','追尊徐溫為忠武皇帝，','《新五代史》写追尊徐温为忠武皇帝。','《资治通鉴》写武皇帝，《新五代史》写忠武皇帝，尊号用字分别保留。',relation='conflicts')
add('xu_jie_crowns_yang_ranghuang','徐诰派徐玠奉册尊杨溥为让皇',51,'乙酉，','高尚思玄弘古让皇，',[('齐王诰','派右丞相徐玠奉册，仍在册文中自称受禅老臣'),('玠','奉册到杨溥处，呈上尊号'),('吴主','接受高尚思玄弘古让皇尊号的吴国旧主')],when='937年十月乙酉',note='上尊号与本人仍称老臣为册文内容；不推为徐诰仍在吴主之下执政。')
sup('xu_jie_crowns_yang_ranghuang',51,'xinwudaishi-062-accession',source_span('xinwudaishi-062-accession','昪以冊尊溥曰：','弘古讓皇帝。」'),'《新五代史》也记徐诰以册文尊杨溥为高尚思玄弘古让皇帝，自称受禅老臣知诰。','同一册尊事件；该句不列乙酉，不补成该书也明确此纪日。')
sup('xu_jie_crowns_yang_ranghuang',51,'jiuwudaishi-134-accession',source_span('jiuwudaishi-134-accession','昪乃冊楊溥為讓皇，','讓皇」云。'),'《旧五代史》也记册杨溥为让皇，册文尊号用字为高尚思元宏古让皇。','册文玄/元、弘/宏等版本字形保留，不悄悄改摘录。',relation='adds')
add('li_bian_preserves_wu_rituals','徐诰保留杨溥的生活礼遇，并沿用吴国礼制',51,'宫室、乘舆、','悉从吴制。',[('齐王诰','保留杨溥宫室、车辆和服用，并沿用吴国礼制'),('吴主','宫室、车辆及服用待遇仍照旧')],when='937年十月乙酉册尊条下',description='杨溥的宫室、乘舆和服用待遇保持原样。宗庙、历法正朔、徽章和服色仍依吴国制度。',note='原句宗庙等制度承南唐建国安排，与杨溥私人待遇并列；不能把悉从吴制推成吴政权仍存在。')
add('xu_zhizheng_jiang_prince','徐知证被封为江王',51,'丁亥，','徐知证为江王，',[('齐王诰','封徐知证为江王'),('徐知证','被封为江王')],when='937年十月丁亥')
sup('xu_zhizheng_jiang_prince',51,'xinwudaishi-062-accession','封徐氏子知證江王，知諤饒王。','《新五代史》也记徐氏子知证被封为江王、知谔被封为饶王。','封爵印证，不只凭徐氏子省称推定两人的长幼关系。')
add('xu_zhie_rao_prince','徐知谔被封为饶王',51,'丁亥，','徐知谔为饶王。',[('齐王诰','封徐知谔为饶王'),('徐知谔','被封为饶王')],when='937年十月丁亥')
sup('xu_zhie_rao_prince',51,'xinwudaishi-062-accession','封徐氏子知證江王，知諤饒王。','《新五代史》也记徐知谔被封为饶王。','复用既有徐知谔主体，原文知諤字形保留。')
add('yang_lian_hongnong_appointment','杨琏领平卢节度使、兼中书令并封弘农公',51,'以吴太子琏',None,[('齐王诰','授予吴国旧太子杨琏官爵'),('琏','领平卢节度使，兼中书令，封弘农公')],when='937年十月丁亥封爵条下',note='领节度使不推为本人已经到平卢驻军；原吴太子是此前身份。')
sup('yang_lian_hongnong_appointment',51,'jiuwudaishi-134-accession','仍以其子遙領平廬軍節度使，遷於海陵。','《旧五代史》记杨溥之子遥领平卢军节度使，并提到迁海陵。','遥领印证官职不等于到任；迁海陵为该书概述，不能定为十月丁亥已经迁居。',relation='adds')
# 52: speeches, appointments, and undated follow-up remain separate.
add('li_decheng_exposes_song_letter','李德诚在天泉阁宴会上出示宋齐丘阻止劝进的书信',52,'唐主宴群臣','齐丘顿首谢。',[('唐主','拿到书信却不看，表示相信三十年的旧交'),('李德诚','称宋齐丘不乐并出示阻止劝进的书信'),('宋齐丘','叩头向徐诰谢罪')],place='天泉阁',description='徐诰宴请群臣时，李德诚称只有宋齐丘对即位不满，并出示宋齐丘阻止自己劝进的信。徐诰拿着信没有看，表示相信三十年的旧交宋齐丘；宋齐丘叩头谢罪。',note='不满是李德诚当席的说法，三十年是徐诰的原话，不据此倒算唯一交往起始年。')
add('li_bian_renames_eastern_palaces','徐诰上表杨溥，更改东都宫殿名为仙经中的名称',52,'己丑，','皆取于仙经。',[('唐主','上表杨溥更改东都宫殿名'),('让皇','徐诰上表的对象')],when='937年十月己丑',place='东都（江都）',note='东都据前后江都上下文定位，不误认为后晋洛阳；原文未列具体改名，不造宫名。')
add('yang_pu_practices_bigu','杨溥常穿羽衣，练习辟谷',52,'让皇常服羽衣，','习辟穀术。',[('让皇','常穿羽衣，练习辟谷')],year=None,when='受禅后的生活记载，具体起止日期未载',description='杨溥退位后常穿羽衣，并练习辟谷，也就是以减少或停止谷物摄入为特点的道教修习。',note='常服和习为持续习惯，不把邻近己丑当作开始日期，也不推为从此完全不进食。')
add('wu_clan_titles_reduced','杨珙等十二名吴国宗室降爵为公，同时加官增邑',52,'辛卯，','而加官增邑。',[('唐主','调整吴国宗室的官爵和封邑'),('珙','原建安王，与另外十一名宗室一同降爵为公并加官增邑')],when='937年十月辛卯',note='十二人含杨珙，其他十一人未具名，不编姓名；降爵与加官增邑同时记录，不简化成全部待遇被削减。')
add('zhang_li_chancellors','张延翰、张居咏、李建勋被任命为南唐同平章事',52,'丙申，','并同平章事。',[('唐主','任命张延翰、张居咏、李建勋为同平章事'),('张延翰','由吴国同平章事转任南唐同平章事'),('张居咏','由门下侍郎被任命为同平章事'),('李建勋','由中书侍郎被任命为同平章事')],when='937年十月丙申',description='徐诰任命原吴国同平章事张延翰、门下侍郎张居咏和中书侍郎李建勋为南唐同平章事。',note='此前职务是本句背景，不能误记三人同时从无官起任。')
add('yang_pu_declines_li_memorials','杨溥写信辞谢徐诰继续向自己上表，徐诰未改变做法',52,'让皇以唐主上表，','唐主表谢而不改。',[('让皇','写信辞谢徐诰继续上表'),('唐主','上表谢复杨溥，但没有改变上表的做法')],when='937年十月受禅后的交往，具体日期未记载',note='辞之承上表，辞谢对象是表奏礼节，不写成杨溥拒绝全部宫殿改名。未列独立纪日，不套丙申。')
add('song_qiqiu_grand_situ','宋齐丘被加授大司徒',52,'丁酉，','加宋齐丘大司徒。',[('唐主','给宋齐丘加授大司徒'),('宋齐丘','被加授大司徒')],when='937年十月丁酉')
add('song_qiqiu_protests_edict','宋齐丘因未参与政事和诏词提及布衣旧交而表达不满',52,'齐丘虽为左丞相，','可不用老臣矣。”',[('宋齐丘','虽任左丞相却不参与政事，听到诏词后大声表达不满'),('唐主','宋齐丘不满所针对的君主')],when='937年十月丁酉加授大司徒条下',description='宋齐丘虽任左丞相，却不参与政事。他因诏词提到“布衣之交”而大声表示，自己还是布衣时徐诰只是刺史，如今徐诰成为天子，便可以不用自己了。',note='后半是宋齐丘的抗议原话，不作为徐诰已经下令罢免他的事实。')
add('song_qiqiu_returns_home_apology','宋齐丘回家请罪，徐诰亲笔诏书致歉但没有改命',52,'还家请罪，','亦不改命。',[('宋齐丘','回家请罪'),('唐主','亲笔诏书致歉，却没有改变任命')],when='937年十月丁酉加授引发争执之后',note='手诏谢之是君主答复，不误写成宋齐丘写手诏；不改命承加大司徒及未预政的安排，不造新的罢官令。')
add('song_proposes_yang_exile','宋齐丘建议迁走杨溥、疏远杨琏并断绝婚姻，徐诰拒绝',52,'久之，','唐主不从。',[('宋齐丘','建议迁杨溥到其他州、疏远杨琏并断绝婚姻'),('唐主','没有采纳这些建议'),('让皇','被提议迁往其他州'),('琏','被提议疏远并断绝婚姻')],year=None,when='十月争执之后久之，具体年月未载',description='过了一段时间，宋齐丘又上书建议把杨溥迁到其他州，疏远吴国旧太子杨琏，并断绝他的婚姻。徐诰没有采纳。',note='久之不硬定937年十月；电子本吴太琏省讹，结合同段吴太子琏及前文婚姻识别杨琏。建议没有执行，不新增迁居、离婚事实。')
add('song_queen_becomes_empress','徐诰立王后宋氏为皇后',52,'乙巳，','立王后宋氏为皇后。',[('唐主','立原王后宋氏为皇后'),('王后宋氏','由齐王王后成为皇后')],when='937年十月乙巳',note='复用此前未具名的齐王妃主体：此前册为王后，此处王后宋氏接同一位徐诰配偶；不因补出姓氏新建重复人物，也不改旧档案姓名。')
claim('person',people['齐王妃（徐知诰妻）'],'description','《资治通鉴》十月乙巳条记徐诰的王后姓宋，此时被立为皇后。',52,'乙巳，立王后宋氏为皇后。','与此前册王后身份相接，复用原齐王妃稳定主体，姓氏补为独立引用。')
relationship('唐主','王后宋氏','丈夫',52,'乙巳，立王后宋氏为皇后。','徐诰的王后宋氏与此前齐王妃为同一主体，复用已校核方向的丈夫关系。')
add('li_jing_wu_prince_appointments','徐景通被任命为诸道副元帅等职并封吴王',52,'戊申，',None,[('唐主','任命徐景通为诸道副元帅等职并封吴王'),('景通','由诸道都统、判元帅府事被任命为诸道副元帅、判六军诸卫事、太尉、尚书令、吴王')],when='937年十月戊申',description='徐诰将原任诸道都统、判元帅府事的徐景通任命为诸道副元帅、判六军诸卫事、太尉、尚书令，并封吴王。徐景通与后来的李璟是同一人。',note='复用李璟主体；徐景通仍是此时名字，十一月更名另按下一段处理。')
sup('li_jing_wu_prince_appointments',52,'xinwudaishi-062-accession','封子景為吳王，','《新五代史》也记徐诰封儿子景为吴王。','同人使用既有李璟主体，景是该书省称，不另建李景。')
relationship('唐主','景通','父亲',52,'封子景為吳王，','《新五代史》明示子景，复用已有李昪是李璟父亲的方向与稳定key。',source='xinwudaishi-062-accession')
# 53: no contradictory kinship edges are asserted as settled facts.
add('wang_jigong_reports_min_accession','王继鹏命王继恭向后晋报告继位，并请求设邸舍',53,'闽主',None,[('闽主','命威武节度使王继恭向后晋报告自己继位并请求设立邸舍'),('继恭','奉命向后晋上表报告闽王继位并请求在后晋都城设邸舍')],description='王继鹏命威武节度使王继恭向后晋上表，报告自己的继位，并请求在后晋都城设立邸舍。《资治通鉴》称王继恭为其弟，《新五代史》称为其子，亲属身份待进一步校核。',note='报告的是闽王继位，不是王继恭即位；设邸为请求，不写成后晋已准许或邸舍已建成。')
claim('person',people['王继恭'],'description',NEW_DESCRIPTIONS['王继恭'],53,Q[53]['text'],'《资治通鉴》本句明确威武节度使、上表行动及其弟；另一书父子异说另附，不先建立确定的弟弟或父子图谱边。')
claim('person',people['王继恭'],'description','《新五代史》闽世家称王继恭为王昶之子，并记后晋册他为临海郡王。',53,'晉天福二年，昶遣使朝貢京師，高祖遣散騎常侍盧損冊昶閩王，拜其子繼恭臨海郡王。','王昶为已有王继鹏的别名；该书其子与《资治通鉴》其弟冲突，不把两种亲属边同时设为确定关系。册封为同年补证，未列月份，不套十月纪日。',source='xinwudaishi-068-wang-jigong',relation='conflicts')
# Initial prose and fact check, supported profiles for every new person.
for name,n,start,end in [('徐知证',51,'丁亥，','徐知谔为饶王。'),('张延翰',52,'丙申，','并同平章事。'),('张居咏',52,'丙申，','并同平章事。')]:
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'新人物简介只使用本句明确身份与行动，生卒、家世无证据的部分留空。')
reviews={51:'九月丙寅奉玺绶与十月甲申即位、乙酉册尊及礼制、丁亥封爵分开。主书国号唐与新旧五代史初号齐并列；不将后来的复姓李及改名提前。太祖武王结合前文复用徐温，尊号差异保留。杨琏领平卢不推到任。',52:'宴会言论归说话者；三十年不倒算确切始交年。己丑东都宫名、辛卯宗室降爵但加官增邑、丙申三宰相、丁酉宋加司徒、乙巳王后宋氏、戊申景通任官分开。辟谷习惯、久之后续建议日期不明留null；建议迁杨溥和断婚未获采纳。王后宋氏复用原齐王妃，同人父亲、丈夫关系复用既有方向。',53:'王继恭奉闽王命报告闽王继位并请邸，不能当本人即位或邸已设。主书其弟与新史其子冲突，各附独立出处，暂不新增确定亲属边。'}
assert not (P/'publication.json').exists()
for n in range(51,54): ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(51,54)],next_paragraph=Q[54]['id'],next_volume=281,next_year=937,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第51—53段，原文件56—58行；九月奉玺绶、十月即位及封爵、南唐初期任官与吴宗室安排、宋齐丘争执及后续建议、闽国报告继位与请求设邸。937年未完成。',source_issues_review='逐行核对原文及导出片段；新旧五代史传主和卷号已核。国号唐/齐、杨璘九月奉玺绶/十月传位、尊号用字、王继恭弟/子分别保留。宋氏复用既有齐王妃，不按姓氏新增主体；吴太琏电子疑字依前文吴太子琏识别，不改底本。纸本和版本字形待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(51,54)],plain_language_review='首次录入逐条自查新增标题、人物简介、角色、事件说明、关系和事实解释。言论归说话者，命令和请求不写成执行完成，未知时日留空；引用保持底本原字。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
