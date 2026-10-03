# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 33–40."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 53))
specs=[
 ('tongjian-276-late-summer',YEAR/'part-05/sources/library/tongjian-276-late-summer','86b40c48','司马光等'),
 ('jiuwudaishi-088-zhangxichong',P/'sources/library/jiuwudaishi-088-zhangxichong','72e54c9a','薛居正等'),
 ('xinwudaishi-047-zhangxichong',P/'sources/library/xinwudaishi-047-zhangxichong','72e54c9a','欧阳修'),
 ('jiuwudaishi-039-september',P/'sources/library/jiuwudaishi-039-september','72e54c9a','薛居正等'),
 ('jiuwudaishi-039-october',P/'sources/library/jiuwudaishi-039-october','72e54c9a','薛居正等'),
 ('jiuwudaishi-039-november',P/'sources/library/jiuwudaishi-039-november','72e54c9a','薛居正等'),
 ('jiuwudaishi-074-doutingwan',P/'sources/library/jiuwudaishi-074-doutingwan','72e54c9a','薛居正等'),
 ('xinwudaishi-061-baitian',P/'sources/library/xinwudaishi-061-baitian','72e54c9a','欧阳修'),
 ('jiuwudaishi-039-intercalary',YEAR/'part-06/sources/library/jiuwudaishi-039-intercalary','f88fd498','薛居正等'),
 ('xinwudaishi-006-928',YEAR/'part-01/sources/library/xinwudaishi-006-928','c991ab36','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-late-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p033-p040',
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
lines = (ROOT / 'resources/derived/tongjian/276.txt').read_text().splitlines()
for n in range(33, 41):
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
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷276·天成三年（928）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0928_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','希崇':'张希崇','吴王太后':'王氏（吴太妃）','季兴':'高季昌','高季兴':'高季昌','廷琬':'窦廷琬','从敏':'李从敏'}
NEW_ALIASES={'张希崇':['張希崇'],'张行简':['張行簡'],'李廷规':['李廷規'],'陶玘':[],'石知讷':['石知訥'],'聂屿':['聶嶼'],'窦廷琬':['竇廷琬'],'李从敏':['李從敏']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成三年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='928年'+('闰八月' if n<=34 else '九月' if n<=38 else '十月')+'本段；确日未载'
    key = 'event_zztj_276_0928_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', title+'。', n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_276_0928_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{next(x["name"] for x in B["people"] if x["key"]==pk)}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。',source=source)
    return key

def relationship(a,b,kind,n,quote,note,source=None):
    pa=person(a,n,f'{b}之{kind}',quote,source=source); pb=person(b,n,f'与{a}关系对象',quote,source=source)
    a=next(x['name'] for x in B['people'] if x['key']==pa); b=next(x['name'] for x in B['people'] if x['key']==pb)
    matches={}
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_276_0928_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
zold='jiuwudaishi-088-zhangxichong';znew='xinwudaishi-047-zhangxichong';sep='jiuwudaishi-039-september';octo='jiuwudaishi-039-october';nov='jiuwudaishi-039-november';dou='jiuwudaishi-074-doutingwan';wu='xinwudaishi-061-baitian';inter='jiuwudaishi-039-intercalary';ann='xinwudaishi-006-928'
E=ev('zhangxichong_replaces_luwenjin_pingzhou','卢文进来降后，契丹以张希崇接任，守平州，遣三百骑监视',33,'初','三百骑监之。',[('希崇','藩汉都提举使、接任卢龙节度守平州者'),('卢文进','其离去后职位获接替者')],year=None,when='初追叙卢文进南归后，张接任、派监确日未载',place='平州',note='卢来降为已录前事背景不重建；主卢龙节度、补新平州节度及旧平州任称并列，不改原字或现代地理。')
claim('event',E,'description','新张传称张希崇接卢文进为平州节度使，契丹派亲将三百骑监视。',33,'明宗時，盧文進自平州亡歸，契丹因以希崇代文進為平州節度使，遣其親將以三百騎監之。','主卢龙节度守平州与新平州节度职称叙法并列，卢文进旧归降不重造；三百是监骑数不是所部总人口。',source=znew)
claim('person',people['张希崇'],'description','张希崇字德峰，幽州蓟县人，少通左氏春秋且好吟咏。',33,'張希崇，字德峰，幽州薊縣人也。父行簡，假薊州玉田令。希崇少通《左氏春秋》，復癖於吟詠。','补字、史载籍贯与学识，不配现代出生坐标，不按后来卒龄倒生年。',source=zold)
relationship('张行简','希崇','父亲',33,'張希崇，字德峰，幽州薊縣人也。父行簡，假薊州玉田令。','张传明父行简，父子方向张行简→张希崇；假玉田令为史载职称不补任年月。',source=zold)
E=ev('zhangxichong_scholarly_background_trust','张希崇本书生、幽州牙将，陷于契丹，性和易而渐获契丹将亲信',33,'希崇本','契丹将稍亲信之，',[('希崇','旧牙将、被俘书生及渐获信任者')],year=None,when='南归前生平与受信追叙，确年日未载',place='幽州、契丹所管平州',note='稍亲信是渐变背景，不当官将结义；没于契丹不是死亡。')
E=ev('zhangxichong_consults_southward_return','张希崇与部曲谋南归，部曲愿归但忧敌众我寡',33,'因与','虏众我寡，奈何？”',[('希崇','召议南归者')],year=None,when='南归行动前谋议，确年日未载',place='平州',note='部曲无名不造角色名；担忧人数非确定己方兵少具体比率，谋归非已走。')
claim('event',E,'description','新张传称麾下怕不能全军脱身，劝张希崇独自离去。',33,'其麾下皆言兵多，不可俱亡，懼不得脫，因勸希崇獨去。','独去为部下建议，后来举众南归不同，不把建议当已独逃结果。',source=znew)
E=ev('zhangxichong_plans_kill_supervisor_escape','张希崇提出杀监将令其军溃散，并以距契丹王帐千余里争取时间',33,'希崇曰','众曰：“善！”',[('希崇','提出逃归计策者')],year=None,when='谋归会议中，确年日未载',place='平州至契丹王帐距离原述',note='兵必溃与会征去远是张的预期，未先当战果；千余里史载概数不转地图精确公路距离。')
E=ev('zhangxichong_prepares_lime_pit','张希崇部先掘坑，填石灰',33,'乃先','实以石灰，',[('希崇','计策部署者')],year=None,when='杀监将前一日，确年日未载',place='平州',note='准备与次日酒宴分别录，不编坑深、化学机理或具体参与者姓名。')
E=ev('zhangxichong_kills_drunken_supervisor_followers','次日张希崇召契丹将饮酒，醉后杀将及从者，投入坑中',33,'明日','投诸阱中。',[('希崇','召饮与杀监将计策执行者')],year=None,when='填灰坑次日，确年日未载',place='平州',note='明日为相对掘坑日；主杀后投与旧悉投灰阱中毙叙法分别保留，不虚构监将姓名或杀伤人数。')
claim('event',E,'description','旧张传称首领与群从来牙帐，饮醉后悉投灰坑中毙。',33,'明旦，首領與群從至，希崇飲以醇酎數鐘，既醉，悉投於灰阱中斃焉。','主杀后投、旧投灰阱中毙的动作次序不同保留，不据此推现代确定死因。',source=zold,relation='conflicts')
E=ev('zhangxichong_attacks_north_camp','张希崇部迅速攻城北契丹营，契丹军溃去',33,'其营','契丹众皆溃去。',[('希崇','派兵攻营者')],year=None,when='监将被杀后，确年日未载',place='平州城北营',note='溃去为散逃，非全部歼灭；城北营并非整个契丹国都。')
E=ev('zhangxichong_returns_with_twenty_thousand_people','张希崇率所部二万余人口南归后唐',33,'希崇悉','二万馀口来奔，',[('希崇','率人口南归者')],when='928年闰八月条的归顺记载，实际起行日未载',place='平州至后唐',note='二万余口为所部人口，不是二万士兵；初段前部追叙无确年，南归据旧本年闰月上表归顺及十月入见定位，未强所有步骤同日。')
claim('event',E,'description','旧明宗纪闰月记契丹所署平州刺史张希崇上表归顺。',33,'契丹平州刺史張希崇上表歸順。','独立年月定位归顺表，实际起行日期未独具，不把上表与全程南归当同一天。',source=inter,relation='corroborates')
claim('event',E,'description','旧张传同记管内生口二万余南归。',33,'希崇遂以管內生口二萬餘南歸。','旧生口二万余原称保留，不能把口等战兵；新另条引文记二万，不强精确差数。',source=zold,relation='corroborates')
claim('event',E,'description','新张传记率麾下得生口二万南归。',33,'希崇率其麾下，得生口二萬南歸。','主旧二万余、新二万概数叙法保留，未精算运输、男女老少比例。',source=znew,relation='corroborates')
E=event('zhangxichong_yuande_audience_rewards','旧明宗纪记张希崇等八十余人入见元德殿，获差等赏赐',33,'戊午，契丹平州刺史張希崇已下八十餘人見於元德殿，頒賜有差。',[('希崇','入朝获赏者')],source=octo,when='928年十月戊午',place='元德殿',note='八十余是入见随员而非二万口归众总数；按不同动作另录，不猜赏品数量。')
E=ev('zhangxichong_ruzhou_cishi','朝廷授张希崇汝州刺史',33,'诏以',None,[('希崇','汝州刺史获任者')],when='928年南归后；主未独记授官月日，旧纪记十一月壬午',place='汝州',note='归顺所在闰月不等授官也在闰月；旧帝纪十一月补具体任职时点，旧新列传称汝州防御使职衔并列，不造三个人。')
claim('event',E,'time_original','旧明宗纪十一月壬午项记张希崇为汝州刺史，加检校太傅。',33,'是日，以契丹所署平州刺史、光祿大夫、檢校太保張希崇為汝州刺史，加檢校太傅。','是日承壬午，高死报告在前原文不拆改；本条仅补张任日期和检校，不提前处理高死主线段。',source=nov)
claim('event',E,'description','旧张传称南归后唐明宗授汝州防御使，新张传同称。',33,'唐明宗嘉之，授汝州防禦使。','主刺史、列传防御使不同层级职称并列，未强本日全部同时授职，不掩帝纪月份定位。',source=zold)
claim('event',E,'description','新张传称明宗嘉其南归，拜汝州防御使。',33,'明宗嘉之，拜汝州防禦使。','补职称并列，不提前后迁灵武及屯田业绩。',source=znew,relation='corroborates')
E=ev('wu_wang_empress_dowager_dies','吴皇太后去世',34,'吴王',None,[('吴王太后','吴已尊皇太后、去世者')],place='吴',note='沿927已尊太妃王氏主体，不混李嗣源王德妃、后梁王太后等；主吴王太后原语保留，未具日龄死因不补。')
E=ev('jingnan_defeats_chu_baitian','荆南在白田击败楚军',35,'九月','败楚兵于白田，',[],when='928年九月辛巳',place='白田',note='主不具直接统兵将，新名季兴为胜军归属补证；不凭此原语推其本人在前线亲战。')
claim('event',E,'description','新吴世家乾贞二年九月记高季兴在白田败楚军，获将吏三十四人献吴。',35,'九月，季興敗楚師於白田，獲其將吏三十四人來獻。','二年承前段乾贞改元，已存前段上下文定位；三十四是新记获将吏，非全部楚军死伤或战兵总俘数。',source=wu)
E=ev('litinggui_captured_sent_wu','楚岳州刺史李廷规被荆南擒获，送至吴',35,'执楚',None,[('李廷规','被擒并送吴的楚岳州刺史')],when='928年九月辛巳白田战后',place='白田至吴',note='归于吴承被获李，不等其自愿归附或已任吴官；新将吏三十四未直接名李，不能据此强三十四全员名单。')
E=ev('edict_wentao_death_tomb_plundering','朝廷以温韬发陵为由，令所在赐死温韬',36,'乙未',None,[('温韬','所在被命赐死者')],when='928年九月乙未敕令',place='温韬所在；旧记德州',note='敕令与实际执行日分开，不凭令字确定当天已死；发诸陵是所列既往理由，未造928新盗陵事件。')
E=ev('edict_duanning_death_repeated_shifts','朝廷以段凝反复为由，令所在赐死段凝',36,'乙未',None,[('段凝','所在被命赐死者')],when='928年九月乙未敕令',place='段凝所在；旧记辽州',note='反覆为敕列理由与政治评价，非具体本年新反叛案；令赐死不等原文明示执行日。')
q='乙未，詔德州流人溫韜、遼州流人段凝、嵐州司戶陶玘、憲州司戶石知訥、原州司馬聶嶼，並宜賜死於本處，暴其宿惡而誅之也。'
for ek in ['edict_wentao_death_tomb_plundering','edict_duanning_death_repeated_shifts']:
 claim('event','event_zztj_276_0928_'+ek,'description','旧明宗纪同日诏温韬在德州、段凝在辽州及陶玘、石知讷、聂屿同被命所在赐死。',36,q,'补流放所在与同诏对象，不扩作本日五人均已执行的明证。',source=sep,relation='corroborates')
E=event('edict_tao_shi_nie_death_supplement','旧明宗纪补陶玘、石知讷、聂屿同诏在所在赐死',36,q,[('陶玘','岚州司户、被诏赐死者'),('石知讷','宪州司户、被诏赐死者'),('聂屿','原州司马、被诏赐死者')],source=sep,when='928年九月乙未敕令',place='岚州、宪州、原州',note='同诏新增对象据旧记，不把主二人扩大为主书明载五人，命令不独立证明当日执行。')
E=ev('fangzhiwen_jingnan_commander','武宁节度使房知温兼荆南行营招讨使，知荆南行府事',37,'己亥','知荆南行府事；',[('房知温','荆南行营招讨及行府事务获任者')],when='928年九月己亥',place='荆南行营',note='沿房知温李绍英同人，不造同名新主体；授行府职不等攻取江陵或灭荆南。')
claim('event',E,'description','旧明宗纪同日称徐州节度使房知温兼荆南行营招讨使，知行府事。',37,'己亥，詔徐州節度使房知溫兼荊南行營招討使，知荊南行府事。','徐州是武宁治州，名称叙法相合，兼军职非新任徐州本身。',source=sep,relation='corroborates')
E=ev('court_sends_eunuchs_mobilize_xiangyang','朝廷分遣中使发诸道兵赴襄阳，讨高季兴',37,'分遣',None,[('季兴','被诸道军诏讨对象')],when='928年九月己亥任讨使后，确日未独载',place='诸道至襄阳',note='发兵赴襄阳是动员集军，不等诸军已到江陵；中使无名不猜演员名单，未补军数。')
E=ev('doutingwan_transfer_qingzhou_jinzhou','窦廷琬由庆州防御使被调为金州刺史',38,'辛丑','为金州刺史；',[('廷琬','奉调金州者')],when='928年九月辛丑',place='庆州至金州',note='任命调动不等本人已赴金州，后文仍据庆州拒命；窦竇繁简匹配，未与其他窦廷者合并。')
claim('event',E,'description','旧窦传称课利未足，朝廷诏移任金州，随后据庆州反叛。',38,'課利不集，詔移任於金州。廷琬據慶州叛，','课利未集为旧补调任背景，未猜欠额和盐利承包数，刑峻史评未直接当现代法院已确认罪。',source=dou)
E=ev('doutingwan_refuses_transfer_qingzhou','窦廷琬据庆州拒绝调任命令',38,'冬，十月',None,[('廷琬','据庆州拒命者')],when='928年十月',place='庆州',note='拒命才是实际行为，与九月授金职分开，不提前十二月攻破族诛。')
claim('event',E,'time_original','新明宗纪将庆州防御使窦廷琬反列在八月后、冬十月讨之之前。',38,'慶州防禦使竇廷琬反。冬十月，靜難軍節度使李敬周討之。','新简纪段序与主九月调、十月拒不同密度，未强定新反为八月某日；原纪时分别保留。',source=ann,relation='conflicts')
E=ev('licongmin_northern_deputy_campaign','横海节度使李从敏兼北面行营副招讨使',39,'丙午','兼北面行营副招讨使。',[('从敏','北面行营副招讨获任者')],when='928年十月丙午',place='北面行营',note='李新主体原从敏不与李从珂、从荣合并；主副与旧纪招讨称法并列，军衔不猜具体已战。')
claim('person',people['李从敏'],'description','李从敏为李嗣源的从子。',39,'从敏，帝之从子也。','从子保留原亲属称谓，未明父名及伯叔长幼，不造李嗣源亲父或确定叔父边。')
claim('event',E,'description','旧明宗纪十月丙午称沧州节度使李从敏兼北面招讨使。',39,'丙午，以滄州節度使李從敏兼北面招討使。','沧州与横海同军治州，招讨/副招讨职称差异保留，未覆盖主副或再造同时升一级事件。',source=octo,relation='conflicts')
E=ev('lijingzhou_ordered_campaign_doutingwan','朝廷命静难节度使李敬周发兵讨窦廷琬',40,'戊申',None,[('李敬周','奉诏发兵讨者'),('廷琬','诏讨对象')],when='928年十月戊申',place='静难至庆州',note='发兵诏令与后十二月收城不同，不提前攻破或屠族；静难与邠州同军治州。')
claim('event',E,'description','旧明宗纪同日诏邠州节度使李敬周攻庆州，因窦廷琬拒命。',40,'詔邠州節度使李敬周攻慶州，以刺史竇廷琬拒命故也。','本句承戊申前项同日，史字保留；攻令未具完成，不引用后平之夷族作为当日结果。',source=octo,relation='corroborates')
review='卷276连续928年第33—40段。张希崇新主体：卢文进离去后接职监骑、书生被俘渐信、谋归部曲担忧、杀将拖时间计划、填坑、次日召饮杀将投坑、攻北营分别，初追叙年月null。主卢龙守平州与新平州节度并列；没于为被俘非死。三百为监骑非所部，二万余口非二万兵。旧闰月上表、十月戊午八十余入见、十一月壬午授汝刺分定位，不强全在闰八月或八十余为全归众；旧新列传防御使补衔不造同名。旧投坑中毙与主杀后投并列不猜现代死因。字德峰蓟籍学春秋好诗与父张行简假玉田令补，父边明确；不提前后屯田、任职、卒。吴太后沿927尊太妃王氏主体，不混明宗王德妃；本句无病龄日不补。九月辛巳白田胜、执楚岳李廷规送吴分；新乾贞二年承前即位乾贞上下文，获将吏三十四不等全军战死，不推高本人前线及李自愿降。乙未温发陵段反覆为赐死诏理由非本年新盗陵反叛；敕令非当日实际执行。旧补德州辽州流所，同诏陶玘岚司户石知讷宪司户聂屿原司马独补，不说主载五人同日已死。己亥房武宁徐州兼荆南行府、使发军襄阳分，军动员非江陵克。辛丑窦金州调命与冬十月仍据庆拒分，旧课利不足背景不精算未纳，新反段序保留不定八月精日；不提前十二月族诛。十月丙午李从敏主副讨旧招讨称法并列，从子不补父及伯叔长幼；戊申李敬周静难邠州命讨非已攻城平族。展示简体，原字定位不改，纸本异文待核。'
ctx=ROOT/'content/books/zizhi-tongjian/vol-276/year-0927/part-04/sources/library/xinwudaishi-061-wu-accession'
cr=json.loads((ctx/'paragraph.json').read_text());contexts=[dict(file=os.path.relpath(ctx/'source.txt',P/'sources'),sha256=hashlib.sha256((ctx/'source.txt').read_bytes()).hexdigest(),paragraph_id=cr['id'],citation=cr['citation'],url='https://github.com/greed-216/histree/blob/755ad621/'+str((ctx/'source.txt').relative_to(ROOT)),purpose='乾贞改元上下文，白田段二年承此；复用既有原文快照，不重复录入927帝位。')]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(33,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(33,41)],next_paragraph='zztj-v276-y0928-p041',next_volume=276,next_year=928,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续928年第33—40段、原文件65—72行；张希崇南归与授职、吴太后薨、白田楚军战、诏温段等死、荆南动员、窦拒调及李从敏李敬周军令。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(33,41)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
