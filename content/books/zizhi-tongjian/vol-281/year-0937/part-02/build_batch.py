# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 9–12."""
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
specs=[(d.name,d,'a7d3fe25','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-opening']:
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
main_sources = ['tongjian-281-937-opening','tongjian-281-937-xi-aftermath','tongjian-281-937-wuyue']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p009-p012',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-095-wu-luan':'卷95·吴峦传','xinwudaishi-029-wu-luan':'卷29·吴峦传','jiuwudaishi-095-zhai-zhang':'卷95·翟璋传','liaoshi-003-wu-luan':'卷3·太宗纪·天显十二年','liaoshi-076-zhang-li':'卷76·张砺传','jiuwudaishi-076-qian-death-report':'卷76·晋高祖纪·天福二年'}
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
for n in range(9, 13):
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
    labels={'jiuwudaishi-095-wu-luan':'卷95·吴峦传','xinwudaishi-029-wu-luan':'卷29·吴峦传','jiuwudaishi-095-zhai-zhang':'卷95·翟璋传','liaoshi-003-wu-luan':'卷3·太宗纪·天显十二年','liaoshi-076-zhang-li':'卷76·张砺传','jiuwudaishi-076-qian-death-report':'卷76·晋高祖纪·天福二年'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '二月条下（含追叙及三月事）'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'杨璪':'吴国宜阳王。937年受杨溥派遣，前往西都册命齐王徐知诰。',
'齐王妃（徐知诰妻）':'徐知诰担任齐王时的王妃。937年在吴国册命齐王的记载中被册为王后；此段没有记载她的姓名。',
'吴峦':'大同军节度判官。沙彦珣被契丹扣留后，他被推举主持云州事务，并闭城拒守。',
'郭崇威':'应州马军都指挥使，金城人。937年条中记载他不愿臣服契丹，独自南归。',
'翟璋':'威塞节度使。契丹要求他在新州筹集十万缗犒军钱。',
'去诸（西奚王）':'奚王。因不满契丹的统治，率部西迁妫州，依附刘仁恭父子，其部被称为西奚。',
'李绍威（西奚王）':'西奚王去诸的儿子，原名扫刺。李存勖灭刘守光后，赐他姓李、名绍威。',
'逐不鲁（契丹）':'契丹人。获罪后投奔西奚王李绍威，得到收留。其姐姐嫁给李绍威。',
'逐不鲁之姊（李绍威妻）':'逐不鲁的姐姐，嫁给西奚王李绍威。史书在此段没有记载她的姓名。',
'拽剌（西奚王）':'西奚王李绍威的儿子，在父亲去世后继位。耶律德光从上党北归时，他前往迎接并归降。',
'高彦英（契丹通事）':'契丹通事。张砺逃走后，耶律德光责备高彦英没有妥善照顾张砺，并处罚了他。',
'钱元㺷（吴越王少子）':'钱镠的少子。《资治通鉴》记载他拥有军功，后掌管吴越土客马步军。937年三月被钱元瓘召入宫中后杀死。姓名在本段中也写作元珪，版本与同名辨认仍待校核。'}
NEW_ALIASES={n:[] for n in NEW_DESCRIPTIONS}
NEW_ALIASES.update({'李绍威（西奚王）':['扫刺','扫剌','李绍威'],'钱元㺷（吴越王少子）':['钱元珪','元珪','元㺷']})
ALIASES.update({'契丹主':'耶律德光','元瓘':'钱传瓘','钱元瓘':'钱传瓘','元珦':'钱传珦','钱元珦':'钱传珦','扫刺':'李绍威（西奚王）','去诸':'去诸（西奚王）','拽剌':'拽剌（西奚王）','逐不鲁':'逐不鲁（契丹）','元珪':'钱元㺷（吴越王少子）'})



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
    if when is None:when='937年二月条下，具体日期未记载'
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
add('yang_zao_qi_investiture','杨溥派杨璪册命齐王徐知诰',9,'戊子，','册命齐王；',[('吴主','派宜阳王杨璪前往西都册命齐王'),('杨璪','前往西都册命齐王徐知诰'),('徐知诰','接受册命的齐王')],when='937年二月戊子',place='吴国西都',note='宜阳王璪补吴宗室姓杨；西都依本段名称记录，地理坐标未核。此为齐王册命，不是十月受禅。')
add('qi_accepts_and_amnesty','徐知诰接受册命并赦免境内罪人',9,'王受册，','赦境内。',[('徐知诰','接受齐王册命并发布境内赦令')],when='937年二月戊子',note='赦免范围沿“境内”，没有推成吴国全国赦免。')
add('qi_queen_investiture','齐王妃被册为王后',9,'册王妃',None,[('齐王妃（徐知诰妻）','由齐王妃被册为王后')],when='937年二月戊子',note='本段未载王妃姓名，使用身份限定主体，待他书证明后再补名，不凭常识直接命名。')
relationship('徐知诰','齐王妃（徐知诰妻）','丈夫',9,Q[9]['text'],'“王妃”对应本段齐王徐知诰，建立丈夫指向妻子的关系。')
add('qian_yuanxiang_deposed','钱元瓘将弟弟钱元珦废为庶人',10,'吴越王',None,[('钱元瓘','将弟弟钱元珦废为庶人'),('钱元珦','原任顺化节度使、同平章事，被废为庶人')],note='两人复用旧名钱传瓘、钱传珦的主体；没有根据获罪一词补出具体罪名。')
relationship('钱元瓘','钱元珦','兄长',10,Q[10]['text'],'“元瓘之弟”明确长幼，兄长方向为钱传瓘指向钱传珦。')
# The long paragraph mixes return from Shangdang with earlier Xi history and later aftermath.
def a11(code,title,start,end,actors,**kw):
 kw.setdefault('year',None);kw.setdefault('when','937年二月条中记述，确切发生日期未单独记载')
 return add(code,title,11,start,end,actors,**kw)
