"""Curate consecutive Tongjian vol. 269, 915 paragraphs 15–18."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 34))
main = 'tongjian-269-915-autumn'
old_28 = 'jiuwudaishi-028-he-delun'
old_08 = 'jiuwudaishi-008-autumn'
old_70 = 'jiuwudaishi-070-xia-luqi'
new_25 = 'xinwudaishi-025-yuan-xingqin'
specs = [
    (main, P / 'sources/library' / main, '12e43f3a', '司马光等'),
    (old_28, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-04/sources/library' / old_28, '70b0b93e', '薛居正等'),
    (old_08, P / 'sources/library' / old_08, '12e43f3a', '薛居正等'),
    (old_70, P / 'sources/library' / old_70, '12e43f3a', '薛居正等'),
    (new_25, ROOT / 'content/books/zizhi-tongjian/vol-268/year-0913/part-02/sources/library' / new_25, '01699c4a', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p015-p018',
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
for n in range(15, 19):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in (source_dirs[main] / 'source.txt').read_text(), n
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

def claim(table, key, field, value, n, quote, note, source=main, relation='adds'):
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明元年（915）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0915_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'李存审': '符存审', '李绍荣': '元行钦', '李绍奇': '夏鲁奇'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
    if name == '夏鲁奇':
        row['aliases'] = ['李绍奇']
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '姓名按既有主体规范；原文和摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=915):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0915_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '915年本段条；确日未载', dynasty='五代十国',
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
          '段内追叙，确年待考。' if year is None else '按主书段落次序；未把干支换算成公历日。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0915_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定其他关系。')
    return key




# p015: Beizhou resistance, Dezhou raid, and Chanzhou capture.
event('zhang_yuande_resists_jin', '贝州刺史张源德拒绝归晋并阻断镇定粮道', 15,
      '张彦之以魏博归晋也，贝州刺史张源德不从，北结沧德，南连刘鄩以拒晋，数断镇、定粮道。',
      [('张源德','拒绝归晋、连接沧德和刘鄩的贝州刺史'),('刘鄩','被张源德联络抗晋的梁将')],
      when='915年魏博归晋后；确日未载', place='贝州、沧州、德州、镇州、定州',
      note='“北结”“南连”为主书叙述，未把各州所属政权画成确定国界。')
event('jin_takes_dezhou', '李存勖遣五百骑袭取德州', 15,
      '乃遣骑兵五百，昼夜兼行，袭德州。刺史不意晋兵至，逾城走，遂克之，',
      [('李存勖','采袭德州之策并遣骑兵的晋王')],
      when='915年魏博归晋后；确日未载', place='德州',
      note='原文未具名德州原刺史或领兵将领；五百骑为主书记数。底本“德州录于沧州”疑字保留待核。')
claim('event','event_zztj_269_0915_jin_takes_dezhou','description',
      '《旧五代史》卷二十八也记晋军乘德州无备袭取，以隔断沧贝交通。',15,
      '聞德州無備，遣別將襲之，遂拔其城。',
      '旧书只称“别将”，不补具体将领姓名。',old_28,'corroborates')
event('ma_tong_dezhou_governor', '李存勖以马通为德州刺史', 15,
      '以辽州守捉将马通为刺史。',
      [('李存勖','委任马通为德州刺史的晋王'),('马通','原辽州守捉将，获任德州刺史')],
      when='915年德州被晋军攻取后；确日未载', place='德州',
      note='所任刺史承上文德州，不误作辽州。')
claim('event','event_zztj_269_0915_ma_tong_dezhou_governor','description',
      '《旧五代史》卷二十八称辽州牙将马通为德州刺史。',15,
      '命遼州牙將馬通為德州刺史',
      '旧书官衔“牙将”与主书“守捉将”不同，先并列官称不自定孰是。',old_28,'adds')
event('jin_takes_chanzhou', '晋军七月夜袭并攻下澶州', 15,
      '秋，七月，晋人夜袭澶州，陷之。',
      [],
      when='915年七月', place='澶州',
      note='主书未载具体攻城将领；王彦章当时是否在城，旧书与通鉴异说并列。')
claim('event','event_zztj_269_0915_jin_takes_chanzhou','description',
      '《旧五代史》卷八称澶州陷落时王彦章弃城来奔；《通鉴》作王彦章在刘鄩营。',15,
      '秋七月，又陷澶州，刺史王彥章棄城來奔。',
      '旧书原文与主书王彦章所在不同；旧书随后转引《通鉴》，转引部分不作为独立补证。',old_08,'conflicts')
event('wang_yanzhang_family_killed', '晋军获王彦章家属后杀其家，王彦章拒绝劝降', 15,
      '刺史王彦章在刘鄩营，晋人获其妻子，待之甚厚，遣间使诱彦章，彦章斩其使，晋人尽灭其家。',
      [('王彦章','当时在刘鄩营并拒绝晋方劝降的梁将')],
      when='915年七月澶州陷落后；确日未载', place='澶州、刘鄩营',
      note='主书称“其妻子”“其家”而未列具体姓名、人数；“晋人”未具名，下令者不自造。')
event('li_yan_chanzhou_governor', '李存勖以魏州将李岩为澶州刺史', 15,
      '晋王以魏州将李岩为澶州刺史。',
      [('李存勖','任命李岩的晋王'),('李岩','魏州将，获任澶州刺史')],
      when='915年七月澶州被晋军攻取后', place='澶州',
      note='“李岩”原字保留，未与同名人物自动合并。')
# p016: the river ambush and a separately recorded bestowed name.
event('jin_wang_wei_river_ambush', '刘鄩伏兵围晋王，夏鲁奇力战，符存审援军解围', 16,
      '晋王劳军于魏县，因帅百馀骑循河而上，觇刘鄩营。会天阴晦，鄩伏兵五千于河曲丛林间，鼓噪而出，围王数重。王跃马大呼，帅骑驰突，所向披靡。裨将夏鲁奇等操短兵力战，自午至申乃得出，亡其七骑，鲁奇手杀百馀人，伤夷遍体，会李存审救兵至，乃得免。',
      [('李存勖','率百余骑侦察刘鄩营后被围的晋王'),('刘鄩','设伏兵围攻晋王的梁将'),('夏鲁奇','近战护晋王突围并负伤的裨将'),('符存审','以李存审之名率援军解围的晋将')],
      when='915年七月条；确日未载', place='魏县、河曲丛林',
      note='主书记伏兵五千、晋王损失七骑及夏鲁奇手杀百余；这些数字不相加为总伤亡。')
claim('event','event_zztj_269_0915_jin_wang_wei_river_ambush','description',
      '《旧五代史》卷七十夏鲁奇传也记其护晋王突围，伏兵作万余。',16,
      '莊宗不滿千騎，汴人伏兵萬餘，大噪而起，圍莊宗數重。',
      '主书伏兵五千、旧书万余；旧书晋王“不满千骑”也与主书“百余骑”不等同，分别保留。',old_70,'conflicts')
claim('event','event_zztj_269_0915_jin_wang_wei_river_ambush','description',
      '《旧五代史》卷七十记夏鲁奇与同伴护晋王，自午至申力战，李存审军至而解。',16,
      '魯奇與王門關、烏德兒等奮命決戰，自午至申，俄而李存審兵至方解。',
      '旧书补同伴姓名，不据此推定所有人都幸存；王门关、乌德儿本批不建独立人物。',old_70,'adds')
event('xia_luqi_renamed_li_shaoqi', '李存勖赐夏鲁奇姓名李绍奇', 16,
      '鲁奇，青州人也，王以是益爱之，赐姓名曰李绍奇。',
      [('夏鲁奇','因护晋王有功获赐名李绍奇的青州裨将'),('李存勖','向夏鲁奇赐姓改名的晋王')],
      when='915年河曲伏兵战后；确日未载',
      note='“李绍奇”纳入夏鲁奇别名，同一人物不另建UUID；旧五代史卷三十六后记恢复夏鲁奇旧名，暂不提前写作当年事。')
claim('person',people['夏鲁奇'],'aliases','夏鲁奇获赐名李绍奇。',16,
      '赐姓名曰李绍奇', '主书明确改名；新建夏鲁奇主体的aliases含李绍奇，原文仍保留。')
# p017: feint, pursuit, withdrawal, and the long standoff at Shenxian.
event('liu_xun_feints_jinyang', '刘鄩暗撤洹水军，留草人执旗佯动并西趋晋阳', 17,
      '刘鄩以晋兵尽在魏州，晋阳必虚，欲以奇计袭取之，乃潜引兵自黄泽西去。晋人怪鄩军数日不出，寂无声迹，遣骑觇之，城中无烟火，但时见旗帜循堞往来。',
      [('刘鄩','意图袭晋阳并暗撤军队的梁将')],
      when='915年七月后；确日未载', place='洹水、黄泽、晋阳',
      note='此时“欲”袭晋阳是计划，晋阳并未失陷；草人执旗由本段后句说明。')
claim('event','event_zztj_269_0915_liu_xun_feints_jinyang','description',
      '《通鉴》明记刘鄩营中以草人执旗乘驴佯动。',17,
      '乃缚刍为人，执旗乘驴在城上耳。',
      '底本此处引号及主语衔接不整，原字保留；不据引号错误改变叙事主体。')
claim('event','event_zztj_269_0915_liu_xun_feints_jinyang','description',
      '《旧五代史》卷八概记刘鄩自洹水潜军经黄泽路西趋晋阳。',17,
      '劉鄩自洹水潛師由黃澤路西趨晉陽',
      '旧书概记路线，不补草人佯动细节。',old_08,'corroborates')
event('jin_pursues_liu_huangze', '晋军追刘鄩穿黄泽险路遇久雨，李嗣恩先入晋阳布防', 17,
      '亟发骑兵追之。会阴雨积旬，黄泽道险，堇泥深尺馀，士卒援藤葛而进，皆腹疾足肿，或坠崖谷死者什二三。晋将李嗣恩倍道先入晋阳，城中知之，勒兵为备。',
      [('李存勖','得知刘鄩西行后命骑军追击的晋王'),('李嗣恩','抢先入晋阳布防的晋将')],
      when='915年刘鄩西趋晋阳时；确日未载', place='黄泽道、晋阳',
      note='“堇泥”为底本字形，待校；“死者什二三”只按史书记追兵艰险，不换算总兵力或死亡人数。')
event('liu_xun_returns_east', '刘鄩知晋阳有备、粮尽，转经漳水东回宗城', 17,
      '鄩至乐平，糗粮且尽。又闻晋有备，追兵在后，众惧，将溃。鄩谕之曰：“今去家千里，深入敌境，腹背有兵，山谷高深，如坠井中，去将何之！惟力战庶几可免，不则以死报君亲耳。”众泣而止。周德威闻鄩西上，自幽州引千骑救晋阳，至土门，鄩已整众下山，自邢州陈宋口逾漳水而东，屯于宗城。鄩军往还，马死殆半。',
      [('刘鄩','因晋阳有备和粮乏而率军东返的梁将'),('周德威','自幽州引千骑驰援晋阳的晋将')],
      when='915年西趋晋阳未果后；确日未载', place='乐平、土门、陈宋口、漳水、宗城',
      note='主书称军马死殆半，不等于梁军人员死亡过半；旧书只概记久雨还师。')
claim('event','event_zztj_269_0915_liu_xun_returns_east','description',
      '《旧五代史》卷八记刘鄩至乐平遇连日霖雨而班师，次宗城。',17,
      '至樂平縣，值霖雨積旬，乃班師還。次宗城，遂至貝州，軍於堂邑。',
      '旧书侧重雨阻和回军，不给主书晋阳有备、粮尽细节。',old_08,'adds')
event('zhou_dewei_secures_linqing', '周德威追刘鄩，传言已据临清后抢先进城', 17,
      '德威急追鄩，再宿，至南宫，遣骑擒其斥候者数十人，断腕而纵之，使言曰：“周侍中已据临清矣！”鄩军大骇。诘朝，德威略鄩营而过，入临清，鄩引军趋贝州。',
      [('周德威','追刘鄩并抢先入临清的晋将'),('刘鄩','因晋军逼近改趋贝州的梁将')],
      when='915年刘鄩东返途中；确日未载', place='南宫、临清、贝州',
      note='“已据临清”是周德威使斥候传达的虚实未明言辞，真正入临清在次晨。')
event('shenxian_standoff', '刘鄩在莘县筑壕接甬道，晋王营于莘西，双方屡战', 17,
      '时晋王出师屯博州，刘鄩军堂邑，周德威攻之，不克。翌日，鄩军于莘县，晋军踵之，鄩治莘城，堑而守之，自莘及河筑甬道以通馈饷。晋王营于莘西三十里，烟火相望，一日数战。',
      [('李存勖','在莘县以西与梁军对峙的晋王'),('刘鄩','筑壕和甬道坚守莘县的梁将'),('周德威','攻堂邑未克的晋将')],
      when='915年刘鄩东返后；确日未载', place='博州、堂邑、莘县',
      note='“一日数战”为反复交战的概括，不推定每场战役胜负。')
# p018: Yuan Xingqin is the existing person, newly bestowed Li Shaorong.
event('yuan_xingqin_given_to_jin', '李存勖从李嗣源处征调元行钦，任散员都部署并赐名李绍荣', 18,
      '晋王爱元行钦骁健，从代州刺史李嗣源求之，嗣源不得已献之，以为散员都部署，赐姓名曰李绍荣。',
      [('李存勖','征调元行钦并授职赐名的晋王'),('李嗣源','不得已将元行钦交与晋王的代州刺史'),('元行钦','获任散员都部署并改名李绍荣者')],
      when='915年此段条；确日未载', place='代州、晋王军中',
      note='既有元行钦稳定主体复用；李绍荣是赐名，不另建人物。')
claim('person',people['元行钦'],'aliases','元行钦获赐姓名李绍荣。',18,
      '赐姓名曰李绍荣', '线上别名需补李绍荣及繁体李紹榮，保留元行钦稳定key。')
claim('event','event_zztj_269_0915_yuan_xingqin_given_to_jin','description',
      '《新五代史》卷二十五也记庄宗得元行钦后任散员都部署、赐姓名李绍荣。',18,
      '取之為散員都部署，賜姓名曰李紹榮。',
      '新书另记元行钦此前为明宗养子；该养父关系已在旧批次录入，本批不重复建边。',new_25,'corroborates')
event('gao_xingzhou_refuses_transfer', '高行周婉拒晋王延揽，留事代州', 18,
      '王复欲求行周，重于发言，密使人以官禄啖之。行周辞曰：“代州养壮士，亦为大王耳，行周事代州，亦犹事大王也。代州脱行周兄弟于死，行周不忍负之。”乃止。',
      [('李存勖','遣人以官禄延揽高行周但最终作罢的晋王'),('高行周','辞谢延揽、继续事代州的将领')],
      when='915年元行钦被征调后；确日未载', place='代州',
      note='“行周兄弟”未在此段列姓名，不新建兄弟关系；结果为高行周未转属晋王直辖。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(15, 19):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第15—18段连续处理；德州、澶州、黄泽军情分录，王彦章所在及伏兵数异说并列，夏鲁奇和元行钦赐名复用原人物。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main, primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(15, 19)], next_paragraph=Q[19]['id'],
    coverage='卷269贞明元年七月至秋第15—18段；晋军取德州、澶州，刘鄩黄泽绕袭失败，元行钦获赐名。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[15]['id'],'note':'“德州录于沧州”底本疑字原样保留；王彦章所在通鉴与旧五代史卷8异说，妻子遇害细节只有主书。'},
      {'paragraph_id':Q[16]['id'],'note':'伏兵数通鉴五千、旧五代史卷70万余；晋王随骑通鉴百余、旧书不满千，分别保留。'},
      {'paragraph_id':Q[17]['id'],'note':'底本引号衔接和“堇泥”待纸本核；雨途死亡与军马损失不混算。'},
      {'paragraph_id':Q[18]['id'],'note':'元行钦赐名李绍荣与既有元行钦同UUID；别名修订已发布并匿名读回，见content/revisions/2026-10-02-yuan-xingqin-aliases；高行周婉拒延揽。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
