"""Curate Tongjian 268, year 912, consecutive paragraphs 41-50."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
main1 = 'tongjian-268-912-autumn'
main2 = 'tongjian-268-912-year-end'
old_baijing = 'jiuwudaishi-028-baijingling'
new_baijing = 'xinwudaishi-022-baijingling'
old_liuxun = 'jiuwudaishi-061-liuxun'
new_gao = 'xinwudaishi-069-gaojichang'
B = {'format_version': 1, 'batch_key': 'zztj-v268-y0912-p041-p050',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
specs = [
    (main1, YEAR / 'part-04/sources/library' / main1, '7826e264', '司马光等'),
    (main2, P / 'sources/library' / main2, 'c07f5489', '司马光等'),
    (old_baijing, P / 'sources/library' / old_baijing, 'c07f5489', '薛居正等'),
    (new_baijing, P / 'sources/library' / new_baijing, 'c07f5489', '欧阳修'),
    (old_liuxun, P / 'sources/library' / old_liuxun, 'c07f5489', '薛居正等'),
    (new_gao, P / 'sources/library' / new_gao, 'c07f5489', '欧阳修'),
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
primary_texts = {key:(source_dirs[key]/'source.txt').read_text() for key in (main1,main2)}
for n in range(41,51):
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
           '王景仁':'王茂章','张宗奭':'张全义','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','元膺':'王宗懿','硃友谦':'朱友谦','王镠':'钱镠','吴越王镠':'钱镠','张宗奭':'张全义','李存审':'符存审','韩珪':'韩勍','丁昭浦':'丁昭溥','徐知浩':'李昪','徐知诰':'李昪','王德明':'张文礼','段凝':'段明远','王寂侃':'王宗侃','王宗播':'许存','王宗钅岁':'王宗鐬','宗钅岁':'王宗鐬','短俊':'刘知俊','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','李存审':'符存审','宋鄴':'宋邺','宗钅岁':'王宗鐬','昌王宗钅岁':'王宗鐬','德明':'张文礼','赵德明':'张文礼','晋王':'李存勖','赵王镕':'王镕',
           '宗懿':'王宗懿','高季兴':'高季昌','王德明':'张文礼','元坦':'王宗懿','硃温':'朱温','上':'朱温'}
people, used, reused, supplements = {}, {}, set(), []

def claim(table, key, field, value, n, quote, note, source=None, supplement_relation='adds'):
    source = source or next(key for key in (main1,main2) if quote in primary_texts[key])
    text = (source_dirs[source] / 'source.txt').read_text()
    assert quote in text, (source, quote)
    if source in (main1,main2):
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷268·乾化二年（912）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = json.loads((source_dirs[source] / 'paragraph.json').read_text())['citation']
    ck = f'claim_zztj_268_0912_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in (main1,main2):
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
                   description=f'《资治通鉴》卷268乾化二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '只据本段确认身份；繁简字形用于匹配，原文仍保持底本原字。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=912):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_268_0912_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when or '912年本段条；确日未载', dynasty='五代十国',
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
        edge = 'participation_zztj_268_0912_' + code + '_' + pk
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

event('shu_wude_army_rename', '前蜀改剑南东川为武德军', 41,
      '辛巳，蜀改剑南东川曰武德军。',
      when='912年九月辛巳',place='剑南东川、武德军',
      note='本段是军额改名，未指明个人发令或治所迁移。')

event('zhu_youqian_again_asks_jin', '朱友谦再次向晋告急，李存勖自泽潞西进', 42,
      '硃友谦复告急于晋，冬，十月，晋王自将自泽潞而西，',
      [('硃友谦','再次向晋告急的河中将领朱友谦'),('李存勖','亲率晋军自泽潞西进的晋王')],
      when='912年十月',place='河中、泽州、潞州',
      note='底本“硃友谦”归入既有朱友谦；“复”承第38段归晋求援，不推此前另有未记的救援战。')
event('jin_defeats_liang_jiexian', '李存勖在解县破康怀贞，追至白径岭，梁军撤围', 42,
      '遇康怀贞于解县，大破之，斩首千级，追至白径岭而还。梁兵解围，退保陕州。',
      [('李存勖','在解县击败梁军并追至白径岭的晋王'),('康怀贞','在解县败退的梁河中军统帅')],
      when='912年十月；确日未载',place='解县、白径岭、陕州',
      note='主书记康怀贞、解县、斩首千级；旧五代史卷28作康怀英、平阳、千余级，异名地点和数字并列。')
claim('event','event_zztj_268_0912_jin_defeats_liang_jiexian','description',
      '《旧五代史》卷二十八记晋王破康怀英于平阳，追至白径岭，河中解围。',42,
      '帝自澤州路赴河中，遇梁將康懷英於平陽，破之，斬首千餘級，追至白徑嶺。朱友謙會帝於猗氏，梁軍解圍而去。',
      '旧书康怀英、平阳、千余级与主书康怀贞、解县、千级有差异；不据形似自动合并康氏两实体。',old_baijing,'conflicts')
claim('event','event_zztj_268_0912_jin_defeats_liang_jiexian','description',
      '《新五代史》卷二十二亦记康怀英在白径岭败于晋军。',42,
      '其後朱友謙叛附于晉，以懷英討之，與晉人戰白徑嶺，懷英又大敗。',
      '新史以白径岭为交战地点；与主书解县交战、白径岭追击的战斗阶段或地点不同。',new_baijing,'adds')
event('zhu_youqian_meets_jin_wang', '朱友谦到猗氏谢晋王，以舅相称并在营中宴宿', 42,
      '友谦身自至猗氏谢晋王，从者数十人，撤武备，诣晋王帐，拜之为舅。晋王夜置酒张乐，友谦大醉。晋王留宿帐中，友谦安寝，鼾息自如。明旦复置酒而罢。',
      [('朱友谦','亲至猗氏晋王营中致谢并留宿'),('李存勖','在营中宴请并留朱友谦过夜的晋王')],
      when='912年十月梁军撤围后；确日未载',place='猗氏',
      note='“拜之为舅”是政治礼仪称谓，不据此建立血缘关系。')

event('yang_shihou_shows_force_to_yougui', '杨师厚率精兵万赴洛阳，朱友珪厚赐后遣还', 43,
      '师厚曰：“理知其为人，虽往，如我何！”乃帅精兵万人，渡河趣洛阳，友珪大惧。丁亥，至都门，留兵于外，与十馀人入见。友珪喜，甘言逊词以悦之，赐与巨万。癸巳，遣还。',
      [('杨师厚','带精兵赴洛阳入见并获遣还的梁将'),('朱友珪','召杨师厚、厚赐后遣还的梁帝')],
      when='912年十月丁亥入见、癸巳遣还',place='洛阳',
      note='杨师厚麾下精兵万留都外，仅与十余人入见；不写成万人入宫。')

event('wang_deming_raids_zongcheng', '张文礼（王德明）率赵军掠武城、临清并取宗城', 44,
      '十一月，赵将王德明将兵三万掠武城，至于临清，攻宗城，下之。',
      [('王德明','以赵将王德明名率三万兵进攻宗城的张文礼')],
      when='912年十一月癸丑前；确日未载',place='武城、临清、宗城',
      note='王德明是前文赵德明、张文礼同人；“三万”是史书所记兵数，原文繁简异字不另立实体。')
event('yang_shihou_tangdian_ambush', '杨师厚唐店伏击赵军，史载斩首五千余级', 44,
      '癸丑，杨师厚伏兵唐店，邀击，大破之，斩首五千馀级。',
      [('杨师厚','在唐店伏击赵军的梁将')],
      when='912年十一月癸丑',place='唐店',
      note='斩首五千余级为主书战果，不推为全部阵亡人数。')

event('zhu_wen_buried_xuanling', '朱温葬宣陵，庙号太祖', 45,
      '甲寅，葬神武元圣孝皇帝于宣陵，庙号太祖。',
      [('朱温','葬于宣陵、庙号太祖的梁开国皇帝')],
      when='912年十一月甲寅',place='宣陵',
      note='本段的神武元圣孝皇帝即第28段遇弑的朱温；不将葬日误作死亡日。')

event('wu_captures_yuezhou', '吴将陈璋水军袭岳州，俘楚刺史苑玫', 46,
      '吴淮南节度副使陈璋等将水军袭楚岳州，执刺史苑玫；楚王殷遣水军都指挥使杨定真救岳州。',
      [('陈璋','率吴水军袭岳州并俘刺史'),('苑玫','在岳州被吴军俘获的楚刺史'),('马殷','遣杨定真救岳州的楚王'),('杨定真','奉马殷命救岳州的楚水军都指挥使')],
      when='912年十一月前后；确日未载',place='岳州',
      note='主书先记陈璋俘苑玫，再记马殷派水军救援；未记杨定真是否夺回岳州。')
event('wu_attacks_jingnan', '陈璋续攻荆南，高季昌遣倪可福抵御，刘信屯吉州声援', 46,
      '璋等进攻荆南，高季昌遣其将倪可福拒之。吴恐楚人救荆南，遣抚州刺史刘信帅江、抚、袁、吉、信五州兵屯吉州，为璋声援。',
      [('陈璋','率吴军进攻荆南'),('高季昌','遣将抵御吴军的荆南节度使'),('倪可福','奉高季昌命抵御陈璋'),('刘信','率五州兵屯吉州声援吴军')],
      when='912年十一月前后；确日未载',place='荆南、吉州',
      note='刘信军仅记屯吉州声援，未写其已与陈璋合兵或参与岳州战。')

event('shu_takes_wenzhou', '王宗汾攻取岐文州，守将李继夔出走', 47,
      '十二月，戊寅，蜀行营都指挥使王宗汾攻岐文州，拔之，守将李继夔走。',
      [('王宗汾','攻取文州的前蜀行营都指挥使'),('李继夔','失文州后出走的岐守将')],
      when='912年十二月戊寅',place='文州',
      note='“走”只指离开文州，未记去向。')

event('liu_xun_suizhou_defection', '刘训杀隰州刺史、以州降晋，获任瀛州刺史', 48,
      '是岁，隰州都将刘训杀刺史，以州降晋，晋王以为瀛州刺史。训，永和人也。',
      [('刘训','杀隰州刺史后以州降晋并受瀛州刺史'),('李存勖','任刘训瀛州刺史的晋王')],
      when='912年是岁；确月日未载',place='隰州、瀛州',
      note='旧五代史卷61称刘训曾隶河中、任隰州防御都将，与901年河中牙将刘训履历相接，沿既有UUID；旧书作杀陕州刺史，与主书隰州异。')
claim('person',people['刘训'],'description',
      '《旧五代史》卷六十一记刘训先隶河中，后为隰州防御都将。',48,
      '後隸河中，為隰州防禦都將。居無何，殺陝州刺史，以郡歸莊宗，曆瀛州刺史。',
      '河中履历支持与901年已录刘训为同人；旧书作杀陕州刺史、通鉴作隰州，原文异地待校。',old_liuxun,'adds')

event('tan_quanbo_takes_qianzhou', '李彦图卒，虔州人奉谭全播知州，梁授百胜防御使', 49,
      '虔州防御使李彦图卒，州人奉谭全播知州事，遣使内附，诏以全播为百胜防御使虔、韶二州节度开通使。',
      [('李彦图','于912年去世的虔州防御使'),('谭全播','被州人奉为知州并获梁授百胜防御使')],
      when='912年是岁；确月日未载',place='虔州、韶州',
      note='“州人奉”与梁诏任官分清先后；“虔、韶二州节度开通使”照底本保留，职名细分待校。')

event('gao_jichang_xiangzhou_defeat', '高季昌声称助梁伐晋而攻襄州，被孔勍击败，朝贡路断', 50,
      '高季昌出兵，声言助梁代晋，进攻襄州，山南东道节度使孔勍击败之。自是朝贡路绝。',
      [('高季昌','声称助梁而攻襄州的荆南将领'),('孔勍','击退高季昌的山南东道节度使')],
      when='912年是岁；确月日未载',place='襄州、荆南',
      note='底本“代晋”保留原字，语义或作“伐晋”待核；“自是朝贡路绝”是其后状态，不假定永久。')
claim('event','event_zztj_268_0912_gao_jichang_xiangzhou_defeat','description',
      '《新五代史》卷六十九记高季兴（高季昌）攻襄州，为孔勍所败，停止朝贡。',50,
      '又發兵聲言助梁擊晉，以侵襄州，為孔勍所敗，乃絕貢賦累年。',
      '新史作“击晋”、名高季兴，支持底本“代晋”疑字及同一人物别名；其“累年”不改主书912年事件日期。',new_gao,'adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,51):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
                       review='卷268乾化二年第41—50段连续处理；刘训身份据旧史履历复核，白径岭及襄州异文保留。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=268,year=912,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(41,51)],next_paragraph='zztj-v268-y0913-p001',
    coverage='卷268乾化二年九月至岁末第41—50段，河中解围、唐店伏击、吴楚战事、荆南叛离。',
    supplements=supplements,status=status,textual_reviews=[
      {'paragraph_id':Q[42]['id'],'note':'旧五代史卷28康怀英、平阳、千余级；通鉴康怀贞、解县、千级；新五代史卷22白径岭败，战场/异名待核。'},
      {'paragraph_id':Q[48]['id'],'note':'旧五代史卷61刘训履历从河中到隰州，支持复用901年人物；该书作杀陕州刺史、通鉴作隰州刺史，地点冲突保留。'},
      {'paragraph_id':Q[50]['id'],'note':'底本高季昌“助梁代晋”，新五代史卷69高季兴“助梁击晋”；高季昌/季兴同人归既有UUID，代/击/伐异字待纸本核。'}]),
    ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
