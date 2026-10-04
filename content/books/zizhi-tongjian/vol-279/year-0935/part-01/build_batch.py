# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 935 paragraphs 1–11."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,38))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'104a22bf','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-934-year-end',YEAR.parent/'year-0934/part-10/sources/library/tongjian-279-934-year-end','82c9d42c','司马光等'),
 ('xinwudaishi-040-yichao-siege',ROOT/'content/books/zizhi-tongjian/vol-278/year-0933/part-02/sources/library/xinwudaishi-040-yichao-siege','0f922712','欧阳修'),
 ('jiuwudaishi-136-mengchang-parentage',ROOT/'content/books/zizhi-tongjian/vol-275/year-0927/part-05/sources/library/jiuwudaishi-136-mengchang-parentage','4b8f7b80','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0935-p001-p011',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-123-an-shenqi':'卷123·安审琦传','songshi-485-li-yiyin-name':'卷485·夏国传·李彝兴','jiuwudaishi-136-mengchang-parentage':'卷136·孟昶传'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订2115814；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/279.txt').read_text().splitlines()
for n in range(1, 12):
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
for revision in sorted((ROOT/'content/revisions').glob('*/aliases.json')):
    if not (revision.parent/'publication.json').exists():continue
    for corrected in json.loads(revision.read_text()).get('people',[]):
        if corrected['name'] in registry:registry[corrected['name']]=dict(registry[corrected['name']],aliases=corrected['after'])
people, used, reused, supplements = {}, {}, {key for key, path, _, _ in specs if not path.is_relative_to(P)}, []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'jiuwudaishi-123-an-shenqi':'卷123·安审琦传','songshi-485-li-yiyin-name':'卷485·夏国传·李彝兴','jiuwudaishi-136-mengchang-parentage':'卷136·孟昶传'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '正月条下' if n==1 else '二月条下' if n<=7 else '三月条下'
        citation = f'卷279·清泰二年（935；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0935_01_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','蜀主':'孟昶','闽主':'王延钧','彝殷':'李彝殷','李太后':'李氏（孟昶母）','魏氏':'魏氏（李从珂母）','陈后':'陈金凤','守恩':'陈守恩','匡胜':'陈匡胜','元瓘':'钱传瓘','陈氏':'陈氏（钱传瓘母）','金全':'安金全'}
NEW_ALIASES={'李彝殷':['李彜殷','李彝兴','李彝興'],'陈金凤':['陳金鳳'],'陈守恩':['陳守恩'],'陈匡胜':['陳匡勝'],'陈氏（钱传瓘母）':['陳氏（錢傳瓘母）','陈氏（钱元瓘母）','陳氏（錢元瓘母）'],'安审琦':['安審琦']}

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

