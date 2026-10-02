"""Curate consecutive Tongjian volume 270, year 918, paragraphs 39–44."""
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
specs = [
    ('tongjian-270-918-year-end', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-09/sources/library/tongjian-270-918-year-end', '652cec40', '司马光等'),
    ('tongjian-270-918-to-919-boundary', P / 'sources/library/tongjian-270-918-to-919-boundary', 'fda1f808', '司马光等'),
    ('jiuwudaishi-028-huliupo', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0918/part-09/sources/library/jiuwudaishi-028-huliupo', '652cec40', '薛居正等'),
    ('xinwudaishi-005-huliupo', P / 'sources/library/xinwudaishi-005-huliupo', 'fda1f808', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v270-y0918-p039-p044',
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
lines = (ROOT / 'resources/derived/tongjian/270.txt').read_text().splitlines()
for n in range(39, 45):
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
        citation = f'卷270·贞明四年（918）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_270_0918_10_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'晋王':'李存勖','契丹主':'耶律阿保机','帝':'朱友贞',
            '李存审':'符存审','嗣源':'李嗣源','从珂':'李从珂',
            '王':'李存勖','建及':'王建及','光辅':'周光辅'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷270贞明四年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='918年本段条；确日未载', note='', year=918, place='吴'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_270_0918_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '主书本段未明标月日；他书记载作独立引文，不覆盖主书。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_270_0918_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('jin_reaches_huliupo', '晋王十二月壬戌到胡柳陂，梁军随后追至',39,
      '贺瑰闻晋王已西，亦弃营而踵之。晋王发魏博白丁三万从军，以供营栅之役，所至，营栅立成。壬戌，至胡柳陂。癸亥旦，候者言梁兵自后至矣。',
      [('贺瑰','弃梁营追晋军者'),('晋王','率军至胡柳陂者')],
      when='918年十二月壬戌到胡柳陂；癸亥旦知梁军到',place='胡柳陂',
      note='三万白丁为主书所记营栅役夫，不当作三万骑兵；战斗始于癸亥。')
claim('event','event_zztj_270_0918_jin_reaches_huliupo','time_original',
      '《旧五代史》卷二十八记晋军癸亥至胡柳坡，与主书壬戌至有一日差异。',39,
      '癸亥，次胡柳坡。遲明，梁軍亦至',
      '主书壬戌至、癸亥交战；旧书癸亥至、迟明梁军到。暂保留两书日次。',
      'jiuwudaishi-028-huliupo','conflicts')
event('zhou_dewei_advises_delay', '周德威劝晋王持营待梁军疲，晋王未采纳',39,
      '周德威曰：“贼倍道而来，未有所舍，我营栅已固，守备有馀，既深入敌境，动须万全，不可轻发。此去大梁至近，梁兵各念其家，内怀愤激，不以方略制之，恐难得志。王宜按兵勿战，德威请以骑兵扰之，使彼不得休息，至暮营垒未立，樵爨未具，乘其疲乏，可一举灭也。”王曰：“前在河上恨不见贼，今贼至不击，尚复何待，公何怯也！”顾李存审曰：“敕辎重先发，吾为尔殿后，破贼而去！”即以亲军先出。',
      [('周德威','劝持营待梁军疲者'),('晋王','拒周德威缓战建议并率亲军先出者'),('李存审','受命先遣辎重者')],
      when='918年十二月癸亥战前',place='胡柳陂晋营',
      note='周德威建议来自本段前文，此句体现晋王不从；不把辎重先发写成已安全撤离。')
claim('event','event_zztj_270_0918_zhou_dewei_advises_delay','description',
      '周德威主张按兵、以骑扰梁，使其疲后再攻。',39,
      '王宜按兵勿战，德威请以骑兵扰之，使彼不得休息',
      '这是周德威提出的方案，未获晋王采纳。')
event('jin_initial_assault_wang_yanzhang_retreats', '晋银枪军突梁阵，王彦章部先败趋濮阳',39,
      '王帅银枪都陷其陈，冲荡击斩，往返十馀里。行营左厢马军都指挥使、郑州防御使王彦章军先败，西走趣濮阳。',
      [('晋王','率银枪都突击梁阵者'),('王彦章','所部先败向濮阳退者')],
      when='918年十二月癸亥胡柳陂初战',place='胡柳陂、濮阳方向',
      note='王彦章所部先败，但紧随其后的晋军辎重与幽州阵又溃，战役未就此结束。')
event('jin_baggage_rout_zhou_dewei_dies', '晋辎重惊溃冲乱幽州军，周德威父子及王缄阵亡',39,
      '晋辎重在陈西，望见梁旗帜，惊溃，入幽州陈，幽州兵亦扰乱，自相蹈藉；周德威不能制，父子皆战死。魏博节度副使王缄与辎重俱行，亦死。',
      [('周德威','幽州军乱中与子阵亡者'),('王缄','随晋军辎重而阵亡者')],
      when='918年十二月癸亥胡柳陂初战',place='胡柳陂晋阵西侧',
      note='原文未列周德威此时阵亡儿子的名字；不自动指为周光辅，后者本段下一处受官。')
claim('event','event_zztj_270_0918_jin_baggage_rout_zhou_dewei_dies','description',
      '《新五代史》卷五概称晋军初战大败、周德威阵亡。',39,
      '戰于胡柳，晉軍大敗，周德威死之。',
      '与主书前半战局相合；该书下文亦记晋军再败梁军，不能截取前句当最终胜负。',
      'xinwudaishi-005-huliupo','corroborates')

event('jin_regroups_takes_hill', '晋王收散兵后夺胡柳陂土山',40,
      '晋王据高丘收散兵，至日中，军复振。陂中有土山，贺瑰引兵据之。晋王谓将士曰：“今日得此山者胜，吾与汝曹夺之。”即引骑兵先登，李从珂与银枪大将王建及以步卒继之，梁兵纷纷而下，遂夺其山。',
      [('晋王','整军并率骑兵攻土山者'),('贺瑰','率梁军先占土山者'),
       ('李从珂','率部继进者'),('王建及','银枪大将、率步卒继进者')],
      when='918年十二月癸亥日中前后',place='胡柳陂土山',
      note='王建及不是当年六月去世的前蜀王建；初战阵乱后晋军重整夺山。')
claim('event','event_zztj_270_0918_jin_regroups_takes_hill','description',
      '《旧五代史》卷二十八亦记梁先据土山、晋军攻占。',40,
      '帝率軍先登，銀槍步兵繼進，遂奪其山。',
      '补书与主书的夺山次序相合，细节详略有别。',
      'jiuwudaishi-028-huliupo','corroborates')

event('jin_council_decides_evening_attack', '阎宝、李嗣昭、王建及劝晋王当日再攻梁军',41,
      '王愕然曰：“非公等言，吾几误计。”',
      [('阎宝','主张乘高下击者'),('李嗣昭','主张精骑扰敌、乘退追击者'),
       ('王建及','请率众攻疲梁军者'),('晋王','听诸将建议改变退营意向者')],
      when='918年十二月癸亥傍晚',place='胡柳陂土山',
      note='各将策略不完全相同；晋王采纳继续作战，而不是已经在此句取胜。')
claim('event','event_zztj_270_0918_jin_council_decides_evening_attack','description',
      '阎宝指出王彦章骑兵已入濮阳，梁步卒暮晚有归志。',41,
      '王彦章骑兵已入濮阳，山下惟步卒，向晚皆有归志',
      '为阎宝战场判断，不作为精确兵种清点。')
event('jin_evening_counterattack_liang_defeated', '晋军傍晚再攻梁阵，梁军大败',41,
      '嗣昭、建及以骑兵大呼陷陈，诸军继之，梁兵大败。元城令吴琼、贵乡令胡装，各帅白丁万人，于山下曳柴扬尘，鼓噪以助其势。',
      [('李嗣昭','率骑兵突梁阵者'),('王建及','率骑兵突梁阵者'),
       ('吴琼','率元城白丁助战者'),('胡装','率贵乡白丁助战者')],
      when='918年十二月癸亥傍晚',place='胡柳陂土山及山西',
      note='主书先记晋初乱、后记晋反击胜；白丁曳柴扬尘为助势行动。')
claim('event','event_zztj_270_0918_jin_evening_counterattack_liang_defeated','description',
      '《新五代史》卷五也记梁军暮休土山、晋军再击使其败。',41,
      '梁軍暮休于土山，晉軍復擊，大敗之',
      '补书概述再战结局，与主书同为晋反击胜，不覆盖前半晋军大败。',
      'xinwudaishi-005-huliupo','corroborates')
claim('event','event_zztj_270_0918_jin_evening_counterattack_liang_defeated','description',
      '《资治通鉴》称此战两军损失都很重，并给出梁军死者“几三万人”的估数。',41,
      '梁兵自相腾藉，弃甲山积，死亡者几三万人。装，证之曾孙也。是日，两军所丧士卒各三之二',
      '仅呈现原书数字，不将“几三万人”“各三之二”当作现代核算所得。')

event('li_cunxu_honors_zhou_guangfu', '晋王悲周德威阵亡，授其子周光辅岚州刺史',42,
      '晋王还营，闻周德威父子死，哭之恸，曰：“丧吾良将，是吾罪也！”以其子幽州中军兵马使光辅为岚州刺史。',
      [('晋王','闻周德威死而授其子官者'),('周德威','已阵亡的幽州将领'),('光辅','周德威之子、受任岚州刺史者')],
      when='918年十二月癸亥战后；确日未载',place='晋营、岚州',
      note='周光辅是战后受官的儿子，不推定其为本段“父子皆战死”中的阵亡儿子。')
father=person('周德威',42,'周光辅之父','以其子幽州中军兵马使光辅为岚州刺史')
son=person('光辅',42,'周德威之子','以其子幽州中军兵马使光辅为岚州刺史')
rk='relationship_zztj_270_0918_zhou_dewei_father_of_guangfu'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=son,
    relation_type='父亲',description='周德威是周光辅的父亲。',status='draft'))
claim('person_relationship',rk,'description','周德威是周光辅的父亲。',42,
      '以其子幽州中军兵马使光辅为岚州刺史',
      '“其子”承周德威；光辅战后受官，不是前文已阵亡的未具名儿子。')
event('li_siyuan_crosses_north_in_confusion', '李嗣源误信晋王北渡，遂渡河北去',42,
      '李嗣源与李从珂相失，见晋军挠败，不知王所之，或曰：“王已北渡河矣。”嗣源遂乘冰北渡，将之相州。',
      [('李嗣源','因误信消息而北渡者'),('李从珂','与李嗣源失散而仍在晋军者')],
      when='918年十二月癸亥胡柳陂战中',place='胡柳陂、渡河往相州',
      note='这是战场失联和误传后的北渡，不记为投梁；李从珂当天仍参与夺山晚战。')
event('jin_captures_puyang', '晋王十二月甲子攻取濮阳',42,
      '甲子，晋王进攻濮阳，拔之。',
      [('晋王','率军攻取濮阳者')],
      when='918年十二月甲子',place='濮阳',
      note='甲子为胡柳陂癸亥战次日，和胡柳陂两阶段战斗分开。')
event('li_siyuan_returns_puyang_rebuked', '李嗣源知晋胜后回见晋王并受责',42,
      '李嗣源知晋军之捷，复来见王于濮阳，王不悦，曰：“公以吾为死邪？渡河安之！”嗣源顿首谢罪。',
      [('李嗣源','知胜后回见并谢罪者'),('晋王','责李嗣源渡河者')],
      when='918年十二月甲子攻取濮阳后；确日未载',place='濮阳',
      note='主书后称晋王待李嗣源稍薄，为关系变化评价；不误作本次诛罚。')

event('salaabo_flees_to_jin', '契丹北大王撒剌阿拨率众奔晋并被晋王收为假子',43,
      '撒剌阿拨帅其众奔晋，晋王厚遇之，养为假子，任为刺史',
      [('撒剌阿拨','率众投晋并受任刺史者'),('晋王','厚遇并收其为假子者')],
      when='本段“初”所追叙；确年未载',year=None,place='契丹、晋',
      note='此前谋乱、囚释与投晋未明确发生在918年，不强定年；假子有原文明证。')
father=person('晋王',43,'收撒剌阿拨为假子者','晋王厚遇之，养为假子')
child=person('撒剌阿拨',43,'晋王所收假子','晋王厚遇之，养为假子')
rk='relationship_zztj_270_0918_li_cunxu_adoptive_father_salaabo'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=child,
    relation_type='养父',description='李存勖收撒剌阿拨为假子。',status='draft'))
