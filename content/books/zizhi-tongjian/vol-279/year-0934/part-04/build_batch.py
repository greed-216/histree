# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 934 paragraphs 14–18."""
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
 specs.append((directory.name,directory,'d4437e45','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-279-934-eastmarch',YEAR/'part-03/sources/library/tongjian-279-934-eastmarch','62cb1bdd','司马光等'),('jiuwudaishi-046-congke-hostages',YEAR.parent.parent/'vol-278/year-0934/part-01/sources/library/jiuwudaishi-046-congke-hostages','5d053db4','薛居正等'),('xinwudaishi-007-934-newyear',YEAR.parent.parent/'vol-278/year-0934/part-01/sources/library/xinwudaishi-007-934-newyear','5d053db4','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-eastmarch','tongjian-279-934-palace-flight','tongjian-279-934-weizhou']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0934-p014-p018',
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
for n in range(14, 19):
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
        citation = f'卷279·清泰元年（934；三、四月闵帝应顺元年）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0934_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'潞王':'李从珂','王':'李从珂','帝':'李从厚','闵帝':'李从厚','弘昭':'朱弘昭','冯':'冯赟','义诚':'康义诚','太后':'曹氏（李嗣源后）','太妃':'王淑妃','明宗':'李嗣源','陈晖':'陈晖（石敬瑭亲将）'}
NEW_ALIASES={'康思立':[],'慕容迁':['慕容遷'],'卢导':['盧導'],'沙守荣':['沙守榮'],'奔洪进':['奔洪進','奔弘进','奔弘進'],'陈晖（石敬瑭亲将）':['陳暉（石敬瑭親將）']}

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
    if when is None:when='934年四月条下；确日未独载' if n>=17 else '934年三月条下；确日未独载'
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




# Consecutive paragraphs 14–18. Narrative allegations and reported arrivals are not confirmed acts.
q=span(14,'癸亥，','以王思同副之。')
for code,name,title,role in [('kang','康义诚','康义诚制授凤翔行营都招讨使','制授招讨使者'),('wang','王思同','王思同被制授副招讨使','文书任副的对象')]:
 event('campaign_new_command_'+code,'三月癸亥'+title,14,q,[(name,role)],when='934年三月癸亥',note='朝廷文书任命与执行区分；前段思同已被获遇害，主仍列制书任副，不当复活或已经就副职，亦不猜朝廷何时获知死讯。')
ev('congke_detains_yao_huazhou','三月甲子李从珂到华州，捕药彦稠并囚之',14,'甲子，','囚之。',[('潞王','到华州拘人者'),('药彦稠','被捕囚者')],when='934年三月甲子',place='华州',note='捕囚与后来处死分，本句不提前记药已死。')
ev('congke_reaches_wenxiang','三月乙丑李从珂到阌乡',14,'乙丑，','至阌乡。',[('潞王','到阌乡者')],when='934年三月乙丑',place='阌乡')
ev('reinforcements_surrender_to_western_army','朝廷所发诸军遇西军即迎降，主书说未有交战',14,'朝廷前后所发','无一人战者。',[],note='按本段继续派援诸军概述，不能覆盖此前凤翔实际攻城交战；未列具体部队，不给归降总人数。')
ev('kang_leaves_luoyang','三月丙寅康义诚率侍卫兵自洛阳出发',14,'丙寅，','发洛阳，',[('义诚','领侍卫兵出发者')],when='934年三月丙寅',place='洛阳',note='出发与到新安散兵、干壕请降分。')
ev('an_congjin_capital_patrol','三月丙寅安从进受诏任京城巡检',14,'诏以侍卫','京城巡检；',[('安从进','原侍卫马军指挥使、新京城巡检')],when='934年三月丙寅',place='洛阳',note='旧原侍卫职与今巡检不混；旧纪此诏置乙亥条、主丙寅，保历日异说不擅改底本。')
ev('an_congjin_congke_letter_background','追记安从进已得李从珂书信，暗布腹心',14,'从进已受','潜布腹心矣。',[('安从进','受书并布腹心者'),('潞王','给书者')],year=None,when='巡检授职前已受书的追记；起日与布人年月未独载',note='已受书不当书信内容逐项明载，不编布人名单；此前行动确时不强定丙寅。')
ev('congke_reaches_lingbao','三月丙寅李从珂到灵宝',14,'是日，','潞王至灵宝，',[('潞王','到灵宝者')],when='934年三月丙寅',place='灵宝',note='是日承丙寅。')
q=span(14,'护国节度使','皆降，')
for code,name,role in [('yanwei','安彦威','护国节度使、降者'),('zhongba','安重霸','匡国节度使、降者')]:
 event('lingbao_surrender_'+code,'三月丙寅'+name+'降李从珂',14,q,[(name,role),('潞王','受降者')],when='934年三月丙寅',place='灵宝',note='两镇节度本人降与镇地全部完成改隶不同，不推已授新职。')
ev('kang_sili_plans_resistance','康思立想守陕城等康义诚援军',14,'惟保义节度使','以俟康义诚。',[('康思立','保义节度使、拟守陕城者'),('义诚','被期待来援者')],when='934年三月丙寅条下',place='陕城',note='谋固守是初拟计划，不当已实现持久守城或康军已到。')
ev('pengsheng_vanguard_background','追记戍陕西的捧圣五百骑成为李从珂前锋',14,'先是，','为潞王前锋，',[('潞王','拥有该前锋者')],year=None,when='先是追记；捧圣骑原戍及转前锋确年月未独载',place='陕西',note='五百为主数，不能据此编每次出发日或各骑姓名。')
ev('vanguard_claims_new_emperor','潞军前锋到陕城下，宣称十万禁军已奉新帝',14,'至城下，','人涂地耳。”',[],when='934年三月进陕条下；独日未载',place='陕城下',note='十万已奉新帝为城下劝降宣传，不当已核兵数或从珂此时正式即帝位。')
ev('kang_sili_forced_to_welcome','捧圣卒争出迎潞军，康思立无法制止，亦出迎',14,'于是捧圣卒','不得已亦出迎。',[('康思立','不能制止出迎、最终亦迎者')],when='934年三月进陕条下；独日未载',place='陕城',note='先谋守后出迎分；出迎不自动记为签订具体盟约。')
ev('congke_reaches_shan','三月丁卯李从珂到陕',14,'丁卯，','潞王至陕，',[('潞王','到陕者')],when='934年三月丁卯',place='陕')
ev('retinue_advises_pause_and_reassure','李从珂僚佐因传闻闵帝播迁，劝在陕暂停并慰京人',14,'僚佐说王曰：','京城士庶。”',[('潞王','受僚佐建议者')],when='934年三月丁卯条下',place='陕',note='传闻乘舆播迁是消息，不能据此将后段戊辰出奔提前定为已经发生；僚佐未名不猜。')
ev('congke_reassures_luoyang_except_two_clans','李从珂移书安抚洛阳，唯朱弘昭、冯赟两族不赦',14,'王从之，','勿有忧疑。',[('潞王','发安抚及不赦声明者'),('弘昭','不赦声明涉及者'),('冯赟','不赦声明涉及者')],when='934年三月丁卯条下',place='洛阳（移书对象）',note='声明不赦不是已经屠尽两族，与后段冯族被灭事实分。')
ev('kang_troops_desert_xinan','康义诚至新安，军士结群弃兵争赴陕降',14,'康义诚军至新安，','累累不绝。',[('义诚','部下大量脱离的主将')],when='934年三月洛阳出发后；到新安独日未载',place='新安、陕',note='百什为群是分群概述，不编累计十万或某确总数。')
ev('kang_requests_surrender_ganhao','康义诚至干壕只余数十部下，托潞军候骑请降',14,'义诚至干壕，',None,[('义诚','解弓剑为信、请求降者'),('潞王','受请降对象')],when='934年三月新安散兵后；独日未载',place='干壕',note='数十部下、十余候骑为原数；请降与下段到陕被责、暂宥分。主侯骑词疑沿引文，展示为候骑。')
ev('conghou_summons_zhu_after_defeat','三月戊辰李从厚闻潞军到陕、康军溃，急召朱弘昭谋去向',15,'戊辰，','谋所向，',[('闵帝','闻军溃急召者'),('弘昭','被召谋去向者')],when='934年三月戊辰',note='急召谋所向与朱自认为被罪不同，不当帝明确下诛朱令。')
ev('zhu_hongzhao_suicide','朱弘昭以为急召欲罪己，投井死',15,'弘昭曰：','赴井死。',[('弘昭','自疑被罪而投井死者')],when='934年三月戊辰条下；新纪置丁卯',note='欲罪之也为朱自言，新与主日期一日差异并列，不当他已被押诛。')
ev('an_congjin_kills_feng_clan','安从进听朱死后，杀冯赟并灭其族',15,'安从进闻弘昭死，','灭其族，',[('安从进','杀冯及族者'),('冯赟','被杀者')],when='934年三月戊辰条下；新纪置丁卯',place='冯赟宅第',note='族人未名不逐人编造；主灭其族与第14段不赦声明不同。')
ev('an_sends_heads_to_congke','安从进将朱弘昭、冯赟首级送李从珂',15,'安从进闻弘昭死，','传弘昭、赟首于潞王。',[('安从进','传两首者'),('弘昭','首被传者'),('冯赟','首被传者'),('潞王','首级送达对象')],when='934年三月戊辰条下；实际送到日未载',note='传首是派送行为，不凭此句定从珂何日验收。')
ev('conghou_orders_meng_prepare_weizhou','李从厚想奔魏州，召孟汉琼先往准备',15,'帝欲奔魏州，','为先置；',[('帝','拟奔魏州、下召者'),('孟汉琼','被召先置者')],when='934年三月戊辰条下',place='魏州（拟往）',note='欲奔不等成功到魏州，先置是命令不是准备已完成。')
ev('meng_refuses_summons_heads_shan','孟汉琼不应召，单骑奔陕',15,'汉琼不应召，','单骑奔陕。',[('孟汉琼','拒召另奔陕者')],when='934年三月戊辰条下',place='陕（奔赴目标）',note='另奔与后段渑池见潞王被斩分，不当已因旧恩获留用。')
ev('murong_qian_trust_background','追叙李从厚在藩爱信慕容迁，即位后授控鹤指挥使',15,'初，帝在籓镇，','以为控鹤指挥使；',[('帝','此前爱信及即位后任用者'),('慕容迁','此前牙将、后控鹤指挥使')],year=None,when='初字追叙；藩镇爱信与即位后任用确日未独载',note='任控鹤虽在933即位后，但无确日可能跨年，不强塞934三月；爱信不造养父或结义边。')
ev('conghou_assigns_murong_gate','李从厚拟北渡河，密令慕容迁领兵守玄武门',15,'帝将北渡河，','守玄武门。',[('帝','密令守门者'),('慕容迁','奉令守门的部将')],when='934年三月戊辰出奔前',place='玄武门',note='守门任令与下一句出门后的关闭分；将北渡是意图，不当已渡河。')
ev('conghou_leaves_xuanwu_gate','三月戊辰夜李从厚以五十骑出玄武门，令慕容迁控鹤兵跟随',15,'是夕，','汝帅有马控鹤从我。”',[('帝','出门并令骑兵随行者'),('慕容迁','受命随行者')],when='934年三月戊辰夜',place='洛阳玄武门',note='原文谓迁曰缺开引号保底字；主五十骑、旧出门百骑有数差，不调平。玄/元为门名异字保。')
ev('murong_closes_gate_does_not_follow','慕容迁口称生死相从，却在帝出后闭门不行',15,'迁曰：','即阖门不行。',[('慕容迁','口许却闭门不从者'),('帝','被拒随的出奔君主')],when='934年三月戊辰夜',place='玄武门',note='阳为团结表示佯作整队，不当其真的随帝至魏州。')
ev('ministers_learn_flight_at_duanmen','三月己巳冯道等到端门，得知朱冯死、帝北走',15,'己巳，','帝已北走。',[('冯道','入朝获讯者')],when='934年三月己巳',place='洛阳端门',note='获讯与死亡发生日分，不把朱冯死改己巳。')
ev('li_yu_proposes_empress_instructions','冯道、刘昫欲归，李愚主张到中书向太后请示',15,'道及刘昫欲归，','人臣之义也。”',[('冯道','拟归者'),('刘昫','拟归者'),('李愚','建议请示太后者'),('太后','拟请示的曹太后')],when='934年三月己巳',place='洛阳',note='主张与已取太后令不同；此时曹氏为明宗皇后太后，不推两帝生母。')
ev('feng_dao_advocates_waiting_home','冯道主张无君不宜入宫，归家等待潞王教令',15,'道曰：','乃归。',[('冯道','提出归俟教令并归行者')],when='934年三月己巳',note='归行后仍在天宫寺被留，不当已经一路回家完成退官。')
ev('an_congjin_calls_ministers_to_welcome','安从进使人劝冯道等率百官到谷水迎潞王',15,'至天宫寺，','召百官。',[('安从进','遣人催迎者'),('冯道','留天宫寺召官者')],when='934年三月己巳',place='天宫寺、谷水（拟迎地点）',note='且至是使者报告，不当李从珂此刻已到；使者未名不编。')
ev('feng_requests_lu_dao_accession_petition','冯道要求中书舍人卢导草劝进文书',15,'中书舍人卢导至，','宜速具草。”',[('冯道','请草劝进者'),('卢导','中书舍人、受请者')],when='934年三月己巳',place='天宫寺',note='要求草稿不是卢已经写好、百官已上表或从珂已接受。')
ev('lu_dao_opposes_premature_accession','卢导反对天子在外即劝他人即位，主张先取太后令',15,'导曰：“潞王入朝，','则去就善矣。”',[('卢导','坚持先问太后者'),('冯道','争论对象'),('太后','建议取令的曹太后')],when='934年三月己巳',note='若潞王北面责问为卢假设，不当潞王已经拒迎群臣；废立与太后令为程序建议，不建立新母子血亲。')
ev('an_congjin_urges_on_claimed_arrival','安从进屡遣人称潞王已到、太后太妃已迎，催百官',15,'道未及对，','道等即纷然而去。',[('安从进','屡遣人催迎者'),('冯道','被催往者')],when='934年三月己巳',note='称潞王至与下句实际未至冲突，保报告层；太后太妃已遣为使者说法，不直接当曹王二人出宫亲迎。')
ev('lu_dao_repeats_advice_shangyang','潞王未到，三相停上阳门外，卢导再申先请太后令',15,'既而潞王未至，','导对如初。',[('冯道','再次问卢者'),('卢导','再次坚持意见者')],when='934年三月己巳',place='上阳门外',note='实际未到与先前催者声称已至分；三相名既有冯刘李但本句未逐名，不替他们造三个重复独立行程。')
ev('li_yu_accepts_lu_advice','李愚承认卢导言是，感叹自己的罪过',15,'李愚曰：',None,[('李愚','认同卢导者'),('卢导','其意见被认同者')],when='934年三月己巳',place='上阳门外',note='擢发不足数为自责语，不作司法已判罪或确数。')
ev('kang_presents_himself_for_punishment','康义诚到陕待罪，受李从珂责备后叩头请死',16,'康义诚至陕','叩头请死。',[('义诚','待罪、请死者'),('潞王','责问立嗣执政责任者')],place='陕',note='等罪底字保，展示用待罪；责问为从珂指控，不能当正式判决已下。')
ev('congke_temporarily_spares_kang','李从珂暂宥康义诚，未立即处死',16,'王素恶','且宥之。',[('潞王','暂宥者'),('义诚','被暂宥者')],place='陕',note='未欲遽诛且宥是暂缓，不当终身赦免；后来四月死尚待主线。')
q=span(16,'马步都虞侯','东军尽降。')
for code,name,role in [('chang','苌从简','马步都虞侯、被部下执降者'),('wang','王景戡','左龙武统军、被部下执降者')]:
 event('officer_seized_surrender_'+code,name+'被部下拘执，降于李从珂',16,q,[(name,role),('潞王','受降者')],note='部下未名不补；东军尽降为本段总括，不覆盖既有西面交战事实。')
ev('congke_petitions_dowager_and_moves_east','李从珂上笺太后请示，随后自陕东行',16,'潞王上笺',None,[('潞王','上笺请示并东行者'),('太后','收请示的曹太后')],place='陕东出',note='上笺取进止与下一段太后使迎安排分，未当已受即位令。')
ev('conghou_meets_shi_weizhou','四月庚午朔未明，李从厚在卫州东遇石敬瑭，问社稷计',17,'夏，四月，','问以社稷大计，',[('闵帝','出奔后遇石问计者'),('石敬瑭','被问计的节度使')],when='934年四月庚午朔未明；旧纪作三月二十九日夜',place='卫州东数里',note='主朔前未明与旧前月二十九日夜时界分歧并列，不换公历，不调平随骑人数。')
ev('shi_asks_kang_campaign_status','石敬瑭询康军与帝来由，闵帝称康也叛去',17,'敬瑭曰：','长叹数四，',[('石敬瑭','询问及叹息者'),('帝','答康已叛者')],when='934年四月庚午朔条下',place='卫州附近',note='回答系闵帝叙述，康请降在前已另录，不重复一场新叛军。')
ev('shi_consults_wang_hongzhi','石敬瑭往问卫州刺史王弘贽如何应对闵帝困局',17,'曰：“卫州刺史','乃往见弘贽问之，',[('石敬瑭','往咨询者'),('王弘贽','卫州刺史、被咨询宿将')],when='934年四月庚午朔条下',place='卫州',note='王宏贄旧异字沿已有王弘贽；不凭宿将称谓编生年。')
ev('wang_hongzhi_assesses_no_recovery','王弘贽以将相侍卫府库法物皆无，认为难以兴复',17,'弘贽曰：','将若之何？”',[('王弘贽','判断难兴复者')],when='934年四月庚午朔条下',note='无四者及五十骑为王判断和主记，不逐项当已经盘点整国全部府库，兴复困难是意见。')
ev('shi_reports_wang_assessment_at_station','石敬瑭到卫州驿，将王弘贽之言告闵帝',17,'敬瑭还，','以弘贽之言告。',[('石敬瑭','告王言者'),('帝','在驿受告者')],when='934年四月庚午朔条下',place='卫州驿')
ev('sha_ben_accuse_shi','沙守荣、奔洪进责石敬瑭未共患难，指其欲附贼卖天子',17,'弓箭库使','附贼卖天子耳！”',[('沙守荣','责石的弓箭库使'),('奔洪进','共同责石者'),('石敬瑭','被责者')],when='934年四月庚午朔条下',place='卫州驿',note='欲附贼卖帝是两人指控，不替他们证实石已与从珂缔约。奔洪进旧同字、新奔弘进异名保，不改无证贲姓。')
ev('sha_chen_fight_and_die','沙守荣拔刀欲刺石敬瑭，陈晖救石，两人斗死',17,'守荣抽佩刀','守荣与晖斗死，',[('沙守荣','欲刺石、与陈斗死者'),('陈晖','石敬瑭亲将、救石斗死者'),('石敬瑭','遇刺而被救者')],when='934年四月庚午朔条下；旧纪在三月二十九日夜段',place='卫州驿',note='陈晖为石亲将，与909梁军马步都指挥使陈晖同名未证同人，先职务消歧不强并；欲刺不当石已被刺死。')
ev('ben_hongjin_suicide','奔洪进在卫州驿自刎',17,'洪进亦自刎。','洪进亦自刎。',[('奔洪进','自刎者')],when='934年四月庚午朔条下；旧纪承三月二十九日夜',place='卫州驿')
ev('liu_zhiyuan_kills_conghou_retinue','刘知远引兵入卫州驿，尽杀闵帝左右从骑，只留闵帝',17,'敬瑭牙内指挥使','独置帝而去。',[('刘知远','石牙内指挥使、引兵杀随从者'),('帝','被单独留下的君主')],when='934年四月庚午朔条下；旧纪承三月二十九日夜',place='卫州驿',note='主明执行者刘知远，旧新归敬瑭尽杀为责任统叙异层保；左右未名不编，独置不当此时闵帝也已被杀。')
ev('shi_heads_luoyang_after_station','卫州驿事后，石敬瑭奔赴洛阳',17,'敬瑭遂','趣洛阳。',[('石敬瑭','离卫州奔洛阳者')],when='934年四月庚午朔条下',place='洛阳（趋赴目标）',note='趣为赴往，抵达具体日未载。')
ev('dowager_sends_offices_to_ganhao','四月庚午朔太后令内诸司去干壕迎潞王，潞王遣还洛阳',17,'是日，太后',None,[('太后','令内司迎的曹太后'),('潞王','遣迎者还洛阳者')],when='934年四月庚午朔',place='干壕、洛阳',note='是日承朔；内诸司未名不猜，曹太后本人未亲往干壕。')
relationship('石敬瑭','明宗','女婿',17,'公明宗爱婿','石敬瑭→李嗣源为女婿；已存在同方向边则复用UUID，不凭此处公爱子新增其他母子血亲。')
ev('wang_shufei_sends_meng_comfort_retrospective','追叙李从珂罢河中归私第时，王淑妃屡遣孟汉琼慰抚',18,'初，潞王罢河中，','存抚之。',[('潞王','罢河中归私第受慰抚者'),('王淑妃','屡遣使者'),('孟汉琼','被遣慰抚者')],year=None,when='初字追叙；罢河中归私第时往事，确年月此句未独载',note='屡遣无每次日不编；既有从珂罢镇背景不重造一次新934罢镇。')
ev('meng_meets_congke_mianchi','孟汉琼自谓有旧恩，在渑池西哭见李从珂',18,'汉琼自谓','诸事不言可知。”',[('孟汉琼','自恃旧恩、哭见者'),('潞王','被见并答语者')],when='934年四月条下；独日未载，旧纪置三月二十八日、新纪己巳',place='渑池西',note='旧恩为孟本人判断，不当从珂认可免罪承诺；见王哭不推宫中血亲。')
ev('congke_orders_meng_execution','孟汉琼自列从臣，李从珂命将其斩于路隅',18,'仍自预从臣之列，',None,[('孟汉琼','自列从臣后被斩者'),('潞王','命斩者')],when='934年四月条下；独日未载，旧纪三月二十八日、新纪己巳',place='渑池西路隅',note='自预不是已获正式任用；主无此日干支，保旧新不同时间位置，不以当前章节月头强定死亡日。')
old='jiuwudaishi-045-934-palace-flight';station='jiuwudaishi-045-934-weizhou';lu='jiuwudaishi-092-lu-dao';newstation='xinwudaishi-048-weizhou';kang='jiuwudaishi-066-kang-surrender';east='xinwudaishi-008-congke-eastmarch';hostages='jiuwudaishi-046-congke-hostages';new='xinwudaishi-007-934-newyear'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='同人同动作与时序核对；纸本及异文待核，原字不改。'):
 claim('event','event_zztj_279_0934_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
supp('campaign_new_command_kang',old,'癸亥，','餘如故。','旧闵帝纪同癸亥制康义诚凤翔行营都招讨使。',14)
supp('campaign_new_command_wang',old,'以王思同','副招討使；','旧闵帝纪同癸亥以王思同为副招讨使。',14)
supp('an_congjin_capital_patrol',old,'詔侍衛馬軍','潛布腹心矣。','旧闵帝纪乙亥条下令安从进京巡检并记已得潞王书，主在丙寅。',14,relation='conflicts',note='旧乙亥与主丙寅历日异文保，旧底字或月内编次须纸核，未径改。')
supp('congke_reaches_shan',old,'丁卯，','潞王至陝州。','旧闵帝纪同丁卯潞王到陕州。',14)
supp('kang_requests_surrender_ganhao',kang,'及義誠率軍至新安，','未欲行法。','旧康义诚传同记到新安军士争赴陕降，康以数十人向潞王请罪暂不行法。',14,relation='adds',note='只引请降暂宥，后四月处决在尚待主线段，不提前建死亡事件。')
supp('congke_reaches_lingbao',east,'丙寅，','來降。','新废帝纪丙寅到灵宝并记安彦威、康思立降；主康先谋守后迎，保新总括。',14,relation='adds')
supp('zhu_hongzhao_suicide',old,'戊辰，','宏昭懼，投於井。','旧闵帝纪同戊辰朱宏昭被急召、惧投井，宏弘沿同人。',15)
supp('an_congjin_kills_feng_clan',new,'丁卯，京城巡檢使','傳其二首于從珂。','新闵帝纪丁卯记安从进杀冯、朱自杀并传首，比主戊辰早一日。',15,relation='conflicts',note='两书日期并列；新此句未明确灭族，不据总括删去主明载灭族事实。')
supp('murong_closes_gate_does_not_follow',old,'是夜，帝以百騎','即闔門不行。','旧同戊辰夜帝百骑出元武门，慕容迁帝出后闭门不行；主五十骑、玄武名。',15,relation='conflicts',note='百与五十随骑数字、元玄门字差并列，不拿驿所五十余回调夜出百骑。')
supp('lu_dao_opposes_premature_accession',lu,'導與舍人張昭遠先至，','率爾而行！」','旧卢导传同记冯请劝进、卢坚持废立应听太后令，并补与张昭远先到。',15,relation='adds',note='旧发言皆太后之子为礼制论证，曹非两人生母，不能由此新增亲生母子边；新未将补名张昭远强套主某未名使者。')
supp('lu_dao_repeats_advice_shangyang',lu,'是日，潞王未至，','導之守正也如是。','旧卢导传同记潞王尚未到、上阳门外冯再请而卢坚持，李愚称言是。',15)
claim('person',people['卢导'],'description','卢导字熙化，其先范阳人。',15,'盧導，字熙化，其先范陽人也。','其先为祖籍措辞，不直接断当前出生地坐标；别名盧導仅繁体匹配。',source=lu,relation='adds')
supp('congke_temporarily_spares_kang',hostages,'二十八日，','帝宥之。','旧废帝纪二十八日康军兵相继来降，康诣军门请罪获宥；主到陕段未独日。',16,relation='adds')
supp('congke_temporarily_spares_kang',east,'己巳，','來降。','新废帝纪把到陕、康义诚降记于己巳，主到陕为丁卯、康到独日未载，旧康二十八日。',16,relation='conflicts',note='到陕及受降日期不同叙法并列，不压成统一一天。')
supp('conghou_meets_shi_weizhou',station,'是月二十九日夜，','石敬瑭也。','旧闵帝纪三月二十九日夜遇石，在卫州东七八里；主四月朔未明东数里。',17,relation='conflicts',note='月份时界和距离数字异说保，旧是月承三月，主入夏四月，不换公历。')
supp('wang_hongzhi_assesses_no_recovery',newstation,'高祖曰：「衞州刺史','其可得乎！」','新王弘贽传记石咨询、王以将相国宝法物无而谓难兴复，随骑百骑与主五十不同。',17,relation='conflicts',note='高祖为后追称石敬瑭，不当此时已晋帝；王判断保引述层。')
supp('sha_chen_fight_and_die',station,'乃抽佩刀','洪進亦自刎。','旧闵帝纪同记沙守荣与陈晖斗死、奔洪进自刎，旧陈暉字；日期承前二十九夜。',17,relation='conflicts')
supp('sha_chen_fight_and_die',newstation,'弓箭庫使沙守榮、奔弘進','弘進亦自刎。','新王弘贽传同记沙、陈斗死与奔弘进自刎，弘进与主洪进同案异名。',17,relation='adds',note='同驿变同责石、自刎情节对照为同人，保奔姓不擅改贲；陈新旧暉仅字体，仍未证与909梁将同人。')
claim('person',people['奔洪进'],'aliases','奔洪进在新王弘贽传作奔弘进。',17,'弓箭庫使沙守榮、奔弘進前謂高祖曰：','同石、沙、陈驿变与自刎的独立新传定位，作异名检索别名，不另造人物。',source=newstation,relation='adds')
supp('liu_zhiyuan_kills_conghou_retinue',station,'是日，敬瑭','乃馳騎趨洛。','旧闵帝纪以石敬瑭尽诛帝从骑五十余归责，主明确刘知远引兵执行，均独留帝。',17,relation='conflicts',note='责任统叙与具名执行者两层保，不当旧有独立明载刘下令或石亲手杀每人。')
supp('liu_zhiyuan_kills_conghou_retinue',newstation,'高祖因盡殺','獨留帝于驛而去。','新王弘贽传亦归石敬瑭尽杀从兵，主记刘知远引兵；帝被留未在本段遇害。',17,relation='conflicts')
supp('congke_orders_meng_execution',hostages,'二十八日，','誅宣徽南院使孟漢瓊於路左。','旧废帝纪承三月二十八日记孟汉琼被诛路左，主在四月条下、独日未载。',18,relation='conflicts',note='两书时间位置分歧并列；旧补宣徽南院使身份，不提前依主四月月头填庚午死日。')
supp('congke_orders_meng_execution',east,'己巳，','殺宣徽使孟漢瓊。','新废帝纪己巳记康降及杀孟汉琼，日期与旧二十八、主四月未独日不同。',18,relation='conflicts')
reviews={14:'癸亥康招讨王副为文书不是任命已执行；王前段已遇害不当复活。甲子药拘与后杀分，乙丑阌乡、丙寅康出兵安巡检及灵宝两节度降、康思立谋守被迫迎、丁卯陕、僚佐传闻帝迁、慰京除两族、新安散兵干壕请降分。捧圣戍陕西先是未独年；十万奉新帝为劝降话不当核数正式即位。旧乙亥安巡检和主丙寅历日疑保。',15:'戊辰朱以为被罪井死、安杀冯族传首、孟拒召奔陕分。初慕容爱信任职未定年；玄门密谋、五十骑出、口许实闭分，旧百骑元武数字字差，新朱冯丁卯比主早一日保。己巳端门获讯不是死亡日，冯刘欲归李问太后、冯归俟、天宫寺催、冯催草劝进卢反、安报已到实际未到、上阳再议李承是分；不当太后亲迎或已发正式即位令，卢说太后之子不推生母。',16:'康到陕请死暂宥与后来四月被杀分；新己巳康降、旧二十八请罪、主独日未载并列。苌王被下执降分别，东军总括未列全部人不猜；上笺太后与动身东行不当已即位。',17:'主四月庚午朔未明遇石，旧三月二十九夜时界保，王弘贽字沿已有、旧宏贄原字保。石问王还驿、沙奔责石、沙抽刀陈救两斗死、奔自刎、刘引兵杀随骑留帝、石趋洛、太后内司干壕迎王返分。四者无及欲附贼为意见指控；主刘执行与旧新石归责不同层并列。新奔弘进同案异名合，未擅改贲。陈晖石亲将与909梁将同名无同人证先消歧，死亡不加到909陈主体。',18:'初王淑妃数遣孟慰潞王罢河中为过往，确年此句未独载。孟自恃旧恩渑池西哭见自预从臣与王命斩分。主四月附记、旧三月二十八、新己巳杀不同位置并列，主不定庚午死日。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(14,19):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=934,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(14,19)],next_paragraph='zztj-v279-y0934-p019',next_volume=279,next_year=934,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷279连续934年第14—18正文段，原19—23行；康降、闵帝出奔、朝廷请令争议、卫州驿变与孟被斩。第19段两镇降蜀待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(14,19)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
