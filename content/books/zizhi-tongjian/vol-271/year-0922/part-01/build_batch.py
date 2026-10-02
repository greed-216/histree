"""Curate consecutive Tongjian volume 271, year 922, paragraphs 1–7."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 21))
specs = [
 ('tongjian-271-921-yearend',ROOT/'content/books/zizhi-tongjian/vol-271/year-0921/part-04/sources/library/tongjian-271-921-yearend','4fea316c','司马光等'),
 ('tongjian-271-922-spring',P/'sources/library/tongjian-271-922-spring','16b51066','司马光等'),
 ('xinwudaishi-039-wang-du-coup',ROOT/'content/books/zizhi-tongjian/vol-271/year-0921/part-03/sources/library/xinwudaishi-039-wang-du-coup','57d33707','欧阳修'),
 ('jiuwudaishi-029-922-campaign',P/'sources/library/jiuwudaishi-029-922-campaign','16b51066','薛居正等'),
 ('jiuwudaishi-029-922-zhen-siege',P/'sources/library/jiuwudaishi-029-922-zhen-siege','16b51066','薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0922-p001-p007',
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
for n in range(1, 8):
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
people, used, reused, supplements = {}, {}, {'tongjian-271-921-yearend','xinwudaishi-039-wang-du-coup'}, []

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
        citation = f'卷271·龙德二年（922）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0922_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','高祖':'王建','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271龙德二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='922年本段；确日未载', note='', year=922, place='五代十国', source=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0922_' + code
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
        edge = 'participation_zztj_271_0922_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_271_0922_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)
event('wang_du_visits_chuzhi','王都元旦探望被幽的王处直，遭其殴击',1,Q[1]['text'],[('王都','探望后掣袂逃开者'),('王处直','殴王都并欲噬其鼻者')],when='922年正月壬午朔',place='定州西第',note='元旦为探望日，未几死亡另录，不把两个动作定成同一天。')
event('wang_chuzhi_death','王处直在被幽后去世，两书死因记载不同',1,'未几，处直忧愤而卒。',[('王处直','去世者')],when='922年正月朔探望后未几；确日未载',place='定州',note='通鉴记忧愤而卒；新史记见杀，并列异说，不确定杀者与精确日期。')
claim('event',used[1][-1],'description','《新五代史》记王处直欲噬王都鼻、王都逃走后，处直遂见杀。',1,'都掣袖而走，處直遂見殺。','与通鉴未几忧愤而卒的原因、时距不同；被杀记载未明具体行凶者，未推王都亲手杀父。',source='xinwudaishi-039-wang-du-coup',relation='conflicts')
claim('person',people['王处直'],'death_year','王处直于922年去世。',1,'未几，处直忧愤而卒。','本年正月条，确日及死因另有异说；此事实引用不强改已有档案字段。')
event('jin_reaches_xincheng','李存勖至新城南，得知契丹前锋涉沙河南下',2,'甲午，晋王至新城南，候骑白契丹前锋宿新乐，涉沙河而南；',[('晋王','率军至新城者')],when='922年正月甲午',place='新城南、新乐、沙河')
event('jin_soldiers_flee','晋军士卒惊惧逃亡，主将处斩仍不能止',2,'将士皆失色，士卒有亡去者，主将斩之不能止。',[],when='922年正月甲午得契丹军情后',place='新城南',note='未载主将姓名，不指认郭崇韬或李嗣昭为处斩者。')
event('guo_chongtao_advocates_attack','郭崇韬反对撤军，建议挫败契丹前锋',2,'晋王犹豫未决，中门使郭崇韬曰：',[('晋王','权衡退守者'),('郭崇韬','建议进攻前锋的中门使')],when='922年正月甲午本段',place='新城南',note='契丹为财而来、挫锋必退是郭的判断；未作独立事实认定。')
claim('event',used[2][-1],'description','诸将建议返魏州救援或解镇州围西入井陉；郭崇韬认为契丹受王郁诱、图货财，主张挫其前锋。',2,'苟挫其前锋，遁走必矣。','保留建议与当事人预测，未说晋军实际撤军。')
event('li_sizhao_supports_advance','李嗣昭自潞州至，劝晋王进而不退',2,'李嗣昭自潞州至，亦曰：“今强敌在前，吾有进无退，不可轻动以摇人心。”',[('李嗣昭','到军劝进者')],when='922年正月甲午本段',place='潞州至新城')
event('jin_attacks_khitan_vanguard','李存勖率五千铁骑至新城北，击退契丹骑兵',2,'乃自帅铁骑五千先进。至新城北，半出桑林，契丹万馀骑见之，惊走。',[('晋王','率五千铁骑进攻者')],when='922年正月甲午',place='新城北桑林',note='人数为本战原文数；天命之言归属李存勖，不作胜因。')
event('jin_captures_khitan_son','晋军追击数十里，俘获契丹主一子',2,'晋王分军为二逐之，行数十里，获契丹主之子。',[('晋王','分军追击、俘敌方主子者')],when='922年正月甲午新城战后',place='新城、沙河沿线',note='两书均不载此子姓名；不强配耶律倍等既有人物，不凭疑名创建父子关系。')
claim('event',used[2][-1],'description','《旧五代史》亦记追击数十里、获安巴坚之子。',2,'追躡數十里，獲安巴堅之子。','安巴坚为此处阿保机异称；旧史本段亦直书阿保機，但被俘之子仍未名。',source='jiuwudaishi-029-922-campaign',relation='corroborates')
event('khitan_drowning_shahe','契丹军争过沙河，桥狭冰薄，陷溺者众',2,'时沙河桥狭冰薄，契丹陷溺死者甚众。',[],when='922年正月甲午追击中',place='沙河',note='甚众无确数，不填写具体阵亡总数。')
event('khitan_retreats_wangdu','阿保机闻前军败，自定州退保望都',2,'契丹主车帐在定州城下，败兵至，契丹举众退保望都。',[('契丹主','率众退保望都者')],when='922年正月甲午新城败后',place='定州、望都')
event('wang_du_requests_marriage','王都迎宴李存勖，请以爱女嫁李继岌',2,'晋王至定州，王都迎谒于马前，宴于府第，请以爱女妻王子继岌。',[('王都','迎宴并提出婚姻者'),('晋王','受迎宴者'),('李继岌','被提议婚配的王子')],when='922年正月新城胜后、戊戌战前',place='定州',note='请以表示婚姻请求，未记允婚或成婚；不建立妻子关系，不为未名女虚拟姓名。')
event('jin_encircled_by_tunei','望都战中李存勖千骑被奚酋秃馁五千骑围困',2,'戊戌，晋王引兵趣望都，契丹逆战，晋王以亲军千骑先进，遇奚酋秃馁五千骑，为其所围。',[('晋王','先率千骑而被围者'),('秃馁','率五千骑围晋王的奚酋')],when='922年正月戊戌',place='望都',note='奚酋为原书身份，不泛称契丹帝；两军数字不累加到此前五千铁骑。')
event('li_sizhao_rescues_jin_king','李嗣昭率三百骑横击，解李存勖之围',2,'晋王力战，出入数四，自午至申不解。李嗣昭闻之，引三百骑横击之，虏退，王乃得出。',[('晋王','被救出者'),('李嗣昭','率三百骑横击救援者')],when='922年正月戊戌，自午至申被围后',place='望都')
event('jin_pursues_yizhou','晋军乘势击败契丹，追至易州',2,'因纵兵奋击，契丹大败，逐北至易州。',[('晋王','率军乘势追击者')],when='922年正月戊戌望都战后',place='望都、易州')
claim('event',used[2][-1],'description','《旧五代史》正文记追击至易水；夹注另引《契丹国志》记北至易州。',2,'追擊至易水，','正文易水与通鉴易州地点层级不同，原称并列；旧史夹注不另算已校的独立国志底本。',source='jiuwudaishi-029-922-campaign',relation='adds')
event('khitan_snow_retreat','大雪持续，契丹缺粮，人马沿途倒毙而北归',2,'会大雪弥旬，平地数尺，契丹人马无食，死者相属于道。契丹主举手指天，谓卢文进曰：“天未令我至此。”乃北归。',[('契丹主','率军北归、对卢文进发言者'),('卢文进','受其发言者')],when='922年望都败后，大雪弥旬；确日未载',place='易州以北',note='天未令为阿保机言论，不据此解释气象因果；缺粮死者没有确数。')
event('jin_observes_khitan_camp','李存勖蹑契丹后，见宿营整齐，称其法严',2,'晋王引兵蹑之，随其行止，见其野宿之所，布藁于地，回环方正，皆如编剪，虽去，无一枝乱者，叹曰：“虏用法严乃能如是，中国所不及也。”',[('晋王','观察并评价契丹军法者')],when='922年契丹北归途中',place='契丹退路',note='所不及为李存勖评论，不外推为双方军制全面比较。')
event('jin_scouts_captured','晋王命二百骑追至境界，追骑越境后多被俘',2,'晋王至幽州，使二百骑蹑契丹之后，曰：“虏出境即还。”骑恃勇追击之，悉为所擒，惟两骑自它道走免。',[('晋王','下令出境即还者')],when='922年契丹退后晋王至幽州时',place='幽州、出境追路',note='二百骑为派遣数，两骑逃免，其余记被俘；不改成全部阵亡。')
event('aboji_detains_wang_yu','阿保机责王郁，拘系带归，此后不听其谋',3,Q[3]['text'],[('契丹主','责拘王郁者'),('王郁','被拘带归者')],when='922年契丹南征退归时',place='契丹归途',note='絷不等于处死；自是不听其谋不强定终止年月。')
event('li_sigong_secures_northern_prefectures','李嗣肱率兵定妫、儒、武等州',4,'晋代州刺史李嗣肱将兵定妫、儒、武等州，',[('李嗣肱','率兵收定的代州刺史')],when='922年年初本段；确日未载',place='妫州、儒州、武州',note='李嗣肱与前条涿州被俘李嗣弼不同，不因嗣字及近形合并。')
event('li_sigong_promoted_shanbei','李嗣肱授山北都团练使',4,Q[4]['text'],[('李嗣肱','获授山北都团练使者')],when='922年定北部诸州后；确日未载',place='山北')
event('fu_cunshen_divides_defense','符存审与李嗣源议分军，屯澶州防梁',5,'晋王之北攻镇州也，李存审谓李嗣源曰：',[('李存审','建议分军备袭的符存审'),('李嗣源','共议防守者')],when='晋王北攻镇州时，约921年末至922年初；确日未载',year=None,place='德胜、澶州',note='之北攻也追述前事；不把议分军填成二月援军日。')
claim('event',used[5][-1],'description','符存审担忧梁军袭德胜或魏州，建议分军防备，遂分军屯澶州。',5,'遂分军屯澶州。','未明说两人各自具体驻点，不凭此句分配谁驻澶州。')
event('li_siyuan_prepares_weizhou','戴思远趋魏州，李嗣源先至狄公祠并告魏备敌',5,'戴思远果悉杨村之众趣魏州，嗣源引兵先之，军于狄公祠下，遣人告魏州，使为之备。',[('戴思远','自杨村趋魏州者'),('李嗣源','抢先布防并告警者')],when='922年年初；旧史列正月',place='杨村、狄公祠、魏州')
event('shi_wanquan_challenges_liang','戴思远至魏店，李嗣源遣石万全骑兵挑战',5,'思远至魏店，嗣源遣其将石万全将骑兵挑战。',[('戴思远','至魏店者'),('李嗣源','遣骑挑战者'),('石万全','率骑挑战者')],when='922年年初魏州防御时',place='魏店')
event('dai_siyuan_takes_chengan','戴思远知魏州有备，渡洹水拔成安，掠而还',5,'思远知有备，乃西渡洹水，拔成安，大掠而还。',[('戴思远','转攻成安并掠归者')],when='922年年初；旧史正月条',place='洹水、成安')
claim('event',used[5][-1],'description','《旧五代史》正月条亦记戴思远乘虚寇魏州、因有备渡洹水陷成安。',5,'梁人知其有備，乃西渡洹水，陷成安而去。','该史段起天祐十九年春正月甲午；前锋三千骑另为旧史数，不与通鉴万余战队混合。',source='jiuwudaishi-029-922-campaign',relation='corroborates')
event('dai_siyuan_sieges_desheng','戴思远以五万军急攻德胜北城，符存审拒守',5,'又将兵五万攻德胜北城，重堑复垒，断其出入，昼夜急攻之，李存审悉力拒守。',[('戴思远','围攻者'),('李存审','拒守的符存审')],when='922年年初，二月救援前',place='德胜北城')
event('jin_relief_desheng','李存勖自幽州赴援德胜，五日至魏州',5,'晋王闻德胜势危，二月，自幽州赴之，五日至魏州。',[('晋王','五日至魏州的救援者')],when='922年二月；赴援五日，确日未载',place='幽州、魏州、德胜',note='五日是路程耗时，不换算公历日期；旧史本段是月接正月，月份异说保留。')
claim('event',used[5][-1],'time_original','《旧五代史》正月条末记是月戴思远攻德胜、晋王自幽赴援。',5,'是月，梁將戴思遠寇德勝北城，','是月承接正月，而通鉴明确二月；不覆盖主书纪月，不自行据历日定真伪。',source='jiuwudaishi-029-922-campaign',relation='conflicts')
event('dai_siyuan_retreats_yangcun','戴思远闻晋王到，烧营退还杨村',5,'思远闻之，烧营遁还杨村。',[('戴思远','烧营退军者')],when='922年二月晋王赴魏后；旧史纪月不同',place='德胜、杨村')
event('shu_king_disguise_hat_order','王宗衍好微行，令士民皆戴大裁帽以避被认出',6,Q[6]['text'],[('蜀主','微行并下令的王宗衍')],when='通鉴系922年春条的惯常行为及命令；确时未载',year=None,place='蜀',note='好为、靡所不到为惯常概述；令的年份未明，不将所有微行记成922一次具体行程。')
event('yan_bao_floods_zhenzhou','阎宝围镇州，决滹沱水环城，城中缺粮',7,'晋天平节度使兼侍中阎宝筑垒以围镇州，决滹沱水环之。内外断绝，城中食尽。',[('阎宝','围城决水者')],when='922年丙午镇兵出战前；旧史列三月',place='镇州、滹沱水')
event('zhenzhou_breaks_siege','镇兵丙午出战，破围焚阎宝营，阎宝退赵州',7,'丙午，遣五百馀人出求食。宝纵其出，欲伏兵取之；其人遂攻长围，宝轻之，不为备，俄数千人继至。诸军未集，镇人遂坏长围而出，纵火攻宝营，宝不能拒，退保赵州。',[('阎宝','败退赵州者')],when='922年丙午；旧史明确三月丙午',place='镇州、赵州',note='五百余与后续数千为不同阶段人数；未载出战者主将，不强称张处瑾亲自率军。')
claim('event',used[7][-1],'time_original','《旧五代史》明确记三月丙午王师败于镇州、阎宝退赵州。',7,'三月丙午，王師敗於鎮州城下，閻寶退保趙州。','主书只列丙午、置二月后四月前；三月来自旧史独立补证，不暗补成主书原文。',source='jiuwudaishi-029-922-zhen-siege',relation='adds')
event('zhenzhou_seizes_supplies','镇兵毁晋营垒，取其刍粟，数日不尽',7,'镇人悉毁晋之营垒，取其刍粟，数日不尽。',[],when='922年丙午破围后',place='镇州围营',note='数日不尽是搬取或数量叙述，不填精确粮储吨数。')
event('li_sizhao_replaces_yan_bao','晋王以李嗣昭代阎宝为北面招讨使',7,'晋王闻之，以昭义节度使兼中书令李嗣昭为北面招讨使，以代宝。',[('晋王','更换招讨使者'),('李嗣昭','继任北面招讨使者'),('阎宝','被代职者')],when='922年丙午围城败后；旧史三月条',place='镇州')
claim('event',used[7][-1],'description','《旧五代史》亦记因镇州败绩，以李嗣昭为北面招讨使进攻镇州。',7,'帝聞失律，即以昭義節度使李嗣昭為北面招討使，進攻鎮州。','旧史帝指后来的庄宗李存勖；当时尚为晋王，不提前作皇帝即位事件。',source='jiuwudaishi-029-922-zhen-siege',relation='corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,8):
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='922年首七段连续校核；王处直死因、德胜援军纪月保留异说，镇州三月由旧史补证；未名俘子和请求婚姻不虚建身份。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=271,year=922,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,8)],next_paragraph=Q[8]['id'],supplements=supplements,coverage='卷271龙德二年第1—7正文段，原文件69—75行；包含长篇望都战事，全段按动作分录。',reviewed_questions=[
 {'paragraph_id':Q[1]['id'],'note':'死因通鉴忧愤而卒、新史见杀；未几不当元旦，未推杀者。'},
 {'paragraph_id':Q[2]['id'],'note':'被俘阿保机之子未名，不强配身份；王都请以女妻李继岌未记婚成；旧史追至易水、通鉴易州分别引用；二百骑被擒两骑逃免，不记阵亡；国志夹注不独立采集。'},
 {'paragraph_id':Q[3]['id'],'note':'阿保机复用修订后的person_阿保机；王郁拘系不当死亡。'},
 {'paragraph_id':Q[4]['id'],'note':'李嗣肱与涿州刺史李嗣弼不同，沿用既有主体。'},
 {'paragraph_id':Q[5]['id'],'note':'议分军系追述，年份null；成安旧史正月补证，德胜赴援通鉴二月与旧史是月承正月并列待核。'},
 {'paragraph_id':Q[6]['id'],'note':'好微行为惯常概述，发生年未定；王宗衍规范主体不重复。'},
 {'paragraph_id':Q[7]['id'],'note':'镇州丙午战事旧史明记三月，不把补证月冒充主书明文；未名出战主将不推张处瑾亲率。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
