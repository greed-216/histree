"""Curate Tongjian 268, year 913, consecutive paragraphs 21-30."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 50))
main2 = 'tongjian-268-913-coup'
main3 = 'tongjian-268-913-midyear'
old_siege = 'jiuwudaishi-028-yan-siege'
old_ying = 'jiuwudaishi-028-yingzhou-zhaozhou'
old_zhao = 'jiuwudaishi-008-liang-zhao'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0913-p021-p030',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main2, P.parent / 'part-01/sources/library' / main2, 'be135c91', '司马光等'),
    (main3, P / 'sources/library' / main3, '0c7bdab7', '司马光等'),
    (old_siege, P / 'sources/library' / old_siege, '514bab10', '薛居正等'),
    (old_ying, P / 'sources/library' / old_ying, '514bab10', '薛居正等'),
    (old_zhao, P / 'sources/library' / old_zhao, '514bab10', '薛居正等'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main2,main3)}
for n in range(21,31):
    row=Q[n]
    assert row['text']==(ROOT/'resources/derived/tongjian/268.txt').read_text().splitlines()[row['source_line']-1]
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
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main2,main3) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main2,main3):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化三年（913）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0913_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main2,main3):
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
                   description=f'《资治通鉴》卷268乾化三年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=913):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0913_' + code
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
        edge = 'participation_zztj_268_0913_' + code + '_' + pk
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

event('zhou_dewei_south_gate', '周德威进军幽州南门', 21,
      '晋周德威进军逼幽州南门。',
      [('周德威','率晋军逼近幽州南门')],
      when='913年四月壬辰前；确日未载',place='幽州南门')
event('liu_shouguang_peace_appeal', '刘守光向周德威请和遭拒，再求哀后呈晋王', 21,
      '壬辰，燕主守光遣使致书于德威以请和，语甚卑而哀。德威曰：“大燕皇帝尚未郊天，何雌伏如是邪！予受命讨有罪者，结盟继好，非所闻也。”不答书。守光惧，复遣人祈哀，德威乃以闻于晋王。',
      [('刘守光','两次向周德威请和或祈哀的燕主'),('周德威','拒绝答书，后来把请求上报晋王'),('李存勖','收到周德威上报的晋王')],
      when='913年四月壬辰及其后',place='幽州',
      note='第一次使者主书未具名；旧五代史卷28作王遵化，作为书证补充。引语是周德威讥讽，不当作事实判断。')
claim('event','event_zztj_268_0913_liu_shouguang_peace_appeal','description',
      '《旧五代史》卷二十八称首位求和使者为王遵化。',21,
      '壬辰，劉守光遣使王遵化致書哀祈於德威，德威戲遵化曰：「大燕皇帝尚未郊天，何怯劣如是耶！」守光再遣哀祈，德威乃以狀聞。',
      '旧书补使者姓名；主书与旧书讥讽措辞不同，未将王遵化误作主书具名人物。',old_siege,'adds')
event('qian_chuanguan_qianqiuling', '钱传瓘于千秋岭断吴军后路并大败吴军', 22,
      '千秋岭道险狭，钱传瓘使人伐木以断吴军之后而击之，吴军大败，虏李涛及士卒三千馀人以归。',
      [('钱传瓘','命伐木断吴军后路并击败吴军的吴越将领'),('李涛','此战被吴越军俘获的吴将')],
      when='913年四月；确日未载',place='千秋岭',
      note='原文“三千馀人”为俘虏李涛及士卒的人数，未给吴军总损失或死亡数。')
event('liu_guangjun_pingzhou', '刘光濬攻下平州并执张在吉', 23,
      '己亥，晋刘光浚拔燕平州，执刺史张在吉。',
      [('刘光濬','以“刘光浚”字形攻下燕平州的晋将'),('张在吉','平州被攻下后遭俘的燕刺史')],
      when='913年四月己亥',place='平州',
      note='“浚”与前段“濬”是繁简／异体同一字的规范化，复用刘光濬稳定实体，原文仍为“光浚”。')
claim('event','event_zztj_268_0913_liu_guangjun_pingzhou','description',
      '《旧五代史》卷二十八亦记己亥刘光浚攻下平州并获张在吉。',23,
      '己亥，劉光浚攻下平州，獲刺史張在吉。',
      '旧书本段字形“浚”，按同日同地事迹对为一人；保留通鉴前段“濬”字形。',old_siege,'corroborates')
event('liu_guangjun_yingzhou', '刘光濬进攻营州，杨靖以城降', 23,
      '五月，光浚攻营州，刺史杨靖降。',
      [('刘光濬','进攻燕营州的晋将'),('杨靖','向晋军投降的燕营州刺史')],
      when='913年五月；确日未载',place='营州',
      note='《旧五代史》卷28记五月壬寅朔；主书未给日，保留月级时间。')
claim('event','event_zztj_268_0913_liu_guangjun_yingzhou','description',
      '《旧五代史》卷二十八记五月壬寅朔刘光浚迫营州、杨靖以城降。',23,
      '五月壬寅朔，光浚進迫營州，刺史楊靖以城降。',
      '旧书补日与“以城降”细节；与主书月、人与地点相合。',old_ying,'adds')
event('wang_kai_chancellor', '王建任王锴中书侍郎、同平章事', 24,
      '乙巳，蜀主以兵部尚书王锴为中书侍郎、同平章事。',
      [('王建','任命王锴的前蜀皇帝'),('王锴','由兵部尚书转中书侍郎、同平章事')],
      when='913年五月乙巳',place='前蜀')
event('yang_liu_raids_zhao', '杨师厚与刘守奇率梁军十万侵赵并焚掠', 25,
      '杨师厚与刘守奇将汴、滑、徐、兗、魏、博、邢、洺之兵十万大掠赵境，师厚自柏乡入攻土门，趣赵州，守奇自贝州人趣冀州，所过焚掠。',
      [('杨师厚','率梁军自柏乡攻土门趋赵州'),('刘守奇','率梁军由贝州趋冀州')],
      when='913年五月；确日未载',place='赵境、土门、冀州',
      note='“十万”为主书称总兵力；底本“自贝州人趣”疑“入”讹为“人”，引用原字，路线按上下文谨慎概述。')
claim('event','event_zztj_268_0913_yang_liu_raids_zhao','description',
      '《旧五代史》卷八称杨师厚、刘守奇五月乙巳率十万讨镇州。',25,
      '五月乙巳，天雄軍節度使楊師厚及劉守奇率魏、博、邢、洺、徐、兗、鄆、滑之眾十萬討鎮州。',
      '旧书与主书兵力一致，但列举州军不同（旧书鄆、主书汴），分别保留。',old_zhao,'conflicts')
event('yang_shihou_zhenzhou', '杨师厚抵镇州并焚其关城', 25,
      '庚戌，师厚至镇州，营于南门外，燔其关城。',
      [('杨师厚','率梁军抵镇州南门外并焚关城')],
      when='913年五月庚戌',place='镇州南门',
      note='焚的是关城，未推为焚尽镇州全城。')
event('yang_liu_xiabo', '杨师厚退军下博，刘守奇会攻并拔下博', 25,
      '壬子，师厚自九门退军下博，守奇引兵与师厚会攻下博，拔之。',
      [('杨师厚','自九门退军下博并与刘守奇会攻'),('刘守奇','会攻并拔下博')],
      when='913年五月壬子',place='九门、下博',
      note='主书明确二人会攻；旧书卷八把“陷下博”归于刘守奇一军，不改写主书。')
claim('event','event_zztj_268_0913_yang_liu_xiabo','description',
      '《旧五代史》卷八称刘守奇一军掠衡水、阜城并陷下博。',25,
      '劉守奇以一軍自貝州掠冀州衡水、阜城，陷下博。',
      '旧书主语侧重刘守奇，主书说杨师厚会攻，过程异说并列。',old_zhao,'conflicts')
event('zhao_requests_relief', '赵王向周德威告急，晋赵两军共拒梁军', 25,
      '晋将李存审、史建瑭戍赵州，兵少，赵王告急于周德威。德威遣骑将李绍衡会赵将王德明同拒梁军。',
      [('符存审','以李存审之名戍赵州的晋将'),('史建瑭','与李存审戍赵州的晋将'),('王镕','向周德威告急的赵王'),('周德威','遣李绍衡赴援的晋将'),('李绍衡','奉命会赵将拒梁军的晋骑将'),('张文礼','以王德明之名与李绍衡同拒梁军的赵将')],
      when='913年五月；确日未载',place='赵州',
      note='李存审沿既有符存审主体，王德明沿张文礼主体；旧书另记史建瑭率五百骑自赵州入镇州。')
claim('event','event_zztj_268_0913_zhao_requests_relief','description',
      '《旧五代史》卷八记史建瑭自赵州率五百骑进入镇州。',25,
      '晉將史建瑭自趙州領騎五百入於鎮州，師厚知其有備，自九門移軍於下博。',
      '旧书补史建瑭具体调动；主书仅说其与李存审戍赵州，不把旧书补充冒充主书原句。',old_zhao,'adds')
event('yang_liu_cangzhou', '梁军逼沧州，张万进请求迁镇，杨师厚表请改镇', 25,
      '师厚、守奇自弓高渡御河而东，逼沧州，张万进惧，请迁于河南；师厚表徙万进镇青州，以守奇为顺化节度使。',
      [('杨师厚','与刘守奇逼沧州并表请改镇'),('刘守奇','随杨师厚渡御河逼沧州，获表请任顺化节度使'),('张万进','因梁军逼沧州而请迁河南')],
      when='913年五月；确日未载',place='弓高、沧州、青州',
      note='表请是上奏阶段，张万进正式平卢任命见第30段；旧书卷8称张万进“送款”并刘守奇为沧州节度使，异说保留。')
claim('event','event_zztj_268_0913_yang_liu_cangzhou','description',
      '《旧五代史》卷八称张万进送款，杨师厚请以刘守奇为沧州节度使。',25,
      '張萬進懼，送款，師厚表請以萬進為青州節度使，以劉守奇為滄州節度使。',
      '主书称万进请迁河南、刘守奇顺化节度使；旧书作送款、沧州节度使，措辞与官号均保留待核。',old_zhao,'conflicts')
event('wu_guangde_garrison', '吴遣花虔、涡信屯广德，钱传瓘进攻', 26,
      '吴遣宣州副指挥使花虔将兵会广德镇遏使涡信屯广德，将复寇衣锦军。吴越钱传瓘就攻之。',
      [('花虔','率吴军与涡信屯广德的宣州副指挥使'),('涡信','与花虔同屯广德的镇遏使'),('钱传瓘','进攻广德吴军的吴越将领')],
      when='913年五月后至六月前；确日未载',place='广德',
      note='“将复寇衣锦军”表示吴军计划，未记再次攻衣锦军已发生。')
event('zhang_chengye_yanzhou_council', '晋王遣张承业赴幽州与周德威议军事', 27,
      '六月，壬申朔，晋王遣张承业诣幽州，与周德威议军事。',
      [('李存勖','派张承业赴幽州的晋王'),('张承业','受派与周德威议军事'),('周德威','在幽州与张承业议军事')],
      when='913年六月壬申朔',place='幽州',
      note='主书仅言议军事，未记具体决策内容。')
event('du_guangting_titles', '王建加杜光庭官爵、封蔡国公并进号广成先生', 28,
      '丙子，蜀主以道士杜光庭为金紫光禄大夫、左谏议大夫，封蔡国公，进号广成先生。光庭博学善属文，蜀主重之，颇与议政事。',
      [('王建','授杜光庭官爵并与其议政的前蜀皇帝'),('杜光庭','前蜀道士，受封蔡国公、广成先生并参与政事商议')],
      when='913年六月丙子',place='前蜀',
      note='“博学善属文”为主书评价，可作为史书评价展示，不作为量化能力事实。')
event('qian_chuanguan_takes_guangde', '钱传瓘攻下广德，俘花虔、涡信', 29,
      '吴越钱传瓘拔广德，虏花虔、涡信以归。',
      [('钱传瓘','率吴越军攻下广德'),('花虔','广德失守后被俘'),('涡信','广德失守后被俘')],
      when='913年六月丙子后、戊子前；确日未载',place='广德',
      note='原文未记俘虏后处置；承第26段吴军屯广德。')
event('zhang_wanjin_pinglu', '梁任张万进为平卢节度使', 30,
      '戊子，以张万进为平卢节度使。',
      [('张万进','受任平卢节度使，承第25段改镇表请')],
      when='913年六月戊子',place='平卢',
      note='本段记正式任命；与第25段杨师厚表奏分开。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,31):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化三年四月至六月第21—30段连续处理；刘光浚／濬与王德明等复用稳定主体，旧书异说独立引用。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=913,
    primary_source_key=main2,primary_source_keys=[main2,main3],
    paragraphs=[Q[n]['id'] for n in range(21,31)],next_paragraph='zztj-v268-y0913-p031',
    coverage='卷268乾化三年四月至六月第21—30段，燕晋幽州攻守、吴越广德战事、梁赵沧州战事与蜀官员任命。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[21]['id'],'note':'旧五代史卷28补首位请和使者王遵化；主书未具名，未据补证把主书记录改为具名。'},
      {'paragraph_id':Q[23]['id'],'note':'通鉴本年早段作刘光濬，后段作刘光浚；繁简／异体统一为既有主体，原文引字保留。'},
      {'paragraph_id':Q[25]['id'],'note':'主书“守奇自贝州人趣冀州”疑“人”误“入”；旧五代史卷8记州军名单、下博攻克者、张万进态度、刘守奇官号等与主书有差异，分别存证。'},
      {'paragraph_id':Q[28]['id'],'note':'“博学善属文”与“蜀主重之”为通鉴叙述与评价，未外推现代评判。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
