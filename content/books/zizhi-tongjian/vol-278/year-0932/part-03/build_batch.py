# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 278, year 932 paragraphs 21–28."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 29))
specs=[]
for directory in sorted((P/'sources/library').iterdir()):
 specs.append((directory.name,directory,'747dcc12','司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '欧阳修'))
PREV=YEAR/'part-02'
specs += [(key,PREV/'sources/library'/key,'01575dcc',author) for key,author in [('tongjian-278-932-october','司马光等'),('jiuwudaishi-043-932-november','薛居正等')]]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-278-932-october']
B = {'format_version': 1, 'batch_key': 'zztj-v278-y0932-p021-p028',
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
lines = (ROOT / 'resources/derived/tongjian/278.txt').read_text().splitlines()
for n in range(21, 29):
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
        citation = f'卷278·长兴三年（932）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_278_0932_03_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'上':'李嗣源','帝':'李嗣源','敬瑭':'石敬瑭','延光':'范延光','延寿':'赵延寿','义诚':'康义诚','硃弘昭':'朱弘昭','徐知诰':'李昪','知诰':'李昪','汉主':'刘岩','知远':'刘知远'}
Sons=[('耀枢','耀樞','雍正','邕王'),('龟图','龜圖','康王','康王'),('弘度','洪度','宾王','秦王'),('弘熙','洪熙','晋王','晉王'),('弘昌','洪昌','越王','越王'),('弘弼','洪弼','齐王','齊王'),('弘雅','洪雅','韶王','韶王'),('弘泽','洪澤','镇王','鎮王'),('弘操','洪操','万王','萬王'),('弘杲','洪杲','循王','循王'),('弘暐','洪暐','思王','息王'),('弘邈','洪邈','高王','高王'),('弘简','洪簡','同王','同王'),('弘建','洪建','益王','益王'),('弘济','洪濟','辩王','辨王'),('弘道','洪道','贵王','貴王'),('弘昭','洪昭','宜王','宣王'),('弘政','洪政','通王','通王'),('弘益','洪益','定王','定王')]
NEW_ALIASES={'张敬达':['張敬達','张志通','生铁'],'张彦超':['張彥超'],'周瑰':[]}
for name,other,_,_ in Sons:
 NEW_ALIASES['刘'+name]=list(dict.fromkeys(['劉'+name,'刘'+other,'劉'+other]))

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

def event(code, title, n, quote, actors, when=None, note='', year=932, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='932年十一月承前本段；确日未独载' if n<=26 else '932年十二月本段；确日未独载'
    key = 'event_zztj_278_0932_' + code
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
        edge = 'participation_zztj_278_0932_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_278_0932_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
# Consecutive ten body paragraphs in the next volume of the same year.
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
nov='jiuwudaishi-043-932-november';dec='jiuwudaishi-043-932-december';jing='jiuwudaishi-070-zhang-jingda';newjing='xinwudaishi-033-zhang-jingda';earlyjing='jiuwudaishi-041-930-jingda';yanchao='jiuwudaishi-129-zhang-yanchao';zhou='jiuwudaishi-095-zhou-gui';sons='xinwudaishi-065-liu-sons';liu='xinwudaishi-065-liu-yan-name'
ev('hedong_final_debate','十一月乙酉李嗣源催定河东帅，李崧坚持用石敬瑭，群臣终从其议',21,'乙酉，','众乃从崧议。',[('上','因北边受逼催议并遣中使者'),('敬瑭','愿赴河东的候选者'),('延光','本次欲用康、又称曾荐石者'),('延寿','本次欲用康者'),('康义诚','本次群议候选者'),('李崧','枢密直学士、坚持用石者')],when='932年十一月乙酉',place='后唐朝廷',note='主在本次分歧与范自言此前累奏用石均保，不能省成范从未荐石或李崧独任免；帝欲留宿卫为范所言，非独核帝心思。')
E=ev('shi_hedong_final_appointment','十一月丁亥石敬瑭正式任北京留守、河东节度使及四军蕃汉马步总管，兼侍中',21,'丁亥，',None,[('上','授任者'),('敬瑭','获河东及四军总管任命者')],when='932年十一月丁亥',place='北京、河东及大同等军',note='北京为后唐北都非现代北京市，未核坐标；大同振武彰国威塞四军逐名留，不提前割燕云。与此前初命仍兼副使争议分阶段。')
claim('event',E,'description','旧明宗纪同丁亥记石敬瑭任河东节度及四军蕃汉马步总管。',21,'丁亥，以河陽節度使兼六軍諸衛副使石敬瑭為河東節度使，兼大同、彰國、振武、威塞等軍蕃漢馬步總管。','旧列四军次序不同不造两次授任，主北京留守兼侍中与旧六军副使前职细节各保。',source=nov,relation='corroborates')
E=ev('zhaoyanshou_chancellor','十一月己丑赵延寿加同平章事',22,'己丑，',None,[('上','加官者'),('延寿','枢密使、加同平章事者')],when='932年十一月己丑',place='后唐朝廷')
claim('event',E,'description','旧明宗纪同己丑记枢密使赵延寿加同平章事。',22,'己丑，樞密使趙延壽加同平章事。','主旧同平章事对应同任，未猜实授职权扩大程度。',source=nov,relation='corroborates')
E=ev('xu_new_titles_desheng','吴授徐知诰大丞相、太师，并加领德胜节度使',23,'吴以诸道都统','加领德胜节度使；',[('徐知诰','诸道都统、被加授官者')],place='吴、德胜军',note='主体沿李昪，不以徐知诰新造；本句授与后半受辞未定分，不能据授就认已接受所有衔。')
claim('event',E,'description','通鉴底本后半作“知诰矢丞相、太师”，辞受动作字待核。',23,'知诰矢丞相、太师。','矢不是繁简字形转换；未获选定二十四史同事明文，不强改为辞或受，不建肯定受辞事件。此句已读而待异文校核，未漏读。',relation='adds')
E=ev('jingda_blocks_khitan','大同节度使张敬达聚兵要害，契丹未能南下而退',24,'大同节度使', '契丹竟不敢南下而还。',[('张敬达','大同节度使、聚兵防边者')],place='大同军边地要害',note='竟不敢为史述结果归因，不推歼灭数量、战场现代坐标；不自动指定未名契丹将帅。')
claim('event',E,'description','旧张传记敬达聚兵塞下，使契丹未能南牧。',24,'敬達每聚兵塞下，以遏其衝。契丹竟不敢南牧，邊人賴之。','旧传将其放在四年迁云州后，主932本段，旧本纪930庚午已记应州移云州；叙层不同保留，不将旧传四年强改主年。旧后清泰及夹注契丹国志不提前新增。',source=jing,relation='corroborates')
claim('person',people['张敬达'],'description','张敬达为代州人，字志通，小字生铁。',24,'張敬達字志通，代州人也，小字生鐵。','新身份补主籍贯；字与小字为别名不造另一人。后徙各镇泛叙不借以复建所有未定年任命。',source=newjing,relation='adds')
claim('person',people['张敬达'],'description','旧明宗纪930年十月庚午记张敬达由应州移云州。',24,'庚午，應州節度使張敬達移雲州，','用既有930卷年上下文核任职层次；本条作当前身份补证及传纪差异说明，不在932造930转任新事件，也不凭三年四年传记覆本纪。',source=earlyjing,relation='adds')
claim('person',people['张敬达'],'description','旧张传记张敬达字志通、代州人、小字生铁，与新史相同。',24,'張敬達，字志通，代州人，小字生鐵。','仅取可核身份，新旧互参不算完全独立确认。',source=jing,relation='corroborates')
E=ev('yanchao_submits_weizhou','张彦超闻石敬瑭为总管，举蔚州城归契丹',25,'蔚州刺史张彦超','举城附于契丹，',[('张彦超','蔚州刺史、举城归契丹者'),('敬瑭','新任总管、被述与张有隙者')],place='蔚州',note='与石有隙为主叙背景，不凭同场建立仇敌永久边；举城投附不等石发令使其降。')
claim('event',E,'description','旧张传亦记素与晋高祖不协，其总戎太原时张举城投契丹。',25,'素與晉高祖不協，屬其總戎於太原，遂舉其城投於契丹，','晋高祖为回称石敬瑭，不把此时写成936已建后晋；其后南侵入汴等未来事未提前。',source=yanchao,relation='corroborates')
E=ev('yanchao_khitan_datong','契丹授张彦超大同节度使',25,'契丹以为大同节度使。',None,[('张彦超','投附后获契丹授大同者')],place='契丹所授大同军',note='主大同与旧云州军治称对应，此为契丹授职，不说已击败并接收张敬达控制全部军境。')
claim('event',E,'description','旧张传称投契丹后即任云州节度使。',25,'即以為雲州節度使。','主大同军、旧云州称分别留，不静改主地名。',source=yanchao,relation='corroborates')
claim('person',people['张彦超'],'description','张彦超本沙陀部人，曾为李嗣源养子。',25,'張彥超，本沙陀部人也。','族属明确，不以李氏养父给本人改姓；不把跛子贬称作本站姓名。养父关系另有主旧明文。',source=yanchao,relation='corroborates')
relationship('上','张彦超','养父',25,'尝为帝养子','帝为当卷明宗李嗣源；李嗣源→张彦超养父，不当生父，收养日期未载。')
rel=B['person_relationships'][-1]['key'];claim('person_relationship',rel,'description','李嗣源曾收张彦超为养子。',25,'明宗嘗以為養子。','旧明确明宗补主帝称；尝追叙不定932收养。',source=yanchao,relation='corroborates')
ev('shi_arrives_jinyang','石敬瑭抵达晋阳，任刘知远、周瑰为都押衙',26,'石敬瑭至晋阳，','委以心腹；',[('敬瑭','到晋阳后任部将者'),('知远','部将、获都押衙者'),('周瑰','部将、获都押衙者')],place='晋阳',note='到任与朝廷丁亥授任分，到日未独载；心腹为史述信任，不造不随时间变化的盟友边。')
ev('shi_assigns_military_treasury','石敬瑭将军事交刘知远、帑藏交周瑰',26,'军事委知远，','帑藏委瑰。',[('敬瑭','分委军政与府藏者'),('知远','获委军事者'),('周瑰','获委帑藏者')],place='晋阳',note='军事、帑藏分别保留，不把二人都写成掌全部三司或中央财政；后936任权判三司不提前。')
claim('person',people['周瑰'],'description','周瑰为晋阳人，旧传称善书计，石敬瑭历镇时委其帑廪出纳。',26,'周瑰，晉陽人也。少端厚，善書計，自高祖時歷鎮藩翰，用為腹心，累職至牙門都校，凡帑廩出納，咸以委瑰，','旧历镇与十余年属回顾不定每次年，此取身份及任事背景，不把他日称高祖理解此时已称帝；未来937遇害未提前。',source=zhou,relation='adds')
E=ev('kang_heyang_guard_commander','十二月戊午康义诚任河阳节度使，兼侍卫亲军马步都指挥使',27,'十二月，戊午，','兼侍卫亲军马步都指挥使；',[('上','正式授职者'),('康义诚','受河阳及侍卫军职者')],when='932年十二月戊午',place='河阳及后唐侍卫亲军')
claim('event',E,'description','旧明宗纪同戊午记康义诚河阳节度兼侍卫亲军马步军都指挥使。',27,'康義誠為河陽節度使，充侍衛親軍馬步軍都指揮使。','与主同日同人同职，不重复。',source=dec,relation='corroborates')
E=ev('zhu_shannan_regular_appointment','十二月戊午朱弘昭正式任山南东道节度使',27,'以硃弘昭',None,[('上','正式授职者'),('硃弘昭','从暂知转正式节度任命者')],when='932年十二月戊午',place='山南东道',note='与前朱知山南、代康入阙的临时阶段分，不重叠为两次同日任命。硃/朱及旧宏/主弘沿同人。')
claim('event',E,'description','旧明宗纪同戊午记前宣徽使朱宏昭任襄州节度使。',27,'戊午，以前宣徽使朱宏昭為襄州節度使；','襄州为山南东道军治称，朱宏昭沿已建朱弘昭；不是另一位宏昭。',source=dec,relation='corroborates')
# Main and supplementary lists preserve differences, including the PUA placeholder.
familyquote=span(28,'是岁，','弘益为定王；')
father=person('汉主',28,'南汉君主、十九子受封的父亲',familyquote)
claim('person',father,'aliases','刘岩亦名刘龑；新史记其初名岩。',28,'龑，初名巖，謙庶子也。','巖与岩为字形匹配；已建南汉刘岩沿同一key，不重复新建刘龑。此只取姓名，不据同段异闻建出生神迹。',source=liu,relation='adds')
for i,(name,other,title,newtitle) in enumerate(Sons,1):
 pname='刘'+name; rawname='弘\ue449' if name=='弘暐' else name
 # first phrase differs syntactically from the subsequent list.
 q=('汉主立其子'+rawname+'为'+title) if i==1 else rawname+'为'+title
 display='邕王（据新史；主底本作雍正待核）' if i==1 else title
 E=event('liuhan_son_'+str(i).zfill(2),f'南汉刘岩封{pname}为{display}',28,q,[('汉主','授王爵的父亲'),(pname,'获封王爵之子')],when='通鉴932年是岁；确月日未载',year=932,place='南汉',note='南汉十九子按原顺序逐人分录，不把爵名当人名。主弘后缺字按新对应洪暐补核；弘/洪分组异文非繁简规则，姓名沿主弘系但新形式登记别名。各子生年、生母与长幼未独不猜。')
 nq=('封子'+other+newtitle) if i==1 else other+newtitle
 claim('event',E,'description',f'新南汉世家五年名单记{pname}封{newtitle.translate(str.maketrans({"晉":"晋","齊":"齐","鎮":"镇","萬":"万","貴":"贵"}))}。',28,nq,'新五年承大有纪年，对应主932；弘/洪及封号异说并列。主耀枢雍正疑字，新邕王；弘度主宾后秦、新五年直秦；弘暐主思新息；弘济主辩新辨；弘昭主宜新宣，不能静改原文或拆成不同儿子。',source=sons,relation='adds' if title!=newtitle else 'corroborates')
 relationship('汉主',pname,'父亲',28,familyquote,'刘岩→'+pname+'父亲，主其子及新封子全名单明示；未推母亲和其他手足长幼。')
ev('liuhan_hongdu_transferred_qin','南汉刘弘度受封后不久改封秦王',28,'未几，',None,[('汉主','改封之父'),('刘弘度','改封秦王者')],when='未几，932年封子后不久；具体发生年未独载',year=None,place='南汉',note='未几不强定932；新五年直接列秦王与主先宾再秦为记事层次差异，分列，不回写为两个弘度。')
reviews={21:'十一月乙酉催议与丁亥终任分。范前荐石和本次欲康、自言累荐石均留，李崧意见不当独任免；北京为后唐北都非现代北京，旧六军副使前职补；四军未画界或提前燕云割地。',22:'己丑赵延寿加同平章与旧同平章事同日互核，不造第二任。',23:'吴加大丞相太师领德胜明确，后知诰矢字不是繁简，受辞未确定，保留待核不建肯定辞事件；身份李昪复用。',24:'张敬达聚兵与契丹回退，主代州、新字志通小字生铁补。旧传三年应州四年云州与旧本纪930应州移云州、主932大同任层次差异并列，不强定每聚兵各年或套后936危局；旧夹注契丹国志不新增。',25:'张彦超本沙陀、帝养子与旧明宗互核，养父李嗣源不是生父，收养确年未知。投附蔚州与契丹授大同分，旧云州军治称补，未等已夺张敬达全部管区或提前947入汴。',26:'石抵晋阳任两都押衙、分军及帑藏明确，周瑰晋阳籍与旧善书计财任补。旧十余年追叙不推起年、未来936权三司937被害不提前；心腹不建永久盟边。',27:'十二月戊午康河阳侍卫、朱山南正任分别，同旧康职与襄州军治互核；朱前暂知不当已正授，宏弘硃朱沿已有稳定人。',28:'十九子逐人受爵及父亲边；主汉主映刘岩、新龑初巖姓名补，不猜母与生日。弘/洪和爵名不同并列，主缺字按新对应洪暐补但原保。耀枢主雍正新邕王、弘度宾后秦新直秦、弘暐思息、弘济辩辨、弘昭宜宣均留；未几徙秦yearnull，不强定932。新五年承大有需上下文确认，正文49段完成后才全年核验，分隔及933标题非正文。'}
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,29):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
context=P/'sources/context/liuhan-dayou-era/source.txt'
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=278,year=932,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(21,29)],next_paragraph='zztj-v278-y0933-p001',next_volume=278,next_year=933,supplements=supplements,source_contexts=[dict(file=os.path.relpath(context,P/'sources'),sha256=hashlib.sha256(context.read_bytes()).hexdigest(),note='新卷65前大有改元回查，五年为大有五年；本段战事不新增。')],excluded_non_body=[dict(source_line=34,text='◎',reason='年际分隔'),dict(source_line=35,text=lines[34],reason='933年标题')],coverage='卷278连续932年最后第21—28段、原26—33行；河东终议授职、吴加官、防边与蔚州投附、晋阳军财任事、十二月康朱正式任、南汉十九子封爵及改秦。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(21,29)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
