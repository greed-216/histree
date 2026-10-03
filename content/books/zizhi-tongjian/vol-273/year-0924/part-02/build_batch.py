# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 273, year 924, paragraphs 13–24."""
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
 ('tongjian-273-924-salt-empress',P/'sources/library/tongjian-273-924-salt-empress','7ec9cfdc','司马光等'),
 *[(key,P/'sources/library'/key,'7ec9cfdc',author) for key,author in [
 ('jiuwudaishi-031-salt-empress','薛居正等'),('jiuwudaishi-031-privy-resignation','薛居正等'),
 ('jiuwudaishi-031-border-gao-cunxian','薛居正等'),('jiuwudaishi-053-cunxian-successor','薛居正等'),
 ('jiuwudaishi-049-han-principal','薛居正等'),
 ('xinwudaishi-024-inner-audit-empress','欧阳修'),('xinwudaishi-024-lineage-claim','欧阳修')]],
 ('xinwudaishi-005-924-annals',YEAR/'part-01/sources/library/xinwudaishi-005-924-annals','fa5fd41a','欧阳修'),
 ('xinwudaishi-069-gao-departure',ROOT/'content/books/zizhi-tongjian/vol-272/year-0923/part-11/sources/library/xinwudaishi-069-gao-departure','b88b07ee','欧阳修'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v273-y0924-p013-p024',
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
lines = (ROOT / 'resources/derived/tongjian/273.txt').read_text().splitlines()
for n in range(13, 25):
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
people, used, reused, supplements = {}, {}, {'xinwudaishi-005-924-annals','xinwudaishi-069-gao-departure'}, []

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
        citation = f'卷273·同光二年（924）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_273_0924_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote, source=None):
    name = {'韩夫人':'韩夫人（李存勖正妃）','硃勍':'朱勍','正方':'王正言','正言':'王正言','李继\ue4be严':'李继曮','继\ue4be严':'李继曮','李崇韬':'郭崇韬','高季兴':'高季昌','存渥':'李存渥','继达':'李继达','继俦':'李继俦','杨氏':'杨氏（李继韬母）','蘋':'卢苹','卢蘋':'卢苹','光胤':'赵光胤','光逢':'赵光逢','说':'韦说','岫':'韦岫','廷珪':'薛廷珪','逢':'薛逢','宪':'张宪','谦':'孔谦','绍冲':'温韬','李绍冲':'温韬','李继麟':'朱友谦','李绍琛':'康延孝','李绍安':'袁象先','希范':'马希范','季兴':'高季昌','景通':'李璟','知诰':'李昪','泰章':'钟泰章','新磨':'敬新磨','进':'景进','孔岩':'孔谦','其女（钟泰章）':'钟氏（李璟妻）','李绍钦':'段凝','李紹欽':'段凝','李绍虔':'杜晏球','李紹虔':'杜晏球','陆思鐸':'陆思铎','思鐸':'陆思铎','昭图':'温韬','温昭图':'温韬','硃友贞':'朱友贞','晏球':'杜晏球','岳':'刘岳','崇龟':'刘崇龟','翘':'封翘','敖':'封敖','权':'王权','龟':'王龟','撒刺阿拨':'撒剌阿拨','存纪':'李存纪','绍宏':'李绍宏','硃珪':'朱珪','朱圭':'朱珪','友诲':'朱友诲','邵王友诲':'朱友诲','全昱':'朱全昱','友谅':'朱友谅','友雍':'朱友雍','友徽':'朱友徽','麟':'皇甫麟','闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','契丹主':'阿保机','耶律阿保机':'阿保机','述律后':'述律平','处琪':'张处琪','高季昌女':'高季昌女（倪知进妻）','知进':'倪知进','季昌':'高季昌','循':'苏循','习':'符习','蒙':'符蒙','处瑾':'张处瑾','郁':'王郁','都':'王都','刘云郎':'王都','赵王':'王镕','王太保':'张文礼','钱镒':'钱镒','镒':'钱镒','涛':'李涛','惠王友能':'朱友能','友能':'朱友能','鄩':'刘鄩','张宗奭':'张全义','蜀主':'王宗衍','吴主':'杨溥','唐高祖':'李渊','韦妃':'王宗衍韦妃','高知言女':'王宗衍高氏妃','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
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
                   aliases={'韩夫人（李存勖正妃）':['韓夫人（李存勖正妃）'],'朱勍':['硃勍'],'李龟祯':['李龜禎'],'李继曮':['李繼曮','李继严','李繼嚴','李从曮','李從曮','李从严','李從嚴'],'杨氏（李继韬母）':['楊氏（李繼韜母）'],'卢苹':['卢蘋','盧蘋'],'李继珂':['李繼珂'],'赵光胤':['趙光胤'],'韦说':['韋說'],'韦岫':['韋岫'],'薛廷珪':[],'薛逢':[],'王稔':[],'李璟':['徐景通','景通','李景'],'钟氏（李璟妻）':['鍾氏（李璟妻）'],'张云':['張雲'],'景进':['景進'],'敬新磨':[],'陆思铎':['陸思鐸','陆思鐸'],'刘岳':['劉嶽','劉岳'],'任赞':['任讚'],'姚顗':[],'封翘':['封翹'],'李怿':['李懌'],'刘光素':['劉光素'],'陆崇':['陸崇'],'王权':['王權'],'王龟':['王龜'],'封敖':[],'赵鹄':['趙鵠'],'张希逸':['張希逸'],'李存纪':['李存紀'],'朱友诲':['朱友誨'],'皇甫麟':[],'顾在珣':['顧在珣'],'刘赞':['劉贊'],'蒲禹卿':[],'李知节':['李知節'],'赵廷隐':['趙廷隱'],'刘嗣彬':['劉嗣彬'],'任钊':['任釗'],'田章':[],'任团':['任團'],'赵德钧':['趙德鈞','李绍斌','李紹斌'],'李周':[],'焦彦宾':['焦彥賓'],'范延光':[],'康延孝':[],'李绍兴':['李紹興'],'卢顺密':['盧順密'],'刘遂严':['劉遂嚴'],'燕颙':['燕顒'],'崔筜':['崔簹'],'朱守殷':['硃守殷'],'李德休':[],'执宜（李存勖曾祖）':['執宜'],'豆卢革':['豆盧革'],'卢程':['盧程'],'崔协':['崔協'],'魏琢':[],'申蒙':[],'裴约':['裴約'],'董璋':[],'郭威':[],'李存儒':['杨婆儿','楊婆兒'],'张朗':['張朗'],'张处球':['張處球'],'李再丰':['李再豐'],'李冲（李再丰子）':[],'高蒙':['高濛'],'何瓒':['何瓚'],'张宪':['張憲'],'赵季良':['趙季良'],'躬乂':['躬乂（大封王）'],'王建（高丽）':['王建（高麗）'],'秃馁':['禿餒'],'石万全':['石萬全'],'张处琪':['張處琪'],'齐俭':['齊儉'],'彭赟':['彭贇'],'崔太初':[],'高季昌女（倪知进妻）':[],'倪知进':['倪知進'],'倪曙':[]}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷273同光二年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='924年本段；确日未载', note='', year=924, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_273_0924_' + code
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
        edge = 'participation_zztj_273_0924_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_273_0924_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quotes preserve the contiguous source paragraph.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('youqian_salt_request','朱友谦请求专榷安邑解县盐，每季输省课',13,'河中','每季输省课。',[('李继麟','河中节度使、请榷者')],when='924年二月己卯任职前',place='安邑、解县盐池',note='李继麟复用朱友谦；每季输课为请议条件，不算四季已足额缴完。')
E=ev('youqian_salt_commission','朱友谦任制置两池榷盐使',13,'己卯',None,[('李继麟','受任者')],when='924年二月己卯',place='安邑、解县两池')
claim('event',E,'description','旧史同己卯以李继麟兼两池榷盐使。',13,'己卯，以河中節度使、冀王李繼麟兼安邑、解縣兩池榷鹽使。','同日任职印证，不造李继麟另一主体。',source='jiuwudaishi-031-salt-empress',relation='corroborates')
E=ev('maozhen_qin_king','李茂贞进爵秦王，仍不名不拜',14,'辛己',None,[('岐王','进爵受礼者')],when='924年二月，主书辛己疑日字，旧史辛巳',place='唐廷、凤翔',note='辛己非规范干支组合，保留底本，旧史对应条作辛巳；不自行换公历；不拜不名为礼遇。')
claim('event',E,'time_original','旧史辛巳记秦王李茂贞仍不拜不名。',14,'以開府儀同三司、守尚書令、秦王李茂貞依前封秦王，餘如故，仍賜不拜、不名。','该句处辛巳张全义条后，旧史用依前封秦与主书进爵记序不同，保持各书称谓，不强说首次受册同义。',source='jiuwudaishi-031-salt-empress')
E=ev('shaohong_inner_audit','郭崇韬置内句使掌三司财赋，任李绍宏',15,'郭崇韬知','移报之烦。',[('崇韬','设置任职者'),('绍宏','内句使受任者')],when='924年二月本段；设置确日未载',place='唐廷、州县财赋',note='平怨之冀、未悦、徒增烦为主书解释和评价；内句与内勾是书间官称，不等财政三司新建。')
claim('event',E,'description','新史同记内勾使掌租庸出入，后因文簿繁多罢其事。',15,'凡天下錢穀出入于租庸者，皆經內勾。既而文簿繁多，州縣為弊，遽罷其事，','补制度后续，既而具体废止年日未给，不提前定此段同日已罢或设置固定年限。',source='xinwudaishi-024-inner-audit-empress')
ev('chongtao_favourites_conflict','主书记郭崇韬权重性急，抑嬖幸求请，宦官向帝诋毁他',15,'崇韬位','欲制之不能。',[('崇韬','被记拒请及受谤者'),('上','受宦官谗言的君主')],when='任将相后此段总结，确年未载',year=None,place='唐廷',note='权侔人主、性刚急等为作者品评；匿名宦官不等特定已知某个人，每次进谗未给日期。')
E=ev('chongtao_fenyang_descent_claim','豆卢革韦说问郭氏族源，郭崇韬自称与汾阳王相距四世',15,'豆卢革','固从祖也。”',[('革','询族源并称从祖者'),('说','同问者'),('崇韬','自述谱牒遗失及世距者')],when='尝问为不定次追叙，确年未载',year=None,place='唐廷',note='自述及迎合话语未见谱牒，不能据此建郭子仪为曾祖或确定血缘，四世也不简单计算出生年代。')
claim('event',E,'description','新史记因郭姓而以为子仪后，郭崇韬认可。',15,'以其姓郭，因以為子儀之後，崇韜遂以為然。','新史同属来源说法，不能作为独立谱牒确证；未把以后伐蜀墓前哭事提前录。',source='xinwudaishi-024-lineage-claim',relation='corroborates')
ev('chongtao_status_based_selection','主书记郭崇韬以门第甄别官人，拒门地寒素求职者，引发勋旧怨',15,'崇韬由是','勋旧怨之于外。',[('崇韬','被记按门第选人者')],when='此段持续行为总结，确年未载',year=None,place='唐廷选官',note='勋旧怨为主书概述，不把所引匿名求官者合为已知官人。')
E=ev('chongtao_offers_privy_shaohong','郭崇韬屡请让枢密使给李绍宏，帝不许，又请分院务归内诸司',15,'崇韬屡请','谤之不已。',[('崇韬','让职及分务请议者'),('绍宏','被提议继职者'),('上','不准让职者')],when='924年本段所记屡请，确日未列',place='唐廷枢密院',note='主书不许明确针对让职；分务只记又请，不能自行认定同获准或已执行。')
claim('event',E,'description','旧史二月壬辰记郭崇韬再表请退枢密，优诏不允。',15,'壬辰，樞密使郭崇韜再上表，請退樞密之職，優詔不允。','补一次请退日次，不将主书屡请全压壬辰同日。',source='jiuwudaishi-031-privy-resignation',relation='corroborates')
ev('chongtao_considers_own_command','郭崇韬与亲近者谋赴本镇避谗，遭劝阻',15,'崇韬郁郁',None,[('崇韬','谋退本镇者')],when='此段未列确日，赴镇未成',year=None,place='唐廷，拟赴本镇',note='谋与实际行止分开，未发生本镇出行，亲近者未名。')
E=ev('liu_empress_plan_delayed','追叙李存勖欲立刘夫人为后，因有韩正妃及曹太后郭崇韬反对而未果',16,'先是','不果。',[('上','欲立后者'),('魏国夫人刘氏','拟立后对象'),('韩夫人','已有正妃'),('太后','不喜刘氏的曹氏'),('崇韬','屡谏者')],when='924年册立前先是追叙，确年未载',year=None,place='唐宫',note='先是背景不锁924；主书素恶与不果为其叙述，韩正妃当前称名，未提前记未来淑妃册封。')
claim('person',people['韩夫人（李存勖正妃）'],'description','旧史卷49列韩氏为庄宗正室。',16,'淑妃韓氏，莊宗正室。','旧史传用后称淑妃确认本主体，底本注明原传缺佚；引注册年后文不作为当前册封。',source='jiuwudaishi-049-han-principal',relation='corroborates')
E=ev('chongtao_supports_liu_empress','亲近者建议借皇后助力，郭崇韬与百官奏立刘夫人',16,'于是所亲','正位中宫。',[('崇韬','受劝转而奏请者'),('魏国夫人刘氏','被奏请立后者')],when='924年二月癸未立后前',place='唐廷',note='内有后助为游说策略，不说已证明后确替郭排除一切谗害；匿名亲近者不造姓名。')
claim('event',E,'description','新史同记亲近者劝借中宫援助，郭上书请立刘氏。',16,'崇韜以為然，乃上書請立劉氏為皇后。','同建议改变补证，后果并非立刻实现。',source='xinwudaishi-024-inner-audit-empress',relation='corroborates')
E=ev('liu_established_empress','魏国夫人刘氏被立为皇后',16,'癸未','为皇后。',[('魏国夫人刘氏','册立对象'),('帝','立后君主')],when='924年二月癸未',place='唐廷',note='此前求情史传追称刘皇后与当时刘夫人区别；此立后日不等所有后续册礼同日。')
claim('event',E,'description','旧史癸未制立魏国夫人刘氏，并另令择日备礼册命。',16,'製以魏國夫人劉氏為皇后，仍令所司擇日備禮冊命。','制立与以后礼册各自步骤，不把择日礼仪当已完成。',source='jiuwudaishi-031-salt-empress',relation='corroborates')
claim('event',E,'time_original','新史亦记二月癸未立刘氏。',16,'癸未，立劉氏為皇后。','正文事实引用；评论立后正不正的编校议论不当历史事件。',source='xinwudaishi-005-924-annals',relation='corroborates')
ev('liu_wealth_trading_background','主书记刘夫人在魏州贩售薪苏果茹等积财',16,'皇后生','皆贩鬻之。',[('魏国夫人刘氏','被记经营积财者')],when='此前在魏州的追叙，确年未载',year=None,place='魏州',note='寒微、专务等为主书描述，未凭此猜生年或收入数量。')
ev('empress_contributions_treasures','主书记立后后贡献分进天子中宫，刘后积宝用于写经施尼',16,'及为后',None,[('魏国夫人刘氏','中宫受贡及用财者'),('帝','天子受贡者')],when='924年立后后持续习惯，起讫未载',year=None,place='唐廷、中宫',note='贡献分二及惟用于经尼为主书归纳，不计全量统计，不能断定此癸未即已全额收齐。')
ev('cao_liu_orders_equal','主书记曹太后诰、刘皇后教与制敕同被藩镇奉行',17,'是时',None,[('太后','曹氏、诰命来源'),('魏国夫人刘氏','刘皇后、教命来源'),('帝','制敕来源君主')],when='924年立后后是时，确日未載',place='唐诸藩镇',note='政治实践的作者概述，未造具体某份教令内容；奉之如一不是正式颁布一条三命平等法。')
ev('zhuqing_dredges_suoshui','唐诏蔡州刺史朱勍疏浚索水以通漕运',18,'诏',None,[('硃勍','受诏疏水者')],when='924年二月末本段，确日未載',place='蔡州、索水',note='诏令任务不等工程已竣工；硃归朱，不能混襄州孔勍；索水原名未核现代流域及坐标。')
ev('shu_yishen_feast','王宗衍与近臣宫人在怡神亭饮宴，主书记脱冠喧哗',19,'三月','喧哗自恣。',[('蜀主','前蜀君主宴主')],when='924年三月己亥朔',place='前蜀怡神亭',note='喧哗自恣是主书叙述，不由编辑量化醉酒程度；干支与底本一致，未自行换算公历。')
ev('li_guizhen_admonition','李龟祯谏前蜀君臣饮酒误政，王宗衍不听',19,'知制诰',None,[('李龟祯','京兆人、知制诰谏者'),('蜀主','不听谏者')],when='924年三月己亥朔宴时',place='怡神亭',note='恐启北敌谋是李的担忧，不证明唐已因本宴制定攻蜀计划；京兆为籍贯不是宴所在地。')
E=ev('zhenzhou_khitan_alert','镇州奏契丹将犯塞',20,'乙巳','将犯塞，',[],when='924年三月乙巳奏报',place='镇州、北塞',note='将犯为预警，不等当日已经攻破镇州。')
E=ev('shaobin_congke_cavalry','唐诏赵德钧与李从珂率骑分道备契丹，李嗣源屯邢州',20,'诏横海','屯邢州。',[('李绍斌','横海节度使、分道备敌者'),('李从珂','北京左厢马军指挥使、备敌者'),('嗣源','屯邢州者')],when='924年三月乙巳',place='北边分道、邢州',note='李绍斌复用赵德钧；北京称名以太原语境，不设现代北京市坐标。')
claim('event',E,'description','旧史乙巳条同记镇州报契丹、诏李嗣源屯邢州。',20,'鎮州奏，契丹犯塞，詔李嗣源率師屯邢州。','主书将犯与旧史犯塞奏的措辞并列，不凭省略确断实际攻击先后；旧史未列李从珂在此句。',source='jiuwudaishi-031-border-gao-cunxian',relation='corroborates')
claim('person',people['赵德钧'],'aliases','本段记李绍斌原姓赵名行实、幽州人。',20,'绍斌本姓赵，名行实，幽州人也。','别名赵行实与赵德钧既有主体合并，先核规范名，无新造同姓李某。')
E=ev('gao_nanping_honour','高季兴加兼尚书令，并记封南平王',21,'丙午',None,[('高季兴','荆南节度使、受加官封王者')],when='924年三月丙午；新史传记封王年不同',place='唐廷、荆南',note='高季兴规范主体高季昌；主书时封封王与加官并记，旧史同日，异年另列。')
claim('event',E,'description','旧史同丙午加高季兴尚书令、封南平王。',21,'丙午，以荊南節度使、守中書令、渤海王高季興依前檢校太師、兼尚書令，封南平王；','同日两件印证。',source='jiuwudaishi-031-border-gao-cunxian',relation='corroborates')
claim('event',E,'time_original','新史高氏传记同光三年封南平王。',21,'同光三年，封南平王。','同光三年为925，与主书和旧史924不同，保留冲突，不在925预生成第二个封王事件。',source='xinwudaishi-069-gao-departure',relation='conflicts')
ev('cunshen_requests_audience','符存审病重屡请入觐先遭郭崇韬阻，后获许',22,'李存审','乃许之。',[('李存审','病中求觐者'),('崇韬','先不许者'),('帝','最终准入觐者')],when='924年三月李存贤任卢龙前',place='幽州至唐廷为拟行程',note='感愤因未预克汴为主书解释，准入觐不证明已与帝见面，病日不作死亡年。')
E=ev('cunxian_wrestling_promise','追叙李存贤与李存勖手搏，将帝仆倒，帝曾许胜则授藩镇',22,'初，帝','仅仆帝而止。',[('帝','手搏及许诺者'),('李存贤','手搏胜者')],when='初为此前追叙，确年未载',year=None,place='唐宫，具体处所未载',note='手搏是角力，非战场击杀；初未定年，授镇许诺与后来任官区分。')
E=ev('cunxian_lulong_successor','李存贤先任卢龙行军司马，旬日后任节度使，李存勖称践手搏之约',22,'及许',None,[('李存贤','被任司马后节度使者'),('帝','任命并说明者')],when='924年三月本段，司马后旬日任节度使',place='卢龙、幽州',note='旬日为约十日，不算具体公历日；手搏约为帝所称理由，不认全部任命动机仅此。')
claim('event',E,'time_original','旧史本纪丙午记李存贤由幽州行军司马为幽州节度使。',22,'以幽州節度行軍司馬李存賢依前檢校太保，為幽州節度使。','同丙午条依郭高前文日次，可补本纪授职日，不把最初司马日强推十日前。',source='jiuwudaishi-031-border-gao-cunxian',relation='corroborates')
claim('event',E,'description','旧史李存贤传记帝选北门主帅，称即日授卢龙节度使。',22,'即日授特進、檢校太保，充幽州盧龍節度使。','主书司马旬日后升任与传即日不同，保留叙事粒度差异；五月到镇及以后死亡不提前录。',source='jiuwudaishi-053-cunxian-successor',relation='conflicts')
ev('khitan_xincheng_report','幽州奏契丹寇新城',23,'庚戌',None,[],when='924年三月庚戌奏报',place='幽州、新城',note='奏报日不同实际开战首日，地点只用史名不设现代坐标。')
ev('siyuan_requests_army_release','李嗣源因勋臣畏谗背景请求解兵柄，李存勖不许',24,'勋臣',None,[('嗣源','蕃汉内外马步副总管、请求解兵者'),('帝','拒绝解兵者')],when='924年三月本段，确日未载',place='唐廷',note='勋臣皆不安是主书概括，求解不等已罢兵权，不把后来政变提前作为当前动机确证。')
relationship('韩夫人','帝','妻子',16,span(16,'先是','不果。'),'上即李存勖，正妃韩夫人为其妻；原文未给成婚年份，不虚构婚期。')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
review='连续13—24段；李继麟朱友谦、李绍斌赵德钧、李存审符存审、高季兴高季昌同主体；辛己疑干支旧史辛巳保留；内句内勾同官，新史后罢无确年；郭自陈四世无谱牒，不建确定郭子仪血缘；退枢密与赴镇只是请谋；韩正妃不提前册淑妃，立后制令和择日礼册分清；贩财、受贡惯例确年未给null；索水诏浚非已竣；蜀宴与谏言不造攻蜀因果；高封王924与新史925异说并列；李存贤手搏追叙年null，司马旬日后授镇与旧传即日并列，准符入觐非实际见面，未来到镇与卒未提前录。'
for n in range(13,25):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=273,year=924,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(13,25)],next_paragraph=Q[25]['id'],supplements=supplements,coverage='卷273第13—24段，原文件18—29行；盐政、进爵、内句枢密、立后、漕运、蜀宴及契丹边事。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(13,25)]),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