a11('sha_detained','沙彦珣出迎契丹军，被耶律德光扣留','契丹主自上党归，','不使还镇。',[('契丹主','经过云州时扣留出迎的沙彦珣'),('沙彦珣','以大同节度使身份出迎，随后被扣留')],place='云州',note='TXT姓名有私用字，同书校读及新旧吴峦传均作沙彦珣，复用既有主体。南归发生在936年末至937年初的交界，不凭条目年强定确日。')
sup('sha_detained',11,'jiuwudaishi-095-wu-luan','及契丹還塞，彥珣出城迎謁，尋為所擄。','《旧五代史》吴峦传也记载沙彦珣出迎后被契丹扣留。','传中前文明确沙彦珣，姓名与大同职务链一致。')
sup('sha_detained',11,'tongjian-281-937-collation','大同節度使沙彥珣出迎，契丹主留之，不使還鎮。','同书另一电子版本的姓名作沙彦珣。','只用于修复展示姓名的缺字，原TXT的私用字保持不变；这不是独立史书补证。',relation='adds')
a11('wu_refuses_khitan','吴峦被推举主持云州，闭城拒绝契丹命令','节度判官吴峦','闭城不受契丹之命，',[('吴峦','向守城者表明拒绝臣服契丹，被推举主持州事并闭城拒守')],place='云州',note='原引语是吴峦的价值判断，不当作本站对族群的评价。城中推举不等于朝廷已任命正式节度使。')
sup('wu_refuses_khitan',11,'xinwudaishi-029-wu-luan','城中推巒主州事，巒即閉門拒守，契丹以兵圍之。','《新五代史》也记载城中推举吴峦主持州事并拒守。','未把推举职务写成正式节度使任命。')
a11('khitan_fails_yunzhou','史书记载契丹进攻云州，未能攻下','契丹攻之，','不克。',[('吴峦','守卫云州，抵抗契丹进攻')],place='云州',note='《通鉴》本句记未攻克，不据此抹去他书后来投降或解围的记载。')
sup('khitan_fails_yunzhou',11,'jiuwudaishi-095-wu-luan','契丹大怒，攻之，半歲不能下。高祖致書於契丹，乃解圍而去。','《旧五代史》称契丹攻城半年未下，石敬瑭致书后契丹解围。','半年是围城时长，不反推准确开战日；解围为另一独立事件。',relation='adds')
sup('khitan_fails_yunzhou',11,'xinwudaishi-029-wu-luan','契丹圍之凡七月。','《新五代史》记围城七个月。','与《旧五代史》的半年有差异，分别保留，不换算出确定开始月份。',relation='conflicts',field='time_original')
sup('khitan_fails_yunzhou',11,'liaoshi-003-wu-luan','庚申，上親征，至城下諭之，巒降。','《辽史》太宗纪记天显十二年正月庚申，耶律德光到城下劝谕，吴峦投降。','《辽史》记投降，新旧五代史记拒守后解围，结局和时间线存在差异；不将两种说法默认为同一过程。',relation='conflicts')
event('shi_requests_yunzhou_relief','新旧五代史记石敬瑭致书契丹，云州得到解围',11,'高祖致書於契丹，乃解圍而去。',[('帝','致书契丹，请其解围'),('吴峦','其守卫的云州得到解围')],source='jiuwudaishi-095-wu-luan',year=None,when='吴峦守云州后的经历，传记未载具体日期',place='云州',note='独立补录书信和解围，不把围城时长当日期；吴峦此时后续任官异文另保留。')
E['shi_requests_yunzhou_relief']='event_zztj_281_0937_shi_requests_yunzhou_relief'
sup('shi_requests_yunzhou_relief',11,'xinwudaishi-029-wu-luan','高祖義巒所為，乃以書告契丹，使解兵去。','《新五代史》也记载石敬瑭致书契丹使其解围。','这句不等于两书围城时长完全一致。')
a11('guo_chongwei_returns','郭崇威不愿臣服契丹，独自南归','应州马军','挺身南归。',[('郭崇威','以应州马军都指挥使身份独自南归')],place='应州至南方',note='金城是籍贯；郭崇威与郭威不因名字相近合并，南归目的地未明。')
a11('zhai_raises_army_money','耶律德光命翟璋筹集十万缗犒军钱','契丹主过新州，','犒军钱十万缗。',[('契丹主','命翟璋筹集犒军钱'),('翟璋','被要求在新州筹集十万缗犒军钱')],place='新州',note='十万缗是征集要求，不等于已经全额收齐。')
sup('zhai_raises_army_money',11,'jiuwudaishi-095-zhai-zhang','時契丹大軍歸國，遣璋於管內配率犒宴之資，須及十萬緡，山後地貧，民不堪命。','《旧五代史》也记要求十万缗，并称当地贫困，百姓难以承担。','保存史家对民生的描述，不增加具体户数和完成额度。',relation='adds')
a11('aba_overtakes_tribes','史书追述阿保机强盛时室韦、奚等部受其控制','初，契丹主阿保机','皆役属焉，',[('耶律阿保机','强盛时期使室韦、奚等部役属')],when='追述阿保机时期，具体年份未记载',note='第三族名在TXT中为私用字，同书校读作霫；不据此建立未核边界或人口数据。')
sup('aba_overtakes_tribes',11,'tongjian-281-937-collation','室韋、奚、霫皆役屬焉，','同书另一电子版本中，缺失的第三个族名作霫。','保留原TXT缺字，用固定修订进行字形校读，不算独立史书确证。',relation='adds')
a11('quzhu_moves_west','奚王去诸率部西迁妫州，依附刘仁恭父子','奚王去诸','号西奚。',[('去诸','因不满契丹统治，率部西迁妫州'),('刘仁恭','其父子政权接受西迁奚部依附')],when='追述刘仁恭父子在幽州时期，确年未记载',place='妫州',note='父子所指政权范围，不认定父子都在迁徙现场；“依”不建立没有证据的私人盟友关系。')
a11('saoci_succeeds','去诸去世，儿子扫刺继位','去诸卒，','子扫刺立。',[('去诸','去世的奚王'),('扫刺','父亲去世后继位')],when='追述西奚王位传承，具体年份未记载')
relationship('去诸','扫刺','父亲',11,span(11,'去诸卒，','子扫刺立。'),'“子扫刺”明确父子关系，去诸指向李绍威。')
a11('saoci_named_li','李存勖灭刘守光后，赐扫刺姓李、名绍威','唐庄宗灭刘守光，','名绍威。',[('李存勖','在灭刘守光后给扫刺赐姓名'),('扫刺','获赐姓名李绍威')],when='追述李存勖灭刘守光之后的经历，赐名日期未记载',note='扫刺、扫剌与李绍威在同段叙事中为同一人，保留异写，灭刘守光只作背景不重复创建其旧事件。')
a11('shaowei_marriage','李绍威娶逐不鲁的姐姐','绍威娶','之姊。',[('扫刺','娶契丹逐不鲁的姐姐'),('逐不鲁之姊（李绍威妻）','嫁给李绍威')],when='追述西奚王婚姻，具体年份未记载')
relationship('扫刺','逐不鲁之姊（李绍威妻）','丈夫',11,span(11,'绍威娶','之姊。'),'原文明示婚姻；丈夫方向为李绍威指向其妻。')
relationship('逐不鲁之姊（李绍威妻）','逐不鲁','姐姐',11,span(11,'绍威娶','之姊。'),'“逐不鲁之姊”明确长幼，姐姐指向逐不鲁；不补姓名。')
a11('zhubulu_flees_xi','逐不鲁获罪于契丹，投奔李绍威并获收留','逐不鲁获罪','绍威纳之；',[('逐不鲁','获罪于契丹后投奔李绍威'),('扫刺','收留逐不鲁')],when='追述逐不鲁投奔西奚，具体年份未记载',note='没有交代所犯罪名，不推成刑事判决或确定的争权原因。')
a11('khitan_fails_xi','契丹因李绍威收留逐不鲁而进攻，未能攻下','契丹怒，','攻之，不克。',[('扫刺','其政权受到契丹进攻')],when='追述收留逐不鲁后的战争，具体年份未记载',note='与前面的云州守城为两场不同战事。')
a11('yela_succeeds','李绍威去世，儿子拽剌继位','绍威卒，','子拽剌立。',[('扫刺','去世的西奚王'),('拽剌','父亲去世后继位')],when='追述西奚王位传承，具体年份未记载')
relationship('扫刺','拽剌','父亲',11,span(11,'绍威卒，','子拽剌立。'),'明确父子关系，李绍威指向拽剌；拽剌加西奚王身份限定，避免与同名契丹使臣混同。')
a11('yela_submits','拽剌迎接北归的耶律德光并归降','及契丹主德光','拽剌迎降，',[('拽剌','迎接耶律德光并归降'),('契丹主','自上党北还，接受拽剌归降')],place='西奚',note='迎降不等于双方建立终身联盟。')
a11('khitan_disperses_remains','耶律德光命掘出李绍威和逐不鲁的遗骨，磨碎扬散','时逐不鲁亦卒，','硙而扬之。',[('契丹主','责称李绍威和逐不鲁辜负自己，并下令处置其遗骨'),('扫刺','去世后遗骨被掘出扬散'),('逐不鲁','去世后遗骨被掘出扬散')],description='史书记载，耶律德光称拽剌无罪，却责备已经去世的李绍威和逐不鲁，命人掘出他们的遗骨、磨碎并扬散。',note='这是对已经去世者遗骨的处置，不记录为当场杀死两人；指责是耶律德光的言辞。')
a11('xi_people_flee','史书称奚人畏惧契丹统治，多有逃叛','诸奚畏','多逃叛。',[],note='史书记载的概述不换算成迁徙人数，也不假定所有奚人一致行动。')
a11('khitan_promises_zhai_return','耶律德光许诺让翟璋卸任南归','契丹主劳翟璋','令汝南归。”',[('契丹主','许诺为翟璋安排接替者并让他南归'),('翟璋','获得南归许诺')],note='这是许诺，与实际离开分开；后文记载他最终仍被留下。')
a11('zhai_requests_return','翟璋上表请求回朝','己亥，','璋表乞征诣阙。',[('翟璋','上表请求回朝')],year=937,when='937年二月己亥奏表；其他追叙不据此定日',note='本段己亥为上表日期，不能用来给前后所有事件定日。')
a11('zhai_campaigns_retained','翟璋讨伐叛奚并攻云州有功，仍被契丹留下','既而契丹遣璋','留不遣璋，',[('契丹主','派翟璋出兵，之后仍不让他南归'),('翟璋','率兵讨伐叛奚、进攻云州，之后被留')],when='己亥奏表之后的经历，具体起止日期未记载',place='奚部、云州',note='记有功不等于攻克云州，不把战果外推。')
sup('zhai_campaigns_retained',11,'jiuwudaishi-095-zhai-zhang','及委璋平叛奚、圍雲州皆有功，故留之不遣。','《旧五代史》也记翟璋平叛奚、围云州有功，因此被留。','原书使用围云州，不新增攻克云州事实。')
a11('zhai_dies_after_retention','翟璋被留在契丹后郁郁不乐，后来去世','璋郁郁','而卒。',[('翟璋','被留下后郁郁不乐，后来去世')],when='被留后的经历，死亡年份未明确',note='同段后续死亡没有确年，人物死年保持空值。')
sup('zhai_dies_after_retention',11,'jiuwudaishi-095-zhai-zhang','璋郁郁不得志，遇疾尋卒焉。','《旧五代史》补充翟璋失意后患病，不久去世。','没有具体死亡年份，不能据编年条目直接填937年。',relation='adds')
a11('zhang_li_escape_capture','张砺从契丹逃走，后被追兵抓回','张\ue3ff厉自契丹逃归，','为追骑所获，',[('张砺','从契丹逃走后被追兵抓回')],note='TXT“张”后为缺字，按同书校读和《辽史》张砺传确认姓名；原文缺字不改写。')
sup('zhang_li_escape_capture',11,'liaoshi-076-zhang-li','未幾，謀亡歸，為追騎所獲。','《辽史》张砺传也记载他逃归后被追兵抓回。','传首张砺与后文高彦英通事、责问及处罚链一致，确认同人。')
a11('zhang_li_explains','张砺向耶律德光解释自己不适应契丹生活','契丹主责之曰：','愿早就戮。”',[('契丹主','责问张砺为何逃走'),('张砺','自陈饮食衣服不适应，并请求处死')],description='耶律德光责问张砺为何离开。张砺说自己是中原人，饮食衣服与当地不同，生不如死，愿被处死。这是张砺当时的答话，并非他已被处死。')
sup('zhang_li_explains',11,'liaoshi-076-zhang-li','礪對曰：「臣不習北方土俗，飲食居處，意常郁郁，以是亡耳。」','《辽史》记张砺答称不习惯北方风俗、饮食和居处，因此逃走。','两书保存不同措辞；《辽史》此处没有请求处死，不拼接成同一逐字引语。',relation='adds')
a11('khitan_punishes_interpreter','耶律德光责罚高彦英，并向张砺道歉','契丹主顾通事高彦英','笞彦英而谢\ue3ff厉。',[('契丹主','责备并处罚高彦英，向张砺道歉'),('高彦英（契丹通事）','因没有妥善照顾张砺受到处罚'),('张砺','得到耶律德光的道歉')],note='“谢”依责通事与善遇上下文解释为道歉，不译为授予官职。')
sup('khitan_punishes_interpreter',11,'liaoshi-076-zhang-li','遂杖彥英而謝礪。','《辽史》也记处罚高彦英并向张砺道歉。','高彦英为通事，使用身份限定主体，不凭同姓推亲属。')
a11('zhang_li_candid_advice','史书称张砺直言尽忠，受到耶律德光重视','\ue3ff厉事契丹主甚忠直，',None,[('张砺','遇事直言，受到耶律德光重视'),('契丹主','重视张砺的直言')],when='概述张砺在契丹期间的表现，未记起止年份',note='忠直和重视属于史家的概述，不认作具体某日新任命。')
# Qian family politics: anonymous reports and the actual deaths are kept separate.
add('qian_yuanxu_early_rewards','钱镠因少子元㺷的军功赏赐兵器',12,'初，吴越王','镠赐之兵仗。',[('钱镠','因少子的军功赏赐兵器'),('元珪','因军功获得钱镠赏赐')],year=None,when='追述钱镠在世时的经历，具体年份未记载',note='底本姓名含私用字，同书校读作元㺷；与同段元珪的叙事连续，原字保留。与旧档案钱传球是否同人尚未确证，暂不合并。')
sup('qian_yuanxu_early_rewards',12,'tongjian-281-937-collation','初，吳越王鏐少子元㺷數有軍功，鏐賜之兵仗。','同书另一电子版本将这位吴越王少子的名字写作元㺷。','用于缺字校读；本段其他句写元珪，名称仍待纸本核查，不与早年钱传球直接合并。',relation='adds')
add('qian_yuanxu_military_power','钱元瓘即位后，元㺷掌军并增置兵器',12,'及吴越王','国人多附之。',[('钱元瓘','即位后的吴越王'),('元珪','掌管土客马步军，增置兵器并得到许多人依附')],year=None,when='钱元瓘即位后至937年三月之前的经历，具体日期未载',description='史书记载，钱元瓘即位后，元㺷任土客马步军都指挥使、静江节度使并兼中书令。他增置兵器至数千，许多人依附他。',note='静江为此书官衔写法，《旧五代史》作静海，差异另存；“数千”指兵仗，不换算成士兵人数。')
add('qian_requests_disarm','钱元瓘要求元㺷交出兵器、到温州任职，遭到拒绝',12,'元瓘忌之，','元珪不从。',[('钱元瓘','派人劝元㺷交出兵器并出判温州'),('元珪','拒绝交出兵器和出判温州的要求')],year=None,when='937年三月杀人前的经历，具体日期未载',note='这是提出要求和拒绝，不记录为已经完成调任温州。')
add('qian_temple_report','铜官庙吏报告祈求主掌吴越及秘密联络之事',12,'铜官庙吏','与兄元珦谋议。',[('钱元瓘','收到铜官庙吏的报告'),('元珪','报告涉及其祈求主掌吴越及秘密联络'),('钱元珦','被报告与弟弟秘密谋议')],year=None,when='937年三月杀人前的报告，具体日期未载',description='铜官庙吏向钱元瓘报告，称元㺷遣亲信祈求主掌吴越，并以蜡丸通过水窦秘密联络哥哥元珦。此处保留为告发者的说法。',note='原句“告元瓘遣亲信”省略告发内容主语，按随后元珪与其兄叙事解释，但不当作独立证明谋反成立的证据。')
add('qian_yuanxu_killed','钱元瓘召元㺷入宫，左右称他藏刃并将他杀死',12,'三月，戊午，','即格杀之；',[('钱元瓘','召元㺷入宫赴宴'),('元珪','被召入宫后遭杀害')],when='937年三月戊午',place='吴越宫中',description='钱元瓘派使者召元㺷到宫中赴宴。元㺷到后，左右称有刀刃从其怀袖中掉出，随即将他杀死。藏刃之说是左右的报告。',note='不将左右报告自动认定为已查实的刺杀企图。')
sup('qian_yuanxu_killed',12,'jiuwudaishi-076-qian-death-report','七月辛亥，兩浙錢元瓘奏：「弟吳越士客馬步諸軍都指揮使、靜海軍節度使元球，非時入府，欲謀為亂，腰下搜得匕首，已誅戮訖。」詔削元球在身官爵。','《旧五代史》记七月辛亥钱元瓘奏称弟弟元球入府谋乱，搜出匕首后已被杀，并诏削官爵。','月份为奏报而不是独立杀人日；人物名作元球、官衔作静海，与《通鉴》有异写。仅登记同一杀事的候选补证，尚不据此合并既有钱传球主体。',relation='conflicts')
add('qian_yuanxiang_killed','钱元珦同时被杀',12,'并杀元珦。','并杀元珦。',[('钱元珦','在弟弟被杀时同时遭杀害')],when='937年三月戊午',note='与二月废为庶人为两个不同阶段，原文未说明具体执行者姓名。')
relationship('钱元珦','元珪','兄长',12,span(12,'又为蜡丸','与兄元珦谋议。'),'“兄元珦”明确长幼，钱传珦指向钱元㺷，不反建重复弟弟边。')
add('qian_renjun_stops_inquiry','钱仁俊劝钱元瓘停止追究相关将吏，钱元瓘接受',12,'元瓘欲按',None,[('钱元瓘','原想追究关联将吏，后接受钱仁俊的建议'),('钱仁俊','引用历史事例，劝钱元瓘安抚相关将吏')],when='937年三月戊午杀人之后，劝谏具体日期未单独记载',description='钱元瓘想追查与元珦、元㺷往来的将吏。钱仁俊引用刘秀和曹操焚毁相关书信以安定人心的事例，劝他效法，钱元瓘接受了建议。',note='原文“其子仁俊”与932年明确“从子仁俊”有差异，复用钱仁俊但不新增父亲关系；刘秀、曹操是引述的历史人物，不创建937年现场参与。')
# Individual profiles receive quotes covering the complete stated scope.
profile_spans={
 '杨璪':(9,'戊子，','册命齐王；'),
 '齐王妃（徐知诰妻）':(9,'册王妃',None),
 '吴峦':(11,'节度判官吴峦','闭城不受契丹之命，'),
 '郭崇威':(11,'应州马军','挺身南归。'),
 '翟璋':(11,'契丹主过新州，','犒军钱十万缗。'),
 '去诸（西奚王）':(11,'奚王去诸','号西奚。'),
 '李绍威（西奚王）':(11,'去诸卒，','名绍威。'),
 '逐不鲁（契丹）':(11,'绍威娶','绍威纳之；'),
 '逐不鲁之姊（李绍威妻）':(11,'绍威娶','之姊。'),
 '拽剌（西奚王）':(11,'绍威卒，','拽剌迎降，'),
 '高彦英（契丹通事）':(11,'契丹主顾通事高彦英','笞彦英而谢\ue3ff厉。'),
 '钱元㺷（吴越王少子）':(12,'初，吴越王','即格杀之；')}
