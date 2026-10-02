"""Curate consecutive Tongjian vol. 270, 917 paragraphs 1–4."""
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
main = 'tongjian-270-917-start'
old28 = 'jiuwudaishi-028-yuzhou-august-relief'
new65 = 'xinwudaishi-065-dayue-founding'
specs = [
    (main,P / 'sources/library' / main,'8cdf5b01','司马光等'),
    (old28,P / 'sources/library/jiuwudaishi-028-yuzhou-relief','8cdf5b01','薛居正等'),
    (new65,P / 'sources/library' / new65,'8cdf5b01','欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0917-p001-p004',
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
for n in range(1, 5):
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
        citation = f'卷270·贞明三年（917）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0917_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'晋王':'李存勖','蜀主':'王建','李存审':'符存审','越王岩':'刘岩','刘龑':'刘岩'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明三年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '原文称谓与既有姓名合并；原文摘录保留底本字形。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=917):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0917_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '917年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_270_0917_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p001: two separate July appointment dates, with no inferred battle.
event('shu_first_recruiting_commanders','蜀主分别任桑弘志、王宗宏为西北东北面招讨',1,
      '秋，七月，庚戌，蜀主以桑弘志为西北面第一招讨，王宗宏为东北面第二招讨。',
      [('王建','任命招讨将领的蜀主'),('桑弘志','任西北面第一招讨者'),('王宗宏','任东北面第二招讨者')],
      when='917年七月庚戌',place='蜀',note='本段只见任命，未据职衔推断已出兵或战果。')
event('shu_chief_recruiting_commanders','蜀主任王宗侃、刘知俊为东北西北面都招讨',1,
      '己未，以兼中书令王宗侃为东北面都招讨，武信节度使刘知俊为西北面都招讨。',
      [('王建','任命都招讨者'),('王宗侃','任东北面都招讨者'),('刘知俊','任西北面都招讨者')],
      when='917年七月己未',place='蜀',note='与庚戌任命另按原文日次记录；确切公历日期未换算。')

# p002: reinforcements for Youzhou, before the relief battle in p005.
event('jin_sends_fu_cunshen_reinforcement','晋王增派符存审救援幽州',2,
      '晋王以李嗣源、阎宝兵少，未足以敌契丹，辛未，更命李存审将兵益之。',
      [('李存勖','增派援军的晋王'),('李嗣源','原先救援将领'),('阎宝','原先救援将领'),('李存审','奉命率军增援者')],
      when='917年七月辛未',place='幽州援军',
      note='原文李存审即既有符存审；这是增援命令，解围与战果留在卷270本年第5段。')
claim('event','event_zztj_270_0917_jin_sends_fu_cunshen_reinforcement','description',
      '《旧五代史》庄宗纪也记七月辛未遣李存审与李嗣源会于易州。',2,
      '秋七月辛未，帝遣李存審領軍與嗣源會於易州',
      '旧书用李存审，本站复用符存审主体；未把后续八月战事提前到七月。',old28,'corroborates')

# p003: Shu court politics and sanctions, preserving source transcription issue.
event('tang_wenyi_mao_wenxi_rivalry','唐文扆、张格与毛文锡争权',3,
      '蜀飞龙使唐文扆居中用事，张格附之，与司徒、判枢密院事毛文锡争权。',
      [('唐文扆','蜀飞龙使，居中用事者'),('张格','附唐文扆者'),('毛文锡','与唐文扆一方争权者')],
      when='917年八月前的朝廷局势；确日未载',place='蜀',
      note='政治关系限于本段记述，不由“附之”推成长期联盟关系。')
event('mao_wenxi_family_music_accusation','毛文锡枢密院亲族宴乐遭唐文扆谮毁',3,
      '文锡将以女适左仆射兼中书侍郎、同平章事庾传素之子，会亲族于枢密院用乐，不先表闻，蜀主闻乐声，怪之，文扆从而谮之。',
      [('毛文锡','为女议婚、会亲族用乐者'),('庾传素','拟结亲家族之父'),('王建','闻乐声而疑惑的蜀主'),('唐文扆','趁机谮毛文锡者')],
      when='917年八月庚寅之前；确日未载',place='蜀枢密院',
      note='原文说“将以女适”，婚姻尚未成立；不建婚姻关系或未具名子女主体。')
event('mao_wenxi_dismissal_family_penalties','蜀贬毛文锡并流其子、贬其弟、罢庾传素',3,
      '八月，庚寅，贬文锡茂州司马，其子司封员外郎询流维州，籍没其家；贬文锡弟翰林学士文晏为荣经尉；传素罢为工部尚书。',
      [('毛文锡','贬茂州司马并籍没家产者'),('毛询','流维州的毛文锡之子'),('毛文晏','贬荣经尉的毛文锡之弟'),('庾传素','罢相后为工部尚书者')],
      when='917年八月庚寅',place='蜀、茂州、维州、荣经',
      note='询和文晏依前文分别解为毛文锡子与弟；荣经照原文字形，地名待考。')
event('yu_ningji_acts_privy_council','庾凝绩权判蜀内枢密院事',3,
      '以翰林学士承旨庾凝绩权判内枢密院事。',
      [('庾凝绩','权判内枢密院事者')],when='917年八月庚寅后；确日未载',place='蜀',
      note='后句电子底本作“凝积”，与此前“庾凝绩”字形冲突，保留原文并待纸本核。')
claim('person',people['庾凝绩'],'description','《通鉴》称庾凝绩为庾传素再从弟。',3,
      '凝积，传素之再从弟也。',
      '电子底本此句作“凝积”，上句作“庾凝绩”；据同段上下文暂认同人，纸本待核。')

# p004: Southern Han foundation, appointments and commemorative names.
event('liu_yan_founds_dayue','刘岩在番禺称帝，建大越并改元乾亨',4,
      '癸巳，清海、建武节度使刘岩即皇帝位于番禺，国号大越，大赦，改元乾亨。',
      [('刘岩','在番禺即皇帝位者')],when='917年八月癸巳',place='番禺',
      note='《新五代史》作刘龑，为同一主体的后改名，不新建人物；大越为此时国号。')
claim('event','event_zztj_270_0917_liu_yan_founds_dayue','description',
      '《新五代史》卷六十五也记贞明三年刘龑即位，国号大越、年号乾亨。',4,
      '貞明三年，龑即皇帝位，國號大越，改元曰乾亨。',
      '异名龑与本站刘岩同人；《新五代史》仅给年，此处八月癸巳仍据主书。',new65,'corroborates')
event('dayue_first_chancellors','刘岩任赵光裔、杨洞潜、李殷衡同平章事',4,
      '以梁使赵光裔为兵部尚书，节度副使杨洞潜为兵部侍郎，节度判官李殷衡为礼部侍郎，并同平章事。',
      [('刘岩','任命朝臣者'),('赵光裔','兵部尚书、同平章事'),('杨洞潜','兵部侍郎、同平章事'),('李殷衡','礼部侍郎、同平章事')],
      when='917年八月癸巳后；确日未载',place='番禺',
      note='《新五代史》作赵光胤、李衡等，姓名异文待纸本核，不径改本站既有赵光裔、李殷衡。')
claim('event','event_zztj_270_0917_dayue_first_chancellors','description',
      '《新五代史》亦记大越置百官，但其名单作赵光胤、李衡并增倪曙，与主书不同。',4,
      '置百官，以楊洞潛為兵部侍郎，李衡禮部侍郎，倪曙工部侍郎，趙光胤兵部尚書，皆平章事。',
      '仅确认置百官及杨洞潜；赵、李姓名与人数均存异，未将额外人名合并到主书主体。',new65,'conflicts')
event('dayue_three_ancestral_temples','刘岩建三庙，追尊祖父兄',4,
      '建三庙，追尊祖安仁曰太祖文皇帝，父谦曰代祖圣武皇帝，兄隐曰烈宗襄皇帝。',
      [('刘岩','建三庙并追尊亲属者'),('刘安仁','被追尊太祖文皇帝的祖父'),('刘谦','被追尊代祖圣武皇帝的父亲'),('刘隐','被追尊烈宗襄皇帝的兄长')],
      when='917年即位后；确日未载',place='番禺',
      note='亲属称谓依主书；仅以追尊事件记录，人物关系另需核查既有键及异文。')
event('guangzhou_xingwang_fu','刘岩改广州为兴王府',4,
      '以广州为兴王府。',[('刘岩','改广州为兴王府者')],
      when='917年即位后；确日未载',place='广州',
      note='行政地名变更依原文；现代坐标未核。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,5):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷270贞明三年第1—4段；蜀军任命与宫廷政争、晋增援幽州、大越建立。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=270,year=917,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(1,5)],next_paragraph=Q[5]['id'],
    coverage='卷270贞明三年第1—4段；七八月蜀、晋、大越政军事件。',supplements=supplements,
    reviewed_questions=[
      {'paragraph_id':Q[3]['id'],'note':'电子底本“庾凝绩／凝积”不一致，按同段上下文暂作同人，待纸本校核；毛文锡女仅拟婚。'},
      {'paragraph_id':Q[4]['id'],'note':'新五代史所记赵光胤／李衡与通鉴赵光裔／李殷衡异，未跨书强并；刘龑与刘岩依已知改名同人。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
