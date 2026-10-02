"""Curate consecutive Tongjian vol. 269, 916 paragraphs 5–10."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 39))
main = 'tongjian-269-916-spring'
old08 = 'jiuwudaishi-008-liu-xun-defeat'
old08tan = 'jiuwudaishi-008-wang-tan-jin'
old28 = 'jiuwudaishi-028-jinyang'
old61 = 'jiuwudaishi-061-an-jinquan'
old65 = 'jiuwudaishi-065-shi-junli'
new25 = 'xinwudaishi-025-an-jinquan'
new44 = 'xinwudaishi-044-he-delun-death'
specs = [
    (main, P / 'sources/library' / main, 'b1a2623e', '司马光等'),
    (old08, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-01/sources/library' / old08, '6d9827c7', '薛居正等'),
    (old08tan, P / 'sources/library' / old08tan, 'b1a2623e', '薛居正等'),
    (old28, P / 'sources/library' / old28, 'b1a2623e', '薛居正等'),
    (old61, P / 'sources/library' / old61, 'b1a2623e', '薛居正等'),
    (old65, P / 'sources/library' / old65, 'b1a2623e', '薛居正等'),
    (new25, P / 'sources/library' / new25, 'b1a2623e', '欧阳修'),
    (new44, P / 'sources/library' / new44, 'b1a2623e', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p005-p010',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
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
for n in range(5, 11):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
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

def choose_source(quote):
    for key in (main,):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明二年（916）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0916_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'全昱':'朱全昱','友谅':'朱友谅','硃瑾':'朱瑾','李存审':'符存审','晋王':'李存勖','吴王':'杨隆演','蜀主':'王建','帝':'朱友贞'}.get(name,name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明二年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=916):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0916_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '916年本段条；确日未载', dynasty='五代十国',
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
          '追叙确年不明。' if year is None else '按主书段落次序；干支未换算公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0916_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p005: one expedition, several successive actions, and disagreement among other histories.
event('wang_tan_raids_jinyang','王檀率关西梁军袭击晋阳并急攻城垒',5,
      '匡国节度使王檀密疏请发关西兵袭晋阳，帝从之，发河中、陕、同华诸镇兵合三万，出阴地关，奄至晋阳城下，昼夜急攻。',
      [('王檀','上疏请求袭晋阳并领军急攻的梁将'),('朱友贞','批准王檀所请并发兵的后梁皇帝')],
      when='916年二月至三月间；主书本段未明日',place='阴地关、晋阳',
      note='主书作三万，旧五代史卷八另列谢彦章、王彦章，卷二十八记五万；分歧并列。')
claim('event','event_zztj_269_0916_wang_tan_raids_jinyang','description',
      '《旧五代史》卷八记二月王檀与谢彦章、王彦章自阴地关攻晋阳。',5,
      '是月，命許州節度使王檀、河陽節度使謝彥章、汝州防禦使王彥章率師自陰地關抵晉陽，急攻其壘，不克而還。',
      '本纪年条作二月并增加两将；主书此段未逐名列出，未把二人加入主书参与边。',old08tan,'adds')
claim('event','event_zztj_269_0916_wang_tan_raids_jinyang','description',
      '《旧五代史》卷二十八记王檀所率为五万，与主书三万不同。',5,
      '是月，梁主遣別將王檀率兵五萬，自陰地關趨晉陽，急攻其城',
      '该段在三月战后叙王檀；兵数及编次与主书、旧书卷八有异，不能混成一个确数。',old28,'conflicts')
event('an_jinquan_defends_jinyang','安金全率子弟、退将夜出晋阳北门击退梁军',5,
      '承业即与之。金全帅其子弟及退将之家得数百人，夜出北门，击梁兵于羊马城内。梁兵大惊，引却。',
      [('安金全','率数百人出北门击梁军的退将'),('张承业','将库甲授安金全并组织守城的监军')],
      when='916年晋阳受攻夜间；确日未载',place='晋阳北门、羊马城',
      note='张承业授甲见同段上文，数百人为主书记数，不以新五代史百余人改写。')
claim('event','event_zztj_269_0916_an_jinquan_defends_jinyang','description',
      '《旧五代史》安金全传也记数百人夜出北门击退梁军。',5,
      '得數百人。夜出北門，擊賊於羊馬城內，梁人驚潰，由是退卻。',
      '旧书列传与主书人数和行动大体相合；原文保留繁体。',old61,'corroborates')
claim('event','event_zztj_269_0916_an_jinquan_defends_jinyang','description',
      '《新五代史》安金全传称所率百余人，与主书数百人不同。',5,
      '召率子弟及故將吏得百餘人，夜出北門，擊檀於羊馬城中',
      '人数差异保留，不把百余与数百累加。',new25,'conflicts')
event('shi_junli_relief_jinyang','石君立率骑兵自上党救晋阳并突破汾河桥',5,
      '昭义节度使李嗣昭闻晋阳有寇，遣牙将石君立将五百骑救之。君立朝发上党，夕至晋阳。梁兵扼汾河桥，君立击破之',
      [('李嗣昭','遣牙将救援晋阳的昭义节度使'),('石君立','率五百骑自上党赴援并突破汾河桥者')],
      when='916年晋阳受攻期间；确日未载',place='上党、汾河桥、晋阳',
      note='主书与旧五代史石君立传一致记石君立五百骑；旧书卷二十八异作石嘉才三百骑。')
claim('event','event_zztj_269_0916_shi_junli_relief_jinyang','description',
      '《旧五代史》石君立传记其率五百骑救援并击破汾河桥守军。',5,
      '嗣昭遣君立率五百騎，自上黨朝發暮至。王檀遊軍扼汾橋，君立一戰敗之',
      '列传与主书相合；“汾橋”与主书“汾河桥”按同一战斗地点记录。',old65,'corroborates')
claim('event','event_zztj_269_0916_shi_junli_relief_jinyang','description',
      '《旧五代史》卷二十八另作石嘉才率三百骑救援。',5,
      '昭義李嗣昭遣將石嘉才率騎三百赴援。',
      '同书石君立传及主书皆作石君立五百骑；此处姓名和人数异文待纸本核，未据异名新建人物。',old28,'conflicts')
event('wang_tan_retires_from_jinyang','安金全与石君立合击后，王檀率梁军退走',5,
      '遂入城。夜，与安金全等分出诸门击梁兵，梁兵死伤什二三。诘朝，王檀引兵大掠而还。',
      [('安金全','与援军分门出击者'),('石君立','入城后与安金全合击者'),('王檀','次日率梁军退走并掠夺者')],
      when='916年晋阳解围前夜及次晨；确日未载',place='晋阳',
      note='“梁兵死伤什二三”是主书概数，不推算为精确人数；石君立入城见紧接前句。')
event('jinyang_defenders_unrewarded','晋王未对安金全等晋阳守城者行赏',5,
      '晋王性矜伐，以策非己出，故金全等赏皆不行。',
      [('李存勖','未对安金全等行赏的晋王'),('安金全','守城后未获行赏者')],
      when='晋阳解围后；确年未能由此句单独确定',place='晋军',year=None,
      note='“以策非己出”是主书解释，未把晋王内心动机当可独立核实事实；赏不行发生时间未定。')
claim('event','event_zztj_269_0916_jinyang_defenders_unrewarded','description',
      '《新五代史》亦说庄宗终其世未记安金全守城之功。',5,
      '然莊宗不以金全為能，終其世不錄其功。',
      '旧书范围是后来一段时期，不可将“终其世”压缩成916年当天。',new25,'adds')
# p006: title and original surname differ among books only as normal variants.
event('he_delun_executed','张承业因贺德伦部众逃奔梁军而收斩贺德伦',6,
      '梁兵之在晋阳城下也，大同节度使贺德伦部兵多逃入梁军，张承业恐其为变，收德伦，斩之。',
      [('贺德伦','部兵逃奔梁军后被收斩的大同节度使'),('张承业','因担忧变故而收斩贺德伦的晋方监军')],
      when='916年王檀围晋阳期间；确日未载',place='晋阳',
      note='“恐其为变”是张承业的担忧，原文未说贺德伦本人已起兵。')
claim('event','event_zztj_269_0916_he_delun_executed','description',
      '《新五代史》卷四十四也记贺德伦部下奔王檀、张承业因惧而杀他。',6,
      '王檀攻太原，德倫麾下多奔檀，承業懼德倫為變，殺之。',
      '新书与主书相合；不将担忧写成德伦已发动叛乱。',new44,'corroborates')
# p007: record the reaction as reported speech, not an objective prognosis.
event('liang_emperor_laments_defeats','后梁帝闻刘鄩败、王檀无功而叹“吾事去矣”',7,
      '帝闻刘鄩败，又闻王檀无功，叹曰：“吾事去矣！”',
      [('朱友贞','闻两路失利而发出感叹的后梁皇帝')],
      when='916年刘鄩败、王檀退后；确日未载',place='后梁朝廷',
      note='此为史书记载的当事人感叹，不判定后梁政权在此时实际终结。')
claim('event','event_zztj_269_0916_liang_emperor_laments_defeats','description',
      '《旧五代史》卷二十八也载梁主闻两路不利说“吾事去矣”。',7,
      '時鄩敗於莘縣，王檀遁於晉陽，梁主聞之，曰：「吾事去矣！」',
      '旧书地点用莘县和晋阳，是传中叙述；与主书故元城和晋阳行动联系时保留原措辞。',old28,'corroborates')
# p008: two sieges and a place-name change.
event('jin_takes_weizhou','晋王攻卫州，刺史米昭降晋',8,
      '三月，乙卯朔，晋王攻卫州，壬戌，刺史米昭降之。',
      [('李存勖','攻卫州的晋王'),('米昭','壬戌以卫州降晋的刺史')],
      when='916年三月乙卯朔至壬戌；未换算公历日',place='卫州',
      note='乙卯朔开始进攻，壬戌为降城之日；不混成同日。')
claim('event','event_zztj_269_0916_jin_takes_weizhou','description',
      '《旧五代史》卷二十八亦记三月攻卫州、壬戌米昭降。',8,
      '三月乙卯朔，分兵以攻衛州。壬戌，刺史米昭以城降。',
      '旧书此处作分兵，不据此推定晋王本人到卫州城下。',old28,'corroborates')
event('jin_takes_huizhou','晋军攻惠州，刺史靳绍出走后被擒斩',8,
      '又攻惠州，刺史靳绍走，擒斩之',
      [('靳绍','弃惠州出走后被擒斩的刺史')],
      when='916年三月壬戌后；确日未载',place='惠州',
      note='“擒斩之”指靳绍；本句未给执行擒斩的具体将领。')
event('huizhou_renamed_cizhou','晋军复以惠州为磁州',8,
      '复以惠州为磁州。',
      [],
      when='916年三月攻惠州后；确日未载',place='惠州、磁州',
      note='此为州名更改，不等于另一次独立攻城。')
# p009: appointment follows failed recall.
event('liu_xun_appointed_xuanyi','后梁授刘鄩宣义节度使，命其屯黎阳',9,
      '上屡召刘鄩不至，己巳，即以鄩为宣义节度使，使将兵屯黎阳。',
      [('朱友贞','多次召刘鄩未果后授其宣义节度使的后梁帝'),('刘鄩','受授宣义节度使并被命屯黎阳的梁将')],
      when='916年三月己巳；未换算公历日',place='黎阳、后梁朝廷',
      note='“屡召不至”是任命前背景，不武断说明刘鄩拒命动机。')
claim('event','event_zztj_269_0916_liu_xun_appointed_xuanyi','description',
      '《旧五代史》卷八亦记己巳授刘鄩宣义军节度使，但官称更详。',9,
      '己巳，製以鄩為滑州宣義軍節度副大使，知節度事。',
      '旧书官名与主书简写不同，分别保留；旧书未在这句载屯黎阳。',old08,'corroborates')
# p010: military occupation and appointment are distinct outcomes.
event('jin_takes_mingzhou','晋军于四月攻拔洺州',10,
      '夏，四月，晋人拔洺州',
      [],
      when='916年夏四月；确日未载',place='洺州',
      note='主书只写“晋人”，晋王是晋方统领者，未称其亲临攻城。')
claim('event','event_zztj_269_0916_jin_takes_mingzhou','description',
      '《旧五代史》卷二十八同记四月攻下洺州。',10,
      '夏四月，攻洺州，下之。',
      '旧书为后唐本纪，叙事同年；不补具体领兵者。',old28,'corroborates')
event('yuan_jianfeng_mingzhou_governor','袁建丰由魏州都巡检使转任洺州刺史',10,
      '以魏州都巡检使袁建丰为洺州刺史。',
      [('袁建丰','受任洺州刺史的原魏州都巡检使')],
      when='916年夏四月洺州被攻取后；确日未载',place='洺州',
      note='袁建丰名字只见主书本段；未据未核同名资料增补生卒或其他经历。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(5, 11):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明二年第5—10段连续处理；晋阳战事分录，兵数、援将姓名和纪月异说并列，贺德伦未被误记为已叛。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=916,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(5, 11)], next_paragraph=Q[11]['id'],
    coverage='卷269贞明二年第5—10段；晋阳救援、贺德伦被杀、梁帝叹、卫惠洺诸州易手。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[5]['id'],'note':'主书王檀兵三万、石君立五百骑；旧五代史卷二十八作王檀五万、石嘉才三百骑，卷六十五石君立传又作五百骑。姓名、兵数异文保留待纸本核。旧书卷八作二月发兵，卷二十八在三月战后记晋阳战。'},
      {'paragraph_id':Q[5]['id'],'note':'安金全守晋阳，主书与旧五代史记数百人，新五代史记百余人；未合并成确数。主书追述未获行赏，发生年留空。'},
      {'paragraph_id':Q[6]['id'],'note':'贺德伦部下投梁与本人谋反不同；主书与新五代史均只记张承业因惧而杀。'},
      {'paragraph_id':Q[8]['id'],'note':'卫州壬戌降，惠州又被攻取、靳绍被擒斩，磁州为其复名；未将数事混成同日。'},
      {'paragraph_id':Q[9]['id'],'note':'刘鄩官称通鉴简作宣义节度使，旧五代史作滑州宣义军节度副大使、知节度事。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