claim('person_relationship',rk,'description','李存勖收撒剌阿拨为假子。',43,
      '晋王厚遇之，养为假子','本句有明确养父子身份；发生确年未载。')
event('salaabo_family_comes_during_battle', '胡柳陂之战时撒剌阿拨妻子来奔晋',43,
      '胡柳之战，以其妻子来奔。',
      [('撒剌阿拨','妻子于胡柳战时来奔晋者')],
      when='918年十二月胡柳陂之战',place='晋营',
      note='来奔者是其妻和子女，撒剌阿拨此前已奔晋；妻子本段未具名。')

event('daliang_panics_after_huliupo', '胡柳陂败报至大梁，梁帝令市民登城并欲奔洛阳',44,
      '京城大恐。帝驱市人登城，又欲奔洛阳，遇夜而止。',
      [('帝','因败报欲奔洛阳但未成行的梁帝')],
      when='918年十二月胡柳陂战后；确日未载',place='大梁',
      note='“欲奔洛阳”是意图，原文说遇夜而止，不记为已经迁都或出走。')
claim('event','event_zztj_270_0918_daliang_panics_after_huliupo','description',
      '《旧五代史》卷二十八也记败卒入大梁不满千人，城中驱市人守城。',44,
      '梁人大恐，驅市人以守。其殘眾奔歸汴者不滿千人',
      '旧书支持败报入城后的恐慌与部分残兵数字；不能把不满千人当梁军全部余部。',
      'jiuwudaishi-028-huliupo','adds')
