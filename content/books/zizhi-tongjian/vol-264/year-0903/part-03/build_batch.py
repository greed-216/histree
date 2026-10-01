"""Curate Tongjian 264, year 903, consecutive paragraphs 17–24."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(p['id'][-3:]): p for p in ledger}
assert list(Q) == list(range(1, 55))
primary_prev = 'tongjian-264-903-spring'
primary = 'tongjian-264-903-may'
old_five = 'jiuwudaishi-024-li-ting'
new_five = 'xinwudaishi-054-li-ting'
old_zhu = 'jiuwudaishi-019-zhu-yougong'

B = {'format_version': 1, 'batch_key': 'zztj-v264-y0903-p017-p024',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
source_specs = [
    (primary_prev, P.parent / 'part-02/sources/library' / primary_prev, '71feb52', '司马光等'),
    (primary, P / 'sources/library' / primary, '3ae36b2', '司马光等'),
    (old_five, P / 'sources/library' / old_five, '3ae36b2', '薛居正等'),
    (new_five, P / 'sources/library' / new_five, '3ae36b2', '欧阳修等'),
    (old_zhu, P / 'sources/library' / old_zhu, '3ae36b2', '薛居正等'),
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
primary_texts = {sk: (source_dirs[sk] / 'source.txt').read_text() for sk in (primary_prev, primary)}
for n in range(17, 25):
    assert Q[n]['text'] == (ROOT / 'resources/derived/tongjian/264.txt').read_text().splitlines()[Q[n]['source_line']-1], n

registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
aliases = {'硃全忠':'朱温','全忠':'朱温','硃友宁':'朱友宁','硃友伦':'朱友伦','硃友裕':'朱友裕','茂贞':'李茂贞','祚':'李祚','可范':'第五可范','李存审':'符存审'}
people, used, reused, supplements = {}, {}, set(), []

def primary_for(n, quote):
    return next(sk for sk, data in primary_texts.items() if quote in data and json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_start'] <= Q[n]['source_line'] <= json.loads((source_dirs[sk] / 'paragraph.json').read_text())['locator']['line_end'])

def claim(table, key, field, value, n, quote, note):
    assert quote in Q[n]['text'], (n, quote)
    B['claims'].append(dict(key=f'claim_zztj_264_0903_03_{len(B["claims"])+1:04d}',
                            subject_table=table, subject_key=key, field_path=field, claim_text=value,
                            source_key=primary_for(n, quote),
                            citation=f'卷264·天复三年（903）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行',
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
                   death_year=None, description=f'《资治通鉴》卷264天复三年条所见人物：{canonical}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[canonical] = row['key']
    claim('person', row['key'], 'description', f'本段记{canonical}：{role}。', n, quote or Q[n]['text'],
          '只据本段确认参与身份；同名与异体字回查后复用。')
    return row['key']

def event(code, title, n, quote, actors=(), when=None, place=None, note=None, year=903):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_264_0903_' + code
    desc = title + '。'
    B['events'].append(dict(key=key, title=title, start_year=year, end_year=year,
                            time_original=when or '903年本段条；确日未载', dynasty='唐', description=desc,
                            phases=[], location_name=place, location_modern_name=None, location_lat=None,
                            location_lng=None, location_precision='unknown',
                            location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。', status='draft'))
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', desc, n, quote, note or '按原文动作分录，不外推结果。')
    claim('event', key, 'time_original', when or '903年本段条；确日未载', n, quote,
          note or ('段内追叙，确年待考。' if year is None else '沿主书段落次序；干支日未换算公历日。'))
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_264_0903_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本段措辞，不因同场出现推定额外关系。')
    return key

def extra(sk, table, key, field, text, quote, n, relation, note):
    assert quote in (source_dirs[sk] / 'source.txt').read_text(), (sk, quote)
    record = json.loads((source_dirs[sk] / 'paragraph.json').read_text())
    ck = f'claim_zztj_264_0903_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=text, source_key=sk, citation=record['citation'],
                            note='原文：' + quote + '；核对说明：' + note, status='draft'))
    supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                            subject_key=key, relation=relation))

# 17. Relief order, Cheng Rui's decision, and Li Ting's rejected advice.
event('du_hong_asks_relief','杜洪求援，朱全忠遣韩勍屯滠口并召诸镇救鄂',17,
      '杜洪求救于硃全忠，全忠遣其将韩勍将万人屯滠口，遣使语荆南节度使成汭、武安节度使马殷、武贞节度使雷彦威，令出兵救洪。',
      [('杜洪','求援者'),('朱温','派兵并致书者'),('韩勍','率军屯滠口者'),('成汭','受召援者'),('马殷','受召援者'),('雷彦威','受召援者')],
      when='903年四月至五月间；确日未载',place='滠口、鄂州',
      note='“万人”为本段韩勍部所记，命诸镇援鄂不等于各镇同向执行。')
event('cheng_rui_sails_east','成汭率舟师沿江东下援鄂',17,
      '汭畏全忠之强，且欲侵江、淮之地以自广，发舟师十万，沿江东下。',
      [('成汭','率舟师东下者')],
      when='903年四月至五月间；确日未载',place='长江',
      note='“畏”“欲侵”是主书解释的动机；十万是主书记数，不作实数核定。')
event('cheng_rui_large_ships','成汭先前历三年建造巨舰',17,
      '汭作巨舰，三年而成，制度如府署，谓之“和州载”',
      [('成汭','造舰者')],when='援鄂以前历三年；起止年未定',year=None,place='荆南',
      note='三年为建造时长，不从903年倒推精确始年。')
event('li_ting_warns_cheng','李珽劝成汭屯巴陵避决战，成汭不听',17,
      '不若遣骁将屯巴陵，大军与之对岸，坚壁勿战，不过一月，吴兵食尽自遁，鄂围解矣。”汭不听。',
      [('李珽','献策者'),('成汭','未采纳者')],
      when='903年成汭援鄂出兵前；确日未载',place='荆南',
      note='“吴兵食尽自遁”是李珽的预期，不作为实际战果；舰船三年建成是前事，未倒填900年。')

# 18. Wang Jian's Qin-Long campaign and diplomatic exchange are separate.
event('wang_jian_qin_long','王建乘李茂贞势弱出兵攻秦陇',18,
      '王建出兵攻秦、陇，乘李茂贞之弱也',
      [('王建','出兵者'),('李茂贞','被攻地区控制者')],
      when='903年四月至五月间；确日未载',place='秦、陇',
      note='“乘李茂贞之弱”为主书动机叙述；本段未载攻取秦陇。')
event('wang_jian_diplomacy','王建遣韦庄入贡并结好朱全忠，朱遣王殷回聘',18,
      '遣判官韦庄入贡，亦修好于硃全忠。全忠遣押牙王殷报聘',
      [('王建','遣韦庄者'),('韦庄','入贡使者'),('朱温','遣王殷报聘者'),('王殷','报聘使者')],
      when='903年四月至五月间；确日未载',place='蜀',
      note='王殷复用前段人物；报聘与谈论骑兵分别记。')
event('wang_jian_horse_review','王建在星宿山阅马示王殷',18,
      '乃集诸州马，大阅于星宿山，官马八千，私马四千，部队甚整。殷叹服。',
      [('王建','阅马者'),('王殷','观阅者')],
      when='903年四月至五月间；确日未载',place='星宿山',
      note='官马八千、私马四千为本段记数；王建过去十年买马是回溯，不另定起始年。')
event('wang_jian_horse_trade','王建得蜀后长期在文黎维茂州购胡马',18,
      '建本骑将，故得蜀之后，于文、黎、维、茂州市胡马，十年之间，遂及兹数。',
      [('王建','购马者')],when='得蜀后十年间；起止年未定',year=None,
      place='文州、黎州、维州、茂州',
      note='“十年之间”只是时间跨度，不据此倒填精确起年。')

# 19. Yunzhou and Zhenwu actions; “先是” has no fixed year.
event('wang_jinghui_defects','王敬晖杀刘再立并叛降刘仁恭',19,
      '五月，丁未，李克用云州都将王敬晖杀刺史刘再立，叛降刘仁恭。',
      [('王敬晖','杀刺史并叛降者'),('刘再立','被杀者'),('刘仁恭','受降者')],
      when='903年五月丁未',place='云州',
      note='李克用是原上级，未记其参与杀刺史。')
event('li_sizhao_counterattack','李克用遣李嗣昭李存审讨王敬晖，援军至后王弃城',19,
      '克用遣李嗣昭、李存审将兵讨之。仁恭遣将以兵五万救敬晖，嗣昭退保乐安，敬晖举众弃城而去。',
      [('李克用','遣讨者'),('李嗣昭','讨伐并退守者'),('李存审','共同受遣者'),('刘仁恭','遣援者'),('王敬晖','弃城者')],
      when='903年五月丁未后；确日未载',place='云州、乐安',
      note='五万为本段所记援军数；退保乐安与王敬晖弃城分清，未记王被擒。')
event('qibi_rang_zhengwu_prior','契苾让先前逐石善友据振武',19,
      '先是，振武将契苾让逐戍将石善友，据城叛。',
      [('契苾让','逐将据城者'),('石善友','被逐戍将')],
      when='“先是”追叙；确年未载',year=None,place='振武',
      note='“先是”前事不可直接定为903年。')
event('li_sizhao_recovers_zhengwu','李嗣昭等攻振武，契苾让自焚后复取城',19,
      '嗣昭等进攻之，让自燔死。复取振武城，杀吐谷浑叛者二千馀人。',
      [('李嗣昭','攻城者'),('契苾让','自焚者'),('李存审','前文同受遣将领')],
      when='903年五月；确日未载',place='振武',
      note='李存审参与根据“嗣昭等”与本段前文推接，待异书校；二千余人为史书记数。')
event('li_keyong_punishes_generals','李克用因失王敬晖杖李嗣昭李存审并削官',19,
      '克用怒嗣昭、存审失王敬晖，皆杖之，削其官。',
      [('李克用','处分者'),('李嗣昭','被处分者'),('李存审','被处分者')],
      when='903年五月；确日未载',
      note='处分原因是李克用认定其失王敬晖，未据此断定擒获本可实现。')

# 20. Jingjiang raid and battle of Junshan are not the same action.
event('xu_ouyang_jiangling','许德勋与欧阳思趁成汭东下袭陷江陵',20,
      '马殷遣大将许德勋将舟师万馀人，雷彦威遣其将欧阳思将舟师三千馀人会于荆江口，乘虚袭江陵，庚戌，陷之，尽掠其人及货财而去。',
      [('马殷','遣许德勋者'),('许德勋','袭江陵者'),('雷彦威','遣欧阳思者'),('欧阳思','袭江陵者')],
      when='903年五月庚戌',place='荆江口、江陵',
      note='万人、三千余人为主书记数；江陵失陷与君山交战分别记。')
event('cheng_rui_army_demoralized','江陵失陷后成汭军将士失家而斗志衰落',20,
      '将士亡其家，皆无斗志。',
      [('成汭','所率军队主帅')],when='903年五月庚戌后；确日未载',
      note='主书将失家与无斗志相连，属军队状态概述，不推定每名士卒家庭遭遇。')
event('li_shenfu_scouts_cheng','李神福亲察成汭战舰，主张急击',20,
      '李神福闻其将至，自乘轻舟前觇之，谓诸将曰：“彼战舰虽多而不相属，易制也，当急击之！”',
      [('李神福','侦察并主张急击者'),('成汭','被侦察者')],
      when='903年五月壬子前；确日未载',place='鄂州附近',
      note='舰船易制是李神福判断，未写成已经取胜。')
event('junshan_battle','秦裴杨戎奉李神福命于君山败成汭，成汭赴水死',20,
      '壬子，神福遣其将秦裴、杨戎将众数千逆击汭于君山，大破之，因风纵火，焚其舰，士卒皆溃，汭赴水死，获其战舰二百艘。',
      [('李神福','遣将者'),('秦裴','领军作战者'),('杨戎','领军作战者'),('成汭','战败赴水死者')],
      when='903年五月壬子',place='君山',
      note='舰二百艘与兵数千均为主书记数；把焚舰、溃败、成汭之死归于本战。')
event('han_qing_withdraws','韩勍闻成汭败亡后引军退',20,
      '韩勍闻之，亦引兵去。',[('韩勍','撤军者')],
      when='903年五月壬子后；确日未载',place='鄂州附近',
      note='闻之承前君山之战；不推断韩勍亲临战场。')

# 21. Yuezhou settlement and the chronicle's undated character summary.
event('xu_deng_yuezhou','许德勋还经岳州，邓进忠携族迁长沙',21,
      '许德勋还过岳州，刺史邓进忠开门具牛酒犒军，德勋谕以祸福，进忠遂举族迁于长沙。',
      [('许德勋','受犒并劝说者'),('邓进忠','携族迁长沙者')],
      when='903年五月江陵袭击后；确日未载',place='岳州、长沙',
      note='“谕以祸福”为劝说，原文没有说邓进忠被俘。')
event('ma_appoints_xu_deng','马殷任许德勋岳州刺史、邓进忠衡州刺史',21,
      '马殷以德勋为岳州刺史，以进忠为衡州刺史。',
      [('马殷','任命者'),('许德勋','岳州刺史'),('邓进忠','衡州刺史')],
      when='903年五月；确日未载',place='岳州、衡州')
event('lei_raids_neighbors','雷彦威经常泛舟焚掠荆鄂邻境',21,
      '雷彦威狡狯残忍，有父风，常泛舟焚掠邻境，荆、鄂之间，殆至无人。',
      [('雷彦威','屡次劫掠者')],when='泛指长期行为；起止年未载',year=None,place='荆、鄂之间',
      note='“狡狯残忍”“殆至无人”为主书评价与概述，非903年单次事件。')

# 22-24. Offices and a possible source transcription error.
event('li_maozhen_renounces_shangshu','李茂贞请辞尚书令，朝廷复授中书令',22,
      '李茂贞畏硃全忠，自以官为尚书令，在全忠上，累表乞解去。诏复以茂贞为中书令。',
      [('李茂贞','请辞及受新官者'),('李杰','诏命代表者')],
      when='903年五月；确日未载',
      note='“畏朱全忠”为主书动机叙述；累表与最终诏令分清。')
event('cui_recruit_guards','崔胤请募六军侍卫六千六百，朝廷从之并令郑元规召募',23,
      '请每军募步兵四将，每将二百五十人，骑兵一将百人，合六千六百人，选其壮健者，分番侍卫，”从之。令六军诸卫副使、京兆尹郑元规立格召募于市。',
      [('崔胤','奏请者'),('李杰','采纳者'),('郑元规','立格召募者')],
      when='903年五月；确日未载',place='长安',
      note='六千六百是奏请总额，原文未记实际募足；郑元规承担召募。')
event('zhu_recommends_yougong','朱全忠表荐颍州刺史朱友恭为武宁军使职',24,
      '硃全忠表颍州刺史硃友恭为武宁李度使。',
      [('朱温','上表推荐者'),('朱友恭','被表荐者')],
      when='903年五月；确日未载',place='武宁',
      note='底本文字作“李度使”，疑“节度使”讹；旧五代史卷19作天复中武宁军留后，官名异文并列待核。')

extra(old_five,'event','event_zztj_264_0903_li_ting_warns_cheng','description',
      '《旧五代史》卷24亦载李珽劝成汭屯巴陵、避以巨舰决战，成汭不听。',
      '珽入言曰：「今舳艫容介士千人，載稻倍之，緩急不可動。',17,'corroborates',
      '同段后续载成汭败死，后果归第20段；兵数为史书记数。')
extra(new_five,'event','event_zztj_264_0903_li_ting_warns_cheng','description',
      '《新五代史》卷54亦记李珽劝成汭屯巴陵，成汭未采纳。',
      '珽為汭謀曰：「今一舟容甲士千人',17,'corroborates',
      '新旧五代史可互见叙事，不视为彼此独立的统计确证。')
extra(old_five,'event','event_zztj_264_0903_junshan_battle','description',
      '《旧五代史》卷24记淮军乘风纵火，成汭舟焚而溺死。',
      '淮人果乘風縱火，舟盡焚，兵盡溺，汭亦自沈於江',20,'corroborates',
      '旧五代史作“自沈”，通鉴作“赴水死”，保留措辞差异。')
extra(new_five,'event','event_zztj_264_0903_junshan_battle','description',
      '《新五代史》卷54记成汭败而溺死。',
      '汭不聽，果敗，溺死',20,'corroborates',
      '同段与旧五代史均为李珽传材料，不能当作两份完全独立的确证。')
extra(old_zhu,'event','event_zztj_264_0903_zhu_recommends_yougong','description',
      '《旧五代史》朱友恭传记其天复中任武宁军留后。',
      '天復中，為武寧軍留後',24,'adds',
      '旧五代史官名为留后，通鉴电子底本“李度使”疑损；并列待纸本核。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(17,25):
    ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
        review='卷264天复三年第17—24段连续处理；追叙、动机、进言与未实现建议均保留归属，疑字及异文并列。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=264,year=903,
    primary_source_key=primary_prev,primary_source_keys=[primary_prev,primary],
    paragraphs=[Q[n]['id'] for n in range(17,25)],next_paragraph=Q[25]['id'],
    coverage='卷264天复三年共54个非空段落中的第17—24段连续处理；同年后续仍待录入。',
    supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
