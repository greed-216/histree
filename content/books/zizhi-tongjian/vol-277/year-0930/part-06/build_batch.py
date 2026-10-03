# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 930, paragraphs 46–48."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 56))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'696f1bdc','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
specs.extend([
 ('tongjian-277-930-autumn-winter',YEAR/'part-04/sources/library/tongjian-277-930-autumn-winter','73f70bd8','司马光等'),
 ('xinwudaishi-064-meng-campaign',YEAR/'part-04/sources/library/xinwudaishi-064-meng-campaign','73f70bd8','欧阳修'),
])

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-930-autumn-winter','tongjian-277-930-jianmen']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0930-p046-p048',
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
for n in range(46, 49):
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
        citation = f'卷277·长兴元年（930）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0930_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'知祥':'孟知祥','璋':'董璋','殷':'马殷','弘贽':'王弘贽','冯晖':'冯晖（后唐泸州刺史）','廷隐':'赵廷隐','李筠':'李筠（前蜀永平节度使）','福诚':'庞福诚','锽':'谢锽','偓':'朱偓','帝':'李嗣源'}
NEW_ALIASES={'张环':['張環'],'朱偓':['硃偓'],'黄损':['黃損'],'王弘贽':['王弘贄','王宏贽','王宏贄'],'冯晖（后唐泸州刺史）':['馮暉（後唐瀘州刺史）'],'齐彦温':['齊彥溫'],'李筠（前蜀永平节度使）':[],'庞福诚':['龐福誠'],'谢锽':['謝鍠'],'潘福超':[],'沙延祚':[],'杨汉宾':['楊漢賓'],'崔善':[],'王晖（前蜀陵州刺史）':['王暉（前蜀陵州刺史）']}
ALIASES['王晖']='王晖（前蜀陵州刺史）'

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

