# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 54–59."""
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
specs=[(d.name,d,'5bcdd3b7314e12d7264f468cb5a94810f96be300','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith(('liaoshi','songshi')) else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-min-and-year-end','xinwudaishi-064-meng-secret-succession']:
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
main_sources = ['tongjian-281-937-min-and-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p054-p059',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-076-november':'卷76·晋高祖纪·天福二年十一月','jiuwudaishi-097-hu-jia':'卷97·李金全传','liaoshi-004-huitong':'卷4·太宗纪·会同元年十一月','liaoshi-076-zhao-yanshou':'卷76·赵延寿传'}
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
for n in range(54, 60):
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
    labels={'jiuwudaishi-076-november':'卷76·晋高祖纪·天福二年十一月','jiuwudaishi-097-hu-jia':'卷97·李金全传','liaoshi-004-huitong':'卷4·太宗纪·会同元年十一月','liaoshi-076-zhao-yanshou':'卷76·赵延寿传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '十一月条下，含时日未明的追叙' if n<57 else '十二月条下' if n<59 else '年末总记'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'徐景达':'徐诰的儿子。937年十一月被封为寿阳公，姓名在本站统一使用此时的徐氏形式。具体生卒年份此段未载。',
'胡汉筠':'李金全的亲近吏员。受任中门使，掌管安远军府事务。史书记载他遭朝廷召调后劝李金全背离朝廷，又谋害反对自己的庞令图和接替他的贾仁沼。各次行动的具体日期并非全都记明。',
'贾仁沼':'后晋吏员。石敬瑭派他接替胡汉筠，后来被胡汉筠毒杀。具体死亡年份此段未载。',
'庞令图':'李金全的故人，曾多次劝他接受贾仁沼并替换胡汉筠。胡汉筠派人在夜间翻墙杀害庞令图一家，具体发生日期未载。',
'张纬（李金全推官）':'李金全属下推官。史书记载他与胡汉筠互相勾结，以奉承的方式影响李金全，具体起止时间未载。'}
NEW_ALIASES={'徐景达':['景达','徐景達'],'胡汉筠':['胡漢筠'],'贾仁沼':['賈仁沼','贾仁绍','賈仁紹'],'庞令图':['龐令圖'],'张纬（李金全推官）':['张纬','張緯']}

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
    if when is None:when='937年十一月，具体日期未记载'
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
ALIASES.update({'唐主':'李昪','景通':'李璟','景遂':'徐景遂','景达':'徐景达','杨琏妃':'徐氏（杨琏妃）','胡汉筠':'胡汉筠','仁沼':'贾仁沼','张纬':'张纬（李金全推官）','蜀主':'孟昶','契丹主':'耶律德光','帝':'石敬瑭','元瓘':'钱传瓘'})
add('jing_tong_renamed_jing','徐景通改名为璟',54,'十一月，乙卯，','更名璟。',[('景通','以吴王身份改名为璟')],when='937年十一月乙卯',note='本句只改名璟，徐姓未在本日改为李；本站复用后来李璟的稳定主体，不建立新人物。')
add('yang_lian_wife_yongxing','徐诰赐杨琏妃永兴公主称号',54,'唐主赐','号永兴公主；',[('唐主','赐杨琏妃永兴公主称号'),('杨琏妃','获赐永兴公主称号')],when='937年十一月乙卯条下',note='电子本杨画家杨琏为异常重复文字，摘录保持原字；依据杨琏妃及前文已录徐诰女儿婚姻识别既有徐氏，不新建杨画家人物。公主是封号，不是另一个人名。')
add('yongxing_weeps_at_title','杨琏妃听到别人称自己为公主便流泪辞谢',54,'妃闻人','流涕而辞。',[('杨琏妃','听到别人称自己为公主时流泪辞谢')],year=None,when='获赐永兴公主称号之后，具体起止日期未载',note='反应为后续习惯，没有明确说明每次流泪的动机，不代她断言对亡国或父亲的评价。')
add('jing_sui_ji_prince','徐诰封徐景遂为吉王',54,'戊午，','景遂为吉王，',[('唐主','封儿子徐景遂为吉王'),('景遂','被封为吉王')],when='937年十一月戊午')
add('jing_da_shouyang_duke','徐诰封徐景达为寿阳公',54,'戊午，','景达为寿阳公；',[('唐主','封儿子徐景达为寿阳公'),('景达','被封为寿阳公')],when='937年十一月戊午')
relationship('唐主','景达','父亲',54,span(54,'戊午，','景达为寿阳公；'),'其子明确修饰景遂与景达，方向为李昪是徐景达的父亲，不由公爵封号推其他亲属关系。')
relationship('唐主','景遂','父亲',54,span(54,'戊午，','景达为寿阳公；'),'其子明确父亲方向，使用既有徐景遂主体与同向关系，不因后来的李姓另建主体。')
add('jing_sui_eastern_capital','徐景遂任侍中、东都留守和江都尹，率留司百官赴东都',54,'以景遂',None,[('唐主','任命徐景遂为侍中、东都留守、江都尹'),('景遂','率留司百官赴东都')],when='937年十一月戊午条下',place='东都（江都）',note='任官与赴东都均有原文；不误将江都尹当后晋洛阳尹，不补抵达日期。')
add('qian_yuanguan_national_king','钱传瓘被加授天下兵马副元帅，进封吴越国王',55,'戊辰，',None,[('帝','给吴越王钱传瓘加官进封'),('元瓘','被加授天下兵马副元帅，进封吴越国王')],when='937年十一月戊辰',note='元瓘复用既有钱传瓘主体；吴越王至吴越国王是封爵文字变化，不写成在本日新建吴越国家。')
sup('qian_yuanguan_national_king',55,'jiuwudaishi-076-november','戊辰，鎮海鎮東節度使、吳越王錢元瓘加天下兵馬副元帥，封吳越國王。','《旧五代史》也在十一月戊辰记钱元瓘加天下兵马副元帅，封吴越国王。','钱元瓘与钱传瓘为同一人物，沿用既有主体，纪日相同。')
# 56: only the dated memorial receives a definite 937 date.
add('hu_hanjun_controls_anyuan','李金全让亲吏胡汉筠任中门使，并将军府事务交给他',56,'安远节度使','军府事一以委之。',[('李金全','任用亲吏胡汉筠并将军府事务交给他'),('胡汉筠','任中门使，掌管军府事务')],year=None,when='李金全任安远节度使期间，具体任用日期未记载',place='安远军（安州）',note='叙述背景不能当乙亥当天任命，任安远后的时间范围不等于精确始年。')
sup('hu_hanjun_controls_anyuan',56,'jiuwudaishi-097-hu-jia','金全有親吏胡漢筠者，勇譎嗇褊，貪詐殘忍，軍府之政，一以委之。','《旧五代史》也记李金全把军府事务交给亲吏胡汉筠。','正文叙述印证，不把该书贪詐等评价直接作为网站自行定论。')
claim('person',people['胡汉筠'],'description','《资治通鉴》评价胡汉筠贪婪狡猾、残忍，聚敛没有节制。',56,'汉筠贪滑残忍，聚敛无厌。','这是史书对人物行事的评价，以书名明确归属，不把它扩写为未载的具体罪行。')
add('shi_replaces_hu_with_jia','石敬瑭派贾仁沼接替胡汉筠，并召胡汉筠另拟任职',56,'帝闻之，','庶保全功臣。',[('帝','派贾仁沼接替胡汉筠，召胡汉筠并打算另授职务'),('仁沼','被派接替胡汉筠'),('胡汉筠','被召回，皇帝打算给他另授职务'),('李金全','皇帝希望保全的功臣')],year=None,when='李金全报告胡汉筠患病之前，具体召调日未记载',place='安州与朝廷',note='想授其他职务不是已完成任命；保全功臣指李金全，不译为胡汉筠已立大功。')
sup('shi_replaces_hu_with_jia',56,'jiuwudaishi-097-hu-jia','高祖聞其事，遣吏賈仁紹往代其職，且召漢筠。','《旧五代史》也记石敬瑭派吏员接替胡汉筠并召胡汉筠，接替者写作贾仁绍。','同一职务替换、毒杀经过对应贾仁沼，作为同人异名，不另建贾仁绍；该书正文不列日期。',relation='adds')
add('hu_urges_li_disloyalty','胡汉筠因恐惧召调，开始劝李金全背离朝廷',56,'汉筠大惧，','始劝金全以异谋。',[('胡汉筠','因恐惧召调而开始劝李金全采取背离朝廷的行动'),('李金全','受到胡汉筠劝说')],year=None,when='朝廷召调胡汉筠之后，具体劝说日未载',note='异谋是背离朝廷的谋划，不能等同于此时已经起兵反叛或投奔南唐。')
add('li_reports_hu_sick','李金全上表称胡汉筠患病，无法赴朝廷',56,'乙亥，','未任行。',[('李金全','上表称胡汉筠患病，不能动身'),('胡汉筠','李金全报告其患病，无法赴朝廷')],when='937年十一月乙亥奏报',note='患病是表奏所称，不据此确认胡汉筠确实有病；奏报日期不用于此前或后续杀人。')
sup('li_reports_hu_sick',56,'jiuwudaishi-076-november',source_span('jiuwudaishi-076-november','壬午，安州李金全上言：','候損日赴闕。」'),'《旧五代史》将李金全称胡汉筠患重病、待痊愈赴阙的奏报记为十一月壬午。','《资治通鉴》记乙亥，该书记壬午，纪日不同分别保存，不覆盖主书日期。',relation='conflicts',field='time_original')
add('pang_urges_accept_jia','庞令图多次劝李金全接受贾仁沼接替胡汉筠',56,'金全故人','所益多矣。”',[('庞令图','多次劝李金全接受贾仁沼接替胡汉筠'),('李金全','受到故人庞令图劝说'),('仁沼','庞令图推荐接受的接替者'),('胡汉筠','被提议替换的人')],year=None,when='朝廷派贾仁沼后，具体劝说日期未载',note='忠义为庞令图的评价；故人不自动新增结义或盟友关系。')
add('hu_kills_pang_family','胡汉筠派人夜间翻墙，杀害庞令图一家',56,'汉筠夜遣','灭令图之族，',[('胡汉筠','派壮士在夜间翻墙杀害庞令图一家'),('庞令图','自己及家人被胡汉筠派人杀害')],year=None,when='庞令图多次劝谏之后，具体夜间行动年月未载',place='庞令图住所',note='灭族不补未载的家属姓名、人数或具体刑罚，不把乙亥奏报日当杀人日。')
add('hu_poisons_jia','胡汉筠毒杀贾仁沼',56,'又毒仁沼，','舌烂而卒。',[('胡汉筠','下毒害死接替自己的贾仁沼'),('仁沼','被毒害后舌头溃烂而死')],year=None,when='朝廷派贾仁沼接替胡汉筠之后，具体死亡年月未载',note='此段后续叙事没有另载死日；不把相邻乙亥定为死日，舌烂为史载症状不新增医学诊断。')
sup('hu_poisons_jia',56,'jiuwudaishi-097-hu-jia','及仁紹至，漢筠鴆而殺之。','《旧五代史》记贾仁绍到达后被胡汉筠毒杀。','与贾仁沼的同一替职和死亡经过对应，姓名异文保留；不把传末天福五年任马全节前的全部背景倒定为940年。',relation='adds')
add('hu_zhang_flatter_li','胡汉筠与推官张纬勾结，用奉承影响李金全',56,'汉筠与推官',None,[('胡汉筠','与张纬勾结，用奉承影响李金全'),('张纬','以推官身份与胡汉筠勾结'),('李金全','更加信任胡汉筠')],year=None,when='安州吏政后续记载，具体起止年月未载',note='相结明确此事合作，不扩大成终身政治盟友；张纬用职务限定姓名，避免与别时代同名人混同。')
add('meng_chang_december_amnesty','孟昶在蜀国宣布大赦',57,'十二月戊申，','蜀大赦，',[('蜀主','宣布大赦')],when='937年十二月戊申',place='蜀国')
add('shu_next_year_era_announcement','蜀国宣布更改次年年号，史书所载名称不同',57,'十二月戊申，',None,[('蜀主','宣布更改次年年号')],when='937年十二月戊申宣布，拟次年实施',place='蜀国',description='蜀国宣布更改次年年号。《资治通鉴》电子底本此处写“明德”，《新五代史》记孟昶沿用明德至五年才改为“广政”。两种记载分别保留，年号名称待版本校核。',note='主书原字明德保留，不悄悄改为广政，也不把次年实施写成本日已进入新年号。')
sup('shu_next_year_era_announcement',57,'xinwudaishi-064-meng-secret-succession','昶立，不改元，仍稱明德，至五年始改元曰廣政。','《新五代史》记孟昶即位后沿用明德，至五年才改元广政。','复用已发布来源；该书不列本段十二月戊申公告日，分别保存年号差异，纸本待核。',relation='conflicts')
add('ma_xifan_jiangnan_command','马希范被加授江南诸道都统，负责武平、静江等军务',58,'诏加',None,[('帝','给马希范加授江南诸道都统等军务职权'),('马希范','被加授江南诸道都统，制置武平、静江等军务')],when='937年十二月条下，具体诏令日未载',place='武平、静江等军',note='制置是军务职掌，不推为已吞并这些地区或发动实际战争。')
add('khitan_huitong_era','契丹改元会同',59,'是岁，','契丹改元会同，',[('契丹主','改元会同')],when='《资治通鉴》937年是岁总记，具体月日未载',place='契丹',note='与《辽史》纪日分列，不以主书总记硬推具体日期。')
sup('khitan_huitong_era',59,'liaoshi-004-huitong',source_span('liaoshi-004-huitong','丙寅，皇帝御宣政殿，','大赦，改元會同。'),'《辽史》记皇帝在十一月丙寅接受尊号，大赦并改元会同。','所属会同元年由卷4前文年题核对；与《资治通鉴》937年是岁总记定位分列，年号公元换算及版本年份仍待核，不自动覆盖主书。',relation='adds',field='time_original')
add('khitan_daliao_state_name','《资治通鉴》记契丹改国号为大辽',59,'国号大辽，','国号大辽，',[('契丹主','按《资治通鉴》年末总记，改国号为大辽')],when='《资治通鉴》937年是岁总记，具体月日未载',place='契丹',note='这是主书的明确记载，本次《辽史》改元段没有同时明写改国号，不能宣称另一书已独立确认同年改名。')
add('khitan_models_central_offices','契丹仿照中原官制设置官员，并任用中原人',59,'公卿庶官','参用中国人，',[('契丹主','仿照中原官制设置官员，并任用中原人')],when='《资治通鉴》937年是岁总记，具体实施起止未载',place='契丹',description='《资治通鉴》记契丹的公卿和各级官员仿照中原制度，并任用中原人。',note='中国按当时语境解释为中原，不推所有契丹本部制度都被完全撤销。')
sup('khitan_models_central_offices',59,'liaoshi-004-huitong',source_span('liaoshi-004-huitong','升北、南二院','二室韋闥林為僕射，'),'《辽史》改元条还列各部职官调整及宣徽、阁门、御史等官职的设置。','补具体官制条目；不把该段列出的每一职官都另行推为有具名任职者。',relation='adds')
add('zhao_yanshou_khitan_privy','赵延寿被任命为契丹枢密使',59,'以赵延寿','为枢密使，',[('契丹主','任命赵延寿为枢密使'),('赵延寿','被任命为契丹枢密使')],when='《资治通鉴》937年是岁总记，具体任命日未载',place='契丹',note='与赵延寿此前后唐枢密使职务分开，不能把两国同名官衔当一次任命。')
add('zhao_yanshou_government_order','赵延寿随后兼任契丹政事令',59,'以赵延寿',None,[('契丹主','让赵延寿兼任政事令'),('赵延寿','在任枢密使后兼政事令')],year=None,when='任契丹枢密使后不久，确切年月未载',place='契丹',note='寻只指后续不久，不强定937年同日。')
sup('zhao_yanshou_government_order',59,'liaoshi-076-zhao-yanshou','會同初，帝幸其第，加政事令。','《辽史》赵延寿传记会同初皇帝到他的宅邸，加授政事令。','补任官背景和年号范围；不把会同初强换成一个未经校核的公元年份。',relation='adds',field='time_original')
for name,n,start,end in [('徐景达',54,'戊午，','景达为寿阳公；'),('胡汉筠',56,'安远节度使','舌烂而卒。'),('贾仁沼',56,'帝闻之，','舌烂而卒。'),('庞令图',56,'金全故人','灭令图之族，'),('张纬（李金全推官）',56,'汉筠与推官',None)]:
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'简介据本段明确身份和行动，未记时日不补生卒年；他书姓名差异另有独立引用。')
claim('person',people['贾仁沼'],'aliases','贾仁沼在《旧五代史》李金全传正文中写作贾仁绍。',56,'高祖聞其事，遣吏賈仁紹往代其職，且召漢筠。','两书所述同一替职、被毒杀经过相接，作为同人异名保留，不因转录差异重复建人。',source='jiuwudaishi-097-hu-jia',relation='adds')
reviews={54:'十一月乙卯改名只改璟，不提前复姓。杨画家杨琏为异常重复，保留底本，依杨琏妃及前文已录徐氏识别公主；流涕不猜心理。戊午封景遂、景达及东都任官分录，父亲方向明确。',55:'戊辰加副元帅、进封吴越国王，旧本纪同日补证。沿用钱传瓘，不推本日国家新建。',56:'安远军府背景、朝廷换吏、异谋建议、乙亥奏病、庞屡谏、夜杀其族、毒贾、胡张勾结分录。仅奏报定937十一月，旧本纪壬午不同另存。后续杀人等年月未载留null，不倒定940。贾仁绍/仁沼按同职同案识别，正文与马令书引注区别，不将引注作独立二十四史事实。',57:'十二月戊申大赦与明年改元公告分录；底本明德与新五代史明德五年改广政不同，保留待考，不悄改原字或写当日新元已用。',58:'诏加江南都统并制置武平静江军务，不造已经攻取。月份承十二月，诏日未知。',59:'契丹改元、国号、仿中原官制、赵任枢密及寻兼政事令分录。原书937总记与辽史十一月纪日、会同初赵加政事令分别保存；国号没有辽史本段独立确认，不宣称一致。'}
assert not (P/'publication.json').exists()
for n in range(54,60):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n');(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(54,60)],next_paragraph='zztj-v281-y0938-p001',next_volume=281,next_year=938,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第54—59段，原文件59—64行，937年正文末段；原65行分隔符、66行938年题、67行938年首段已核。来源快照含后年上下文，不计为处理完成。',source_issues_review='全部原文逐行对照；杨画家重复字不展示为人名；新旧姓名、纪日、年号名称及契丹年记与纪日保留差异。旧李金全传中马令南唐书引注不当独立二十四史确证。纸本版本仍待核。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(54,60)],plain_language_review='首次逐条自查展示字段：明确主语、官职、请求与执行、原话评价、未知日期和关系方向；引用原字保留，不复写旧批次。'),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
