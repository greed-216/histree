"""Curate Tongjian 267, year 911, consecutive paragraphs 1-11."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 12))
main1 = 'tongjian-267-910-yearend'
main2 = 'tongjian-267-911-winter'
new_baixiang = 'xinwudaishi-025-baxiang'
new_annals = 'xinwudaishi-005-baixiang'
new_shi = 'xinwudaishi-025-shi-jiantang'
new_li = 'xinwudaishi-025-li-jianji'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0911-p001-p011',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR.parent / 'year-0910/part-05/sources/library' / main1, '7674c2cb', '司马光等'),
    (main2, P / 'sources/library' / main2, 'dcd113f9', '司马光等'),
    (new_baixiang, YEAR.parent / 'year-0910/part-05/sources/library' / new_baixiang, '7674c2cb', '欧阳修'),
    (new_annals, P / 'sources/library' / new_annals, 'dcd113f9', '欧阳修'),
    (new_shi, P / 'sources/library' / new_shi, 'dcd113f9', '欧阳修'),
    (new_li, P / 'sources/library' / new_li, 'dcd113f9', '欧阳修'),
]
source_dirs = {key: path for key, path, _, _ in specs}
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
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {key: (source_dirs[key] / 'source.txt').read_text() for key in (main1, main2)}
for n in range(1, 12):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in primary_texts[main1 if n <= 3 else main2], n

registry = {}
existing_relation_keys = set()
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    archived = json.loads(path.read_text())
    existing_relation_keys.update(row['key'] for row in archived['person_relationships'])
    for row in archived['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (path, row['name'])
        registry[row['name']] = row
aliases = {'吴越王镠':'钱镠','楚王殷':'马殷','蜀主':'王建',
           '王景仁':'王茂章','李存审':'符存审','宋鄴':'宋邺','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1, main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1, main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷267·乾化元年（911）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_267_0911_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1, main2):
        book = json.loads((source_dirs[source] / 'paragraph.json').read_text())['book']
        supplements.append(dict(claim_key=ck, source_book=book, primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=supplement_relation))
    return ck

def person(name, n, role, quote):
    name = aliases.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷267乾化元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=911):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_267_0911_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '911年本段条；确日未载', dynasty='五代十国',
               description=title + '。', phases=[], location_name=place,
               location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown',
               location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',
               status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote,
          note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', row['time_original'], n, quote,
          '段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_267_0911_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key,
                                       role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key

def relation(a, b, kind, n, quote, note):
    ak, bk = people[a], people[b]
    key = f'relationship_{ak}_{bk}_{kind}'
    if key in existing_relation_keys:
        reused.add(key)
    B['person_relationships'].append(dict(key=key, person_a_key=ak, person_b_key=bk,
                                          relation_type=kind, description=f'{a}是{b}的{kind}。', status='draft'))
    claim('person_relationship', key, 'description', f'{a}是{b}的{kind}。', n, quote, note)

event('new_year_eclipse', '乾化元年正月朔日食', 1,
      '春，正月，丙戌朔，日有食之。',when='911年正月丙戌朔',
      note='沿用主书纪日，不另行换算公历日期。')

event('baixiang_forage', '晋军抄击梁军刈刍部队，梁马缺草多死', 2,
      '柏乡比不储刍，梁兵刈刍自给，晋人日以游军抄之，梁兵不出。周德威使胡骑环营驰射而诟之，梁兵疑有伏，愈不敢出，坐刂屋茅坐席以饲马，马多死。',
      [('周德威','组织胡骑骚扰梁营的晋将')],when='911年正月丁亥前；确日未载',place='柏乡',
      note='前因是梁军草料不足；“疑有伏”是梁军判断。')
event('baixiang_liang_sallies', '周德威等挑梁垒，王茂章、韩勍率军出战', 2,
      '丁亥，周德威与别将史建瑭、李嗣源将精骑三千压梁垒门而诟之，王景仁、韩勍怒，悉众而出。',
      [('周德威','率三千精骑挑战梁营'),('史建瑭','与周德威同率精骑'),('李嗣源','与周德威同率精骑'),('王景仁','率梁军出营'),('韩勍','率梁军出营')],
      when='911年正月丁亥',place='柏乡',note='三千为晋军挑战骑兵；王景仁按已核身份复用王茂章。')
event('baixiang_bridge_defense', '梁军争野河桥，李建及率二百人击退', 2,
      '李存璋以步兵陈于野河之上，梁军横亘数里，竞前夺桥，镇、定步兵御之，势不能支。晋王谓匡卫都指挥使李建及曰：“贼过桥则不可复制矣。”建及选卒二百，援枪大噪，力战却之。',
      [('李存璋','在野河列步兵'),('李存勖','命李建及守桥的晋王'),('李建及','选二百兵力战退梁军')],
      when='911年正月丁亥',place='野河桥',note='桥头形势危急后由二百人反击；不把二百当梁军总数。')
claim('event','event_zztj_267_0911_baixiang_bridge_defense','description',
      '《新五代史》李建及传也记其率二百人击退梁兵。',2,
      '建及選二百人馳擊梁兵，梁兵敗，解去。',
      '新史同人作王建及，主书称李建及并记其原姓王；复用同一人物。',new_li,'corroborates')
event('baixiang_wait_until_tired', '周德威劝晋王暂缓决战，待梁军饥疲', 2,
      '德威叩马而谏曰：“观梁兵之势，可以劳逸制之，未易以力胜也。彼去营三十馀里，虽挟糗粮，亦不暇食，日昳之后，饥渴内迫，矢刃外交，士卒劳倦，必有退志。当是时，我以精骑乘之，必大捷。于今未可也。”王乃止。',
      [('周德威','劝晋王待梁军饥疲再战'),('李存勖','听取周德威建议的晋王')],
      when='911年正月丁亥午前后',place='柏乡、高邑附近',note='此为战场决策；“必大捷”是周德威的判断，胜负见下一段。')

event('baixiang_liang_rout', '柏乡之战梁军东阵先退，继而全军溃败', 3,
      '时魏、滑之兵陈于东、宋、汴之兵陈于西。至晡，梁军未食，士无斗志，景仁等引兵稍却，周德威疾呼曰：“梁兵走矣！”晋兵大噪争进，魏、滑兵先退，李嗣源帅众噪于西陈之前曰：“东陈已走，尔何久留！”梁兵互相惊怖，遂大溃。',
      [('王景仁','梁军主帅，率兵稍退'),('周德威','呼喊促晋军反击'),('李嗣源','向梁西阵喊话的晋将')],
      when='911年正月丁亥至晡',place='柏乡、野河',note='主书分东阵魏滑、 西阵宋汴，先退后大溃；不把战果提前放入910年。')
claim('event','event_zztj_267_0911_baixiang_liang_rout','description',
      '《新五代史》庄宗纪也记八年正月败梁军于柏乡。',3,
      '八年正月，敗梁軍于柏鄉，斬首二萬級',
      '新史沿唐天祐八年纪年，与后梁乾化元年对应；人数按各书原文独立保留。',new_annals,'corroborates')
claim('event','event_zztj_267_0911_baixiang_liang_rout','description',
      '《新五代史》史建瑭传另记其击梁军右翼。',3,
      '周德威擊其左，建瑭擊其右，梁軍皆走，遂大敗之。',
      '传记补史建瑭行动；主书未明说其击右翼，标为补充书证。',new_shi,'adds')
event('baixiang_pursuit', '晋赵军追击梁军至柏乡、邢州，梁将逃脱', 3,
      '赵人以深、冀之憾，不顾剽掠，但奋白刃追之，梁之龙骧、神捷精兵殆尽，自野河至柏乡，僵尸蔽地。王景仁、韩勍、李思安以数十骑走。晋兵夜至柏乡，梁军已去，弃粮食、资财、器械不可胜计。凡斩首二万级。李嗣源等追奔至邢州，河朔大震。',
      [('王景仁','败后与数十骑逃走的梁将'),('韩勍','败后逃走的梁将'),('李思安','败后逃走的梁将'),('李嗣源','追击至邢州的晋将')],
      when='911年正月丁亥及其后',place='野河、柏乡、邢州',
      note='斩首二万是主书记载的战果，未经独立数字核计；不把“精兵殆尽”解释为梁军所有兵种尽灭。')
event('baixiang_wang_tan_refuge', '王檀收容梁军败卒并遣归本道', 3,
      '保义节度使王檀严备，然后开城纳败卒，给以资粮，散遣归本道。',
      [('王檀','开城收容并遣返败卒的梁将')],when='911年柏乡战后',place='邢州',
      note='先戒备后开城；败卒人数未载。')
event('deep_ji_abandoned', '杜廷隐等弃深冀，掳丁壮并坑杀老弱', 3,
      '杜廷隐等闻梁兵败，弃深、冀而去，悉驱二州丁壮为奴婢，老弱者坑之，城中存者坏垣而已。',
      [('杜廷隐','梁军败后弃深冀并掳杀居民的一方主将')],
      when='911年柏乡战败消息后',place='深州、冀州',
      note='主书归于“杜廷隐等”，具体执行者及人数未分明；不外推到其他具名梁将。')

event('yang_shihou_recalled', '梁复任杨师厚北面都招讨使，收集散兵', 4,
      '癸巳，复以杨师厚为北面都招讨使，将兵屯河阳，收集散兵，旬馀，得万人。',
      [('杨师厚','复任北面都招讨使并收兵')],
      when='911年正月癸巳起；旬余得万人',place='河阳',note='万人为旬余所收散兵规模，不计为癸巳当日已成。')
event('jin_northern_counteroffensive', '晋军分兵趣澶魏、攻邢州', 4,
      '己亥，晋王遣周德威、史建瑭将三千骑趣澶、魏，张承业、李存璋以步兵攻邢州，自以大军继之，移檄河北州县，谕以利害。',
      [('李存勖','派遣两路军并亲率大军继后'),('周德威','率三千骑趋澶魏'),('史建瑭','与周德威同率骑兵'),('张承业','率步兵攻邢州'),('李存璋','率步兵攻邢州')],
      when='911年正月己亥',place='澶州、魏州、邢州',note='三千为周、史所率骑兵总数；檄文效果未载。')
event('liang_reinforces_xingzhou', '梁帝遣徐仁溥千兵夜入邢州助王檀', 4,
      '帝遣别将徐仁溥将兵千人，自西山夜入邢州，助王檀城守。',
      [('朱温','遣援兵助守邢州的梁帝'),('徐仁溥','率千人夜入邢州'),('王檀','受援守邢州的梁将')],
      when='911年正月己亥后；确日未载',place='邢州',note='千人为徐仁溥所率援兵。')
event('wang_jingren_dismissed', '梁免王茂章（王景仁）招讨使并落平章事', 4,
      '己酉，罢王景仁招讨使，落平章事。',
      [('王景仁','柏乡败后被罢招讨使并落平章事')],
      when='911年正月己酉',place='后梁',note='王景仁复用已校的王茂章实体。')

event('princess_returns_shu', '普慈公主诉李继崇骄矜嗜酒，王建召女归宁', 5,
      '蜀主之女普慈公主嫁岐王从子秦州节度使继崇，公主遣宦者宋光嗣以绢书遣蜀主，言继崇骄矜嗜酒，求归成都，蜀主召公主归宁。',
      [('普慈公主','向父王请归成都的前蜀公主'),('李继崇','被公主指责的岐王从子、秦州节度使'),('宋光嗣','传递绢书的宦者'),('王建','召女归宁的蜀主')],
      when='911年正月辛亥前',place='秦州、成都',note='“骄矜嗜酒”出于公主书信，作为其陈述记录。')
relation('王建','普慈公主','父亲',5,'蜀主之女普慈公主嫁岐王从子秦州节度使继崇',
         '原文明言普慈公主为王建之女。')
event('shu_qi_break', '王建留普慈公主并任宋光嗣，岐王与蜀绝交', 5,
      '辛亥，公主至成都，蜀主留之，以宋光嗣为阁门南院使。岐王怒，始与蜀绝。',
      [('普慈公主','到成都后被父王留下'),('王建','留女并任宋光嗣'),('宋光嗣','获任阁门南院使'),('李茂贞','因之与蜀绝交的岐王')],
      when='911年正月辛亥及后',place='成都、岐',note='岐王按既有李茂贞身份复用，不把绝交提前到公主求归时。')

event('lu_shizhou_captures_pan', '吕师周入飞山洞擒潘金盛并在武冈斩杀', 6,
      '吕师周引兵攀藤缘崖入飞山洞袭潘金盛，擒送武冈，斩之。移兵击宋鄴。',
      [('吕师周','率楚军擒潘金盛并移兵攻宋邺'),('潘金盛','被楚军擒送武冈斩杀'),('宋鄴','成为楚军下一攻伐对象')],
      when='911年正月后段；确日未载',place='飞山洞、武冈',
      note='“移兵击宋鄴”只说明出击，结果需待后续段落；宋鄴规范简体为宋邺。')

event('jin_fails_weizhou', '晋王攻魏州未克', 7,
      '二月，己未，晋王至魏州，攻之，不克。',
      [('李存勖','亲至魏州攻城未克')],when='911年二月己未',place='魏州')
event('li_zhen_reinforces_wei', '梁任李振天雄副使，杜廷隐护千兵入魏州', 7,
      '庚申，以户部尚书李振为天雄节度副使，命杜廷隐将兵千人卫之，自杨刘济河，间道夜入魏州，助周翰城守。',
      [('朱温','任命李振、遣杜廷隐护卫'),('李振','获任天雄节度副使入魏州'),('杜廷隐','率千人护李振入魏州'),('罗周翰','受援守魏州')],
      when='911年二月庚申',place='杨刘、魏州',note='千人为杜廷隐所率护卫兵；与前文撤深冀时同一将。')
event('jin_at_liyang', '晋王至黎阳观河，梁渡河兵闻讯弃舟', 7,
      '癸亥，晋王观河于黎阳，梁兵万馀将渡河，闻晋王至，皆弃舟而去。',
      [('李存勖','至黎阳观河的晋王')],when='911年二月癸亥',place='黎阳',
      note='梁兵万余只是拟渡河兵的主书数目，未记交战。')

event('caizhou_mutiny', '刘行琮在蔡州作乱，王存俨诛之并抚众', 8,
      '蔡州右厢指挥使刘行琮作乱，纵兵焚掠，将奔淮南；顺化指挥使王存俨诛行琮，抚遏其众，自领州事，以众情驰奏。',
      [('刘行琮','在蔡州兵变并被杀'),('王存俨','诛刘行琮、抚众并领州事')],
      when='911年二月条；确日未载',place='蔡州',note='刘行琮意图奔淮南，原文未称已经抵达。')
event('liang_halts_caizhou_attack', '朱温召回博王友文所发讨蔡州兵，授王存俨权知州事', 8,
      '时东京留守博王友文不先请，遽发兵讨之，兵至鄢陵，帝曰：“存俨方惧，若临之以兵，则飞去矣。”驰使召还。田子，授存俨权知蔡州事。',
      [('朱友文','未先请即发兵讨蔡州的博王'),('朱温','召回讨兵并授王存俨权知州事'),('王存俨','获授权知蔡州事')],
      when='911年二月条；底本“田子”疑字，确日待核',place='鄢陵、蔡州',
      note='底本“田子”字形不明，保持原字，不擅改为干支；未把朱友文兵记为已攻蔡州。')

event('zhou_dewei_hebei_campaign', '周德威攻取贝、博、澶州诸城并进逼卫州', 9,
      '乙丑，周德威自临清攻贝州，拔夏津、高唐；攻博州，拔东武、朝城。攻澶州，刺史张可臻弃城走，帝斩之。德威进攻黎阳，拔临河、淇门；逼卫州，掠新乡、共城。',
      [('周德威','率晋军攻取多城、进逼卫州'),('张可臻','弃澶州而逃，后被梁帝斩杀'),('朱温','因弃城处死张可臻')],
      when='911年二月乙丑起；庚午前',place='贝州、博州、澶州、黎阳、卫州',
      note='列举地名按原文，不将所掠新乡、共城写作长期占领。')
event('liang_white_sima_slope', '朱温率亲军屯白司马阪防晋', 9,
      '庚午，帝帅亲军屯白司马阪以备之。',
      [('朱温','率亲军驻白司马阪防备晋军')],when='911年二月庚午',place='白司马阪')

event('liu_shouguang_torture', '刘守光在燕施酷刑，闻柏乡战败后谋四镇盟主', 10,
      '卢龙、义昌节度使兼中书令燕王守光既克沧州，自谓得天助，淫虐滋甚。每刑人，必置诸铁笼，以火逼之；又为铁刷刷人面。',
      [('刘守光','在燕施铁笼、铁刷酷刑的燕王')],
      when='克沧州后至911年本段条；确日未载',place='燕',
      note='本段追述克沧州后的行为，不能一概定在911年单日。')
claim('event','event_zztj_267_0911_liu_shouguang_torture','description',
      '刘守光闻柏乡梁败后请以四镇联兵为由商议盟主。',10,
      '闻梁兵败于柏乡，使人谓赵王镕及王处直曰：“闻二镇与晋王破梁兵，举军南下，仆亦有精骑三万，欲自将之为诸公启行。然四镇连兵，必有盟主，仆若至彼，何以处之？”',
      '“精骑三万”为刘守光自称，不能当作已出兵规模。')
event('jin_considers_yan', '李存勖与诸将商议先攻燕，随后晋军解邢魏围', 10,
      '诸将曰：“云、代与燕接境，彼若扰我城戍，动摇人情，吾千里出征，缓急难应，此亦腹心之患也。不若先取守光，然后可以专意南讨。”王曰：“善！”',
      [('李存勖','同意诸将先攻燕的建议'),('刘守光','成为晋将建议讨伐对象')],
      when='911年二月柏乡战后；确日未载',place='晋、燕',
      note='先攻燕是议策，此句未记已经发兵。')
event('jin_lifts_xing_wei_sieges', '杨师厚援邢魏，晋军解围；梁军追至漳水后屯魏州', 10,
      '会杨师厚自磁、相引兵救邢、魏，壬申，晋解围去；师厚追之，逾漳水而还，邢州围亦解。师厚留屯魏州。',
      [('杨师厚','率梁军解邢魏围并屯魏州'),('李存勖','率晋军解围撤离')],
      when='911年二月壬申',place='邢州、魏州、漳水',note='同时记魏州与邢州解围，不写成杨师厚攻克晋城。')

event('wang_rong_visits_jin', '王镕至赵州犒晋军，遣养子张文礼率三十七都随征', 11,
      '赵王镕自来谒晋王于赵州，大犒将士，自是遣其养子德明将三十七都常从晋王征讨。德明本姓张，名文礼，燕人也。',
      [('王镕','亲至赵州犒军并遣养子'),('李存勖','在赵州受王镕犒军的晋王'),('张文礼','王镕养子、率三十七都随晋王征讨')],
      when='911年二月壬申后；确日未载',place='赵州',
      note='原文“德明”与本姓张名文礼为同一人；三十七都是部队编制数，不换算兵员。')
next(x for x in B['people'] if x['key']==people['张文礼'])['aliases']=['赵德明','德明']
relation('王镕','张文礼','养父',11,'自是遣其养子德明将三十七都常从晋王征讨。德明本姓张，名文礼',
         '原文明言德明为王镕养子；姓名按同一稳定人物合并。')
event('jin_returns_jinyang', '李存勖自赵州返晋阳，留周德威三千人戍赵州', 11,
      '壬午，晋王发赵州，归晋阳，留周德威等将三千人戍赵州。',
      [('李存勖','自赵州返晋阳的晋王'),('周德威','留率三千人戍赵州的晋将')],
      when='911年二月壬午',place='赵州、晋阳',note='三千为留戍赵州之兵，不是全晋军规模。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1, 12):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷267乾化元年正月至二月第1—11段连续处理；柏乡主战与前一年对峙分年。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=267, year=911,
    primary_source_key=main1, primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(1,12)],next_paragraph='zztj-v268-y0911-p001',
    coverage='卷267乾化元年正月至二月第1—11段，柏乡决战、晋军进击、蜀岐绝交及燕赵互动。',
    supplements=supplements,status=status,
    textual_reviews=[{'paragraph_id':Q[8]['id'],'note':'第8段电子底本“田子”疑损字，未换算确日，纸本待核。'},
                     {'paragraph_id':Q[2]['id'],'note':'李建及原姓王；《新五代史》李建及传写王建及，按同一人物记录，原文各保留。'},
                     {'paragraph_id':Q[11]['id'],'note':'德明本姓张名文礼，归入一人并保留赵德明别名。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({key:len(value) for key,value in B.items() if isinstance(value,list)})