def event(code, title, n, quote, actors, when=None, note='', year=930, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='930年十一月本段；确日未独载'
    key = 'event_zztj_277_0930_' + code
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
        edge = 'participation_zztj_277_0930_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0930_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
nov='jiuwudaishi-041-930-november';maold='jiuwudaishi-133-mayin-death';manew='xinwudaishi-066-mayin-death';machron='xinwudaishi-074-ma-chronology';feng='xinwudaishi-049-fenghui';wang='xinwudaishi-033-wangsitong-campaign';meng='xinwudaishi-064-meng-campaign'
E=ev('zhangwu_arrives_yuzhou_zhanghuan_surrenders','张武至渝州，刺史张环降之',46,'十一月，戊辰，','张环降之，',[('张武','率水军至渝州者'),('张环','渝州刺史、投降者')],when='930年十一月戊辰',place='渝州',note='降之承张武；不造张环与张武亲属关系。')
claim('event',E,'description','新孟传记张武已取渝州。',46,'張武已取渝州，','同张武行动补证，不把新随后武病卒同定戊辰。',source=meng,relation='corroborates')
E=ev('zhangwu_takes_luzhou','张武取泸州',46,'遂取泸州','遂取泸州，',[('张武','取泸州者')],place='泸州',note='遂承渝州降后，未独日不强同戊辰；与后唐泸州刺史冯晖的名义职并列，不据此推冯在城中被擒。')
E=ev('zhuwo_sent_qian_fu','张武遣先锋朱偓分兵趣黔、涪',46,'遣先锋',None,[('张武','派分兵者'),('偓','先锋、赴黔涪者')],place='黔、涪',note='硃/朱繁异用规范朱，趣是方向，实际弃黔取涪后段另录。')
E=ev('mayin_dies','楚王马殷卒',47,'己巳，','楚王殷卒，',[('殷','去世的楚王')],when='930年十一月己巳',place='楚',note='与此前朝廷疑死分；事件记主纪日，不由旧传931死亡覆盖。')
claim('event',E,'time_original','新楚世家记长兴元年马殷卒，年七十九。',47,'長興元年，殷卒，年七十九，','支持930，年龄原载不倒算精确生辰；谥葬后续主线未提前录。',source=manew,relation='corroborates')
claim('event',E,'time_original','旧马传记长兴二年十一月十日薨，年七十八，与主新年及年龄不同。',47,'長興二年十一月十日，薨於位，時年七十有八。','旧931与主930异说并列；不静改旧引或马主体字段。',source=maold,relation='conflicts')
claim('event',E,'time_original','新五代史年谱考证认为旧马传长兴二年与七十八岁说有误，取长兴元年。',47,'惟舊史書殷卒二年，及年七十八，希聲立不周歲卒為繆爾。','这是新史编者校考结论，所转述九国志等不冒作独立已核原书；保留不同说法可回查。',source=machron,relation='adds')
E=ev('mayin_orders_sibling_succession','马殷遗命诸子兄弟相继，置剑祠堂戒违命者',47,'遗命诸子，','违吾命者戮之！”',[('殷','立兄弟相继遗命者')],when='马殷临终遗命；具体立命日未载',place='楚、祠堂',note='置剑与违者戮为制度和威胁，非本日诸子已争位被杀；未名诸子不造人数及实名。')
E=ev('chu_generals_propose_border_guard','楚诸将议先遣兵守四境再发丧',47,'诸将议','然后发丧，',[('殷','其丧事引发边备讨论的故楚王')],place='楚四境',note='议是计划，不登记四境军队已经派出；将未具名不造。')
E=ev('huangsun_advises_notice_succession','黄损称丧君有君，无须戒备，建议向邻道告终称嗣',47,'兵部侍郎黄损',None,[('黄损','兵部侍郎、建议告终称嗣者')],place='楚、邻道',note='宜遣是建议，不能写成使已抵各邻国或四境无战争已验证。')
E=ev('shi_enters_sanguan','石敬瑭入散关',48,'石敬瑭入散关','石敬瑭入散关，',[('石敬瑭','率讨蜀主军入关者')],place='散关',note='未独干支，不把后来壬申克剑门即定本人同日到剑门。')
E=ev('tang_flanks_jianmen','王弘贽、冯晖、王思同、赵在礼引兵经人头山后绕至剑门南袭关',48,'阶州刺史','还袭剑门，',[('弘贽','阶州刺史、绕袭领兵者'),('冯晖','泸州刺史、绕袭领兵者'),('王思同','前锋马步都虞候、绕袭领兵者'),('赵在礼','步军都指挥使、绕袭领兵者')],place='人头山后、剑门南',note='主首王经贽后弘贽，旧阶州王宏贄同任同役，识别王弘贽保留疑字，不造王经另人。冯与902弘铎部下未有身份衔接，不自动同人。')
claim('person',people['冯晖（后唐泸州刺史）'],'description','新冯传称魏州人，效节队长入梁，梁亡赦后随明宗及平蜀，参与剑门绕袭。',48,'馮暉，魏州人也。為効節軍卒，以功遷隊長。','本批主晖魏州与新相合，旧泸州职对照；与既有902弘铎将冯晖缺身份衔接，分消歧主体待校，不凭同名合并，也不断言两人永无联系。',source=feng,relation='adds')
claim('event',E,'description','新冯传记剑门守兵不得入，冯从他道出其左击守兵。',48,'軍至劍門，劍門兵守，不得入，暉從佗道出其左，擊蜀守兵殆盡。','支持绕路作战，殆尽为新概称与主三千数并列；后班师和澶州任命不提前。',source=feng,relation='corroborates')
E=ev('tang_captures_jianmen_qiyanwen','唐军克剑门，杀东川兵三千，获都指挥使齐彦温而据守',48,'壬申，','据而守之。',[('弘贽','克关军领兵者'),('冯晖','克关军领兵者'),('王思同','克关军领兵者'),('赵在礼','克关军领兵者'),('齐彦温','被获东川都指挥使')],when='930年十一月壬申',place='剑门',note='三千为主所载死兵，旧三千余为战报数差；齐被获不等当日被杀。')
claim('event',E,'description','旧明宗纪辛巳收到军前奏：十三日王宏贽、冯晖绕袭，杀败守关兵三千余并收剑州。',48,'今月十三日，階州刺史王宏贄、瀘州刺史馮暉，自利州取山路出劍門關外倒下，殺敗董璋守關兵士三千餘人，收復劍州。','辛巳是奏闻、十三日是战报所载；主克剑门与旧合叙收剑州不抹成同动作日，三千与三千余差留，宏/弘同任同役校。',source=nov,relation='corroborates')
claim('event',E,'description','新孟传记唐师攻剑门，杀董璋守兵三千人而入关。',48,'唐師攻劍門，殺璋守兵三千人，遂入劍門。','同役概证，不等整段所有行军全部同一日。',source=meng,relation='corroborates')
E=ev('tang_takes_burns_jianzhou_retreat','王弘贽等破剑州，因大军不继而焚庐舍取粮，还保剑门',48,'甲戌，','还保剑门。',[('弘贽','破剑州而撤回领兵者'),('冯晖','同役军将')],when='930年十一月甲戌',place='剑州至剑门',note='大军不继为兵力补给衔接情况，不造石已阵亡；只录明示焚舍取粮，未知烧屋数。')
claim('event',E,'description','新王思同传概叙入剑门后军不继，战不胜而却。',48,'兵入劍門，而後軍不繼，思同與璋戰，不勝而却。','新概战败退与主焚剑州、夜袭退等过程有不同层次；不强认新概退只对应甲戌或确日。',source=wang,relation='adds')
E=ev('court_strips_meng_offices','后唐诏削孟知祥官爵',48,'乙亥，','官爵。',[('知祥','被削官爵者')],when='930年十一月乙亥',note='官爵处分不等两川实际已被平定。')
claim('event',E,'description','旧纪同乙亥制削孟知祥，称其与董璋同叛。',48,'乙亥，製西川節度使孟知祥削奪官爵，以其同董璋叛也。','同日处分及诏归因，不据此重写其所有既有官职主体字段。',source=nov,relation='corroborates')
E=ev('dong_appeals_chengdu','董璋遣使成都告急',48,'己卯，','告急。',[('璋','告急求援者'),('知祥','成都受告者')],when='930年十一月己卯',place='东川至成都')
E=ev('meng_fears_jianmen_loss','孟知祥闻剑门失守大惧，责董璋误己',48,'知祥闻剑门失守，','董公果误我！”',[('知祥','闻失关而惧者'),('璋','被责误计者')],note='情绪与归责是孟话，不独证董先辞援是唯一败因。')
E=ev('lizhao_sent_five_thousand_jianzhou','孟知祥遣李肇率五千赴援，戒倍道先据剑州',48,'庚辰，','北军无能为也。”',[('知祥','命援并戒行军者'),('李肇','牙内都指挥使、率五千援者')],when='930年十一月庚辰',place='成都至剑州',note='沿926孟收汝阴李肇主体；倍道是军令，不推实际每小时路程；北军无能为是预测。')
E=ev('zhaotingyin_ordered_jianzhou','孟知祥遣使遂州，令赵廷隐率万人会屯剑州',48,'又遣使诣遂州，','会屯剑州。',[('知祥','调兵令者'),('廷隐','受命率万人援剑州者')],place='遂州至剑州',note='万人主数同新分兵万；与原三万攻遂总兵不简单相加。')
claim('event',E,'description','新孟传亦记董告急，孟遣赵廷隐分兵万人以东。',48,'遣廷隱分兵萬人以東，','同调援，主点明从遂会剑，不另建新书同案。',source=meng,relation='corroborates')
E=ev('liyun_shu_sent_longzhou','孟知祥遣故蜀永平节度使李筠率四千趣龙州守要害',48,'又遣故蜀','守要害。',[('知祥','命分兵守龙州者'),('李筠','故蜀永平节度使、率四千者')],place='龙州',note='本李筠为前蜀将，897被诛的唐捧日都头已有主体不复用；亦不无证合960潞州李筠。')
E=ev('zhaotingyin_rallies_cold_soldiers','天寒士卒观望，赵廷隐泣谕力战以保妻子，众心振奋',48,'时天寒，','众心乃奋。',[('廷隐','劝士卒力战者')],place='剑州援军',note='妻子为妻和子女；将被人有为劝战危言，不建已发生家属全被掠。')
E=ev('dong_stations_mumazhai','董璋自阆州率两川兵屯木马寨',48,'董璋自阆州','屯木马寨。',[('璋','率两川兵驻木马寨者')],place='阆州至木马寨')
E=ev('pang_xie_prior_laisu_garrison','追叙庞福诚、谢锽此前屯来苏村',48,'先是，','屯来苏村，',[('福诚','太谷人、西川牙内指挥使、原屯来苏者'),('锽','昭信指挥使、原屯来苏者')],year=None,when='剑门失守前驻屯；起始年日未载',place='来苏村',note='先是不用930定最初驻年；太谷是庞籍贯，不当来苏现代位置。')
E=ev('pang_xie_rush_jianzhou','庞福诚、谢锽闻剑门失守，担忧二蜀，率千余人间道趣剑州',48,'闻剑门失守，相谓','趣剑州。',[('福诚','率部间道援剑州者'),('锽','率部间道援剑州者')],place='来苏村至剑州',note='千余为两人合部不各千余；二蜀势危为二人判断，非城全陷。')
E=ev('pang_xie_face_tang_on_north_hill','庞福诚、谢锽至剑州，遇官军万余自北山下，暮议夜战',48,'始至，','逮明则吾属无遗矣。”',[('福诚','兵少而谋夜战者'),('锽','共同谋夜战者')],place='剑州北山',note='万余为官军史载数，不等全役十万；天亮无遗为判断非已被全部歼灭。')
E=ev('pang_xie_night_raid_tang','庞福诚夜率数百登北山营后鼓噪，谢锽率余众短兵前击，官军惊遁退剑门',48,'福诚夜引兵','十馀日不出。',[('福诚','营后鼓噪夜袭者'),('锽','短兵前击者')],place='剑州北山至剑门',note='数百是分队，非合部精确人数；十余日是退后驻态不换算确止日，无确主将名不把每唐将都加此事件。')
E=ev('meng_assesses_tang_retreat','孟知祥闻唐军焚剑州取粮退守剑门，庆幸其未径攻梓州',48,'孟知祥闻之，','吾事济矣。”',[('知祥','评战局者'),('弘贽','被评军略的唐将')],place='剑州、剑门、梓州',note='直趣梓、董奔还、解遂围、两川震动皆孟设想路线，非已实发生；济是评价，不提前判整役胜负。')
E=ev('pan_sha_defeat_tang_longzhou','官军分道趣文州拟袭龙州，被潘福超、沙延祚击败',48,'官军分道','沙延祚所败。',[('潘福超','西川定远指挥使、击败官军者'),('沙延祚','太原人、义胜都头、击败官军者')],place='文州至龙州',note='拟袭与被败分在同战事，未具战地坐标及唐带队姓名，不造。')
E=ev('zhangwu_dies_yuzhou','张武卒于渝州',48,'甲申，','张武卒于渝州；',[('张武','卒于渝州的峡路主将')],when='930年十一月甲申',place='渝州')
claim('event',E,'description','新孟传记张武取渝州后病卒。',48,'張武已取渝州，武病卒，','病为新补死因、主仅卒，不另定具体疾病。',source=meng,relation='adds')
E=ev('yuan_replaces_zhangwu','孟知祥命袁彦超代领张武军',48,'知祥命袁彦超','代将其兵。',[('知祥','命代将者'),('袁彦超','由副代领军者'),('张武','死后军队交代的原主将')],place='渝州峡路军',note='主副转代将不擅补具体升任节度官。')
E=ev('yanghanbin_abandons_qiannan','朱偓将至涪州，武泰节度使杨汉宾弃黔南奔忠州',48,'硃偓将至涪州，','奔忠州；',[('偓','向涪推进者'),('杨汉宾','武泰节度使、弃黔南奔忠者')],place='黔南至忠州',note='主杨汉宾与旧杨汉章同职同弃城案可校异名，暂保留差，不把其合并已被诛朱汉宾。')
claim('event',E,'description','旧纪壬申记黔南节度使杨汉章弃城奔忠州，称为董璋所攻。',48,'壬申，黔南節度使楊漢章棄城奔忠州，為董璋所攻也。','主杨汉宾旧杨汉章姓名、主朱偓进军旧董攻叙法差并列；主本动作未独日，不以旧壬申把主提前同剑门克日。',source=nov,relation='conflicts')
E=ev('zhuwo_chases_fengdu_takes_fuzhou','朱偓追至丰都，还取涪州',48,'偓追至丰都，','还取涪州。',[('偓','追击并回取涪州者'),('杨汉宾','前句奔逃被追对象')],place='丰都、涪州',note='未言追获杨，不把追至当俘获；还不是归成都。')
E=ev('cuishan_acting_wutai','孟知祥以成都支使崔善权武泰留后',48,'知祥以成都','权武泰留后。',[('知祥','任留后者'),('崔善','成都支使、权武泰留后')],place='武泰',note='权为暂摄，未写为正式节度使或独立国主。')
E=ev('wanghui_sent_jianzhou_south','董璋遣前陵州刺史王晖率三千会李肇，分屯剑州南山',48,'董璋遣前陵州',None,[('璋','遣援将者'),('王晖','前陵州刺史、率三千者'),('李肇','会屯军将')],place='剑州南山',note='本王晖以前蜀陵州标识，非本段冯晖，也不合早年王晖叛云州异人；三千为此次部军不各将三千。')
reviews={46:'戊辰张至渝张环降；随后取泸遣朱先锋未独日，硃/朱规范显示。新已取渝佐核不提前张病卒。',47:'主930十一己巳卒，新楚93079岁支持，旧931十一十日78岁异并列，新年谱考证是编者观点非另原书实证。遗命兄弟相继剑戒非已刑诸子，诸将四境计划黄建议告终非使已经出发。',48:'剑门长段按全动作读完，跨两主快照。王经疑字与后弘旧宏同阶州同役校沿王弘贽，未改原引。冯本魏州与新、旧泸州同人；902弘铎同名无衔接不并，保留消歧待考。李筠新蜀将不复用897被诛唐人。李肇复用926汝阴主体。壬申克关甲戌破烧剑州分；旧辛巳奏十三日为奏与行为不同日，三千余差留。孟削爵乙亥、董告己卯、李援庚辰分。庞谢先屯起年null，夜前后夹击；孟假设梓州董回遂解非事实。潘沙败拟袭龙军；张死甲申新补病、袁代，朱追不等获杨，杨汉宾旧汉章及朱旧董攻叙差留。崔权留后王晖陵州消歧，三千仅其部。未提前马嗣东丹来及十二月后续。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(46,49):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=930,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(46,49)],next_paragraph='zztj-v277-y0930-p049',next_volume=277,next_year=930,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续第46—48段，原51—53行；张武峡路进军、马殷卒与遗命、唐蜀剑门进退及两川反攻。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(46,49)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
