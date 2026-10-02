"""Curate consecutive Tongjian volume 271, year 921, paragraphs 7–14."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 25))
specs = [
    ('tongjian-271-921-spring', YEAR / 'part-01/sources/library/tongjian-271-921-spring', '668adafc', '司马光等'),
    ('jiuwudaishi-054-wang-zhaohui', P / 'sources/library/jiuwudaishi-054-wang-zhaohui', '3ae6868a', '薛居正等'),
    ('xinwudaishi-039-wang-zhaohui', P / 'sources/library/xinwudaishi-039-wang-zhaohui', '3ae6868a', '欧阳修'),
    ('jiuwudaishi-062-zhang-wenli-seizes', P / 'sources/library/jiuwudaishi-062-zhang-wenli-seizes', '3ae6868a', '薛居正等'),
    ('jiuwudaishi-010-zhu-youneng-revolt', P / 'sources/library/jiuwudaishi-010-zhu-youneng-revolt', '3ae6868a', '薛居正等'),
    ('jiuwudaishi-010-longde-edict', P / 'sources/library/jiuwudaishi-010-longde-edict', '3ae6868a', '薛居正等'),
    ('jiuwudaishi-010-zhu-youneng-surrenders', P / 'sources/library/jiuwudaishi-010-zhu-youneng-surrenders', '3ae6868a', '薛居正等'),
    ('jiuwudaishi-023-liu-xun-death', P / 'sources/library/jiuwudaishi-023-liu-xun-death', '3ae6868a', '薛居正等'),
    ('jiuwudaishi-063-zhang-quanyi-name', ROOT / 'content/books/zizhi-tongjian/vol-270/year-0917/part-04/sources/library/jiuwudaishi-063-zhang-quanyi-name', '28106b55', '薛居正等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0921-p007-p014',
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
for n in range(7, 15):
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
people, used, reused, supplements = {}, {}, {'tongjian-271-921-spring','jiuwudaishi-063-zhang-quanyi-name'}, []

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
        citation = f'卷271·龙德元年（921）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0921_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','高祖':'王建','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨溥',
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
                   aliases={'张友顺':['張友順'],'普宁公主':['普寧公主']}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271龙德元年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='921年本段；确日未载', note='', year=921, place='五代十国'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0921_' + code
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
        edge = 'participation_zztj_271_0921_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

def relationship(a,b,kind,n,quote,note):
    pa=person(a,n,f'{b}之{kind}',quote); pb=person(b,n,f'与{a}关系对象',quote)
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
        row=dict(key=f'relationship_zztj_271_0921_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note)
event('wang_rong_delegates_zhaozuo','王镕委政于王昭祚',7,
 '赵王既杀李弘规、李霭，委政于其子昭祚。',[('赵王','委政于子者'),('昭祚','受父委政者')],
 when='921年二月条背景；李弘规、李蔼被杀已见920年末',place='镇州',
 note='既杀回接前一年族诛，不重复新增李弘规或李蔼被杀事件；本项记委政后果。')
event('wang_zhaozuo_purges_li_honggui_followers','王昭祚族诛旧附李弘规者',7,
 '昭祚性骄愎，既得大权，曏时附弘规者皆族之。',[('昭祚','得权后族诛旧附弘规者')],
 when='921年二月条背景；确日未载',place='镇州',note='骄愎属主书人物评价；未将全部旧部五百人直接当作已被杀。')
event('wang_rong_delays_guard_rewards','王镕因石希蒙被杀而不及时给亲军赏赐，军众益惧',7,
 '会诸军有给赐，赵王仇亲军之杀石希蒙，独不时与，众益惧。',[('赵王','独不时给亲军赏赐者')],
 when='921年二月条；确日未载',place='镇州',note='此前石希蒙被杀已录920；此处记赏赐及军众恐惧，不重建其死亡。')
event('zhang_wenli_incites_guard_fear','张文礼以王命尽坑之说激亲军',7,
 '王德明素蓄异志，因其惧而激之曰：“王命我尽坑尔曹。吾念尔曹无罪并命，欲从王命则不忍，不然又获罪于王，奈何？”众皆感泣。',
 [('王德明','以王命尽坑之说激军的张文礼')],when='921年二月条；镇州军乱前',place='镇州',
 note='这是张文礼激众时的说法，不能据此认定王镕真实下过坑杀令；王德明沿用已校核张文礼身份。')
claim('event',used[7][-1],'description','《旧五代史》亦记李宏规部下五百人恐惧、张文礼以尽坑之说激众。',7,
 '及宏規見殺，其部下五百人懼罪，將欲奔竄，聚泣偶語，未有所之。','印证恐惧背景；李宏规与通鉴李弘规沿用校核身份，原字不改。',source='jiuwudaishi-062-zhang-wenli-seizes',relation='corroborates')
event('guards_murder_wang_rong','镇州亲军逾城杀王镕，焚其府第',7,
 '赵王方焚香受箓，二人断其首而出，因焚府第。',[('赵王','焚香受箓时被亲军杀害的王镕')],
 when='921年二月条之是夕；确日未载',place='镇州',note='承前潭城西门宿卫饮酒谋乱、逾城而入；杀人者无名，未把张友顺或张文礼误录为执刀者。')
claim('person',people['王镕'],'death_year','王镕于921年二月条记被亲军杀害。',7,
 '赵王方焚香受箓，二人断其首而出，因焚府第。','按本年二月条，不另换算日次。')
event('zhang_youshun_asks_wenli_acting','张友顺率军请张文礼为留后，张文礼复姓名',7,
 '军校张友顺帅众诣德明第，请为留后，德明复姓名曰张文礼，',
 [('张友顺','率军请留后的军校'),('王德明','受请为留后、复姓名张文礼者')],
 when='921年二月王镕遇害后',place='镇州',note='军校率众请求与四月晋王承制授任分开；同一人物更名，不另建王德明实体。')
event('zhang_wenli_kills_wang_clan_keeps_princess','张文礼屠王氏亲族，留普宁公主以托梁',7,
 '尽灭王氏之族，独置昭祚之妻普宁公主以自托于梁。',
 [('王德明','主书记屠王氏亲族并留公主者'),('普宁公主','被留以托梁的王昭祚之妻'),('昭祚','其妻被留的王氏成员')],
 when='921年二月镇州军乱后',place='镇州',note='尽灭为主书概述；其他书明确王昭诲幸存，不能据此说王氏绝后。王昭祚被杀具体经过另据旧史补证。')
massacre=used[7][-1]
claim('event',massacre,'description','《旧五代史》记张文礼在乱翌日索王昭祚，斩于军门。',7,
 '鎔長子昭祚，亂之翌日，張文禮索之，斬於軍門。','补充王昭祚被杀时序；未与王镕遇害当夜混成同日。',source='jiuwudaishi-054-wang-zhaohui')
claim('person',people['王昭祚'],'death_year','王昭祚于王镕遇害之翌日被张文礼斩于军门。',7,
 '鎔長子昭祚，亂之翌日，張文禮索之，斬於軍門。','对应主书921年镇州军乱，未另换算日期。',source='jiuwudaishi-054-wang-zhaohui')
pk=person('王昭诲',7,'王镕次子、乱中获救者','次子昭誨。當鎔被禍之夕，昭誨為軍人攜出府第，置之地穴十餘日，乃髡其發，被以僧衣。',source='jiuwudaishi-054-wang-zhaohui')
claim('event',massacre,'description','《旧五代史》记王昭诲被军人救出、匿地穴后穿僧衣；王氏有幸存者。',7,
 '次子昭誨。當鎔被禍之夕，昭誨為軍人攜出府第，置之地穴十餘日，乃髡其發，被以僧衣。','对尽灭作具体例外补充；未把后文明宗朝及显德授官录成921发生。',source='jiuwudaishi-054-wang-zhaohui',relation='conflicts')
claim('person',pk,'description','《新五代史》亦记王昭诲被藏地穴、剃发披僧衣，并由李震载往湖南。',7,
 '其軍士有德鎔者，藏之穴中，亂定，髠其髮，被以僧衣，遇湖南人李震，匿昭誨於茶籠中，載之湖南，','印证幸存及转送；十岁与旧史表文十余岁并存，未据年龄倒推生年。',source='xinwudaishi-039-wang-zhaohui',relation='corroborates')
edge='participation_zztj_271_0921_wang_zhaohui_survives_clan_slaughter'
B['person_events'].append(dict(key=edge,person_key=pk,event_key=massacre,role='被军人救出、幸存的王镕之子',status='draft'))
claim('person_event',edge,'role','王昭诲为乱中被军人救出的幸存者。',7,
 '當鎔被禍之夕，昭誨為軍人攜出府第，','参与事实来自独立补证；不据主书尽灭错误记其死亡。',source='jiuwudaishi-054-wang-zhaohui')
relationship('普宁公主','昭祚','妻子',7,'昭祚之妻普宁公主','妻子明文，适用王昭祚遇害前；原书无个人名。')
claim('person',people['普宁公主'],'description','《旧五代史》记王昭祚妻朱氏被留以通梁，称普宁公主无恙。',7,
 '惟留王昭祚妻朱氏通梁人；尋間道告於梁曰：「王氏喪於亂軍，普寧公主無恙。」','朱氏姓有书证，不据此新增独立朱氏实体；无恙为张文礼报梁的说法。',source='jiuwudaishi-062-zhang-wenli-seizes',relation='corroborates')

event('wu_returns_qian_yi','吴归钱镠从弟钱镒于钱唐',8,
 '三月，吴人归吴越王镠从弟龙武统军镒于钱唐，',[('镒','被归吴越的龙武统军、钱镠从弟'),('吴越王镠','接归从弟的吴越王')],
 when='921年三月',place='钱唐',note='从弟为较年幼的堂亲，关系用堂弟；不记成同父兄弟。')
event('wuyue_returns_li_tao','钱镠归吴将李涛于广陵',8,
 '镠亦归吴将李涛于广陵。',[('钱镠','归还吴将李涛者'),('李涛','被归吴的将领')],when='921年三月',place='广陵',
 note='沿用887、913年吴将李涛主体；与后晋后汉宰相同名者不能合并。')
event('xu_wen_promotes_li_tao','徐温任李涛为右雄武统军',8,
 '徐温以涛为右雄武统军，',[('徐温','任命李涛者'),('涛','受任右雄武统军者')],when='921年三月',place='吴')
event('qian_liu_promotes_qian_yi','钱镠任钱镒为镇海节度副使',8,
 '镠以镒为镇海节度副使。',[('钱镠','任命钱镒者'),('镒','受任镇海节度副使者')],when='921年三月',place='吴越')
relationship('镒','钱镠','堂弟',8,'吴越王镠从弟龙武统军镒','从弟为同宗较幼堂亲，保留堂弟而非同父弟弟；钱镒沿用903年主体。')
event('zhang_wenli_seeks_jin_commission','张文礼向晋王报乱劝进，请求节钺',9,
 '张文礼遣使告乱于晋王，且奉笺劝进，因求节钺。',[('张文礼','报乱劝进并求节钺者'),('晋王','受报及劝进者')],
 when='921年镇州军乱后、四月授任前',place='镇州、晋行台',note='告乱为张文礼的报告，不把报文自动视为真相。')
event('jin_defers_punishing_zhang_wenli','李存勖闻乱悲泣欲讨，僚佐劝先安张文礼',9,
 '晋王方置酒作乐，闻之，投杯悲泣，欲讨之。僚佐以为文礼罪诚大，然吾方与梁争，不可更立敌于肘腋，宜且从其请以安之。',
 [('晋王','欲讨而受僚佐暂缓建议者')],when='921年张文礼告乱后、四月授任前',place='晋行台',
 note='意见为僚佐提出的战略权衡，不提前录成已出兵讨镇。')
event('jin_commissions_zhang_wenli_acting','李存勖遣卢质授张文礼成德留后',9,
 '王不得已，夏，四月，遣节度判官卢质承制授文礼成德留后。',
 [('晋王','承制授任者'),('卢质','奉命授任的节度判官'),('张文礼','受授成德留后者')],when='921年四月',place='成德、镇州')
claim('event',used[9][-1],'description','《旧五代史》亦记张文礼报事求节、奉笺劝进，庄宗姑含容可其请。',9,
 '以事上聞，兼要節旄，尋亦奉箋勸進，莊宗姑示含容，乃可其請。','印证受命，庄宗为后世称谓；未记此时已称帝。',source='jiuwudaishi-062-zhang-wenli-seizes',relation='corroborates')
event('zhu_youneng_revolts','陈州刺史惠王朱友能举兵趋大梁',10,
 '陈州刺史惠王友能反，举兵趣大梁，',[('友能','自陈州举兵趋大梁的惠王')],when='921年四月条',place='陈州、大梁')
claim('event',used[10][-1],'description','《旧五代史》亦记四月陈州刺史惠王友能反，举兵向阙。',10,
 '夏四月，陳州刺史惠王友能反，舉兵向闕。','印证月次及身份；未据诏书评价添加叛乱动机。',source='jiuwudaishi-010-zhu-youneng-revolt',relation='corroborates')
event('liang_orders_youneng_suppression','梁命霍彦威、王彦章、张汉杰讨朱友能',10,
 '诏陕州留后霍彦威、宣义节度使王彦章、控鹤指挥使张汉杰将兵讨之。',
 [('霍彦威','奉诏讨朱友能的陕州留后'),('王彦章','奉诏讨朱友能的宣义节度使'),('张汉杰','奉诏讨朱友能的控鹤指挥使')],
 when='921年四月条',place='陈州、大梁')
event('youneng_defeated_chenliu_besieged','朱友能至陈留兵败，退陈州被围',10,
 '友能至陈留，兵败，走还陈州，诸军围之。',[('友能','兵败退陈州而被围者')],when='921年四月条',place='陈留、陈州')
claim('event',used[10][-1],'description','《旧五代史》记朱友能退保陈州后，开封太康、襄邑、雍丘三县受陈军冲击，夏税只据见苗输纳。',10,
 '敕開封府太康、襄邑、雍丘三縣，遭陳州賊軍奔衝，其夏稅隻據見苗輸納。','补充叛乱民生与赋税影响；只据见苗是计税依据，不说三县完全免税。',source='jiuwudaishi-010-zhu-youneng-revolt')
e=event('liang_changes_longde','梁改元龙德',11,Q[11]['text'],[],when='921年五月丙戌朔',place='梁',
 note='主书本句省略年号，以旧史卷10改元诏补明龙德元年；此前贞明七年改元前名义保留。')
claim('event',e,'description','《旧五代史》改元诏规定贞明七年改为龙德元年。',11,
 '其貞明七年，宜改為龍德元年，','直接诏书补明改元年号；未将年首龙德标题理解为正月即已改元。',source='jiuwudaishi-010-longde-edict',relation='corroborates')
claim('event',e,'description','改元诏令在禁罪人除大辟外减一等，并免贞明三四年残欠及五六年夏税残税。',11,
 '應天下見禁罪人，除大辟罪外，遞減一等。德音到後，三日內疏理訖奏。應欠貞明三年、四年諸色殘欠，五年、六年夏稅殘稅，並放。',
 '补充有限减刑和指定年份税欠蠲免，不能称无条件全部大赦或所有赋税免除。',source='jiuwudaishi-010-longde-edict')
relationship('刘鄩','硃友谦','姻亲',12,'初，刘鄩与硃友谦为婚。','为婚指婚家、姻亲；未载子女配偶组合，不误写两个男性为夫妻或确定岳父。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《旧五代史》亦称刘鄩与朱友谦为婚家。',12,
 '先是，鄩與河中朱友謙為婚家，','印证姻亲，不另造子女名字。',source='jiuwudaishi-023-liu-xun-death',relation='corroborates')
event('liu_xun_delays_to_persuade_youqian','刘鄩至陕州先遣书谕朱友谦，待月余才进兵',12,
 '鄩之受诏讨友谦也，至陕州，先遣使移书，谕以祸福；待之月馀，友谦不从，然后进兵。',
 [('鄩','先遣书劝归、待月余进兵者'),('硃友谦','不从劝归者')],
 when='追叙920年讨朱友谦途中；确日未载',year=920,place='陕州',
 note='主书初起追叙，结合已录920讨同州及旧史卷23贞明六年校定；只新增先遣书待月余细节，不重复建同州战败事件。')
claim('event',used[12][-1],'description','《旧五代史》亦记刘鄩在陕州停留月余，遣檄谕朱友谦归国而未从。',12,
 '及王師西討，行次陝州，鄩遣使齎檄與友謙，諭以禍福大計，誘令歸國，友謙不從，如是停留月餘。','印证停留与目的；本段起六年六月、九月，接已录920战事。',source='jiuwudaishi-023-liu-xun-death',relation='corroborates')
event('yin_hao_duan_ning_accuse_liu_xun','尹皓、段凝谮刘鄩逗遛养寇，梁帝信之',12,
 '尹皓、段凝素忌鄩，因谮之于帝曰：“鄩逗遛养寇，俾俟援兵。”帝信之。',
 [('尹皓','谮刘鄩者'),('段凝','谮刘鄩者'),('刘鄩','被指逗遛养寇者'),('梁帝','听信谮言者')],
 when='刘鄩讨朱友谦期间或败后背景；确日未载',year=None,place='梁',note='指控与主书素忌评价按叙述归属；不能把待援养寇当刘鄩的已证实真实意图。')
event('liu_xun_seeks_relief_medical_leave','刘鄩败归请解兵柄，梁帝准其西都就医',12,
 '鄩既败归，以疾请解兵柄，诏听于西都就医，',[('刘鄩','以疾请解兵柄、西都就医者'),('梁帝','准西都就医者')],
 when='刘鄩920年战败后、921年五月死亡前；确日未载',year=None,place='西都、洛阳')
event('zhang_quanyi_poison_liu_xun','梁帝密令张宗奭鸩刘鄩，刘鄩卒',12,
 '密令留守张宗奭鸩之，丁亥，卒。',[('梁帝','密令鸩刘鄩者'),('张宗奭','奉命鸩杀刘鄩的留守、即张全义'),('刘鄩','被鸩杀者')],
 when='921年五月丁亥',place='西都、洛阳',note='张宗奭沿用张全义；丁亥承五月丙戌朔之后，不记为追叙920死亡。')
claim('person',people['张全义'],'aliases','张全义在梁时期名张宗奭，后复名全义。',12,
 '初名居言，賜名全義，梁祖改為宗奭；莊宗定河南，復名全義。','明确异名书证；展示使用既有张全义、出处保留张宗奭。',source='jiuwudaishi-063-zhang-quanyi-name')
claim('event',used[12][-1],'description','《旧五代史》亦记河南尹张宗奭承密旨逼刘鄩饮鸩，刘鄩卒时六十四岁。',12,
 '及兵敗，詔歸洛，河南尹張宗奭承朝廷密旨，逼令飲鴆而卒。時年六十四，詔贈中書令。','印证鸩杀并补年龄、赠中书令；旧史未单列死亡确日，以主书921五月丁亥为准，年龄不倒推生年。',source='jiuwudaishi-023-liu-xun-death',relation='corroborates')
claim('person',people['刘鄩'],'death_year','刘鄩卒于921年五月丁亥条。',12,'丁亥，卒。','死亡日依本段主书，六十四岁不自动换算生年。')
event('solar_eclipse_sixth_month','六月乙卯朔日食',13,Q[13]['text'],[],when='921年六月乙卯朔',place='主书未载观测地点',note='史书天象记录，未附现代天文反算或观测地点。')
event('zhu_youneng_surrenders','惠王朱友能降',14,'秋，七月，惠王友能降。',[('友能','七月投降的惠王')],when='921年七月',place='陈州')
event('youneng_pardoned_demoted','梁赦朱友能死罪，降封房陵侯',14,
 '庚子，诏赦其死，降封房陵侯。',[('友能','获免死、降封房陵侯者')],when='921年七月庚子',place='梁',note='免死和降封，不写仍为惠王或完全无处罚。')
claim('event',used[14][-1],'description','《旧五代史》七月庚子诏记朱友能获议亲贷法、降封房陵侯。',14,
 '特施貸法之恩，蓋舉議親之律。','补充皇帝诏书所述议亲宽贷理由；不据诏书伯仲套语推出具体同父兄弟关系。',source='jiuwudaishi-010-zhu-youneng-surrenders')
claim('event',used[14][-1],'description','《旧五代史》诏书明定朱友能降封房陵侯。',14,
 '可降封房陵侯。','印证降封，未采同段末朱友谅封爵作本段朱友能事件。',source='jiuwudaishi-010-zhu-youneng-surrenders',relation='corroborates')

payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(7,15):
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,
  review='921年二月至七月八段连续校核；补旧、新五代史，王氏尽灭有王昭诲幸存例外，张宗奭同张全义；追叙与本年死亡分开。')
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=271,year=921,
 primary_source_key=main_sources[0],primary_source_keys=main_sources,
 paragraphs=[Q[n]['id'] for n in range(7,15)],next_paragraph=Q[15]['id'],supplements=supplements,
 coverage='卷271龙德元年第7—14段连续处理，原文件49—56行：镇州军乱、吴越交换将领、晋授成德留后、朱友能叛降、梁改元、刘鄩被鸩与日食。',
 reviewed_questions=[
 {'paragraph_id':Q[7]['id'],'note':'尽灭王氏为通鉴概述；旧、新史均明确王昭诲幸存，独立补证并记差异。王德明复用张文礼，未误认其为王镕的真亲生子。'},
 {'paragraph_id':Q[8]['id'],'note':'钱镒从弟记堂弟非同父弟；李涛沿用887杨行密将领与913被俘者，不合并后晋后汉同名宰相。'},
 {'paragraph_id':Q[9]['id'],'note':'军校推留后与四月晋承制授任分开；未从劝进记晋已称帝。'},
 {'paragraph_id':Q[10]['id'],'note':'补旧史开封三县按见苗输夏税，未夸为全部免税。'},
 {'paragraph_id':Q[11]['id'],'note':'五月改元龙德由旧史诏补明；减刑除大辟，免税限指定残欠，未概括全部大赦。'},
 {'paragraph_id':Q[12]['id'],'note':'为婚是姻亲非男性夫妻。陕州先谕待月余据旧史六年及已录920战事校定，谮言、请解兵柄确日不明，五月丁亥死亡明确921；张宗奭复用张全义，原文异名有旧史63书证。'},
 {'paragraph_id':Q[13]['id'],'note':'日食仅据史载，不自行反算日期坐标。'},
 {'paragraph_id':Q[14]['id'],'note':'七月庚子免死降封房陵侯，旧史诏书可回查；未将同段朱友谅封爵当作友能。'}]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
