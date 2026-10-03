# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 933 paragraphs 43–49."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
# The final ledger item is the next imperial section heading, not a 933 event.
raw_lines=(ROOT/'resources/derived/tongjian/278.txt').read_text().splitlines()
assert raw_lines[91:94]==['潞王上','◎','清泰元年甲午，公元九三四年']
assert ledger[56]['text']=='潞王上' and ledger[56]['source_line']==92 and not ledger[56]['event_keys']
ledger[56].update(kind='section_heading',status='excluded_non_body_verified',review='潞王上为下一帝纪节标题，后接934年年题；保原ID及行号，不生成历史事实，不计933正文。')
boundaries=json.loads((YEAR/'boundaries.json').read_text())
boundaries.update(body_source_lines=[36,91],body_paragraphs=56,ledger_source_lines=[36,92],ledger_records=57)
if not any(x['source_line']==92 for x in boundaries['excluded_non_body']):boundaries['excluded_non_body'].insert(0,dict(paragraph_id=ledger[56]['id'],source_line=92,text='潞王上',reason=ledger[56]['review']))
(YEAR/'boundaries.json').write_text(json.dumps(boundaries,ensure_ascii=False,indent=2)+'\n')
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 58))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'8487026c','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [('tongjian-278-933-aftermath',YEAR/'part-05/sources/library/tongjian-278-933-aftermath','ba163460','司马光等'),('jiuwudaishi-044-933-coup-aftermath',YEAR/'part-05/sources/library/jiuwudaishi-044-933-coup-aftermath','ba163460','薛居正等'),('xinwudaishi-006-933-princes',YEAR/'part-02/sources/library/xinwudaishi-006-933-princes','0f922712','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-933-aftermath']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0933-p043-p049',
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
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(43, 50):
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
        citation = f'卷278·长兴四年（933）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0933_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','上':'李嗣源','闽王':'王延钧','文杰':'薛文杰','继图':'王继图','李赞化':'耶律倍','李赞华':'耶律倍','知诰':'李昪','徐知诰':'李昪','从荣':'李从荣','秦王':'李从荣','延光':'范延光','赟':'冯赟','汉琼':'孟汉琼','义诚':'康义诚','彝超':'李彝超'}
NEW_ALIASES={'苏瓒': ['蘇瓚'], '刘陟': ['劉陟'], '司徒诩': ['司徒詡'], '王说': ['王說'], '李瀚': [], '江文蔚': [], '郭晙': [], '赵远': ['趙遠', '赵上交', '趙上交'], '黄氏（闽太后）': ['黃氏（閩太后）'], '盛韬': ['盛韜'], '蒋延徽': ['蔣延徽'], '李荛': ['李蕘']}

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

