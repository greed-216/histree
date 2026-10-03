# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 277, year 931, paragraphs 11–20."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 51))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'1066c58f','薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('liaoshi') else '欧阳修'))
specs.extend([
 ('tongjian-277-931-february',YEAR/'part-01/sources/library/tongjian-277-931-february','91251854','司马光等'),
 ('xinwudaishi-064-meng-campaign',YEAR.parent/'year-0930/part-04/sources/library/xinwudaishi-064-meng-campaign','73f70bd8','欧阳修'),
])

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-277-931-february']
B = {'format_version': 1, 'batch_key': 'zztj-v277-y0931-p011-p020',
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
lines = (ROOT / 'resources/derived/tongjian/277.txt').read_text().splitlines()
for n in range(11, 21):
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
        citation = f'卷277·长兴二年（931）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_277_0931_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','重诲':'安重诲','知祥':'孟知祥','仁罕':'李仁罕','廷隐':'赵廷隐','璋':'董璋','知诰':'李昪','吴主':'杨溥','齐丘':'宋齐丘','景通':'李璟','突欲':'耶律倍','惕隐':'赫邈','从珂':'李从珂'}
NEW_ALIASES={'安崇阮':[]}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=931, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='931年'+('二月' if n<=13 else '三月')+'本段；确日未独载'
    key = 'event_zztj_277_0931_' + code
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
        edge = 'participation_zztj_277_0931_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_277_0931_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive nine paragraphs, chronological facts and independently located supplements.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
