# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 932 paragraphs 11–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 29))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'01575dcc','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
V277=YEAR.parent.parent/'vol-277/year-0932'
specs += [('tongjian-278-932-july',YEAR/'part-01/sources/library/tongjian-278-932-july','24e32443','司马光等'),('jiuwudaishi-043-932-princess-report',V277/'part-01/sources/library/jiuwudaishi-043-932-princess-report','585a188b','薛居正等'),('jiuwudaishi-043-932-april',V277/'part-02/sources/library/jiuwudaishi-043-932-april','e9aa70e4','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-932-july','tongjian-278-932-october']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0932-p011-p020',
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
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(11, 21):
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
        citation = f'卷278·长兴三年（932）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0932_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','德钧':'赵德钧','仁赞':'孟昶','知祥':'孟知祥','知诰':'李昪','徐知诰':'李昪','从荣':'李从荣','从厚':'李从厚','重诲':'安重诲','王淑妃':'王德妃（李嗣源妃）','敬瑭':'石敬瑭','延光':'范延光','延寿':'赵延寿','硃弘昭':'朱弘昭','孟秸':'孟鹄','鹄':'孟鹄','赟':'冯赟','永宁公主':'永宁公主（石敬瑭妻）'}
NEW_ALIASES={'高辇':['高輦'],'李金全':[],'康澄':[],'永宁公主（石敬瑭妻）':['永宁公主','永寧公主']}

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

