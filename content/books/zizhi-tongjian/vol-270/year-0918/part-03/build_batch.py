"""Curate consecutive Tongjian vol. 270, 918 paragraphs 12–13."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 45))
main = 'tongjian-270-918-spring'
old09 = 'jiuwudaishi-009-april-appointments'
new63 = 'xinwudaishi-063-wang-jian-death'
specs = [
    (main,ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-02/sources/library' / main,'4138a6db','司马光等'),
    (old09,ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-02/sources/library' / old09,'26b19a11','薛居正等'),
    (new63,P / 'sources/library' / new63,'01f4add0','欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p012-p013',
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
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/270.txt').read_text().splitlines()
for n in range(12, 14):
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
    for key in (main,):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷270·贞明四年（918）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0918_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'蜀主':'王建','太子':'王宗衍','王衍':'王宗衍','宗弼':'王宗弼','在迎':'潘在迎'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷270贞明四年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=918):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0918_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '918年本段条；确日未载', dynasty='五代十国',
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
          '只保留原纪年，不换算公历日；叙述性回顾不推成逐次日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0918_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key
# p012: Liang minister retires; Shu king sets commands and states succession limits.
event('zhao_guangfeng_retires','梁宰相赵光逢以司徒致仕',12,
      '司空兼门下侍郎、同平章事赵光逢告老，己巳，以司徒致仕。',
      [('赵光逢','告老并以司徒致仕者')],when='918年四月己巳',place='后梁',
      note='主书“告老”与“致仕”对应，不写为去世。')
claim('event','event_zztj_270_0918_zhao_guangfeng_retires','description',
      '《旧五代史》末帝纪亦记赵光逢上章请老后以司徒致仕。',12,
      '己巳，以開府儀同三司、守司空兼門下侍郎、同平章事趙光逢為司徒致仕',
      '旧书还记加食邑，与主书主干相符。',old09,'corroborates')
event('wang_zongbi_recalled_shu_capital','病重的王建召回王宗弼任马步都指挥使',12,
      '蜀主自永平末得疾，昏瞀，至是增剧。以北面行营招讨使兼中书令王宗弼沉静有谋，五月，召还，以为马步都指挥使。',
      [('蜀主','病重并召回王宗弼者'),('王宗弼','自北面招讨召回任马步都指挥使者')],
      when='918年五月；确日未载',place='蜀',
      note='王建患病起自永平末为追叙；五月召还任命为本年事实。')
event('wang_jian_final_instructions','王建病中召大臣交代储君及徐氏亲属安排',12,
      '乙亥，召大臣入寝殿，告之曰：“太子仁弱，朕不能违诸公之请，逾次而立之。若其不堪大业，可置诸别宫，幸勿杀之。但王氏子弟，诸公择而辅之。徐妃兄弟，止可优其禄位，慎勿使之掌兵预政，以全其宗族。”',
      [('王建','召大臣交代继位与任人限制的蜀主'),('王宗衍','王建所指的太子')],
      when='918年五月乙亥；确公历日期未换算',place='蜀宫寝殿',
      note='“仁弱”是王建对太子的评价；安置别宫是预案，不记为已废黜。')

# p013: Tang Wenyi affair and transfer of power; distinguish charges from proven actions.
event('tang_wenyi_blocks_ministers','唐文扆派人守蜀宫门，使王宗弼等大臣难见王建',13,
      '内飞龙使唐文扆久典禁兵，参预机密，欲去诸大臣，遣人守宫门。王宗弼等三十馀人日至朝堂，不得入见',
      [('唐文扆','掌禁兵并派人守宫门者'),('王宗弼','被阻不得见蜀主的重臣')],
      when='918年五月至六月王建病重期间；确日未载',place='蜀宫',
      note='“欲去诸大臣”属史书叙述的意图，不写成已完成清洗。')
event('pan_zaiying_discloses_plot','潘在迎把唐文扆谋划告知王宗弼等',13,
      '遣其党内皇城使潘在迎侦察外事，在迎以其谋告宗弼等。',
      [('唐文扆','派潘在迎侦察者'),('潘在迎','向王宗弼等告知谋划的内皇城使'),('王宗弼','获悉谋划者')],
      when='918年五月至六月；确日未载',place='蜀宫',
      note='“其谋”沿上句，按史书归属唐文扆，不增补具体未载密谋步骤。')
event('wang_zongbi_ministers_enter_palace','王宗弼等入宫奏唐文扆罪，召太子侍疾',13,
      '宗弼等排闼入，言文扆之罪，以天册府掌书记崔延昌权判六军事，召太子入侍疾。',
      [('王宗弼','率臣入宫并奏唐文扆罪者'),('唐文扆','被奏罪者'),('崔延昌','权判六军事者'),('王宗衍','被召入侍疾的太子')],
      when='918年六月以前；确日未载',place='蜀宫',
      note='这里是奏罪与临时任命；正式处罚另记。')
claim('event','event_zztj_270_0918_wang_zongbi_ministers_enter_palace','description',
      '《新五代史》亦记王宗弼等排闼入宫指称唐文扆欲变。',13,
      '故將聞建疾，皆不得入見，久之，宗弼等排闥入，言文扆欲為變',
      '新书紧接称“乃杀之”，与主书先贬、王建死后才杀的顺序不一致；并列保留。',new63,'conflicts')
event('tang_wenyi_initial_exile','王建先贬唐文扆眉州刺史，再削官流雅州',13,
      '丙子，贬唐文扆为眉州刺史。翰林学士承旨王保晦坐附会文扆，削官爵，流泸州。',
      [('唐文扆','先被贬眉州刺史者'),('王保晦','因附会唐文扆而削官流泸州者')],
      when='918年五月至六月丙子；确月待上下文校核',place='眉州、泸州',
      note='本句先记初罚；后续丁酉削官流雅州、乙卯被杀分别作追加事实。')
claim('event','event_zztj_270_0918_tang_wenyi_initial_exile','description',
      '唐文扆后来又被削官爵，流雅州。',13,
      '丁酉，削唐文扆官爵，流雅州。',
      '丁酉为第二次处分，不误作已执行死刑。')
event('shu_privy_reassignment','王建令庾凝绩掌财赋文书、宋光嗣掌都城军旅',13,
      '丙申，蜀主诏中外财赋、中书除授、诸司刑狱案牍专委庾凝绩，都城及行营军旅之事委宣徽南院使宋光嗣。',
      [('王建','重新分派财政与军事职责的蜀主'),('庾凝绩','受命管财赋除授刑狱者'),('宋光嗣','受命管都城行营军旅者')],
      when='918年六月前后丙申；本段未明标月',place='蜀',
      note='按职责分录，不概括为同一人独揽蜀政。')
event('song_guangsi_regent','宋光嗣任内枢密使并与王宗弼等受遗诏辅政',13,
      '辛丑，以宋光嗣为内枢密使，与兼中书令王宗弼、宗瑶、宗绾、宗夔并受遗诏辅政。',
      [('宋光嗣','任内枢密使并受遗诏辅政者'),('王宗弼','受遗诏辅政者'),('王宗瑶','受遗诏辅政者'),('王宗绾','受遗诏辅政者'),('王宗夔','受遗诏辅政者')],
      when='918年六月前后辛丑；本段未明标月',place='蜀',
      note='主书后评宦者自此始用事，作为史家评价，不推定所有宦官此前均无权。')
event('wang_jian_dies','蜀主王建六月壬寅朔去世',13,
      '六月，壬寅朔，蜀主殂。',[('王建','六月壬寅朔去世的蜀主')],
      when='918年六月壬寅朔',place='蜀',
      note='《新五代史》也记光天元年六月卒，年龄七十二为彼书说法，未据此反推精确生年。')
claim('event','event_zztj_270_0918_wang_jian_dies','description',
      '《新五代史》卷六十三记王建光天元年六月卒。',13,
      '光天元年六月，建卒，年七十二。',
      '新书给年龄但未核生月日；年月与主书相合。',new63,'corroborates')
event('wang_zongyan_succeeds_shu','蜀太子王宗衍六月癸卯即皇帝位',13,
      '癸卯，太子即皇帝位。尊徐贤妃为太后、徐淑妃为太妃。以宋光嗣判六军诸卫事。',
      [('王宗衍','继位的蜀太子'),('徐贤妃','被尊为太后者'),('徐淑妃','被尊为太妃者'),('宋光嗣','判六军诸卫事者')],
      when='918年六月癸卯',place='蜀',
      note='新书称即位后去“宗”名衍；本站王宗衍主体不另建“王衍”。')
claim('person',people['王宗衍'],'description','《新五代史》记太子继位后去宗字，名衍。',13,
      '太子立，去「宗」名衍。',
      '此为同一人更名书证；既有主体今后应增“王衍”别名。',new63,'adds')
event('tang_wenyi_wang_baohui_executed','新蜀主继位后杀唐文扆、王保晦',13,
      '乙卯，杀唐文扆、王保晦。',
      [('唐文扆','被杀者'),('王保晦','被杀者')],
      when='918年六月乙卯',place='蜀',
      note='主书明系继位后乙卯，与新五代史将唐文扆之死置王建卒前不同。')
claim('event','event_zztj_270_0918_tang_wenyi_wang_baohui_executed','description',
      '《新五代史》称王建死前王宗弼等入宫后即杀唐文扆，时间顺序与主书乙卯不同。',13,
      '宗弼等排闥入，言文扆欲為變，乃殺之。建因以老將大臣多許昌故人',
      '依新书叙述王建仍在世；同一死亡的时序异说并列，不另造第二起杀害。',new63,'conflicts')
event('shu_purge_tang_wenyi_family','蜀命杀唐文裔，免唐道崇官',13,
      '命西面招讨副使王宗昱杀天雄节度使唐文裔于秦州，免左保胜军使领右街使唐道崇官。',
      [('王宗昱','奉命在秦州杀唐文裔者'),('唐文裔','被杀于秦州者'),('唐道崇','被免官者')],
      when='918年六月乙卯后；确日未载',place='秦州、蜀',
      note='王宗昱为执行命令者；命令发出者此句未具名，不凭相邻称号强指。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(12,14):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷270贞明四年第12—13段；王建病重与蜀政权交接、唐文扆事件及异说。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=270,year=918,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(12,14)],next_paragraph=Q[14]['id'],
    coverage='卷270贞明四年第12—13段；王建病重、蜀廷权力安排及王宗衍继位。',supplements=supplements,
    reviewed_questions=[
      {'paragraph_id':Q[12]['id'],'note':'永平末得病是追叙，五月召还王宗弼与乙亥遗言为本年；安置太子别宫是预案。'},
      {'paragraph_id':Q[13]['id'],'note':'新五代史把唐文扆被杀叙于王建去世前，通鉴明确在王宗衍即位后乙卯；同一死亡保留时序异说。'},
      {'paragraph_id':Q[13]['id'],'note':'新五代史记王宗衍即位后去“宗”字名衍，本站复用主体，别名需单独修订。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
