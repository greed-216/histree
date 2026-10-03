# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 931, paragraphs 41–50."""
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
 specs.append((directory.name,directory,'b9e535ed','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
specs += [('tongjian-277-931-october',YEAR/'part-04/sources/library/tongjian-277-931-october','077b3114','司马光等'),('xinwudaishi-061-931-song-post',YEAR/'part-02/sources/library/xinwudaishi-061-931-song-post','1066c58f','欧阳修'),('xinwudaishi-068-baohuang',YEAR/'part-04/sources/library/xinwudaishi-068-baohuang','077b3114','欧阳修')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-931-october']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0931-p041-p050',
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
for n in range(41, 51):
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
    ck = f'claim_zztj_277_0931_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'汉主':'刘岩','李进':'李进（南汉交州将）','知祥':'孟知祥','璋':'董璋','仁罕':'李仁罕','知诰':'李昪','景通':'李璟','崇':'张崇','武穆王':'马殷','梁太祖':'朱温','希声':'马希声','廷隐':'赵廷隐','肇':'李肇','延钧':'王延钧','继鹏':'王继鹏','廷艺':'杨廷艺','进':'李进（南汉交州将）','宝':'程宝'}
NEW_ALIASES={'杨廷艺':['楊廷藝'],'程宝':['程寶'],'潘起':[],'王继鹏':['王繼鵬']}

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
    if when is None:when='931年'+('十一月' if n<=44 else '十二月' if n<=49 else '全年纪事，月未独载')+'；确日未独载'
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
# Consecutive ten paragraphs with independently located supplements.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
nov='jiuwudaishi-042-931-november';dec='jiuwudaishi-042-931-december';meng='xinwudaishi-064-meng-dong-dissent';ma='xinwudaishi-066-ma-funeral';jiao='xinwudaishi-065-jiaozhou-revolt';wu='xinwudaishi-061-931-song-post';temple='xinwudaishi-068-baohuang'
E=ev('november_solar_eclipse','十一月甲申朔日食',41,'十一月，',None,[],when='931年十一月甲申朔',place='观测地未载',note='史载日食，不凭古日期自行推算公历时分或全食范围。')
claim('event',E,'description','旧明宗纪同十一月甲申朔记日食。',41,'十一月甲申朔，日有蝕之。','两纪同日；无现代历法换算。',source=nov,relation='corroborates')
ev('suyuan_arrives_chengdu','苏愿抵成都，孟知祥得知甥侄在朝廷者均无恙',42,'癸巳，','在朝廷者皆无恙，',[('苏愿','奉遣后抵成都的进奏官'),('知祥','获知朝中甥侄安全者')],when='931年十一月癸巳',place='成都',note='甥妷沿原字，泛称未具名不推每位甥侄名单；闰五月遣与十一月到分别。')
E=ev('meng_invites_dong_apology','孟知祥遣使告董璋，欲共同上表谢罪',42,'遣使告董璋，','俱上表谢罪。',[('知祥','提议共同上表者'),('璋','受邀共同上表者')],when='931年十一月癸巳苏愿抵后',place='成都至东川',note='欲谢为提议，非两人已经上表或已被赦免。')
claim('event',E,'description','新孟世家亦记知祥闻安重诲死及唐厚待其家属，邀董璋同谢罪。',42,'知祥聞重誨誅死，而唐厚待其家屬，乃邀璋欲同謝罪，','补同邀谢背景，后932三遣李昊及交战未提前本批；安重诲死在前批，此不重造死亡。',source=meng,relation='corroborates')
E=ev('dong_refuses_meng_apology','董璋以自己家族被诛而拒谢，疑谕旨只让苏愿知，孟董再成怨敌',42,'璋怒曰：',None,[('璋','以家族遇害拒谢并质疑谕旨者'),('知祥','被拒并再交恶者'),('苏愿','被董称知道诏书者'),('刘澄','被董称不得预闻者')],place='东川、西川',note='璋已族灭、刘澄安得预闻是董说辞；朝廷是否刻意只给苏书未独证，不录客观阴谋。再怨为史述结果，非新932两川已开战。')
claim('event',E,'description','新孟世家同记董称孟家属皆存、己子孙被杀，何须谢。',42,'璋曰：「孟公家屬皆存，而我子孫獨見殺，我何謝為！」','新子孙与主族灭程度叙法分别归于董言；董后来有光嗣在蜀，不把族灭理解为全时全处所有董族已死。',source=meng,relation='corroborates')
ev('lirenhan_returns_chengdu','李仁罕自夔州引军还成都',43,'乙未，',None,[('仁罕','自夔州引军返者')],when='931年十一月乙未',place='夔州至成都',note='还成都与前陷夔州两动作分；未具返兵数不套前役全部三万。')
ev('xuzhigao_requests_jinling','徐知诰称辅政久，上表请归老金陵',44,'吴中书令','请归老金陵；',[('知诰','吴中书令、请归金陵者')],place='吴至金陵',note='归老为表述，后仍总录朝政，不当退出全部政治权力。')
E=ev('xuzhigao_jinling_posts','吴以徐知诰为镇海、宁国节度使，镇金陵，余官如故，总录朝政',44,'乃以知诰','如徐温故事。',[('知诰','镇金陵并继续总录朝政者'),('徐温','其旧辅政模式被援引者')],place='吴金陵',note='徐温作为被援引的已故先例，不录931仍在任；任命与十二月实际到金陵分。')
claim('event',E,'description','新吴世家大和三年记徐知诰为金陵尹。',44,'三年，以徐知誥為金陵尹，','三年承大和为931；新称金陵尹，主镇海宁国镇金陵官衔层次分别保留，不默认本条已废两镇任。',source=wu,relation='adds')
E=ev('jing_tong_wu_regency','徐景通任司徒、同平章事，知中外左右诸军事，留江都辅政',44,'以其子兵部尚书','留江都辅政；',[('知诰','其子接江都辅政的原辅政者'),('景通','兵部尚书参政事、转司徒同平章事辅政者')],place='吴江都',note='景通沿李璟，留江都不是此时已称帝，父金陵总录与子江都辅政并行。')
claim('event',E,'description','新吴世家同大和三年记景通为司徒。',44,'以其子景通為司徒，','同父子、同年官衔补，不将新后景迁当本次景通。',source=wu,relation='corroborates')
relationship('知诰','景通','父亲',44,'以其子兵部尚书、参政事景通为司徒、同平章事，','李昪→李璟父亲沿既有方向与key，父子当时徐姓名留原引文。')
E=ev('wanglingmou_youpuye','吴以内枢使王令谋为右仆射兼门下侍郎，同平章事兼内枢使，佐景通',44,'以内枢使、','以佐景通。',[('王令谋','右仆射兼门下侍郎、仍平章内枢佐政者'),('景通','受王令谋佐政者')],place='吴江都',note='所取引句含宋齐丘与并同衔，按人拆同一任命组不重复把两人都赋中书门下。')
claim('event',E,'description','新吴世家同年作左仆射王令谋皆平章事，主此处作右仆射。',44,'及左僕射王令謀、右僕射宋齊丘皆平章事。','左/右差并存，不靠繁简转换改官名，也不推断他在全年一定多次改左右职。',source=wu,relation='conflicts')
E=ev('songqi_qiu_youpuye_regency','吴以宋齐丘为右仆射兼中书侍郎，同平章事兼内枢使，佐景通',44,'以宋齐丘','以佐景通。',[('宋齐丘','右仆射兼中书侍郎、平章内枢佐政者'),('景通','受宋齐丘佐政者')],place='吴江都',note='本次十一月平章佐政与三月致仕分别，不能把前本次致仕混为一直在任。')
claim('event',E,'description','新吴世家同年记右仆射宋齐丘皆平章事。',44,'及左僕射王令謀、右僕射宋齊丘皆平章事。','同年右仆射平章对照此次任命；前批三月致仕异说保留其上下文，不回改既有引用。',source=wu,relation='corroborates')
ev('zhangchong_qinghe_king','吴赐德胜节度使张崇清河王爵',44,'赐德胜', '清河王。',[('崇','德胜节度使、受清河王爵者')],place='吴庐州',note='爵清河王不当已取得清河地区军事辖地。')
ev('zhangchong_luzhou_repeated_bribery','史书追述张崇在庐州贪暴，屡入朝厚赂权要，常获还镇，患庐州二十余年',44,'崇在庐州',None,[('崇','被史书批评贪暴结赂的长期庐州主政者')],year=None,when='追叙张崇长期在庐州，具体起止年未载',place='吴庐州',note='二十余年是主概数，不反推从911开始；屡入朝未独日不生成多个猜年入朝，权要未名不猜受贿人名单。')
E=ev('opens_iron_casting','后唐准百姓自铸农器及杂铁器，并按田征农具钱',45,'十二月，',None,[],when='931年十二月甲寅朔',place='后唐',note='初听是当时政策开始，不当所有铁禁永远撤销。每二亩夏秋输三钱按原记，不无依据折算全年合计。')
claim('event',E,'description','旧明宗纪同十二月甲寅朔诏开铁禁，许自铸农器什器，夏秋每亩农器钱一钱五分。',45,'十二月甲寅朔，詔開鐵禁，許百姓自鑄農器、什器之屬，於夏秋田畝上，每畝輸農器錢一錢五分。','主二亩三钱与旧每亩一钱五分算数相合，单位分不改公制元；夏秋是否分别计额未独解释，不推每年总税。',source=dec,relation='corroborates')
E=ev('maxisheng_imitates_chicken','马希声闻朱温嗜食鸡而仿效，袭位后日杀五十鸡供膳，主称居丧无戚容',46,'武安、静江','居丧无戚容。',[('希声','仿效日食鸡的武安静江节度使'),('梁太祖','被援引饮食习惯的已故朱温')],year=None,when='追叙马希声袭位后习惯；始行具体年未独载',place='楚',note='闻慕为主叙；日五十是史载惯例数，非当前十二月单日独核消费；朱温已故仅被谈及。')
claim('event',E,'description','新楚世家亦记马希声慕梁太祖食鸡，日烹五十鸡供膳。',46,'希聲嘗聞梁太祖好食鷄，慕之，乃日烹五十鷄以供膳。','同一习惯补证，日数不是单次宴席人数，未另定发生年份。',source=ma,relation='corroborates')
E=ev('ma_yin_buried_hengyang','武穆王马殷葬于衡阳',46,'庚申，','葬武穆王于衡阳，',[('武穆王','被安葬的已故马殷'),('希声','处父丧的继任者')],when='931年十二月庚申',place='衡阳',note='安葬与930去世分；原未载主持礼全部名单，不把所有马氏子都加入。')
claim('event',E,'description','新楚世家作葬马殷于上潢，主作衡阳。',46,'葬殷上潢，','地点称法并列，上潢与衡阳层级地理关系未独核，不把未核同地推断当确证或加坐标。',source=ma,relation='conflicts')
ev('maxisheng_eats_before_funeral','马希声在马殷将发引时顿食数盘鸡食',46,'将发引，','数盘，',[('希声','父将发引时顿食者'),('武穆王','将发引的逝者')],when='931年十二月庚申葬发引前',place='楚、衡阳',note='原鸡隺为底本字部件问题，展示概括鸡食、不猜菜名；数盘无确定数量，不套习惯日五十为这次吃五十。')
E=ev('panqi_satirizes_maxisheng','潘起以阮籍居丧食蒸豚典故讥马希声',46,'前吏部侍郎潘起',None,[('潘起','以古人典故讥刺者'),('希声','被讥者')],when='931年十二月庚申发引时',place='楚',note='何代无贤为讥语，不能按字面写赞马贤；阮籍是典故被引人物，不新造931阮籍活动或硬录无年古人事件。')
claim('person',people['潘起'],'description','新楚世家称其礼部侍郎潘起，主此段称前吏部侍郎。',46,'其禮部侍郎潘起譏之曰：','礼/吏与前字差保留，同行同讥同君认同人；不自动转改官衔。',source=ma,relation='conflicts')
ev('xuzhigao_arrives_jinling','徐知诰抵金陵',47,'癸亥，',None,[('知诰','按前镇令实际抵达金陵者')],when='931年十二月癸亥',place='金陵',note='十一月任镇与十二月到分，不再造一次授任。')
ev('zhaotingyin_requests_yield_lizhao','赵廷隐报利州城堑已完，以昔日与李肇同功，请让昭武给李肇',48,'昭武留后','愿以昭武让肇，',[('廷隐','报城堑完并请让留后者'),('知祥','受报受请者'),('肇','牙内都指挥使、被拟让职者')],place='利州、成都',note='顷在剑州同功是赵请让理由中的追叙，不重造一场931剑州战；报已完不造筑城从何日起。')
ev('meng_initially_refuses_yield','孟知祥褒谕赵廷隐，初不许其让昭武',48,'知祥褒谕，','不许；',[('知祥','初不许让职者'),('廷隐','受褒而初请未许者')],place='西川',note='本次不许与最后召还李代分，不能整段只留拒而漏后改任。')
ev('zhaotingyin_thrice_yields','赵廷隐三次请求让昭武',48,'延隐三让，','延隐三让，',[('廷隐','三请让昭武者'),('肇','被拟让职者')],place='西川',note='延隐依段主赵廷隐及后召廷隐同职同请识疑字，保留原字；三让为合述不猜三次确日。')
ev('meng_recalls_zhao_lizhao_replaces','孟知祥召赵廷隐还成都，以李肇代昭武留后',48,'癸酉，',None,[('知祥','召赵还而以李代者'),('廷隐','奉召还成都者'),('肇','代昭武留后者')],when='931年十二月癸酉',place='利州、成都',note='奉召不等本句已抵成都；此时仍留后，不提前朝廷933授正式节度使。')
E=ev('chen_predicts_sixty_years','陈守元等以宝皇之命称王延钧避位受道将为天子六十年，王延钧信之',49,'闽陈守元等称','延钧信之，',[('陈守元','称神命并作预言者'),('延钧','相信预言的闽王')],place='闽',note='当为是道士预言，不生成未来实际统治六十年的事实；等未名成员不扩全体巫名单。')
claim('event',E,'description','新闽世家亦记陈守元称宝皇命王暂避位，后当为六十年天子。',49,'守元謂鏻曰：「寶皇命王少避其位，後當為六十年天子。」','新此段跨后称帝简叙，只补同预言，具体主丙子避位留主日期。',source=temple,relation='corroborates')
E=ev('jipeng_controls_government','王延钧命其子王继鹏权军府事',49,'丙子，','权军府事。',[('延钧','任命子权军府事者'),('继鹏','被任命权军府事的王子')],when='931年十二月丙子',place='闽',note='节度使使重字保留；权为暂掌军府，不等已继王或此刻称帝，未提前王昶后名。')
claim('event',E,'description','新闽世家记王延钧暂逊位，命其子继鹏权主府事。',49,'鏻欣然遜位，命其子繼鵬權主府事。','同子权府补，主军府与新府事称法分别留，不推完全永久退位。',source=temple,relation='corroborates')
relationship('延钧','继鹏','父亲',49,'命其子节度使使继鹏权军府事。','王延钧→王继鹏父亲，原明确其子；不将后王昶名提前为当前已改名事件。')
ev('yanjun_receives_dao_name','王延钧避位受箓，道名玄锡',49,'延钧避位',None,[('延钧','避位受箓取道名者')],when='931年十二月丙子命子后；受箓确日未独载',place='闽',note='玄锡为王道名同一人，非新道人实体；后复位在932主段待录。')
ev('yang_fosters_plans_jiaozhou','爱州将杨廷艺养假子三千，图复交州',50,'爱州将','图复交州；',[('廷艺','爱州将、养假子谋复交州者')],year=None,when='交州起兵前背景追述；养子开始具体年未载',place='爱州、交州',note='三千为史载群体数，未逐人名不建三千人物；图是计划，不等本句已攻复；杨廷艺不混920年魏州杨廷式。')
ev('lijin_takes_yang_bribe','交州守将李进知道杨廷艺图复，受其贿而不报',50,'汉交州守将','不以闻。',[('李进','知情受赂不报的南汉交州守将'),('廷艺','被指行贿的爱州将')],year=None,when='交州起兵前背景；确年未独载',place='交州',note='李进复用930守交州主体；未独授刺史时刻，不另建李进与李进唐混同。')
E=ev('yang_besieges_jiaozhou','杨廷艺举兵围交州',50,'是岁，','举兵围交州，',[('廷艺','举兵围交州者'),('李进','被围交州的守将')],when='931年，是岁；月日未载',place='交州')
claim('event',E,'description','新南汉世家大有四年记爱州杨廷艺攻交州刺史李进。',50,'四年，愛州楊廷藝叛，攻交州刺史李進，','四年承大有为931；新从南汉视角称叛，主图复，视角并列，不替换称为现代民族国家之间战争。',source=jiao,relation='adds')
ev('han_sends_chengbao_relief','刘岩遣承旨程宝率兵救交州',50,'汉主遣承旨','将兵救之，',[('汉主','派援交州者'),('宝','承旨、率兵救交州者')],when='931年，杨围交州后；月日未载',place='南汉至交州',note='派援不等援军已赶上李进守城。')
ev('jiaozhou_falls_before_relief','程宝援军未至，交州已陷',50,'未至，','城陷。',[('廷艺','围城后取得交州者'),('李进','城陷的守将'),('宝','尚未抵达的援将')],when='931年，程宝援未到时；月日未载',place='交州',note='援未到是程宝在该阶段角色，未假造城内守将程宝；不把城陷月强置十二月，岁末汇记未独月。')
E=ev('lijin_flees_executed','李进逃归南汉，刘岩将其杀死',50,'进逃归，','汉主杀之。',[('李进','城陷逃归被杀者'),('汉主','杀逃归守将者')],when='931年，交州陷后；月日未载',place='南汉，行刑地未载',note='逃归与被杀可同句连事实，不推具体广州刑场或被程宝阵杀。')
claim('event',E,'description','新南汉世家亦记李进逃归，未叙本句被杀。',50,'進遯歸。','新仅支持逃归，死亡据主；不把新未记死亡当已证明主错。',source=jiao,relation='corroborates')
ev('chengbao_besieges_jiaozhou','程宝转而围攻已被杨廷艺取得的交州',50,'宝围交州，','宝围交州，',[('宝','围攻交州者'),('廷艺','已据交州的被围者')],when='931年，交州陷后；月日未载',place='交州',note='初来救李与后围杨不同阶段，同军不同攻防身份分，避免把南汉援将描成一直与杨同阵营。')
E=ev('yang_defeats_kills_chengbao','杨廷艺出战，程宝败死',50,'廷艺出战，',None,[('廷艺','出战击败程宝者'),('宝','战败身死的南汉承旨')],when='931年，程宝围交州时；月日未载',place='交州')
claim('event',E,'description','新南汉世家同记刘龑遣程宝攻杨廷艺，程宝战死。',50,'龑遣承旨程寶攻廷藝，寶戰死。','龑沿刘岩，援攻后阶段补；本句不独述程死于某将刀下，不猜杀人执行者。',source=jiao,relation='corroborates')
reviews={41:'十一月甲申朔日食旧同日补，不换算公历范围。',42:'癸巳苏抵成都与五月遣分；知甥侄无恙不强造名单。邀同谢是意图，董族灭、刘不预闻为董说，未独证幕后诏旨阴谋，且董在蜀另有子未全族全时亡。新同谢相拒补，后932三遣李昊开战不提前。',43:'乙未仁罕自夔引还，未套三万兵总数。',44:'请归老、仍总录金陵、景通留江都辅政、王宋并平章内枢佐、张清河爵分别。李昪李璟父亲复用，徐温为已故模式被援引。新令谋左与主右异文保留；宋当前十一月平章不同三月致仕，未回改前引用。张长期二十余年贪暴屡朝无起止year空，不倒推出911，权要未名不造名单。',45:'十二月甲寅朔自铸铁器征农具钱，主二亩三钱旧亩一钱五分单位合，夏秋是否各征不推年度额；开铁禁不等所有铁政永久废。',46:'马慕朱日五十习惯开始无年，居丧评价保留归属；庚申马殷安葬同930死分。新上潢主衡阳地点异叙未硬核同地；潘主前吏新礼衔差。鸡部件疑字保留展示鸡食，不猜菜名，数盘不套五十；阮籍典故不造931活动，讥语非赞贤。',47:'癸亥徐抵金陵与前任镇分。',48:'城堑已完为报、以顷同功请让、孟初拒、三让、癸酉召还李代分；延隐疑字同主廷隐沿稳定人。前剑州同功仅请让背景不重造931战；不提前933正授节度。',49:'陈称宝皇预言六十年为预言不是历史真实期限；丙子继鹏权府、王避位受箓道名玄锡同人；重使字留，未提前后名王昶或932复位933称帝。父亲方向直接其子。',50:'养假子三千、受赂不报为未独年背景，year空；是岁围城救兵、未至城陷、李逃被杀、宝转围、杨出战宝死逐阶段。交州岁末汇记不硬十二月，杨廷艺不混杨廷式，李进复用930守将不混李进唐，新大有四年同931、叛为南汉视角，死亡李据主新仅逃，宝战死不猜执行者。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,51):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=931,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(41,51)],next_paragraph='zztj-v277-y0932-p001',next_volume=277,next_year=932,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续931年第41—50段、原103—112行；日食、苏至孟董再怨、仁罕归、吴辅政转任、张爵、铁器政令、马葬、徐抵金陵、昭武让任、闽避位及交州战。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(41,51)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
