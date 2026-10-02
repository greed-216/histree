"""Curate consecutive Tongjian vol. 269, 916 paragraphs 23–27."""
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
main = 'tongjian-269-916-autumn'
old28 = 'jiuwudaishi-028-cangzhou'
new63 = 'xinwudaishi-063-shu-invasion'
new33a = 'xinwudaishi-033-zhang-yuande-siege'
new33b = 'xinwudaishi-033-beizhou-surrender'
old53 = 'jiuwudaishi-053-li-cunzhang'
old22 = 'jiuwudaishi-022-wang-tan-death'
specs = []
for key, path, commit, author in [
    (main, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-04/sources/library' / main, '5e858107', '司马光等'),
    (old28, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-04/sources/library' / old28, '5e858107', '薛居正等'),
    (new63, ROOT / 'content/books/zizhi-tongjian/vol-269/year-0916/part-04/sources/library' / new63, '5e858107', '欧阳修'),
    (new33a, P / 'sources/library' / new33a, '91f2b9c9', '欧阳修'),
    (new33b, P / 'sources/library' / new33b, '91f2b9c9', '欧阳修'),
    (old53, P / 'sources/library' / old53, '91f2b9c9', '薛居正等'),
    (old22, P / 'sources/library' / old22, '91f2b9c9', '薛居正等'),
]:
    specs.append((key,path,commit,author))
B = {'format_version': 1, 'batch_key': 'zztj-v269-y0916-p023-p027',
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
lines = (ROOT / 'resources/derived/tongjian/269.txt').read_text().splitlines()
for n in range(23, 28):
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
    for key in ([main]):
        if quote in (source_dirs[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('no Tongjian snapshot', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((source_dirs[source] / 'paragraph.json').read_text())
    assert quote in (source_dirs[source] / 'source.txt').read_text(), (source, quote)
    if source == main:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷269·贞明二年（916）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_269_0916_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source != main:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))
    return ck

def person(name, n, role, quote):
    name = {'蜀主':'王建','晋王':'李存勖','李存审':'符存审','王宗播':'许存','契丹王阿保机':'阿保机','吴王':'杨隆演','蜀主':'王建','李继岌':'桑弘志','曹夫人':'曹氏（李存勖母）'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases=[],
                   era='五代十国', birth_year=None, death_year=None,
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
          '只保留原纪年，不换算公历日；叙述性回顾不推成逐次日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_269_0916_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；称谓按既有主体匹配。')
    return key

# p023: Yunzhou relief, Beizhou siege and capitulation must not be collapsed.
event('jin_relief_yunzhou','晋王率兵救云州至代州，契丹引去',23,
      '晋王自将兵救云州，行至代州，契丹闻之，引去，王亦还。',
      [('李存勖','率兵救云州至代州的晋王')],place='云州、代州',
      note='主书称契丹闻晋军来而退；旧五代史庄宗纪另称王闻蔚州陷而班师，异说保留。')
claim('event','event_zztj_269_0916_jin_relief_yunzhou','description',
      '《旧五代史》卷二十八称晋王北征至代州北，闻蔚州陷而班师。',23,
      '帝領親軍北征，至代州北，聞蔚州陷，乃班師。',
      '旧书所述退兵触发与通鉴不同，不合并推成确定因果。',old28,'conflicts')
event('li_cunzhang_daitong_governor','晋任李存璋为大同节度使',23,
      '以李存璋为大同节度使。',
      [('李存璋','受大同节度使任命者')],place='大同')
claim('event','event_zztj_269_0916_li_cunzhang_daitong_governor','description',
      '《旧五代史》李存璋传记敌退后以功授大同军节度使。',23,
      '敵退，以功加檢校太傅、大同軍節度使、應蔚等州觀察使。',
      '旧书补授官理由及兼官；保留大同称谓差异。',old53,'corroborates')
event('beizhou_siege_endures','晋围贝州逾年，城中断粮',23,
      '晋人围贝州逾年，张源德闻河北诸州皆为晋有，欲降，谋于其众。',
      [('张源德','被长期围困的贝州守将')],place='贝州',
      note='“逾年”为跨年持续状态，不推定围城起日；此事件仅记916年所见情势。')
event('zhang_yuande_killed_by_garrison','贝州守军反对投降，杀守将张源德',23,
      '张源德闻河北诸州皆为晋有，欲降，谋于其众。众以穷而后降，恐不免死，不从。共杀源德，婴城固守。',
      [('张源德','提出投降而被守军杀害的贝州守将')],place='贝州',
      note='“欲降”是通鉴叙述；新五代史作张源德不从众人劝降，谁主张投降存在相反记载。')
claim('event','event_zztj_269_0916_zhang_yuande_killed_by_garrison','description',
      '《新五代史》称贝人劝张源德投降，张源德不从，遂遭杀害。',23,
      '乃勸源德出降，源德不從，遂見殺。',
      '与通鉴“源德欲降、众不从”相反；并列保留，不推定哪一版本正确。',new33a,'conflicts')
event('beizhou_famine_cannibalism','贝州被围至食尽，城中以人为粮',23,
      '城中食尽，啖人为粮',[],place='贝州',
      note='按主书保留危机叙述；未记具体人数或被害者身份。')
event('beizhou_armed_surrender_terms','贝州守军请求持甲兵出降，晋将答应',23,
      '乃谓晋将曰：“出降惧死，请擐甲执兵而降，事定而释之。”晋将许之',[],place='贝州',
      note='主书未给晋将姓名，不将承诺归给晋王；此为降前约定。')
event('beizhou_surrenderers_killed','贝州三千守军释甲后遭晋军围杀',23,
      '其众三千出降，既释甲，围而杀之，尽殪。',[],place='贝州',
      note='三千是主书记载的降者数量；执行者称晋军，不推定具体主令。')
claim('event','event_zztj_269_0916_beizhou_surrenderers_killed','description',
      '《新五代史》死事传亦记三千贝人释甲后遭晋兵围杀。',23,
      '貝人三千出降，已釋甲，晉兵四面圍而盡殺之。',
      '新书与主书叙述相近，可能存在史料依赖；不视为独立统计确证。',new33b,'corroborates')
event('mao_zhang_beizhou_prefect','晋王任毛璋为贝州刺史',23,
      '晋王以毛璋为贝州刺使。',
      [('李存勖','任毛璋为贝州地方官的晋王'),('毛璋','受任贝州刺史者')],place='贝州',
      note='主书原字作“刺使”，旧五代史卷二十八作“刺史”；展示官名据旧书规范化，摘录不改字。')
claim('event','event_zztj_269_0916_mao_zhang_beizhou_prefect','description',
      '《旧五代史》庄宗纪明记毛璋为贝州刺史。',23,
      '是月，貝州平，以滄州降將毛璋為貝州刺史。',
      '旧书“刺史”可校主书电子本“刺使”，仍需纸本校勘。',old28,'corroborates')
event('jin_controls_hebei_except_liyang','晋得河北诸州，黎阳仍为梁守',23,
      '于是河北皆入于晋，惟黎阳为梁守。',[],place='河北、黎阳',
      note='主书总括性归属，不外推精确国界或所有县份。')
event('jin_king_returns_weizhou','晋王李存勖赴魏州',23,
      '晋王如魏州。',[('李存勖','赴魏州的晋王')],place='魏州')

# p024: Guangzhou mutiny and intervention.
event('wang_yan_kills_dai_zhao','吴光州将王言杀刺史载肇',24,
      '吴光州将王言杀刺史载肇',
      [('王言','杀光州刺史的吴将'),('载肇','遇害的光州刺史')],place='光州',
      note='“载肇”照通鉴电子底本记录；限定史料尚未找到二十四史对应书证，姓名字形待纸本核。')
event('li_hou_ordered_to_guangzhou','吴王遣李厚讨王言',24,
      '吴王遣楚州团练使李厚讨之。',
      [('吴王','下令讨伐王言的吴王'),('李厚','奉命讨王言的楚州团练使')],place='楚州、光州')
event('zhang_chong_drives_wang_yan_out','张崇未待吴王命令，率兵趋光州迫王言逃走',24,
      '庐州观察使张崇不俟命，引兵趣光州，言弃城走。',
      [('张崇','未待命而率兵赴光州的庐州观察使'),('王言','弃光州而走者')],place='庐州、光州',
      note='“不俟命”是主书用语；不据此推断吴王后来惩处张崇。')
event('li_hou_interim_guangzhou','李厚权知光州',24,
      '以李厚权知光州。崇，慎县人也。',
      [('李厚','权知光州者')],place='光州',
      note='后句“崇，慎县人也”系张崇籍贯，不作李厚籍贯。')
claim('person',person('张崇',24,'庐州观察使、慎县人','崇，慎县人也。'),'description',
      '张崇为慎县人。',24,'崇，慎县人也。','“崇”承上张崇；史载地名保留。')

# p025: material construction, no inferred map coordinates.
event('shu_new_palace_completed','前蜀新宫建成，位于旧宫之北',25,
      '庚申，蜀新宫成，在旧宫之北。',[],when='916年庚申；未换算公历日',place='蜀新宫、旧宫',
      note='仅记录相对方位；旧宫、新宫具体坐标未经核证。')

# p026: Wang Tan's recruitment background, murder and suppression.
event('wang_tan_bandit_retinue','王檀招募群盗为亲兵',26,
      '天平节度使兼中书令琅邪忠毅王王檀，多募群盗，置帐下为亲兵。',
      [('王檀','招募群盗置于帐下为亲兵的天平节度使')],when='本段追叙；招募起始年未载',place=None,
      note='“多募”是先前形成的背景，起始年不详；本段以916年追叙，不推为己卯当日招募。',year=None)
event('wang_tan_murdered_by_retinue','王檀亲兵乘其不备突入府第杀王檀',26,
      '己卯，盗乘檀无备，突入府杀檀。',
      [('王檀','在府中遇害者')],when='916年己卯；未换算公历日',place='天平军府',
      note='行凶者主书称“盗”，承上王檀所募群盗，未具名。')
claim('event','event_zztj_269_0916_wang_tan_murdered_by_retinue','description',
      '《旧五代史》王檀传记所募盗徒突入府第杀王檀。',26,
      '數輩竊發，突入府第，檀素不為備，遂為所害',
      '旧书与主书一致；“数辈”未换算人数。',old22,'corroborates')
event('pei_yan_suppresses_wang_tan_killers','裴彦率府兵讨杀王檀凶徒',26,
      '节度副使裴彦帅府兵讨诛之，军府由是获安。',
      [('裴彦','率府兵讨诛王檀凶徒的节度副使')],place='天平军府',
      note='“之”承上杀王檀的盗徒，不生成未具名人物。')
claim('event','event_zztj_269_0916_pei_yan_suppresses_wang_tan_killers','description',
      '《旧五代史》记裴彦率府兵擒杀盗徒，州城安定。',26,
      '節度副使裴彥聞變，率府兵盡擒諸賊，州城帖然。',
      '旧书原字裴彥，本站统一人物名裴彦。',old22,'corroborates')

# p027: distinguish the Qi officer called Li Jiji from Jin prince of same name.
event('shu_breaks_qi_at_baoji','王宗绾军出大散关败岐兵，取宝鸡',27,
      '冬，十月，甲申，蜀王宗绾等出大散关，大破岐兵，俘斩万计，遂取宝鸡。',
      [('王宗绾','率蜀军出大散关攻取宝鸡者')],when='916年冬十月甲申；未换算公历日',place='大散关、宝鸡',
      note='“俘斩万计”为主书概数，不当作核实人数。')
event('xu_cun_reaches_longzhou','前蜀西北路王宗播由故关至陇州',27,
      '己丑，王宗播等出故关，至陇州。',
      [('王宗播','以赐名王宗播率蜀军至陇州者')],when='916年冬十月己丑；未换算公历日',place='故关、陇州',
      note='王宗播为本站已有许存之别名，复用许存人物 UUID。')
event('sang_hongzhi_defects_to_shu','岐将李继岌率部二万弃陇州投蜀',27,
      '丙寅，保胜节度使兼侍中李继岌畏岐王猜忌，帅其众二万，弃陇州奔于蜀军。',
      [('李继岌','原名桑弘志、以李继岌名率部投蜀的岐将')],when='916年冬十月丙寅；未换算公历日',place='陇州',
      note='二万为主书所载部众数。此岐将后来恢复姓名桑弘志，非晋王之子同名李继岌。')
event('sang_hongzhi_shu_command','前蜀军攻陇州，任桑弘志为第四招讨',27,
      '蜀兵进攻陇州，以继岌为西北面行营第四招讨。',
      [('李继岌','以李继岌名受前蜀西北面行营第四招讨')],place='陇州',
      note='段末明确复原姓名桑弘志，主体用桑弘志；不复用晋王之子李继岌。')
event('shu_besieges_fengxiang_then_withdraws','刘知俊会王宗绾围凤翔，雪大后蜀主召军还',27,
      '刘知俊会王宗绾等围凤翔，岐兵不出。会大雪，蜀主召军还。',
      [('刘知俊','会合王宗绾围凤翔的蜀将'),('王宗绾','与刘知俊围凤翔的蜀将'),('王建','因大雪召蜀军回师的蜀主')],place='凤翔',
      note='岐兵不出不等于全境无战；围城结束由本句大雪与召军回师表述。')
event('sang_hongzhi_name_restored','前蜀恢复岐降将姓名桑弘志',27,
      '复李继岌姓名曰桑弘志。弘志，黎阳人也。',
      [('李继岌','获恢复本名桑弘志的岐降将')],place=None,
      note='“李继岌”仅为此人在本段的旧名；与后唐魏王李继岌严格区分。')
claim('person',person('桑弘志',27,'原以李继岌为名、黎阳人','复李继岌姓名曰桑弘志。弘志，黎阳人也。'),'description',
      '桑弘志曾名李继岌，为黎阳人。',27,
      '复李继岌姓名曰桑弘志。弘志，黎阳人也。',
      '同名李继岌另为晋王之子，人物键分离；暂不把无歧义别名“李继岌”写入别名数组。')
claim('event','event_zztj_269_0916_shu_breaks_qi_at_baoji','description',
      '《新五代史》概述王宗绾等出大散关攻岐及随后取陇州。',27,
      '遣王宗綰等率兵十二萬出大散關攻岐，取隴州。',
      '与主书这段出关相近，但兵数及取陇州时序不完全相同，保留概述性质。',new63,'adds')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(23, 28):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷269贞明二年第23—27段连续处理；贝州降杀及张源德意愿异说、光州变乱、蜀宫、王檀遇害、前蜀攻岐。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=269,year=916,
    primary_source_key=main,primary_source_keys=[main],paragraphs=[Q[n]['id'] for n in range(23,28)],
    next_paragraph=Q[28]['id'],coverage='卷269贞明二年第23—27段；云州解围、贝州惨杀、光州变乱、蜀宫、王檀遇害、蜀岐战事。',
    supplements=supplements,reviewed_questions=[
      {'paragraph_id':Q[23]['id'],'note':'张源德议降意愿：《通鉴》称欲降而众不从，《新五代史》称源德不从众劝；降后围杀三千人的叙述相近但可能有史源依赖。主书“刺使”字形，旧书作“刺史”，待纸本核。'},
      {'paragraph_id':Q[24]['id'],'note':'光州刺史姓名主书电子底本作“载肇”；当前二十四史检索未得对应互证，保持字形并待纸本核。'},
      {'paragraph_id':Q[26]['id'],'note':'王檀募群盗为回顾背景，起始年份不详；裴彦为“裴彥”繁简归一。'},
      {'paragraph_id':Q[27]['id'],'note':'岐将李继岌即桑弘志，非晋王之子同名李继岌；两人主体分离，旧名放入引用和身份说明。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
