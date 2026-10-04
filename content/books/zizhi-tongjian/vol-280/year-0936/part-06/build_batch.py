# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 280, year 936 paragraphs 37–41."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,71))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'7ec8616b','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))

specs += [('tongjian-280-936-november-commands',YEAR/'part-05/sources/library/tongjian-280-936-november-commands','4db2cb5d','司马光等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-280-936-november-commands','tongjian-280-936-sang-rescue-plans']
B = {'format_version': 1, 'batch_key': 'zztj-v280-y0936-p037-p041',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-075-jin-enthronement':'卷75·晋高祖纪（石敬瑭）','jiuwudaishi-076-first-decree':'卷76·晋高祖纪（石敬瑭）','jiuwudaishi-137-khitan-agreement':'卷137·外国列传·契丹','xinwudaishi-029-sang-persuasion':'卷29·桑维翰传','xinwudaishi-056-long-min-final-plan':'卷56·龙敏传','liaoshi-003-jin-enthronement':'卷3·太宗纪','liaoshi-003-proposed-enthronement':'卷3·太宗纪','jiuwudaishi-048-dan-militia':'卷48·唐末帝纪（李从珂）'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/280.txt').read_text().splitlines()
for n in range(37, 42):
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
    labels={'jiuwudaishi-075-jin-enthronement':'卷75·晋高祖纪（石敬瑭）','jiuwudaishi-076-first-decree':'卷76·晋高祖纪（石敬瑭）','jiuwudaishi-137-khitan-agreement':'卷137·外国列传·契丹','xinwudaishi-029-sang-persuasion':'卷29·桑维翰传','xinwudaishi-056-long-min-final-plan':'卷56·龙敏传','liaoshi-003-jin-enthronement':'卷3·太宗纪','liaoshi-003-proposed-enthronement':'卷3·太宗纪','jiuwudaishi-048-dan-militia':'卷48·唐末帝纪（李从珂）'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '十一月条下' if n==37 else '闰十一月条下'
        citation = f'卷280·后唐清泰三年／后晋天福元年（936；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_280_0936_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_ALIASES={'窦贞固':['竇貞固'],'景延广':['景延廣'],'康承询':['康承詢'],'罗周岳':['羅周嶽','罗周嶽'],'李玘':[]}

ALIASES.update({'汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=936, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='936年'+('十一月' if n==37 else '闰十一月')+'条下；确日未独载'
    key = 'event_zztj_280_0936_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_280_0936_' + code + '_' + pk
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
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_280_0936_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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

add('deguang_offers_throne','耶律德光称远来必成功、拟立石敬瑭为帝',37,'契丹主谓石敬瑭曰：','吾欲立汝为天子。”',[('耶律德光','拟授帝位、陈述判断者'),('石敬瑭','受提议者')],note='三千里与气貌识量是德光话，非现代测距或相术已验证。')
sup('deguang_offers_throne',37,'liaoshi-003-proposed-enthronement','丁卯，召敬瑭至行在所，賜坐。上從容語之曰：「吾三千里舉兵而來，一戰而勝，殆天意也。觀汝雄偉弘大，宜受茲南土，世為我藩輔。」遂命有司設壇晉陽，備禮冊命。','辽将召谈、命备坛系十月丁卯。','辽前文十月框架，后十一月丁酉才正式册，准备与正式册分；主未载本次提议独立日。',relation='adds',field='time_original')
add('shi_accepts_enthronement','石敬瑭辞让数次，经将吏劝进后答应',37,'敬瑭辞让','乃许之。',[('石敬瑭','答应帝位者')],note='匿名将吏不猜桑或刘个体；辞让数四保概数不以精确四次序列。')
add('jin_enthronement_liulin','契丹作册、筑坛柳林，石敬瑭即大晋皇帝位',37,'契丹主作册书，','即皇帝位。',[('耶律德光','作册、授衣冠者'),('石敬瑭','受册即位者')],when='936年十一月，主己亥改元前；辽十一月丁酉，旧唐帝纪闰月丁卯异说',place='柳林',note='是日即位承上筑坛，主本段未具干支；辽丁酉与旧唐闰丁卯并列，不把己亥改元移作登坛日。')
sup('jin_enthronement_liulin',37,'jiuwudaishi-075-jin-enthronement','既而諸軍勸請相繼，乃命築壇於晉陽城南，冊立為大晉皇帝，戎王自主解衣冠授焉。','旧晋纪同记受册授衣冠，坛地作晋阳城南。','城南与柳林只按史载并列，不据此填坐标；旧夹注辽日依赖辽正文不独证。',relation='adds')
sup('jin_enthronement_liulin',37,'liaoshi-003-jin-enthronement','十一月丁酉，冊敬瑭為大晉皇帝。','辽太宗纪系十一月丁酉。','辽正文独具日期，主本段无日而己亥系改元；不覆写主底本。',field='time_original')
sup('jin_enthronement_liulin',37,'jiuwudaishi-048-dan-militia','丁卯，戎王立石敬瑭為大晉皇帝，約為父子之國，改元為天福。','旧唐末帝纪将立晋、父子之国和改元连系闰月丁卯。','与主十一月改元、辽丁酉册异时序，完整保，不挪为辽十月备坛丁卯同一次日期。',relation='conflicts',field='time_original')
add('shi_agrees_sixteen_prefectures','石敬瑭割幽蓟等十六州与契丹',37,'割幽、','十六州以与契丹，',[('石敬瑭','割让一方'),('耶律德光','契丹一方')],note='当前成立时的割让安排，列州逐字可索；不把各州图籍交付与各地控制同步完成认作当日。《辽史》会同元年另记图籍来献，留上下文核时，不提前录938。',place='幽、蓟、瀛、莫、涿、檀、顺、新、妫、儒、武、云、应、寰、朔、蔚')
sup('shi_agrees_sixteen_prefectures',37,'jiuwudaishi-137-khitan-agreement','約為父子之國，割幽州管內及新、武、雲、應、朔州之地以賂之，仍每歲許輸帛三十萬。','旧外国传记父子之国、割幽州管内及新武云应朔等地。','父子是政治名分不生血亲边；旧用辖区概括非额外州清单，不能累加为二十一州。',relation='adds')
add('shi_promises_annual_silk','石敬瑭许每年输契丹帛三十万匹',37,'仍许岁输','帛三十万匹。',[('石敬瑭','许岁输者')],note='许是承诺，非本年或每年已实收三十万；主具匹，旧外国传省计量不另加。')
sup('shi_promises_annual_silk',37,'jiuwudaishi-137-khitan-agreement','仍每歲許輸帛三十萬。','旧也记每岁许帛三十万。','正文约定印证，非以后历年全部履约的证据。')
add('shi_changes_era_amnesty','十一月己亥石敬瑭改长兴七年为天福元年并大赦',37,'己亥，','大赦；',[('帝','颁改元赦令者')],when='936年十一月己亥',note='晋不用后唐清泰三而追称长兴七，主原纪年保；同年唐仍在，不提前记录唐亡。')
sup('shi_changes_era_amnesty',37,'jiuwudaishi-076-first-decree','天福元年十一月己亥，帝御北京崇元殿，降制：「改長興七年為天福元年，大赦天下。','旧晋纪同己亥改元大赦，补御北京崇元殿。','北京指当时太原，非现代北京；诏位置与柳林登坛位置不同。',relation='adds')
add('shi_restores_mingzong_codes','石敬瑭敕法制遵李嗣源旧规',37,'敕命法制，','皆遵明宗之旧。',[('帝','敕遵旧制者')],when='936年十一月己亥条下',note='已故明宗为法制参照不作现诏参与人；不把所有制度无变动当实证。')
sup('shi_restores_mingzong_codes',37,'jiuwudaishi-076-first-decree','應明宗朝所行敕命法制，仰所在遵行，不得改易。','旧赦制载遵明宗敕命法制，不得改易。','诏令规范非后来所有地方实际执行的证据。')
add('zhao_ying_jin_academician','赵莹任翰林学士承旨、户部侍郎、知河东军府事',37,'以节度判官赵莹','知河东军府事，',[('赵莹','原节度判官、获任者')],when='936年十一月己亥条下',note='赵职完整，桑另记；不因此记录赵此时已门下相。')
sup('zhao_ying_jin_academician',37,'jiuwudaishi-076-first-decree','以節度判官趙瑩為翰林學士承旨、守尚書戶部侍郎、知河東軍府事，','旧同赵莹新职。','瑩沿莹已有主体，守尚书为旧完整衔，繁体不另建赵瑩。')
add('sang_jin_academician_privy','桑维翰任翰林学士、礼部侍郎、权知枢密使事',37,'掌书记桑维翰为','权知枢密使事，',[('桑维翰','原掌书记、获任者')],when='936年十一月己亥条下',note='未把新史后来中书侍郎平章事提前；相命另在后段。')
sup('sang_jin_academician_privy',37,'jiuwudaishi-076-first-decree','以節度掌書記桑維翰為翰林學士、守尚書禮部侍郎、知樞密院事，','旧同桑翰林礼部知枢密。','主权知、旧知字不同并列，不擅提升确定为正式枢密使。')
sup('sang_jin_academician_privy',37,'xinwudaishi-029-sang-persuasion','高祖即位，以維翰為翰林學士、禮部侍郎、知樞密院事，','新桑传同记即位后所任。','新传后续迁相未加入本次初命，维翰代称以传首核。')
add('xue_rong_jin_censor','薛融任侍御史知杂事',37,'观察判官薛融为','侍御史知杂事，',[('薛融','原观察判官、获任者')],when='936年十一月己亥条下')
sup('xue_rong_jin_censor',37,'jiuwudaishi-076-first-decree','以觀察判官薛融為吏部郎中兼侍御史、知雜事，','旧补吏部郎中兼侍御史。','旧具额外兼衔，主省吏部职无冲突，不造第二次任命。',relation='adds')
add('dou_zhengu_jin_academician','窦贞固任翰林学士',37,'节度推官白水窦贞固','为翰林学士，',[('窦贞固','原节度推官、获任者')],when='936年十一月己亥条下',note='白水是人物籍贯信息，不擅记任翰林发生于白水；与窦贞无根据不合。')
sup('dou_zhengu_jin_academician',37,'jiuwudaishi-076-first-decree','節度推官竇貞固為翰林學士，','旧同窦贞固任翰林。','繁简同人，旧未载白水，籍贯只据主。')
add('liu_zhiyuan_jin_guard_command','刘知远任侍卫军都指挥使',37,'军城都巡检使刘知远','为侍卫军都指挥使，',[('刘知远','原军城都巡检使、获任者')],when='936年十一月己亥条下')
sup('liu_zhiyuan_jin_guard_command',37,'jiuwudaishi-076-first-decree','軍城都巡檢使劉知遠為侍衛馬軍都指揮使，','旧官衔具侍卫马军都指挥使。','主省马、旧具马原衔保，暂不确定为两次职位；非侍卫步军景延广同职。',relation='adds')
add('jing_yanguang_jin_infantry','景延广任步军都指挥使',37,'客将景延广','延广，陕州人也。',[('景延广','原客将、获任者')],when='936年十一月己亥条下',note='陕州籍贯不当任命所在地，广与廣同人；不提前录后期外交行为。')
sup('jing_yanguang_jin_infantry',37,'jiuwudaishi-076-first-decree','客將景延廣為步軍都指揮使，','旧同景延广新职。','客将为前职，本次仅步军命，非后期禁军全部权。')
add('shi_wife_jin_empress','石敬瑭立晋国长公主为皇后',37,'立晋国长公主','为皇后。',[('石敬瑭','册后者'),('晋国长公主','获册皇后者')],when='936年十一月己亥条下',note='沿全站永宁公主（石敬瑭妻）含晋国长公主，原既有夫妇边不另增；不是李从珂后刘氏。')
# Extra offices and policies appear in the same first decree, retained as independent evidence.
s='jiuwudaishi-076-first-decree'
event('shi_salt_trade_decree','旧补石敬瑭赦制准民自行购盐、禁太原官场糴货',37,'其在京鹽貨，元是官場出糴，自今後並不禁斷，一任人戶取便糴易，仍下太原府，更不得開場糴貨。',[('石敬瑭','降制者')],source=s,when='936年十一月己亥',place='太原',note='原糴及开场糴货保，不擅改成全面废除全国盐税；只据当地销售购盐措施。')
event('shi_qu_price_decree','旧补石敬瑭赦制减曲价每斤三十文',37,'其曲每斤與減價錢三十文。',[('石敬瑭','降制者')],source=s,when='936年十一月己亥',note='减价不是新价格三十文；曲原字保未另定酒税一律减幅。')
event('luo_zhouyue_jin_admonisher','旧补太原县令罗周岳任左谏议大夫',37,'太原縣令羅周嶽為左諫議大夫，',[('罗周岳','原太原县令、获任者')],source=s,when='936年十一月己亥条下',note='展示岳，嶽保别名；补主未具而非主无此任。')
event('li_qi_jin_works_vice_minister','旧补太原少尹李玘任工部侍郎',37,'太原少尹李玘為尚書工部侍郎。',[('李玘','原太原少尹、获任者')],source=s,when='936年十一月己亥条下',note='玘字保，不能因同音并吕琦、李琪、李琦。')
add('khitan_baggage_retreat_readiness','契丹主驻柳林，辎重老弱留虎北口，每晚整装防仓促撤退',37,'契丹主虽军柳林，','以备仓猝遁逃，',[('耶律德光','驻军与退路安排所属一方')],place='柳林、虎北口',note='主叙预备撤退非已撤；尚在战略危险与先前胜仗可同时成立。')
add('zhaodejun_waits_tuanbai','赵德钧欲借契丹取中原，在团柏逾月按兵、与晋安消息不通',37,'而赵德钧欲倚','声问不能相通。',[('赵德钧','按兵者')],when='936年十一月石即位时追述团柏逾月；屯起日不重定',place='团柏、晋安',note='逾月为持续长度，才百里史载概距非现代坐标；与上批屯谷口命为后来持续状态。')
add('zhaodejun_repeatedly_seeks_chengde','赵德钧多次为赵延寿求成德，以幽州势孤需镇州接应为理由',37,'德钧累表为','左右便于应接。”',[('赵德钧','奏请者'),('赵延寿','拟得成德者')],place='成德、幽州、镇州',note='累表不计确次数；以便接应为奏说非已核唯一动机，未授镇不造任命事件。')
add('congke_defers_chengde_request','李从珂答赵延寿击敌无暇赴镇，待平敌再如所请',37,'唐主曰：“延寿方','当如所请。”',[('唐主','答复者')],note='方击贼为帝答话，非主在此独立记赵已实战；俟平以后是条件承诺。')
add('congke_angry_zhao_pressure','赵仍求镇，李从珂怒斥玩敌邀君，赵闻不悦',37,'德钧求之不已，',None,[('唐主','怒斥者'),('赵德钧','闻而不悦者')],note='虽欲代位亦甘心为愤怒条件话，非正式禅位或可直接推终身仇敌关系。')
add('zhaoyanshou_presents_khitan_gifts','闰十一月赵延寿献契丹诏与甲马弓剑，声称父遣使为唐求好归兵',38,'闰月，','说令引兵归国；',[('赵延寿','献物、陈述者'),('赵德钧','被称遣使者')],note='诈云是主史判断，献物与父暗约另记；原甲马不简化成仅战马件数。')
add('zhaodejun_secret_bid_for_throne','赵德钧密书厚赂，求契丹立己为帝，拟平洛阳、兄弟之国并让石氏常镇河东',38,'其实别为密书，','仍许石氏常镇河东。”',[('赵德钧','密书求立、厚赂一方'),('耶律德光','被请求者')],note='请、许是未成交易，见兵=现兵语境，原字保；石氏常镇是赵提案而非石同意；兄弟政治名分不生兄弟边。')
sup('zhaodejun_secret_bid_for_throne',38,'jiuwudaishi-137-khitan-agreement','時幽州趙德鈞屯兵於團柏谷，遣使至幕帳，求立己為帝，以石氏世襲太原，','旧外国传也记赵求立、石氏世袭太原条件。','求立不是已立，旧不具献诏诈辞；同主河东与旧太原语境保原。')
sup('zhaodejun_secret_bid_for_throne',38,'xinwudaishi-029-sang-persuasion','耶律德光已許諾，而趙德鈞亦以重賂啖德光，求助己以篡唐。','新桑传也记赵重赂求助篡唐。','主、新都将赵意图归其本人，不作正式即位。')
add('deguang_considers_zhao_offer','契丹主因深入、晋安未下和诸路压力，想答应赵德钧',38,'契丹主自以',None,[('耶律德光','被主叙衡量风险、欲许者')],note='欲许未最后许，范在东与山北可能断归路是其顾虑，匿名山北将不具名。')
add('shi_sends_sang_against_zhao','石敬瑭闻赵方案大惧，急遣桑维翰见契丹主',39,'帝闻之，','见契丹主，',[('帝','遣说者'),('桑维翰','出说者'),('耶律德光','受说对象')],note='此帝沿刚即位石敬瑭，唐主另李从珂，不能沿前批帝全作从珂。')
sup('shi_sends_sang_against_zhao',39,'xinwudaishi-029-sang-persuasion','高祖懼事不果，乃遣維翰往見德光，為陳利害甚辯，德光意乃決，','新桑传同石遣桑、陈利害使德光意决。','高祖是晋石，以传首背景核；不将新传压缩为主每句逐字独证。')
add('sang_argues_zhao_unreliable','桑维翰称赵父子不可信且唐军将尽，劝勿贪小利弃成事',39,'说之曰：','弃垂成之功乎！',[('桑维翰','评敌与劝守约者'),('耶律德光','受说者')],note='食尽力穷与不忠不信为桑论据，非此时独立全军粮耗证明；赵北平为赵德钧称号不另人物。')
add('sang_promises_resources','桑维翰称晋得天下将竭中国财奉契丹',39,'且使晋得天下，','岂此小利之比乎！”',[('桑维翰','提出未来利益者'),('耶律德光','受说者')],note='且使是条件利诱，非已得全部中国财或现代财政统计。')
add('deguang_sang_mouse_debate','德光以捕鼠会咬手比大敌风险，桑答已扼喉不能咬',39,'契丹主曰：“尔见','安能啮人乎！”',[('耶律德光','提出风险比喻者'),('桑维翰','反驳者')],note='比喻不是史中捕鼠实体事件；拆讲话以展示双方论点。')
add('deguang_explains_tactics','德光称未改前约，只是兵家权谋',39,'契丹主曰：“吾非','不得不尔。”',[('耶律德光','解释权谋者')],note='其自辩与主前欲许赵并列，不替作者认定从未动摇。')
add('sang_appeals_faith','桑维翰以信义与四海耳目劝勿改命，跪帐前自旦至暮哭争',39,'对曰：“皇帝以信义','涕泣争之。',[('桑维翰','劝守信、跪哭争者'),('耶律德光','被劝一方')],note='属耳目是桑言，非世界人口调查；旦暮是持续一天语义不换小时。')
add('deguang_rejects_zhao_bid','德光从桑说，指石对赵使称已许石郎、石烂才改',39,'契丹主乃从之，',None,[('耶律德光','维持石约、告赵使者')],note='赵使匿名不猜其子亲自来帐；指石誓句不作为石敬瑭名字神异证据。')
sup('deguang_rejects_zhao_bid',39,'jiuwudaishi-137-khitan-agreement','德光對使指帳前一石曰：「我已許石郎為父子之盟，石爛可改矣。」','旧外国传亦记指石拒赵、称父子盟。','同政治盟约，父子非亲生，旧不直接独证桑跪旦暮。')
# Main chronicle reaches the same two plans already published from Long Min's biography.
add('long_min_discusses_li_yi_primary','龙敏与李懿讨论赵德钧救援能力',40,'龙敏谓前郑州','岂可恃乎！',[('龙敏','谋议者'),('李懿','帝亲将、受议者')],stable_key='event_zztj_280_0936_long_min_discusses_li_yi',note='上批旧龙敏传已录同一谋议，复用事件、参与UUID；主补李懿前郑州防御，国近亲未具谱系不生具体亲属边。')
add('long_min_thousand_horse_plan_primary','龙敏提出千骑救晋安方案',40,'仆有狂策，','况虏骑乎！”',[('龙敏','拟领队者'),('郎万金','被提议共同领队者'),('李懿','讨论对象')],stable_key='event_zztj_280_0936_long_min_thousand_horse_plan',note='上批传记同一未执行方案，复用主体；万余兵近五千马是龙所述现有资源，千骑与半得入为计划，不是已出动结果。')
sup('long_min_thousand_horse_plan_primary',40,'xinwudaishi-056-long-min-final-plan','今聞駕前之馬，猶有五千，願得壯者千匹，健兵千人，與勇將郎萬金，自平遙沿山冒虜中而趨官砦，且戰且行，得其半達，則事濟矣！','新龙传同千骑千人半达计划，路线自平遥沿山。','主介休山路、新平遥沿山，保叙法不同无坐标猜；是提出方案非执行。',relation='adds')
add('liyi_reports_long_plan','李懿向李从珂报告龙敏方案',40,'懿以白唐主，','懿以白唐主，',[('李懿','转达者'),('唐主','受报者')],note='已报告与提出方案分行动，不把李懿赞同赵必胜说删掉；前国近亲没具谱系。')
sup('liyi_reports_long_plan',40,'xinwudaishi-056-long-min-final-plan','懿為言之廢帝，廢帝莫能用。','新亦记李懿转达而废帝不能采用。','不能用说明未实行，不推具体禁令文本。')
add('congke_says_plan_too_late','李从珂称龙敏志壮但采用太晚',40,'唐主曰：“龙敏',None,[('唐主','评价并未采用者')],note='帝自言晚非核算军已必然无法救；主无实施，另新明莫能用印证。')
sup('congke_says_plan_too_late',40,'xinwudaishi-056-long-min-final-plan','懿為言之廢帝，廢帝莫能用。然人皆壯其大言。','新称不能用、人壮其言。','人皆为史家笼统评价，未明名单不造群众个人。',relation='adds')
add('dan_militia_expels_kang','丹州义军乱，逐刺史康承询',41,'丹州义军','逐刺史康承询，',[('康承询','被逐刺史')],place='丹州',note='与延州杀杨汉章不同官、不同军变；与唐咸通康承训不合，两名字不是繁简。')
add('kang_chengxun_flees_fuzhou','康承询逃往鄜州',41,'承询奔','鄜州。',[('康承询','奔逃者')],place='鄜州',note='鄜州不是福州，古地名原保；未具日期不认壬戌奔逃日。')
sup('kang_chengxun_flees_fuzhou',41,'jiuwudaishi-048-dan-militia','時承詢奉詔率義軍赴延州義軍亂，承詢奔鄜州，故有是責。','旧补奉诏率义军赴延州、军乱奔鄜背景。','原赴延州义军乱无现代标点分法须保，不把丹州/延州乱覆盖成同杨汉章杀；壬戌为后处分。',relation='adds')
event('kang_chengxun_removed_exiled','旧补闰十一月壬戌康承询停任、流邓州',41,'壬戌，丹州刺史康承詢停任，配流鄧州。',[('康承询','被停任配流者')],source='jiuwudaishi-048-dan-militia',when='936年闰十一月壬戌',place='邓州',note='诏处分与前奔鄜分，配流目的地不证明当日已经到邓州。')

reviews={37:'册晋登坛、割州约定、岁输承诺、己亥改元赦制、法制与6官命、册后、契丹后路、赵求镇及唐答分。辽丁酉和旧唐闰丁卯异时序保；十六州约定不当图籍当日交清，会同上下文留核。旧同赦制补盐曲令和罗李官。政治父子不建血亲，已故明宗非在场。',38:'赵延寿献诏甲马弓剑及诈称和议，与赵密书求帝厚赂分。兄弟之国石常镇皆提案未成；德光欲许不是已许，理由是主所述其顾虑。',39:'帝为石敬瑭，唐主为李从珂。桑遣说、批评赵、许中国财、鼠喻争论、信义哭谏、德光指石拒赵分；军粮和忠信为说辞不替成独立实测。旧外国及新桑传正文补，旧桑传引通鉴不算另证。',40:'主与上批旧龙传两件谋议同事，复用事件及5参与UUID。国近亲未具谱系不造血亲；主介休与新平遥路线并列。现资源数、拟千骑半入、李懿报告、帝称晚未用分。',41:'丹州逐康与延州杀杨不同，奔鄜与旧壬戌停任流邓分，康承询非唐康承训；原赴延州义军乱叙法保，不猜已到流所。'}
contexts=[]
for d in sorted((P/'sources/context').iterdir()):
 rec=json.loads((d/'paragraph.json').read_text());f=d/'source.txt'
 contexts.append(dict(file=os.path.relpath(f,P/'sources'),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),paragraph_id=rec['id'],purpose='新传代称主体或辽会同年界与后续图籍交付核对；不扩录段外整年生平',url='https://github.com/greed-216/histree/blob/7ec8616b/'+str(f.relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(37,42):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=280,year=936,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(37,42)],next_paragraph=Q[42]['id'],next_volume=280,next_year=936,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='连续第37—41段原42—46行：册晋、割州与初制、赵求帝、桑争约、龙救寨未用、丹州兵乱。后29段待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(37,42)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
