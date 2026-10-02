"""Curate Tongjian 267, year 909, consecutive paragraphs 1–25."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 61))
main1 = 'tongjian-267-909-spring'
main2 = 'tongjian-267-909-summer'
old_gao = 'jiuwudaishi-132-gaowanxing'
new_gao = 'xinwudaishi-040-gaowanxing'
new_suzhou = 'xinwudaishi-067-suzhou'
old_wang = 'jiuwudaishi-019-wangzhongshi'
new_liu_pre = 'xinwudaishi-044-liuzhijun-pre'
new_liu_revolt = 'xinwudaishi-044-liuzhijun-revolt'
new_wang = 'xinwudaishi-002-wangzhongshi'
B = {'format_version': 1, 'batch_key': 'zztj-v267-y0909-p001-p025',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (main1, P / 'sources/library' / main1, '8a032ff7', '司马光等'),
    (main2, P / 'sources/library' / main2, '8a032ff7', '司马光等'),
    (old_gao, P / 'sources/library' / old_gao, '8a032ff7', '薛居正等'),
    (new_gao, P / 'sources/library' / new_gao, '8a032ff7', '欧阳修等'),
    (new_suzhou, P / 'sources/library' / new_suzhou, '8a032ff7', '欧阳修等'),
    (old_wang, P / 'sources/library' / old_wang, '8a032ff7', '薛居正等'),
    (new_liu_pre, P / 'sources/library' / new_liu_pre, '8a032ff7', '欧阳修等'),
    (new_liu_revolt, P / 'sources/library' / new_liu_revolt, '8a032ff7', '欧阳修等'),
    (new_wang, P / 'sources/library' / new_wang, '8a032ff7', '欧阳修等'),
]
source_dirs = {sk: d for sk, d, _, _ in source_specs}
manifest = []
for sk, d, commit, author in source_specs:
    record = json.loads((d / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((d / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=sk, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=sk, file=os.path.relpath(d / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((d / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保原字、空格与换行。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (main1, main2)}
for n in range(1, 26):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/267.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'徐知诰':'李昪', '吕兗':'吕兖', '李继徽':'杨崇本', '王景仁':'王茂章', '硃景':'朱景', '硃全忠':'朱温', '蜀主':'王建', '吴越王镠':'钱镠', '晋王克用':'李克用', '晋王存勖':'李存勖', '济阴王':'唐昭宣帝', '唐哀皇帝':'唐昭宣帝', '存勗':'李存勖', '克寧':'李克宁'}
people, used, reused, supplements = {}, {}, set(), []
legacy_events = {row['key']: row for row in json.loads((ROOT / 'content/later-liang-907-923/content-batch.json').read_text())['events']}
legacy_relations = {}
for archive in ('content/late-tang-zhu-wen-early/content-batch.json',
                'content/year-0907/content-batch.json',
                'content/later-liang-907-923/content-batch.json',
                'content/books/zizhi-tongjian/vol-260/year-0895/part-04/content-batch.json',
                'content/books/zizhi-tongjian/vol-263/year-0902/part-02/content-batch.json'):
    for row in json.loads((ROOT / archive).read_text())['person_relationships']:
        if row['key'] in legacy_relations:
            assert legacy_relations[row['key']] == row
        legacy_relations[row['key']] = row

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_267_0909_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷267·开平三年（909）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical,
                   aliases=[], era='五代十国', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷267开平三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=909, time_quote=None, reuse_key=None):
    assert quote in Q[n]['text'], (n, quote)
    key = reuse_key or ('event_zztj_267_0909_' + code)
    if reuse_key:
        assert not actors, 'Published event edges are preserved by stable key'
        if key not in {row['key'] for row in B['events']}:
            row = dict(legacy_events[reuse_key], status='draft')
            B['events'].append(row)
        reused.add(key)
        desc = title + '。'
    else:
        desc = title + '。'
        B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                                time_original=when or '909年本段条；确日未载', dynasty='五代十国', description=desc,
                                phases=[], location_name=place, location_modern_name=None, location_lat=None,
                                location_lng=None, location_precision='unknown',
                                location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '909年本段条；确日未载', n, time_quote or quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_267_0909_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def relation(key, n, quote, note):
    assert quote in Q[n]['text']
    row = legacy_relations[key]
    if key not in {item['key'] for item in B['person_relationships']}:
        B['person_relationships'].append(dict(row, status='draft'))
        reused.add(key)
    claim('person_relationship',key,'description',row['description'],n,quote,note)

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_267_0909_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1–3: Liang relocates its ritual center and records fiscal and celestial changes.
event('luoyang_temple_move','后梁迁太庙神主于洛阳，朱温由大梁赴洛阳行郊礼并大赦',1,
      '春，正月，己巳，迁太庙神主于洛阳。甲戌，帝发大梁。壬申，以博王友文为东都留守。己卯，帝至洛阳。庚寅，飨太庙。辛巳，祀圆丘，大赦。',
      [('朱温','自大梁赴洛阳并行郊礼的后梁皇帝'),('朱友文','受任东都留守')],
      when='909年正月己巳迁神主、甲戌发大梁、己卯至洛阳、辛巳大赦',place='大梁、洛阳',
      note='迁神主、启程、任留守、到洛阳与祭祀大赦有不同干支日；908年仅拟迁都，909年才有实际行动。')
event('liang_full_salaries','后梁开始给百官全额俸禄',2,
      '丙申，以用度稍充，初给百官全俸。',
      when='909年正月丙申',place='后梁朝廷',
      note='“用度稍充”是主书所述背景；未量化财政余额。')
event('eclipse_feb909','909年二月丁酉朔日食',3,
      '二月，丁酉朔，日有食之。',when='909年二月丁酉朔',
      note='保留主书纪日，未以现代天文计算改写。')

# 4: Yan-zhou mutiny; Old/New Five Histories disagree about actor and date.
event('liu_wanzi_killed','李延实攻杀刘万子并占延州，高万兴兄弟降梁',4,
      '李继徽使延州牙将李延实图之。延实因万子葬胡敬璋，攻而杀之，遂据延州。',
      [('刘万子','于胡敬璋葬礼期间被杀'),('杨崇本','以李继徽之名遣李延实图刘万子'),('李延实','据《通鉴》攻杀刘万子并据延州')],
      when='909年二月条；葬礼确日未载',place='延州',
      note='杨崇本即李继徽；新五代史作许从实杀刘万子且系于开平二年，旧五代史作高万兴、万金六年二月杀之，异说不强并。')
extra(old_gao,'event','event_zztj_267_0909_liu_wanzi_killed','description',
      '《旧五代史》卷一百三十二系刘万子被杀于“六年二月”，并记高万兴、万金在葬礼攻杀。',
      '六年二月，萬子葬敬璋，將佐皆集於葬所，萬興、萬金因會縱兵攻萬子，殺之',4,'conflicts',
      '旧书“六年”按本传上文唐天祐五年冬承接，约当909；凶手与《通鉴》李延实不同，待纸本校。')
extra(new_gao,'event','event_zztj_267_0909_liu_wanzi_killed','description',
      '《新五代史》卷四十系葬礼于梁开平二年，并记许从实杀刘万子。',
      '梁開平二年，葬於州南，萬子在會，其將許從實殺萬子',4,'conflicts',
      '新史年份作908，与《通鉴》909年条不同；杀者亦异，保留原文不擅选定。')
event('gao_brothers_defect','高万兴、高万金率部降梁，岐方翟州守将亦降',4,
      '马军都指挥使河西高万兴与其弟万金闻变，以其众数千人诣刘知俊降。岐王置翟州于鄜城，其守将亦降。',
      [('高万兴','率部投降后梁'),('高万金','随兄高万兴投降后梁'),('刘知俊','接受高万兴兄弟投降的梁将')],
      when='909年二月刘万子被杀后；确日未载',place='鄜城、延州',
      note='“闻变”明确在刘万子事变之后；新史说高万兴兄弟当时在边境，与主书可并列。')
B['person_relationships'].append(dict(key='relationship_person_高万兴_person_高万金_兄长',
    person_a_key=people['高万兴'],person_b_key=people['高万金'],relation_type='兄长',
    description='高万兴是高万金的兄长。',status='draft'))
claim('person_relationship','relationship_person_高万兴_person_高万金_兄长','description',
      '高万兴是高万金的兄长。',4,'高万兴与其弟万金',
      '“其弟”明载长幼；两人不是同一人物。')

# 5–12: Western marches, a Huainan appointment and enfeoffments.
event('liang_western_march','朱温三月离洛阳，杨师厚兼潞州招讨使',5,
      '三月，甲戌，帝发洛阳。以山南东道节度使杨师厚兼潞州四面行营招讨使。',
      [('朱温','离洛阳西行的后梁皇帝'),('杨师厚','兼潞州四面行营招讨使')],
      when='909年三月甲戌',place='洛阳',
      note='本段仅载发洛阳及任命，后续到河中见下一段。')
event('liang_reaches_hezhong','朱温至河中并调兵会高万兴攻丹、延',6,
      '庚辰，帝至河中，发步骑会高万兴兵取丹、延。',
      [('朱温','到河中并发兵的梁帝'),('高万兴','奉命会兵取丹延')],
      when='909年三月庚辰',place='河中、丹州、延州',
      note='“发兵会”是出兵部署，不能在本段记为已得丹延。')
event('han_xun_yingchuan','韩逊受封颍川王',7,
      '丙戌，以朔方节度使兼中书令韩逊为颍川王。',
      [('韩逊','获封颍川王')],when='909年三月丙戌',
      note='“唐末据本镇”为追叙，不另定为909年事件。')
event('cui_gongshi_submits','丹州刺史崔公实请降后梁',8,
      '辛卯，丹州刺史崔公实请降。',
      [('崔公实','请求归降的丹州刺史')],when='909年三月辛卯',place='丹州',
      note='只确认请降，未据此推定本人或全城随后处置。')
event('xu_wen_shengzhou','徐温领升州刺史并遣假子徐知诰经营金陵舟师',9,
      '徐温以金陵形胜，战舰所聚，乃自以淮南行军副使领升州刺史，留广陵，以其假子元从指挥使知诰为升州队遏兼楼船副使，往治之。',
      [('徐温','领升州刺史并留广陵主持军府'),('徐知诰','徐温假子，赴升州负责楼船')],
      when='909年三月后条；确日未载',place='广陵、升州、金陵',
      note='徐知诰即后来的李昪，复用既有稳定key；徐温自己留广陵，不能写为同时移驻金陵。')
relation('relationship_person_徐温_person_李昪_养父',9,'以其假子元从指挥使知诰为升州队遏兼楼船副使',
         '“假子”确认收养关系；沿用895年已发布的徐温→李昪养父关系，知诰为其当时称名。')
event('liu_zhijun_yanzhou','刘知俊四月攻延州，刘儒另围坊州',10,
      '夏，四月，丙申朔，刘知俊移军攻延州，李延实婴城自守。知俊遣白水镇使刘儒分兵围坊州。',
      [('刘知俊','移军攻延州的梁将'),('李延实','守延州的将领'),('刘儒','奉命分兵围坊州')],
      when='909年四月丙申朔',place='延州、坊州',
      note='围攻与攻克分开，延州归降见第12段。')
event('wang_shenzhi_liu_yin_kings','后梁册王审知为闽王、刘隐为南平王',11,
      '庚子，以王审知为闽王，刘隐为南平王。',
      [('王审知','受封闽王'),('刘隐','受封南平王')],when='909年四月庚子',
      note='称王是后梁授封；不据此推定二人实际独立建国时间。')
event('yanzhou_taken','刘知俊攻克延州，李延实投降',12,
      '刘知俊克延州，李延实降。',
      [('刘知俊','攻克延州'),('李延实','向刘知俊投降')],
      when='909年四月条；确日未载',place='延州',
      note='接第10段四月朔围攻，未载具体克城日。')

# 13–18: Suzhou defense, relief, and Huainan's new examination administration.
event('suzhou_defense_works','孙琰用轮索与网抵御淮南军攻苏州',13,
      '淮南兵围苏州，推洞屋攻城，吴越将临海孙琰置轮于竿首，垂絙投锥以揭之，攻者尽露，砲至则张网以拒之，淮南人不能克。',
      [('孙琰','运用城防器具抵御淮南军的吴越将领')],
      when='909年四月后条；围城确日未载',place='苏州',
      note='“不能克”指这阶段未攻下苏州，仍要与后续内外夹击分开。')
event('qian_liao_suzhou_relief','钱镠遣钱镖、杜建徽等率兵援苏州',13,
      '吴越王镠遣牙内指挥使钱镖、行军副使杜建徽等将兵救之。',
      [('钱镠','遣援军的吴越王'),('钱镖','率兵救苏州的牙内指挥使'),('杜建徽','率兵救苏州的行军副使')],
      when='909年四月后条；确日未载',place='苏州',
      note='出兵救援与第16段已成功解围分开。')
event('sima_fu_suzhou_entry','司马福潜入苏州，使城中与援军号令相应',14,
      '吴越游弈都虞候司马福欲潜行入城，故以竿触网，敌闻铃声举网，福因得过，凡居水中三日，乃得入城。由是城中号令与援兵相应',
      [('司马福','避过淮南水网潜入苏州并沟通援军')],
      when='909年苏州被围时；历时三日',place='苏州',
      note='“居水中三日”为主书记述；并非三日战役起止精确日。')
extra(new_suzhou,'event','event_zztj_267_0909_sima_fu_suzhou_entry','description',
      '《新五代史》卷六十七也记司马福以竹触铃网，趁网举时入城。',
      '水軍卒司馬福，多智而善水行，乃先以巨竹觸網',14,'corroborates',
      '新史以王朝早期主名叙此役，未据此更改909年主书编年。')
event('lu_renzhang_message','钱镠遣陆仁章入苏州传信并取得回报',15,
      '及苏州被围，使仁章通信入城，果得报而返。',
      [('钱镠','派陆仁章往返苏州传信'),('陆仁章','入城传信并返回的园卒')],
      when='909年苏州围城期间；确日未载',place='苏州',
      note='本段“累迁两府军粮都监使”为后续经历，不全系于909年。')
claim('event','event_zztj_267_0909_lu_renzhang_message','description',
      '陆仁章后来累迁两府军粮都监使。',15,
      '累迁两府军粮都监使，卒获其用',
      '“累迁”是后见追叙，未给具体授官年份。')
event('suzhou_relief_victory','吴越内外夹击淮南围军，周本败退',16,
      '辛亥，吴越兵内外合击淮南兵，大破之，擒其将何朗等三十馀人，夺战舰二百艘。周本夜遁，又追败之于皇天荡。',
      [('周本','淮南主将，败后夜撤'),('何朗','据《通鉴》记被俘的淮南将领')],
      when='909年四月辛亥、当夜及后续追击',place='苏州、皇天荡',
      note='“三十馀”“二百”为主书记数；《新五代史》被俘将领名单作闾丘直、何明，异名不强并。')
extra(new_suzhou,'event','event_zztj_267_0909_suzhou_relief_victory','description',
      '《新五代史》卷六十七亦记吴越内外合攻而败周本，但记被俘将领为闾丘直、何明。',
      '淮人以為神，遂大敗之，本等走，擒其將閭丘直、何明等',16,'conflicts',
      '主书记何朗；“何朗”与“何明”或为异文、或为不同人，保留两书不合并身份。')
event('zhong_taizhang_rearguard','钟泰章以二百精兵殿后，阻吴越追军',16,
      '钟泰章将精兵二百为殿，多树旗帜于菰蒋中，追兵不敢进而还。',
      [('钟泰章','为淮南军殿后的将领')],
      when='909年苏州败退后；确日未载',place='皇天荡附近',
      note='“二百”为主书记数；不将本段视为淮南军转胜。')
event('gao_wanxing_baoda','李彦博、李彦昱弃城赴岐，高万兴与牛存节受梁授镇',17,
      '岐王所署保大节度使李彦博、坊州刺史李彦昱皆弃城奔凤翔，鄜州都将严弘倚举城降。己未，以高万兴为保塞节度使，以绛州刺史牛存节为保大节度使。',
      [('李彦博','弃保大镇赴凤翔'),('李彦昱','弃坊州赴凤翔'),('严弘倚','率鄜州降梁'),('高万兴','受任保塞节度使'),('牛存节','受任保大节度使')],
      when='909年四月己未授高万兴、牛存节；弃城稍早',place='鄜州、坊州',
      note='岐方弃城、严弘倚降与梁任命同段，未据此细绘即时政区界限。')
event('huainan_examinations','淮南初置选举，由骆知祥主持',18,
      '淮南初置选举，以骆知祥掌之。',
      [('骆知祥','主持淮南初设选举')],
      when='909年四月后条；确日未载',place='淮南',
      note='“初置选举”按主书记录制度起点，不自行补入具体科目或录取人数。')

# 19–21: the recall and execution of Wang Zhongshi.
event('liuzhijun_binzhou_order','朱温命刘知俊进取邠州，刘知俊以缺粮辞而被召还',19,
      '五月，丁卯，帝命刘知俊乘胜取邠州，知俊难之，辞以阙食，乃召还。',
      [('朱温','命取邠州并召回刘知俊的梁帝'),('刘知俊','以粮食不足辞攻邠州的梁将')],
      when='909年五月丁卯',place='邠州',
      note='取邠州是命令，未实际完成；“阙食”为刘知俊所辞，不自行验证粮况。')
extra(new_liu_pre,'event','event_zztj_267_0909_liuzhijun_binzhou_order','description',
      '《新五代史》卷四十四亦记朱温令刘知俊攻邠州，刘知俊以军食不继而未行。',
      '遣知俊復攻邠州，知俊以軍食不給未行',19,'corroborates',
      '这是新史记述的理由，与主书“辞以阙食”并列；未将其改写为已克邠州。')
event('wangzhongshi_recalled','朱温召王重师入朝，任刘捍为佑国留后',20,
      '己巳，召重师入朝，以左龙虎统军刘捍为佑国留后。',
      [('朱温','召王重师并任刘捍的梁帝'),('王重师','被召离长安的佑国节度使'),('刘捍','受任佑国留后')],
      when='909年五月己巳',place='长安',
      note='“怒其贡奉不时”为主书所述朱温不满，不能单独推为王重师有通岐事实。')
claim('event','event_zztj_267_0909_wangzhongshi_recalled','description',
      '朱温于癸酉从河中出发，己卯抵洛阳。',20,
      '癸酉，帝发河中；己卯，至洛阳',
      '是梁帝行程，与王重师被召离镇同段不同日。')
event('wangzhongshi_executed','王重师遭刘捍指控通邠岐，贬官后被赐死并族诛',21,
      '王重师不为礼，捍谮之于帝，云重师潜与邠、岐通。甲申，贬重师溪州刺史，寻赐自尽，夷其族。',
      [('王重师','被贬、赐死并遭族诛的梁将'),('刘捍','向朱温指控王重师潜通邠岐')],
      when='909年五月甲申贬官、其后赐死；确日未载',place='长安、洛阳',
      note='“潜与邠岐通”是刘捍的指控，主书用“谮”；《新五代史》系处死于五月己卯，《旧五代史》另述因擅遣兵败而受刑，异说并列。')
extra(new_wang,'event','event_zztj_267_0909_wangzhongshi_executed','time_original',
      '《新五代史》卷二记五月己卯朱温自河中返后杀王重师。',
      '五月己卯，至自河中，殺佑國軍節度使王重師',21,'conflicts',
      '主书己卯仅载帝至洛阳，甲申贬官后才“寻赐自尽”；两书日期先后不合。')
extra(old_wang,'event','event_zztj_267_0909_wangzhongshi_executed','description',
      '《旧五代史》卷十九记刘捍构陷之外，另以王重师擅遣张君练攻邠凤失利作为朱温追斩的缘由。',
      '擅遣裨將張君練縱兵深入邠、鳳，君練敗北。太祖聞之，怒其專擅，因追而斬之',21,'adds',
      '旧书传记称“斩”，主书为“贬、赐自尽、夷族”；处置方式及动机并列，旧书注文另引《通鉴》不算独立确证。')
extra(new_liu_pre,'event','event_zztj_267_0909_wangzhongshi_executed','description',
      '《新五代史》刘知俊传称王重师无罪被杀，刘知俊因此加深恐惧。',
      '王重師無罪見殺，知俊益懼，不自安',21,'adds',
      '“无罪”是新史作者评价；此处只作为刘知俊叛变背景的书证。')

# 22–25: Liu Shouwen's capture and Liu Zhijun's break with Liang.
event('liu_shouwen_captured','刘守文在鸡苏胜后被元行钦擒获，刘守光军进攻沧州',22,
      '守文单马立于陈前，泣谓其众曰：“勿杀吾弟！”守光将元行钦识之，直前擒之，沧德兵皆溃。守光囚之别室，栫之藂棘，乘胜进攻沧州。',
      [('刘守文','被元行钦擒获并囚禁'),('刘守光','囚兄并乘胜进攻沧州'),('元行钦','识别并擒刘守文的刘守光部将')],
      when='909年五月后条；确日未载',place='鸡苏、沧州',
      note='刘守文先在鸡苏胜，后孤身前出被擒；“勿杀吾弟”是其战场呼吁，不代表刘守光随即宽释。')
relation('relationship_person_刘守文_person_刘守光_兄长',22,'勿杀吾弟',
         '主书刘守文自称守光为“吾弟”，复用既有兄长关系，不反向建重复边。')
event('liu_yanzuo_cangzhou','吕兖、孙鹤推刘延祚守沧州',22,
      '沧州节度判宫吕兗、孙鹤推守文子延祚为帅，乘城拒守。',
      [('吕兗','推刘延祚守沧州的节度判官'),('孙鹤','与吕兖同推刘延祚'),('刘延祚','被推为帅守沧州的刘守文之子')],
      when='909年刘守文被擒后；确日未载',place='沧州',
      note='“吕兗”显示规范作吕兖、引文保留原字；刘延祚与907年入质的刘延祐字形不同，暂不合并。')
B['person_relationships'].append(dict(key='relationship_person_刘守文_person_刘延祚_父亲',
    person_a_key=people['刘守文'],person_b_key=people['刘延祚'],relation_type='父亲',
    description='刘守文是刘延祚的父亲。',status='draft'))
claim('person_relationship','relationship_person_刘守文_person_刘延祚_父亲','description',
      '刘守文是刘延祚的父亲。',22,'守文子延祚',
      '“守文子”明载父子；907年刘延祐是否同一人待异本及后文核，不据相似字合并。')
event('liuzhijun_defects','刘知俊以同州附岐，拘押不从将佐并袭华州',23,
      '六月，乙未朔，知俊奏称“为军民所留”，遂以同州附于岐，执监军及将佐之不从者，皆械送于岐。遣兵袭华州，逐刺史蔡敬思，以兵守潼关。',
      [('刘知俊','以同州归岐并遣兵夺华州、守潼关'),('蔡敬思','被刘知俊军逐出的华州刺史')],
      when='909年六月乙未朔',place='同州、华州、潼关',
      note='“为军民所留”是刘知俊奏辞；依主书后文行动记为附岐，但不将其自述当独立事实。')
extra(new_liu_revolt,'event','event_zztj_267_0909_liuzhijun_defects','description',
      '《新五代史》卷四十四亦记刘知俊叛梁归李茂贞，攻雍华并扼潼关。',
      '知俊遂叛，臣於李茂貞，以兵攻雍、華',23,'corroborates',
      '新史对附岐措辞为“臣於李茂贞”；主书所载同州六月朔与下一段处分仍为时间主线。')
event('liu_han_killed','刘知俊诱长安将领执刘捍，送往岐后将其杀死',23,
      '潜遣人以重利啖长安诸将，执刘捍，送于岐，杀之。',
      [('刘知俊','诱使长安将领拘刘捍并送岐'),('刘捍','被送岐后杀死')],
      when='909年六月刘知俊附岐后；确日未载',place='长安、岐',
      note='主书句末未明指杀刘捍者为谁，不把执行者归于刘知俊本人。')
event('liuzhijun_seeks_allies','刘知俊向岐、晋求兵，致书晋王预言可取两京',23,
      '知俊遣使请兵于岐，亦遣使请晋人出兵攻晋、绛，遗晋王书曰：“不过旬日，可取两京，复唐社稷。”',
      [('刘知俊','遣使求岐晋出兵并致书晋王'),('李存勖','收到刘知俊书信的晋王')],
      when='909年六月刘知俊附岐后；确日未载',place='岐、晋',
      note='取两京与复唐是刘知俊的预期和政治宣称，未作为已经实现的战果。')
event('han_xun_yancheng','韩逊奏克盐城，斩岐所署李继直',24,
      '丁未，朔方节度使韩逊奏克盐城，斩岐所署刺史李继直。',
      [('韩逊','奏报攻克盐城'),('李继直','据奏报被斩的岐方刺史')],
      when='909年六月丁未',place='盐城',
      note='“奏克”是韩逊向梁廷所报，来源未独立复核。')
event('liang_punishes_liuzhijun','朱温削刘知俊官爵，任杨师厚招讨并自洛阳出发',25,
      '庚戌，诏削知俊官爵，以山南东道节度使杨师厚为西路行营招讨使，帅侍卫马步军都指挥使刘鄩等讨之。辛亥，帝发洛阳。',
      [('朱温','下诏削刘知俊官爵并离洛阳'),('杨师厚','受任西路招讨使'),('刘鄩','随杨师厚讨刘知俊的将领'),('刘知俊','被削官爵的叛梁将领')],
      when='909年六月庚戌处分、辛亥朱温出发',place='洛阳',
      note='前段朱温称悔杀王重师为其回应辞令，不据此确认刘捍所告必假；杨师厚出军与战果分开。')
extra(new_liu_revolt,'event','event_zztj_267_0909_liang_punishes_liuzhijun','description',
      '《新五代史》卷四十四亦记朱温以王重师之死向刘知俊解释，刘知俊不答。',
      '朕固知卿以此，吾誅重師，乃劉捍誤我',25,'adds',
      '所引为朱温对刘知俊的说辞；不能直接证明刘捍所报真伪。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,26):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷267开平三年第1—25段连续处理；延州事变与王重师被杀三书异说并列，苏州围城及刘知俊叛梁分阶段记录。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=267,year=909,
    primary_source_key=main1,primary_source_keys=[main1,main2],
    paragraphs=[Q[n]['id'] for n in range(1,26)],next_paragraph=Q[26]['id'],
    coverage='卷267开平三年第1—25段连续处理；迁洛、延州事变、苏州解围、王重师受刑、刘守文被擒与刘知俊归岐。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
