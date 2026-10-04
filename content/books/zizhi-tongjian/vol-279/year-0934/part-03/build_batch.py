# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 9–13."""
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
 specs.append((directory.name,directory,'62cb1bdd','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-279-934-army',YEAR/'part-02/sources/library/tongjian-279-934-army','2ec8cf50','司马光等'),('jiuwudaishi-046-congke-hostages',YEAR.parent.parent/'vol-278/year-0934/part-01/sources/library/jiuwudaishi-046-congke-hostages','5d053db4','薛居正等'),('xinwudaishi-007-934-newyear',YEAR.parent.parent/'vol-278/year-0934/part-01/sources/library/xinwudaishi-007-934-newyear','5d053db4','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-army','tongjian-279-934-eastmarch']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p009-p013',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    if key.startswith('songshi-262-'):record=dict(record,section_title='卷262·赵上交传',citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
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
for n in range(9, 14):
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
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    if source.startswith('songshi-262-'):record=dict(record,citation='《宋史》卷262·赵上交传，段落 '+record['id']+'；EPUB卷题李濤傳沿卷内另一传主，正文已回查赵上交传，纸本待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷279·清泰元年（934；三月闵帝应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'潞王':'李从珂','王':'李从珂','帝':'李从厚','硃':'朱弘昭','朱':'朱弘昭','冯':'冯赟','洪实':'朱洪实','义诚':'康义诚','从荣':'李从荣','尼惠明':'李幼澄','惠明':'李幼澄','鄩':'刘鄩','德胜':'王德胜（王思同子）','守钧':'赵守钧（王思同故人）'}
NEW_ALIASES={'刘遂雍':['劉遂雍'],'刘延朗':['劉延朗'],'王景从':['王景從'],'王德胜（王思同子）':['王德勝（王思同子）'],'赵守钧（王思同故人）':['趙守鈞（王思同故人）']}

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
    if when is None:when='934年三月条下；确日未独载'
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




# Consecutive paragraphs 9–13. Speeches, promises and alleged motives retain their attribution.
ev('fengxiang_outer_gates_captured','三月乙卯诸道兵攻凤翔，克东西关城',9,'乙卯，','城中死者甚众。',[],when='934年三月乙卯',place='凤翔东西关城',note='所克为东西关城，不当凤翔内城已经陷落；死者甚众无确数不编。')
ev('fengxiang_renewed_assault','三月丙辰诸道兵再次进攻凤翔城',9,'丙辰，','众心危急，',[],when='934年三月丙辰',place='凤翔',note='城堑卑浅守备乏为主概述，不臆测城墙高度；期必取为攻方意图，不当已攻陷。')
ev('congke_wall_appeal','李从珂登城哭诉，呼吁攻城军念旧',9,'潞王登城','闻者哀之。',[('潞王','登城向外军哭诉者')],when='934年三月丙辰攻城条下',place='凤翔城上',note='未冠百战金创及无罪是本人申说，完整保发言层，不据此给精确入伍年龄、战役数或诊断伤情。')
ev('zhang_drives_soldiers_and_escapes','张虔钊持刃催兵登城，士卒反攻，张跃马逃脱',9,'张虔钊性','走免，',[('张虔钊','主攻西南、催兵后遭反攻而逃者')],when='934年三月丙辰攻城条下',place='凤翔城西南',note='褊急是史家评语；走免不是阵亡，未名反攻士卒不造首领。')
ev('yang_siquan_surrenders','杨思权率诸军解甲降李从珂，由西门入城',9,'杨思权因大呼','自西门入，',[('杨思权','号召解甲入城请降者'),('潞王','接受请降的城中首领')],when='934年三月丙辰攻城条下',place='凤翔西门',note='大相公吾主为杨号召，不当此时从珂已正式即帝位。')
ev('yang_requests_governorship','杨思权递纸请求克京城后任节度使',9,'以幅纸进潞王曰：','勿以为防、团。”',[('杨思权','请求节度而不愿防御团练者'),('潞王','受请者')],when='934年三月丙辰入城后',note='愿王克京城日为条件与将来期望，不把京城已克或官职已正式完成。')
ev('congke_promises_yang_binning','李从珂书授杨思权可为邠宁节度使',9,'潞王即书','授之。',[('潞王','书授者'),('杨思权','获可任邠宁书授者')],when='934年三月丙辰入城后',note='临战纸授为从珂承诺，非现任闵帝正式制授，也不当同日实际到邠宁接镇。')
ev('wang_continues_attack_unaware','王思同尚不知西军倒戈，继续催兵登城',9,'王思同犹','趣士卒登城，',[('王思同','尚未知倒戈的催兵主帅')],when='934年三月丙辰攻城条下',place='凤翔')
ev('yin_calls_for_surrender','尹晖呼称西军已入城受赏，军士弃甲投降',9,'尹晖大呼','其声震地。',[('尹晖','号召入城受赏者')],when='934年三月丙辰攻城条下',place='凤翔',note='受赏为尹的号召，未据此提前断定每人已拿同额赏钱。')
ev('fengxiang_army_collapses','丙辰日中军士悉入凤翔，外军溃散，王思同等逃走',9,'日中，','皆遁去。',[('王思同','诸节度使逃走者中明名一人')],when='934年三月丙辰日中',place='凤翔',note='主思同等六节度使未列全，不将上一段五人一概填成六人的具体名单。')
ev('congke_collects_rewards_fengxiang','李从珂收取凤翔将吏士民财物犒军，鼎釜亦估价给军',9,'潞王悉敛','估直以给之。',[('潞王','收财及犒军者')],when='934年三月丙辰军溃后附记；独日未载',place='凤翔',note='悉敛为主叙述，不能编每户额度；旧十七日即丁巳记收财，与主未独日并列。')
ev('suiyong_refuses_wang_entry','三月丁巳王思同、药彦稠到长安，被刘遂雍拒入后奔潼关',9,'丁巳，','乃趣潼关。',[('王思同','从凤翔败走者'),('药彦稠','共同败走者'),('刘遂雍','西京副留守、闭门拒入者')],when='934年三月丁巳',place='长安、潼关',note='趣潼关为改道奔赴，未独载抵达日；拒入与下一段奖潞军分开。')
relationship('刘鄩','刘遂雍','父亲',9,'遂雍，鄩之子也。','刘鄩→刘遂雍为父亲；本段刘遂雍全名与末句鄩对应已有刘鄩，不猜其生母为父妾王氏。')
ev('congke_organizes_eastward_march','李从珂建大将旗鼓、整军东进',10,'潞王建','整众而东，',[('潞王','建旗鼓整军东进者')],when='934年三月凤翔军变后、庚申到长安前；旧纪记丁巳整众而东',place='凤翔东出',note='将旗鼓是军事仪制，不当已经正式皇帝即位。')
ev('congke_trusts_liu_yanlang','李从珂以孔目官刘延朗为腹心',10,'以孔目官','为腹心。',[('潞王','倚为腹心者'),('刘延朗','孔目官、被倚重者')],note='本批所见孔目官身份，后来枢密副职不提前录；不新建含糊统属关系。')
claim('person',people['刘延朗'],'description','刘延朗为虞城人。',10,'孔目官虞城刘延朗','籍虞城仅作为身份，不换现代地名坐标。')
ev('congke_fears_changan_resistance','李从珂起初忧王思同等合力据长安抵抗',10,'潞王始忧','据长安拒守，',[('潞王','担忧者'),('王思同','被设想据守者')],when='934年三月东进初期；确日未载',note='始忧为从珂担忧，不能当王已经据长安建立防线。')
ev('congke_reassures_suiyong','李从珂至岐山闻刘遂雍拒王思同，遣使慰抚',10,'至岐山，','遣使慰抚之，',[('潞王','闻讯喜并遣使者'),('刘遂雍','受慰抚者')],place='岐山、长安',note='未名使者不补；闻拒入是接上一段已发生行为，不另新建一次拒入。')
ev('suiyong_rewards_vanguard','刘遂雍出府库财，给到达的潞军前锋赏赐并令过城',10,'遂雍悉出','皆不入城。',[('刘遂雍','出财赏前军者')],when='934年三月庚申从珂到长安前',place='长安城外',note='给赏令过与前军皆不入城，不当军士入城抢掠；府库财与随后民财分。')
ev('congke_arrives_changan','三月庚申李从珂至长安，刘遂雍迎谒并收民财赏军',10,'庚申，',None,[('潞王','到长安者'),('刘遂雍','迎谒及率民财者')],when='934年三月庚申',place='长安',note='率民财是本次赏军来源，不编征收制度或每户定额。')
ev('wang_jingcong_reports_defeat','三月庚申王景从等从军前返回，朝野震惊',11,'是日，','中外大骇。',[('王景从','西面步军都监、自军前返回者')],when='934年三月庚申',place='后唐朝廷',note='是日承上段庚申；旧同日奏十五攻十六降证明执行与奏报不是同一日。')
ev('conghou_offers_to_yield','李从厚对康义诚等表示想迎李从珂、让大位',11,'帝不知所为，','亦所甘心。”',[('帝','表示迎兄让位意向者'),('义诚','受言者')],when='934年三月庚申军败消息到后',note='欲自迎大位让为意向，未当正式退位或已交付帝位；先帝去世继立经过为闵帝自述，不重新定933前事。')
ev('zhu_feng_silent_at_yield_offer','朱弘昭、冯赟听闵帝欲让位，大惧不答',11,'硃弘昭、','不敢对。',[('朱','大惧不答者'),('冯','大惧不答者')],when='934年三月庚申军败消息到后')
ev('kang_requests_guard_campaign','康义诚请求率侍卫兵出征，史叙其意在迎降邀功',11,'义诚欲悉','幸陛下勿为过忧！”',[('义诚','表请自行、被史书述有迎降意者'),('帝','受表请的君主')],when='934年三月庚申条下',note='迎降为史述意图与表面振军奏辞区分，不当已经率宿卫投降。')
ev('conghou_summons_shi','李从厚遣使召石敬瑭，想让其领兵抵抗',11,'帝遣使召','欲令将兵拒之。',[('帝','遣使召将者'),('石敬瑭','被召且拟领兵者')],when='934年三月庚申条下',note='欲令是拟派，没有写石已同意、已领兵或已与潞军交战。')
ev('conghou_rewards_troops','康义诚坚持自行，李从厚慰谕将士并尽府库财赏军',11,'义诚固请自行，','空府库以劳之，',[('义诚','坚持请自行者'),('帝','慰谕及颁赏者')],when='934年三月庚申条下',place='后唐朝廷',note='空府库为主记颁赏，不另推国家财政账或确额。')
ev('conghou_promises_extra_rewards','李从厚许平凤翔后每人再赏二百缗，不足则继以宫中服玩',11,'许以平凤翔，','宫中服玩继之。',[('帝','许附条件赏赐者')],when='934年三月庚申条下',note='许平凤翔为附条件承诺，不当二百缗已全发，不把服玩已全部变卖。')
ev('troops_demand_another_reward','军士负赏物，在路上扬言到凤翔还要再请一份',11,'军士益骄，','更请一分。”',[],when='934年三月庚申颁赏后附记',note='益骄为史家评语，未名军士不补领头者；再请是要求非又得赏。')
ev('chongji_killed_songzhou','朝廷遣楚匡祚在宋州杀李重吉，楚拷打索财',11,'遣楚匡祚','责其家财。',[('楚匡祚','奉遣杀人、榜棰索财者'),('李重吉','被拷打及杀害者')],when='934年三月庚申条下；处决确日未独载',place='宋州',note='与前批拘幽不同，是今处决；此句无独干支不硬认杀日庚申。')
ev('youcheng_huiming_killed','尼惠明即李幼澄一并被杀',11,'又杀尼惠明。','又杀尼惠明。',[('尼惠明','被杀的李从珂女')],when='934年三月庚申条下；处决确日未独载',note='沿已据旧废帝纪核实的惠明大师幼澄，不混他人。省主语不认楚也亲杀尼，后举哀日不是死亡日。')
ev('hongshi_favored_by_congrong','追叙朱洪实曾受秦王李从荣厚待',12,'初，马军都指挥使','为秦王从荣所厚，',[('洪实','曾被秦王厚待者'),('从荣','厚待朱者')],year=None,when='初字追叙；秦王生前往事，确年月未载',note='后文以宗史事朱弘昭疑字保在出处，不据此建立宗兄或血亲边。')
claim('person',people['朱洪实'],'description','朱洪实曾为孟汉琼率兵击秦王，康义诚由此恨之。',12,'从荣勒兵天津桥，洪实首为孟汉琼击从荣，康义诚由是恨之。','933已录孟令五百骑讨秦事件，今为追叙补因；不重复新建933同一军事行动，不造永久仇敌边。')
ev('conghou_left_storehouse_gifts','三月辛酉李从厚亲至左藏，给将士金帛',12,'辛酉，','给将士金帛。',[('帝','亲往给赏者')],when='934年三月辛酉',place='左藏',note='与庚申尽府库赏军分属主书分日记，未载不同库余额不自行解释。')
ev('hongshi_advocates_luoyang_defense','朱洪实主张禁军守洛阳，再徐图进取',12,'义诚、洪实共论','可以万全。”',[('洪实','提出固守建议者'),('义诚','论兵对方')],when='934年三月辛酉条下',place='洛阳（拟守目标）',note='主张与推断敌不敢前为论兵意见，不当该守策已实施成功。')
ev('kang_hongshi_accuse_each_other','康义诚、朱洪实争论用兵，互指对方欲反',12,'义诚怒曰：','其声渐厉。',[('义诚','指洪实反者'),('洪实','回指康反者')],when='934年三月辛酉条下',note='互斥欲反为当事人指控，不替任一方证实已反；不新增叛乱完成事件。')
ev('conghou_questions_guard_commanders','李从厚召问康义诚与朱洪实，两人在帝前争辩',12,'帝闻，','帝不能辨其是非，',[('帝','召讯而未辨者'),('义诚','帝前争辩者'),('洪实','帝前争辩者')],when='934年三月辛酉条下')
ev('hongshi_executed','三月辛酉李从厚斩朱洪实，军士更愤怒',12,'帝不能辨其是非，',None,[('帝','未辨是非而处决者'),('洪实','被斩的马军都指挥使')],when='934年三月辛酉',note='既有洪实/弘实为同人，新记杀朱弘实而非朱弘昭；军怒为主叙不补统计。')
ev('congke_hears_wang_captured','三月壬戌李从珂到昭应，听闻前军获王思同',13,'壬戌，','亦可嘉也。”',[('潞王','到昭应闻讯并评价者'),('王思同','已被前军获的主帅')],when='934年三月壬戌',place='昭应',note='听闻与押到问答分，未给实际被获独日；尽心可嘉是从珂评价。')
ev('wang_delivered_to_lingkou','三月癸亥王思同被押到灵口，与李从珂问答',13,'癸亥，','公且休矣。”',[('潞王','到灵口责问后改容者'),('王思同','被押到并陈述忠于先帝者')],when='934年三月癸亥',place='灵口',note='起行间富贵祸殃、无面见先帝均王自述，不单独重建不明年官历；休矣不当已正式释放。')
ev('congke_intends_spare_wang','李从珂欲赦王思同，杨思权一党耻见其面',13,'王欲宥之，','耻见其面。',[('潞王','有意宥王者'),('王思同','拟获宥对象'),('杨思权','史记其徒耻见王者')],when='934年三月王押至灵口后；独日未载',note='欲宥不等赦放完成，耻见是史述动机，不列未知同党名单。')
ev('yin_seizes_wang_household','追记李从珂过长安时，尹晖取王思同家资及妓妾',13,'王之过长安，','家资及妓妾，',[('尹晖','取财及妓妾者'),('王思同','家资被取者')],when='934年三月过长安时追记；独日未载',place='长安',note='追记与后灵口醉中处置分，不把妓妾具名或推具体婚姻关系。')
ev('yin_urges_removing_wang','尹晖屡向刘延朗称留王思同会失士心',13,'屡言于刘延朗曰：','虑失士心。”',[('尹晖','屡陈不可留王者'),('刘延朗','受言者'),('王思同','被排斥对象')],when='934年三月尹取财后、王遇害前；独日未载',note='虑失士心是尹主张，不当调查证明所有军士都要求杀王。')
ev('wang_sitong_family_killed_without_order','李从珂醉时，王思同及妻子被擅杀',13,'属王醉，','擅杀思同及其妻子。',[('王思同','被擅杀者'),('潞王','醉中未获报的主事者')],when='934年三月王被押问后；主未独载遇害干支',place='李从珂行军途中',note='主不待报擅杀不明确直接行刑者，故不指定刘亲手杀；旧本传并子德胜，新记从珂乃杀之，责任与被害家属范围异说并列。')
ev('congke_regrets_wang_death','李从珂醒后怒刘延朗，为王思同嗟惜数日',13,'王醒，',None,[('潞王','醒后怒及嗟惜者'),('刘延朗','受责者'),('王思同','被嗟惜者')],when='934年三月王被擅杀后数日；独起日未载',note='累日为延续，不确定结束日或醉日；与新书从珂下杀的异说分层保。')
old='jiuwudaishi-045-934-defeat-reports';wang='xinwudaishi-033-wang-sitong';oldwang='jiuwudaishi-065-wang-sitong-death';sui='xinwudaishi-022-liu-suiyong';yan='xinwudaishi-027-liu-yanlang';hostages='jiuwudaishi-046-congke-hostages';new='xinwudaishi-007-934-newyear'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='按同人行动与日期核对，保原字及主补书差异；纸本待核。'):
 claim('event','event_zztj_279_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('yang_siquan_surrenders',old,'今月十五日，','山南軍潰。','旧闵帝纪庚申王景从奏称十五日攻城、十六日尹东杨西入城，山南军溃。',9,relation='adds',note='奏报庚申不等倒戈日；十六日对应主丙辰，旧尹严卫右厢与前段主左厢职位表述差异保。')
supp('fengxiang_army_collapses',new,'三月丙辰，','叛降于從珂。','新闵帝纪同记三月丙辰军溃、尹晖杨思权叛降。',9)
supp('zhang_drives_soldiers_and_escapes',wang,'興元張虔釗攻城西，','虔釗走。','新王思同传同记张虔钊催攻城西过急、军士反攻，张走；主写西南。',9,relation='adds')
supp('suiyong_refuses_wang_entry',sui,'潞王從珂反於鳳翔，','悉封府庫以待潞王。','新刘鄩传末刘遂雍事记拒王思同、封府库待李从珂。',9,relation='adds',note='正文传主沿刘鄩传子刘遂雍段，电子卷题不另猜刘独立专传；后入立淄州职不提前记。')
supp('congke_collects_rewards_fengxiang',hostages,'十七日，','以賞軍士。','旧废帝纪明确十七日收居民家财赏军，主军溃后附记无独日。',9,relation='adds')
supp('congke_organizes_eastward_march',hostages,'十七日，','帝整眾而東。','旧废帝纪承十七日记整众东进，与新丁巳东行对应。',10,relation='adds')
supp('congke_arrives_changan',hostages,'二十日，','京兆居民家財犒軍。','旧废帝纪二十日到长安、刘遂雍以城降、率京兆民财犒军，与主庚申相合。',10,relation='adds')
supp('suiyong_rewards_vanguard',sui,'潞王前軍至者，','悉以金帛給之。','新刘鄩传末同记刘遂雍给潞王前军金帛。',10)
claim('person',people['刘延朗'],'description','刘延朗为宋州虞城人，凤翔起兵时为孔目官。',10,'劉延朗，宋州虞城人也。','新刘延朗传直接籍贯补，主虞城；宋州为所属史称，不换现代行政区。',source=yan,relation='adds')
supp('congke_trusts_liu_yanlang',yan,'初，廢帝起於鳳翔，','而延朗為孔目官。','新刘延朗传记凤翔起兵时孔目官刘延朗为共事五人之一。',10,relation='adds',note='只补刘身份，不凭本段五人列名提前建其他四人的新关系或事件。')
supp('wang_jingcong_reports_defeat',old,'庚申，','山南軍潰。','旧闵帝纪同庚申王景从回报三月十五日攻、十六日尹杨入城。',11)
supp('conghou_offers_to_yield',old,'帝聞之，','於理為便。','旧闵帝纪同记闵帝表示欲迎兄主社稷、自归藩。',11,note='仍是主上言辞与意向，不当正式退位已发生。')
supp('conghou_rewards_troops',old,'乃出銀絹錢','更請一分。','旧闵帝纪同记出银绢钱厚赏至府藏空、军士扬言再请。',11,relation='adds')
supp('conghou_left_storehouse_gifts',old,'辛酉，','視給將士金帛。','旧闵帝纪同辛酉亲临左藏视给将士金帛。',12)
supp('hongshi_executed',old,'是日，誅馬軍','忿爭故也。','旧闵帝纪辛酉诛马军朱洪实，记因与康义诚忿争。',12)
supp('hongshi_executed',new,'辛酉，殺侍衞','朱弘實。','新闵帝纪同辛酉杀朱弘实，弘实与主洪实沿同人异名。',12)
supp('wang_delivered_to_lingkou',oldwang,'二十二日，','且憩歇。','旧王思同传将献俘及问答系于二十二日昭应，主壬戌闻获、癸亥灵口押到问答分两日两地。',13,relation='conflicts',note='旧二十二日昭应与主二十三日灵口问答位置分歧并列，不能将两书强统一。')
supp('wang_sitong_family_killed_without_order',oldwang,'屬王醉，','累日嗟惜之。','旧王思同传同记王醉不待报杀思同，并明列其子德胜；王醒怒刘延朗嗟惜。',13,relation='adds',note='旧明德胜、主妻子范围不等，保分别被害范围；直接行刑人仍未名，不推刘亲手行刑。')
supp('wang_sitong_family_killed_without_order',wang,'從珂引兵東，','乃殺之。','新王思同传记从珂至昭应前锋执王，问答后从珂愧其言乃杀之。',13,relation='conflicts',note='新直接写从珂杀，与主旧醉中不待报、醒后嗟惜责任叙述不同；全部保出处，不抹平。')
supp('wang_sitong_family_killed_without_order',hostages,'二十三日，','誅王思同。','旧废帝纪二十三日至灵口诛王思同，与主灵口押至后未独杀日的叙法不同。',13,relation='adds',note='旧帝纪二十三日直言诛，主未独干支且说擅杀；不拿帝纪统称覆盖本传与主责任叙述。')
q=excerpt(oldwang,'屬王醉，','殺思同並其子德勝。')
event('wang_desheng_killed','王思同之子德胜与父一同被杀',13,q,[('德胜','旧本传明名被杀的王思同之子')],source=oldwang,when='934年三月王醉时被擅杀；旧本传本句无独日',note='旧传补具名儿子，主妻子未名；规范名带父亲消歧，不猜妻名或其他子女。')
relationship('王思同','德胜','父亲',13,'殺思同並其子德勝。','王思同→其子德胜为父亲，补书明确，不另造反向子边。',source=oldwang)
q=excerpt(oldwang,'顧謂趙守鈞曰：','達予撫慰之意。')
event('zhao_shoujun_sent_to_wang','李从珂令赵守钧在路迎王思同并传慰意',13,q,[('潞王','命故人迎慰者'),('守钧','王思同故人、受命迎慰者'),('王思同','拟受迎慰者')],source=oldwang,when='旧本传934年三月二十二日昭应段下；主无此具名使者',note='旧传独立补使者身份、属命令，不推迎接已完成。赵名带王思同故人消歧，不与可能守均同名者强合。')
reviews={9:'乙卯攻东西关、丙辰再攻与潞王哭诉、张驱卒反攻逃、杨降西入请节度纸授、王未知督战、尹呼降、日中军溃、收民财、丁巳长安拒门奔关逐项分。檄哭词与赏诺保发言和将来条件，邠宁纸授不是已抵任正式制。六节度未全名不猜，旧十七收财补，刘遂雍父刘鄩明示，母不推王淑妃。',10:'旗鼓东进、刘腹心、虑王据长安、岐山闻讯慰抚、府库外赏前军不入城、庚申入长安收民财分；府库财与民财区别。新补刘延朗宋州虞城孔目官，不提前枢密职；旧十七东进、二十长安补日期。',11:'是日承庚申，王景从奏与十五攻十六降分。闵帝让位是欲，康表面出征奏与史书迎降意图分，召石欲领兵不当已出。库赏已给与平凤翔后再二百承诺分，服玩未当已变卖。楚宋州拷索杀重吉与前拘幽分，尼惠明幼澄沿旧名，不以举哀日作死日，不擅楚亲杀尼。',12:'初朱受秦厚为追叙未定年；宗史字疑在来源保不造血亲。933讨秦已有稳定事件，今只添朱与康恨的追叙人物事实不重复战事。辛酉临左藏、朱守洛建议、互斥欲反、帝前争、帝斩朱分。新朱弘实与主洪实同人非弘昭，军怒不编数。',13:'壬戌昭应听获与癸亥灵口押至问答分；旧本传二十二日昭应问答并列地日异说。王欲宥未成、尹取家资追叙、屡告刘、醉不报杀、醒怒嗟惜分。主旧责任为醉中擅杀，新直接从珂乃杀；旧帝纪二十三灵口诛为另一统叙，主杀日未独干支不强定。旧明子德胜补具名与父边、旧赵守钧故人奉迎命令补，姓名带情境消歧。新王传使郝诩与既有主赧诩另作疑字对照，当前不新建郝重复主体。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9,14):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(9,14)],next_paragraph='zztj-v279-y0934-p014',next_volume=279,next_year=934,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷279连续934年第9—13正文段，原14—18行；凤翔军变东进、闵帝赏军与楚杀子女、斩洪实及思同遇害。本年共89正文段，第14段康义诚西行与潞军进陕仍待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(9,14)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
