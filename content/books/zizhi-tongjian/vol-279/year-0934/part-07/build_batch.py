# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 35–46."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,78))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'651c7870','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-934-accession-aftermath',YEAR/'part-05/sources/library/tongjian-279-934-accession-aftermath','8468a699','司马光等'),
 ('jiuwudaishi-046-934-reward-edict',YEAR/'part-06/sources/library/jiuwudaishi-046-934-reward-edict','fb64c2b0','薛居正等'),
 ('xinwudaishi-064-two-towns-join-shu',YEAR/'part-05/sources/library/xinwudaishi-064-two-towns-join-shu','8468a699','欧阳修'),
 ('jiuwudaishi-044-933-september',YEAR.parent.parent/'vol-278/year-0933/part-03/sources/library/jiuwudaishi-044-933-september','8df19907','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-accession-aftermath','tongjian-279-934-may-towns']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p035-p046',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[key]
        record=dict(record,section_title=label,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(35, 47):
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
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in {'jiuwudaishi-096-liu-suiqing','jiuwudaishi-093-li-zhuanmei','xinwudaishi-027-yao-death','xinwudaishi-047-chang-release'}:
        label={'jiuwudaishi-096-liu-suiqing':'卷96·刘遂清传','jiuwudaishi-093-li-zhuanmei':'卷93·李专美传','xinwudaishi-027-yao-death':'卷27·药彦稠传','xinwudaishi-047-chang-release':'卷47·苌从简传'}[source]
        record=dict(record,citation='《'+record['book']+'》'+label+'，段落 '+record['id']+'；传首及正文已核，纸本及异文待核。')
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '四月丙申' if n==35 else '五月条下；追叙纪时另注'
        citation = f'卷279·清泰元年（934；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','明宗':'李嗣源','蜀':'孟知祥','太后':'曹氏（李嗣源后）','魏国公主':'永宁公主（石敬瑭妻）','李从曮':'李继曮','李冲':'李冲（平卢司马）'}
