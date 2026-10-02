# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 14–18."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 77))
specs = [
 ('tongjian-272-923-yangliu',P/'sources/library/tongjian-272-923-yangliu','c5e5bad1','司马光等'),
 ('jiuwudaishi-029-923-new-fort',P/'sources/library/jiuwudaishi-029-923-new-fort','c5e5bad1','薛居正等'),
 ('jiuwudaishi-029-923-july',P/'sources/library/jiuwudaishi-029-923-july','c5e5bad1','薛居正等'),
 ('xinwudaishi-032-923-slander',P/'sources/library/xinwudaishi-032-923-slander','c5e5bad1','欧阳修'),
 ('jiuwudaishi-029-923-desheng',YEAR/'part-03/sources/library/jiuwudaishi-029-desheng','c8d197bd','薛居正等'),
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p014-p018',
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
lines = (ROOT / 'resources/derived/tongjian/272.txt').read_text().splitlines()
for n in range(14, 19):
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
people, used, reused, supplements = {}, {}, {'jiuwudaishi-029-923-desheng','xinwudaishi-005-923-founding'}, []

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
        citation = f'卷272·同光元年（923）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_272_0923_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'曹氏（李存勖母）','太妃':'刘氏（李克用妻）',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦','曹氏':'曹氏（李存勖母）','刘氏':'刘氏（李克用妻）','武皇':'李克用','考晋王':'李克用','上':'李存勖','帝':'李存勖','执宜':'执宜（李存勖曾祖）','国昌':'李国昌','继岌':'李继岌','硃守殷':'朱守殷','硃安殷':'朱守殷','守殷':'朱守殷','王铁枪':'王彦章','彦章':'王彦章','翔':'敬翔','顺密':'卢顺密','嗣源':'李嗣源','遂严':'刘遂严','颙':'燕颙','梁末帝':'朱友贞','崇韬':'郭崇韬','延孝':'康延孝','延光':'范延光','宗侃':'王宗侃','赵':'赵岩','张':'张汉杰'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷272同光元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='923年本段；确日未载', note='', year=923, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_272_0923_' + code
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
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_272_0923_' + code + '_' + pk
        existing = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['person_events'] if (x['person_key'],x['event_key'])==(pk,key)] if stable_key else []
        if existing:
            assert len({x['key'] for x in existing})==1
            er=dict(existing[0],status='draft');edge=er['key'];reused.add(edge)
        else:er=dict(key=edge,person_key=pk,event_key=key,role=role,status='draft')
        B['person_events'].append(er)
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
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
        row=dict(key=f'relationship_zztj_272_0923_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)

# Paragraph 14: evacuation, siege, messages and relief.
E=event('jiao_li_defend_yangliu','李存勖遣焦彦宾赴杨刘，与李周固守',14,'帝遣宦者焦彦宾急趣杨刘，与镇使李周固守，',[('帝','遣使守城者'),('焦彦宾','奉命赴杨刘的宦者'),('李周','杨刘镇使、守将')],when='923年五月德胜南城破后',place='杨刘',note='李周与已有王周不是同名换姓，不合并；趣为趋，原字保留。')
claim('event',E,'description','《旧五代史》称中书焦彦宾驰杨刘，后记与守将李周固守。',14,'帝令中書焦彥賓馳至楊劉，固守其城；','旧史官称中书、主书宦者并列，不视作不同人。',source='jiuwudaishi-029-923-desheng',relation='corroborates')
event('abandon_desheng_north','朱守殷奉命弃德胜北城，撤屋为筏载械助杨刘',14,'命守殷弃德胜北城，撤屋为筏，载兵械浮河东下，助杨刘守备，',[('帝','命弃北城者'),('守殷','撤城运输兵械者')],when='923年五月南城失后',place='德胜北城、杨刘',note='是北城弃守，不能误说王彦章同时攻拔两城；助守与南城救不及不同措施。')
event('desheng_stores_transported','德胜刍粮薪炭徙澶州，耗失近半',14,'徙其刍粮薪炭于澶州，所耗失殆半。',[],when='923年五月撤北城时',place='德胜、澶州',note='近半为史载运输损失，未明烧毁或偷盗因由，不添加责任归属。')
claim('event',used[14][-1],'description','《旧五代史》亦记仓卒迁粮，耗失殆半。',14,'事既倉卒，耗失殆半。','对应库存而非上一段战场斩首数，数目范围分开。',source='jiuwudaishi-029-923-desheng',relation='corroborates')
event('river_raft_running_battle','唐梁各行河岸，舟筏中流交战，至杨刘损失甚重',14,'王彦章亦撤南城屋材浮河而下，各行一岸，每遇湾曲，辄于中流交斗，飞矢雨集，或全舟覆没，一日百战，互有胜负。比及杨刘，殆亡士卒之半。',[('王彦章','梁军下河者'),('朱守殷','唐军撤北城下河者')],when='923年五月撤德胜至杨刘途中',place='德胜至杨刘河道',note='朱守殷承上句撤屋载械；殆亡士卒之半原书范围不明确，不分摊两军精确死者数；一日百战是史载概数。')
claim('event',used[14][-1],'description','《旧五代史》同记两岸行进、中流交斗、终日百战，至杨刘殆亡其半。',14,'一彼一此，終日百戰，比及楊劉，殆亡其半。','死亡口径不据其字强指某军全部兵力。',source='jiuwudaishi-029-923-desheng',relation='corroborates')
E=event('liang_assault_yangliu','王彦章、段凝攻杨刘，以九艘巨舰截援',14,'己巳，王彦章、段凝以十万之众攻杨刘，百道俱进，昼夜不息，连巨舰九艘，横亘河津以绝援兵。',[('王彦章','梁攻城主将'),('段凝','梁攻城副将')],when='923年五月己巳',place='杨刘、河津',note='己巳在六月乙亥前承五月；十万、九艘按主书，非独立军力统计，绝援意图不等完全无援。')
claim('event',E,'description','《旧五代史》亦记己巳二将大军攻杨刘南城，昼夜百道攻。',14,'己巳，王彥章、段凝率大軍攻楊劉南城，焦彥賓與守城將李周極力固守。','旧史未给十万九舰，不伪称两个来源均证数目。',source='jiuwudaishi-029-923-desheng',relation='corroborates')
event('li_zhou_resists_siege','李周与士卒同甘苦，拒梁攻城，梁军退屯城南',14,'城垂陷者数四，赖李周悉力拒之，与士卒同甘苦，彦章不能克，退屯城南，为连营以守之。',[('李周','悉力守城者'),('彦章','未克退屯城南者')],when='923年五月己巳攻城后',place='杨刘南城、城南',note='垂陷并非已经四次陷落；此刻退屯连营，围攻尚未结束。')
E=event('cunxu_arrives_yangliu','李存勖引兵救杨刘，六月乙亥抵达',14,'帝引兵救之，曰：“李周在内，何忧！”日行六十里，不废畋猎，六月，乙亥，至杨刘。',[('帝','引兵救杨刘者')],when='923年六月乙亥；主书纪时',place='杨刘',note='城使请日百里与实际日六十里分开；不废畋猎史述保留，不自行判断是否造成军事损失。')
claim('event',E,'time_original','《旧五代史》记六月己亥至杨刘。',14,'六月己亥，帝親禦軍至楊劉，','主书乙亥与旧史己亥干支不同，待纸本及历日校核，不能当繁简转换自动改字。',source='jiuwudaishi-029-923-new-fort',relation='conflicts')
E=event('chongtao_proposes_river_fort','郭崇韬建议博州东岸筑垒固河津，分梁兵势',14,'臣请筑垒于博州东岸以固河津，既得以应接东平，又可以分贼兵势。',[('郭崇韬','献筑垒策者')],when='923年六月李存勖抵杨刘后',place='博州东岸',note='对曰承问郭，内容为作战方案；旬日城成是假设，实际六日另录。')
claim('event',E,'description','郭崇韬又请以敢死士每日挑战，牵制王彦章使筑垒得成。',14,'愿陛下募敢死之士，日令挑战以缀之，苟彦章旬日不东，则城成矣。','愿、苟是献策条件，未当确已募成固定队伍。')
claim('event',E,'description','《旧五代史》同记郭崇韬请下流据河筑垒救郓，并日令勇士挑战。',14,'崇韜請於下流據河築壘，以救鄆州。又請帝日令勇士挑戰，旬日之內，寇若不至，營壘必成。','主书博州东岸与旧史下流各保留，不强换现代地理。',source='jiuwudaishi-029-923-new-fort',relation='corroborates')
event('yunzhou_isolated_communications','李嗣源守郓州，与河北声问不通',14,'时李嗣源守郓州，河北声问不通，人心渐离，不保朝夕。',[('李嗣源','被孤隔的郓州守将')],when='923年六月筑新城前',place='郓州、河北',note='不保朝夕是形势评述，不作将死日期；后有奏报始通。')
event('kang_requests_surrender_secretly','康延孝密向李嗣源请降',14,'会梁右先锋指挥使康延孝密请降于嗣源，',[('康延孝','密请降的梁右先锋指挥使'),('嗣源','受密降请求者')],when='923年六月本段；确日未载',place='梁军、郓州',note='密请降不同八月本人百骑来奔，保留两个阶段，不提前八月任博州刺史。')
event('kang_earlier_flight_to_liang','主书追叙康延孝有罪，亡奔梁',14,'延孝者，太原胡人，有罪，亡奔梁，时隶段凝麾下。',[('延孝','曾亡奔梁的太原人')],when='密请降前追叙；确年未载',year=None,place='太原、梁',note='罪名未载不虚构；胡人为史书称谓，不强配现代民族；隶段凝是当时军职而非永久私人关系。')
E=event('fan_delivers_wax_letter','范延光奉李嗣源遣送康延孝蜡书，建议筑马家口垒',14,'嗣源遣押牙临漳范延光送延孝蜡书诣帝，延光因言于帝曰：',[('嗣源','遣押牙者'),('范延光','送蜡书并献策者'),('延孝','蜡书作者'),('帝','收书受策者')],when='923年六月密降之后',place='郓州、杨刘',note='范延光临漳籍据原句，不把密信假定公开外交使节；密信送达与康本人来奔分开。')
claim('event',E,'description','范延光称杨刘控扼已固，建议马家口筑垒通郓路。',14,'请筑垒马家口以通郓州之路。','范氏建议并行郭崇韬筑博州东岸之策；不把两个献策者合并。')
E=event('chongtao_builds_new_fort','李存勖遣郭崇韬率万人至马家口渡河，六日筑新城',14,'帝从之，遣崇韬将万人夜发，倍道趣博州，至马家口渡河，筑城昼夜不息。',[('帝','遣筑城者'),('崇韬','率军筑新城者')],when='923年六月乙亥后、戊子攻城前',place='博州、马家口、东岸新城',note='万人为主书数，六日承后句；马家口/麻家口异写待地理校核，不落点。')
claim('event',E,'description','主书记郭崇韬筑新城六日。',14,'崇韬筑新城凡六日，','实际六日不同此前献策旬日假设。')
claim('event',E,'description','《旧五代史》补毛璋同筑，人数作数千。',14,'即令崇韜與毛璋率數千人中夜往博州濟河東，晝夜督役，居六日，營壘將成。','人物增补；主书万人与旧史数千并列，未据六日一致消除兵数差异。',source='jiuwudaishi-029-923-new-fort',relation='conflicts')
pk=person('毛璋',14,'与郭崇韬同筑新垒者','即令崇韜與毛璋率數千人中夜往博州濟河東，',source='jiuwudaishi-029-923-new-fort')
ek='participation_zztj_272_0923_build_fort_mao_zhang';B['person_events'].append(dict(key=ek,person_key=pk,event_key=E,role='与郭崇韬同筑新垒者',status='draft'))
claim('person_event',ek,'role','毛璋与郭崇韬同筑新垒。',14,'即令崇韜與毛璋率數千人中夜往博州濟河東，','仅旧史补名，保留来源，不伪作主书具名。',source='jiuwudaishi-029-923-new-fort')
E=event('liang_attacks_new_fort','王彦章攻博州新城，以巨舰截援',14,'戊子，急攻新城，连巨舰十馀艘于中流以绝援路。',[('王彦章','攻新城主将')],when='923年六月戊子',place='博州新城、河津',note='十余舰是此次新城截援，不混前杨刘九舰。')
claim('event',E,'description','《旧五代史》补杜晏球与王彦章同攻，数万人。',14,'戊子，梁將王彥章、杜晏球領徒數萬，晨壓帝之新壘。','补另一主将杜晏球，不由同战推亲属或长期盟友。',source='jiuwudaishi-029-923-new-fort',relation='adds')
pk=person('杜晏球',14,'同攻新垒的梁将','戊子，梁將王彥章、杜晏球領徒數萬，晨壓帝之新壘。',source='jiuwudaishi-029-923-new-fort')
ek='participation_zztj_272_0923_attack_fort_du_yanqiu';B['person_events'].append(dict(key=ek,person_key=pk,event_key=E,role='同攻新垒的梁将',status='draft'))
claim('person_event',ek,'role','杜晏球与王彦章同攻新垒。',14,'戊子，梁將王彥章、杜晏球領徒數萬，晨壓帝之新壘。','旧史明确具名，旧将名复用。',source='jiuwudaishi-029-923-new-fort')
event('chongtao_holds_new_fort','郭崇韬先士卒拒新城之攻，遣间使求援',14,'崇韬慰劳士卒，以身先之，四面拒战，遣间使告急于帝。',[('崇韬','新城拒守、求援者')],when='923年六月戊子攻城时',place='博州新城',note='城犹卑沙土疏为主书描述，不造现存城址参数；间使未具名不建人。')
E=event('cunxu_relief_new_fort','李存勖自杨刘赴新城救援，王彦章退邹家口',14,'帝自杨刘引大军救之，陈于新城西岸，城中望之增气，大呼叱梁军，梁人断绁敛舰；帝舣舟将渡，彦章解围，退保邹家口。',[('帝','自杨刘引救者'),('彦章','解围退邹家口者')],when='923年六月戊子新城告急后',place='杨刘、新城西岸、邹家口',note='舣舟将渡是准备渡，未明确全部大军已登东岸；梁退该城但未全面退回梁国。')
claim('event',E,'description','《旧五代史》同记自杨刘列军西岸、舣舟将渡、梁退邹家口。',14,'帝自楊劉引軍陣於西岸，城中望之，大呼，帝艤舟將渡，梁軍遂解圍，退保鄒家口。','同次解除新城围，不与七月杨刘总围解混同。',source='jiuwudaishi-029-923-new-fort',relation='corroborates')
claim('event',E,'description','《新五代史》六月简记与王彦章战新垒、败之。',14,'六月，及王彥章戰于新壘，敗之。','本纪简记，与主书退邹家口事互证，但未给戊子日。',source='xinwudaishi-005-923-founding',relation='corroborates')
event('yunzhou_reports_restored','新城解围后，郓州奏报开始畅通',14,'郓州奏报始通。',[],when='923年六月新城解围后',place='郓州、河北',note='是通信恢复，不代表所有道路及地区完全控制。')
event('siyuan_requests_shouyin_punishment','李嗣源密表请治朱守殷覆军罪，李存勖不从',14,'李嗣源密表请正硃守殷覆军之罪，帝不从。',[('李嗣源','密表请求者'),('硃守殷','请治对象'),('帝','未采纳者')],when='923年六月新城解围后',place='后唐',note='覆军罪是请罪指控，不写已定罪处罚；不从为结果。')
# Paragraph 15, July movements.
E=event('cunxu_south_along_river','李存勖沿河南进，梁军弃邹家口再趋杨刘',15,'秋，七月，丁未，帝引兵循河而南，彦章等弃邹家口，复趣杨刘。',[('帝','循河南进者'),('彦章','弃邹家口转杨刘者')],when='923年七月丁未',place='邹家口、杨刘')
claim('event',E,'description','《旧五代史》同记丁未沿河南进、梁弃邹家口。',15,'秋七月丁未，帝御軍沿河而南，梁軍棄鄒家口夜遁，','同日动作互证；夜字为旧史补，不加到主书全部部队。',source='jiuwudaishi-029-923-july',relation='corroborates')
event('li_shaoxing_qingqiu_victory','李绍兴在清丘驿南败梁游兵',15,'甲寅，游弈将李绍兴败梁游兵于清丘驿南。',[('李绍兴','败梁游兵的游弈将')],when='923年七月甲寅',place='清丘驿南',note='对手未具名不虚建；李绍兴不可仅按姓绍字误合李绍荣。')
event('duan_reproaches_yanzhang','段凝以为唐兵自上流已渡，责王彦章深入',15,'段凝以为唐兵已自上流渡，惊骇失色，面数彦章，尤其深入。',[('段凝','以为已渡、责将者'),('彦章','受责者')],when='923年七月清丘战后本段',place='梁军',note='以为是判断，不能据此确定唐兵此日真实渡点；不建立长期仇敌关系。')
# Paragraph 16, a distinct region.
event('wang_zongkan_dies','前蜀侍中魏王王宗侃去世',16,'乙卯，蜀侍中魏王宗侃卒。',[('宗侃','去世的蜀侍中魏王')],when='923年七月乙卯',place='前蜀',note='宗侃沿用已有王宗侃及田师侃别名；不混前批诸王宗侃宗寿宗弼。')
claim('person',people['王宗侃'],'death_year','王宗侃于923年七月乙卯去世。',16,'乙卯，蜀侍中魏王宗侃卒。','主书记死亡年明确；复用主体的生卒字段补充以引用呈现，发布器不覆盖旧行。')
# Paragraph 17, the final relief of Yangliu.
event('yuan_captures_scouts','李存勖遣李绍荣直抵梁营，擒梁斥候',17,'戊午，帝遣骑将李绍荣直抵梁营，擒其斥候，梁人益恐，',[('帝','遣骑将者'),('李绍荣','袭营擒斥候的元行钦')],when='923年七月戊午',place='梁军营',note='李绍荣复用元行钦；旧史同日作李紹貽，暂保留异文待核，不将贻当荣繁体或给人物补正式别名。')
claim('event',used[17][-1],'description','《旧五代史》同日骑将名字作李绍贻。',17,'戊午，遣騎將李紹貽直抵梁軍壘，梁益恐。','同日同动作用以并列异文；仅主书李绍荣可确认元行钦，旧史贻尚不强行认正式异名。',source='jiuwudaishi-029-923-july',relation='conflicts')
event('tang_fire_rafts_burn_fleet','唐军以火筏焚梁连舰',17,'又以火筏焚其连舰。',[],when='923年七月戊午本段',place='梁连舰、河道',note='原书未具名火筏实际指挥者，不默认李绍荣本人纵火。')
E=event('liang_lifts_yangliu_siege','王彦章等解杨刘围退杨村，唐军追击复屯德胜',17,'王彦章等闻帝引兵已至邹家口，己未，解杨刘围，走保杨村；唐兵追击之，复屯德胜。',[('王彦章','解围退杨村者'),('帝','引兵至邹家口的李存勖')],when='923年七月己未',place='杨刘、杨村、德胜、邹家口',note='听闻帝至是梁军所闻，主书以此叙述；没有灭梁或全线停止战争。')
claim('event',E,'description','《旧五代史》同记己未夜梁军退杨村、帝军屯德胜，但近因写闻李嗣源自郓引大军将至。',17,'又聞李嗣源自鄆州引大軍將至，己未夜，梁軍拔營而遁，復保於楊村。帝軍屯於德勝。','主书闻帝至邹家口、旧史闻嗣源援至，来军及叙述近因各存，不把两者硬写单一原因。',source='jiuwudaishi-029-923-july',relation='conflicts')
event('yangliu_siege_losses_summary','主书总述梁攻诸城损失重，杨刘已断粮三日',17,'杨刘比至围解，城中无食已三日矣。',[],when='923年七月杨刘围解时及前后总述',place='杨刘、梁攻诸城',note='断粮三日为城中；前句死者且万人是梁前后急攻诸城总述，不只该日某一战。')
claim('event',used[17][-1],'description','主书称梁军前后攻城伤亡近万人，弃资粮铠仗锅幕以千计。',17,'梁兵前后急攻诸城，士卒遭矢石、溺水、曷死者且万人，委弃资粮、铠仗、锅幕，动以千计。','私用区字加曷有电子字形疑点，原字保留；展示不擅释为某种死因，数量及口径仅据史载。')
# Paragraph 18, military reporting and political pressure.
E=event('yanzhang_threatens_court_favourites','主书记王彦章曾称成功后诛奸臣，赵张闻之欲倾其势',18,'王彦章疾赵、张乱政，及为招讨使，谓所亲曰：“待我成功还，当尽诛奸臣以谢天下！”赵、张闻之，私相谓曰：“我辈宁死于沙陀，不可为彦章所杀。”相与协力倾之。',[('王彦章','放言诛奸臣者')],when='923年任招讨时及其后追叙；确日未载',place='梁军、梁廷',note='疾与私议为作者叙事；此为宣言和对抗，不是已诛赵张；泛赵张涵群体，独立姓名由新史补证，不将所有张氏归一。')
claim('event',E,'description','《新五代史》明确段凝与赵岩、张汉杰交往，王彦章放言诛奸臣，赵岩等协力倾之。',18,'是時，段凝已有異志，與趙巖、張漢傑交通，彥章素剛，憤梁日削，而嫉巖等所為，嘗謂人曰：「俟吾破賊還，誅姦臣以謝天下。」巖等聞之懼，與凝叶力傾之。','巖规范展示岩，沿用已有赵岩；叶力原字保留。新史异志为评价不作独立叛变事实。',source='xinwudaishi-032-923-slander',relation='adds')
for name,role in [('赵岩','新史记与段凝交往的当权者'),('张汉杰','新史记与段凝交往的当权者')]:
 quote='是時，段凝已有異志，與趙巖、張漢傑交通，';pk=person(name,18,role,quote,source='xinwudaishi-032-923-slander');ek='participation_zztj_272_0923_favourites_'+pk
 B['person_events'].append(dict(key=ek,person_key=pk,event_key=E,role=role,status='draft'));claim('person_event',ek,'role',name+'：'+role+'。',18,quote,'名字由新史补，主书赵张不直接当唯一姓名。',source='xinwudaishi-032-923-slander')
E=event('duan_reports_against_yanzhang','主书记段凝与王彦章相违，伺过失上闻，捷奏归功段凝',18,'段凝素疾彦章之能而谄附赵、张，在军中与彦章动相违戾，百方沮挠之，惟恐其有功，潜伺彦章过失以闻于梁主。每捷奏至，赵、张悉归功于凝，由是彦章功竟无成。',[('段凝','被记阻挠与报过失者'),('彦章','被记受阻者')],when='923年任招讨后军中追叙；确日未载',place='梁军、梁廷',note='嫉谄等评价带史述归属，未设心理诊断；不将作者因果概括转成穷尽梁亡原因。')
claim('event',E,'description','《新五代史》补破南城后各上捷书，段凝请求匿王书、上己书，末帝独劳段凝。',18,'其破南城也，彥章與凝各為捷書以聞，凝遣人告巖等匿彥章書而上己書，末帝初疑其事，已而使者至軍，獨賜勞凝而不及彥章，軍士皆失色。','是同军功争议补详，匿书具体日未载，不硬套七月己未；使者无名。',source='xinwudaishi-032-923-slander',relation='adds')
event('yanzhang_recalled_to_zezhou','朱友贞召王彦章回大梁，命其会董璋攻泽州',18,'及归杨村，梁主信谗，犹恐彦章旦夕成功难制，征还大梁。使将兵会董璋攻泽州。',[('梁主','召还并遣攻者'),('彦章','召回并会军者'),('董璋','受命会攻的梁将')],when='923年七月退杨村后、八月泽州陷前',place='大梁、泽州',note='命会攻不是已攻陷，陷城后事续录；信谗恐难制为史述评因不写可独证内心。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(14,19):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='连续校核杨刘围攻、博州新垒与七月退围；六月乙亥/己亥并列、人数不拼；密降与八月奔分阶段、李绍贻异文不强定身份、私用字保留、赵张评议带来源。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(14,19)],next_paragraph=Q[19]['id'],supplements=supplements,coverage='卷272正文第14—18段，原文件19—23行，含杨刘围攻长段及七月各地记事。',reviewed_questions=[
 {'paragraph_id':Q[14]['id'],'note':'北城弃不同南城陷；粮损与舟战伤亡口径分开；主书六月乙亥、旧史己亥并列；筑城主书万人旧史数千，毛璋与杜晏球旧史补名；康密请降不同本人来奔，亡梁初事年null；攻新垒不混围解。'},
 {'paragraph_id':Q[15]['id'],'note':'七月丁未、甲寅按主书记；李绍兴不混李绍荣；段凝以为是其判断，不自动作唐已渡证据。'},
 {'paragraph_id':Q[16]['id'],'note':'王宗侃复用既有田师侃主体；蜀魏王与后唐魏王不同，七月乙卯卒独立记。'},
 {'paragraph_id':Q[17]['id'],'note':'李绍荣复用元行钦；旧史李绍贻异文不强加正式别名；己未退围原因帝邹家口/嗣源援军分别存；私用字死因不改释，近万人是前后总述非单日。'},
 {'paragraph_id':Q[18]['id'],'note':'赵张群体与新史赵岩张汉杰分层，史书心理及因果归属带作者；匿捷书新史补；宣言诛奸不当已杀；召王会董攻泽未提前陷城。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
