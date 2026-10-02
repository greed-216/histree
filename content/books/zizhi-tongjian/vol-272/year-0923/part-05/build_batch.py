# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 19–24."""
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
 ('tongjian-272-923-august',P/'sources/library/tongjian-272-923-august','d77c4a74','司马光等'),
 ('jiuwudaishi-029-923-august',P/'sources/library/jiuwudaishi-029-923-august','d77c4a74','薛居正等'),
 ('jiuwudaishi-010-923-august',P/'sources/library/jiuwudaishi-010-923-august','d77c4a74','薛居正等'),
 ('xinwudaishi-028-lu-cheng-demotion',P/'sources/library/xinwudaishi-028-lu-cheng-demotion','d77c4a74','欧阳修'),
 ('xinwudaishi-072-dejun-shaobin',P/'sources/library/xinwudaishi-072-dejun-shaobin','d77c4a74','欧阳修'),
 ('xinwudaishi-005-923-founding',YEAR/'part-02/sources/library/xinwudaishi-005-923-founding','ca9db7c8','欧阳修'),
 ('xinwudaishi-032-923-slander',YEAR/'part-04/sources/library/xinwudaishi-032-923-slander','c5e5bad1','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p019-p024',
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
for n in range(19, 25):
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
people, used, reused, supplements = {}, {}, {'xinwudaishi-032-923-slander','xinwudaishi-005-923-founding'}, []

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
    ck = f'claim_zztj_272_0923_05_{len(B["claims"])+1:04d}'
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
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦','曹氏':'曹氏（李存勖母）','刘氏':'刘氏（李克用妻）','武皇':'李克用','考晋王':'李克用','上':'李存勖','帝':'李存勖','执宜':'执宜（李存勖曾祖）','国昌':'李国昌','继岌':'李继岌','硃守殷':'朱守殷','硃安殷':'朱守殷','守殷':'朱守殷','王铁枪':'王彦章','彦章':'王彦章','翔':'敬翔','顺密':'卢顺密','嗣源':'李嗣源','遂严':'刘遂严','颙':'燕颙','梁末帝':'朱友贞','崇韬':'郭崇韬','延孝':'康延孝','延光':'范延光','宗侃':'王宗侃','赵':'赵岩','张':'张汉杰','任团':'任团','圜':'任圜','团':'任团','绍斌':'赵德钧','李绍斌':'赵德钧','凝':'段凝','振':'李振','张宗奭':'张全义'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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

# Paragraph 19: July court dispute and August rescue of Zezhou.
E=event('cunxu_commends_li_zhou','李存勖到杨刘慰劳李周，称其善守保全大事',19,'甲子，帝至杨刘劳李周曰：“微卿善守，吾事败矣。”',[('帝','慰劳者'),('李周','获慰劳的守城将')],when='923年七月甲子',place='杨刘',note='甲子承七月，赞语为帝言；未以反事实赞语推出客观唯一功臣。')
event('lu_cheng_whips_prefecture_clerk','卢程以私事要求兴唐府，鞭不能应的府吏',19,'中书侍郎、同平章事卢程以私事干兴唐府，府吏不能应，鞭吏背。',[('卢程','鞭兴唐府吏者')],when='923年主书七月本段；确日未载',place='兴唐府',note='甲子只明确慰劳李周，不直接指定卢程冲突同日；府吏未名不虚建。')
claim('event',used[19][-1],'description','《新五代史》补私事为给假驴夫，府吏以无例拒，卢程笞吏。',19,'人有假驢夫於程者，程帖興唐府給之，府吏啟無例，程怒笞吏背。','驴夫具体请求来自新史独立补证，不改主书私事。',source='xinwudaishi-028-lu-cheng-demotion',relation='adds')
E=event('ren_tuan_complains_of_lu_cheng','任团向卢程申诉，被辱后诉于李存勖',19,'光禄卿兼兴唐少尹任团，圜之弟，帝之从姊婿也，诣程诉之。程骂曰：“公何等虫豸，欲倚妇力邪！”团诉于帝。',[('任团','诉府吏被鞭及受辱者'),('程','辱申诉者'),('帝','受任团申诉者')],when='923年七月主书本段；确日未载',place='兴唐府、后唐',note='通鉴主角任团，任圜之弟；新史作任圜，异说保留不合并兄弟。')
claim('event',E,'description','《新五代史》同一申诉记少尹任圜、庄宗姊婿，而主书作任团及从姊婿。',19,'少尹任圜，莊宗姊婿也，詣程訴其不可。','人物名和亲属称谓两重差异：不把任团设为任圜别名，不从姊婿自动改亲姊婿，待异本校核。',source='xinwudaishi-028-lu-cheng-demotion',relation='conflicts')
relationship('任圜','任团','兄长',19,'任团，圜之弟','通鉴明确弟字，任圜是任团兄长；另书同事写任圜本人，身份异说附事件，未合并。')
relationship('任团','李存勖','从姊夫',19,'帝之从姊婿也','原文从姊婿，任团是李存勖从姊之夫；不建立未名妻子、不写亲姐姐丈夫；新史姊婿异说单列。')
E=event('lu_cheng_saved_and_demoted','李存勖欲令卢程自尽，卢质力救，卢程贬右庶子',19,'帝怒曰：“朕误相此痴物，乃敢辱吾九卿！”欲赐自尽；卢质力救之，乃贬右庶子。',[('帝','欲赐自尽、后贬者'),('卢程','被贬右庶子者'),('卢质','力救者')],when='923年主书七月本段；新史本纪记六月罢',place='后唐',note='欲赐自尽被救，非此刻处死；帝痴物为言论非人物客观评价。')
claim('event',E,'description','《新五代史》传亦记卢质力解，罢右庶子。',19,'賴盧質力解之，乃罷為右庶子。','传记同结果；前句郭崇韬亦欲杀为该书补说，未推最终杀死。',source='xinwudaishi-028-lu-cheng-demotion',relation='corroborates')
claim('event',E,'time_original','《新五代史》本纪记六月卢程罢。',19,'是月，盧程罷。','前句六月及王彦章战新垒，承六月，与通鉴七月段叙次不同，不统一改日；传末入洛途中卒为后事暂不提前入本段。',source='xinwudaishi-005-923-founding',relation='conflicts')
event('pei_yue_appeals_for_help','裴约遣间使告急，李存勖命李绍斌救取裴约',19,'裴约遣间使告急于帝，',[('裴约','被围告急者'),('帝','收告急并遣救者')],when='923年八月壬申遣救前；告急确日未载',place='泽州、后唐',note='未名间使不虚建；李存勖吾兄是对李嗣昭称兄，不在此推亲生兄弟。')
E=event('shaobin_rescues_zezhou','李存勖遣李绍斌率甲士五千救泽州，援兵未至城陷',19,'八月，壬申，绍斌将甲士五千救之，未至，城已陷，约死。',[('绍斌','率甲士救泽州的赵德钧'),('裴约','被救未及的守将')],when='923年八月壬申遣救；城陷确日未载',place='泽州',note='壬申标援救，并非直接为城陷日；李绍斌与赵德钧由新史明确赐姓名合并同主体。')
claim('event',E,'description','《旧五代史》同记八月壬申朔遣李绍斌五千救泽州，未至城陷裴约害。',19,'八月壬申朔，帝遣李紹斌以甲士五千援澤州。','补朔日为旧史纪时；主书无朔，不换公历。',source='jiuwudaishi-029-923-august',relation='corroborates')
claim('person',people['赵德钧'],'aliases','赵德钧曾获李存勖赐姓名李绍斌。',19,'德鈞，幽州人也，事劉守光、守文為軍校，莊宗伐燕得之，賜姓名曰李紹斌。','新史明确同一人赐姓名；仅用于稳定身份和别名，不把后半937年前后事录作923年。',source='xinwudaishi-072-dejun-shaobin',relation='adds')
E=event('zezhou_falls_pei_yue_dies','泽州陷落，裴约死亡',19,'未至，城已陷，约死。',[('裴约','城陷死者')],when='923年八月救援未及之时；确日未载',place='泽州',note='不强把壬申当死亡日；守城阶段已从三月开始，不重新设造一场三月阵亡。')
claim('event',E,'description','《旧五代史》记董璋攻泽州而下。',19,'董璋攻澤州，下之。','梁本纪补攻陷主将；同批唐本纪未至城陷裴约被害，与主书死同事。',source='jiuwudaishi-010-923-august',relation='adds')
claim('event',E,'description','《新五代史》亦记八月梁克泽州、守将裴约死。',19,'秋八月，梁人克澤州，','主书与新史同月；接句守将裴约死之，未明确殉死方式，不推自刎或处刑。',source='xinwudaishi-005-923-founding',relation='corroborates')
claim('person',people['裴约'],'death_year','裴约于923年泽州陷落时死亡。',19,'未至，城已陷，约死。','死亡年明确，死法未在主书本段具体说明。')
event('cunxu_returns_xingtang_august','李存勖自杨刘还兴唐',19,'甲戌，帝自杨刘还兴唐。',[('帝','自杨刘还兴唐者')],when='923年八月甲戌',place='杨刘、兴唐府',note='原书唐本纪称归邺，为同地称谓，不另设回京两次。')
claim('event',used[19][-1],'description','《旧五代史》同记甲戌自杨刘归邺。',19,'甲戌，帝自楊劉歸鄴。','邺与本段兴唐地名互参；不依据古名提供未经核实坐标。',source='jiuwudaishi-029-923-august',relation='corroborates')
# Paragraph 20: flood barrier and Liang change of commander.
E=event('liang_breaches_yellow_river','朱友贞命滑州决河，水注曹濮郓以限唐军',20,'梁主命于滑州决河，东注曹、濮及郓以限唐兵。',[('梁主','下令决河者')],when='923年八月本段；确日未载',place='滑州、曹州、濮州、郓州',note='以限为军事目的，不能直接推有效阻断全部唐军或给洪水损失现代精确数。')
claim('event',E,'description','《旧五代史》载康延孝言滑州南决堤，水入曹濮汶阳以陷北军。',20,'又自滑州南決破河堤，使水東注曹、濮之間，至於汶陽，彌漫不絕，以陷北軍。','出于康延孝情报陈说，同事独立出处；汶阳与郓地区称谓不当现代无证坐标。',source='jiuwudaishi-029-923-august',relation='corroborates')
event('jing_li_oppose_duan_monitoring','主书追叙敬翔、李振请罢段凝监军，朱友贞拒绝',20,'初，梁主遣段凝监大军于河上，敬翔、李振屡请罢之，梁主曰：“凝未有过。”',[('梁主','遣监并拒罢者'),('段凝','被遣监大军者'),('敬翔','请罢者'),('李振','请罢者')],when='八月换帅前追叙；确年未载',year=None,place='河上、梁廷',note='初、屡提示此前多次，不能都定八月某日；监大军不同后来正帅。')
E=event('duan_seeks_command_bribes','主书记段凝厚赂赵张求招讨使，敬翔李振反对',20,'至是，凝厚赂赵、张求为招讨使，翔、振力争以为不可；赵、张主之，',[('凝','被记厚赂求职者'),('翔','反对者'),('振','反对者')],when='923年八月换帅前',place='梁廷',note='赵张泛集团，本段不逐名所有受贿者；不把政治争执建永久敌对关系。')
claim('event',E,'description','《新五代史》记段凝和赵岩等毁王彦章，最终以凝为招讨。',20,'趙巖等從中日夜毀之，乃罷彥章，以凝為招討使。','独立来源对换帅背景叙法不同，保留主书贿赂、新史毁之，不以两书记述断现代法律定罪。',source='xinwudaishi-032-923-slander',relation='adds')
E=event('duan_replaces_yanzhang','段凝取代王彦章为北面招讨使',20,'竟代王彦章为北面招讨使，',[('段凝','新任北面招讨使'),('王彦章','被替换的招讨使')],when='923年八月；确日未载',place='梁北面军',note='代承前凝，不误倒任命方向；职务互换不等王彦章此时被杀。')
claim('event',E,'description','《旧五代史》梁本纪同记八月以段凝代王彦章北面行营招讨。',20,'八月，以段凝代王彥章為北面行營招討使。','同月同任免互证。',source='jiuwudaishi-010-923-august',relation='corroborates')
event('zhang_quanyi_jing_remonstrate','张全义、敬翔劝朱友贞慎任主帅，梁主不听',20,'天下兵马副元帅张宗奭言于梁主曰：',[('张宗奭','以副元帅进言的张全义'),('梁主','未采谏的朱友贞')],when='923年八月段凝换帅时',place='梁廷',note='张宗奭按已有别名规范张全义；无须创建同名新主体。')
claim('event',used[20][-1],'description','敬翔称将帅系国家安危，梁主皆不听。',20,'敬翔曰：“将帅系国安危，今国势已尔，陛下岂可尚不留意邪！”梁主皆不听。','敬翔进言和张全义同事件，两者话语各按原文；宿将士卒不服是主书概述。')
pk=person('敬翔',20,'劝慎任将帅者','敬翔曰：“将帅系国安危，今国势已尔，陛下岂可尚不留意邪！”梁主皆不听。');ek='participation_zztj_272_0923_jing_command_advice';B['person_events'].append(dict(key=ek,person_key=pk,event_key=used[20][-1],role='劝慎任将帅者',status='draft'));claim('person_event',ek,'role','敬翔劝朱友贞留意将帅任用。',20,'敬翔曰：“将帅系国安危，今国势已尔，陛下岂可尚不留意邪！”','同段另一明示进谏者。')
# Paragraphs 21–23.
E=event('duan_crosses_gaoling_to_dunqiu','段凝率五万营王村，渡高陵津，剽掠澶州至顿丘',21,'戊子，凝将全军五万营于王村，自高陵津济河，剽掠澶州诸县，至于顿丘。',[('凝','率军渡河剽掠者')],when='923年八月戊子',place='王村、高陵津、澶州、顿丘',note='五万是主书兵数，全军范围为段凝所部，非整个后梁全部武力。')
claim('event',E,'description','《旧五代史》唐本纪同记戊子五万营王村、自高陵渡河。',21,'戊子，凝帥眾五萬結營於王村，自高陵渡河。','同日兵数路线互证。',source='jiuwudaishi-029-923-august',relation='corroborates')
claim('event',E,'description','《旧五代史》梁本纪称渡河后复临河而还。',21,'戊子，段凝營於王村，引軍自高陵渡河，復臨河而還。','该书后程补说，不以此删除主书澶州至顿丘。',source='jiuwudaishi-010-923-august',relation='adds')
E=event('yanzhang_yun_border_deployment','朱友贞遣王彦章万人屯兖郓边境，张汉杰监军',22,'梁主又命王彦章将保銮骑士及它兵合万人，屯兗、郓之境，谋复郓州，以张汉杰监其军。',[('梁主','遣屯及监军任命者'),('王彦章','屯兖郓谋复郓主将'),('张汉杰','监该军者')],when='923年八月本段；确日未载',place='兖州、郓州边境',note='兗规范展示兖，原文引用保留；谋复郓是计划，未说已经复城。')
claim('event',E,'description','《旧五代史》梁本纪记王彦章屯郓东境。',22,'命滑州節度使王彥章率兵屯守鄆之東境。','东境是旧史补方位，主书兖郓境并列；不混九月战汶递坊。',source='jiuwudaishi-010-923-august',relation='corroborates')
E=event('cunxu_camps_chaocheng','李存勖引兵屯朝城',23,'庚寅，帝引兵屯朝城。',[('帝','屯朝城者')],when='923年八月庚寅',place='朝城',note='主书明确，不误作同时已至郓州。')
claim('event',E,'description','《旧五代史》唐本纪同记庚寅至朝城。',23,'庚寅，帝御軍至朝城。','同日同地互证。',source='jiuwudaishi-029-923-august',relation='corroborates')
claim('event',E,'description','《旧五代史》梁本纪地名作胡城。',23,'庚寅，唐帝軍於胡城，','朝城/胡城同日同事地名异文，不自动合成两个进军地点，也不改底本字。',source='jiuwudaishi-010-923-august',relation='conflicts')
# Paragraph 24: actual defection, distinct from June's secret letter.
E=event('kang_personally_defects_august','康延孝率百余骑来奔，李存勖赐锦袍玉带',24,'戊戌，康延孝帅百馀骑来奔，帝解所御锦袍玉带赐之，',[('康延孝','率骑来奔者'),('帝','接纳赐衣带者')],when='923年八月戊戌',place='后唐军、朝城本段',note='六月密请降与八月本人来奔分阶段；百余不写精确101人数。')
claim('event',E,'description','《旧五代史》唐本纪同记戊戌康延孝百骑来奔，赐衣带。',24,'戊戌，梁左右先鋒指揮使康延孝領百騎來奔，帝虛懷引見，賜禦衣玉帶，屏人問之。','旧史百骑与主书百余各保留，左右先锋与此前右先锋是称谓差异，未拆两人。',source='jiuwudaishi-029-923-august',relation='corroborates')
event('kang_appointed_bozhou','康延孝为南面招讨都指挥使，领博州刺史',24,'以为南面招讨都指挥使，领博州刺史。',[('康延孝','任南面招讨都指挥使、领博州刺史'),('帝','任命者')],when='923年八月戊戌来奔后',place='后唐、博州',note='以为承康，领不等本人当天赴博州；未提前改李继琛。')
E=event('kang_discloses_liang_governance','康延孝密答李存勖，批评梁朝用人、监军与权贵',24,'帝屏人问延孝以梁事，对曰：',[('帝','屏人问梁事者'),('延孝','报告梁事者')],when='923年八月戊戌来奔后',place='后唐军帐',note='以下批评与败亡预言属于来奔者陈说，不当已独立核实全部政治事实。')
claim('event',E,'description','康延孝称赵张兄弟受贿擅权、任官不择才德，将帅受监军制约。',24,'梁主每出一军，不能专任将帅，常以近臣监之，进止可否动为所制。','主书记录的是康的评价；每出等概括不改成逐役已核清单。')
claim('event',E,'description','《旧五代史》亦载其称赵岩赵鹄张汉杰专政受贿。',24,'趙岩、趙鵠、張漢傑居中專政，締結宮掖，賄賂公行。','姓名增补作为情报归属，不据姓氏构造所有赵张兄弟关系；赵鹄未另扩完整履历。',source='jiuwudaishi-029-923-august',relation='adds')
E=event('kang_reports_liang_four_prong_plan','康延孝报告梁拟十月四路进军的计划',24,'近又闻欲数道出兵，令董璋引陕虢、泽潞之兵自石会关趣太原，霍彦威以汝、洛之兵自相卫、邢洺寇镇定，王彦章、张汉杰以禁军攻郓州，段凝、杜晏球以大军当陛下，决以十月大举。',[('延孝','陈说四路计划者'),('董璋','所报石会关趋太原一路拟将'),('霍彦威','所报趋镇定一路拟将'),('王彦章','所报攻郓一路拟将'),('张汉杰','所报攻郓一路拟将'),('段凝','所报迎唐主力一路拟将'),('杜晏球','所报迎唐主力一路拟将')],when='923年八月来奔时报告；拟十月大举',place='石会关、太原、镇定、郓州',note='近闻欲、决十月是情报和计划，不建立十月四路已经出发的事件；参与身份均标拟。')
claim('event',E,'description','《旧五代史》同载梁拟四路进军与十月大举。',24,'決取十月內大舉。','完整段落各路前句支持；仅引用概括，不伪作已兑现战果。',source='jiuwudaishi-029-923-august',relation='corroborates')
event('kang_advises_direct_dash_liang','康延孝建议待梁分兵后精骑五千自郓直取大梁',24,'愿陛下养勇蓄力以待其分兵，帅精骑五千自郓州直抵大梁，擒其伪主，旬月之间，天下定矣。',[('延孝','献直取大梁策者'),('帝','听取献策者')],when='923年八月来奔陈策时',place='郓州、大梁',note='愿与天下定是作战建议和预测，五千拟军不是此时已经出兵；伪主为来奔者立场，展示不用作正式人名。')
claim('event',used[24][-1],'description','《旧五代史》亦载待分兵，以五千铁骑郓州直抵汴的建议。',24,'陛下但待分兵，領鐵騎五千，自鄆州兼程直抵於汴，不旬日，天下事定矣。','不旬日与主书旬月预估不同，都是预估而非灭梁准确历时。',source='jiuwudaishi-029-923-august',relation='adds')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(19,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review='连续七月底至八月，任团/任圜及姊婿异说并存不合并；罢程六月/七月叙次保留；泽州壬申是遣救非确死亡日；李绍斌赵德钧同人明确；胡城朝城异文；康六月密降与八月本人来奔分开，四路为情报计划。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(19,25)],next_paragraph=Q[25]['id'],supplements=supplements,coverage='卷272正文第19—24段，原文件24—29行；七月甲子后旧事与八月各军行动连续整理。',reviewed_questions=[
 {'paragraph_id':Q[19]['id'],'note':'甲子仅慰李周；任团弟任圜与新史任圜本人、从姊/姊婿异说分别存不建别名；卢程未被杀，主书七月段与新史六月罢不同；壬申救援不是城陷精确日；赵德钧赐李绍斌有明确依据，未来937年后事不录。'},
 {'paragraph_id':Q[20]['id'],'note':'初段凝监军年null；决河军事意图不自动当有效封锁；赵张泛集团不构造全部姓名亲属；换帅职任与异书政治背景分层；张宗奭复用张全义。'},
 {'paragraph_id':Q[21]['id'],'note':'戊子承八月，五万为段凝军；旧史梁本纪渡河后程补说不删除主书剽掠。'},
 {'paragraph_id':Q[22]['id'],'note':'兗展示兖保留原字，万人并非全梁军；谋复郓未等复城，张汉杰监军明确。'},
 {'paragraph_id':Q[23]['id'],'note':'朝城与梁本纪胡城同日异文，未伪作两个营地。'},
 {'paragraph_id':Q[24]['id'],'note':'八月本人来奔不同六月密信；百余/百及左右/右先锋称谓分存；康所报败亡、四路进军与五千直取为评价计划非已执行，月份不提前十月。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