NEW_ALIASES={'房暠':[],'赵澄':['趙澄'],'李冲（平卢司马）':['李沖（平盧司馬）','李冲（房知温司马）','李沖（房知溫司馬）']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=934, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='934年五月条下；确日未独载'
    key = 'event_zztj_279_0934_' + code
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
        edge = 'participation_zztj_279_0934_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_279_0934_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




# Consecutive paragraphs 35–46. Preserve the original sequence including 戊午 before 丁未.
ev('mingzong_burial','四月丙申李嗣源下葬徽陵',35,'丙申，','庙号明宗。',[('明宗','下葬徽陵者')],when='934年四月丙申',place='徽陵',note='本段下葬非死亡日；圣德和武钦孝皇帝与庙号明宗识别李嗣源，前已死，不改其死亡年。')
ev('congke_mourning_follows_tomb','李从珂服衰绖护送明宗至徽陵并住宿',35,'帝衰绖','宿焉。',[('帝','服丧护送并宿陵者'),('明宗','被护送至陵所者')],when='934年四月丙申',place='徽陵',note='衰绖为丧服；护送与宿陵是主明确动作，不把后五月祔庙合为此事。')
claim('event','event_zztj_279_0934_mingzong_burial','description','旧末帝纪也记丙申葬明宗于徽陵。',35,'丙申，葬明宗皇帝於徽陵。','旧卷46正文补证下葬日及陵名；前附引通鉴赏数与此句无关。',source='jiuwudaishi-046-934-reward-edict',relation='corroborates')
claim('person',people['李嗣源'],'description','本段记李嗣源的庙号为明宗。',35,'庙号明宗。','庙号与下葬同段；不将庙号当在世姓名。')
E={}
E['han']=ev('han_shu_mishi','五月丙午韩昭胤受任枢密使',36,'五月，丙午，','以韩昭胤为枢密使，',[('韩昭胤','枢密使获任者'),('帝','任命者')],when='934年五月丙午',place='洛阳')
E['liu']=ev('liu_yanlang_deputy','五月丙午刘延朗由庄宅使受任枢密副使',36,'以庄宅使','为枢密副使，',[('刘延朗','庄宅使、枢密副使获任者'),('帝','任命者')],when='934年五月丙午',place='洛阳')
E['fang']=ev('fang_gao_north_xuanhui','五月丙午房暠受任宣徽北院使',36,'权知枢密院记','为宣徽北院使。',[('房暠','宣徽北院使获任者'),('帝','任命者')],when='934年五月丙午',place='洛阳',note='主作权知枢密院记，记字疑讹，底字保原；旧同日记权知枢密事，前职字形分别注明。')
claim('person',people['房暠'],'description','房暠为长安人。',36,'暠，长安人也。','籍贯依主，不补现代坐标或出生年。')
for name,key,quote in [('韩昭胤','han','丙午，以端明殿學士韓昭允為樞密使；'),('刘延朗','liu','以莊宅使劉延朗為樞密副使；'),('房暠','fang','以權知樞密事房暠為宣徽北院使；')]:
 claim('event',E[key],'description','旧末帝纪记'+name+'于五月丙午受任'+('枢密使' if key=='han' else '枢密副使' if key=='liu' else '宣徽北院使')+'。',36,quote,'同日同官核对；旧韩名昭允与主昭胤、新昭胤对应，保已有韩昭胤主体；房前职事与主记不改原文。',source='jiuwudaishi-046-934-may-appointments',relation='corroborates')
claim('person',people['韩昭胤'],'aliases','旧末帝纪五月丙午任枢密使条作韩昭允，对应主书韩昭胤。',36,'丙午，以端明殿學士韓昭允為樞密使；','同日、同前职端明学士、同新职枢密使及新纪昭胤交叉识别；允胤不是繁简转换，保底字待纸本。',source='jiuwudaishi-046-934-may-appointments')
for key,quote in [('han','五月丙午，端明殿學士、左諫議大夫韓昭胤為樞密使，'),('liu','莊宅使劉延朗為樞密副使。')]:
 claim('event',E[key],'description','新废帝纪也记五月丙午的此项枢密任命。',36,quote,'新卷七正文独立补证；不照抄自动卷号以外的传主。',source='xinwudaishi-007-934-may',relation='corroborates')
ev('congke_shi_serve_mingzong','追记李从珂和石敬瑭以勇力善斗侍明宗左右',36,'帝与石敬瑭','事明宗为左右；',[('帝','侍明宗左右者'),('石敬瑭','侍明宗左右者'),('明宗','被侍奉者')],year=None,when='李从珂即位前的追叙；具体年、月、日未载',note='与卷278早年随明宗征伐概述复用同一事件及参与边，此段补左右职务与勇力描述；不强定934。',stable_key='event_zztj_278_0934_congke_shi_service_background')
ev('congke_shi_rivalry_background','追记李从珂与石敬瑭互相竞争、素来不悦',36,'然心竞，','素不相悦。',[('帝','被记与石竞争者'),('石敬瑭','被记与李竞争者')],year=None,when='李从珂即位前的关系追叙；起止年未载',note='记史书心竞与不悦，不造永久敌对关系或确定起始年。')
claim('person',people['石敬瑭'],'description','主书追述李从珂即位后石敬瑭不得已入朝，葬礼结束后不敢请求回镇。',36,span(36,'帝即位，','不敢言归。'),'实际四月己卯入朝已在前批记录，此处补当时顾虑，不重复建立同一入朝事件。')
claim('person',people['石敬瑭'],'description','主书形容石敬瑭当时久病而瘦弱。',36,'时敬瑭久病赢瘠，','赢瘠保底字；不诊断病名、病因、病程或由此断定无政治威胁。')
ev('dowager_princess_request_shi_return','曹太后和魏国公主屡为石敬瑭请求归镇',36,'太后及魏国公主','屡为之言；',[('太后','为石敬瑭进言者'),('魏国公主','为石敬瑭进言者'),('石敬瑭','被代为请求归镇者')],note='承上不敢言归及下留之，请归镇为语境；不由二人同求推定曹氏为公主生母，魏封与永宁身份由旧纪回查。')
claim('person',people['永宁公主（石敬瑭妻）'],'aliases','本段魏国公主为此前永宁公主石氏。',36,'壬戌，永寧公主石氏進封魏國公主，','旧卷44长兴四年九月原条已发布；本年称魏国公主沿用封号，不当作本年首次册封，保稳定主体。',source='jiuwudaishi-044-933-september')
ev('fengxiang_advisers_retain_shi','凤翔旧将佐多数劝李从珂留石敬瑭',36,'而凤翔旧将佐','多劝帝留之，',[('帝','被旧将佐劝留者'),('石敬瑭','被建议留下者')],note='旧将佐未具名，不擅指定杨思权、尹晖或他人为建议者。')
ev('han_li_oppose_suspicion','韩昭胤、李专美以赵延寿在汴为由反对猜忌石敬瑭',36,'惟韩昭胤、','不宜猜忌敬瑭。',[('韩昭胤','不宜猜忌意见提出者'),('李专美','不宜猜忌意见提出者'),('赵延寿','当时在汴的相关人物'),('石敬瑭','被讨论者')],note='以赵在汴为理由是二人意见，不推盟约、兄弟关系或确立客观安全判断。',place='洛阳、汴州')
ev('congke_trust_shi_statement','李从珂见石敬瑭瘦弱而不以为虑，并宣称愿以天下重任托付他',36,'帝亦见其骨立，','尚谁托哉！”',[('帝','作信任表态者'),('石敬瑭','被表示信任者')],note='引语为从珂态度，尚谁托不等于已经转让帝位；密亲不单凭此创建新亲属关系。',place='洛阳')
E['shi']=ev('shi_restored_hedong','李从珂复任石敬瑭为河东节度使',36,'乃复以','为河东节度使。',[('帝','复任者'),('石敬瑭','河东节度使获复任者')],when='934年五月丙午条下；主未另列此命确日',place='河东',note='主续丙午长条，旧纪同丙午列此命；任命不等于已于同日抵达河东。')
claim('event',E['shi'],'description','旧末帝纪在五月丙午列石敬瑭北京留守、河东节度使之命，加检校太师、兼中书令，诸军都部署如故。',36,'以成德軍節度使、大同彰國振武威塞等軍蕃漢馬步都部署、檢校太尉、兼中書令、駙馬都尉石敬瑭為北京留守、河東節度使，加檢校太師、兼中書令，都部署如故。','补同一复任的官衔；北京为后唐北京，不标现代北京；新旧职分列，不作此前诸军部署已撤。',source='jiuwudaishi-046-934-may-appointments')
E['xiang']=ev('xiangli_jin_baoyi','五月戊午相里金由陇州防御使受任保义节度使',37,'戊午，','为保义节度使。',[('相里金','保义节度使获任者'),('帝','任命者')],when='934年五月戊午；按底本原次序',place='陇州、保义军',note='主戊午排在丁未前；保连续原次序，不据此倒排或改纪日。')
claim('event',E['xiang'],'description','旧末帝纪也记戊午相里金从陇州防御使改任陕州节度使。',37,'戊午，以隴州防禦使相裏金為陝州節度使。','陕州与主保义是同镇地名与军号，保两种表述；旧纪也作戊午，不擅改主为另一干支。',source='jiuwudaishi-046-934-may-governors',relation='corroborates')
ev('zhao_cheng_surrenders_shu','五月丁未阶州刺史赵澄降蜀',38,'丁未，','降蜀。',[('赵澄','阶州刺史、降蜀者')],when='934年五月丁未',place='阶州',note='主只说赵澄降蜀，不把整州同日武力攻破、其家属迁徙或孟亲自受降加进来。')
E['yang']=ev('yang_siquan_jingnan','五月戊申杨思权由羽林军使受任静难节度使',39,'戊申，','为静难节度使。',[('杨思权','静难节度使获任者'),('帝','任命者')],when='934年五月戊申',place='静难军')
claim('event',E['yang'],'description','旧末帝纪戊申条补杨思权原为羽林右第一军都指挥使、春州刺史，转邠州节度使。',39,'以羽林右第一軍都指揮使、春州刺史楊思權為邠州節度使。','邠州与主静难为州与军镇称谓；前职旧记更细，任命与亲赴镇分开。',source='jiuwudaishi-046-934-yang-siquan',relation='corroborates')
E['move']=ev('zhang_sun_families_chengdu','五月己酉张虔钊、孙汉韶举族迁成都',40,'己酉，','迁于成都。',[('张虔钊','举族迁成都者'),('孙汉韶','举族迁成都者')],when='934年五月己酉',place='成都',note='举族迁与此前举地归蜀、张业进两州不同阶段；家族未具名不编成员。')
claim('event',E['move'],'description','新孟世家记六月张虔钊等至成都，孟知祥宴劳他们。',40,'六月，虔釗等至成都，知祥宴勞之，','主五月己酉记迁，新六月记到达宴劳，分别保留出迁与抵达，不强认同日或径判纪月矛盾；不前移宴中病及死亡。',source='xinwudaishi-064-two-towns-join-shu')
E['feng']=ev('feng_dao_kuangguo','五月庚戌冯道出任匡国节度使并保同平章事衔',41,'庚戌，','充匡国节度使。',[('冯道','出任匡国节度使者'),('帝','任命者')],when='934年五月庚戌',place='匡国军',note='出镇仍带同平章事为使相衔；新纪明说罢，不读作继续中央日常宰相职务。')
claim('event',E['feng'],'description','旧末帝纪同日记冯道加检校太尉、同平章事，充同州节度使。',41,'庚戌，以司空兼門下侍郎、平章事馮道為檢校太尉、同平章事，充同州節度使；','同州与主匡国为地名及军号；保检校官与同平章事荣衔层次。',source='jiuwudaishi-046-934-may-governors',relation='corroborates')
claim('event',E['feng'],'description','新废帝纪在五月庚戌明确记冯道罢。',41,'庚戌，馮道罷。','对应主出镇，罢是中枢宰相职务结束，不抹去使相衔。',source='xinwudaishi-007-934-may',relation='corroborates')
E['fan']=ev('fan_yanguang_shumishi','范延光由天雄节度使兼侍中受任枢密使',42,'以天雄','为枢密使。',[('范延光','枢密使获任者'),('帝','任命者')],when='934年五月庚戌条后；本句未独列日，旧新纪同庚戌',place='洛阳',note='主另起一段无独日；以旧新纪同条补庚戌，不假装主句自有日期。')
claim('event',E['fan'],'description','旧末帝纪五月庚戌条记范延光为枢密使、封齐国公。',42,'以天雄軍節度使範延光為樞密使，封齊國公；','同一次任命补封爵，範／范为字形对应，不新建範延光。',source='jiuwudaishi-046-934-may-governors')
claim('event',E['fan'],'time_original','新废帝纪五月庚戌冯道罢后紧接范延光为枢密使。',42,'庚戌，馮道罷。天雄軍節度使范延光為樞密使。','新纪同日连记，与旧纪互核任命日；保持主句无独日说明。',source='xinwudaishi-007-934-may',relation='corroborates')
ev('congke_takes_li_congyan_assets','追记李从珂起兵凤翔时取李从曮家财甲兵供军',43,'帝之起凤翔也，','甲兵以供军。',[('帝','取家财甲兵供军者'),('李从曮','天平节度使、家财甲兵被取者')],when='934年起兵凤翔时的追叙；此句未独载月日',place='凤翔',note='主李从严含私用缺字；经同凤翔复镇的新传与旧纪对读识别为既有李继曮（当时李从曮），摘录保原，不推家财数量。')
ev('fengxiang_people_request_li_return','追记凤翔民众拦马请求李从曮再镇凤翔',43,'将行，','镇凤翔，',[('李从曮','被民众请求复镇者'),('帝','被拦马请求者')],when='934年李从珂将离凤翔时；此句未独载月日',place='凤翔',note='民众未具名，不造虚构群体人物；遮马请求非已经任命。')
ev('congke_promises_li_return','李从珂答应凤翔民众请求',43,'帝许之，','帝许之，',[('帝','答应民众者'),('李从曮','所许复镇对象')],when='934年李从珂将离凤翔时；此句未独载月日',place='凤翔',note='承前请求，许为承诺，与五月实际任命分别。')
E['li']=ev('li_congyan_restored_fengxiang','李从曮改任凤翔节度使',43,'至是，','为凤翔节度使。',[('李从曮','凤翔节度使获任者'),('帝','任命者')],when='934年五月条下；旧末帝纪记于庚戌',place='凤翔',note='主至是本年五月，旧纪庚戌补日；不把此前离凤翔承诺当当天任命。')
claim('person',people['李继曮'],'aliases','本段缺字所指为李从曮，沿用既有李继曮主体。',43,'廢帝起鳳翔，將行，鳳翔人叩馬乞從曮。廢帝入立，復以從曮為鳳翔節度使，','同一拦马请复镇叙事与旧纪李從嚴同职核对；原书缺字不覆盖，曮／严属异写与缺字校核，不当普通繁简。',source='xinwudaishi-040-li-congyan-return')
claim('event',E['li'],'description','新李茂贞传附子记李从曮在废帝入立后复任凤翔节度使。',43,'廢帝入立，復以從曮為鳳翔節度使，','附子从曮承传首茂贞子，正文已回查；其卒年四十九未列发生年，不提前录死亡于934。',source='xinwudaishi-040-li-congyan-return',relation='corroborates')
claim('event',E['li'],'time_original','旧末帝纪五月庚戌条记郓州节度使李从严为凤翔节度使。',43,'鄆州節度使李從嚴為鳳翔節度使。','旧郓州与主天平为州及军号；本句承庚戌，主至是无独日，原严字保留。',source='jiuwudaishi-046-934-may-governors')
ev('fang_serves_northern_campaign_background','追记明宗为北面招讨使、房知温为副都部署，李从珂等事房',44,'初，','帝与别将事之，',[('明宗','北面招讨使'),('房知温','副都部署'),('帝','当时事房的将领')],year=None,when='明宗任北面招讨使时的追叙；确年未载',note='早年背景，不因段落归934就定934；别将未具名，房当时军职与此段所称平卢节度使不强定同时。')
E['quarrel']=ev('congke_fang_drinking_quarrel','追记李从珂与房知温曾饮酒争忿、拔刀相向',44,'尝被酒','拔刃相拟。',[('帝','与房饮酒争忿者'),('房知温','与李饮酒争忿者')],year=None,when='李从珂即位前的往事；确年未载',note='主省主语按前从珂事房及旧房传两人刀争核对，不编别将名单或酒争起因。')
claim('event',E['quarrel'],'description','旧房知温传也记与唐末帝失意杯盘、以白刃相恐。',44,'始與唐末帝嘗失意於杯盤間，以白刃相恐，','独立印证刀争双方；未载年，不把与接着入朝同定五月壬戌。',source='jiuwudaishi-091-fang-court',relation='corroborates')
ev('fang_li_plan_resist_congke','李从珂举兵入洛时房知温密与李冲谋拒',44,'及帝举兵入洛，','谋拒之，',[('房知温','密谋拒从珂者'),('李冲','平卢司马、密谋参与者'),('帝','被谋拒者')],when='934年李从珂举兵入洛期间；此句未独载月日',place='平卢、洛阳',note='李冲以房知温司马身份消歧；不并李再丰子或华州都监。谋拒是意向，未录已交战。')
claim('person',people['李冲（平卢司马）'],'description','新房知温传称李冲为房知温的司马。',44,'謂其司馬李沖曰：','主行军司字样与新司马核对；其生卒籍贯未载，不凭同名并入其他李冲。',source='xinwudaishi-046-fang-court')
claim('person',people['房知温'],'description','新房传记房知温自称钱数屋、兵数千，欲乘时建立功业。',44,'吾有錢數屋，養兵數千，因時建義，功必有成。','房本人说法及意向，不将钱屋数换算资产、不将声称兵数当精确军籍；新乘间窥觎与主谋拒各记来源。',source='xinwudaishi-046-fang-court')
ev('li_chong_requests_observe_court','李冲请先奉表观察洛中形势',44,'冲请先','以观形势，',[('李冲','奉表察形势建议者'),('房知温','被建议先察形势者')],when='934年李从珂举兵入洛期间；此句未独载月日',place='平卢、洛阳',note='请为建议，实际到京与称贺由新传另补，不把奏表具体文本编出。')
E['report']=ev('li_chong_returns_reports_stability','李冲返回报告洛中已安定',44,'还，','洛中已安定，',[('李冲','返报洛中安定者'),('房知温','听取报告者')],when='934年李从珂入洛以后、房知温入朝以前；确日未载',place='平卢、洛阳',note='安定为李报告，不代表全天下均已平定。')
claim('event',E['report'],'description','新房传补李冲到京时李从珂已即位，奉表称贺，回劝房知温入朝。',44,'及沖至京師，廢帝已入立，沖即奉表稱賀，還勸知溫入朝，','同一观察返报补实际行动；新传入立以后表贺，主谋拒是先前意向，两阶段不混。',source='xinwudaishi-046-fang-court')
E['court']=ev('fang_enters_court_apologizes','五月壬戌房知温入朝谢罪',44,'知温惧，','入朝谢罪，',[('房知温','入朝谢罪者')],when='934年五月壬戌',place='洛阳',note='恐惧为主书所记心理，入朝谢罪不等于依法定罪处罚。')
E['courtesy']=ev('congke_treats_fang_courteously','李从珂优礼房知温',44,'帝优礼之。','帝优礼之。',[('帝','优礼房者'),('房知温','受优礼者')],when='934年五月壬戌入朝条下',place='洛阳',note='主优礼及旧慰遣均非处死；新还镇封王与旧封先朝后职序不同另说明，不加无证封爵日。')
claim('event',E['court'],'description','旧房传记房知温赴洛申宿过并感新恩，末帝厚礼慰遣。',44,'知溫徑赴洛陽，申其宿過，且感新恩，末帝開懷以厚禮慰而遣之。','独立补入朝所申旧过与获遣，旧无确日；旧称末帝先封王宁之，新记还镇封王，先后各保，勿认主壬戌就是册封日。',source='jiuwudaishi-091-fang-court',relation='corroborates')
claim('event',E['courtesy'],'description','新房传也记废帝对房知温慰劳甚厚。',44,'廢帝慰勞之甚厚。','对应主优礼，未具日独立补，后封东平王未当主同日新任。',source='xinwudaishi-046-fang-court',relation='corroborates')
ev('fang_large_contribution','房知温贡献甚厚',44,'知温贡献','甚厚。',[('房知温','厚献者')],when='934年五月入朝条下；贡献未独列确日',note='无金额，不套新自称钱数屋或旧还镇积货数百万作此次献数。',place='洛阳')
ev('xu_zhi_xun_dies','吴镇南节度使、守中书令、东海康王徐知询去世',45,'吴镇南','徐知询卒。',[('徐知询','去世者')],when='934年五月条下；确日未载',note='复用徐知询，区别已死的徐知训；旧新未查到本次死亡独立补记，不伪造第二来源，不猜死因地点。')
claim('person',people['徐知询'],'death_year','徐知询于934年五月条下去世。',45,'吴镇南节度使、守中书令东海康王徐知询卒。','死亡年依主明确本年顺叙；只新增有出处事实，不覆写既有主体档案。')
ev('shu_takes_chengzhou','蜀军取得成州',46,'蜀人','取成州。',[],place='成州',note='主无将领、日、过程，不把孟知祥当亲征；其他书955年取成州不能拿来支持934这件事。')

reviews={35:'四月丙申葬明宗徽陵与从珂服丧护送宿陵分，非死日非五月祔庙；旧纪同日独证。',36:'五月丙午韩刘房三任分；韩主新胤旧允为同职同日异写，房主记旧事保底字。石李旧侍和不悦不定年，不重复前入朝；请归、劝留、韩李意见、信任表态与复任分。魏公主以旧933永宁石氏进封匹配，不推曹生母；复河东旧丙午补官，不等于抵达。',37:'戊午在丁未前保原顺序，旧亦戊午；陕州保义地名军号分，不擅改日。',38:'赵澄阶州刺史降蜀，尚无二十四史独立补记，不猜举州武力攻破与家属。',39:'戊申杨静难旧邠州同镇军号，旧前职更细；命与抵达分。',40:'主五月己酉举族迁成都，新六月至成都宴劳保迁与到达阶段，宴中病后死亡不前移，族无名单。',41:'庚戌冯出镇匡国旧同州，新明罢，保同平章事使相衔非继续中枢。',42:'主范无独日，旧新庚戌同条补，旧封齐国公补爵；範范同人。',43:'主李从私用字严，新从曮同拦马复镇旧从严同任，沿李继曮已有别名；供军资产、请、许、今任分。田千顷竹千亩未作主取资产量，卒49不定934。',44:'初北面及醉刀争不定年；934谋拒、李察京返报、房入朝优礼厚贡分。李冲限平卢司马不并华州都监或李再丰子。新自称兵钱仅引语；旧封王先朝、新返镇后封次序不同，主无封王日不造日。',45:'徐知询区别徐知训，主五月去世；未得独立补史死亡条不编，死因未载。',46:'蜀人取成州未名将无日，主体政权不做孟亲征；955年新史取成州是另一事件。'}
contexts=[]
for directory in sorted((P/'sources/context').iterdir()):
 r=json.loads((directory/'paragraph.json').read_text());contexts.append(dict(file=os.path.relpath(directory/'source.txt',P/'sources'),sha256=hashlib.sha256((directory/'source.txt').read_bytes()).hexdigest(),paragraph_id=r['id'],purpose='房知温及李茂贞附子从曮传首核对；不提前新增传中后事',url='https://github.com/greed-216/histree/blob/651c7870/'+str((directory/'source.txt').relative_to(ROOT))))
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(35,47):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(35,47)],next_paragraph='zztj-v279-y0934-p047',next_volume=279,next_year=934,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续934年第35—46正文段，原40—51行；明宗葬、石敬瑭请归与河东复任、五月任官、赵降蜀及张孙迁成都、李从曮复镇、房知温入朝与徐知询卒、蜀取成州。第47段六月重美授职待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(35,47)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