claim('event','event_zztj_270_0918_daliang_panics_after_huliupo','description',
      '主书记梁军伤散后经过月余才再能成军。',44,
      '伤夷逃散，各归乡里，月馀仅能成军。',
      '这是后续时长，可能跨919年界，不另造918年单日军队恢复事件。')
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(39, 45):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷270贞明四年第39—44段；胡柳陂之战阶段、战后人物与德胜渡大梁惊恐。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=270, year=918,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(39, 45)], next_paragraph='zztj-v270-y0919-p001',
    coverage='卷270贞明四年第39—44段；胡柳陂初战、晋军重整夺土山与反击、周德威阵亡、濮阳得失、契丹投晋追叙及大梁城内惊恐。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id': Q[39]['id'], 'note': '胡柳陂先有梁将王彦章军败退，随后晋辎重冲乱幽州阵、周德威父子及王缄阵亡；不概括为单一方从头胜到尾。'},
      {'paragraph_id': Q[41]['id'], 'note': '两军死亡各三分之二和梁军几三万人为主书数字，保留史家原述；不现代估算。王建及不是前蜀王建。'},
      {'paragraph_id': Q[42]['id'], 'note': '李嗣源渡河北去是误信晋王已北渡后的动作，后来知捷回见并受责，非临阵投梁。'},
      {'paragraph_id': Q[43]['id'], 'note': '撒剌阿拨早先谋乱、囚释、投晋及收养是“初”追叙，确年未载；胡柳之战妻子来奔是当前事。'},
      {'paragraph_id': Q[44]['id'], 'note': '大梁惊恐和朱友贞欲奔洛阳为当时反应；“月馀仅能成军”跨年可能，未强定为918年单日。'}
    ]), ensure_ascii=False, indent=2) + '\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
