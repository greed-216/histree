"""Curate consecutive Tongjian volume 271, year 920, paragraphs 9–13."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 27))
specs = [
    ('tongjian-271-920-april', YEAR / 'part-01/sources/library/tongjian-271-920-april', '438b833a', '司马光等'),
    ('jiuwudaishi-010-tongzhou', YEAR / 'part-02/sources/library/jiuwudaishi-010-tongzhou', 'e9c4775b', '薛居正等'),
    ('xinwudaishi-063-han-zhao', P / 'sources/library/xinwudaishi-063-han-zhao', '6dd2bd92', '欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0920-p009-p013',
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
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(9, 14):
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
        citation = f'卷271·贞明六年（920）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0920_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'温昭图':'温韬','溫昭圖':'温韬','蜀主':'王宗衍','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'温昭图':['溫昭圖'],'张士乔':['張士喬'],'韩昭':['韓昭']}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271贞明六年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='920年本段条；确日未载', note='', year=920, place='五代十国'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0920_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_271_0920_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('zhou_xiang_yongping_jiedushi','蜀命周庠充永平节度使',9,
      '丁巳，蜀以司徒兼门下侍郎、同平章事周庠同平章事，充永平节度使。',
      [('周庠','充永平节度使、保有同平章事衔者')],
      when='920年六月丁巳',place='永平',
      note='底本前后重见同平章事，保留原字；确定本段新记充永平节度使，未据重复官衔另造二次授相。')

event('liu_xun_leads_liang_attack_tongzhou','梁任刘鄩为河东道招讨使，率尹皓等攻同州',10,
      '帝以泰宁节度使刘鄩为河东道招讨使，帅感化节度使尹皓、静胜节度使温昭图、庄宅使段凝攻同州。',
      [('刘鄩','受命为河东道招讨使率诸将攻同州者'),('尹皓','随刘鄩攻同州的感化节度使'),
       ('温昭图','随刘鄩攻同州的静胜节度使'),('段凝','随刘鄩攻同州的庄宅使')],
      when='920年六月本段；确日未载',place='同州',
      note='主书按本段官衔录入；温昭图沿已发布勘误的温韬别名复用同一主体。同州围攻结果留到后续连续段落。')
claim('event','event_zztj_271_0920_liu_xun_leads_liang_attack_tongzhou','description',
      '《旧五代史》卷十六月同记刘鄩、尹皓、温昭图、段凝领军攻同州。',10,
      '六月，遣兗州節度使劉鄩、華州節度使尹皓、崇州節度使溫昭圖、莊宅使段凝領軍攻同州。',
      '旧书分别作兗州、华州、崇州节度使，主书分别作泰宁、感化、静胜；四名将领与攻同州事实对应，职衔原貌并列。',
      'jiuwudaishi-010-tongzhou','corroborates')

event('shu_king_builds_gaozu_temple_wanliqiao','蜀主于万里桥作高祖原庙并率百官祭祀',11,
      '闰月，庚申朔，蜀主作高祖原庙于万里桥，帅后妃、百官用亵味作鼓吹祭之。',
      [('蜀主','于万里桥作高祖原庙并率祭者')],
      when='920年闰月庚申朔（承六月）；不换算公历',place='万里桥',
      note='主书只写闰月，承上六月并保留原纪时；祭祀对象为蜀高祖王建，未把已卒者写成参与人。')
event('zhang_shiqiao_remonstrates_and_exiled','张士乔谏原庙祭礼，蜀主削官流黎州',11,
      '华阳尉张士乔上疏谏，以为非礼，蜀主怒，欲诛之，太后以为不可，乃削官流黎州，',
      [('张士乔','上疏谏祭礼后被削官流黎州的华阳尉'),('蜀主','初欲诛张士乔后削官流放者'),
       ('太后','反对诛张士乔的蜀太后')],
      when='920年闰月庚申朔祭祀后本段；确日未载',place='华阳、黎州',
      note='“欲诛”未执行；太后沿王宗衍朝已核徐贤妃主体，反对处死而后削官流放有原文。')
event('zhang_shiqiao_drowns_himself','张士乔流放后感愤赴水而死',11,
      '士乔感愤，赴水死。',[('张士乔','削官流黎州后赴水而死者')],
      when='张士乔被流放后；确年、月、日未载',year=None,place='黎州相关地，确地未载',
      note='原文把赴水死接在流放后，未给死日或所到地点；不把流放目的地直接当作确切死亡地点。')

event('zhu_youqian_seeks_jin_relief_tongzhou','刘鄩围同州，朱友谦求救于晋',12,
      '刘鄩等围同州，硃友谦求救于晋。',
      [('刘鄩','围同州的梁将'),('硃友谦','因同州被围而向晋求救者')],
      when='920年七月遣援前；确日未载',place='同州、晋',
      note='硃友谦按朱友谦匹配既有主体；只记围城和求救，不预写胜败。')
event('jin_sends_four_generals_to_relieve_tongzhou','晋王遣符存审等四将救同州',12,
      '秋，七月，晋王遣李存审、李嗣昭、李建及、慈州刺史李存质将兵救之。',
      [('晋王','遣四将救同州者'),('李存审','奉命领兵救同州的晋将'),('李嗣昭','奉命领兵救同州的晋将'),
       ('李建及','奉命领兵救同州的晋将'),('李存质','奉命领兵救同州的慈州刺史')],
      when='920年七月；确日未载',place='同州',
      note='李存审沿符存审既有主体；此段记遣军，实际抵达及战果在后续段落。')

event('shu_king_decrees_northern_tour','蜀主下诏北巡',13,
      '乙卯，蜀主下诏北巡，',[('蜀主','下诏北巡者')],
      when='920年七月乙卯',place='蜀',
      note='下诏与八月发成都、九月到安远分别录入。')
event('han_zhao_wensi_grand_academician','蜀任韩昭为文思殿大学士',13,
      '以礼部尚书兼成都尹长安韩昭为文思殿大学士，位在翰林承旨上。',
      [('韩昭','受任文思殿大学士的礼部尚书兼成都尹')],
      when='920年七月乙卯同段',place='成都',
      note='长安为主书籍贯说明；不据此推生年。')
claim('person','person_韩昭','description','《新五代史》卷六十三将韩昭列为王衍狎客。',13,
      '以韓昭、潘在迎、顧在珣、嚴旭等為狎客；',
      '补书写王衍朝韩昭为狎客，未给确年；同一姓名和朝廷身份对应，未用其证明920年大学士任命日期。',
      'xinwudaishi-063-han-zhao','adds')
event('han_zhao_seeks_prefectures_for_sale','韩昭请售数州刺史职位营居第，蜀主许之',13,
      '昭无文学，以便佞得幸，出入宫禁，就蜀主乞通、渠、巴、集数州刺史卖之以营居第，蜀主许之。',
      [('韩昭','请求数州刺史职位出售以营居第者'),('蜀主','允许韩昭请求者')],
      when='韩昭受宠期间本段叙事；确年、月、日未载',year=None,place='通州、渠州、巴州、集州',
      note='“许之”证明准其请求，未记具体受官买家、交易金额及是否完成。')
event('shu_king_departs_chengdu_northern_tour','蜀主发成都北巡',13,
      '八月，戊辰，蜀主发成都，被金甲，冠珠帽，执弓矢而行，旌旗兵甲，亘百馀里。',
      [('蜀主','八月自成都出巡者')],
      when='920年八月戊辰',place='成都',
      note='“百馀里”是主书对行列规模的记述，未换算为地理线路。')
event('duan_rong_remonstrates_against_tour','段融谏蜀主远离都邑，未获采纳',13,
      '雒令段融上言：“不宜远离都邑，当委大臣征讨。”不从。',
      [('段融','谏不宜远离都邑的雒县令'),('蜀主','未采纳段融建议者')],
      when='920年八月发成都后本段；确日未载',place='蜀',
      note='段融所言是建议委大臣征讨，未说明具体敌方或已发生征讨；不添战争对象。')
event('shu_king_reaches_anyuan','蜀主北巡至安远城',13,
      '九月，次安远城。',[('蜀主','北巡九月至安远城者')],
      when='920年九月；确日未载',place='安远城',
      note='本段主语承蜀主；不据未核地名填现代坐标。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(9, 14):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明六年第9—13段；周庠任官、梁晋同州攻援、张士乔谏祭与蜀主北巡。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=920,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(9, 14)], next_paragraph=Q[14]['id'],
    coverage='卷271贞明六年第9—13段；周庠充永平、同州攻援、万里桥祭谏与蜀北巡。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[9]['id'],'note':'周庠同平章事官衔底本重复，原字保留；本段新动作是充永平节度使。'},
      {'paragraph_id':Q[10]['id'],'note':'旧书六月所记四将与主书相合，节度使军名／州名职衔分别保存；温昭图复用温韬，依据已发布2026-10-02-wen-tao-li-yantao身份勘误，不另建人物。'},
      {'paragraph_id':Q[11]['id'],'note':'闰月原纪时保留；张士乔欲诛未执行，后赴水死确日与地点未给，不硬定死亡年和地点。'},
      {'paragraph_id':Q[12]['id'],'note':'同州求援与七月遣军分录，李存审复用符存审；未提前录后文到达或战果。'},
      {'paragraph_id':Q[13]['id'],'note':'北巡诏、韩昭授官、八月启行、拒谏、九月安远分阶段；补书狎客背景未冒作本年任官证明。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
