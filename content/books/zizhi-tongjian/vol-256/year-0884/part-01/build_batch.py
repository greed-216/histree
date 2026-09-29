"""Curate every 884 paragraph in Tongjian volume 256; rerunnable after audit."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
paras = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in paras}
assert list(Q) == list(range(1, 22))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0884-p001-p021', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-256-884'
raw = (ROOT / 'resources/derived/tongjian/256.txt').read_bytes()
sha = hashlib.sha256(raw).hexdigest()
url = 'https://github.com/greed-216/histree/blob/fdc81a0b21a4c29dcfb4a4ecc9006df86ffe9248/resources/derived/tongjian/256.txt'
B['sources'].append(dict(key=source, title='资治通鉴·卷256', source_type='primary', author='司马光等', edition='仓库电子文本；未核纸本。引文按原文保留，疑似转录讹字单独注明。', url=url, note='卷256中和四年21段；原始电子文本与SHA-256见来源清单。'))
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources' / 'manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=sha, url=url, upstream='resources/derived/tongjian/256.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for rel in ['content/later-liang-907-923/content-batch.json', 'content/year-0907/content-batch.json', 'content/late-tang-zhu-wen-early/content-batch.json', 'content/books/zizhi-tongjian/vol-255/year-0884/part-01/content-batch.json', 'content/books/zizhi-tongjian/vol-255/year-0884/part-02/content-batch.json']:
    for row in json.loads((ROOT / rel).read_text())['people']:
        registry[row['name']] = row
alias = {'朱全忠': '朱温', '硃全忠': '朱温', '王鐸': '王铎', '硃瑄': '朱瑄', '硃瑾': '朱瑾'}
people, used, reused = {}, {}, set()

def claim(table, key, field, value, n, quote=None, note='按该段原文整理；只陈述引文支持的事实，不推定未载的日期。'):
    quote = quote or Q[n]['text']
    assert quote in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0884_01_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·中和四年（884）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{quote}；核对说明：{note}', status='draft'))

def person(name, n, role):
    name = alias.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name, aliases=[], era='晚唐', birth_year=None, death_year=None, description=f'《资治通鉴》卷256中和四年条所见人物：{name}。', biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记载{name}：{role}。', n)
    return row['key']

def event(code, title, n, when, where, description, actors=(), year=884, note=None, quote=None):
    key = 'event_zztj_256_0884_' + code
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year, time_original=when, dynasty='唐', description=description, phases=[], location_name=where, location_modern_name=None, location_lat=None, location_lng=None, location_precision='unknown', location_note='仅保留史载地名；未核坐标。' if where else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', description, n, quote, note or '按该段原文整理；未载细节不补写。')
    claim('event', key, 'time_original', when, n, quote, note or ('本段为追叙，确年待考。' if year is None else '依卷年定位；干支日未换算为公历日。'))
    for name, role in actors:
        pk = person(name, n, role)
        edge = 'participation_zztj_256_0884_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote)
    return key

def relation(a, b, kind, n, description, quote=None):
    ka, kb = person(a, n, kind), person(b, n, kind)
    key = f'relationship_{ka}_{kb}_{kind}'
    B['person_relationships'].append(dict(key=key, person_a_key=ka, person_b_key=kb, relation_type=kind, description=description, status='draft'))
    claim('person_relationship', key, 'description', description, n, quote)

# June: report, siege outcome and appointment are distinct claims in one paragraph.
event('yang_shili_fall', '杨师立自杀，郑君雄以其首出降', 1, '中和四年六月壬辰奏报；围城经过历时未详', '梓州', '高仁厚围梓州，致书城内劝降。郑君雄率众入府，杨师立自杀；郑君雄携首出降。', [('高仁厚','围城及奏报者'),('郑君雄','率众出降者'),('杨师立','自杀者')])
event('yang_son_executed', '陈敬瑄处死杨师立之子', 1, '杨师立死后；具体日未载', '城北', '陈敬瑄命人将杨师立之子钉于城北。', [('陈敬瑄','下令者'),('杨师立','被处死者之父')])
event('gao_dongchuan', '高仁厚获任东川节度使', 1, '中和四年六月条，具体日未载', '东川', '朝廷以高仁厚为东川节度使。', [('高仁厚','获任者')])
event('huang_xiaqiu', '李师悦、尚让于瑕丘败黄巢', 2, '中和四年六月甲辰', '瑕丘', '李师悦与尚让追黄巢至瑕丘并击败之；黄巢逃至狼虎谷。', [('李师悦','追击者'),('尚让','追击者'),('黄巢','败走者')])
event('huang_death', '林言斩黄巢及其家人首，随后被沙陀博野军所杀', 2, '中和四年六月丙午', '狼虎谷一带', '《通鉴》记黄巢外甥林言斩黄巢兄弟及妻子之首，拟献时溥；途中沙陀博野军夺首，杀林言并献时溥。', [('黄巢','被斩首者'),('林言','斩首及被杀者'),('时溥','受献者')], note='依本段记载；“巢兄弟妻子首”照原文语义整理，黄巢死亡过程不据其他书擅补。')
event('zhu_jin_relief', '朱瑾救朱全忠，于合乡败秦宗权', 3, '中和四年六月条；具体月日未载', '合乡', '秦宗权攻宣武节度使朱全忠。朱全忠向朱瑄求援；朱瑄派朱瑾率军赴援，于合乡击败秦宗权。', [('秦宗权','进攻者'),('朱温','以朱全忠名义求援者'),('朱瑄','遣援军者'),('朱瑾','领兵救援者')])
relation('朱瑄','朱瑾','从父弟',3,'《通鉴》称朱瑾为朱瑄从父弟。')
relation('朱温','朱瑄','约为兄弟',3,'合乡救援后，朱全忠与朱瑄约为兄弟；这是结盟称兄弟，不是血缘兄弟。')
event('huang_heads_presented', '时溥献黄巢等首，俘虏姬妾遭处决', 4, '中和四年七月壬午', '大玄楼及市', '时溥遣使献黄巢及家人首级和姬妾。皇帝在大玄楼受献并讯问；一名未记姓名的姬妾反诘后，众姬妾皆被处决。', [('时溥','遣使献俘者')], note='原文未记答问女子姓名，不据此创造具名人物。')
event('yinshui_battle', '朱全忠于溵水战秦宗权', 5, '中和四年七月条；具体日未载', '溵水', '《通鉴》电子底本记朱全忠击秦宗权，并称在溵水取胜；“败示权”中的“示”疑为转录讹字，胜败对象依上下文待校。', [('朱温','进攻方'),('秦宗权','被进攻方')], note='底本文字“败示权于溵水”有疑字；未默改原文，也未据疑字扩写战况。')
event('li_petitions', '李克用上表控诉朱全忠，朝廷劝解', 6, '中和四年七月后条；八表先后时间未载', '晋阳、行在', '李克用回晋阳后整备甲兵，遣李承嗣上表，指控朱全忠谋害自己并求朝廷削其官爵。朝廷遣使劝和，李克用先后上表八次，仍未获准讨伐。', [('李克用','上表指控者'),('李承嗣','奉表者'),('朱温','被指控者'),('杨复恭','奉命劝谕者')], note='朱全忠谋害等细节为李克用奏表说法；与卷255围驿叙事可对读，不能把奏表每一指控直接作已证事实。')
event('li_august_requests', '李克用八月奏请麟州、昭义及云蔚归属', 7, '中和四年八月', '麟州、昭义、云蔚', '李克用请麟州隶河东、弟李克修任昭义节度使，均获准；又奏罢云蔚防御使，使其依旧隶河东，亦获准。朝廷进李克用爵陇西郡王。', [('李克用','上奏者及受封者'),('李克修','获任昭义节度使者')])
relation('李克用','李克修','兄弟',7,'《通鉴》称李克修为李克用之弟。')
event('zhu_chancellor', '朱全忠加同平章事', 8, '中和四年九月己未', None, '朱全忠加同平章事。', [('朱温','以朱全忠名义获加官者')])
event('wang_hui_changan', '王徽知京兆尹，修治长安宫室', 9, '中和四年九月后、十月前条；具体日未载', '长安', '王徽知京兆尹事，招抚流散人口、修缮宫室，使百司事务渐有头绪。', [('王徽','知京兆尹及修治者')])
event('return_petitions', '关东藩镇上表请僖宗返京', 9, '中和四年十月', '关东、长安', '关东藩镇上表请求皇帝返回长安。')
event('wang_duo_transfer', '王铎请还朝，徙义昌节度使', 10, '卷256中和四年追叙；确年待考', '义昌', '《通鉴》追叙：朱全忠初镇大梁时对王铎礼敬，后兵势渐强；王铎认为不足倚靠，上表请还朝，朝廷徙其为义昌节度使。', [('王铎','上表及改任者'),('朱温','以朱全忠名义被王铎倚为援者')], year=None, note='本段以“硃全忠之降也”起追述，不能据所在年条将整段经过定为884年。')
event('five_generals_defect', '王建等五将离鹿晏弘奔行在', 11, '中和四年十一月', '兴元、行在', '王建、韩建、张造、晋晖、李师泰率众数千离开鹿晏弘，奔赴行在。田令孜收五人为假子，任诸卫将军，编为随驾五都。', [('王建','出走及被收为假子者'),('韩建','出走及被收为假子者'),('张造','出走及被收为假子者'),('晋晖','出走及被收为假子者'),('李师泰','出走及被收为假子者'),('鹿晏弘','被离弃者'),('田令孜','收五人为假子者')])
for child in ['王建','韩建','张造','晋晖','李师泰']:
    relation('田令孜',child,'假父',11,f'《通鉴》卷256记田令孜在十一月收{child}为假子。')
event('lu_leaves_xingyuan', '鹿晏弘弃兴元东走', 11, '中和四年十一月，五将奔行在之后', '兴元', '田令孜遣禁兵讨鹿晏弘；鹿晏弘率众弃兴元逃走。', [('田令孜','遣禁兵者'),('鹿晏弘','弃城者')])
event('cao_old_resistance', '曹知悫在黄巢陷长安后据嵯峨山抗敌', 12, '黄巢陷长安后；具体年待考', '嵯峨山、长安', '曹知悫聚集壮士据嵯峨山南自保，并数次夜入长安袭黄巢军营。', [('曹知悫','率众抵抗者'),('黄巢','其部遭袭者')], year=None, note='本段以“初”追叙，不能定为884年。')
event('cao_executed', '王行瑜奉田令孜密令袭杀曹知悫', 12, '车驾将还长安之时；确日未载', '嵯峨山', '田令孜厌恶曹知悫，密令王行瑜诛杀；王行瑜出兵袭击，曹知悫一营尽死。', [('田令孜','密令者'),('王行瑜','出兵者'),('曹知悫','被杀者')])
event('lu_xiangzhou', '鹿晏弘与秦宗权部攻陷襄州', 13, '中和四年十一月后条；确日未载', '襄州', '鹿晏弘出兵襄州；秦宗权遣秦诰、赵德諲会合，攻陷襄州。山南东道节度使刘臣容奔成都。', [('鹿晏弘','攻城者'),('秦宗权','遣将者'),('秦诰','领兵攻城者'),('赵德諲','领兵攻城者'),('刘臣容','弃城奔成都者')])
event('lu_xuzhou', '鹿晏弘据许州并获任忠武节度使', 13, '襄州陷后；具体日未载', '许州', '鹿晏弘转掠各州后进入许州；周岌弃镇，鹿晏弘自称留后。朝廷无力讨伐，任其为忠武节度使。', [('鹿晏弘','据许州及受任者'),('周岌','弃镇者')])
event('chen_resigns', '陈敬瑄辞三川军事职', 14, '中和四年十二月己丑', '三川', '陈敬瑄上表辞三川都指挥、招讨、制置、安抚等使，朝廷准许。', [('陈敬瑄','辞职者')])
event('chen_yan_old', '陈岩兴九龙军并击退李连', 15, '黄巢转掠福建时及其后；确年待考', '福建、福州', '《通鉴》追叙陈岩聚乡众号九龙军，郑镒奏其为团练副使；李连后来攻福州，陈岩击败之。', [('陈岩','聚众及击退李连者'),('郑镒','举荐者'),('李连','攻福州者')], year=None, note='本段以“初”引出旧事，未确年；不得将陈岩起兵、李连进攻都定为884年。')
event('chen_yan_fujian', '陈岩任福建观察使', 15, '中和四年十二月壬寅', '福建', '郑镒上表请陈岩接任，朝廷以陈岩为福建观察使。', [('陈岩','受任者'),('郑镒','荐代者')])
event('wang_duo_killed', '乐从训伏杀王铎，乐彦祯称其为盗所杀', 16, '中和四年十二月条；具体日未载', '高鸡泊', '乐从训伏兵杀过魏州的王铎及宾僚从者，并掠其资装；乐彦祯向朝廷上报称王铎为盗所杀。', [('乐从训','伏杀者'),('王铎','被杀者'),('乐彦祯','向朝廷报告者')], note='“盗所杀”为乐彦祯奏报说法；不能用它替代本段关于乐从训伏杀的叙述。')
relation('乐彦祯','乐从训','父子',16,'《通鉴》称乐从训为乐彦祯之子。')
event('binning_jingnan', '邠宁军获赐号静难', 17, '中和四年十二月条；具体日未载', '邠宁', '朝廷赐邠宁军号“静难”。')
event('chen_sheng_muzhou', '陈晟逐柳超并获任睦州刺史', 18, '中和四年是岁；具体月日未载', '睦州', '馀杭镇使陈晟逐睦州刺史柳超，自领州事；朝廷任陈晟为刺史。', [('陈晟','驱逐柳超及受任者'),('柳超','被驱逐者')])
event('wang_jingrao_yingzhou', '王敬荛逐颍州刺史并获任命', 18, '中和四年是岁；具体月日未载', '颍州', '颍州都知兵马使王敬荛逐原刺史、自领州事；朝廷任其为刺史。原刺史姓名未载。', [('王敬荛','驱逐原刺史及受任者')])
event('feng_kills_sun', '冯行袭设伏斩孙喜并任均州刺史', 19, '中和四年是岁条；具体月日未载', '均州', '孙喜欲攻均州，冯行袭设计令其单独渡江，伏兵起后斩孙喜；山南东道节度使上奏其功，朝廷任冯行袭为均州刺史。', [('冯行袭','设伏及受任者'),('孙喜','被斩者'),('吕烨','时任均州刺史')])
event('feng_opens_road', '冯行袭讨山贼，蜀道复通', 19, '冯行袭任均州刺史后；具体月日未载', '长山、蜀道', '冯行袭讨伐占据长山、侵夺贡赋的群盗，使通往蜀地的道路恢复通行。', [('冯行袭','讨伐者')])
event('li_changfu_fengxiang', '李昌言病故后李昌符承袭凤翔节度使', 20, '中和四年是岁条；具体月日未载', '凤翔', '李昌言病时上表请弟李昌符知留后；李昌言死后，朝廷任李昌符为凤翔节度使。', [('李昌言','上表及病故者'),('李昌符','受任者')])
relation('李昌言','李昌符','兄弟',20,'《通鉴》称李昌符为李昌言之弟。')
event('qin_expansion_summary', '《通鉴》总述秦宗权部侵扰诸道', 21, '黄巢平后秦宗权势炽；各次侵攻确年待考', '淮南、江南、襄唐邓、东都孟陕虢、汝郑、汴宋等', '《通鉴》在年末总述秦宗权命陈彦、秦贤、秦诰、孙儒、张晊、卢瑭等分路侵掠诸道，并记其所至焚杀严重；各地陷落不能仅据总述一律定于884年。', [('秦宗权','遣将者'),('陈彦','侵淮南者'),('秦贤','侵江南者'),('秦诰','攻襄唐邓者'),('孙儒','攻东都孟陕虢者'),('张晊','攻汝郑者'),('卢瑭','攻汴宋者')], year=None, note='年末为地域和时间跨度不明的总述；用空年份保留时序不确定性。')

for n in Q:
    assert used.get(n), f'Unprocessed paragraph {n}'
    paras[n-1]['status'] = 'reviewed'
    paras[n-1]['event_keys'] = used[n]
    paras[n-1]['batch_key'] = B['batch_key']
for n, review in {5:'底本“败示权”疑讹；照录原文，事件说明明确待校。',6:'李克用奏表中的谋害指控与史家叙事分层。',10:'以朱全忠投降起追叙，王铎改任确年待考。',12:'“初”段旧事确年待考；后续曹知悫遇害不强定具体日。',15:'“初”段旧事不定884年；壬寅任命可定位。',16:'乐彦祯奏称盗杀是其单方陈述。',21:'年末总述覆盖多地，不能把各次攻陷一概定在884年。'}.items():
    paras[n-1]['review'] = review
payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for p in paras:
    p['status'] = status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR/'paragraphs.json').write_text(json.dumps(paras, ensure_ascii=False, indent=2) + '\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=256, year=884, primary_source_key=source, paragraphs=[Q[n]['id'] for n in Q], next_paragraph='zztj-v256-y0885-p001', coverage='卷256中和四年条全部21段；与卷255两批合计覆盖884年。', supplements=[], status=status), ensure_ascii=False, indent=2) + '\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
