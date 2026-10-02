"""Curate consecutive Tongjian volume 271, year 921, paragraphs 1–6."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 25))
specs = [
    ('tongjian-271-921-opening', P / 'sources/library/tongjian-271-921-opening', '668adafc', '司马光等'),
    ('tongjian-271-921-spring', P / 'sources/library/tongjian-271-921-spring', '668adafc', '司马光等'),
    ('new-wudaishi-61-yang-pu', P / 'sources/library/new-wudaishi-61-yang-pu', '668adafc', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0921-p001-p006',
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
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(1, 7):
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
people, used, reused, supplements = {}, {}, set(), []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷271·龙德元年（921）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0921_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','蜀主':'王宗衍','吴主':'杨溥','高祖':'王建','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'王宗衍韦妃':['韦妃','韋妃'],'王宗衍高氏妃':[],'高知言':[],'传真':['傳真']}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271龙德元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='921年正月本段；确日未载', note='', year=921, place='五代十国'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0921_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_271_0921_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('shu_returns_chengdu','蜀主王宗衍还成都',1,Q[1]['text'],[('蜀主','还成都的蜀主')],when='921年正月甲午',place='成都')
event('wang_jian_arranges_crown_prince_marriage','王建为太子王宗衍聘高知言女为妃',2,
 '初，蜀主之为太子，高祖为聘兵部尚书高知言女为妃，',
 [('高祖','为太子聘妃者'),('蜀主','在太子时期受聘妃者'),('高知言','时任兵部尚书、所聘女子之父'),('高知言女','被聘为太子妃者')],
 when='王宗衍为太子时追叙；确年未载',year=None,place='蜀',note='高祖按前蜀王建识别；女子未载个人名，使用限定身份名称，不把高氏与其他女子混同。')
event('shu_sends_gao_consort_home','王宗衍遣高知言女归家，高知言惊仆不食而卒',2,
 '无宠，及韦妃入宫，尤见疏薄，至是遣还家，知言惊仆，不食而卒。',
 [('蜀主','遣高妃归家者'),('高知言女','无宠被遣还家者'),('高知言','闻讯惊仆、不食而卒者')],
 when='921年正月本段至是；确日未载',place='蜀',note='至是将遣还及高知言卒连于本年，未将之前的无宠和入宫追叙硬定921；不自行推死亡间隔。')
claim('person','person_高知言','death_year','高知言于921年正月本段被记不食而卒。',2,
 '至是遣还家，知言惊仆，不食而卒。','按至是本年纪事；未有日次。')
event('xu_consort_enters_shu_palace','王宗衍见徐耕孙女而悦，太后纳其入后宫',2,
 '韦妃者，徐耕之孙也，有姝色，蜀主适徐氏，见而悦之，太后因纳于后宫，',
 [('韦妃','徐耕孙女、被纳后宫者'),('徐耕','韦妃之祖父'),('蜀主','适徐氏见而悦之者'),('太后','纳其入后宫者')],
 when='韦妃入宫背景追叙；确年未载',year=None,place='蜀',note='韦妃是称谓；该女属徐氏，本段下句托称韦昭度孙女，不能据托词建立真实韦氏祖孙关系。')
claim('person','person_王宗衍韦妃','description','韦妃实为徐耕孙女；王宗衍托称其为韦昭度孙女。',2,
 '蜀主不欲娶于母族，托云韦昭度之孙。','托云为身份托词，未建韦昭度祖父关系；徐氏个人名未载。')
event('shu_consort_promoted_yuanfei','韦妃初为婕妤，累加元妃',2,
 '初为婕妤，累加元妃。',[('韦妃','由婕妤累加元妃者')],
 when='韦妃入宫后追叙；确年未载',year=None,place='蜀')
event('shu_king_plays_in_brocade_screens','王宗衍列锦步障击球，远适而外人不知',2,
 '蜀主常列锦步障，击球其中，往往远适而外人不知，',[('蜀主','列锦步障击球、远适者')],
 when='王宗衍在位习惯性叙述；确年未载',year=None,place='蜀')
event('shu_king_burns_fragrances','王宗衍昼夜焚香，久厌更焚皂荚',2,
 '爇诸香，昼夜不绝。久而厌之，更爇皁荚以乱其气。',[('蜀主','昼夜焚香后改焚皂荚者')],
 when='王宗衍在位习惯性叙述；确年未载',year=None,place='蜀',note='皁荚展示规范化为皂荚；逐字引用保留底本皁字。')
event('shu_king_builds_silk_mountains','王宗衍结缯为山及宫殿楼观，损坏则换新',2,
 '结缯为山，及宫殿楼观于其上，或为风雨所败，则更以新者易之。',[('蜀主','以缯营造山及宫殿楼观者')],
 when='王宗衍在位习惯性叙述；确年未载',year=None,place='蜀',note='保留主书所述缯制景物，不推具体工程规模或费用。')
event('shu_king_drinks_on_silk_mountain','王宗衍在缯山乐饮，涉旬不下',2,
 '或乐饮缯山，涉旬不下。',[('蜀主','在缯山乐饮者')],when='王宗衍在位习惯性叙述；确年未载',year=None,place='蜀')
event('shu_king_returns_by_lit_boats','王宗衍穿渠通禁中，夜归以宫女千余持炬照船',2,
 '山前穿渠通禁中，或乘船夜归，令宫女秉蜡炬千馀居前船，却立照之，水面如昼。',[('蜀主','乘船夜归、令宫女持炬照船者')],
 when='王宗衍在位习惯性叙述；确年未载',year=None,place='蜀宫禁',note='千余为史载数，不把匿名宫女逐一建实体；未推渠的坐标。')
event('shu_king_drinks_until_dawn','王宗衍禁中酣饮鼓吹达旦，习以为常',2,
 '或酣馀禁中，鼓吹沸腾，以至达旦。以是为常。',[('蜀主','禁中酣饮鼓吹达旦者')],
 when='王宗衍在位习惯性叙述；确年未载',year=None,place='蜀宫禁',note='底本作酣馀，暂据上下文记录酣饮，摘录不改字，纸本待核。')

def relationship(a,b,kind,n,quote,note):
    pa=person(a,n,f'{b}之{kind}',quote); pb=person(b,n,f'与{a}关系对象',quote)
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
        row=dict(key=f'relationship_zztj_271_0921_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note)
relationship('高知言','高知言女','父亲',2,'高知言女为妃','女明确父女；未载个人名。')
relationship('高知言女','蜀主','妻子',2,'高祖为聘兵部尚书高知言女为妃','聘为妃按已成立太子婚配关系记录，适用为遣归前；未强定婚姻年月。')
relationship('徐耕','韦妃','祖父',2,'韦妃者，徐耕之孙也','徐氏母族孙女，祖父明文；不据托云韦昭度建虚假祖孙关系。')
relationship('韦妃','蜀主','妃子',2,'初为婕妤，累加元妃。','元妃身份记录妃子，避免笼统妻子与正妻混同；未强定纳妃年月。')

event('wen_zhaotu_transferred_xuchang','温昭图徙匡国节度使镇许昌',3,
 '甲辰，徙静胜节度使温昭图为匡国节度使，镇许昌。',[('温昭图','由静胜徙匡国节度使者')],
 when='921年正月甲辰',place='许昌',note='温昭图复用既有温韬主体；温昭图为此时所用名，职衔按底本。')
claim('person','person_温韬','description','温昭图素事赵岩，主书以此说明其得名藩。',3,
 '昭图素事赵岩，故得名籓。','事赵岩是主书叙述，不扩大为终身主从或另建统属关系。')
person('赵岩',3,'温昭图素事之人','昭图素事赵岩，故得名籓。')
event('shu_wu_urge_jin_emperor','蜀主、吴主屡致书劝李存勖称帝',4,
 '蜀主、吴主屡以书劝晋王称帝，',[('蜀主','致书劝晋王称帝者'),('吴主','致书劝晋王称帝者'),('晋王','受劝称帝者')],
 note='屡以书保留多次劝进；当前吴主为杨溥，不能沿用已卒杨隆演。')
event('jin_recounts_father_warning','李存勖示劝进书，称父亲遗训当复唐社稷',4,
 '晋王以书示僚佐曰：',[('晋王','向僚佐陈述先王遗训者')],
 note='本年事件是李存勖陈述旧训；不把引语中的先王旧事全当921发生。')
claim('event',used[4][-1],'description','李存勖称先王劝其以复唐社稷为心，拒闻自帝之议而泣。',4,
 '汝它日当务以复唐社稷为心，慎勿效此曹所为！’言犹在耳，此议非所敢闻也。”因泣。',
 '这是本段所载李存勖转述的先王遗训；先王指李克用，不增九锡禅让真实事件。')
event('jin_orders_imperial_regalia','将佐藩镇劝进不已，李存勖令市玉造法物',4,
 '既而将佐及蕃镇劝进不已，乃令有司市玉造法物。',[('晋王','命有司市玉造法物者')],
 note='备法物是筹备称帝，不等于已登基。')
event('huang_chao_period_seal_found','黄巢破长安时，魏州僧传真之师得传国宝',4,
 '黄巢之破长安也，魏州僧传真之师得传国宝，藏之四十年，',[],
 when='黄巢破长安时期追叙；确年未载',year=None,place='长安、魏州',note='传国宝为史书的认定；四十年不倒推精确年份，师名未载，不建匿名师实体。')
event('chuanzhen_presents_seal','僧传真欲售所藏玉，获指为传国宝后献行台',4,
 '至是，传真以为常玉，将鬻之，或识之，曰：“传国宝也。”传真乃诣行台献之，将佐皆奉觞称贺。',
 [('传真','献传国宝于行台的魏州僧人')],place='魏州、行台',
 note='宝物身份按本段传国宝说法保留，不认作经过现代鉴定；未为僧人与宝物增虚构拥有史。')
event('zhang_chengye_remonstrates','张承业自晋阳赴魏州，谏先灭梁而后定帝位',5,
 '张承业在晋阳闻之，诣魏州谏曰：',[('张承业','赴魏州劝谏者'),('晋王','受劝谏的李存勖')],place='晋阳、魏州',
 note='本次劝谏在921筹备称帝段；未据劝进视作923已登基。')
claim('event',used[5][-1],'description','张承业主张先灭朱氏、立唐后，再统一吴蜀，迟让帝位以固根基。',5,
 '王何不先灭硃氏，复列圣之深仇，然后求唐后而立之，南取吴，西取蜀，汛扫宇内，合为一家，',
 '这是张承业建议，不能录为已经灭梁、立唐后或灭吴蜀的事实。')
claim('event',used[5][-1],'description','李存勖答称非己所愿、难违群下意；张承业恸哭称误老奴。',5,
 '王曰：“此非余所愿，奈群下意何。”承业知不可止，恸哭曰：“诸侯血战，本为唐家，今王自取之，误老奴矣！”',
 '记录对话归属；不把高宜按高祖自动改字或新建人物，高宜疑讹保留待核。')
event('zhang_chengye_returns_ill','张承业归晋阳成疾，不复起',5,
 '即归晋阳邑，成疾，不复起。',[('张承业','劝谏后归晋阳成疾者')],place='晋阳',
 note='不复起不直接写为921死亡；死亡另待后文明确纪年。')
e=event('wu_changes_shunyi','吴改元顺义',6,Q[6]['text'],[],when='921年二月',place='吴')
claim('event',e,'description','吴在杨溥时期于二月改元顺义；《新五代史》并记赦境内。',6,
 '明年二月，改元順義，赦境內。','以隆演卒后立溥之明年顺承921；补充赦境内，未移入同段冬十一月史事。',
 source='new-wudaishi-61-yang-pu',relation='adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,7):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
      review='921年首六段连续校核；前蜀追叙和宫廷习惯未强定年，吴主按杨溥；传国宝及劝进为史载说法，未误记已称帝。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=271,year=921,
 primary_source_key=main_sources[0],primary_source_keys=main_sources,
 paragraphs=[Q[n]['id'] for n in range(1,7)],next_paragraph=Q[7]['id'],supplements=supplements,
 coverage='卷271龙德元年首六段：前蜀宫廷、温昭图调任、晋筹帝位、张承业劝谏、吴改元；原文件43—48行。',
 reviewed_questions=[
 {'paragraph_id':Q[2]['id'],'note':'韦妃实徐耕孙，托称韦昭度孙不建虚假亲属；高知言女未名。初及常或习惯性叙述年为空，至是遣归及高卒归921。'},
 {'paragraph_id':Q[3]['id'],'note':'温昭图按既有温韬主体复用，不因异名重复建人。'},
 {'paragraph_id':Q[4]['id'],'note':'吴主为920年继位杨溥；筹帝位不等于称帝；黄巢时得宝属追叙，不倒推四十年。王太师与先王旧训为李存勖转述，未重复建旧事。'},
 {'paragraph_id':Q[5]['id'],'note':'高宜疑高祖之电子讹字，未据自动繁简转换改原文或建高宜人物；不复起未作921死亡。检索旧史卷72命中《五代史阙文》引述，不当独立原始确证。'},
 {'paragraph_id':Q[6]['id'],'note':'新五代史卷61杨溥条对应明年二月改元顺义并赦境内；原繁体引用保留。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