def event(code, title, n, quote, actors, when=None, note='', year=935, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='935年'+('正月' if n==1 else '二月' if n<=7 else '三月')+'条下；确日未独载'
    key = 'event_zztj_279_0935_' + code
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
        edge = 'participation_zztj_279_0935_' + code + '_' + pk
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
    corrections={}
    import uuid
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content')
    people_ids={str(uuid.uuid5(namespace,x['key'])):x['key'] for x in registry.values()}
    for revision in sorted((ROOT/'content/revisions').glob('*/relations.json')):
        if not (revision.parent/'publication.json').exists():continue
        for revision_row in json.loads(revision.read_text()).get('relations',[]):corrections[revision_row['key']]=revision_row['after']
    for path in (ROOT/'content').rglob('content-batch.json'):
        if path.resolve()==(P/'content-batch.json').resolve():continue
        for x in json.loads(path.read_text())['person_relationships']:
            if x['key'] in corrections:
                c=corrections[x['key']];x=dict(x,person_a_key=people_ids[c['person_a']],person_b_key=people_ids[c['person_b']],relation_type=c['relation_type'])
            if (x['person_a_key'],x['person_b_key'],x['relation_type'])==(pa,pb,kind):matches[x['key']]=x
    assert len(matches)<=1,matches
    if matches:
        row=dict(next(iter(matches.values())),status='draft'); reused.add(row['key'])
    else:
        row=dict(key=f'relationship_zztj_279_0935_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
E['min_amnesty']=ev('min_first_day_amnesty','正月丙申朔闽大赦',1,'春，正月，','闽大赦。',[('闽主','闽主、大赦者')],when='935年正月丙申朔',place='闽',note='承前闽主王延钧，沿王璘王鏻同人；未具赦书条文和对象范围，不编具体被赦名单。')
E['yonghe']=ev('min_yonghe_era','闽改元永和',1,'改元','永和。',[('闽主','改元者')],when='935年正月丙申朔条下',place='闽',note='承本段正月朔叙事，独立改元，不将新同段王仁达死也统作935。')
claim('event',E['yonghe'],'description','新闽世家也记龙启三年改元永和。',1,'龍啟三年，改元永和。','新具年无正月朔；印证改元，后续王仁达往事不在本批扩录。',source='xinwudaishi-068-yonghe-era',relation='corroborates')
ev('shu_first_day_amnesty','二月丙寅朔蜀大赦',2,'二月，','蜀大赦。',[('蜀主','后蜀主、大赦者')],when='935年二月丙寅朔',place='蜀',note='孟昶已继位，蜀主沿已有主体；未记改元，不把本次赦令与改元捆绑。')
E['fan']=ev('fan_yanguang_xuanwu_appointment','二月甲戌范延光由枢密使天雄节度使转任宣武节度使兼中书令',3,'甲戌，','兼中书令。',[('范延光','前枢密使天雄节度使兼侍中、新宣武节度使兼中书令获任者'),('帝','任命者')],when='935年二月甲戌',place='宣武',note='旧汴州为军镇州名写法，不另建汴州任职事件；前任枢密身份不推新命后仍掌枢密。')
claim('event',E['fan'],'description','旧末帝纪同记甲戌范延光由枢密使天雄节度使任汴州节度使兼中书令，并列检校太师。',3,'以樞密使、天雄軍節度使範延光為檢校太師、兼中書令，充汴州節度使；','范、範属底本字形沿范延光；甲戌同日，检校太师独补，不把加衔等同实际三公职掌。',source='jiuwudaishi-047-935-february',relation='corroborates')
ev('li_yichao_reports_illness','二月丁丑李彝超奏报疾病',4,'丁丑，','上言疾病，',[('李彝超','夏州节度使、奏病者')],when='935年二月丁丑',place='夏州',note='奏病为报告，不补病种或病因；与后去世分。')
E['yiyin_acting']=ev('li_yiyin_provisional_xiazhou','行军司马李彝殷权知夏州军州事',4,'以兄行军司马','权知军州事；',[('彝殷','行军司马、权知军州事者')],when='935年二月丁丑奏病条下',place='夏州',note='主以句未独列下令者，不强定李彝超亲令或皇帝下诏。主称兄而旧新宋称弟，亲等异说另列；权知为临时职掌，区别三月正式命。')
E['yichao_death']=ev('li_yichao_dies','李彝超奏病后不久去世',4,'彝超寻','卒。',[('李彝超','寻卒者')],when='935年二月丁丑奏病后、三月任李彝殷前；死日未载',place='夏州',note='寻卒在本年下一命以前，不把丁丑奏日硬当死日；新只具年无日。')
claim('person',people['李彝超'],'death_year','李彝超于935年奏病后去世，确日未载。',4,'彝超寻卒。','同年顺叙，在三月继任前；寻不换算天数。')
claim('event',E['yichao_death'],'description','新李仁福传称李彝超清泰二年卒。',4,'清泰二年卒。','承前传中彝超，已核上下文；只证935年，不证丁丑是死日。',source='xinwudaishi-040-yichao-siege',relation='corroborates')
relationship('彝殷','李彝超','兄弟',4,'以兄行军司马彝殷权知军州事；','兄弟亲属无争议，长幼主称彝殷兄而旧新宋称弟，暂存对称兄弟并明确争议，不将其中一说画成确定兄长方向。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《通鉴》本段称李彝殷为李彝超之兄。',4,'以兄行军司马彝殷权知军州事；','保主原兄字，不用自动繁简或推断抹去长幼异说。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','《宋史》称彝兴为彝超之弟，彝兴本名彝殷，后来因避讳改名。',4,'彝興，彝超之弟也，本名彝殷，避宋宣祖諱，改「殷」為「興」。','与主兄相反，旧三月也称兄彝超；彝兴是宋时改名，仅补别名用于同人匹配，不声称935已经改名。',source='songshi-485-li-yiyin-name',relation='conflicts')
E['li_mother']=ev('meng_chang_honours_li_empress_dowager','二月戊寅孟昶尊母李氏为皇太后',5,'戊寅，','为皇太后。',[('蜀主','尊母者'),('李太后','被尊皇太后者')],when='935年二月戊寅',place='蜀',note='李氏孟昶生母沿既有主体，不与孟知祥妻琼华长公主混同；本年授尊号非新发现母子关系。')
relationship('李太后','孟昶','母亲',5,'蜀主尊母李氏为皇太后。','主母字明示，沿既有孟昶母李氏，A是B母亲；若旧同关系已存则复用。')
claim('person',people['李氏（孟昶母）'],'description','李氏是太原人。',5,'太后，太原人，','太原人为史载籍贯，不强设出生地或经纬度。')
ev('li_mother_former_zhuangzong_palace','追记李氏原属庄宗后宫，后被赐给孟知祥',5,'本庄宗后宫也，','以赐蜀高祖。',[('李太后','原庄宗后宫、被赐孟知祥者'),('李存勖','庄宗、原后宫所属君主'),('孟知祥','蜀高祖、受赐者')],year=None,when='李氏被尊太后之前的往事；具体年份未载',note='后宫不等于皇后，不据此造李氏为庄宗妻的关系；赐为史书记述，年未明不放935。')
claim('person',people['李氏（孟昶母）'],'description','旧孟昶传也记其母李氏原是庄宗嬪御，被赐给孟知祥。',5,'母李氏，本莊宗之嬪御，以賜知祥。','身份同人互核，旧嬪御与主后宫原词分别保，未载本次戊寅尊号日；同传未来965事不提前扩录。',source='jiuwudaishi-136-mengchang-parentage',relation='corroborates')
E['wei']=ev('congke_posthumous_wei_xuanxian','二月己丑追尊李从珂母魏氏为宣宪皇太后',6,'己丑，','曰宣宪皇太后。',[('帝','追尊母亲者'),('魏氏','原鲁国夫人、被追尊者')],when='935年二月己丑',note='追尊身后名号，不当魏氏仍在世任职；主鲁国夫人与旧太夫人独立字样保。')
relationship('魏氏','李从珂','母亲',6,'追尊帝母鲁国夫人魏氏曰宣宪皇太后。','帝为李从珂，母为魏氏，沿旧主体与母亲关系，不反建重复子边。')
claim('event',E['wei'],'description','旧末帝纪记己丑卢文纪等上鲁国太夫人尊谥宣宪皇太后，奏请择日册命，获准。',6,'己丑，宰臣盧文紀等上皇妣魯國太夫人尊諡，曰宣憲皇太后，請擇日冊命。從之。','同日尊谥互核；己丑请择日册命不能说册命典礼当天已经执行。',source='jiuwudaishi-047-935-february',relation='corroborates')
E['chen']=ev('min_chen_jinfeng_empress','闽主王延钧立淑妃陈金凤为皇后',7,'闽主立','为皇后。',[('闽主','立后者'),('陈后','原淑妃、皇后获立者')],place='闽',note='主后续明陈后原名金凤、侍婢身份；陈氏加名用连续句及新姓陈金凤核对，不与楚王母陈氏或吴越母陈氏混同。')
ev('min_two_liu_marriages_background','追述王延钧此前两娶刘氏，书称均出身士族但无宠',7,'初，闽主','皆士族，美而无宠。',[('闽主','两次娶刘氏者')],year=None,when='935年立陈后之前的婚姻往事；本段未列各次年份',place='闽',note='两娶不能将两位刘氏强并为一人；本段没有各自父母、姓名和日期，不强指定都为已有人物刘岩女。美无宠为史书评价，新继室姓金的差异另列。')
claim('person',people['陈金凤'],'description','陈金凤原是闽太祖王审知的侍婢，后受王延钧宠爱。',7,'陈后，本闽太祖侍婢金凤也，陋而淫，闽主嬖之，','陈后承前、金凤为名，闽太祖王审知；陋而淫属于史家评价，展示不当客观容貌或道德定论，不把旧侍婢起年填935。')
E['chen_kin']=ev('min_chen_shouen_kuangsheng_dianshi','王延钧任陈金凤族人陈守恩、陈匡胜为殿使',7,'以其族人','为殿使。',[('闽主','任两殿使者'),('守恩','陈后族人、殿使获任者'),('匡胜','陈后族人、殿使获任者')],place='闽',year=None,when='立陈后段所附初句追叙；任殿使起始年日未载',note='初句所附陈后旧身份及宠爱、任族人的背景，任年未明不硬填935；同族据陈后姓与后续同年主叙姓名补姓陈，具体亲等未明，不造父兄关系。')
relationship('王延钧','陈后','丈夫',7,'闽主立淑妃陈氏为皇后。','闽主与所立皇后婚姻身份，此时陈后是王延钧配偶；A丈夫→B，未反建妻边。')
for name in ['守恩','匡胜']:relationship('陈后',name,'族亲',7,'以其族人守恩、匡胜为殿使。','同族亲属明示，具体亲等、长幼未知，族亲为对称关系，不编父兄子关系。')
claim('event',E['chen'],'description','新闽世家也记王审知之婢金凤姓陈，被王鏻宠爱并立为后。',7,'審知婢金鳳，姓陳氏，鏻嬖之，遂立以為后。','陈金凤姓名及原侍婢身份同句明确；鏻沿已应用王延钧别名，不另建王鏻。',source='xinwudaishi-068-chen-jinfeng',relation='corroborates')
claim('person',people['王延钧'],'biography','新闽世家记王鏻前妻早卒、继室金氏贤而不被礼遇；与主两娶刘氏的表述不同。',7,'鏻妻早卒，繼室金氏賢而不見答。','妻姓及婚次差异保各书，不自动把金氏改为刘氏，也不据本段无法确定具体婚年。',source='xinwudaishi-068-chen-jinfeng',relation='conflicts')
E['zhao']=ev('zhao_yanshou_zhongwu_shumi','三月辛丑赵延寿由宣武节度使任忠武节度使兼枢密使',8,'三月，辛丑，','兼枢密使。',[('赵延寿','前宣武节度使兼侍中、新忠武节度使兼枢密使获任者'),('帝','任命者')],when='935年三月辛丑',place='忠武',note='主前宣武旧前汴州，主忠武旧许州，是军号和治州写法，保原不另造两命。')
claim('event',E['zhao'],'description','旧末帝纪同记三月辛丑以前汴州节度使赵延寿为许州节度使兼枢密使。',8,'辛丑，以前汴州節度使趙延壽為許州節度使兼樞密使；','同日同任职，旧省兼侍中不伪称完全官衔一致。',source='jiuwudaishi-047-935-march',relation='corroborates')
E['yiyin']=ev('li_yiyin_dingnan_formal_appointment','三月任李彝殷为定难节度使',9,'以李彝殷','为定难节度使。',[('彝殷','定难节度使正式获任者'),('帝','任命者')],when='935年三月辛丑条下',place='夏州、定难',note='主承前辛丑条，无另列日；旧同辛丑叙事明确。此命区别二月权知，不直接覆盖临时事件。')
claim('event',E['yiyin'],'description','旧末帝纪在辛丑条记李彝殷由夏州行军司马任本州节度使，因其兄李彝超已卒。',9,'以夏州行軍司馬李彝殷為本州節度使，兄彝超卒故也。','同职任命互核；旧称兄彝超与主前称兄彝殷相反，长幼异说保，不以一书覆盖。',source='jiuwudaishi-047-935-march',relation='corroborates')
claim('event',E['yiyin'],'description','宋夏国传记清泰二年李彝超卒，彝殷继加定难节度使。',9,'初為行軍司馬，清泰二年，彝超卒，遂加定難軍節度使。','印证年及任职前后，无三月日；同人后改彝兴用于检索不前移。',source='songshi-485-li-yiyin-name',relation='corroborates')
E['qian_mother']=ev('qian_yuanguan_mother_jinguo_honour','三月己酉赠钱元瓘母陈氏晋国太夫人',10,'己酉，','为晋国太夫人。',[('陈氏','吴越王钱元瓘母、晋国太夫人获赠者'),('元瓘','获赠者之子、吴越王')],when='935年三月己酉',place='吴越',note='主赠号但未明确下令者，不擅加帝参与或说钱王自行册赠；未列母亲死年，人物death_year不填。不与895年被赐李克用的魏国夫人陈氏合并，限定姓名与母子身份。')
relationship('陈氏','元瓘','母亲',10,'赠吴越王元瓘母陈氏为晋国太夫人。','陈氏为钱元瓘母亲明确；用限定规范名区别其他陈氏，不从同姓推钱镠正妻身份。')
ev('qian_respects_and_rewards_maternal_kin','钱元瓘尊礼母族并厚赐，未因母族关系迁官授重任',10,'元瓘性孝，','授以重任。',[('元瓘','尊礼赐母族而不授重官者')],year=None,when='本段赠号后附记钱元瓘长期待母族的做法；起止年份未载',place='吴越',note='性孝为史家评价；未尝辖迁官及授重任，底本逗号不解成先不升官却授重任。长期做法未具起止，不说935首次开始或编未名母族官员。')
E['an']=ev('an_shenqi_shunhua_appointment','三月壬戌安审琦以彰圣都指挥使领顺化节度使',11,'壬戌，','领顺化节度使。',[('安审琦','彰圣都指挥使、领顺化节度使者'),('帝','任命者')],when='935年三月壬戌',place='顺化',note='领不自动等于赴治州实际到任；旧补富州刺史身份、楚州及军职如故，任命与驻地分别保。')
relationship('金全','安审琦','父亲',11,'审琦，金全之子也。','金全据安氏父名及旧安审琦传明同安北都护振武节度使，与已有人安金全同人；不混李金全。')
claim('event',E['an'],'description','旧末帝纪同记壬戌安审琦领楚州顺化军节度使，彰圣军职如故，并列原富州刺史。',11,'壬戌，以左右彰聖都指揮使、富州刺史安審琦領楚州順化軍節度使，軍職如故。','主省左右、富州、楚州及留军职，独立补充不改变主新职。',source='jiuwudaishi-047-935-march',relation='corroborates')
claim('person',people['安审琦'],'description','旧安审琦传称其字国瑞，其先为沙陀部人。',11,'安審琦，字國瑞，其先沙陀部人也。','已核卷123传首，祖先族属不能自动译成安本人出生于沙陀；不扩录同传晋汉周后事。',source='jiuwudaishi-123-an-shenqi')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','旧安审琦传记其父金全任安北都护、振武军节度使。',11,'父金全，安北都護、振武軍節度使，累贈太師，《唐書》有傳。','父名与旧军职核对已有安金全，不混同期李金全；累赠是身后官衔，不称935年父仍任官。',source='jiuwudaishi-123-an-shenqi',relation='corroborates')
reviews={1:'正月丙申朔闽大赦与改永和分，新同年改元补；不把同段王仁达往事当此日。',2:'二月丙寅朔蜀赦，孟昶主，不推改元。',3:'甲戌范转宣武兼中书令主旧同，旧汴州治州写法，检校太师独补；旧範沿范。',4:'丁丑奏病、彝殷权知、寻卒分；以句下令者未独载，不强定李令代掌或帝诏。死日不等于奏日。主称彝殷兄、旧新宋称弟，暂对称兄弟，原句并列，不合阿啰王；彝兴后改名只检索别名。',5:'戊寅孟尊母与李旧庄宗后宫赐孟追叙分；李母沿旧，不混琼华长公主；籍贯非出生地，旧嬪御互核。',6:'己丑魏追尊，主夫人旧太夫人原别；旧卢等上谥请择日册命，不能将典礼执行日也强己丑。',7:'立陈后、旧两娶刘、陈原侍婢、族人殿使追叙任年未明分；金凤姓陈新明示、闽主王鏻沿王延钧应用别名。美陋淫等为书评非客观定论。主刘与新继金妻姓差异保；族亲不猜具体亲等，两刘不合一。',8:'辛丑赵兼枢密忠武，前宣武与旧汴州、新忠武旧许州军号治州同不造两任。',9:'三月李正式定难与二月权知分，旧称兄彝超不同主兄彝殷；宋同年任职无日、后避讳不前移。',10:'己酉赠陈母号而下令者未载，不加帝参与，不推死年或混魏国陈。待母族长期做法不定起年；未尝辖迁官授任，逗号不导致相反意思。',11:'壬戌安领顺化，旧留军职及楚州富州身份补；父金全从旧传军职核为安金全非李金全；领命非实到，新人物字国瑞先沙陀独补。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(1,12):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=935,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(1,12)],next_paragraph='zztj-v279-y0935-p012',next_volume=279,next_year=935,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='卷279连续935年第1—11正文段，原85—95行；正月闽改元赦、二月蜀赦及唐任免、夏州李家继任、蜀李太后与唐魏追尊、闽陈后族殿使、三月赵李安任官及吴越陈母赠号。935年后26段尚待录入，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(1,12)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
