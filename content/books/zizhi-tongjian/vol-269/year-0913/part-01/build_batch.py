"""Curate Tongjian 269, year 913, consecutive paragraphs 1-4."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 5))
main = 'tongjian-269-913-december'
old_wang = 'jiuwudaishi-023-wang-jingren'
old_liushouguang = 'jiuwudaishi-135-liu-shouguang'
old_jinreturn = 'jiuwudaishi-028-jin-return'
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0913-p001-p004',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main, P / 'sources/library' / main, '8eb6cf39', '司马光等'),
    (old_wang, P / 'sources/library' / old_wang, '8eb6cf39', '薛居正等'),
    (old_liushouguang, P / 'sources/library' / old_liushouguang, '8eb6cf39', '薛居正等'),
    (old_jinreturn, P / 'sources/library' / old_jinreturn, '8eb6cf39', '薛居正等'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main,)}
for n in range(1,5):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/269.txt').read_text().splitlines()[row['source_line']-1]
    assert any(row['text'] in text for text in primary_texts.values()),n

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
           '王景仁':'王茂章','张宗奭':'张全义','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','硃汉宾':'朱汉宾','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
aliases.update({'元膺':'王宗懿','蜀主':'王建','帝':'朱友贞','硃友谦':'朱友谦',
                '鄴王':'杨师厚','晋王':'李存勖','守光':'刘守光',
                '行珪':'高行珪','行周':'高行周','嗣源':'李嗣源',
                '存矩':'李存矩','传瓘':'钱传瓘','传璙':'钱传璙',
                '吴越王镠':'钱镠','从珂':'李从珂','魏氏':'魏氏（李从珂母）'})
aliases.update({'刘光浚':'刘光濬','光浚':'刘光濬','李存审':'符存审',
                '王德明':'张文礼','赵王':'王镕','传瓘':'钱传瓘',
                '师厚':'杨师厚','守奇':'刘守奇','万进':'张万进'})
aliases.update({'元膺':'王宗懿','太子':'王宗懿','蜀主':'王建',
                '道袭':'唐道袭','宗翰':'王宗翰','宗侃':'王宗侃',
                '宗贺':'王宗贺','宗黯':'王宗黯','赵王镕':'王镕',
                '晋王':'李存勖','高季兴':'高季昌'})
aliases.update({'吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘',
                '传璙':'钱传璙','传瑛':'钱传瑛','蜀主':'王建',
                '宗衍':'王宗衍','宗辂':'王宗辂','宗杰':'王宗杰',
                '宗侃':'王宗侃','晋王':'李存勖','守光':'刘守光',
                '朱温':'朱温','王景仁':'王茂章'})
aliases.update({'硃瑾':'朱瑾','硃景浮':'朱景浮','王景仁':'王茂章',
                '景仁':'王茂章','守光':'刘守光','晋王':'李存勖',
                '越王镕':'王镕','赵王镕':'王镕','仁恭':'刘仁恭'})
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main,) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main,):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·乾化三年（913）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_269_0913_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main,):
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
                   description=f'《资治通鉴》卷269乾化三年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=913):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_269_0913_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '913年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_269_0913_' + code + '_' + pk
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

event('zhaobu_wu_withdraws', '徐温、朱瑾率吴军拒梁，赵步初战失利', 1,
      '十二月，吴镇海节度使徐温、平卢节度使硃瑾帅诸将拒之，遇于赵步。吴征兵未集，温以四千馀人与景仁战，不胜而却。景仁引兵乘之，将及于隘，吴吏士皆失色，',
      [('徐温','率未集结完毕的吴军四千余人与梁军交战后退'),('朱瑾','随徐温率吴军拒梁的平卢节度使'),('王茂章','以王景仁之名率梁军乘胜追击')],
      when='913年十二月；确日未载',place='赵步',
      note='赵步初战吴军不胜而却，并非全段战役最终胜负；“四千馀人”是徐温初战兵力。')
event('chen_shao_countercharge', '陈绍在隘口率吴军反击，梁军退', 1,
      '左骁卫大将军宛丘陈绍援枪大呼曰：“诱敌太深，可以进矣！”跃马还斗，众随之，梁兵乃退。温拊其背曰：“非子之智勇，吾几困矣！”赐之金帛，绍悉以分麾下。',
      [('陈绍','在隘口率吴军回击并分赏麾下的左骁卫大将军'),('徐温','赞陈绍并赐金帛的吴军统帅')],
      when='913年十二月赵步交战时',place='赵步附近隘口',
      note='“诱敌太深”是陈绍当场激励军士的说辞，不推定原定诱敌计划；赏金帛后分给麾下。')
event('huoqiu_wu_victory', '吴军集结后于霍丘大败梁军，王景仁率数骑断后', 1,
      '吴兵既集，复战于霍丘，梁兵大败。王景仁以数骑殿，吴人不敢逼。',
      [('徐温','率吴军在霍丘再战的统帅'),('朱瑾','参与吴军拒梁行动的将领'),('王茂章','以王景仁之名率数骑为败退梁军断后')],
      when='913年十二月；确日未载',place='霍丘',
      note='主书记梁兵大败，王景仁本人率数骑殿后；“不敢逼”只记吴军未迫近，不推为梁军全军有序撤出。')
claim('event','event_zztj_269_0913_huoqiu_wu_victory','description',
      '《旧五代史》卷二十三王景仁传称其于霍丘俘吴将、力战引兵还，与主书梁军大败侧重不同。',1,
      '至霍丘接戰，擒賊將袁叢、王彥威、王璠等送京師。俄而朱瑾以大軍至，景仁力戰不屈，常以數騎身先奮擊，寇不敢逼，乃引兵還。',
      '旧书梁方将领列传带胜绩叙述，主书吴方胜利；不把两个战果简单相加为同一无争议结果。',old_wang,'conflicts')
event('zhu_jingfu_moves_markers', '朱景浮移淮河涉水标记，梁军败退时误入深渊', 1,
      '梁之渡淮而南也，表其可涉之津。霍丘守将硃景浮表于木，徙置深渊。及梁兵败还，望表而涉，溺死者太半，吴人聚梁尸为京观于霍丘。',
      [('朱景浮','移动涉水标记至深处的霍丘守将'),('王茂章','其所部败还渡淮遭水险的梁将')],
      when='913年十二月霍丘战前后',place='霍丘、淮水',
      note='“太半”是史书对败退梁兵中溺死者比例的描述，无基数不换算绝对人数；“京观”是史载堆尸标志。')
claim('event','event_zztj_269_0913_zhu_jingfu_moves_markers','description',
      '《旧五代史》卷二十三所引《九国志·朱景传》也记移动涉水标记致梁军溺死，但作朱景、王茂章等称呼。',1,
      '王茂章來寇，度淮水可涉處立表識之，景易置於深潭水中，立表浮木之上。茂軍敗，望表而涉，溺死者大半，積其屍為京觀。',
      '此段是旧书转引他书，不能作为与其所引《九国志》独立的第二证据；主书“朱景浮”与引文“朱景”是否同人待纸本核。',old_wang,'adds')
event('zhou_dewei_lulong', '晋王授周德威卢龙节度使兼侍中', 2,
      '庚午，晋王以周德威为卢龙节度使，兼侍中，',
      [('李存勖','任命周德威的晋王'),('周德威','获任卢龙节度使兼侍中')],
      when='913年十二月庚午',place='卢龙')
event('li_siben_zhenwu', '晋王授李嗣本振武节度使', 2,
      '以李嗣本为振武节度使。',
      [('李存勖','任命李嗣本的晋王'),('李嗣本','获任振武节度使')],
      when='913年十二月庚午',place='振武')
claim('event','event_zztj_269_0913_zhou_dewei_lulong','description',
      '《旧五代史》卷二十八亦记十二月庚午授周德威幽州节度使。',2,
      '十二月庚午，墨製授周德威幽州節度使。',
      '“幽州节度使”与主书“卢龙节度使”官号用法不同，先保留原书措辞。',old_jinreturn,'adds')
event('liu_shouguang_captured', '张师造发现刘守光藏身处，刘守光与家人被擒', 3,
      '燕主守光将奔沧州就刘守奇，涉寒，足肿，且迷失道。至燕乐之境，昼匿坑谷，数日不食，令妻祝氏乞食于田父张师造家。师造怪妇人异状，诘知守光处，并其三子擒之。',
      [('刘守光','逃往沧州途中藏于燕乐，后被擒的燕主'),('刘守奇','刘守光原拟投奔的沧州将领'),('祝氏（刘守光妻）','受命到张师造家乞食的刘守光妻'),('张师造','发现藏身处并擒刘守光及三子者')],
      when='913年十二月癸酉前；确日未载',place='燕乐',
      note='史书说明涉寒足肿、迷失道、数日未食；不是对其伤病的现代诊断。三子主书未具名，不据此段新建三人。')
claim('event','event_zztj_269_0913_liu_shouguang_captured','description',
      '《旧五代史》卷一百三十五亦记祝氏乞食张师造家、刘守光被擒，并补妻李氏、祝氏及子继珣等姓名。',3,
      '至燕樂縣，匿於坑谷，令妻祝氏乞食於田父張師造家，怪婦人異狀，詰之，遂俱擒焉。',
      '旧书与主书捕获地点和方式相合；旧书补全家眷名单，未无证据地投射到主书“其三子”名字。',old_liushouguang,'corroborates')
event('liu_shouguang_brought_to_jin', '刘守光癸酉被送至晋王宴席，与刘仁恭置馆舍', 3,
      '癸酉，晋王方宴，将吏擒守光适至，王语之曰：“主人何避客之深邪！”并仁恭置之馆舍，以器服膳饮赐之。',
      [('李存勖','宴中接到刘守光并安置父子于馆舍的晋王'),('刘守光','被押至晋王处并入馆舍的燕主'),('刘仁恭','与其子同被安置馆舍')],
      when='913年十二月癸酉',place='幽州',
      note='晋王此时安置父子并供给饮食，不等于赦免；后续处置按后文另录。')
event('wang_jian_lubu', '王缄误将露布文字直接写在布上，晋王命人曳行', 3,
      '王命掌书记王缄草露布，缄不知故事，书之于布，遣人曳之。',
      [('李存勖','命王缄草露布的晋王'),('王缄','按文字面把露布写在布上并让人拖行的掌书记')],
      when='913年十二月癸酉后；确日未载',place='幽州',
      note='“不知故事”为主书解释；只记录本次露布制作及展示，不推断王缄一生学识。')
event('jin_route_via_zhending', '王镕、王处直请晋王由中山真定走井陉，晋王从之', 4,
      '晋王欲自云、代归，越王镕及王处直请由中山、真定趣井陉，王从之。',
      [('李存勖','采纳经中山真定井陉路线的晋王'),('王镕','同王处直建议路线的赵王'),('王处直','同王镕建议路线的定州将领')],
      when='913年十二月庚辰前；确日未载',place='中山、真定、井陉',
      note='主书作“越王镕”，依上下文与既有赵王王镕对为同一人，疑底本“赵”讹“越”；原字保留待纸本核。')
claim('event','event_zztj_269_0913_jin_route_via_zhending','description',
      '《旧五代史》卷二十八作镇州王镕、定州王处直请晋王由井陉西行。',4,
      '時鎮州王鎔、定州王處直遣使請帝由井陘而西，許之。',
      '旧书支持“王镕”为镇州赵王，主书“越王镕”疑讹；旧书作遣使而主书省略使者，分别保留。',old_jinreturn,'adds')
event('jin_leaves_youzhou', '晋王庚辰离幽州，刘仁恭父子被荷校押行', 4,
      '庚辰，晋王发幽州，刘仁恭父子皆荷校于露布之下。守光父母唾其面而骂之曰：“逆贼，破我家至此！”守光俯首而已。',
      [('李存勖','率军离幽州的晋王'),('刘仁恭','受拘押随晋王军离幽州的刘守光父'),('刘守光','受拘押随军并遭父母斥责')],
      when='913年十二月庚辰',place='幽州',
      note='“父母”未具名，未另建实体；引语为其父母斥责，不当作司法定罪结论。')
event('jin_route_dingzhou_xingtang', '晋王经定州谒北岳庙至行唐，王镕迎谒', 4,
      '甲申，至定州，舍于关城。丙戌，晋王与王处直谒北岳庙。是日，至行唐，赵王镕迎谒于路。',
      [('李存勖','由定州经北岳庙至行唐的晋王'),('王处直','与晋王谒北岳庙的定州将领'),('王镕','在行唐路上迎谒晋王的赵王')],
      when='913年十二月甲申到定州、丙戌谒庙与到行唐',place='定州、北岳庙、行唐',
      note='两日行程按原文分别注明；“是日”指丙戌。')
claim('event','event_zztj_269_0913_jin_route_dingzhou_xingtang','description',
      '《旧五代史》卷二十八亦记甲申定州、次日曲阳、北岳祠、衡唐王镕迎谒。',4,
      '甲申，次定州，舍於關城。翌日，次曲陽，與王處直謁北嶽祠。是日，次衡唐，鎮州王鎔迎謁於路。',
      '旧书“翌日”与主书丙戌（甲申后隔一日）日期不合；“衡唐／行唐”地名字形亦不同，待纸本与历日核。',old_jinreturn,'conflicts')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,5):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269乾化三年十二月第1—4段连续处理；赵步—霍丘、刘守光被擒、晋王回师；旧史梁吴胜负异说保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=913,
    primary_source_key=main,primary_source_keys=[main],
    paragraphs=[Q[n]['id'] for n in range(1,5)],next_paragraph='zztj-v269-y0914-p001',
    coverage='卷269乾化三年十二月第1—4段，梁吴赵步霍丘战事、晋任命、刘守光被擒和晋王回师。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[1]['id'],'note':'霍丘战果通鉴作梁兵大败；旧五代史卷23王景仁传强调擒吴将、力战还军，所引九国志又记移标溺死。转引书证非独立原始证。'},
      {'paragraph_id':Q[3]['id'],'note':'旧五代史卷135补刘守光妻李氏、祝氏及子姓名；主书只具名祝氏、其三子未具名。'},
      {'paragraph_id':Q[4]['id'],'note':'主书“越王镕”疑“赵王镕”讹字；旧五代史作镇州王鎔。主书丙戌谒北岳，旧书作甲申后翌日，日期与衡唐／行唐字形异说待核。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
