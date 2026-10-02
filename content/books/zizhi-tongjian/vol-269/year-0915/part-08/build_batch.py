"""Curate consecutive Tongjian vol. 269, 915 paragraphs 25–28."""
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
main_early = 'tongjian-269-915-august'
main_late = 'tongjian-269-915-winter'
old_dc = 'jiuwudaishi-008-deconsort'
old_k = 'jiuwudaishi-008-kangwang'
old_28 = 'jiuwudaishi-028-august'
new_dc = 'xinwudaishi-013-deconsort'
new_k = 'xinwudaishi-013-kangwang'
new_63 = 'xinwudaishi-063-shu-fire'
primary_for = {25:main_early,26:main_early,27:main_late,28:main_late}
specs = [
    (main_early, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-06/sources/library' / main_early, '5f494c20', '司马光等'),
    (main_late, P / 'sources/library' / main_late, 'b1919250', '司马光等'),
    (old_dc, P / 'sources/library' / old_dc, 'b1919250', '薛居正等'),
    (old_k, P / 'sources/library' / old_k, 'b1919250', '薛居正等'),
    (old_28, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0915/part-06/sources/library' / old_28, '5f494c20', '薛居正等'),
    (new_dc, P / 'sources/library' / new_dc, 'b1919250', '欧阳修'),
    (new_k, P / 'sources/library' / new_k, 'b1919250', '欧阳修'),
    (new_63, P / 'sources/library' / new_63, 'b1919250', '欧阳修'),
]
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0915-p025-p028',
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
for n in range(25, 29):
    row = Q[n]
    assert row['text'] == (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line'] - 1]
    assert row['text'] in (source_dirs[primary_for[n]] / 'source.txt').read_text(), n
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

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or primary_for[n]
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == primary_for[n]:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明元年（915）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0915_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != primary_for[n]:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'宗侃': '王宗侃', '友敬': '朱友敬', '汉鼎': '张汉鼎', '汉杰': '张汉杰', '汉伦': '张汉伦', '汉融': '张汉融'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷269贞明元年条所见人物：{name}。', biography=None, status='draft')
    if name == '杨延直':
        row['aliases'] = ['楊延直']
    if name == '夏鲁奇':
        row['aliases'] = ['李绍奇']
    if name == '梁末帝德妃张氏':
        row['aliases'] = ['末帝德妃張氏']
        row['description'] = '张归霸之女，朱友贞妃，贞明元年九月册为德妃当夜去世。'
        row['death_year'] = 915
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




# p025: retrospective marriage, then September consort investiture and death.
event('zhu_youzhen_marries_zhang', '朱友贞为均王时娶张归霸之女为妃', 25,
      '初，帝为均王，娶河阳节度使张归霸女为妃，即位，欲立为后。后以帝未南郊，固辞。',
      [('朱友贞','为均王时娶张归霸之女的后梁皇帝'),('张归霸','女儿嫁朱友贞的河阳节度使'),('梁末帝德妃张氏','张归霸之女、朱友贞妃')],
      when='朱友贞为均王时；确年未载', place='后梁', year=None,
      note='“初”为追叙，不能把娶妻记作915年发生；册后未成，不能称已立皇后。')
consort=people['梁末帝德妃张氏']
for a,b,relation,description,quote in [
    (people['张归霸'],consort,'父亲','张归霸是梁末帝德妃张氏的父亲。','娶河阳节度使张归霸女为妃'),
    (people['朱友贞'],consort,'丈夫','朱友贞是梁末帝德妃张氏的丈夫。','帝为均王，娶河阳节度使张归霸女为妃')]:
    rk=f'relationship_{a}_{b}_{relation}'
    B['person_relationships'].append(dict(key=rk,person_a_key=a,person_b_key=b,relation_type=relation,description=description,status='draft'))
    claim('person_relationship',rk,'description',description,25,quote,
          '原文明言亲属／婚姻身份；关系方向为A是B的关系，追叙发生年未定。')
event('zhang_consorte_death', '朱友贞九月册张氏为德妃，张氏当夜去世', 25,
      '九月，壬午，妃疾甚，册为德妃，是夕，卒。',
      [('朱友贞','册张氏为德妃的后梁皇帝'),('梁末帝德妃张氏','九月壬午病重、册为德妃后当夜去世')],
      when='915年九月壬午；未换算公历日', place='后梁宫廷',
      note='册为德妃，不是皇后；主书无享年，新五代史另记二十四岁。')
claim('person',consort,'death_year','梁末帝德妃张氏于915年九月壬午去世。',25,
      '九月，壬午，妃疾甚，册为德妃，是夕，卒。',
      '原文九月壬午在贞明元年（915）条；未反推公历日或生年。')
claim('event','event_zztj_269_0915_zhang_consorte_death','description',
      '《旧五代史》卷八也记壬午册德妃张氏，当夜去世。',25,
      '壬午，正衙命使冊德妃張氏。是夕，妃薨。',
      '旧书与主书记日、册位及死亡相合；前段王彦章官职不并入本事。',old_dc,'corroborates')
claim('person',consort,'description',
      '《新五代史》卷十三记德妃张氏为张归霸女，病重受册，去世时二十四岁。',25,
      '末帝德妃張氏，其父歸霸，事太祖為梁功臣。帝為王時，以婦聘之。帝即位，將冊妃為后，妃請待帝郊天，而帝卒不得郊。貞明元年，[2]妃病甚，帝遽冊為德妃，其夕薨，年二十四。',
      '新书后妃传补享年；其“帝卒不得郊”为后见叙述，不当915年单独事件。',new_dc,'adds')
claim('person',consort,'aliases','梁末帝德妃张氏在《新五代史》写作“末帝德妃張氏”。',25,
      '末帝德妃張氏',
      '规范名用于区别同姓宫妃，繁体保留为检索别名。',new_dc,'corroborates')
# p026: the Kang Prince plot, court favoritism and the separate poisoning attempt.
event('kang_prince_plot', '康王朱友敬遣人伏于寝殿，谋害朱友贞', 26,
      '康王友敬，目重瞳子，自谓当为天子，遂谋作乱。冬，十月，辛亥夜，德妃将出葬，友敬使腹心数人匿于寝殿。帝觉之，跣足逾垣而出，召宿卫兵索殿中，得而手刃之。',
      [('朱友敬','主书称康王友敬，遣人藏于寝殿谋作乱'),('朱友贞','察觉寝殿有人后逃出并诛杀入殿者的后梁皇帝')],
      when='915年十月辛亥夜；未换算公历日', place='后梁宫廷寝殿',
      note='主书作友敬，旧五代史、新五代史作友孜；同为康王、同年同事，暂复用既有朱友敬UUID，异名列入待纸本核。')
claim('event','event_zztj_269_0915_kang_prince_plot','description',
      '《旧五代史》卷八作康王友孜谋反，并记寝殿有人潜入。',26,
      '冬十月辛亥，康王友孜謀反，伏誅。是夕，帝於寢殿熟寐，忽聞禦榻上寶劍有聲，帝遽起視之，而友孜之黨已入於宮中，帝揮之獲免。',
      '康王名与通鉴电子本“友敬”不同；旧书附引《清异录》未作为独立书证。',old_k,'conflicts')
claim('person',people['朱友敬'],'aliases','康王在《旧五代史》《新五代史》作朱友孜。',26,
      '康王友孜謀反',
      '同一康王同一事件的跨书异名，暂纳为别名；旧通鉴名友敬保留，待纸本核是否讹字。',old_k,'conflicts')
claim('event','event_zztj_269_0915_kang_prince_plot','description',
      '《新五代史》卷十三作康王友孜，记其遣刺客入寝，末帝持剑诛之。',26,
      '康王友孜，目重瞳子，嘗竊自負，以為當為天子。貞明元年，末帝德妃薨，將葬，友孜使刺客夜入寢中。',
      '新书与旧书同作友孜，疑非两个不同康王；梦中预警为新书叙事，不写成通鉴事实。',new_k,'conflicts')
event('kang_prince_executed', '朱友贞捕杀康王朱友敬', 26,
      '壬子，捕友敬，诛之。',
      [('朱友贞','下令捕杀康王的后梁皇帝'),('朱友敬','主书称友敬，被捕处死的康王')],
      when='915年十月壬子；未换算公历日', place='后梁宫廷',
      note='通鉴记次日壬子捕诛；旧五代史卷八将“伏诛”并记于辛亥条，日次并列留待核。')
event('zhu_youzhen_favors_zhao_zhang', '朱友贞疏宗室，重用赵岩及德妃张氏亲族', 26,
      '帝由是疏忌宗室，专任赵岩及德妃兄弟汉鼎、汉杰、从兄弟汉伦、汉融，咸居近职，参预谋议，每出兵必使之监护。岩等依势弄权，卖官鬻狱，离间旧将相，敬翔、李振虽为执政，所言多不用。',
      [('朱友贞','疏忌宗室、重用赵岩和张氏亲族的后梁皇帝'),('赵岩','被重用并参与谋议的后梁官员'),('张汉鼎','德妃兄弟之一，获近职参与谋议'),('张汉杰','德妃兄弟之一，获近职参与谋议'),('张汉伦','德妃从兄弟之一，获近职参与谋议'),('张汉融','德妃从兄弟之一，获近职参与谋议'),('敬翔','旧执政者，史称意见多不用'),('李振','旧执政者，史称意见多不用')],
      when='康王之变后；主书带有后续总结，不能全限定915年', place='后梁朝廷', year=None,
      note='此段有“以至于亡”等后见性总评，故事件年未强置915；“兄弟”“从兄弟”未明长幼，暂在角色说明，未建单向关系。')
claim('event','event_zztj_269_0915_zhu_youzhen_favors_zhao_zhang','description',
      '《新五代史》卷十三也以康王事件后疏宗室、信任赵张为后梁败亡原因。',26,
      '由此遂疎弱宗室，而信任趙、張，以至於敗亡。',
      '旧书为后见性评价，不据此把亡国结果记为915年发生。',new_k,'corroborates')
event('liu_xun_poison_attempt', '刘鄩遣诈降者企图毒害晋王，事泄后被杀', 26,
      '刘鄩遣卒诈降于晋，谋赂膳夫以毒晋王。事泄，晋王杀之，并其党五人。',
      [('刘鄩','派兵假意投降并企图毒害晋王的梁将'),('李存勖','毒杀目标，案发后处死来人及同党五人的晋王')],
      when='915年十月条；确日未载', place='晋军',
      note='诈降兵卒、膳夫及五名同党未具名，不擅建具体人物；“杀之并其党五人”不另加未知人数。')
claim('event','event_zztj_269_0915_liu_xun_poison_attempt','description',
      '《旧五代史》卷二十八也记刘鄩遣军士以鸩药行贿晋王膳夫，事发后同党被诛。',26,
      '乃劉鄩密令齎鴆賂帝膳夫，欲置毒於食中，會有告者，索其黨誅之。',
      '旧书置于冬十月；主书仅于本段末概记，未精确到日。',old_28,'corroborates')
# p027–28: Shu palace fire and pardon, separate from the Liang court account.
event('shu_palace_fire', '蜀宫十一月起火，百尺楼所藏宝货焚毁', 27,
      '十一月，己未夜，蜀宫火。自得成都以来，宝货贮于百尺楼，悉为煨烬。',
      [('王建','在位时蜀宫发生火灾的蜀主')],
      when='915年十一月己未夜；未换算公历日', place='成都蜀宫、百尺楼',
      note='主书称百尺楼宝货焚毁；“自得成都以来”是积贮范围，不标为火灾持续时间。')
claim('event','event_zztj_269_0915_shu_palace_fire','description',
      '《新五代史》卷六十三记蜀永平五年十一月大火焚宫室。',27,
      '十一月，大火，焚其宮室。',
      '新书略记火灾；未提百尺楼和宝货，细节仍限主书。',new_63,'corroborates')
event('shu_ruler_refuses_rescue', '王建闭门拒卫兵入救火，次晨命巡太庙神主', 27,
      '诸军都指挥使兼中书令宗侃等帅卫兵欲入救火，蜀主闭门不内。庚申旦，火犹未熄，蜀主出义兴门见群臣，命有司聚太庙神主，分巡都城，言毕，复入宫闭门。将相皆献帷幕饮食。',
      [('王宗侃','率卫兵欲入蜀宫救火的诸军都指挥使'),('王建','闭门未纳卫兵，次晨命巡太庙神主的蜀主')],
      when='915年十一月己未夜至庚申旦；未换算公历日', place='成都蜀宫、义兴门、都城',
      note='主书称“宗侃”，按既有王宗侃身份复用；救火动机和拒入原因未明，不揣测。')
event('shu_amnesty_after_fire', '蜀于十一月壬戌大赦', 28,
      '壬戌，蜀大赦。',
      [('王建','在位时蜀国颁布大赦的蜀主')],
      when='915年十一月壬戌；未换算公历日', place='蜀',
      note='与前段宫火相邻，但主书未明言大赦因火灾而发，不建因果。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25, 29):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷269贞明元年第25—28段连续处理；婚姻追叙与当年册妃分开，康王异名并列，蜀宫火与大赦不强设因果。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=269, year=915,
    primary_source_key=main_early, primary_source_keys=[main_early,main_late],
    paragraphs=[Q[n]['id'] for n in range(25, 29)], next_paragraph=Q[29]['id'],
    coverage='卷269贞明元年九月至十一月第25—28段；张德妃、康王之变、毒杀未遂、蜀宫火和大赦。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[25]['id'],'note':'“初”引婚姻旧事，确年未载；张氏九月受册及死亡为915年事，未立皇后。'},
      {'paragraph_id':Q[26]['id'],'note':'通鉴电子本康王作友敬，旧五代史、新五代史作友孜；同号同年同事复用朱友敬UUID并补朱友孜别名，纸本仍待核。'},
      {'paragraph_id':Q[26]['id'],'note':'“以至于亡”为后见总评，赵张用事叙事不全标作915年；旧书对康王伏诛与通鉴壬子记日不同。'},
      {'paragraph_id':Q[27]['id'],'note':'蜀宫火新旧书细节不一；主书仅说明卫兵欲救、蜀主拒入，不推断原因。'},
      {'paragraph_id':Q[28]['id'],'note':'蜀大赦与宫火先后相邻，尚无明确因果证据。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
