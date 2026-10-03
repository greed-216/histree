# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 18–25."""
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
 ('tongjian-276-dingzhou-start',YEAR/'part-04/sources/library/tongjian-276-dingzhou-start','db4b82d4','司马光等'),
 ('tongjian-276-late-summer',P/'sources/library/tongjian-276-late-summer','86b40c48','司马光等'),
 ('jiuwudaishi-039-july',P/'sources/library/jiuwudaishi-039-july','86b40c48','薛居正等'),
 ('xinwudaishi-064-maochongwei',P/'sources/library/xinwudaishi-064-maochongwei','86b40c48','欧阳修'),
 ('xinwudaishi-063-wangzongshou-burial',P/'sources/library/xinwudaishi-063-wangzongshou-burial','86b40c48','欧阳修'),
 ('jiuwudaishi-146-yeast-tax',P/'sources/library/jiuwudaishi-146-yeast-tax','86b40c48','薛居正等'),
 ('xinwudaishi-072-hemiao',P/'sources/library/xinwudaishi-072-hemiao','86b40c48','欧阳修'),
 ('jiuwudaishi-064-wangyanqiu-dingzhou',YEAR/'part-04/sources/library/jiuwudaishi-064-wangyanqiu-dingzhou','db4b82d4','薛居正等'),
 ('xinwudaishi-046-wangyanqiu-dingzhou',YEAR/'part-04/sources/library/xinwudaishi-046-wangyanqiu-dingzhou','db4b82d4','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-dingzhou-start','tongjian-276-late-summer']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p018-p025',
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
for n in range(18, 26):
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
    ck = f'claim_zztj_276_0928_05_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','殷':'马殷','德勋':'许德勋','季兴':'高季昌','高季兴':'高季昌','希范':'马希范','从嗣':'高从嗣','匡齐':'廖匡齐','王彦章':'王彦章（吴将）','晏球':'杜晏球','王晏球':'杜晏球','硃弘昭':'朱弘昭','知祥':'孟知祥','重威':'毛重威','衍':'王宗衍','王衍':'王宗衍','惕隐':'赫邈'}
