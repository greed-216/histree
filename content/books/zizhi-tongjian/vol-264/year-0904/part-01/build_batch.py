"""Curate Tongjian 264, year 904, consecutive paragraphs 1–4."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 12))
primary = 'tongjian-264-903-yearend'
early = 'tongjian-264-904-early'
old_cui = 'jiutangshu-020-cui-yin'
old_move = 'jiutangshu-020-relocation'
old_liang = 'jiuwudaishi-002-904'
new_ya = 'xintangshu-082-ya-wang'
new_duan = 'xintangshu-082-duan-wang'
new_jia = 'xintangshu-082-jia-wang'
B = {'format_version': 1, 'batch_key': 'zztj-v264-y0904-p001-p004',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary, P.parent.parent / 'year-0903/part-09/sources/library' / primary, '10d7ddd', '司马光等'),
    (early, P / 'sources/library' / early, 'da18066', '司马光等'),
    (old_cui, P / 'sources/library' / old_cui, 'da18066', '刘昫等'),
    (old_move, P / 'sources/library' / old_move, 'da18066', '刘昫等'),
    (old_liang, P / 'sources/library' / old_liang, 'da18066', '薛居正等'),
    (new_ya, P / 'sources/library' / new_ya, 'da18066', '欧阳修等'),
    (new_duan, P / 'sources/library' / new_duan, 'da18066', '欧阳修等'),
    (new_jia, P / 'sources/library' / new_jia, 'da18066', '欧阳修等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary, early)}
for n in range(1, 5):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','邪律阿保机':'耶律阿保机','硃友谅':'朱友谅','李继徽':'杨崇本','独孤捐':'独孤损','侯矩':'王宗矩','张濬':'张浚','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审','王宗本':'谢从本','硃延寿':'朱延寿','王坛':'王檀','坛':'王檀','硃氏（杨行密夫人）':'朱氏（杨行密夫人）','郭行頵':'郭行悰','侯矩':'王宗矩','硃友伦':'朱友伦','硃全忠':'朱温','邪律阿保机':'耶律阿保机','硃友谅':'朱友谅','李继徽':'杨崇本','独孤捐':'独孤损','侯矩':'王宗矩','张濬':'张浚'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0904_01_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷264·天祐元年（904）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role, quote=None):
    canonical = aliases.get(name, name)
    if canonical in people:
        return people[canonical]
    if canonical in registry:
        row = dict(registry[canonical], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + canonical, name=canonical, aliases=[], era='晚唐', birth_year=None,
                   death_year=None, description=f'《资治通鉴》卷264天祐元年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=904):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_264_0904_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '904年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '904年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_264_0904_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_264_0904_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 1: accusations, dismissals, appointments, and Cui Yin's killing.
event('zhu_accuses_cui','朱全忠密奏崔胤专权，请诛郑元规、陈班等',1,
      '春，正月，全忠密表司徒兼侍中、判六军十二卫事、充盐铁转运使、判度支崔胤专权乱国，离间君臣，并其党刑部尚书兼京兆尹、六军诸卫副使郑元规、威远军使陈班等，皆请诛之。',
      [('朱温','密奏指控者'),('崔胤','被指控者'),('郑元规','被请诛者'),('陈班','被请诛者')],
      when='904年正月；确日未载',place='长安',
      note='“专权乱国”“其党”是朱全忠密奏的指控，不能未经核验当成事实。')
event('cui_zheng_chen_demoted','唐廷乙巳贬崔胤、郑元规与陈班，丙午宣其罪状',1,
      '乙巳，诏责授胤太子少傅、分司，贬元规循州司户，班凑州司户。丙午，下诏罪状胤等。',
      [('李杰','下诏者'),('崔胤','责授者'),('郑元规','贬官者'),('陈班','贬官者')],
      when='904年正月乙巳、丙午',place='长安',
      note='诏书与实际处死分开；“凑州”照底本原字，地名疑讹待核。')
event('cui_replacement_ministers','唐廷任裴枢、独孤损分掌军政，并以崔远、柳璨同平章事',1,
      '以裴枢判左三军事、充盐铁运使，独孤捐判右三军事、兼判度支。胤所募兵并纵遣之。以兵部尚书崔远为中书侍郎，翰林学士、左拾遗柳璨为右谏议大夫，并同平章事。',
      [('裴枢','判左三军事'),('独孤损','判右三军事'),('崔远','新任同平章事'),('柳璨','新任同平章事'),('崔胤','所募兵被纵遣者')],
      when='904年正月丙午后；确日未载',place='长安',
      note='“独孤捐”按前一年独孤损同人归并，原文留字；裴枢等职务各有不同，未把军兵遣散归责于其个人。')
event('zhu_youliang_kills_cui','朱全忠戊申密令朱友谅围第杀崔胤及郑元规、陈班等',1,
      '戊申，硃全忠密令宿卫都指挥使硃友谅以兵围崔胤第，杀胤及郑元规、陈班并胤所亲厚者数人。',
      [('朱温','密令者'),('朱友谅','率兵围杀者'),('崔胤','被杀者'),('郑元规','被杀者'),('陈班','被杀者')],
      when='904年正月戊申',place='长安',
      note='《旧唐书》昭宗纪将崔胤等被杀系于903年十二月丙申，与《通鉴》此处纪年日不同，留待并列。')

# 2: prelude and the forced move from Chang'an toward Luoyang.
event('zhu_prepares_luoyang','朱全忠此前屡请迁都洛阳，并令张全义修宫室',2,
      '初，上在华州，硃全忠屡表请上迁都洛阳，上虽不许，全忠常令东都留守佑国军节度使张全义缮修宫室。',
      [('李杰','此前拒迁者'),('朱温','屡次请迁并命修宫者'),('张全义','修东都宫室者')],
      when='“初”追叙；上在华州以来，确年未载',year=None,place='华州、洛阳',
      note='前述是迁都旧议及预备，未写成904年正月才首次提出。')
event('yang_family_held','朱全忠攻克邠州后质杨崇本家属于河中并私近其妻',2,
      '全忠之克邠州也，质静难军节度使杨崇本妻子于河中。崇本妻美，全忠私焉，既而归之。',
      [('朱温','扣押家属并私近其妻者'),('杨崇本','家属被扣押者'),('杨崇本妻（姓名未载）','遭扣押者')],
      when='“初”追叙；邠州失守后，确日未载',year=None,place='河中',
      note='“私焉”依原书照述，不推定女子自愿或补姓名；扣押背景及后归并列。')
event('yang_rejoins_li_maozhen','杨崇本怒而联李茂贞攻京畿，恢复李继徽姓名',2,
      '崇本怒，使谓李茂贞曰：“唐室将灭，父何忍坐视之乎！”遂相与连兵侵逼京畿，复姓名为李继徽。',
      [('杨崇本','联兵并恢复旧名者'),('李茂贞','联兵者')],
      when='904年正月己酉前；确日未载',place='京畿',
      note='“唐室将灭”为杨崇本说辞；李继徽是杨崇本已有别名，未另建人。')
event('zhu_stations_hezhong','朱全忠己酉引兵屯河中',2,
      '己酉，全忠引兵屯河中。',
      [('朱温','领兵屯驻者')],when='904年正月己酉',place='河中')
event('kou_petitions_relocation','寇彦卿丁巳奉朱全忠表请迁都，裴枢促百官东行',2,
      '丁巳，上御延喜楼，硃全忠遣牙将寇彦卿奉表，称邠、歧兵逼畿甸，请上迁都洛阳。及下楼，裴枢已得全忠移书，促百官东行。',
      [('李杰','在延喜楼受表者'),('朱温','遣奏与移书者'),('寇彦卿','奉表者'),('裴枢','促百官东行者')],
      when='904年正月丁巳',place='长安延喜楼',
      note='表中迁都理由属于朱全忠奏词；邠歧出兵与迁都决定不可混为同一行为。')
event('chang_an_residents_moved','长安士民戊午被驱徙东迁',2,
      '戊午，驱徙士民，号哭满路，骂曰：“贼臣崔胤召硃温来倾覆社稷，使我曹流离至此！”老幼繦属，月馀不绝。',
      [('朱温','东迁的主导方'),('崔胤','被士民咒骂者')],
      when='904年正月戊午起；延续月余',place='长安',
      note='骂语归于迁徙士民，不据其责难判定崔胤直接下令迁徙；原文未具驱徙执行者。')
event('emperor_departs_changan','唐昭宗壬戌离长安，朱军毁宫室民舍运材东下',2,
      '壬戌，车驾发长安，全忠以其将张廷范为御营使，毁长安宫室百司及民间庐舍，取其材，浮渭河而下，长安自此遂丘墟矣。',
      [('李杰','被迫离京者'),('朱温','任御营使及毁城主导者'),('张廷范','御营使')],
      when='904年正月壬戌',place='长安、渭河',
      note='拆毁、运材与昭宗出城同段记载；“丘墟”是史书概括，不另造灾损数量。')
event('zhu_builds_luoyang','朱全忠征诸镇工匠与财货营建洛阳宫室',2,
      '全忠发河南、北诸镇丁匠数万，令张全义治东都宫室，江、浙、湖、岭诸镇附全忠者，皆输货财以助之。',
      [('朱温','征人征财者'),('张全义','营造主持者')],
      when='904年正月至二月间；确日未载',place='洛阳',
      note='“数万”为主书约数；无具体各镇名单和贡额。')
event('emperor_huazhou','唐昭宗甲子抵华州，对夹道民众说将不复为主',2,
      '甲子，车驾至华州，民夹道呼万岁，上泣谓曰：“勿呼万岁，朕不复为汝主矣！”馆于兴德宫',
      [('李杰','抵华州并发言者')],when='904年正月甲子',place='华州兴德宫',
      note='“不复为汝主”是唐昭宗当时的感叹，并非当天已被废。')
event('emperor_stops_shan','唐昭宗二月乙亥抵陕州，因洛阳宫未成暂驻',2,
      '二月，乙亥，车驾至陕，以东都宫室未成，驻留于陕。',
      [('李杰','暂驻者')],when='904年二月乙亥',place='陕州',
      note='“至陕”与“驻留”同日条；未推断停留结束日。')
event('zhu_empress_audience','朱全忠丙子自河中来朝，何皇后向其哭诉',2,
      '丙子，全忠自河中来朝，上延全忠入寝室见何后，后泣曰：“自今大家夫妇委身全忠矣！”',
      [('朱温','来朝者'),('李杰','引见者'),('何氏（唐昭宗皇后）','哭诉者')],
      when='904年二月丙子',place='陕州',
      note='“委身全忠”是何皇后原话，不能写成正式禅让或授官。')

# 3: five distinct princes; the earlier 898 雅王禛 was miswritten 祯 in a legacy batch.
event('five_princes_enfeoffed','唐昭宗甲申封五位皇子为端、丰、和、登、嘉王',3,
      '甲申，立皇子祯为端王，祁为丰王，福为和王，禧为登王，祐为嘉王。',
      [('李杰','册封者'),('李祯（端王）','受封端王者'),('李祁','受封丰王者'),('李福','受封和王者'),('李禧','受封登王者'),('李祜','受封嘉王者')],
      when='904年二月甲申',
      note='《新唐书》卷82明端王禎天祐元年始封、嘉王作祜。本站此前898年雅王“李祯”应核为李禛，不能直接复用该实体；本批端王暂用带王号的独立稳定主体。')

# 4: the imperial appeal, a failed relief attempt, and Wang Jian's emergency decrees.
event('emperor_appeals_wang_jian','唐昭宗遣间使持御札告难于王建',4,
      '上遣间使以御札告难于王建',
      [('李杰','遣使求援者'),('王建','受御札者')],
      when='904年二月甲申后；确日未载',
      note='御札具体辞句未在本段摘录，不能补造全文。')
event('wang_jian_relief_fails','王建命王宗祐会凤翔兵迎驾，至兴平遇汴兵不进而还',4,
      '建以邛州剌史王宗祐为北路行营指挥使，将兵会凤翔兵迎车驾，至兴平，遇汴兵，不得进而还。',
      [('王建','任命与遣军者'),('王宗祐','率军者'),('李杰','迎驾目标')],
      when='904年二月甲申后；确日未载',place='邛州、兴平',
      note='底本作“剌史”，按刺史官名展示且原文留字；援军未能推进，不写成交战胜负。')
event('wang_jian_ink_edicts','王建开始以墨制任官，称车驾返长安后奏闻',4,
      '建始自用墨制除官，云“俟车驾还长安表闻。”',
      [('王建','自行任官者')],
      when='904年二月甲申后；确日未载',
      note='“俟车驾还长安表闻”为王建宣称，不证明昭宗后来已收到奏报。')

for code,a,b,kind,description,n,quote,note in [
    ('yang_wife','杨崇本妻（姓名未载）','杨崇本','妻子','这位姓名未载的女子是杨崇本的妻子。',2,'崇本妻美','原文只以“崇本妻”称之，不补本姓。'),
    ('zhen_son','李祯（端王）','李杰','儿子','端王李祯是唐昭宗的儿子。',3,'皇子祯为端王','端王祯与此前雅王禛应为不同皇子；旧批次雅王错误待修订。'),
    ('qi_son','李祁','李杰','儿子','丰王李祁是唐昭宗的儿子。',3,'祁为丰王','“皇子”统领本句并列五人。'),
    ('fu_son','李福','李杰','儿子','和王李福是唐昭宗的儿子。',3,'福为和王','“皇子”统领本句并列五人。'),
    ('xi_son','李禧','李杰','儿子','登王李禧是唐昭宗的儿子。',3,'禧为登王','“皇子”统领本句并列五人。'),
    ('hu_son','李祜','李杰','儿子','嘉王李祜是唐昭宗的儿子。',3,'祐为嘉王','《新唐书》卷82作嘉王祜；主书底本祐与此前德王李祐不可归并。'),
]:
    pa=person(a,n,kind,quote)
    pb=person(b,n,kind,quote)
    key='relationship_zztj_264_0904_'+code
    B['person_relationships'].append(dict(key=key,person_a_key=pa,person_b_key=pb,
        relation_type=kind,description=description,status='draft'))
    claim('person_relationship',key,'description',description,n,quote,note)

extra(old_cui,'event','event_zztj_264_0904_zhu_youliang_kills_cui','time_original',
      '《旧唐书》昭宗纪将朱友谅杀崔胤等系于天复三年十二月丙申。',
      '丙申，制守司徒、侍中、太清宮使、弘文館大學士、延資庫使、判六軍十二衛事、諸道鹽鐵轉運使、判度支、上柱國、魏國公、食邑四千五百戶崔胤責授太子賓客，守刑部尚書、兼京兆尹、六軍諸衛副使鄭元規責授循州司戶。是日，汴州扈駕指揮使朱友諒殺胤及元規',1,'conflicts',
      '该段起首为“十二月丁卯朔”，故丙申属903年十二月；与《通鉴》904年正月戊申不合。')
extra(old_liang,'event','event_zztj_264_0904_zhu_youliang_kills_cui','description',
      '《旧五代史》梁太祖纪亦把朱友谅杀崔胤置于天祐元年正月。',
      '帝乃密令護駕都指揮使硃友諒矯昭宗命，收宰相崔允、京兆尹鄭元規等殺之',1,'corroborates',
      '旧书本段起首为天祐元年正月，作崔允；只印证年份月份，不核定主书的戊申日。')
extra(old_move,'event','event_zztj_264_0904_emperor_departs_changan','time_original',
      '《旧唐书》昭宗纪将车驾发长安记为丁巳。',
      '丁巳，車駕發京師',2,'conflicts',
      '《通鉴》本段作正月壬戌，日分不同；旧书“京师”指长安，不擅自折衷。')
extra(new_ya,'event','event_zztj_264_0904_five_princes_enfeoffed','description',
      '《新唐书》卷82记光化元年封雅王者为禛，而非本次端王禎。',
      '雅王禛，光化元年始王',3,'adds',
      '校核旧批次同名碰撞，雅王应另作李禛；此次端王暂用独立稳定主体。')
extra(new_duan,'event','event_zztj_264_0904_five_princes_enfeoffed','description',
      '《新唐书》卷82记端王禎天祐元年始王，并与丰和登嘉四王同封。',
      '端王禎，天祐元年始王，與豐、和、登、嘉四王同封',3,'corroborates',
      '印证同封与端王身份；不复用旧批次误作雅王的李祯实体。')
extra(new_jia,'person',people['李祜'],'description',
      '《新唐书》卷82记嘉王为祜，主书本段作祐。',
      '嘉王祜',3,'conflicts',
      '同封背景确定嘉王人选，保留两书名讳异文；与已录德王李祐分开。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,5):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天祐元年第1—4段连续处理；崔胤被杀与迁都日分异说并列，五王身份逐一校核。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=904,
    primary_source_key=primary,primary_source_keys=[primary,early],
    paragraphs=[Q[n]['id'] for n in range(1,5)],next_paragraph=Q[5]['id'],
    coverage='卷264天祐元年共11个非空段落中的第1—4段连续处理；正月崔胤之死与迁都，二月五王册封、王建救驾。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
