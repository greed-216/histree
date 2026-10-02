"""Curate consecutive Tongjian volume 271, year 921, paragraphs 15–18."""
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
    ('tongjian-271-921-spring', YEAR / 'part-01/sources/library/tongjian-271-921-spring', '668adafc', '司马光等'),
    ('tongjian-271-921-fu-xi', P / 'sources/library/tongjian-271-921-fu-xi', '57d33707', '司马光等'),
    ('tongjian-271-921-zhen-ding', P / 'sources/library/tongjian-271-921-zhen-ding', '57d33707', '司马光等'),
    ('jiuwudaishi-029-fu-xi-zhenzhou', P / 'sources/library/jiuwudaishi-029-fu-xi-zhenzhou', '57d33707', '薛居正等'),
    ('jiuwudaishi-029-desheng', P / 'sources/library/jiuwudaishi-029-desheng', '57d33707', '薛居正等'),
    ('xinwudaishi-039-wang-du-adoption', P / 'sources/library/xinwudaishi-039-wang-du-adoption', '57d33707', '欧阳修'),
    ('xinwudaishi-039-wang-du-coup', P / 'sources/library/xinwudaishi-039-wang-du-coup', '57d33707', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:3]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0921-p015-p018',
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
for n in range(15, 19):
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
people, used, reused, supplements = {}, {}, {'tongjian-271-921-spring'}, []

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
    ck = f'claim_zztj_271_0921_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','高祖':'王建','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'王都':['刘云郎','劉雲郎','云郎'],'王郁':['王鬱'],'王铤':['王鋌'],'张处瑾':['張處瑾'],'符蒙':[],'李应之':['李應之'],'和昭训':['和昭訓'],'王郁妻李氏':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271龙德元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='921年本段；确日未载', note='', year=921, place='五代十国', source=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0921_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_271_0921_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
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
        row=dict(key=f'relationship_zztj_271_0921_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)
event('zhu_youqian_sends_su_xun','朱友谦遣唐旧臣苏循赴晋行台',15,
 '晋王既许籓镇之请，求唐旧臣，欲以备百官。硃友谦遣前礼部尚书苏循诣行台，',
 [('晋王','求唐旧臣备百官者'),('硃友谦','遣苏循赴行台者'),('苏循','前礼部尚书、赴行台者')],
 when='921年七月后本段；确月日未载',place='魏州、晋行台',note='备百官为称帝筹备；不视为此时正式称帝。')
event('su_xun_bows_and_calls_emperor','苏循至魏州拜府衙为殿，见李存勖呼万岁称臣',15,
 '循至魏州，入牙城，望府廨即拜，谓之拜殿。见王呼万岁舞蹈，泣而称臣。',
 [('循','拜殿、呼万岁称臣者'),('晋王','受苏循礼拜呼万岁者')],when='921年苏循至魏州时',place='魏州',note='谓之拜殿是苏循的礼仪表达；未据此把牙城府廨正式改记宫殿。')
event('su_xun_gives_pens_promoted','苏循献画日笔，李存勖任其河东节度副使',15,
 '翌日，又献大笔三十枚，谓之“画日笔”。王大喜，即命循以本官为河东节度副使，张承业深恶之。',
 [('循','献三十枚画日笔、受任节度副使者'),('晋王','任苏循河东节度副使者'),('张承业','深恶苏循者')],when='921年苏循见晋王翌日',place='魏州')
event('zhang_wenli_seeks_khitan_help','张文礼经卢文进求契丹援兵',15,
 '张文礼虽受晋命，内不自安，复遣间使因卢文进求援于契丹；',
 [('张文礼','受晋命后密求契丹援者'),('卢文进','求契丹援经由之人')],
 when='921年受晋任命后本段；确日未载',place='镇州、契丹',note='秘密求援是动作；此句没有契丹已出兵的结果。')
event('zhang_wenli_seeks_liang_troops','张文礼告梁称已召契丹，请万人渡河相助',15,
 '又遣间使来告曰：“王氏为乱兵所屠，公主无恙。臣已北召契丹，乞朝廷发精甲万人相助，自德、棣渡河，则晋人遁逃不暇矣。”',
 [('张文礼','向梁密求精甲万人援助者')],when='921年受晋任命后本段；确日未载',place='镇州、梁、德州、棣州',
 note='王氏被乱兵所屠、已召契丹、晋将逃遁均为其报文和预测，不据此免除其乱事责任或记梁已派万人。')
event('jing_xiang_urges_help_wenli','敬翔建议梁趁镇州乱援张文礼以复河北',15,
 '帝疑未决。敬翔曰：“陛下不乘此衅以复河北，则晋人不可复破矣。宜徇其请，不可失也。”',
 [('梁帝','犹疑是否援张文礼者'),('敬翔','建议乘镇州乱复河北者')],when='921年张文礼求梁援后',place='梁',note='敬翔建议与其预测作为言论记录，不记梁已恢复河北。')
event('liang_declines_wenli_reinforcements','梁近臣反对分兵援张文礼，梁帝止之',15,
 '赵、张辈皆曰：“今强寇近在河上，尽吾兵力以拒之，犹惧不支，何暇分万人以救张文礼乎！且文礼坐持两端，欲以自固，于我何利焉！”帝乃止。',
 [('梁帝','听反对意见而止援者')],when='921年张文礼求梁援后',place='梁',note='赵、张辈未明全名，不强配赵岩、张汉杰等具体身份；持两端为近臣判断。')
event('jin_intercepts_returns_wenli_letters','晋屡获张文礼蜡丸绢书，李存勖遣使归之',16,
 '晋人屡于塞上及河津获文礼蜡丸绢书，晋王皆遣使归之，文礼惭惧。',
 [('晋王','遣使归所获密书者'),('张文礼','密书被截而惭惧者')],when='921年张文礼密求援后、八月讨镇前',place='塞上、河津、镇州')
event('zhang_wenli_kills_old_zhao_officers','张文礼忌赵旧将，多所诛灭',16,
 '文礼忌赵故将，多所诛灭。',[('张文礼','多诛赵旧将者')],when='921年镇州夺权后、八月讨镇前',place='镇州',note='旧将未列姓名，不逐人虚构死者或把符习录为被杀。')
event('zhang_wenli_recalls_fu_xi','张文礼请召符习回镇、任符蒙参军并赍钱帛劳军',16,
 '符习将赵兵万人从晋王在德胜，文礼请召归，以它将代之，且以习子蒙为都督府参军，遣人赍钱帛劳行营将士以悦之。',
 [('符习','率赵兵万人在德胜、被请求召归者'),('张文礼','请召符习、任其子并劳军者'),('蒙','被任都督府参军的符习之子')],
 when='921年八月讨镇前',place='德胜、镇州',note='请召归不等于已返镇；任子参军保留职衔，不误录其当时在德胜领万人。')
relationship('符习','蒙','父亲',16,'且以习子蒙为都督府参军','习子蒙明确父子；规范名符蒙，无生年依据。')
event('fu_xi_requests_stay_and_revenge','符习请留，李存勖许助兵粮为王镕复仇',16,
 '习见晋王，泣涕请留，晋王曰：“吾与赵王同盟讨贼，义犹骨肉，不意一旦祸生肘腋，吾诚痛之。汝苟不忘旧君，能为之复仇乎？吾以兵粮助汝。”',
 [('习','请留并愿报旧君者'),('晋王','许兵粮助复仇者')],when='921年八月讨镇前',place='德胜',note='义犹骨肉是政治情谊比喻，未建李存勖与王镕真实兄弟关系。')
claim('event',used[16][-1],'description','符习与部将三十余人恸哭，愿以所部报王氏之恩。',16,
 '习与部将三十馀人举身投地恸哭曰：','三十余是将领人数，不与万人兵数混同；所述复仇意愿归属当事人。')
claim('event',used[16][-1],'description','《旧五代史》亦记晋告符习等将弑逆之罪、许资粮兵甲，诸将三十余人请讨。',16,
 '於是習等率諸將三十餘人，慟哭於牙門，請討文禮。','印证请讨，旧史称帝为后世叙法，不记921即位。',source='jiuwudaishi-029-fu-xi-zhenzhou',relation='corroborates')
event('jin_commissions_fu_xi_campaign','李存勖任符习成德留后，命阎宝、史建瑭助讨',17,
 '八月，庚申，晋王以习为成德留后，又命天平节度使阎宝、相州刺史史建瑭将兵助之，自邢洺而北。',
 [('晋王','授符习留后并派助军者'),('习','受任成德留后、率赵军讨镇者'),('阎宝','助攻的天平节度使'),('史建瑭','助攻的相州刺史')],
 when='921年八月庚申',place='邢州、洺州、镇州')
claim('event',used[17][-1],'description','《旧五代史》记授符习成德军兵马留后、遣阎宝助之，以史建瑭为前锋。',17,
 '帝因授習成德軍兵馬留後，以部下鎮、冀兵致討於文禮；又遣閻寶以助之，以史建瑭為前鋒。','补史建瑭前锋身份，通鉴成德留后与旧史成德军兵马留后分别保留，未扩为已正式节度使。',source='jiuwudaishi-029-fu-xi-zhenzhou')
event('jin_takes_zhaozhou_wang_ting_surrenders','晋拔赵州，王铤降而复任刺史',17,
 '甲子，晋兵拔赵州，刺史王铤降，晋王复以为刺史，',[('王铤','归降、获复任的赵州刺史'),('晋王','复任王铤为刺史者')],
 when='921年八月甲子',place='赵州')
claim('event',used[17][-1],'description','《旧五代史》记甲子攻赵州，王铤送符印以迎。',17,
 '甲子，攻趙州，刺史王鋌送符印以迎，','补迎降方式；铤与鋌为繁简，对同一职任复用同人。',source='jiuwudaishi-029-fu-xi-zhenzhou',relation='corroborates')
event('zhang_wenli_dies_zhaozhou_falls','张文礼先病腹疽，闻赵州失陷惊惧而卒',17,
 '文礼先病腹疽；甲子，晋兵拔赵州，刺史王铤降，晋王复以为刺史，文礼闻之，惊惧而卒。',
 [('张文礼','先病腹疽、闻赵州失陷后死亡者')],when='921年八月甲子赵州失陷后；卒日未单列',place='镇州',
 note='甲子明确赵州失陷；卒日未独立纪，不硬定死亡也在甲子，疾病与惊惧按主书。')
claim('person',people['张文礼'],'death_year','张文礼于921年八月条病腹疽、惊惧而卒。',17,
 '文礼闻之，惊惧而卒。','死亡据本段八月条，疾病另见前句腹疽；不自行作现代病因诊断。')
claim('event',used[17][-1],'description','《旧五代史》亦记张文礼八月病疽卒，张处瑾代掌军务。',17,
 '是月，張文禮病疽而卒，其子處瑾代掌軍事。','印证月次和子代军务；未由旧史病疽覆盖主书惊惧说法。',source='jiuwudaishi-029-fu-xi-zhenzhou',relation='corroborates')
event('zhang_chujin_hides_father_death','张处瑾秘不发丧，与韩正时谋拒晋',17,
 '其子处瑾秘不发丧，与其党韩正时谋悉力拒晋。',[('处瑾','秘父死、谋拒晋者'),('韩正时','同谋拒晋者')],
 when='921年八月张文礼卒后',place='镇州')
relationship('张文礼','处瑾','父亲',17,'其子处瑾秘不发丧','其子承张文礼，方向为张文礼是张处瑾的父亲。')
event('jin_floods_zhenzhou_captures_youshun','晋渡滹沱围镇州，决渠灌城、获张友顺',17,
 '九月，晋兵渡滹沱，围镇州，决漕渠以灌之，获其深州刺史张友顺。',
 [('张友顺','被俘的深州刺史、此前镇州军校')],when='921年九月',place='滹沱、镇州',note='复用二月推张文礼的军校；不把决漕渠扩作掘黄河。')
event('shi_jiantang_dies_arrow','史建瑭中流矢卒',17,
 '壬辰，史建瑭中流矢卒。',[('史建瑭','中流矢死亡者')],when='921年九月壬辰',place='镇州')
claim('person',people['史建瑭'],'death_year','史建瑭卒于921年九月壬辰条。',17,'壬辰，史建瑭中流矢卒。','本段确年日可回查。')
claim('event',used[17][-1],'description','《旧五代史》记史建瑭在镇州城下交战时中流矢卒。',17,
 '九月，前鋒將史建瑭與鎮人戰於城下，為流矢所中而卒。','补城下交战场景，不凭箭矢指定射手。',source='jiuwudaishi-029-fu-xi-zhenzhou',relation='corroborates')
event('dai_siyuan_plans_desheng_attack','戴思远谋悉杨村军袭德胜北城，李存勖从降者获知',17,
 '晋王欲自分兵攻镇州，北面招讨使戴思远闻之，谋悉杨村之众袭德胜北城，晋王得梁降者，知之，',
 [('晋王','拟分兵攻镇、获降者告知者'),('戴思远','谋袭德胜北城的北面招讨使')],
 when='921年九月后、十月己未前',place='杨村、德胜北城',note='匿名降者未建个人实体；计划与实际交战分开。')
event('jin_sets_qicheng_ambush','李存勖令李嗣源伏戚城、符存审屯德胜，以骑兵诱梁',17,
 '冬，十月，己未，晋王命李嗣源伏兵于戚城，李存审屯德胜，先以骑兵诱之，伪示羸怯。',
 [('晋王','制定伏击者'),('李嗣源','伏兵戚城者'),('李存审','屯德胜的符存审')],when='921年十月己未',place='戚城、德胜',note='李存审复用符存审；伪示羸怯是诱敌动作，未作晋军真实战力评价。')
event('jin_defeats_dai_siyuan_desheng','晋败戴思远于德胜，梁失亡二万余',17,
 '梁兵竞进，晋王严中军以待之；梁兵至，晋王以铁骑三千奋击，梁兵大败，思远走趣杨村，士卒为晋兵所杀伤及自相蹈藉、坠河陷冰，失亡二万馀人。',
 [('晋王','主书所记以铁骑三千奋击者'),('戴思远','兵败奔杨村者')],when='921年十月己未',place='德胜、杨村',
 note='二万余为杀伤、蹈藉、坠河陷冰等失亡合计，不全写成斩首；精确数字按史载，未现代核验。')
claim('event',used[17][-1],'description','《旧五代史》记同战李嗣源以铁骑三千乘之、梁俘斩二万计。',17,
 '李嗣源以鐵騎三千乘之，梁軍大敗，俘斬二萬計。','旧史突出李嗣源进击，通鉴记晋王奋击；指挥及数字口径分别呈现，不累加为四万人。',source='jiuwudaishi-029-desheng')
event('li_congke_raids_liang_watchtower','李从珂伪持梁旗入梁垒，斧眺楼持级还',17,
 '時李從珂偽為梁幟，奔入梁壘，斧其眺樓，持級而還。',[('李从珂','伪持梁旗入垒毁眺楼者')],
 when='921年十月己未德胜战',place='德胜梁垒',source='jiuwudaishi-029-desheng',note='旧史补同一场战的行动；持级而还未指定被杀者姓名或数目，不作梁旗合法归属解释。')
event('li_siyuan_promoted_after_desheng','李存勖任李嗣源蕃汉内外马步副总管、同平章事',17,
 '晋王以李嗣源为蕃汉内外马步副总管、同平章事。',[('晋王','任命者'),('李嗣源','德胜胜后受任者')],
 when='921年十月德胜战后',place='晋')

event('li_yingzhi_gives_child_to_chuzhi','李应之将刘云郎送王处直，处直养为子名都',18,
 '初，义武节度使兼中书令王处直未有子，妖人李应之得小儿刘云郎于陉邑，以遗处直曰：“是儿有贵相。”使养为子，名之曰都。',
 [('王处直','养刘云郎为子、更名都者'),('李应之','得小儿并送与处直者'),('刘云郎','被处直收养、即王都者')],
 when='王处直无子时追叙；确年未载',year=None,place='陉邑、定州',note='贵相是李应之言论；云郎与王都同一人，不将相术作现代事实。')
relationship('王处直','都','养父',18,'使养为子，名之曰都。','明确收养，不能记王处直为王都亲生父亲。')
claim('person',people['王都'],'aliases','王都本为刘云郎，收养后更名都。',18,
 '應之於陘邑闌得小兒劉雲郎，養以為子，而處直未有子，乃以雲郎與處直，','新史印证同人并补李应之先养；闌得保留原字，未推儿童身世和亲生父母。',source='xinwudaishi-039-wang-du-adoption',relation='corroborates')
relationship('李应之','都','养父',18,'應之於陘邑闌得小兒劉雲郎，養以為子，','新史明确李应之先养为子，后送王处直；两养父适用先后阶段，非同时亲生父子。',source='xinwudaishi-039-wang-du-adoption')
event('wang_du_commands_new_army','王处直爱王都，置新军令其统领',18,
 '及壮，便佞多诈，处直爱之，置新军，使典之。',[('王处直','置新军令养子统领者'),('都','成年后统新军者')],
 when='王都成年后追叙；确年未载',year=None,place='定州',note='便佞多诈为主书评价；新史前段另记李应之立新军，不以同名新军强推必为同一批编制。')
event('wang_yu_flees_jin_married','王郁无宠奔晋，李克用以女妻之',18,
 '处直有孽子郁，无宠，奔晋，晋王克用以女妻之，累迁至新州团练使。',
 [('王处直','庶子王郁之父'),('郁','奔晋、娶李克用女并累迁新州者'),('李克用','以女妻王郁者'),('王郁妻李氏','与王郁成婚的李克用之女')],
 when='李克用在世时追叙；确年未载',year=None,place='晋、新州',note='孽子按庶出身份，非把孩子作道德评价；任官累迁为过程，未强定最终到任日期。')
relationship('王处直','郁','父亲',18,'处直有孽子郁','庶子亦为亲生子；不与王都收养混同。')
relationship('李克用','王郁妻李氏','父亲',18,'晋王克用以女妻之','以女妻郁明确父女，女子无名使用限定身份。')
relationship('王郁妻李氏','郁','妻子',18,'晋王克用以女妻之','明确嫁王郁；确婚期未载，不与其他李克用女混并。')
claim('person',people['王郁'],'description','《新五代史》记王郁奔晋、晋王以女妻之，任新州防御使。',18,
 '郁亦奔焉，晉王以女妻之，為新州防禦使。','主书称新州团练使，新史防御使职衔分别保留，不静默统一。',source='xinwudaishi-039-wang-du-coup',relation='conflicts')
event('chuzhi_makes_du_heir_apparent','王处直以王都为节度副大使，欲为嗣',18,
 '馀子皆幼；处直以都为节度副大使，欲以为嗣。',[('王处直','欲以养子继位者'),('都','受任节度副大使、拟继位者')],
 when='王处直被劫前背景；确年未载',year=None,place='定州',note='欲以为嗣是继承意向，不能提前记王都已正式节度使。')
event('chuzhi_urges_pardon_wenli','王处直恐镇亡定孤，劝李存勖赦张文礼',18,
 '及晋王存勖讨张文礼，处直以平日镇、定相为脣齿，恐镇亡而定孤，固谏，以为方御梁寇，且宜赦文礼。',
 [('王处直','恐镇亡定孤、劝赦张文礼者'),('晋王','受劝赦者')],when='921年晋讨张文礼时',place='定州、镇州',note='脣展示用唇，仅引文保留原字；恐镇亡定孤为处直判断，不立地缘必然因果。')
event('jin_refuses_wenli_pardon','李存勖以张文礼弑君、引梁，拒处直劝赦',18,
 '晋王答以文礼弑君，义不可赦；又潜引梁兵，恐于易定亦不利。',[('晋王','拒绝赦文礼者'),('王处直','受晋王答复者')],
 when='921年晋讨张文礼时',place='晋、易定')
claim('event',used[18][-1],'description','《新五代史》记庄宗以所获张文礼与梁蜡书示王处直，称师不可止。',18,
 '莊宗取所獲文禮與梁蠟書示處直曰：「文禮負我，師不可止。」','补拒赦时展示密书方式；称庄宗不等于921已称帝。',source='xinwudaishi-039-wang-du-coup')
event('chuzhi_orders_yu_summon_khitan','王处直遣人令王郁赂契丹犯塞，以解镇围',18,
 '处直患之，以新州地邻契丹，乃潜遣人语郁，使赂契丹，召令犯塞，务以解镇州之围；其将佐多谏，不听。',
 [('王处直','令子密召契丹而不听将佐谏者'),('郁','被令赂契丹犯塞者')],when='921年晋围镇州时',place='定州、新州、契丹',note='密召之令与实际契丹出兵另由后文确认；不将本句命令录为出兵结果。')
event('wang_yu_requests_heir_position','王郁忌王都冒继宗，要求为嗣，王处直许之',18,
 '郁素疾都冒继其宗，乃邀处直求为嗣，处直许之。',[('郁','请为嗣者'),('王处直','许王郁继嗣者')],
 when='921年召契丹之议中',place='新州、定州',note='嫉都冒继宗为王郁态度，已养子身份不因此否定。')
event('wang_du_he_zhaoxun_plot_coup','王都惧王郁夺继嗣，与和昭训谋劫王处直',18,
 '军府之人皆不欲召契丹，都亦虑郁夺其处，乃阴与书吏和昭训谋劫处直。',
 [('都','虑继位被夺而谋劫者'),('和昭训','参与谋劫的书吏')],when='921年王处直召契丹、许郁为嗣后',place='定州')
event('wang_du_seizes_chuzhi','王都伏新军于府第，劫王处直归西第',18,
 '会处直与张文礼使者宴于城东，暮归，都以新军数百伏于府第，大噪劫之，曰：“将士不欲以城召契丹，请令公归西第。”',
 [('王处直','城东宴使后归而被劫者'),('都','以新军伏府第劫处直者')],
 when='921年王处直被劫之夕；旧史十月辛酉记阎宝报变',place='定州城东、府第、西第',note='旧史报告日不等于劫持日，不自行把事件确日填辛酉。')
event('wang_du_confines_family_purges_officers','王都幽王处直及妻妾，杀中山子孙及腹心将佐',18,
 '乃并其妻妾幽之西第，尽杀处直子孙在中山及将佐之为处直腹心者。',
 [('都','幽父及妻妾、杀中山子孙腹心者'),('王处直','与妻妾被幽西第者')],when='921年定州政变后',place='西第、中山',note='死者限定在中山的子孙及腹心将佐，不包括在外的王郁；未因尽杀措辞虚构未名子孙名单。')
event('jin_accepts_du_replacing_chuzhi','王都自为留后报晋，李存勖以都代处直',18,
 '都自为留后，具以状白晋王。晋王因以都代处直。',[('都','自为留后并获晋认可者'),('晋王','以王都代王处直者')],
 when='921年定州政变后',place='定州、晋')
claim('event',used[18][-1],'description','《旧五代史》十月辛酉记阎宝报王处直被王都幽于别室、王都自称留后。',18,
 '辛酉，閻寶上言，定州節度使王處直為其子都幽於別室，都自稱留後。','印证政变并补报告日；不提前引用新史同段明年王处直之死。',source='jiuwudaishi-029-desheng',relation='corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(15,19):
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
  review='921年第15—18段连续校核；苏循劝进、张文礼求援、符习请讨、八月至十月战事与王都夺定；背景收养婚配不强定年。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=271,year=921,
 primary_source_key=main_sources[0],primary_source_keys=main_sources,
 paragraphs=[Q[n]['id'] for n in range(15,19)],next_paragraph=Q[19]['id'],supplements=supplements,
 coverage='卷271龙德元年第15—18段连续处理，原文件57—60行；长段内追叙、八月至十月分动作处理，后续未读段不宣称完成。',
 reviewed_questions=[
 {'paragraph_id':Q[15]['id'],'note':'劝进备百官未当登基；张文礼报梁求万人为言论及请求，未当援军已发；赵张辈不强配具体全名。'},
 {'paragraph_id':Q[16]['id'],'note':'骨肉为同盟比喻非真兄弟；请召符习未当已归镇，蒙按子名规范符蒙。'},
 {'paragraph_id':Q[17]['id'],'note':'甲子确指赵州归降，文礼死亡紧接但未独立记日；史建瑭九月壬辰卒有旧史城下书证。十月德胜旧史李嗣源铁骑三千与通鉴晋王奋击分别记，俘斩与失亡数字不累加。'},
 {'paragraph_id':Q[18]['id'],'note':'刘云郎即王都，先李应之养、后王处直养，两个养父方向与阶段分明；王郁为庶出亲子。李克用嫁女属生前追叙，女子无个人名。新州团练使与新史防御使并列。十月辛酉为报变日，未当政变确日；王处直明年死暂不入本批。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