NEW_ALIASES={'高从嗣':['高從嗣'],'廖匡齐':['廖匡齊'],'毛重威':[],'赫邈':['惕隐（赫邈）','惕隱（赫邈）']}

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
    if when is None:when='928年'+('五月末至六月' if n==18 else '六月' if n==19 else '七月')+'本段；确日未载'
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
jul='jiuwudaishi-039-july';mao='xinwudaishi-064-maochongwei';bur='xinwudaishi-063-wangzongshou-burial';tax='jiuwudaishi-146-yeast-tax';he='xinwudaishi-072-hemiao';old='jiuwudaishi-064-wangyanqiu-dingzhou';new='xinwudaishi-046-wangyanqiu-dingzhou'
E=ev('wu_requests_peace_captive_release','吴遣使向楚求和，请归苗璘与王彦章',18,'吴遣使','请苗璘、王彦章；',[('苗璘','吴所请归的被俘将领'),('王彦章','吴所请归的被俘将领')],when='928年五月道人矶战后、六月条前，确日未载',place='吴至楚',note='承前吴将苗璘、吴静江王彦章，王彦章不是后梁同名将；求和请求不等已订各项正式条约。')
E=ev('machu_releases_wu_two_generals','马殷归还苗璘、王彦章，命许德勋饯行',18,'楚王殷','使许德勋饯之。',[('殷','归还俘将并命饯行者'),('德勋','奉命饯行者'),('苗璘','获归的吴将'),('王彦章','获归的吴将')],when='928年五月战后、六月条前，确日未载',place='楚至吴',note='归是释放送归，非两人楚国新任；饯行具体地点未载，不推首都宴场。')
E=ev('xudemun_warns_wu_about_chu_succession','许德勋向两吴将言楚尚有宿将，需待诸子争位方可图谋',18,'德勋谓','然后可图也。”',[('德勋','提出楚内政与军事判断者'),('苗璘','受饯听话者'),('王彦章','受饯听话者')],when='928年俘将获归饯行时，确日未载',place='楚',note='众驹争皁栈是对诸子将争的比喻与预判，不作本年诸子已开继位内战；只是许所言，不录吴已实施攻楚计划。')
E=ev('machu_household_succession_background','史书述马殷内宠多、嫡庶无别、诸子骄奢，解释许德勋话语',18,'时殷多','故德勋语及之。',[('殷','宫内及诸子状况所归者'),('德勋','话语背景所归者')],year=None,when='许德勋饯行话语的家内背景，具体起年未载',place='楚',note='多内宠、嫡庶无别、骄奢为史书评价，不造每一未名母子、诏定继承制度或所有子女行为。')
E=ev('gaojixing_renews_wu_vassal_request','高季兴再次请向吴称藩',18,'六月','复请称籓于吴，',[('季兴','请称藩者')],when='928年六月辛巳',place='荆南至吴',note='复是此前请藩后的本次，不复建前次已录事件；称籓展示称藩原字保留，不等并吞荆南。')
E=ev('wu_raises_gaojixing_qinwang','吴进高季兴爵为秦王',18,'吴进','季兴爵秦王，',[('季兴','受进爵者')],when='928年六月辛巳',place='吴、荆南',note='吴授的爵位不当后唐认可授爵或本人在秦地取得实土。')
E=ev('siyuan_orders_chu_campaign_jingnan','李嗣源诏马殷讨高季兴',18,'帝诏','楚王殷讨之。',[('帝','下诏者'),('殷','奉讨荆南命者'),('季兴','诏讨对象')],when='928年六月辛巳称藩进爵条后，确日未独载',place='后唐朝廷至楚、荆南',note='诏讨与下遣军实际行动分别录，不提前九月房知温总讨荆南任命。')
E=ev('xudemun_maxifan_army_shatou','马殷遣许德勋攻荆南，马希范监军，驻沙头',18,'殷遣','次沙头。',[('殷','遣军者'),('德勋','率兵者'),('希范','马殷之子、监军者')],when='928年六月诏讨荆南后，确日未载',place='沙头',note='其子承马殷，非许德勋之子；次是驻军，不等已克沙头及江陵。')
relationship('殷','希范','父亲',18,span(18,'殷遣','次沙头。'),'马殷是马希范的父亲，按既存同端点同类型复用，不建反向子边。')
E=ev('gaocongsi_challenges_maxifan','高从嗣单骑至楚营，邀马希范单挑决胜',18,'季兴从子','挑战决胜，',[('从嗣','高季兴从子、云猛指挥使、挑战者'),('希范','被邀挑战者')],when='928年六月沙头驻军后，确日未载',place='沙头楚营',note='主从子明确亲属但不具父亲或伯叔长幼，不推从嗣是高季兴亲子；马希范被邀，不等本人已接斗。')
claim('person',people['高从嗣'],'description','高从嗣是高季兴的从子，任云猛指挥使。',18,span(18,'季兴从子','从嗣单骑造楚壁，'),'从子保留原亲属称谓，未明父亲与伯叔长幼，不造具体父子边。')
E=ev('liaokuangqi_kills_gaocongsi_duel','副指挥使廖匡齐出战，将高从嗣击杀',18,'副指挥使','拉杀之。',[('匡齐','副指挥使、出斗杀敌者'),('从嗣','决斗被杀者')],when='928年六月沙头挑战后，确日未载',place='沙头楚营',note='拉杀仅据原述击杀，不编武器招式；死者是从嗣，非希范或季兴。')
B['people'][next(i for i,r in enumerate(B['people']) if r['key']==people['高从嗣'])]['death_year']=928
claim('person',people['高从嗣'],'death_year','928年六月条记高从嗣决斗被杀。',18,span(18,'季兴从子','拉杀之。'),'死者承从嗣，本年依据主六月条，日未具。')
E=ev('gaojixing_peace_xudemun_returns','高季兴惧，次日请和，许德勋还军',18,'季兴惧','德勋还。',[('季兴','请和者'),('德勋','还军者')],when='928年六月从嗣被杀次日请和，确日未载',place='荆南、楚',note='明日相对从嗣决斗；德勋还未独有日，不把全军返回精确归同日，不推荆南已灭。')
person('匡齐',18,'赣人、副指挥使',Q[18]['text'])
claim('person',people['廖匡齐'],'description','廖匡齐为赣人。',18,'匡齐，赣人也。','史载地域名称保留，未核现代县界及出生坐标。')
E=ev('wangyanqiu_cautions_dingzhou_attack','王晏球知定州守备，认为不易急攻',19,'王晏球知','未易急攻，',[('晏球','作攻城判断者')],when='928年六月乙未攻城前，确日未载',place='定州',note='军事判断有备不等王投降；不把知道城防当自身畏怯客观事实。')
E=ev('zhuhongzhao_zhangqianzhao_accuse_timidity','朱弘昭、张虔钊宣称大将畏怯',19,'硃弘昭','宣言大将畏怯，',[('硃弘昭','宣言者'),('张虔钊','宣言者')],when='928年六月攻城前，确日未载',place='定州行营',note='畏怯是二人宣言，不当史实认定王晏球怯战。旧宏昭与主弘昭同事同人，未加疑字为正式别名。')
claim('event',E,'description','旧明宗纪称朱宏昭、张虔钊急于立功而促攻。',19,'時晏球知城中有備，未欲急攻，朱宏昭、張虔釗切於立功，促攻賊壘，','切于立功为旧纪补叙动机，朱宏昭按同案复用朱弘昭，不靠自动繁简改宏为弘。',source=jul)
E=ev('court_forces_immediate_dingzhou_assault','朝廷诏令催促攻定州城',19,'有诏','攻城。',[],when='928年六月乙未攻城前，确日未载',place='定州',note='按原未直接记皇帝现场，诏命不造无名使者主体。')
E=ev('forced_dingzhou_assault_three_thousand_losses','王晏球被迫攻定州，杀伤将士三千人',19,'晏球不得已',None,[('晏球','奉诏攻城军统领')],when='928年六月乙未',place='定州',note='主杀伤三千为死伤合数概录，不能写阵亡三千；未述攻克，不能将关城战改主城已陷。')
claim('event',E,'time_original','旧明宗纪在七月甲寅记王晏球奏六月二十二日攻逆城。',19,'甲寅，王晏球奏，六月二十二日進攻逆城，將士傷者三千人。','甲寅奏报与六月二十二行动日分列；主六月乙未原纪时保留，不将七月奏日误作攻城日。',source=jul)
claim('event',E,'description','旧明宗纪称将士伤者三千，及伤痍者众。',19,'甲寅，王晏球奏，六月二十二日進攻逆城，將士傷者三千人。時晏球知城中有備，未欲急攻，朱宏昭、張虔釗切於立功，促攻賊壘，晏球不得已而進兵，遂致傷痍者眾。','旧伤痍叙法与主杀伤数量分类不同，原全句伤者三千另有引用，不合成确定阵亡数。',source=jul,relation='conflicts')
E=ev('maochongwei_sent_three_thousand_kuizhou','朝廷命西川兵戍夔州，孟知祥遣毛重威领三千人赴戍',20,'先是','三千人往。',[('知祥','奉诏遣军者'),('重威','左肃边指挥使、领三千人赴戍者')],year=None,when='先是追叙发兵戍夔州，确年日未独载',place='西川至夔州',note='先是不得直接赋六月；毛重威新主体非杜重威或米重威，三千为所率非后逃军死亡数。')
claim('event',E,'description','新孟蜀世家记唐伐荆南，诏孟知祥兵下峡，遣毛重威三千戍夔州。',20,'是歲，唐師伐荊南，詔知祥以兵下峽，知祥遣毛重威率兵三千戍夔州。','是岁承上一段三年，前段另存上下文；本条只补下峡军务，不强主先是为某月某日。',source=mao)
E=ev('mengzhixiang_requests_recall_kuizhou_garrison','孟知祥称夔忠万三州已平，请召回戍军以省运输',20,'顷之','以省馈运。”',[('知祥','请求撤戍者')],year=None,when='发兵夔州顷之，确年日未独载',place='夔州、忠州、万州至朝廷',note='三州已平是孟奏述，不以此条虚构本次三州征服战与完成日。')
claim('event',E,'description','新孟蜀世家将请撤戍军叙在高季兴死、其子从诲请命之后。',20,'已而荊南高季興死，其子從誨請命，知祥請罷戍兵，不許。','与主此处前列次序不同保留，不能把季兴死亡提前六月；此条为撤戍背景异说，未新建高死重复事件。',source=mao,relation='conflicts')
E=ev('siyuan_refuses_recall_kuizhou_troops','李嗣源不许召回夔州戍兵',20,'帝不许。','帝不许。',[('帝','拒准撤戍者')],year=None,when='孟知祥奏请召还后，确年日未独载',place='后唐朝廷至西川、夔州',note='未许为决定，不造此前另一不许及确日。')
E=ev('mengzhixiang_secretly_induces_garrison_return','孟知祥暗中派人诱导戍军返归',20,'知祥阴','使人诱之，',[('知祥','暗遣诱导者')],year=None,when='撤戍请奏不许之后，确年日未独载',place='西川至夔州',note='使人未具名不虚构使者及详具体言辞。')
E=ev('maochongwei_noisy_garrison_desertion','毛重威率众鼓噪逃回',20,'重威帅','鼓噪逃归。',[('重威','领军逃归者')],year=None,when='孟知祥暗遣诱导后，确年日未独载',place='夔州至西川',note='逃归为实动，非奉准罢兵；不推全部三千精准无损回返。')
claim('event',E,'description','新孟蜀世家同记孟知祥暗示毛重威率军鼓噪溃归。',20,'知祥諷重威以兵鼓譟，潰而歸，','鼓噪、溃归分别保留主述，不由此建立毛是孟亲属。',source=mao,relation='corroborates')
E=ev('siyuan_orders_maochongwei_case_investigation','李嗣源命追究毛重威罪责',20,'帝命','按其罪，',[('帝','命追究者'),('重威','被追究者')],year=None,when='戍兵逃归后，确年日未独载',place='后唐朝廷、西川',note='按罪是查追命令，不等已定罪处刑。')
E=ev('mengzhixiang_secures_maochongwei_exemption','孟知祥请求，毛重威获免追究',20,'知祥请','而免之。',[('知祥','请免者'),('重威','获免者')],year=None,when='命按罪后，确年日未独载',place='西川、后唐朝廷',note='免之依主承毛罪，不新猜赏赐或改官。')
claim('event',E,'description','新孟蜀世家称唐诏劾毛重威，孟知祥奏请不劾，由此唐大臣愈认为孟必反。',20,'唐以詔書劾重威，知祥奏請無劾，由是唐大臣益以知祥為必反。','必反是唐大臣的判断，不能当孟此时已经正式称帝或已自承叛乱。',source=mao)
E=ev('wangzongshou_requests_wangyan_burial','陕州行军司马王宗寿请葬故蜀主王衍',21,'陕州','请葬故蜀主王衍，',[('王宗寿','陕州行军司马、请葬者'),('衍','被请安葬的故蜀主')],year=None,when='七月乙巳追封以前的请葬，确日未载',place='陕州至后唐朝廷',note='王衍沿前蜀王宗衍主体，故主已死，不重建926遇害；请葬未独明日，不强追封当日。')
E=ev('wangyan_posthumous_shunzhenggong','朝廷追赠故蜀主王衍顺正公',21,'秋，七月','赠衍顺正公，',[('衍','被追赠顺正公者')],when='928年七月乙巳',place='后唐朝廷',note='追封是死后爵，不当本人在世再封；主赠、旧追封叙法相合。')
claim('event',E,'description','旧明宗纪同记七月乙巳追封故蜀主王衍为顺正公、以诸侯礼葬。',21,'秋七月乙巳，詔故偽蜀主王衍追封順正公，以諸侯禮葬。','同事同日，旧伪字为史家称述，不写作人物规范名。',source=jul,relation='corroborates')
claim('event',E,'time_original','新前蜀世家记天成二年王宗寿上书请葬，获保义行军司马职并封衍顺正公。',21,'天成二年，出詣京師，上書求衍宗族葬之。明宗嘉其忠，以為保義軍行軍司馬，封衍順正公，許以諸侯禮葬之。','新记天成二年与主旧帝纪天成三年并列，未覆盖主年份；保义陕州同治军州不造第二个王宗寿。',source=bur,relation='conflicts')
E=ev('wangyan_princely_burial_authorized','朝廷定王衍按诸侯礼安葬',21,'赠衍','以诸侯礼葬之。',[('衍','诸侯礼安葬对象')],when='928年七月乙巳追封条，具体下葬日未独载',place='后唐朝廷',note='旧诏、新许礼葬支持礼制准许，未将乙巳必定等实葬日；墓地据新补而非主凭空补地图。')
claim('event',E,'description','新史补王宗寿收王氏十八具丧柩，葬于长安南三赵村。',21,'宗壽得王氏十八喪，葬之長安南三趙村。','新葬地与丧数独立补充，承其天成二年叙法，与主旧三年不强统一实际葬日；十八丧非十八新名死者。',source=bur)
E=ev('anshentong_dies_campaign','北面招讨使安审通去世',22,'北面',None,[('安审通','去世的北面军将')],when='928年七月本段；确日未独载',place='北面行营',note='主北面招讨沿已任副招讨身份，未另造取消副字的升任事件；死未写战死或病名。')
claim('event',E,'description','旧明宗纪记安审通卒于师，七月丁未朝廷为之停朝。',22,'丁未，以滄州節度使安審通卒於師輟朝。','丁未是辍朝记事日，不必等去世日；沧州与横海沿已存身份，本句只明卒于师而非具体战死原因。',source=jul)
E=ev('kongxun_executes_private_yeast_household','东都留守孔循因民犯私曲禁，诛其一家',23,'东都民','留守孔循族之。',[('孔循','东都留守、族诛执行者')],year=None,when='七月己未弛曲禁之前，确日未载',place='东都洛阳',note='罪犯未具姓名及全族人数，不推具体几人；曲是酿酒用曲，私麹原字保留非私酒税商品现代解释。')
claim('event',E,'description','旧食货志记孔循以曲法杀一家于洛阳，之后有人献弛禁之议。',23,'時孔循以麴法殺一家於洛陽，或獻此議，以為愛其人，便於國，故行之。','杀一家补地域和立法背景，后政策不等追回死者或撤销原判。',source=tax,relation='corroborates')
E=ev('proposal_liberalize_yeast_five_coins_tax','有人请许民造曲，秋税每亩收五钱',23,'或请','秋税亩收五钱；',[],when='928年七月己未敕准之前，确日未载',place='后唐',note='建议者未具名不猜宰相；每亩五钱是耕田税附征，不是每斤曲售价。')
E=ev('siyuan_allows_private_yeast_autumn_tax','朝廷敕准民自造曲，按秋田每亩纳五钱',23,'己未',None,[],when='928年七月己未',place='后唐',note='只记主书政策，不能推所有售酒行为免税或全废酒榷。')
claim('event',E,'description','旧明宗纪同记七月己未弛曲禁，许民自造，秋苗纳曲价每亩五钱。',23,'己未，詔弛曲禁，許民間自造，於秋苗上納征曲價，畝出五錢。','秋苗税征收，与量曲价非直接商品价格；旧曲/食货麴/主麹不同字保留底本。',source=jul,relation='corroborates')
claim('event',E,'description','旧食货志细载自天成三年七月后乡村田亩纳曲钱五文足陌，许民自造供家，随夏秋征纳。',23,'唐天成三年七月，詔曰：「應三京、鄴都、諸道州府鄉村人戶，自今年七月後，於是秋田苗上，每畝納麴錢五文足陌，一任百姓自造私麴，醞酒供家，其錢隨夏秋徵納。','补诏书适用范围、币制原词与收取方式，不换成人民币或以足陌推所有地方计数统一。',source=tax)
E=event('yeast_edict_commercial_household_two_tenths','旧食货志记原买官曲酒户可自造售酒，按上年买曲钱十分取二征榷',23,'其京都及諸道州府縣鎮坊界內，應逐年買官麴酒戶，便許自造麴，醞酒貨賣。仍取天成二年正月至年終一年逐戶計算都買麴錢數內，十分只納二分，以充榷酒錢，便從今年七月後，管數徵納。',[],source=tax,when='928年七月弛曲禁诏，七月后征纳',place='三京及诸道州府县镇坊界',note='二分基数为天成二年官曲钱，不是销售收入20%或税率两分钱；允许货卖限此类酒户，不能推广所有人自由售酒。')
E=event('yeast_edict_other_households_sale_limits','旧食货志记其他人可自造供家，不许私卖；违者按中等酒户纳榷，坊村沽卖另列例外',23,'榷酒戶外，其餘諸色人亦許私造酒麴供家，即不得衷私賣酒，如有故違，便即糾察，勒依中等酒戶納榷。其坊村一任沽賣，不在納榷之限。」',[],source=tax,when='928年七月弛曲禁诏',place='后唐；坊村例外原文范围待考',note='坊村与前坊界范围细义留纸本校核，不自行改衷私为私酿或把例外等全国城市免税。')
E=ev('hemiao_seven_thousand_relief_dingzhou','契丹又遣酋长惕隐领七千骑援定州',24,'壬戌','将七千骑救定州，',[('惕隐','本次契丹援军统领')],when='928年七月壬戌条，出兵确日未独载',place='契丹至定州',note='惕隐是史载官称，本次据新四夷附录相同行动识别赫邈，不将所有惕隐官任自动同人；不同于秃馁先前援军。')
claim('person',people['赫邈'],'description','新四夷附录将本次七千骑援定州的惕隐记名赫邈。',24,'德光又遣惕隱赫邈益禿餒以騎七千，晏球又敗之于唐河。','按同一援军数、对象与唐河战逐项识别，官名惕隐不作所有时代人物通用别名，不猜姓氏。',source=he)
claim('event',E,'description','旧王晏球传称惕隐所率勇骑五千至唐河。',24,'俄而契丹首領惕隱率勇騎五千至唐河。','主新七千、旧王传五千并列，不能用不同统计改定其中一本底文。',source=old,relation='conflicts')
claim('event',E,'description','新王晏球传称惕隐七千骑增援王都。',24,'契丹又遣惕隱以七千騎益都，','与主同数印证，但益是增援不是万骑再加七千后总兵力精算。',source=new,relation='corroborates')
E=ev('tanghe_wangyanqiu_defeats_relief_army','王晏球在唐河北迎战，大败契丹援军',24,'王晏球逆','大破之；',[('晏球','迎击胜军统领'),('惕隐','援军统领、受败者')],when='928年七月壬戌',place='唐河北',note='唐河北是唐河之北，非泛河北省，不补现代坐标。')
claim('event',E,'time_original','旧明宗纪七月甲子载王晏球奏本月十九日契丹七千骑援定州，并在唐河北击败。',24,'甲子，王晏球奏，今月十九日契丹七千騎來援定州，王師逆戰於唐河北，大破之。','甲子是奏报日，十九是来援记时；后夹通鉴注与主直接相依，不作为第二独立确证。',source=jul)
E=event('tanghe_pursuit_mancheng_report','旧明宗纪补唐河胜后追至满城，再败援军，斩二千级、获马千匹',24,'追至滿城，又破之，斬二千級，獲馬千匹。',[('晏球','所奏追击军统领')],source=jul,when='928年七月甲子奏报所叙唐河后追击，确日未独载',place='满城',note='二千级为此追击所记，非整次七千都死；马匹不等获俘人数，不与易州泛数合加。')
claim('event',E,'description','新王晏球传同记唐河战后追至满城，斩首二千、获马千匹。',24,'晏球遇之唐河，追擊至滿城，斬首二千級，獲馬千匹。','只印证该阶段，不将主易州与满城当同地点。',source=new,relation='corroborates')
E=ev('yizhou_pursuit_flood_losses','唐军追契丹至易州，久雨水涨，俘斩与陷溺死者不可胜数',24,'甲子',None,[('晏球','率追击军者'),('惕隐','被追的援军统领')],when='928年七月甲子',place='易州',note='不可胜数为史载概述，俘、斩、溺不同类别不合成确数死亡；未提前八月被赵擒。')
claim('event',E,'time_original','旧明宗纪七月己巳记王晏球奏本月二十一日追契丹至易州，掩杀四十里、擒获甚众。',24,'己巳，王晏球奏，此月二十一日，追契丹至易州，掩殺四十里，擒獲甚眾。','己巳奏报与二十一追击日分别保留，四十里战段叙述不精确定位尸体区域。',source=jul)
claim('event',E,'description','旧王传记大雨追至易州河涨，陷没并俘获二千骑而还。',24,'是時大雨，晏球出師逆戰，惕隱復敗，追至易州，河水暴漲，所在陷沒，俘獲二千騎而還。','旧俘二千是此段俘获数，不能等于主不可胜数总损或前满城斩二千同类数。',source=old)
E=ev('wangyanjun_prince_min','北威武节度使王延钧受封闽王',25,'戊辰',None,[('王延钧','闽王获封者')],when='928年七月戊辰',place='闽、后唐朝廷',note='进封为后唐爵号，不当本日首次称帝或改元，北威武与福建既存军号主体复用。')
claim('event',E,'description','旧明宗纪同日诏福建节度使王延钧依前检校太师守中书令，进封闽王。',25,'戊辰，詔福建節度使王延鈞可依前檢校太師、守中書令，進封閩王。','福建节度称军治州差异保留，依前诸衔不另建新授任。',source=jul,relation='corroborates')
review='卷276连续928年第18—25段逐句校核。吴求和返苗璘吴王彦章、饯行许判断、马内宠诸子背景分事；返俘不等楚任、吴将区别梁将，诸子争只是预判。六月辛巳高再请吴藩、秦王、唐诏楚讨、许军马希范监驻沙头、高从嗣独挑战、廖击杀、次日请和军归分别；其子承马殷，复用父亲边；高从嗣是季兴从子不具父名伯叔长幼，不补父子。廖赣人不配现代出生坐标。六月乙未攻城有备判断与朱张畏怯宣言分，旧宏昭同人但非自动繁简别名；三千主杀伤与旧伤者分类不强阵亡，旧七月甲寅奏六月二十二行动区分。毛戍先是及顷之与后续追叙年null，主夔忠万已平是孟奏，新列高死从诲请命后的撤戍背景与主次序不同并列，不提前高死；新是岁承前段三年另存上下文。王宗寿请葬、七月乙巳王宗衍死后顺正公、诸侯礼分事；新天成二年与主旧三年并列，十八丧三赵村补但不强实际葬日同诏日。安主称招讨不造另升官，旧七月丁未辍朝与卒于师非确定死亡日，不猜病战死。孔循私曲族诛起日未明null，或请未具人，己未弛禁五钱每亩非曲商品价；旧食货补原官曲户上年曲钱十取二非营业收入20%及其他家造供用、禁卖、坊村例外按范围保留不推全国免税。七月壬戌契丹惕隐七千援、唐河北战、满城补、甲子易州分；本次官称据新四夷名赫邈不将所有惕隐人物合并，旧王传五千异数；旧甲子奏十九、己巳奏二十一与主行军纪时区别。满城斩二千马千与易州俘二千不同分类，久雨俘斩溺不可胜数不精总死亡或提前八月擒。旧夹通鉴注不独证。戊辰王延钧闽爵与未来称帝分，不造新福建同名人。展示简体、原字及定位保留底本；纸本异文待核。'
context_dir=P/'sources/library/xinwudaishi-064-year-context'
context_rec=json.loads((context_dir/'paragraph.json').read_text())
contexts=[dict(file=os.path.relpath(context_dir/'source.txt',P/'sources'),sha256=hashlib.sha256((context_dir/'source.txt').read_bytes()).hexdigest(),paragraph_id=context_rec['id'],citation=context_rec['citation'],url='https://github.com/greed-216/histree/blob/86b40c48/'+str((context_dir/'source.txt').relative_to(ROOT)),purpose='新孟蜀世家是岁承前文三年；仅存上下文定位，不将整段未读史事提前新增。')]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(18,26):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(18,26)],next_paragraph='zztj-v276-y0928-p026',next_volume=276,next_year=928,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续928年第18—25段、原文件50—57行；楚吴议和、楚荆南战、定州攻城及契丹后援、毛戍撤兵、王衍葬礼、曲税改革、封闽王。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(18,26)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