def event(code, title, n, quote, actors, when=None, note='', year=933, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='933年十一月条下；确日未独载' if n<=48 else '933年十二月条下；确日未独载'
    key = 'event_zztj_278_0933_' + code
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
        edge = 'participation_zztj_278_0933_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_278_0933_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)


# Consecutive body paragraphs 43–49; numbered punishments preserve each book's list.
ev('congrong_posthumous_demoted','十一月丙申追废李从荣为庶人',43,'丙申，','追废从荣为庶人。',[('从荣','死后被追废者'),('帝','在位朝廷君主')],when='933年十一月丙申',note='先前已杀，追废是身份处分而非此日再杀。')
ev('feng_dao_opposes_collective_execution','冯道在官属议罪时反对一概诛杀，区别亲昵者及请病、刚到官者',43,'执政共议','岂得一切诛之乎！”',[('冯道','反对不分参与而一切诛者'),('高辇','冯称秦王所亲者'),('刘陟','冯称秦王所亲者'),('王说','冯称秦王所亲者'),('任赞','冯称到官半月者'),('王居敏','病告半年且为秦王所恶者'),('司徒诩','病告半年者')],note='议罪中的陈述保为冯所言；亲昵不自动推出所有人参加具体谋反，不据半月换任命确日。')
ev('zhu_advocates_punishing_entourage','朱弘昭在议罪中主张连罪官属，忧被视为庇奸',43,'硃弘昭曰：','为庇奸人乎！”',[('朱弘昭','主张处分官属者')],note='反事实使秦入门的任使设想不当已入门或已任使。')
ev('feng_yun_secures_exile_discussion','冯赟力争后，执政改议流贬',43,'冯赟力争之，','始议流贬。',[('冯赟','力争者')],note='议改流贬与丁酉具体诏令分，不造此时全部已到流所。')
ev('gaonian_already_executed','本段记咨议高辇已被处死',43,'时咨议高辇','时咨议高辇已伏诛。',[('高辇','已处死的秦王咨议')],when='933年十一月丁酉议处分前已伏诛；确日未知',note='已伏诛不是丁酉新处死，不编行刑人。')
q=span(43,'丁酉，','等八人并长流，')
for code,name,role in [('renzan','任赞','元帅府判官、兵部侍郎'),('liuzan','刘赞（秦王傅）','秘书监兼王傅'),('sucan','苏瓒','秦王友'),('yuchongyuan','鱼崇远','记室'),('liuzhi','刘陟','河南少尹'),('situxu','司徒诩','判官'),('wangshuo','王说','推官')]:
 event('qin_exile_'+code,'十一月丁酉'+name+'被长流',43,q,[(name,role+'、被长流者')],when='933年十一月丁酉',note='主八人仅列七名，原数保留，不猜第八；刘瓚与旧刘讚同秦王傅沿既有人物，不混923嘉州刘赞。')
q=span(43,'河南巡官李瀚','等六人勒归田里，')
for code,name in [('lihan','李瀚'),('jiangwenwei','江文蔚')]:event('qin_return_home_'+code,'十一月丁酉'+name+'被勒归田里',43,q,[(name,'河南巡官、被勒归者')],when='933年十一月丁酉',note='主六人只具两名，其余不凭空补；主李瀚、旧此名单李潮异名保，不仅字近合并。')
q=span(43,'六军判官、','并贬官。')
for code,name,role in [('wangjumin','王居敏','六军判官、太子詹事'),('guojun','郭晙','推官')]:event('qin_demote_'+code,'十一月丁酉'+name+'被贬官',43,q,[(name,role+'、被贬者')],when='933年十一月丁酉',note='主未具流地与贬后官，旧明宗纪另补；不同原衔保差。')
person('司徒诩',43,'贝州人',span(43,'诩，','诩，贝州人；'))
claim('person',people['司徒诩'],'description','司徒诩为贝州人。',43,'诩，贝州人；','原籍仅史名，不附现代县或坐标。')
claim('person',people['江文蔚'],'description','江文蔚为建安人。',43,'文蔚，建安人也。','沿同巡官及奔吴者，原籍不强换现代区划。')
claim('person',people['李瀚'],'description','本段记李瀚为回之族曾孙。',43,'瀚，回之族曾孙也；','族曾孙不同直系曾孙；回的身份需另核，不据省名新建祖先边，也不将李瀚自动合李澣或旧名单李潮。')
ev('jiang_flees_wu','江文蔚奔吴',43,'文蔚奔吴，','文蔚奔吴，',[('江文蔚','奔吴者')],when='933年十一月官属处分后附记；确日未独载',place='吴')
ev('xu_welcomes_jiang','徐知诰厚礼江文蔚',43,'文蔚奔吴，','徐知诰厚礼之。',[('江文蔚','受礼者'),('徐知诰','厚礼者')],when='933年官属处分后附记；确日未独载',place='吴',note='厚礼不等已授某官；徐知诰沿李昪。')
ev('zhao_remonstrates_qin','赵远以恭世子、戾太子为戒，劝李从荣修德',44,'初，','独不见恭世子、戾太子乎！”',[('赵远','六军判官、司谏郎中、谏者'),('从荣','受谏秦王')],year=None,when='初所追述的秦王败前进谏；具体年月未知',note='历史例子只是谏言，不额外新增两位古代太子事件；赵远与宋赵上交同人有传首明确证据。')
ev('congrong_relegates_zhao','李从荣因谏怒，出赵远为泾州判官',44,'从荣怒，','出为泾州判官；',[('从荣','因谏怒而出官者'),('赵远','出为泾州判官者')],year=None,when='秦王败前、进谏之后的追叙；具体年月未知',place='泾州',note='出官非兵变后新授，也不当逐出至流刑。')
ev('zhao_gains_reputation','李从荣败后，赵远因先前进谏而知名',44,'及从荣败，','远以是知名。',[('赵远','因先前谏言而知名者')],when='933年十一月秦王败后附记；确日未知')
claim('person',people['赵远'],'description','赵远字上交，主书记幽州人。',44,'远，字上交，幽州人也。','宋史涿州范阳为另一原籍层，并列保留；避后汉刘知远讳改字称不当933已经改名事件。')
ev('mingzong_dies','十一月戊戌后唐明宗李嗣源去世',45,'戊戌，','戊戌，帝殂。',[('帝','去世君主')],when='933年十一月戊戌',place='后唐宫廷',note='后唐尚未灭亡，933帝死不等936亡国。')
ev('mingzong_prays_for_sage','史叙明宗每夕焚香祝天早生圣人为生民主',45,'每夕于宫中','为生民主。”',[('帝','每夕祝天者')],year=None,when='明宗在位期间每夕祝天的持续概述；起讫未独载',place='宫中',note='祷词是帝自述胡人、众推身份，愿望不当已有圣人降生。')
ev('mingzong_reign_assessment','通鉴评明宗不猜忌，年谷屡丰、兵革罕用，五代中粗为小康',45,'帝性不猜忌，',None,[('帝','史书评价的君主')],year=None,when='明宗在位时期总评；不是戊戌单日发生',note='粗为小康为史家相较五代的评价；兵革罕用不等全朝没有战争，不作现代统计。')
ev('conghou_arrives_luoyang','十一月辛丑宋王李从厚至洛阳',46,'辛丑，',None,[('李从厚','被征召后到洛阳者')],when='933年十一月辛丑',place='洛阳',note='到京与甲午召、十二月即位各别，不混为同日。')
ev('min_huang_empress_dowager','闽主尊鲁国太夫人黄氏为皇太后',47,'闽主尊','为皇太后。',[('王延钧','尊太后者'),('黄氏（闽太后）','原鲁国太夫人、获尊皇太后者')],place='闽',note='本句太后未明确生母或王审知婚姻，当前不猜本名及生母关系。')
ev('xue_proposes_spirit_inquiry','薛文杰劝闽主用盛韬视鬼察奸，闽主听从',47,'闽主好鬼神，','闽主从之。',[('王延钧','宠巫并听从建议者'),('盛韬','受宠且被称善视鬼的巫者'),('文杰','提出察奸方案者')],place='闽',note='鬼神能力为其说法，不能录作真实侦查能力；从之为获准。')
ev('xue_coaches_wu_headache','薛文杰探望病中吴勖，诱其被问时只称头痛，吴勖许诺',47,'文杰恶枢密使','勖许诺。',[('文杰','对吴勖设言诱导者'),('吴勖','病中的枢密使、应诺者')],place='闽',note='欲罢近密是薛对吴所说，不当主已正式罢官；只知病不作现代病名。')
ev('sheng_fabricates_ghost_accusation','次日盛韬奉薛文杰意，称见鬼神审吴勖谋反并钉击其脑',47,'明日，','金椎击之。”',[('文杰','指使盛韬言说者'),('盛韬','向闽主陈说见鬼讯问者'),('王延钧','听受者'),('吴勖','被指称谋反者')],when='933年本段探病次日；未载独立干支',place='闽',note='适见北庙崇顺王是巫者报告，不当真实审判事件，不新造神祇人物实体。')
ev('min_tests_wu_headache','闽主告薛文杰鬼说，薛建议问疾，使者得头痛答复',47,'闽主以告文杰，','果以头痛对，',[('王延钧','听议并遣问者'),('文杰','提议问疾者'),('吴勖','答头痛者')],place='闽',note='答病与谋反毫无证据等价，史叙陷害不可作吴实际谋反。')
ev('wu_xu_imprisoned','闽主收吴勖下狱，遣薛文杰及狱吏杂治',47,'即收下狱，','杂治之，',[('王延钧','下狱及遣治的闽主'),('文杰','与狱吏审治者'),('吴勖','被审治者')],place='闽')
ev('wu_xu_false_confession_execution','吴勖自诬服，连妻子被诛',47,'勖自诬服，','并其妻子诛之。',[('吴勖','自诬服并遇害者')],place='闽',note='自诬服不是确证吴确实谋反；妻子指妻与子女、无名不造名字名单。')
ev('min_public_anger_increases','吴勖案后史称国人益怒',47,'由是国人益怒。',None,[('吴勖','引发民怨的案中遇害者')],place='闽',note='国人益怒是主书群体评述，未给组织者或人数不造示威事件。')
ev('wu_guang_requests_troops','吴光向吴国请兵',48,'吴光请兵于吴，','吴光请兵于吴，',[('吴光','向吴请兵者')],place='吴、建州',note='吴光人物与吴国国名分清，不当向自己请兵。')
ev('jiang_attacks_jianzhou','吴信州刺史蒋延徽未待朝命，率兵会吴光攻建州',48,'吴信州刺史','引兵会光攻建州，',[('蒋延徽','信州刺史、擅率兵攻建州者'),('吴光','与延徽会兵者')],place='建州',note='主将延徽与同卷后文蒋延徽同一吴攻建州军识同人，原将字不改；无朝命不当吴君已批准，不提前记934围破结果。')
ev('min_seeks_wuyue_aid','闽主遣使向吴越求救',48,'闽主遣使','求救于吴越。',[('王延钧','遣使求救者')],place='闽、吴越',note='求救不当吴越已出兵或已经救胜。')
ev('mingzong_mourning_announced','十二月癸卯朔始发明宗丧',49,'十二月，','始发明宗丧，',[('帝','被宣布丧事的明宗')],when='933年十二月癸卯朔',place='后唐朝廷',note='明宗实际死在十一月戊戌，此日发丧不是死亡日。')
ev('conghou_accession','十二月癸卯朔宋王李从厚即皇帝位',49,'十二月，','宋王即皇帝位。',[('李从厚','即位的宋王')],when='933年十二月癸卯朔',place='后唐朝廷',note='即位与次年改应顺元年分，不把933十二月记为已改元。')
old='jiuwudaishi-044-933-coup-aftermath';succ='jiuwudaishi-045-conghou-succession';new='xinwudaishi-007-conghou-succession';zhao='songshi-262-zhao-yuan-identity';zhadv='songshi-262-zhao-remonstrance';jiang='tongjian-278-934-jiang-name';new6='xinwudaishi-006-933-princes'
def excerpt(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);return t[a:t.index(end,a)+len(end)]
def supp(code,source,start,end,text,n,relation='corroborates',note='对应主段独立书证补充，保各书原字与定位；不据后文提前标主线完成。'):
 claim('event','event_zztj_278_0933_'+code,'description',text,n,excerpt(source,start,end),note,source=source,relation=relation)
for code,name,start,end,loc in [('renzan','任赞','元帥府判官、兵部侍郎任讚','配武州','武州'),('liuzan','刘赞（秦王傅）','秘書監兼秦王傅劉讚','配嵐州','岚州'),('liuzhi','刘陟','河南少尹劉陟','配均州','均州'),('situxu','司徒诩','河南府判官司徒詡','配寧州','宁州'),('sucan','苏瓒','秦王友蘇瓚','配萊州','莱州'),('yuchongyuan','鱼崇远','記室參軍魚崇遠','配慶州','庆州'),('wangshuo','王说','河南府推官王說','配隨州','随州')]:
 supp('qin_exile_'+code,old,start,end,'旧明宗纪同丁酉记'+name+'配'+loc+'。',43,relation='adds',note='主长流、旧具体流地对应；原名繁简同人。流地为处分目标，不写已到流所，不猜现代坐标。')
event('qin_exile_lirao_old','旧明宗纪丁酉另记李荛配石州',43,excerpt(old,'河南少尹李蕘','配石州'),[('李荛','河南少尹、被长流者')],when='933年十一月丁酉',place='石州',source=old,note='旧名单第八人，主省七名而称八人；独立补证，不回填主原文，不因同职将李荛与刘陟合。')
supp('qin_return_home_lihan',old,'河南府推官尹諲','並勒歸田里。','旧明宗纪勒归名单为尹諲、董裔、张九思、张沆、李潮、江文蔚，主此处李瀚与旧李潮待考，不能悄改。',43,relation='conflicts')
supp('qin_demote_wangjumin',old,'六軍判官、殿中監王居敏','並員外置','旧明宗纪记王居敏原殿中监、责授复州司马，郭晙责授坊州司户；主王原太子詹事，职衔异说保。',43,relation='adds')
supp('mingzong_dies',old,'戊戌，帝崩','壽六十七。','旧明宗纪戊戌记帝崩于雍和殿，寿六十七。',45,relation='adds')
supp('mingzong_dies',new6,'戊戌，','皇帝崩于雍和殿。','新明宗纪同戊戌记皇帝崩。',45)
supp('conghou_arrives_luoyang',succ,'二十九日，','帝至自鄴。','旧闵帝纪记十一月二十九日帝至自邺，与主辛丑到洛阳相衔；不另换公历。',46,relation='adds')
supp('conghou_accession',succ,'十二月癸卯朔，','帝於柩前即位。','旧闵帝纪记癸卯朔西宫发丧、柩前即位。',49,relation='adds')
supp('conghou_accession',new,'十二月癸卯朔，','皇帝即位于柩前','新闵帝纪同记癸卯朔西宫发丧与柩前即位。',49,relation='adds')
claim('person',people['赵远'],'aliases','赵远后来避后汉君讳，以字上交称，宋史立传赵上交。',44,'本名遠，字上交，避漢祖諱，遂以字稱。','同人身份有明确传首，当前主体沿933本名赵远，加繁简与字称检索，后来的避讳不造933改名事件。',source=zhao,relation='adds')
claim('person',people['赵远'],'description','宋史赵上交传记赵远为涿州范阳人，主书作幽州人。',44,'趙上交，涿州范陽人。','不同层次地名保并列，不据此造两人或自行现代换点；原卷题李濤傳不当赵传标题。',source=zhao,relation='adds')
supp('zhao_remonstrates_qin',zhadv,'上交從容言曰：','上交由是知名。','宋史赵上交传也记进谏秦王、因怒出为判官、秦王败后知名；记历泾、秦二镇，比主仅泾州更广。',44,relation='adds')
claim('person',people['蒋延徽'],'aliases','同卷下一年攻建州军将写作蒋延徽，本段将延徽同人异字。',48,'吴蒋延徽败闽兵于浦城，遂围建州，','同吴军攻建州连续背景核姓名，规范蒋延徽，摘录保原字；这里只核身份，不提前新增或标完934战事。',source=jiang,relation='adds')
for name,quote in [('李嗣源','戊戌，帝殂。'),('高辇','时咨议高辇已伏诛。'),('吴勖','勖自诬服，并其妻子诛之。')]:
 next(x for x in B['people'] if x['key']==people[name])['death_year']=933
 claim('person',people[name],'death_year',name+'死亡于933年。',45 if name=='李嗣源' else 43 if name=='高辇' else 47,quote,'死亡年据当前编年；具体日仅明宗戊戌明载，其余不硬定。')
reviews={43:'丙申追废、议罪观点、已有高辇死、丁酉各项处分、奔吴受礼分。主八流七列、旧补李蕘石州，保书层而不改主；主六归仅两列，旧具名单但李瀚/李潮异名不盲合。刘瓚沿秦王傅刘赞，不混923刘赞；王原衔主詹事旧殿中监保。李瀚回族曾孙不定直系祖先边。',44:'初进谏出泾州为追叙年未知，败后知名当年；宋卷262赵上交传首明本名远、避汉祖讳以字称，识同人但不记933改名。宋幽州/涿州范阳地名层并存，原EPUB卷题李濤傳误传主说明，引用正文赵传。',45:'戊戌殂与旧雍和殿寿67、新帝纪同日；每夕祷词及在位评价独列持续年未定。小康史家评语不当现代统计，罕用不等无战，933帝死非936国亡。',46:'辛丑到洛阳，旧十一月二十九日自邺对应，不混甲午召或十二月即位。',47:'尊黄太后、巫策、诱吴答头痛、造鬼讯说、遣问、下狱审治、自诬服连妻子诛及民怨分。鬼讯是巫报告，不录神真实审案；自诬非谋反确证，黄未直接生母婚姻不猜关系姓名；当月附记无日不硬干支。',48:'吴光请吴、信州延徽未待命攻建、闽求吴越分；主将延徽同下年同军蒋延徽识异字，仅借后文核姓名不提前录934结果。求救不当已获援或胜。',49:'十二月癸卯朔发明宗丧与宋王即位分，旧新西宫柩前补；实际帝死戊戌，今发丧非死日，不把次年应顺改元提前。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(43,50):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=933,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(43,50)],next_paragraph='zztj-v278-y0933-p050',next_volume=278,next_year=933,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷278连续933年第43—49正文段、原78—84行；追废官属处分、赵谏背景、明宗崩、宋王到京、闽吴勖案、吴攻建与闽求援、宋王即位。第50段后续宫人案尚待录。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(43,50)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
