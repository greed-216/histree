# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 272, year 923, paragraphs 47–55."""
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
 ('tongjian-272-923-regional-courts',P/'sources/library/tongjian-272-923-regional-courts','83be3260','司马光等'),
 ('tongjian-272-923-luoyang-move',P/'sources/library/tongjian-272-923-luoyang-move','83be3260','司马光等'),
 ('jiuwudaishi-030-siyuan-jiji',P/'sources/library/jiuwudaishi-030-siyuan-jiji','83be3260','薛居正等'),
 ('jiuwudaishi-030-fan-governors',P/'sources/library/jiuwudaishi-030-fan-governors','83be3260','薛居正等'),
 ('xinwudaishi-062-jing-name',P/'sources/library/xinwudaishi-062-jing-name','83be3260','欧阳修'),
 ('xinwudaishi-062-zhong-family',P/'sources/library/xinwudaishi-062-zhong-family','83be3260','欧阳修'),
 ('xinwudaishi-069-gao-name',P/'sources/library/xinwudaishi-069-gao-name','83be3260','欧阳修'),
 ('xinwudaishi-037-zhongmou',P/'sources/library/xinwudaishi-037-zhongmou','83be3260','欧阳修'),
 ('xinwudaishi-037-litianxia',P/'sources/library/xinwudaishi-037-litianxia','83be3260','欧阳修'),
 ('xinwudaishi-037-jingjin-kongqian',P/'sources/library/xinwudaishi-037-jingjin-kongqian','83be3260','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:2]]
B = {'format_version': 1, 'batch_key': 'zztj-v272-y0923-p047-p055',
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
for n in range(47, 56):
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
        citation = f'卷272·同光元年（923）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_272_0923_09_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'曹氏（李存勖母）','太妃':'刘氏（李克用妻）',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','梁主':'朱友贞','革':'豆卢革','程':'卢程','质':'卢质','琢':'魏琢','蒙':'申蒙','继韬':'李继韬','继远':'李继远','威':'郭威','曹太夫人':'曹氏（李存勖母）','何瓚':'何瓒','高濛':'高蒙','存儒':'李存儒','朗':'张朗','处球':'张处球','处瑾':'张处瑾','故使':'王镕','李紹榮':'元行钦','曹氏':'曹氏（李存勖母）','刘氏':'刘氏（李克用妻）','武皇':'李克用','考晋王':'李克用','上':'李存勖','帝':'李存勖','执宜':'执宜（李存勖曾祖）','国昌':'李国昌','继岌':'李继岌','硃守殷':'朱守殷','硃安殷':'朱守殷','守殷':'朱守殷','王铁枪':'王彦章','彦章':'王彦章','翔':'敬翔','顺密':'卢顺密','嗣源':'李嗣源','遂严':'刘遂严','颙':'燕颙','梁末帝':'朱友贞','崇韬':'郭崇韬','延孝':'康延孝','延光':'范延光','宗侃':'王宗侃','赵':'赵岩','张':'张汉杰','任团':'任团','圜':'任圜','团':'任团','绍斌':'赵德钧','李绍斌':'赵德钧','凝':'段凝','在珣':'顾在珣','彦朗':'顾彦朗','嘉王宗寿':'王宗寿','魏国夫人刘氏':'刘夫人（李存勖妻）','李绍奇':'夏鲁奇','廷隐':'赵廷隐','嗣彬':'刘嗣彬','知俊':'刘知俊','振':'李振','张宗奭':'张全义'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
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



# Verbatim contiguous spans; source glyphs are never rewritten.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('siyuan_zhongshuling','李嗣源加兼中书令',47,'戊戌','兼中书令；',[('李嗣源','兼中书令者')],when='923年十月戊戌',place='唐廷',note='兼官保留天平节度使，不推同时罢原职。')
claim('event',E,'description','《旧五代史》同记戊戌兼中书令，依前天平节度使。',47,'兼中書令、天平軍節度使、特進，封開國公，','补兼任原镇和封爵，不把兼官等同实际主持全部中书事务。',source='jiuwudaishi-030-siyuan-jiji')
E=ev('jiji_tokyo_guardian','李继岌任东京留守、同平章事',47,'以北京留守',None,[('继岌','原北京留守、改任东京留守者')],when='923年十月戊戌',place='此时东京兴唐府',note='主书北京与旧史北都原名分别保留，不误作后来的汴州东京。')
claim('event',E,'description','《旧五代史》同记李继岌东京留守，补检校太尉。',47,'李繼岌為檢校太尉、同平章事，充東京留守。','同人同日同任。',source='jiuwudaishi-030-siyuan-jiji',relation='corroborates')
ev('regional_governors_tribute','李存勖遣使宣谕，原梁节度使五十余人入贡',48,'帝遣使宣谕诸道','皆上表入贡。',[('帝','遣使宣谕者')],when='923年灭梁后，十一月前本段背景',place='诸道、唐廷',note='五十余为史载数，无名单不虚造；上表不等亲至。')
ev('chuwang_sends_xifan','马殷遣马希范入见，交纳洪鄂都统印及将吏籍',48,'楚王殷','上本道将吏籍。',[('楚王殷','遣子者'),('希范','牙内马步都指挥使、交印籍者')],when='923年灭梁后；确日未载',place='楚、唐廷',note='不据交印籍推楚政权已亡或所有官职皆废。')
relationship('楚王殷','希范','父亲',48,'楚王殷遣其子牙内马步都指挥使希范入见，','其子明确，A马殷是B马希范父亲。')
E=ev('gao_resumes_jixing_name','高季昌避唐庙讳改名高季兴',48,'荆南节度使高季昌','更名季兴，',[('高季昌','改名者')],when='923年闻灭梁后',place='荆南',note='已有高季兴别名，仍复用高季昌key。')
claim('event',E,'description','《新五代史》补避后唐献祖庙讳。',48,'本名季昌，避後唐獻袓廟諱，更名季興。','底本袓字原样保留，展示献祖正常字形；不新建同人。',source='xinwudaishi-069-gao-name')
ev('liangzhen_warns_gao_visit','梁震劝勿入朝，高季兴不听',48,'欲自入朝','季兴不从。',[('季兴','欲入朝者'),('梁震','劝阻者')],when='923年闻灭梁后，入朝之前',place='荆南',note='欲朝不是此刻已抵洛阳；被扣担忧和吞天下为梁震判断。')
ev('tang_notifies_wu_shu','李存勖告吴蜀灭梁，主书称二国皆惧',48,'帝遣使以灭梁','二国皆惧。',[('帝','遣使告捷者')],when='923年灭梁后',place='唐、吴、前蜀',note='使者无名；皆惧为作者情绪概括，不凭此造两君亲自军事行动。')
ev('yan_keqiu_predicts_tang_unrest','严可求答徐温，主张卑辞厚礼、待唐内变',48,'徐温尤严可求曰','保境安民以待之耳。”',[('徐温','责问者'),('严可求','预测内变、答策者')],when='923年闻灭梁后',place='吴廷',note='骄满无法是严的评语；数年内变为预测，未在923年虚录后来的事件。')
ev('wu_tang_letter_protocol','吴拒唐使称诏，唐改国书，吴复书用笺表礼',48,'唐使称诏','辞礼如笺表。',[('帝','改书的唐主'),('吴主','吴方杨溥')],when='923年灭梁后往复外交',place='唐、吴',note='无名使者不建虚名；吴国主以本时杨溥核，不推两方始终完全同等礼制。')
ev('zhong_taizhang_accused_replaced','钟泰章遭侵市官马举报，王稔代寿州，泰章改饶州',48,'吴人有告寿州','以泰章为饶州刺史。',[('钟泰章','被举报改任者'),('徐知诰','依吴王命调任者'),('吴王','命令来源杨溥'),('王稔','霍丘巡视后代寿州者')],when='923年本段；确日未载',place='寿州、霍丘、饶州',note='告为指控，不当已定罪；不把王稔单骑推五千军。')
ev('zhong_taizhang_questioning','徐温召钟泰章至金陵，陈彦谦三次诘问未获答',48,'徐温召至金陵','皆不对。',[('徐温','召问者'),('泰章','不答者'),('陈彦谦','三诘者')],when='923年本段、调任后',place='金陵',note='三为次数，不推三日。')
ev('zhong_taizhang_defence','钟泰章对问者陈说忠义、拒绝自辩',48,'或问泰章','以彰朝廷之失！”',[('泰章','陈说者'),('王稔','答辞言及的代任者')],when='923年本段；确日未载',place='吴',note='十万五千是答辞兵数，非独立统计；县令是假设被降，不是本次实际任命。')
ev('xu_wen_blocks_prosecution','徐知诰欲治钟泰章，徐温忆其救命旧恩而阻止',48,'徐知诰欲以法','安可负之！”',[('徐知诰','欲收治罪者'),('徐温','不许者'),('泰章','被保护者'),('张颢','追叙中的旧敌')],when='923年本段决策；救命旧事另属追叙',place='吴廷',note='欲治罪未成判刑；吾非泰章已死是假设，不生成徐温已死事件。')
E=ev('jing_zhong_marriage_arrangement','徐温命徐知诰为景通娶钟泰章女',48,'命知诰',None,[('徐温','作命者'),('知诰','为子安排婚姻者'),('景通','当时徐景通、规范李璟'),('其女（钟泰章）','婚姻安排中的女子'),('泰章','女子之父')],when='923年本段；完婚确日未载',place='吴',note='命娶不等本日已完婚；新史南唐世系核女子为钟氏。李璟是规范后名，本时景通。')
claim('person',people['李璟'],'aliases','景通与后来李璟同一人，李昪长子。',48,'景，初名景通，昪長子也。既立，又改名璟。','仅核前后名及身份，不提前录943年即位册后。',source='xinwudaishi-062-jing-name')
claim('person',people['钟氏（李璟妻）'],'description','《新五代史》记李煜母钟氏，其父名泰章。',48,'母鍾氏，父名泰章。','该段先称煜为景之子，母钟氏之父泰章；作为婚姻人物身份补证，不录961年嗣位。',source='xinwudaishi-062-zhong-family')
relationship('徐知诰','景通','父亲',48,'命知诰为子景通娶其女以解之。','为子明确，规范A李昪是B李璟父亲，非徐温亲子。')
relationship('泰章','其女（钟泰章）','父亲',48,'命知诰为子景通娶其女以解之。','其女承钟泰章，并经新史母系回查。')
ev('shu_comet_record','主书记舆鬼有彗星，蜀司天监言国有大灾',49,'彗星见舆鬼','国有大灾。',[],when='923年本段；确日未载',place='天象舆鬼；地面观测点未载',note='长丈余为史载估计，未现代天文回算；国灾为占候机构判断。')
ev('shu_yuju_ritual','王宗衍诏玉局化设道场',49,'蜀主诏于','设道场，',[('蜀主','设道场令者')],when='923年彗星记事后；确日未载',place='玉局化',note='原地名无核定坐标；不以仪式解释灾异实际消除。')
ev('zhang_yun_banished_dies','张云上疏谏灾，王宗衍流之黎州，云卒于道',49,'右补阙张云',None,[('张云','上疏、被流道卒者'),('蜀主','流张云者')],when='923年本段；道卒确日未载',place='流向黎州途中',note='亡国之征为谏语，不当923年蜀亡；卒于道不等已到黎州或被斩。')
claim('person',people['张云'],'death_year','主书923年条记张云流黎州，卒于道。',49,'蜀主怒，流云黎州，卒于道。','属该年条但无确日，不作处斩。')
ev('chongtao_requests_governor_titles','郭崇韬请解决河南官未授职之疑，十一月始降制命官',50,'郭崇韬上言',None,[('郭崇韬','上言者')],when='923年十一月始降制；建议在此前',place='河南诸镇、唐廷',note='恐忧疑为郭判断，无具体名单不把各镇任命虚合为某同一天。')
E=ev('duan_taining_via_jingjin','段凝经景进纳货宫掖，获泰宁节度使',51,'滑州留后',None,[('李绍钦','本时李绍钦、规范段凝'),('景进','伶人纳货渠道')],when='923年十一月；旧史辛丑朔条',place='唐宫、泰宁军',note='姓名变化不另建人物；纳货据主书，无金额不虚填。')
claim('event',E,'time_original','《旧五代史》十一月辛丑朔条记李绍钦为兖州节度使。',51,'以滑州兵馬留後、檢校太保李紹欽為兗州節度使。','兖州为泰宁军军府称谓，主书无确日；旧史辛丑承该分段起首。',source='jiuwudaishi-030-fan-governors')
ev('cunxu_performs_with_actors','主书记李存勖戏庭悦刘夫人，以李天下为优名',52,'帝幼善音律','优名谓之“李天下！”',[('帝','戏优者'),('魏国夫人刘氏','所悦的刘夫人')],when='幼与或时为习惯背景；确年未载',year=None,place='宫庭',note='不能把幼年或每次表演全定923年；优名为同一李存勖，不另建李天下。')
E=ev('jing_xinmo_slaps_cunxu','敬新磨批李存勖颊，以李天下一人释语，获厚赐',52,'尝因为优','厚赐之。',[('帝','被戏批、赐赏者'),('敬新磨','批颊释语者')],when='尝：追叙，确年未载',year=None,place='宫庭',note='戏剧言行不误作叛乱袭击或虚设演出日。')
claim('event',E,'description','《新五代史》同记批颊、众惧、释语获赐。',52,'莊宗大喜，賜與新磨甚厚。','同事传记或有史源依赖，不算另一次独立事件。',source='xinwudaishi-037-litianxia',relation='corroborates')
E=ev('zhongmou_hunt_jing_saves_magistrate','中牟令谏猎践田，敬新磨以反语使帝释之',52,'帝尝畋于中牟','帝笑而释之。',[('帝','猎践田、欲杀后释者'),('敬新磨','反语救谏者')],when='尝：追叙，确年未载',year=None,place='中牟',note='县令未名不造姓名；将杀未执行，敬新磨请刑为讽语而非真处死。')
claim('event',E,'description','《新五代史》同事，补诸伶唱和、县令获免。',52,'因前請亟行刑，諸伶共唱和之，莊宗大笑，縣令乃得免去。','集体唱和未具名，无虚造其他参与者。',source='xinwudaishi-037-zhongmou')
ev('actors_chronicle_political_criticism','主书评诸伶受贿侮弄缙绅，景进居首',52,'诸伶出入宫掖','景进为之首。',[('景进','作者政治评价对象')],when='持续背景，起始确年未载',year=None,place='宫掖、诸镇',note='蠹政害人为作者评价，未造每条匿名行贿记录。')
E=ev('jingjin_private_intelligence','李存勖委景进耳目，景进干预政事，孔谦以兄礼事之',52,'进好采闾阎','孔岩常以兄事之。',[('景进','受委耳目、参与政事者'),('上','委任者'),('孔岩','主书疑字，经新史同事匹配孔谦')],when='本段持续政治情形，确年未载',year=None,place='唐廷',note='底本孔岩疑讹，新史同事明三司使孔谦；原字不改，复用孔谦而不造孔岩人物。兄事非血缘，谗慝为作者评价。')
claim('event',E,'description','《新五代史》记景进参与军机，孔谦兄事呼八哥。',52,'三司使孔謙兄事之，呼為「八哥」。','为主书孔岩疑字补身份证；保留两书原字，未把兄礼当兄弟。',source='xinwudaishi-037-jingjin-kongqian')
E=ev('qiwang_congratulatory_letter','李茂贞遣使贺灭梁，以季父自居',53,'壬寅',None,[('岐王','遣使自称季父者'),('帝','受贺者')],when='923年十一月壬寅',place='凤翔至唐廷',note='外交季父自居不建血缘叔侄；辞礼倨为主书评价。')
claim('event',E,'description','《旧五代史》同日记李茂贞遣使贺收复天下。',53,'壬寅，鳳翔節度使、秦王李茂貞遣使賀收復天下。','岐王秦王两书称谓分别留，未凭不同王号造此处新封事件。',source='jiuwudaishi-030-fan-governors',relation='corroborates')
E=ev('youqian_visit_banquet','朱友谦入朝，李存勖宴赐',54,'癸卯',None,[('硃友谦','河中节度使来朝者'),('帝','宴赐者')],when='923年十一月癸卯',place='唐廷',note='无算为作者概括，未填财物金额。')
claim('event',E,'description','《旧五代史》同日记朱友谦来朝。',54,'癸卯，河中節度使、西平王朱友謙來朝。','乙巳赐名在下一段，未提前同一日期录入。',source='jiuwudaishi-030-fan-governors',relation='corroborates')
ev('quanyi_requests_luoyang_capital','张全义请迁都洛阳，李存勖接受',55,'张全义',None,[('张全义','请迁都者'),('帝','接受者')],when='923年十一月癸卯后本段；确日未载',place='洛阳为拟迁目的地',note='从为决策，不等当天迁入；十二月抵洛阳见后文。')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续47—55段；李绍钦归段凝，景通归李璟、知诰归李昪；钟女经新史回查，命娶不伪定已完婚；兄事、季父自居不建血缘；伶人尝和习惯年null；中牟县令未名未死；孔岩疑字按新史孔谦核同人；天象占候与谏语不作真实超自然因果；迁都从议未当实际迁入。'
for n in range(47,56):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=272,year=923,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(47,56)],next_paragraph=Q[56]['id'],supplements=supplements,coverage='卷272第47—55段，原文件52—60行；区域政权外交、吴廷婚姻安排、前蜀谏言及唐廷伶人追叙。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(47,56)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
