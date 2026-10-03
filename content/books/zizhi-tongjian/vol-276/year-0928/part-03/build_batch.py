# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 11–12."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 53))
specs=[
 ('tongjian-276-salt-wars',YEAR/'part-02/sources/library/tongjian-276-salt-wars','f890926e','司马光等'),
 ('jiuwudaishi-039-april',P/'sources/library/jiuwudaishi-039-april','b559f13a','薛居正等'),
 ('xinwudaishi-065-fengzhou',P/'sources/library/xinwudaishi-065-fengzhou','b559f13a','欧阳修'),
 ('xinwudaishi-066-chu-jingnan',P/'sources/library/xinwudaishi-066-chu-jingnan','b559f13a','欧阳修'),
 ('jiuwudaishi-038-december-records',YEAR.parent/'year-0927/part-05/sources/library/jiuwudaishi-038-december-records','cf38d77b','薛居正等'),
 ('xinwudaishi-006-928',YEAR/'part-01/sources/library/xinwudaishi-006-928','c991ab36','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-salt-wars']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p011-p012',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/276.txt').read_text().splitlines()
for n in range(11, 13):
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
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷276·天成三年（928）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0928_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','殷':'马殷','楚王殷':'马殷','季兴':'高季昌','高季兴':'高季昌','汉主':'刘岩','希瞻':'马希瞻','环':'王环','章':'苏章','从荣':'李从荣','从厚':'李从厚','德勋':'许德勋','彦章':'王彦章（吴将）','王彦章':'王彦章（吴将）','璘':'苗璘'}
NEW_ALIASES={'袁诠':['袁詮'],'马希瞻':['馬希瞻'],'苏章':['蘇章'],'苗璘':[],'王彦章（吴将）':['王彥章（吳將）'],'詹信':[],'冯赟':['馮贇'],'杨思权':['楊思權']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成三年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='928年本段，列于四月条之前；月日未明', note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_276_0928_' + code
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
        edge = 'participation_zztj_276_0928_' + code + '_' + pk
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
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_276_0928_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
old='jiuwudaishi-039-april';han='xinwudaishi-065-fengzhou';chu='xinwudaishi-066-chu-jingnan';dec='jiuwudaishi-038-december-records';new='xinwudaishi-006-928'
E=ev('mayin_visits_yuezhou','楚王马殷到岳州',11,'楚王殷','如岳州，',[('殷','到岳州的楚王')],place='岳州',note='如为前往，未具干支；不推全军均从长沙同日出发。')
E=ev('mayin_sends_fleet_jingnan','马殷遣袁诠、王环、马希瞻领水军攻荆南',11,'遣六军使','将水军击荆南，',[('袁诠','六军使、领楚水军者'),('环','副使、领楚水军者'),('希瞻','监军、领楚水军者')],place='楚至荆南',note='楚将王环复用914楚军主体，区别后蜀同名；本句未载楚水军人数。')
claim('event',E,'description','新楚世家同记马殷遣袁诠、王环等攻高季昌，进至城下。',11,'殷遣袁詮、王環等攻之，至其城下，','回查前句史光宪被执为背景，前句明年正月是使贡被执时间，不能据此强将新攻军定927正月；主本行动列928。',source=chu,relation='corroborates')
E=ev('gaojichang_meets_chu_fleet','高季昌以水军迎战楚军',11,'高季兴','以水军逆战。',[('季兴','荆南水军迎战者')],place='荆南水域',note='季兴沿已合并高季昌key；不重建异名人或编兵数。')
E=ev('maxizhan_hides_ships_liulangfu','到刘郎洑后，马希瞻夜间把数十艘战舰藏于港中',11,'至刘郎洑','于港中；',[('希瞻','夜藏战舰者')],place='刘郎洑及港中',note='数十为原概数，不给准确船数、舰型及现代定位。')
E=ev('liulangfu_morning_flank_attack','次晨两军交战，马希瞻出伏舰横击荆南军',11,'诘旦','横击之，',[('希瞻','出伏舰横击者')],when='928年本段藏舰夜后的诘旦，具体月日未明',place='刘郎洑',note='诘旦是次晨，不能换算具体日；突袭与此前夜藏分阶段。')
E=ev('jingnan_defeat_chu_advances_jiangling','荆南军大败，楚军俘斩以千计，进逼江陵',11,'季兴大败','进逼江陵。',[('季兴','所部大败者')],place='刘郎洑至江陵',note='俘斩合计概数不是全为阵亡；进逼未攻克江陵，未扩为楚吞并荆南。')
E=ev('gaojichang_seeks_peace_returns_shiguangxian','高季昌请和，把史光宪送还楚',11,'季兴请和','归史光宪于楚。',[('季兴','求和及还使者'),('史光宪','被送还楚的使者')],place='荆南至楚',note='与927史光宪被执是同人不同阶段；和未列条约全文，不推楚已得荆南领土。')
claim('event',E,'description','新楚世家记高季昌求和，楚军停止进攻。',11,'季昌求和，乃止。','补主请和后的止攻叙法；新该句未写史光宪归还，归还仍据主，未伪称新直接明证。',source=chu,relation='corroborates')
E=ev('chu_returns_mayin_reproaches_wanghuan','楚军返回，马殷责王环未取荆南',11,'军还','不遂取荆南，',[('殷','责问者'),('环','被责副使')],place='楚',note='未取明示不曾占领荆南；责问与和约不是同日。')
E=ev('wanghuan_explains_jingnan_buffer','王环称江陵四面受敌，宜留作楚的屏蔽，马殷认可',11,'环曰','殷说。',[('环','保留荆南主张者'),('殷','听后认可者')],place='楚，议及江陵',note='四战与扞蔽为王环战略评价；说是喜悦，不据此建永久共同防御条约。')
E=ev('wanghuan_leads_and_treats_wounded','史书概述王环每战身先士卒、同甘苦，并用针药照料伤者',11,'环每战','自傅治之。',[('环','被记率先及照料伤者者')],year=None,when='王环历次作战的泛述，确年未载',place='战后帐前，未具固定地',note='每战和常是行事概述，不把全部行为强定928当次；自傅治疗不等现代医药技术或疗效已证。')
claim('event',E,'description','主书记王环部下相贺得死所，并据此评价其所向有功。',11,'士卒隶环麾下者相贺曰：“吾属得死所矣。”故所向有功。','部下话语及史家评价，不作为每场战争百分之百获胜的统计。')
E=ev('chu_besieges_han_fengzhou','楚以大队水军攻南汉，围封州',11,'楚大举','围封州。',[],place='封州',note='围城不等已攻克；本句楚将未名，不把前战荆南三将直接推为封州指挥者。')
claim('event',E,'description','新南汉世家记楚舟师攻封州，封州兵先败于贺江。',11,'四年，楚人以舟師攻封州，封州兵敗於賀江，','新补南汉先败的阶段，不与后苏章救援胜利混淆；四年承前白龙，上下文单独保留，不自行换算公历日。',source=han)
E=ev('liuyan_divines_dayou','南汉主刘岩以周易占筮，遇大有卦',11,'汉主以','遇《大有》，',[('汉主','占筮者')],place='南汉，地点未载',note='记所用占筮和所得卦名，不作为神示真实预言战争结局。')
E=ev('liuyan_han_amnesty_dayou','南汉主宣布大赦',11,'于是','于是大赦，',[('汉主','大赦所归者')],place='南汉',note='只记赦令，未列适用罪名或证所有囚犯均已释。')
E=ev('liuyan_changes_era_dayou','南汉改元大有',11,'改元大有','改元大有；',[('汉主','改元所归者')],place='南汉',note='主年928；新四年年序回查前白龙原文，保留此纪年结构，非大有四年。')
claim('event',E,'description','新南汉世家同述占筮大有、赦境内及改元大有。',11,'龑懼，以周易筮之，遇大有，遂赦境內，改元曰大有。','龑是刘岩后名，沿同人key不造帝；惧为新叙动机，周易卦名不当现代预测能力证据。',source=han,relation='corroborates')
E=ev('suzhang_sent_fengzhou_relief','南汉命左右街使苏章领神弩三千、战舰百艘救封州',11,'命左右街使','救封州。',[('章','左右街使、救援统领')],place='南汉至封州',note='主神弩三千保留原称，新神弩军三千补军名，未武断认三千独立弩具等于三千士兵；舰百艘按主。')
claim('event',E,'description','新南汉世家称苏章率神弩军三千救封州。',11,'遣將蘇章以神弩軍三千救封州，','主神弩与新神弩军称法并列，不补主未明的兵器种类、型号与射程。',source=han)
E=ev('suzhang_hejiang_hidden_chain_trap','苏章到贺江，沉铁絙、设巨轮长堤并伏壮士',11,'章至贺江','伏壮士于堤中。',[('章','布置铁絙机关、长堤及伏兵者')],place='贺江',note='铁絙为原文器具称谓，地点不自动地理配准；长堤用于掩藏，不编工程尺寸。')
claim('event',E,'description','新南汉世家把沉水机关具体记为两根铁索，岸上巨轮及堤。',11,'章以兩鐵索沈賀江中，為巨輪於岸上，築隄以隱之，','新两索为补记，主未明数量，保留不同词形，不视作两种已互证的独立器械。',source=han)
E=ev('suzhang_feigns_loss_chu_pursues','苏章以轻舟迎战假装不利，楚军追进堤中',11,'章以轻舟','入堤中；',[('章','轻舟迎战、佯败诱追者')],place='贺江',note='阳是佯装，不把假败录成实际败仗；楚追军将名未载。')
E=ev('suzhang_locks_ships_shoots_from_banks','苏章部挽轮举絙，使楚舰不能进退，并以强弩夹水射击',11,'挽轮','夹水射之，',[('章','机关拦舰与夹射所部统领')],place='贺江两岸',note='动作承苏章布置，不编射速距离或实际复现效果。')
E=ev('han_defeats_chu_lifts_fengzhou_siege','楚军大败，解除封州之围并退去',11,'楚兵大败','解围遁去。',[],place='封州、贺江',note='大败退去为主结果，不造全部楚军死亡数；与新尽杀叙法并列。')
claim('event',E,'description','新南汉世家称苏章锁住楚舟，夹江强弩射击，尽杀楚人。',11,'章舉巨輪挽索鎖楚舟，以彊弩夾江射之，盡殺楚人。','主楚兵大败解围遁去与新尽杀楚人结果措辞有别，保留异说，不认定全军每人阵亡或给死亡总数。',source=han,relation='conflicts')
E=ev('suzhang_fengzhou_tuanlianshi','南汉主以苏章为封州团练使',11,'汉主以章',None,[('汉主','授官者'),('章','封州团练使获任者')],when='928年封州解围之后，具体月日未明',place='封州',note='战后授官，与出兵时左右街使不同阶段；未推已按同日完成到任。')
E=ev('licongrong_hedong_northern_capital','李从荣由邺都留守任河东节度使、北都留守',12,'夏，四月','北都留守，',[('从荣','河东节度使北都留守获任者')],when='928年四月，确日未载',place='邺都至河东、北都',note='月头无干支，不能直接等后戊寅；与旧前十二月移太原的纪时层次并列。')
claim('event',E,'description','旧明宗纪在前一年十二月庚辰已记皇子从荣由邺都留守移镇太原。',12,'庚辰，皇子鄴都留守從榮移鎮太原。','旧927年十二月移镇概称与主928四月具体河东北都任官时间不同，保留不改主；未强称都是同一次同日任命。',source=dec,relation='conflicts')
E=ev('fengyun_northern_capital_deputy','太原人冯赟由客省使任北都副留守',12,'以客省使','为副留守，',[('冯赟','太原籍客省使、北都副留守获任者')],when='928年四月，确日未载',place='北都、太原',note='籍贯太原与留守治所区分，不标现代坐标；新稳定key，赟贇繁简不造两人。')
E=ev('yangsiquan_infantry_commander','新平人杨思权由夹马指挥使任步军都指挥使，辅佐李从荣',12,'夹马指挥使','以佐之。',[('杨思权','新平籍、步军都指挥使获任者')],when='928年四月，确日未载',place='北都',note='以佐之承从荣，不额外推私人盟誓关系；新平为籍贯名，不编生年。')
E=ev('shijingtang_yedu_tianxiong','石敬瑭任邺都留守、天雄节度使，加同平章事',12,'戊寅','加同平章事；',[('石敬瑭','由宣武任邺都天雄同平章事者')],when='928年四月戊寅',place='宣武至邺都、天雄',note='同平章事加衔不能等任中枢宰相已入朝；不重造去年的宣武任命。')
claim('event',E,'description','旧明宗纪同日记石敬瑭由汴州任邺都留守、天雄节度使及同平章事。',12,'夏四月戊寅，以汴州節度使石敬瑭為鄴都留守，充天雄軍節度使，加同平章事；','汴州宣武为治州军号，沿同人同次任官，不编第二次官迁。',source=old,relation='corroborates')
E=ev('fanyanguang_chengde_command','范延光由枢密使任成德节度使',12,'以枢密使范延光','为成德节度使。',[('范延光','由枢密任成德者')],when='928年四月戊寅',place='后唐朝廷至成德',note='承同段戊寅，主未列其他兼职，新罢枢密不推全部职衔被削。')
claim('event',E,'description','旧明宗纪同日记范延光由枢密使、权知镇州军府事任镇州节度使，兼北面水陆转运使。',12,'以樞密使、權知鎮州軍府事、檢校太保範延光為鎮州節度使兼北面水陸轉運使；','範与范字形同人，镇州与成德治州军号相合，补兼职与原权知，不新造人。',source=old)
claim('event',E,'description','新明宗纪四月戊寅称范延光罢。',12,'夏四月戊寅，延光罷。','回查前文延光为枢密，罢为枢密去职，与主出镇同阶段，不推成德未授。',source=new,relation='corroborates')
E=ev('anzhonghui_henan_yin','枢密使安重诲兼河南尹',12,'丙戌','兼河南尹，',[('安重诲','河南尹兼任者')],when='928年四月丙戌',place='河南府',note='兼任保留枢密衔，非前段三月拟外调已执行。')
claim('event',E,'description','旧明宗纪同日记安重诲兼河南尹。',12,'丙戌，樞密使安重誨兼河南尹；','同一兼任补证，保留誨原字。',source=old,relation='corroborates')
E=ev('liconghou_xuanwu_retains_guards','李从厚由河南尹任宣武节度使，仍判六军诸卫事',12,'以河南尹从厚','仍判六军诸卫事。',[('从厚','宣武节度使获授者、保留六军诸卫职责')],when='928年四月丙戌',place='河南府至宣武、汴州',note='仍判是延续已有职责，不重造六军职初授或提前后十一月婚礼。')
claim('event',E,'description','旧明宗纪同记李从厚任汴州节度使，判六军如故。',12,'以皇子河南尹、判六軍諸衛事從厚為汴州節度使，判六軍如故。','汴州宣武同地两种职称，任官同事，未推实际驻军编制人数。',source=old,relation='corroborates')
E=ev('wu_miaolin_wangyanzhang_attacks_yuezhou','吴将苗璘、王彦章领水军万人攻楚岳州，至君山',12,'吴右雄武','至君山，',[('璘','吴右雄武军使、领水军者'),('彦章','吴静江统军、领水军者')],when='928年四月，丁亥交战前',place='君山、岳州',note='王彦章限定吴将，区别此前后梁王彦章；万人为原兵力概录，不推精确点名册或舟数。')
E=ev('mayin_orders_xudemun_defense','马殷遣右丞相许德勋领战舰千艘迎御吴军',12,'楚王殷遣','千艘御之。',[('殷','遣防御军者'),('德勋','右丞相、御吴统领')],when='928年四月吴军到君山之后，确日未载',place='楚岳州水域',note='千艘为所领舰数，不能等千人或全部楚境兵力；御军与攻荆南此前战不同。')
E=ev('xudemun_assesses_wu_fear','许德勋认为吴军掩袭，见楚大军必惧而走',12,'德勋曰','必惧而走。”',[('德勋','战前判断所归者')],when='928年四月迎御吴军前后本段',place='岳州水域',note='这是许的判断，不作为吴军心理已实证；后吴实际败擒不是此句已发生逃亡。')
E=ev('chu_hides_jiaozi_wanghuan_blocks_route','楚军潜伏角子湖，王环夜领战舰三百屯杨林浦，截吴归路',12,'乃潜军','绝吴归路。',[('德勋','潜军、派截路者'),('环','夜领三百舰屯杨林浦者')],when='928年四月，丁亥之前的夜间布置',place='角子湖、杨林浦',note='伏地与截路地分别记录，不给现代坐标；王环沿楚将key，舰三百不是人三百。')
E=ev('wu_advances_jingjiangkou_plans_jingnan_join','次晨吴军进至荆江口，计划会荆南军攻岳州',12,'迟明','将会荆南兵攻岳州，',[],when='928年四月上述楚伏军夜后的迟明',place='荆江口、拟攻岳州',note='将会为计划，不能证明荆南军已抵现场或虚构其统领；不新建永恒军事同盟关系。')
E=ev('wu_reaches_daorenji','吴军于丁亥至道人矶',12,'丁亥','至道人矶。',[],when='928年四月丁亥',place='道人矶',note='确定到达干支不自行公历换算；未另具守将姓名。')
E=ev('zhanxin_rear_xudemun_front_attack','许德勋命詹信领轻舟三百绕至吴军后方，自己以大军当其前夹击',12,'德勋命','夹击之，',[('德勋','前军夹击统领、命绕后者'),('詹信','战棹都虞侯、领三百轻舟绕后者')],when='928年四月丁亥道人矶交战',place='道人矶',note='原舟三百与前王环战舰三百为两项，不混同同一军；不能推三百人。')
E=ev('chu_defeats_wu_captures_commanders','吴军大败，楚军俘苗璘与王彦章而归',12,'吴军大败',None,[('璘','被俘吴将'),('彦章','被俘吴将'),('德勋','楚胜军统领')],when='928年四月丁亥交战后，归军确日未载',place='道人矶至楚',note='俘为活捉，不造二将战死或提前后续被放还；未推吴全军阵亡。')
claim('event',E,'description','旧明宗纪四月丁亥记复州奏报湖南大破吴军于道人矶。',12,'丁亥，復州奏，湖南大破淮賊於道人磯。','主同日到达及战事与旧丁亥奏报层次区分；旧未列苗王姓名，不冒称它直接印证二将被俘。',source=old,relation='corroborates')
review='连续11—12段逐句校核。楚马到岳、派袁诠王环马希瞻、荆南迎战、夜藏数十舰、次晨横击、败俘斩千进逼江陵、请和还史、军还责问和王缓冲战略分别；未取荆南不能作已吞并，俘斩合计非全阵亡。新楚明年正月前句贡使被执时间不直接赋后攻军；和止印证但未直写归史。王环复用914楚将，区别后蜀同名；每战身先同甘苦针药疗伤及士卒话、所向有功是泛述null不强当前战或现代疗效。楚围封不具将名不把荆南三将推来。新汉先贺江败补阶段，四年承白龙上下文另快照；刘岩龑同人，占筮不当有效神示。赦改元、苏援神弩三千舰百、铁絙巨轮堤伏、佯败楚追、索锁船弩夹射、楚败退解围、苏团练分阶段。新神弩军三千及两索为补称，主未定弩具数量不硬兵器人数；主大败解围退、新尽杀措辞有别并列，不给全军阵亡数。11段列四月前未具月日，年928不强全三月。四月从荣具体官衔与旧927十二月庚辰移太原纪时层次并列，不静改主；冯赟太原籍与杨思权新平籍分籍贯治所，新人不编生年。戊寅石邺天雄衔、范成德与旧转运、新罢枢密同事；丙戌安兼河南非三月拟外调兑现、从厚宣武仍判非初授或纳妃。吴万人苗璘/王彦章吴静江统军，王独立限定避免梁王混；楚许千舰御、判断话语、角湖伏与王环三百舰截杨浦、吴迟明荆江口将会荆南只计划、丁亥道人到达、詹三百轻舟后袭与许当面夹、败擒归分事。舟数非人数，旧丁亥复州奏是报告不是人物捕获直接独证；不提前释放苗王，未给荆南援军已在场及名字。简体展示、原字摘录与定位，纸本异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,13):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
context=P/'sources/library/xinwudaishi-065-era-context';rec=json.loads((context/'paragraph.json').read_text());ctx=dict(file='library/xinwudaishi-065-era-context/source.txt',sha256=hashlib.sha256((context/'source.txt').read_bytes()).hexdigest(),paragraph_id=rec['id'],upstream_locator=rec['locator'],url='https://github.com/greed-216/histree/blob/b559f13a/'+str((context/'source.txt').relative_to(ROOT)),purpose='核对下一段四年所承白龙年号；不是本批新史事，不作为独立fact_claim。')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(11,13)],next_paragraph='zztj-v276-y0928-p013',next_volume=276,next_year=928,supplements=supplements,source_contexts=[ctx],excluded_non_body=[],coverage='卷276连续928年第11—12段、原文件43—44行；楚荆南与南汉封州水战、四月任官、吴楚道人矶战。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(11,13)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
