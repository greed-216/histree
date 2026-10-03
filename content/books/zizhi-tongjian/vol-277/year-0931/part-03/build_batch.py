# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 931, paragraphs 21–30."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'52e45d2f','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
specs.append(('tongjian-277-931-february',YEAR/'part-01/sources/library/tongjian-277-931-february','91251854','司马光等'))

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-931-february','tongjian-277-931-may']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0931-p021-p030',
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
lines = (ROOT / 'resources/derived/tongjian/277.txt').read_text().splitlines()
for n in range(21, 31):
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
        citation = f'卷277·长兴二年（931）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0931_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'王妃':'王德妃（李嗣源妃）','王淑妃':'王德妃（李嗣源妃）','延禀':'王延禀','延钧':'王延钧','延政':'王延政','继升':'王继升','继雄':'王继雄','继伦':'王继伦','仁达':'王仁达','汉琼':'孟汉琼','镕':'王镕','重诲':'安重诲','廷隐':'赵廷隐','知祥':'孟知祥','延光':'范延光','延寿':'赵延寿'}
NEW_ALIASES={'王继升':['王繼升','王繼昇','王继昇'],'王继伦':['王繼倫'],'王仁达':['王仁達'],'王延政':[]}

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

def event(code, title, n, quote, actors, when=None, note='', year=931, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='931年'+('四月' if n<=25 else '五月')+'本段；确日未独载'
    key = 'event_zztj_277_0931_' + code
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
        edge = 'participation_zztj_277_0931_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0931_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive nine paragraphs, chronological facts and independently located supplements.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
apr='jiuwudaishi-042-931-april';may='jiuwudaishi-042-931-may';minbook='xinwudaishi-068-931-min-battle';hu='jiuwudaishi-069-menghu'
E=ev('wang_promoted_shufei','王德妃进位淑妃',21,'夏，四月，',None,[('王妃','进位淑妃者')],when='931年四月辛卯',place='后唐宫廷')
claim('event',E,'description','旧明宗纪同辛卯记德妃王氏进位淑妃。',21,'製德妃王氏進位淑妃。','王德妃、王淑妃同一人，沿既有主体；不混曹皇后。',source=apr,relation='corroborates')
ev('yanbin_leaves_jisheng_jianzhou','王延禀闻王延钧有疾，以次子王继升知建州留后',22,'闽奉国节度使','知建州留后，',[('延禀','闻疾、置建州留后者'),('延钧','被闻有疾的闽王'),('继升','次子、知建州留后者')],place='建州',note='闻疾是起兵背景，不外推病名及具体起病日；知留后不等节度正式实授。')
E=ev('yanbin_jixiong_attack_fuzhou','王延禀率王继雄水军袭福州，分攻西门与东门',22,'帅建州刺史','继雄攻东门；',[('延禀','率军攻福州西门者'),('继雄','建州刺史、率水军攻东门者')],when='931年四月癸卯攻城；出兵确日未载',place='福州西门、东门')
claim('event',E,'description','新闽世家称王延禀攻西门，子王继雄转海攻南门；主书作东门。',22,'長興二年，延稟率兵擊鏻，攻其西門，使其子繼雄轉海攻其南門，','南门、东门冲突并存，不静改引文、不据此绘制确定攻城路线。鏻沿王延钧。',source=minbook,relation='conflicts')
ev('yanjun_sends_renda_defense','王延钧遣楼船指挥使王仁达率水军拒敌',22,'延钧遣楼船','将水军拒之。',[('延钧','派遣水军者'),('仁达','楼船指挥使、率水军拒敌者')],place='福州')
E=ev('renda_feigns_surrender','王仁达伏甲于舟，立白帜假意请降',22,'仁达伏甲舟中，','伪立白帜请降，',[('仁达','设伏假降者'),('继雄','受假降欺骗者')],place='福州舟中',note='伪请降不是实际投降；白帜用途依本句，不推广为全时代固定旗制。')
claim('event',E,'description','新闽世家亦记王仁达伏甲舟中、立白帜请降。',22,'仁達伏甲舟中，偽立白幟請降，','两书同一设伏动作补证，不另立重复事件。',source=minbook,relation='corroborates')
ev('jixiong_boards_renda_ship','王继雄屏退左右，登王仁达舟慰抚',22,'继雄喜，','登仁达舟慰抚之；',[('继雄','信假降、屏左右登舟者'),('仁达','受登舟慰抚的设伏者')],place='福州舟中')
E=ev('renda_kills_jixiong','王仁达斩王继雄，枭首于福州西门',22,'仁达斩继雄，','枭首于西门。',[('仁达','斩首示首者'),('继雄','被斩杀示首者')],place='福州西门')
claim('event',E,'description','新闽世家称王继雄登舟后伏兵刺杀，枭首西门。',22,'繼雄信之，登舟，伏兵發，刺殺之，梟其首西門，','斩与刺杀措辞各存，事件主体及示首地点相合；不再造第二次死亡。',source=minbook,relation='corroborates')
ev('yanbin_mourns_army_routed','王延禀纵火攻城时见王继雄首，恸哭；王仁达纵兵击溃其众',22,'延禀方纵火','众溃，',[('延禀','攻城、见首恸哭的败军首领'),('仁达','乘势击溃敌众者'),('继雄','其首被展示者')],place='福州西门',note='哭与败为主叙相接，不等哭这一因素独自决定整个战局。')
ev('yanbin_carried_away','王延禀左右以斛舁之逃走',22,'左右以斛','而走，',[('延禀','被左右用斛抬走的败将')],place='福州',note='左右未具名不造人物；斛按原器名保留，不改为棺或自行核算容积。')
E=ev('yanbin_captured','王延禀被追擒',22,'甲辰，','追擒之。',[('延禀','逃走后被追擒者')],when='931年四月甲辰',place='福州附近',note='未独名追擒将，不将王仁达一定设为执行抓捕者；俘与五月处死分。')
claim('event',E,'description','新闽世家亦记王延禀被擒。',22,'其兵見之皆潰去，延稟見執。','新兵见首溃与主延禀见首后兵溃叙述侧重点有差；对应败后俘，不替换主甲辰日期。',source=minbook,relation='corroborates')
ev('yanjun_taunts_captive','王延钧以果烦老史再下来讥王延禀，王延禀惭不能对',22,'延钧见之曰：','惭不能对。',[('延钧','见俘后讥语者'),('延禀','受讥不能对者')],place='福州',note='直接引语按主书原字；老史与新老兄字差保留，不判两人为实际兄弟关系。')
ev('yanjun_imprisons_sends_envoy','王延钧囚王延禀于别室，遣使往建州招抚其党',22,'延钧囚于别室，','招抚其党；',[('延钧','囚俘并遣使招抚者'),('延禀','被囚、其党受招抚对象')],place='福州、建州',note='招抚使未名，不建立匿名人物；派使不等招抚成功。')
E=ev('jianzhou_party_kills_envoy_flees','王延禀党众杀招抚使，奉王继升与其弟王继伦奔吴越',22,'其党杀使者，','奔吴越。',[('延禀','其党杀使逃离者'),('继升','被奉奔吴越的建州留后'),('继伦','与兄被奉奔吴越者')],place='建州至吴越',note='奉为拥护伴行，非已拥立吴越王；不补未名使者和党众名单。')
claim('event',E,'description','新闽世家记王延禀子继昇守建州，闻败奔钱塘。',22,'延稟子繼昇守建州，聞敗，奔于錢塘。','继昇与主继升系同役同留守同逃者；钱塘补吴越目的地。新未提继伦不据此删除主记同逃。',source=minbook,relation='adds')
relationship('延禀','继升','父亲',22,'以次子继升知建州留后，','父亲方向为王延禀→王继升；次子仅保留此原文，不据此猜王继雄为长子。')
relationship('延禀','继雄','父亲',22,'使其子繼雄轉海攻其南門，','新直接其子补父亲方向，不依据一起出兵就猜父子；不加长子身份。',source=minbook)
relationship('继升','继伦','兄长',22,'奉继升及弟继伦奔吴越。','哥哥方向为王继升→王继伦；未直接记继伦生父，不从兄弟推造父亲边。')
relationship('仁达','延钧','从子',22,'仁达，延钧从子也。','王仁达是王延钧的从子，沿史书亲属词；未记生父和具体世系，不转换为确定侄子、生父或伯叔长幼。')
E=ev('zhaoyanshou_shumi','赵延寿由宣徽北院使任枢密使',23,'以宣徽北院使',None,[('延寿','由宣徽北院使转任枢密使者')],place='后唐')
claim('event',E,'description','旧明宗纪甲辰记赵延寿任枢密使，兼检校太傅、行礼部尚书。',23,'甲辰，以宣徽北院使、左衛上將軍趙延壽為檢校太傅、行禮部尚書，充樞密使。','旧纪补甲辰及兼衔；主本段未独日，日期以旧出处标示不伪装主原载。',source=apr,relation='adds')
E=ev('shi_six_armies_deputy','天雄节度使石敬瑭兼六军诸卫副使',24,'己酉，',None,[('石敬瑭','天雄节度使同平章事、兼六军诸卫副使者')],when='931年四月己酉',place='后唐')
claim('event',E,'description','旧明宗纪同己酉记石敬瑭兼六军诸卫副使。',24,'己酉，天雄軍節度使石敬瑭兼六軍諸衛副使。','同人同日同职补证，不误设六军所有兵力已交给个人。',source=apr,relation='corroborates')
E=ev('zhu_hongzhao_xuanhui_south','后唐以朱弘昭为宣徽南院使',25,'辛亥，',None,[('朱弘昭','受任宣徽南院使者')],when='931年四月辛亥',place='后唐',note='原硃弘照沿朱弘昭；同人异字保留，不再建弘照主体。')
claim('event',E,'description','旧明宗纪同辛亥记前凤翔节度使朱宏昭任左武卫上将军、宣徽南院使。',25,'辛亥，以前鳳翔節度使朱宏昭為左武衛上將軍，充宣徽南院使。','宏昭、弘照、弘昭由前凤翔身份及同日同任匹配；兼左武卫上将军补，不修改原字。',source=apr,relation='adds')
ev('yanbin_executed_restored_name','王延钧在市斩王延禀，并恢复其原姓名周彦琛',26,'五月，','曰周彦琛，',[('延钧','下令斩并复名者'),('延禀','被斩、恢复周彦琛姓名者')],when='931年五月；确日未载',place='闽',note='俘在四月甲辰、斩在五月，不按新遂杀连叙将死亡硬排四月；复姓名不另造周彦琛人物。')
claim('person',people['王延禀'],'name','王延禀原姓名为周彦琛，王延钧处死后复其姓名。',26,'复其姓名曰周彦琛，','当前沿王延禀稳定key与既有名称，以事实记录原姓名；不批量改写旧人物引用。')
ev('yanjun_sends_yanzheng_jianzhou','王延钧遣其弟、都教练使王延政往建州抚慰吏民',26,'遣其弟',None,[('延钧','派遣其弟抚慰者'),('延政','都教练使、赴建州抚慰者')],when='931年五月；确日未载',place='建州',note='遣抚是派令，本句未述完成抚慰结果，不能当建州民已服。')
relationship('延钧','延政','兄长',26,'遣其弟都教练使延政如建州抚慰吏民。','王延钧→王延政兄长，年龄顺序由其弟直接支持，不建对称兄弟含混边。')
E=ev('abolishes_muqian_tax','后唐罢田亩所征麹钱',27,'丁卯，','罢亩税麹钱，',[],when='931年五月丁卯',place='后唐',note='麹钱为田亩附征的酒曲税钱，罢的是这项税，不是所有田税，不把城中私造禁令当取消。')
claim('event',E,'description','旧明宗纪同丁卯诏放田亩所征曲钱。',27,'應田畝上所征曲錢並放，','旧诏明所征曲钱解除，麹曲繁异字保留，未扩为全部农业赋税。',source=may,relation='corroborates')
E=ev('official_qu_discount','后唐城中官造麹减至旧价一半',27,'城中官造麹','减旧半价，',[],when='931年五月丁卯',place='后唐城郭',note='减旧半价即减半；官造售曲与乡村自造分，不当统一放开城市私造。')
claim('event',E,'description','旧诏称城郭依旧禁私曲，官造曲减旧价之半货卖。',27,'諸州府城郭內依舊禁曲，其曲官中自造，減舊價之半貨賣。','禁私造和官供并行，故依旧禁曲不误为全面禁止喝酒；补城市仍禁私造。',source=may,relation='adds')
E=ev('villages_make_qu','后唐允许乡村百姓自行造麹，主书称民甚便之',27,'乡村听百姓',None,[],when='931年五月丁卯',place='后唐乡村',note='民甚便之为主书评价，不是统计民意；允许对象为乡村。')
claim('event',E,'description','旧诏允许乡村人户私造酒曲，并称时甚便之。',27,'鄉村人戶一任私造。」時甚便之。','两书政令及便民评价对应，不把评价当精确财政或民调数字。',source=may,relation='corroborates')
E=ev('menghanqiong_neishi_xuanhui','孟汉琼知内侍省事，充宣徽北院使',28,'己卯，','充宣徽北院使。',[('汉琼','知内侍省事、充宣徽北院使者')],when='931年五月己卯',place='后唐')
claim('event',E,'description','旧纪同己卯记武德使孟汉琼任右卫大将军、知内侍省、宣徽北院使。',28,'己卯，以武德使孟漢瓊為右衛大將軍、知內侍省，充宣徽北院使。','同任补前衔与兼衔，不混孟鹄或孟知祥。',source=may,relation='adds')
person('镕',28,'孟汉琼原主人赵王',span(28,'汉琼，本','奴也。'))
claim('person',people['孟汉琼'],'description','孟汉琼原为赵王王镕奴。',28,'汉琼，本赵王镕奴也。','本为身份追叙，未独纪年，不编造入奴或释放的具体年；不做永久主奴关系边。')
ev('fan_zhao_avoid_deciding','范延光、赵延寿因警惕安重诲获罪前例，于政事不敢可否',28,'时范延光、','不敢可否；',[('延光','枢密使、谨慎不敢裁决者'),('延寿','枢密使、谨慎不敢裁决者'),('重诲','被引以前例者')],place='后唐',note='刚愎得罪是主书的归因叙述，不当法院判决；原重悔据同一罢枢背景识安重诲，留原字，不建安重悔人物。')
ev('meng_wang_court_power','孟汉琼与王淑妃居中用事，主书称人皆惮之',28,'独汉琼','人皆惮之。',[('汉琼','居中用事者'),('王淑妃','居中用事者')],place='后唐宫廷',note='主述权势与畏惧，不是正式任王枢密使，不捏造人人结党或永久敌对边。')
ev('an_limits_palace_requests','此前安重诲对宫中超常索取执奏，主书称非分之求几绝',28,'先是，','非分之求殆绝。',[('重诲','此前对宫中超常索取执奏者')],year=None,when='追叙安重诲掌枢务时；具体年未载',place='后唐宫廷',note='先是无独年，year为空；未硬编926或931发生，几绝是史述成效不是金额。')
ev('meng_bypasses_treasury_procedure','孟汉琼径以中宫命取府库物，不经枢密院、三司，未有文书',28,'至是，',None,[('汉琼','以中宫命取府库物者')],place='后唐宫廷、府库',note='原亦无语文书保留，展示仅概括未有文书，不自行改成特定口谕或制度；不可胜纪是史述程度，不补金额或具体次。')
E=ev('menghu_sansi','相州刺史孟鹄任左骁卫大将军、三司使',29,'辛巳，',None,[('孟鹄','相州刺史、转左骁卫大将军三司使者')],when='931年五月辛巳',place='后唐')
claim('event',E,'description','旧明宗纪同辛巳记前相州刺史孟鹄任左骁卫大将军、三司使。',29,'辛巳，以前相州刺史孟鵠為左驍衛大將軍，充三司使。','前衔、时间与主同任；三司既有，不误当本日首次设三司。',source=may,relation='corroborates')
claim('person',people['孟鹄'],'description','旧孟鹄传记孟鹄为魏州人，范延光再迁枢密时征为三司使。',29,'孟鵠，魏州人。','补籍贯；传记后述期年发疾和求外任未提前录入当前五月。',source=hu,relation='adds')
claim('event',E,'description','旧孟鹄传亦记范延光再迁枢密时征孟鹄为三司使。',29,'會範延光再遷樞密，乃征鵠為三司使。','传记相对时序补同一授职，不倒推出另一个确日；不重复录早年赋役任职。',source=hu,relation='corroborates')
ev('zhaotingyin_arrives_lizhou','昭武留后赵廷隐自成都赴利州',30,'昭武留后','逾月，',[('廷隐','自成都赴利州的昭武留后')],place='成都至利州',note='赴后逾月为相对时距，未独赴日期，不硬换算成四月某日；前二月撤军与当前再赴是不同动作。')
ev('zhaotingyin_requests_campaign','赵廷隐赴利州逾月后请兵进取兴元、秦州、凤州',30,'请兵','及秦、凤；',[('廷隐','请求增兵进攻者'),('知祥','受请者')],place='利州，拟攻兴元、秦州、凤州',note='请进取不是已经进取成功，不录成三地占领或边界改变。')
ev('meng_refuses_campaign','孟知祥以兵疲民困，不许赵廷隐进取请求',30,'孟知祥',None,[('知祥','以兵疲民困拒绝进取者'),('廷隐','请兵未获允者')],place='成都、利州',note='以兵疲民困是孟拒绝所述理由，不量化士卒民户损耗。')
reviews={21:'王德妃进淑妃沿既有主体，旧同日补证，非曹后。',22:'王继升次子留守、延禀继雄袭分攻、仁达假降设伏、继雄登舟被杀示首、延禀败走追擒囚、招抚使被杀及二子奔吴越逐动分。新南门主东门冲突保留；捕在甲辰、死在五月，未把新遂杀连叙硬塞四月。继升继昇同人；仁达从子按原亲属词，不补未名生父或伯叔长幼。延禀父继雄新直接其子补、父继升主次子补；只继升兄继伦，不猜继雄兄次。',23:'赵延寿宣徽转枢密，旧甲辰兼衔补，主无独日不伪装主明载。',24:'石兼六军副使同己酉旧补，非全军指挥权已归。',25:'硃弘照、朱宏昭沿既有朱弘昭，前凤翔同日同任辨；不拆主体。',26:'五月斩延禀复姓名周彦琛沿旧主体事实引用，不另造人；派延政抚慰不等已完成，兄长方向由其弟直接支持。',27:'丁卯罢麹钱不是全田税；城官曲减价与乡自造分。旧仍禁城私曲，不误作全禁酒。便民为史评，不是数量测量。',28:'孟知内侍宣徽同旧，原赵王奴为无年追叙身份，不永久边；重悔据枢务前例识安重诲留原字。范赵不敢裁政为史述前例，孟王用事非王正式任枢。先是安限制宫索无年；至是府库取物无流程文书，疑语留原，不造金额。',29:'孟鹄不混孟汉琼孟知祥；旧同任、传籍贯及征三司补，传后期年疾求外任未提前。',30:'赵自成都赴利、逾月请兵、孟拒分；不从相对逾月硬算赴日，不把请攻三地当已占或地图改界。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,31):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=931,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(21,31)],next_paragraph='zztj-v277-y0931-p031',next_volume=277,next_year=931,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续931年第21—30段、原83—92行；王妃进位、闽建州攻福州败乱及处置、官职迁转、酒曲政令、内廷财用、三司孟鹄与赵廷隐请兵未许。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,31)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