for name,(n,start,end) in profile_spans.items():
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'简介仅据此段明确行动和身份整理；姓名缺字的同书校读及同人疑问在独立事实中保留，不填未知生卒年。')
reviews={9:'齐王册命、接受与赦令、王妃册后分录；王妃姓名未载，暂用限定名。',10:'钱氏沿旧主体钱传瓘、钱传珦，不补具体罪名；兄长方向由“之弟”确定。',11:'长段已按所有行动和追叙分录。沙彦珣、张砺、霫的缺字据同书校读；未改TXT。西奚王去诸、扫刺、拽剌限定身份，原文明示父子、婚姻及姐姐关系。云州围城半年/七月与辽史投降说并列。翟璋功劳不推为攻克云州，南归许诺不推为执行，死亡年份不确定。',12:'元㺷及元珪异写保留，旧史元球与静海衔另记，暂不合早年钱传球。铜官告发、左右藏刃说均作言辞；三月死亡与七月奏报区分。“其子仁俊”与932从子冲突，不新增父亲边。'}
assert not (P/'publication.json').exists()
for n in range(9,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(9,13)],next_paragraph=Q[13]['id'],next_volume=281,next_year=937,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第9—12段（原14—17行），含西奚追叙和三月吴越事件。937年尚未完成。',source_issues_review='逐行核对TXT与账本；私用字留在原文，另以同书固定修订及相关纪传识别展示字形。新增二十四史段落未发现私用字标记；章节传主已回查正文。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,13)],plain_language_review='首次整理完成新展示字段及事实说明逐条白话自查；引用保留原字，复用人物保留原档案。尚未解决的身份、亲属与异说分别保留，不安排固定的发布后二次文字审阅。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