feb='jiuwudaishi-042-931-february';mar='jiuwudaishi-042-931-march';anpost='jiuwudaishi-040-an-chongruan-post';song='xinwudaishi-061-931-song-post';qian='xinwudaishi-067-qian-restoration';bei='liaoshi-072-bei-tang-names';meng='xinwudaishi-064-meng-campaign'
E=ev('an_appointed_huguo','后唐以安重诲为护国节度使',11,'辛丑，','为护国节度使。',[('重诲','原枢密使兼中书令、出任护国者')],when='931年二月辛丑',place='护国军',note='出镇与后来死亡分；护国与河中为军与治所称法，经旧纪官职对照，不强现代坐标。')
claim('event',E,'description','旧明宗纪同辛丑以安为河中节度使，进沂国公。',11,'以樞密院使、守太尉、兼中書令安重誨為檢校太師、兼中書令，充河中節度使，進封沂國公。','辛丑同段前文承；补检校太师兼中书令封沂衔，出镇不等当日已到河中。',source=feb,relation='corroborates')
E=ev('zhaofeng_defends_an','赵凤向李嗣源称安重诲家臣不叛，因不能周防受谗，若不察将难免死',11,'赵凤言于上曰：','重诲死无日矣。”',[('赵凤','为安申辩者'),('上','受谏者'),('重诲','被申辩的出镇者')],note='不叛受谗及将死均赵观点，不能把未叛和具体谗罪当司法已证，死亡后段独录。')
E=ev('emperor_dislikes_zhao_defense','李嗣源将赵凤为安申辩视作朋党，不悦',11,'上以为朋党','上以为朋党，不悦。',[('上','不悦申辩者'),('赵凤','被认为朋党者')],note='朋党是帝判断，不生成赵已被依法判党罪或实际同安叛乱。')
E=ev('zhao_li_retreat_keep_lizhou_garrison','赵廷隐、李肇自剑州引还，留五千戍利州',11,'乙巳，','戍利州。',[('廷隐','撤主军留戍者'),('李肇','撤主军留戍者')],when='931年二月乙巳',place='剑州、利州',note='五千是共留兵，非各五千；未独返成都日不补。')
E=ev('dong_returns_dongchuan_keeps_garrisons','董璋还东川，留三千戍果、阆',11,'丙午，',None,[('璋','返东川而分留戍者')],when='931年二月丙午',place='东川、果州、阆州',note='三千共戍数不两州各三千；地名不直接绘现代边界。')
E=ev('lirenhan_takes_zhongzhou','李仁罕攻陷忠州',12,'丁巳，',None,[('仁罕','攻陷忠州者')],when='931年二月丁巳',place='忠州',note='与杨汉宾930奔忠为不同动作，不把到忠直接当投降已发生。')
E=ev('xu_proposes_song_chancellor','徐知诰拟以中书侍郎、内枢使宋齐丘为相',13,'吴徐知诰欲','为相，',[('知诰','拟任宋相者'),('齐丘','中书侍郎内枢使、拟任对象')],place='吴',note='欲为相是提议，主后致仕授仆射不是已实相；徐沿李昪主体。')
E=ev('song_requests_hongzhou_burial','宋齐丘自认为资望浅，欲退让取高，谒归洪州葬父',13,'齐丘自以','葬父，',[('齐丘','请归洪州葬父者')],place='吴、洪州',note='欲以退让为高是史述动机，谒归是请归，未明确父名不造父亲实体、不独证本句已完成葬礼。')
E=ev('song_enters_jiuhua_requests_reclusion','宋齐丘入九华山止应天寺，启求隐居',13,'因入九华山，','启求隐居；',[('齐丘','入山住寺求隐者')],place='九华山、应天寺',note='求隐与永久终身不任官不同，后回朝分。')
E=ev('wu_xu_summon_song_not_arrive','杨溥诏征宋齐丘，徐知诰致书召，宋均未至',13,'吴主下诏征之，','皆不至。',[('吴主','诏征者'),('知诰','致书召者'),('齐丘','未应召到者')],place='吴至九华山',note='诏与书两种召方式，皆不至承宋，不是两召者没有到山。')
E=ev('jing_enters_mountain_persuades_song','徐知诰遣其子徐景通入山敦谕宋齐丘',13,'知诰遣其子','自入山敦谕，',[('知诰','派子劝召者'),('景通','亲入山敦谕者'),('齐丘','被劝归者')],place='九华山',note='景通沿李璟，不因父徐子徐时名重复建李氏实体。')
relationship('知诰','景通','父亲',13,'知诰遣其子景通自入山敦谕，','李昪→李璟父亲沿既有稳定key，不造反向重复；原当时父子徐姓名保留。')
E=ev('song_returns_youpuye_retired','宋齐丘始还朝，除右仆射致仕',13,'齐丘始还朝，','除右仆射致仕，',[('齐丘','还朝受右仆射致仕者')],place='吴朝',note='致仕为授后退休衔，不误写立刻实拜宰相专政。')
claim('event',E,'description','新吴世家大和三年记右仆射宋齐丘与王令谋皆平章事。',13,'以其子景通為司徒，及左僕射王令謀、右僕射宋齊丘皆平章事。','承前大和三年为931；新记平章与主本次右仆射致仕叙法不同，不将全年不同授职压成此段同时实拜相，未提前四年东海王等。',source=song,relation='conflicts')
E=ev('yingtian_renamed_zhengxian','应天寺更名征贤寺',13,'更命应天寺',None,[('齐丘','归朝引起寺名变更的隐居者')],place='九华山应天寺、征贤寺',note='未具独立发命人主语，不指定一定宋亲改或私改；不推新建一座寺。')
E=ev('lirenhan_takes_wanzhou','李仁罕攻陷万州',14,'三月，己未朔，','李仁罕陷万州；',[('仁罕','攻陷万州者')],when='931年三月己未朔',place='万州')
E=ev('lirenhan_takes_yunan','李仁罕攻陷云安监',14,'庚申，',None,[('仁罕','攻陷云安监者')],when='931年三月庚申',place='云安监',note='云安监沿史行政生产地名，非监狱，也不误替今日云阳县县境。')
E=ev('bei_given_dongdan_muhua_posts','东丹王突欲获赐姓东丹名慕华，授怀化节度使及瑞慎州观察使',15,'辛酉，','瑞、慎等州观察使；',[('突欲','被赐姓名任官的东丹王')],when='931年三月辛酉',place='后唐、怀化、瑞慎',note='沿耶律倍，赐姓不造新东丹慕华主体；不提前后又李赞华姓名。')
claim('event',E,'description','旧明宗纪同辛酉记东丹慕华任怀化军，兼检校太保安东都护，州名作瑞镇。',15,'詔渤海國人皇王突欲宜賜姓東丹，名慕華，仍授檢校太保、安東都護，充懷化軍節度、瑞鎮等州觀察等使。','旧瑞镇与主瑞慎字差留，辽倍传瑞慎支持不能静改旧；兼衔补，不以辽后移滑虔名提前。',source=mar,relation='adds')
claim('person',people['耶律倍'],'description','辽倍传记唐迎倍至汴，赐东丹慕华，拜怀化军及瑞慎州观察。',15,'賜姓東丹，名之曰慕華。改瑞州為懷化軍，拜懷化軍節度使、瑞慎等州觀察使。','倍、突欲、东丹慕华沿同主体；辽传后李赞华及936被害未提前录事件，当前只核此名官身份。',source=bei,relation='corroborates')
E=ev('beis_followers_captured_generals_given_names','朝廷为突欲部曲和此前被俘的契丹将赐姓名',15,'其部曲','皆赐姓名。',[('突欲','其部曲获赐姓名的东丹王'),('惕隐','此前被俘的契丹将之一')],note='跟随倍的部曲与先俘将为两类人，不能把赫邈说成930同船新俘；主未名他将不凭旧补名单全造。')
E=ev('he_miao_named_di_huaihui','此前被俘契丹将惕隐获赐姓狄名怀惠',15,'惕隐姓狄',None,[('惕隐','获赐狄怀惠姓名的被俘将')],note='惕隐官名只按928定州援败后被武从谏擒的赫邈主体、旧定州先俘范围识，不视所有年代惕隐同人。')
claim('person',people['赫邈'],'description','旧纪称此前在定州被擒的惕隐获赐狄怀惠，兼检校右散骑常侍。',15,'先於定州擒獲蕃將，惕隱宜賜姓狄，名懷惠，','原既有928同役生擒及新赫邈对应作为识别；不因官名通用合别的惕隐，新赐名以事实引用追踪，沿原key。',source=mar,relation='adds')
E=ev('an_yang_flee_from_kuizhou','李仁罕至夔州，安崇阮弃镇，与杨汉宾经均房逃归',16,'李仁罕至夔州，','逃归；',[('仁罕','进抵夔州者'),('安崇阮','宁江节度使、弃镇逃归者'),('杨汉宾','同安经均房逃归者')],place='夔州、均州、房州',note='杨汉宾沿930弃黔奔忠者，逃归朝廷不写成向孟投降；安不混安重诲崇绪崇赞。')
claim('person',people['安崇阮'],'description','旧明宗纪929五月乙酉以黔州节度使安崇阮为夔州节度使。',16,'以黔州節度使安崇阮為夔州節度使，','补原任官身份同夔州军镇，宁江为军名不拆成两人；未本批重复建929任命，拒合安崇宗等近名。',source=anpost,relation='adds')
claim('event',E,'description','新孟世家亦记李仁罕攻夔，安崇阮弃城走。',16,'李仁罕進攻夔州，刺史安崇阮棄城走，','主宁江节度使与新刺史衔层次差留；新后赵季良任留后属于后续主线，此批不提前。',source=meng,relation='corroborates')
E=ev('lirenhan_takes_kuizhou','李仁罕攻陷夔州',16,'壬戌，',None,[('仁罕','攻陷夔州者')],when='931年三月壬戌',place='夔州',note='弃镇与正式入城陷落分，前弃未独干支不自动同日。')
E=ev('emperor_reunites_licongke','李嗣源解安重诲枢务后召李从珂，泣称若从安意则父子不得再见',17,'帝既解','汝安得复见吾！”',[('帝','解安枢务后召子泣语者'),('从珂','被召见者'),('重诲','被帝谈及者')],note='帝归安意的话不等原所有杀从珂计划已独证；亲子称谓不新造生父边，李从珂为养子既有关系另循。')
claim('event',E,'description','旧明宗纪同记李从珂河中失守后归清化里，安出镇河中后帝召见泣语。',17,'從珂自河中失守，歸清化裏第，至是安重誨出鎮河中，帝召見，泣而謂之曰：「如重誨意，爾安得更相見耶！」','补旧宅地点和召语对应，不新建先前河中失守重复事件。',source=mar,relation='corroborates')
E=ev('licongke_left_guard_general','后唐以李从珂为左卫大将军',17,'丙寅，',None,[('从珂','受任左卫大将军者')],when='931年三月丙寅',note='任职不提前本人934即位或出任凤翔。')
E=ev('kongxun_dies','横海节度使同平章事孔循卒',18,'壬申，',None,[('孔循','去世的横海节度使')],when='931年三月壬申',place='横海',note='孔循沿赵殷衡既有身份，不混孔谦孔谦军将。')
claim('event',E,'description','旧明宗纪同壬申记沧州节度使孔循卒，废朝。',18,'壬申，以滄州節度使孔循卒廢朝。','沧州是横海治所称法，两书同人同日，不当另死于两个州；废朝原无天数不补。',source=mar,relation='corroborates')
E=ev('qian_restored_titles','后唐复钱镠天下兵马都元帅、尚父、吴越国王',19,'乙酉，','吴越国王，',[('钱镠','获复官爵者')],when='931年三月乙酉',place='吴越',note='复授与930纲使自便不同动作，新安死后说时差保留不改主三月。')
claim('event',E,'description','旧明宗纪同乙酉复钱官爵，称子元瓘等上表首罪。',19,'乙酉，太師致仕錢鏐復授天下兵馬都元帥、尚父、吳越國王，以其子兩浙節度使元瓘等上表首罪，故有是命。','旧复爵同日佐核，首罪为表述不当全部过去指控已独证；元瓘沿既有钱传瓘不新造人或新增未读表事件。',source=mar,relation='corroborates')
claim('event',E,'time_original','新吴越世家记安重诲死后明宗复钱官爵，与主三月复爵先于安死的顺序不同。',19,'安重誨死，明宗乃復鏐官爵。','新简叙死亡先后差独保留，不强改主月份，也不提前本批安已死。',source=qian,relation='conflicts')
E=ev('zhangjian_sent_qian_edict','后唐遣监门上将军张篯向钱镠谕旨，称此前致仕为安重诲矫制',19,'遣监门上将军',None,[('张篯','监门上将军、传谕使者'),('钱镠','受谕获复者'),('重诲','被归责矫制者')],when='931年三月乙酉诏后；行程确日未载',place='后唐至吴越',note='遣为派使不是已在钱庭读旨；矫制为朝廷本次谕旨归责，保留出处不据一语重写全部旧削爵决策；张篯沿926西都张籛，非兄张筠。')
E=ev('liyu_appointed_chancellor','后唐以太常卿李愚为中书侍郎、同平章事',20,'丁亥，',None,[('李愚','太常卿转中书侍郎同平章事者')],when='931年三月丁亥',place='后唐')
claim('event',E,'description','旧明宗纪同丁亥任李愚中书侍郎平章事，并兼集贤殿大学士。',20,'丁亥，以太常卿李愚為中書侍郎、平章事、集賢殿大學士。','补学士衔与主同任，不另外建另一次拜相。',source=mar,relation='corroborates')
reviews={11:'辛丑安护国=旧河中出镇，未当已死亡；赵不叛受谗将死为赵申辩，帝朋党为帝判断，不造党罪判决。乙巳赵李退五千共留利、丙午董退三千共留果阆，不各分数字。',12:'二月丁巳忠陷分后夔万军进，主独证不硬新夔整段套每座已证。',13:'徐欲齐相非已任；谒归葬父为请求父未名不造，入寺隐居诏书召皆未至、景通敦谕、齐还右仆射致仕、寺改名分。李昪父李璟复用，杨溥吴主稳定。新吴大和三年右仆射皆平章与主本次致仕叙法并列，不压全年不同任命。新宋传篡事成后入九华等未独证同931一次，仅检索核校不新增未来事件。',14:'三月己未朔万、庚申云安监分日，监为史辖名非监狱不绘现代县界。',15:'辛酉突欲沿耶律倍，东丹慕华新姓名同人，辽后李赞华未提前；主瑞慎旧瑞镇辽瑞慎字差留。部曲与先俘契丹将两类分，赫邈据928同救定州被擒及旧先俘范围识，不把官名惕隐全历通用。旧其它先俘将仅快照背景，主未列不此批扩造其姓名。',16:'安新宁江主将旧929黔转夔同人补，安不混重诲等。杨汉宾沿930黔弃至忠，二者弃经均房归朝非降孟。壬戌陷夔与前弃未独日分；新后赵季良留后主后文待录不提前。',17:'解安枢后召从珂泣语与丙寅任左卫分。帝如安意为归责不独证所有谋害细目；从珂养子不建生父边。旧清化里为原归宅补，不重建旧河中失守。',18:'壬申孔循卒，旧沧州治所主横海军同职称法，废朝无具天数不造。',19:'乙酉复钱爵与930纲使自便分别，旧同日首罪表述不确过罪。新安死后复衔与主三月时序差并列，未提前安死。遣张谕为派令非已至，矫制归本谕旨所言不覆写全部旧史决策；张篯籛沿926同人不混兄筠。',20:'丁亥李愚拜相同旧补集贤殿学士，一任不造另一学士任事具体日。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=277,year=931,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v277-y0931-p021',next_volume=277,next_year=931,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷277连续931年第11—20段、原73—82行；安出镇、两川撤留戍、宋入山敦召致仕、峡路陷州、突欲惕隐赐名、李从珂复见授官、孔卒、钱复爵及李愚拜相。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(11,21)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