def event(code, title, n, quote, actors, when=None, note='', year=932, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='932年八月本段；确日未独载' if n<=12 else '932年九月本段；确日未独载' if n<=14 else '932年十月本段；确日未独载' if n<=19 else '932年十一月本段；确日未独载'
    key = 'event_zztj_278_0932_' + code
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
        edge = 'participation_zztj_278_0932_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_278_0932_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive ten body paragraphs in the next volume of the same year.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
old='jiuwudaishi-043-932-october';nov='jiuwudaishi-043-932-november';city='jiuwudaishi-098-dejun-cities';newcity='xinwudaishi-072-dejun-cities';poetry='jiuwudaishi-051-congrong-poetry';chang='xinwudaishi-064-meng-chang';princess='jiuwudaishi-039-yongning-title';sep='jiuwudaishi-043-932-princess-report';apr='jiuwudaishi-043-932-april'
ev('xu_expands_jinling','吴徐知诰扩建金陵城，史载周围二十里',11,'吴徐知诰',None,[('知诰','扩建金陵城者')],place='金陵',note='沿已建李昪主体；周围二十里为城周不是增加面积二十平方里，未换现代里程或画界。')
ev('khitan_disrupts_lulong_supply','通鉴追述契丹强盛后掠卢龙，常伏阎沟劫涿州输幽州粮',12,'初，契丹既强，','掠取之。',[],year=None,when='初，追述契丹强盛以来、赵德钧修城前；各次年份未独载',place='卢龙、涿州至幽州阎沟',note='每次为合述，不猜次数、未名统帅；虏为史文敌称不转成本站民族称号。')
E=ev('dejun_fortifies_liangxiang','赵德钧镇幽州后城阎沟置良乡戍守，粮道稍通',12,'及赵德钧为节度使，','粮道稍通。',[('德钧','城阎沟戍守改善粮道者')],year=None,when='赵德钧镇幽州后、三河奏城前追叙；确年未载',place='阎沟、良乡',note='不因所在932年条把良乡筑城强定932；稍通不等契丹掠粮彻底绝。')
claim('event',E,'description','旧赵传同记阎沟筑垒、戍兵守之，名良乡县以备钞寇。',12,'又於閻溝築壘，以戍兵守之，因名良鄉縣，以備鈔寇。','旧前水运长度段属于此前运河，不在本批借其二百里覆盖主六月一百六十五里；此只取良乡城戍。',source=city,relation='corroborates')
claim('event',E,'description','新契丹附录记于盐沟置良乡县。',12,'趙德鈞鎮幽州，於鹽溝置良鄉縣，','主旧阎沟、新盐沟各字形留，不据此立两个不同县；新庄宗末表相对层次，不独定此处932。',source=newcity,relation='corroborates')
E=ev('dejun_fortifies_luxian','赵德钧于幽州东五十里城潞县戍守，使近州民得耕作',12,'幽州东十里之外，','近州之民始得稼穑。',[('德钧','幽州东城潞县戍守者')],year=None,when='三河奏城前的筑城追叙；确年未载',place='幽州东潞县',note='十里不能樵牧是此前安全范围，五十里为潞县相对方位；未换坐标或认现代县界。')
claim('event',E,'description','新契丹附录亦记幽州东五十里筑城，戍以兵。',12,'又於幽州東五十里築城，皆戍以兵。','新此句未明城名，潞县身份据主；不写新也明称潞县。',source=newcity,relation='corroborates')
E=ev('dejun_builds_sanhe_repels','赵德钧城三河县以通蓟州运路，并击退来争契丹骑兵',12,'至是，又于州东北','德钧击却之。',[('德钧','三河筑城及击却争城骑兵者')],place='幽州东北三河、蓟州运路',note='百余里为相对距离，战日未独，不套后奏城庚辰；击却不等灭契丹国。')
claim('event',E,'description','旧赵传记幽州东筑三河城，北接蓟州，部民稍得樵牧。',12,'又於幽州東築三河城，北接薊州，頗為形勝之要，部民由是稍得樵牧。','旧传概述与主东北百余里详述分层，不改主方位为正东坐标；后清泰三年带兵与夹注辽史不在本批新增。',source=city,relation='adds')
ev('dejun_reports_sanhe_complete','九月庚辰朔赵德钧奏报三河城建成',12,'九月，庚辰朔，',None,[('德钧','奏城三河毕者')],when='932年九月庚辰朔奏闻；完工具体日未独载',place='三河、后唐朝廷',note='奏日非必确完工日，边人赖之为史评价，不据此画全国安定。')
E=ev('xifan_wuan_shizhong','九月壬午马希范任武安节度使，兼侍中',13,'壬午，',None,[('马希范','镇南节度使、转武安兼侍中者')],when='932年九月壬午',place='武安军',note='朝廷授任与此前七月迎、八月长沙袭位分。')
claim('event',E,'description','旧明宗纪同九月壬午记镇南节度使马希范任湖南节度使兼侍中。',13,'九月壬午，以鎮南軍節度使、檢校太尉馬希範為湖南節度使、檢校太尉、兼侍中。','湖南与武安地域军名同授，对应同人同日；不重复造马或两次任命。',source=sep,relation='corroborates')
E=ev('meng_renzan_acting_military','孟知祥命子仁赞摄行军司马，兼总辖两川牙内马步都军事',14,'孟知祥命其子',None,[('知祥','任子摄职者'),('仁赞','以仁赞旧名受摄军职者')],place='两川',note='仁赞沿现孟昶及仁赞别名；摄是代行，不把此时写为已即皇帝或东川正节度使。')
claim('event',E,'description','新孟世家记知祥为两川节度使时，昶为行军司马。',14,'知祥為兩川節度使，昶為行軍司馬。','主摄及兼总辖细节保留，新概官不取消摄字。其后僭号等未提前本段，父子既有关系复用。',source=chang,relation='corroborates')
relationship('知祥','仁赞','父亲',14,'孟知祥命其子仁赞','孟知祥→孟昶父亲，沿927稳定人物与父亲关系，不因仁赞改名新建子。')
claim('person',people['孟昶'],'description','新孟世家称昶为知祥第三子。',14,'昶，知祥第三子也。','排行按明文，未补未知兄长姓名和生日。',source=chang,relation='adds')
E=ev('li_cungui_second_mission','十月己酉朔李嗣源再遣李存瑰赴成都',15,'冬，十月，己酉朔，','帝复遣李存瓘如成都，',[('上','再遣供奉使者'),('李存瑰','被再次派赴成都者')],when='932年十月己酉朔遣；到成都具体日未独载',place='后唐朝廷至成都',note='主李存瓘疑同存瑰，新此前李瓌旧李瑰同供奉使同孟甥任务，复遣沿稳定key；底本文字保留，不把姓名一个字变体造新人。')
claim('event',E,'description','旧明宗纪同己酉朔记再遣李瑰，送故福庆公主祭赠绢三千匹及孟玉带。',15,'冬十月己酉朔，再遣供奉官李瑰使西川，兼押賜故福慶長公主祭贈絹三千匹，並賜知祥玉帶。','补此次使命，绢三千为公主祭赠不是孟所得银钱，未提前她再次死亡；旧具体对象同复使可识存瓘同存瑰。',source=old,relation='adds')
E=ev('tang_delegates_sword_south_offices','朝廷许孟知祥差罢剑南节度使、刺史以下官后奏闻，不再自行除人',15,'凡剑南自节度使、','朝廷更不除人；',[('上','授地方任免范围者'),('知祥','获差罢奏闻权的两川帅')],when='932年十月己酉朔本段',place='剑南、两川',note='此段比前刺史以下请表的权限更广，保留阶段，不把此前请表就说已获全部权；讫奏闻不可省成无须报告。')
claim('event',E,'description','旧明宗纪记允孟所请两川文武将吏权行墨制除补后奏。',15,'知祥所奏兩川部內文武將吏，乞許權行墨製除補訖奏，詔許之。','旧概范围与主节度刺史以下详法各载，五大将正节钺旧续有处分尚未同日已授，留后主续年。',source=old,relation='corroborates')
E=ev('tang_refuses_troop_families_stops_recall','朝廷仍不遣戍兵家属入川，但亦不再征还其兵',15,'唯不遣戍兵妻子，',None,[('上','拒送家属且不再征兵者'),('知祥','前请家属的川帅')],when='932年十月己酉朔本段；持续状态起止未独载',place='两川及东兵原籍',note='兵妻子为家属，不造未名妻子；拒送不等朝廷仍在征兵，两个处置分别留。')
claim('event',E,'description','旧明宗纪记孟请发遣兵士家属入川，诏报不允。',15,'知祥上表乞發遣兵士家屬入川，詔報不允。','当前答复附此前请求，不重复造新请求事件；兵不复征部分仍仅据主，旧此句不载。',source=old,relation='corroborates')
E=ev('congrong_poetry_circle','史述李从荣爱诗，与高辇等幕府士唱和，自矜并苛待不如意诗作',16,'秦王从荣喜为诗，','面毁袭抵弃。',[('从荣','秦王、幕府诗会主人'),('高辇','参与诗歌唱和的幕府士')],year=None,when='从荣秦王幕府素行概述；各次年份未独载',place='秦王幕府',note='浮华自矜为史述评价，不下现代诊断；面毁袭抵疑句保留，不猜已杀诗作者或具体处罚。')
claim('event',E,'description','旧秦王传记从荣与高辇等唱和，有诗千余号紫府集。',16,'從榮為詩，與從事高輦等更相唱和，自謂章句獨步於一時，有詩千餘首，號曰《紫府集》。','自谓独步是本人自称，千余为概数，不据此生成千首未见诗；作品集名补不另造具体某日完稿。',source=poetry,relation='adds')
ev('emperor_advises_congrong_study','十月壬子李从荣入谒，李嗣源劝听儒生讲经义，不要效庄宗以将家子作诗徒受笑',16,'壬子，从荣入谒，',None,[('从荣','入谒受训者'),('上','以经义及庄宗为例劝子者')],when='932年十月壬子',place='后唐朝廷',note='庄宗诗例为帝回顾立场，不在932复建已死庄宗赋诗；吾不知书为自言非现代文盲鉴定。')
ev('youzhou_reports_qidan_nalapo','十月丙辰幽州奏契丹驻屯捺剌泊',17,'丙辰，',None,[],when='932年十月丙辰奏闻；实际扎营起日未独载',place='捺剌泊',note='奏屯不是本句实际攻克幽州；新揆剌泊与主捺剌字名异未核，不强贴现代湖泊坐标。')
ev('li_jinquan_horse_gifts_refused','李金全屡献马被李嗣源拒，帝劝重视镇中治理',18,'前影义节度使李金全屡献马，','勿但以献马为事！”',[('李金全','前节度使、多次献马者'),('上','拒马并问治者')],year=None,when='屡献马概述；各次年月未独载',place='后唐朝廷',note='前影义军名疑字保留，未静改原字或建不存在影义军地理实体；只记前节度使，不把拒马当永不受进奉。')
claim('person',people['李金全'],'description','李金全为吐谷浑人。',18,'金全，吐谷浑人也。','主族属明确，未知父母和出生年不凭姓李猜；不混此前李金道等。')
E=ev('kangcheng_memorial_five_six','十月壬申康澄上疏论五不足惧、六深可畏，劝重人才生业廉耻及直言',19,'壬申，大理少卿康澄上疏曰：','愿陛下修而靡忒。”',[('康澄','大理少卿、上疏者'),('上','受疏君主')],when='932年十月壬申',place='后唐朝廷',note='殷晋灾异例是康论据，不当本年新发生殷商异象；五六按原条，旱灾虫害不足惧是其政治论述不是现代灾害科学结论。')
claim('event',E,'description','旧明宗纪同壬申详记康疏五不足惧、六深可畏。',19,'是知國家有不足懼者五，有深可畏者六。','该摘为条数，具体条目主逐字全引及旧长文可回查；无须将每个所列社会问题都建已发生独立事件。',source=old,relation='corroborates')
E=ev('emperor_rewards_kang_memorial','李嗣源以优诏奖康澄上疏',19,'优诏奖之。','优诏奖之。',[('上','发优诏者'),('康澄','上疏受奖者')],when='932年十月壬申上疏后；诏日未独载',place='后唐朝廷')
claim('event',E,'description','旧明宗纪亦记优诏奖康澄。',19,'優詔獎之。','其后澄言中病识者许之为史评，不等诏证明六项政治风险已全部发生。',source=old,relation='corroborates')
ev('congrong_conduct_in_government','史述李从荣参朝政后骄纵不法、性轻佻峻急',19,'秦王从荣为人鹰视，','多骄纵不法。',[('从荣','被史述参政与骄纵者')],year=None,when='秦王任军政后的素行概述；确年与各次行为未独载',place='后唐朝廷',note='鹰视为史容貌行为修辞，不做身体疾病或人格诊断；此为概述不重复建已有判六军任命。')
ev('an_controls_princes_retrospective','史书追述安重诲受帝专任，自幼亲狎的从荣从厚即使典兵仍畏其制',19,'初，安重诲为枢密使，','畏事之。',[('重诲','过去控制两皇子者'),('上','过去专任安者'),('从荣','过去亲狎但受制者'),('从厚','过去亲狎但受制者')],year=None,when='初，安重诲在世任枢密期间追叙；未独起年',place='后唐',note='安已931死，当前参与是过去，不创建932安复生。自襁褓为叙幼年关系，不据其年龄推生年。')
ev('congrong_slights_inner_officials','安重诲死后王淑妃、孟汉琼传帝命，范赵任枢密，从荣轻侮其人',19,'重诲死，','从荣皆轻侮之。',[('王淑妃','传帝命的王氏淑妃'),('孟汉琼','宣徽使、传帝命者'),('延光','被轻侮的枢密使'),('延寿','被轻侮的枢密使'),('从荣','轻侮者')],year=None,when='安重诲931卒之后概述；各次年月未载',place='后唐内廷及朝廷',note='王淑妃沿旧王德妃（李嗣源妃），旧932王氏淑妃称衔印证，未与前蜀徐淑妃或曹后合并；轻侮不是已诛四人，不造永久敌对边。')
claim('person',people['王德妃（李嗣源妃）'],'name','旧明宗纪932年亦称淑妃王氏。',19,'淑妃王氏曾祖父母已下為太子太保、太傅、太師、國夫人。','王氏在明宗同朝后宫且原德妃角色前后同人，保留既有key；不据祖追赠去造未名四代家属，更不把淑妃曹氏等混入。',source=apr,relation='adds')
ev('yongning_congrong_mutual_dislike','史述石敬瑭妻永宁公主与从荣异母，素相憎疾',19,'河阳节度使、','素相憎疾。',[('敬瑭','兼六军副使且为永宁之夫'),('永宁公主','与从荣异母的公主'),('从荣','被述与公主素相憎者')],year=None,when='素来关系概述；起止年未独载',place='后唐宗室',note='素相憎只是史述此次关系，不建永久仇敌；未独排行不猜长幼。')
relationship('永宁公主','敬瑭','妻子',19,'其妻永宁公主与从荣异母','永宁公主→石敬瑭妻子，石氏为旧婚家称法不是公主本姓，未猜个人名。')
relationship('上','永宁公主','父亲',19,'皇第三女石氏封永寧公主','明宗卷39正文皇第三女明载；旧928封只是身份补不在932重复封爵，未引用夹注五代会要异说。',source=princess)
claim('person',people['永宁公主（石敬瑭妻）'],'description','永宁公主与李从荣为同父异母手足，长幼本段未明。',19,'其妻永宁公主与从荣异母，素相憎疾。','父为李嗣源由旧明宗纪皇第三女补，异母直接主；未因第三女排名与第二子排名跨性别猜谁年长，不新造未名生母。')
ev('congrong_jealous_conghou','从荣因从厚声名更高而忌，从厚卑弱奉之，使嫌隙不外见',19,'从荣以从厚声名','故嫌隙不外见。',[('从荣','因弟声名而被述嫉妒者'),('从厚','以卑弱奉兄者')],year=None,when='兄弟素来相处概述；确年未载',place='后唐宗室',note='声名高低及心理归史叙，不测量声望；不外见不等二人完全没有分歧。')
ev('shi_seeks_post_avoid_congrong','石敬瑭不愿与从荣共事，常思外任以避之',19,'石敬瑭不欲','以避之。',[('敬瑭','思求外任者'),('从荣','被避共事者')],year=None,when='任六军副使后的持续意愿；各次年月未载',place='后唐朝廷',note='常思为意愿，不等本句已离京；河东正式任在后11月段。')
ev('fan_zhao_request_rotation_refused','范延光、赵延寿忧祸，屡辞机要请与旧臣轮任，帝不许',19,'范延光、赵延寿亦虑及祸，','上不许。',[('延光','屡请轮任辞机要者'),('延寿','同请轮任者'),('上','拒请者')],year=None,when='秦王参政后屡次奏请概述；各次年月未独载',place='后唐朝廷',note='忧祸是二人风险判断，未造当时已受杀；旧臣未名不猜轮值名单。')
ev('emperor_seeks_hedong_candidates','契丹欲入寇时帝命择河东帅，范赵荐石敬瑭或康义诚，石也愿行',19,'会契丹欲入寇，','上即命除之。',[('上','择帅并初命出镇者'),('延光','荐石康者'),('延寿','同荐者'),('敬瑭','受荐愿出镇者'),('康义诚','被荐候选者')],when='932年河东选帅议的前段；确月日未独载',place='后唐朝廷、拟河东',note='欲入寇不等本句已攻陷太原；初除诏后尚有留六军副使争议及再议，不提前后丁亥正式任全部官。')
ev('shi_requests_drop_deputy_duties','石敬瑭受初诏仍兼六军副使，复辞其职；帝令朱弘昭知山南东道、代康入阙',19,'既受诏，',None,[('敬瑭','再辞仍兼六军副使者'),('上','安排朱知山南及召康者'),('硃弘昭','宣徽使、暂知山南东道者'),('康义诚','被代而召入阙者')],when='932年河东选帅前段受诏后；确月日未独载',place='后唐朝廷、山南东道',note='知为暂理，不把此时等同12月正授朱节度使；前初命与后再议各阶段保留，未据复辞写辞已获准。')
E=ev('meng_hu_zhongwu_appointment','十一月辛巳三司使孟鹄出任忠武节度使',20,'十一月，辛巳，','以三司使孟秸为忠武节度使，',[('孟秸','三司使、出任忠武者')],when='932年十一月辛巳',place='忠武军',note='主孟秸同段后鹄、旧同日孟鵠识同已有孟鹄；不把秸当新姓名，底本保留。')
claim('event',E,'description','旧明宗纪同十一月辛巳记三司使左武卫大将军孟鹄任许州节度使。',20,'十一月辛巳，以三司使、左武衛大將軍孟鵠為許州節度使，','许州为忠武军治同任，鵠简体鹄；不是秸鹄两人两任。旧未载范私人引荐，此分析仍取主。',source=nov,relation='corroborates')
E=ev('fengyun_xuanhui_finance','十一月辛巳冯赟由忠武节度使任宣徽南院使、判三司',20,'以忠武节度使冯赟','判三司。',[('冯赟','调任宣徽南院、判三司者')],when='932年十一月辛巳',place='后唐朝廷',note='同日孟冯两职转任分，判三司不等本句改成所有财务制度。')
claim('event',E,'description','旧明宗纪同日记前许州节度使冯赟为宣徽使、判三司。',20,'以前許州節度使馮贇為宣徽使、判三司，','主南院详旧宣徽略，不把旧未记南就视为另任北院。',source=nov,relation='corroborates')
ev('meng_hu_fan_patronage_retrospective','史述孟鹄由刀笔吏因与范延光乡里厚善，数年间被引擢至节度，帝虽知速仍不能违',20,'鹄本刀笔吏，',None,[('孟秸','被述数年快速引擢者'),('延光','同乡厚善而引擢者'),('上','被述知速仍未阻者')],year=None,when='孟鹄此前数年升迁至本次任节度的追叙；各次未独年份',place='后唐',note='归因是主叙述，不猜每次贿赂金额或立永久朋党边；数年不推起始具体年。')
reviews={11:'徐知诰沿李昪改名主体，周围二十里为城周不是面积或增加长度；主承八月未独日，不借别书泛金陵布局作同一扩城。',12:'契丹掠粮及良乡潞县先后追叙yearnull，三河至是承当前932、九月庚辰奏城明确，不把三城都定当年或奏日作精确竣工。主旧阎沟新盐沟及三河方位层次留，不画现代边界。旧运河二百里不借覆旧主六月运河数字，旧夹注辽史和后936不提前新增。',13:'九月壬午马武安兼侍中同旧湖南军称，同前朗州迎和长沙袭位不同阶段。',14:'仁赞沿孟昶及既有别名、父亲关系；摄司马及兼两川牙内军职主明确，新概司马不删摄，第三子补，不提前继位。',15:'十月己酉朔复遣使，主存瓘与已建存瑰、新瓌旧瑰同人同任务疑字保留；旧祭赠绢三千与玉带本次使命补。朝廷任免许可比前请求范围扩，讫奏闻不能省；五将正授旧续处置非当前已授。拒送家属与不再征兵同时留，不重复建前请求或公主死亡。',16:'秦幕唱和素行yearnull，旧高辇及紫府集同叙补，千余概数不造未见作品；主面毁袭抵疑句不猜惩罚。十月壬子帝劝经义，以庄宗作诗为回顾例不是932庄宗复生。',17:'十月丙辰幽州奏捺剌泊屯，不等当日已攻城；新揆剌泊异名未核不强同现代地点。',18:'李金全主吐谷浑明，屡献马yearnull；前影义疑军名保原不造影义军，未据拒马说永拒所有贡物。',19:'十月壬申康五不足惧六深畏疏与奖分，灾异殷晋古例不是本年事，政治论据不当科学结论。秦骄政、安在世制诸子、安死后传命与轻侮、公主与秦异母、兄弟名声妒及弟奉、石求外、范赵屡辞、河东初荐初命、石再辞朱暂知康入阙分，素行追叙yearnull不把安复生。王淑沿已有王德，旧王氏淑衔补不与曹徐混；永宁石氏是婚家不是本姓，旧皇第三女补父，长幼母名不猜。初除、再辞与后11月再议终任分；朱知暂不当12月正节。心理风险归各说者，不建永恒仇盟关系。',20:'十一月辛巳孟出忠武、冯转宣徽南判三司分，主秸后鹄及旧鵠同日同三司出许州匹配孟鹄稳定key。旧许州是忠武治；刀笔吏同乡范引擢为数年追叙yearnull，不猜贿赂或升任始年。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=932,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v278-y0932-p021',next_volume=278,next_year=932,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷278连续932年第11—20段、原16—25行；金陵扩城、赵边堡、楚授任、孟子摄职、两川任免答、秦诗幕康疏及宫廷危疑、河东择帅初议、孟冯迁官。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,21)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
