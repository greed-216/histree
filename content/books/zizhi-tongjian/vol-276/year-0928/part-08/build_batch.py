# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 928, paragraphs 41–47."""
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
 ('tongjian-276-year-end',P/'sources/library/tongjian-276-year-end','38a68a4c','司马光等'),
 ('jiuwudaishi-064-huoyanwei',P/'sources/library/jiuwudaishi-064-huoyanwei','38a68a4c','薛居正等'),
 ('xinwudaishi-007-liconghou',P/'sources/library/xinwudaishi-007-liconghou','38a68a4c','欧阳修'),
 ('xinwudaishi-043-kongxun-marriage',YEAR/'part-02/sources/library/xinwudaishi-043-kongxun-marriage','f890926e','欧阳修'),
 ('jiuwudaishi-039-november',YEAR/'part-07/sources/library/jiuwudaishi-039-november','72e54c9a','薛居正等'),
 ('jiuwudaishi-064-wangyanqiu-dingzhou',YEAR/'part-04/sources/library/jiuwudaishi-064-wangyanqiu-dingzhou','db4b82d4','薛居正等'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-late-summer','tongjian-276-year-end']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0928-p041-p047',
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
for n in range(41, 48):
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
    ck = f'claim_zztj_276_0928_08_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','上':'李嗣源','晏球':'杜晏球','王晏球':'杜晏球','王宴球':'杜晏球','都':'王都','哀帝':'李祚','从厚':'李从厚','循':'孔循','重诲':'安重诲','王德妃':'王德妃（李嗣源妃）','继麟':'朱友谦','崇韬':'郭崇韬'}
NEW_ALIASES={'王雅':[],'孔氏（李从厚妃）':['孔氏（李從厚妃）'],'霍承训':['霍承訓'],'霍彦珂':['霍彥珂']}

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

def event(code, title, n, quote, actors, when=None, note='', year=928, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='928年'+('十月' if n==41 else '十一月')+'本段；确日未载'
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
# -*- coding: utf-8 -*-
huo='jiuwudaishi-064-huoyanwei';ann='jiuwudaishi-039-november';wang='jiuwudaishi-064-wangyanqiu-dingzhou';kong='xinwudaishi-043-kongxun-marriage';hou='xinwudaishi-007-liconghou'
E=ev('wangdu_defence_failed_inside_plots','王都固守定州，严密伺察；诸将谋翻城响应官军而未成',41,'王都','皆不果。',[('都','定州守城及严察者')],place='定州',note='谋翻城未成不是已经献城；诸将无名，不猜开门者或后来马让能参与本次密谋。')
E=ev('emperor_urges_wangyanqiu_attack','李嗣源遣使催促王晏球攻定州',41,'帝遣','攻城，',[('帝','遣使督攻者'),('晏球','被催攻城者')],place='定州',note='王宴球为本段疑似讹写，沿王晏球／杜晏球同人，不新增正式别名；催攻非已破城。')
E=ev('wangyanqiu_inspects_explains_high_walls','王晏球与使者并骑巡城，解释城高梯冲难及，强攻徒伤精兵',41,'晏球与','如此何为！',[('晏球','巡城并解释攻城困难者')],place='定州城下',note='借使是设想，不是王都真实允许官军登城；精兵徒死为对强攻后果的判断，不编本日伤亡数。')
E=ev('wangyanqiu_proposes_taxes_wait_inner_collapse','王晏球建议用三州租税，爱民养兵，等待定州内部溃败',41,'不若','彼必内溃。”',[('晏球','建议围待者')],place='定州城下',note='必内溃是预期，不能写为928年城陷；三州未明名，不推税州边界或总额。')
claim('event',E,'description','旧王晏球传同记城坚，建议食三州租税、抚民养军，等待敌军自行溃败。',41,'晏球圍城既久，帝遣使督攻城，晏球曰：「賊壘堅峻，但食三州租稅，撫恤黎民，愛養軍士彼自當魚潰。」帝然其言。','旧传生平段无本行动确月，十月从主书连续段定位；旧主策略互证，预期不提前929城破。',source=wang,relation='corroborates')
E=ev('emperor_accepts_dingzhou_waiting','李嗣源同意王晏球围城待变的建议',41,'帝从之。',None,[('帝','批准待变建议者')],place='定州军务',note='之承王晏球建议，批准非亲赴定州。')
E=ev('officials_propose_aidi_temple','有司请求为唐哀帝立庙',42,'十一月','位庙，',[],place='后唐朝廷',note='位庙原字保留，整理按下文立庙理解，字形待核；有司未具名不臆造官员。')
E=ev('edict_aidi_temple_caozhou','朝廷诏在曹州为唐哀帝立庙',42,'诏','曹州。',[('哀帝','奉诏立庙的唐哀帝')],place='曹州',note='哀帝沿李祚主体，不另建李柷；立庙是诏令，未具建成时点，不能写作当日竣工。')
E=ev('huoyanwei_dies','平卢节度使霍彦威去世',43,'平卢',None,[('霍彦威','平卢节度使、去世者')],place='平卢任所',note='晋忠武公为追赠爵谥，不当此前已有在世授爵；主十一月承段，旧列传三年冬与帝纪十一月相互定位，确卒日未载。')
claim('event',E,'description','旧霍传称天成三年冬卒于任所，年五十七。',43,'三年冬，卒於理所，年五十七。','卒龄照录，不倒推出确定出生公元年；三年承本段天成初、明年、三年次序。',source=huo,relation='corroborates')
claim('event',E,'time_original','旧明宗纪十一月载青州奏霍彦威卒、朝廷辍朝三日。',43,'青州奏，節度使霍彥威卒，輟朝三日。','奏报时间与卒日区分，前己丑中书奏项不能不加证据直接当实际卒日。',source=ann,relation='corroborates')
E=event('emperor_mourns_huoyanwei','李嗣源近郊闻霍彦威讣告，掩泣归宫',43,'奏至之日，明宗方出近郊。忽聞奏訃，掩泣歸宮，',[('帝','闻讣归宫悼念者')],source=huo,when='928年冬，霍彦威讣奏到达之日；确干支未载',place='后唐近郊至宫',note='由卒年冬承续反应，奏到日不强等实际死亡日。')
E=event('court_suspends_sessions_music_for_huo','朝廷为霍彦威辍朝三日，至月末不奏乐',43,'輟朝三日，至月終不舉樂。',[],source=huo,when='928年冬讣报后，辍朝三日、至该月终不举乐',place='后唐朝廷',note='月终承讣报月，未推停乐必整月或具体乐队；主十一月、旧纪同月停朝交核。')
E=event('huoyanwei_posthumous_titles','旧霍传记追赠霍彦威太师、晋国公，谥忠武',43,'冊贈太師、晉國公，諡曰忠武。',[('霍彦威','获追赠爵谥者')],source=huo,year=None,when='霍彦威928年卒后追赠；本句未独立给出年月',place='后唐朝廷',note='旁注天成四年六月敕葬为另事，不用它给本句追赠强定日期；未新增引用专史，纸本待核。')
q='子承訓，弟彥珂，累曆刺史。'
relationship('霍彦威','霍承训','父亲',43,q,'霍传所列子承训，父亲方向霍彦威→霍承训；史载各历刺史不补任职年月与地名。',source=huo)
relationship('霍彦威','霍彦珂','兄长',43,q,'霍传明弟彦珂，兄长方向霍彦威→霍彦珂，不再新增反向弟弟边。',source=huo)
E=ev('wangya_takes_guizhou','忠州刺史王雅取归州',44,'忠州',None,[('王雅','忠州刺史、取归州者')],place='归州',note='王雅本次新主体，未查到二十四史独立同案补证；与西方邺此前攻归州分段分行为，不猜中间再失守经过或现代坐标。')
E=ev('liconghou_marries_kong_daughter','李从厚纳孔循之女为妃',45,'庚寅','为妃，',[('从厚','纳妃者'),('孔氏（李从厚妃）','孔循之女、李从厚妃')],when='928年十一月庚寅',place='大梁',note='与此前议婚获准区分，本段始记实际纳妃；孔女无个人名，以限定名识别，不与其他孔氏合并。')
relationship('孔循','孔氏（李从厚妃）','父亲',45,'皇子从厚纳孔循女为妃，','原文明父孔循，父亲方向孔循→孔氏；不据其生父反推生日。')
relationship('从厚','孔氏（李从厚妃）','丈夫',45,'皇子从厚纳孔循女为妃，','实际婚配明确，丈夫方向李从厚→孔氏，不再重复反向妻子边。')
claim('event',E,'description','新愍帝纪称李从厚妃为孔循之女。',45,'從厚妃，孔循女也，','补身份，不用整段缩写把十一月婚嫁当此前二月罢孔循枢密的直接新因果。',source=hou,relation='corroborates')
claim('event',E,'description','新孔循传记明宗以李从厚娶孔循之女。',45,'明宗即以宋王從厚娶循女。','宋王为后来封爵回称，新愍纪长兴元年始封宋王，928本次不另建封宋王事件。',source=kong,relation='corroborates')
E=ev('kongxun_arrives_daliang_marriage','孔循借女儿成婚得至大梁',45,'循因','大梁，',[('循','借婚至大梁者')],when='928年十一月庚寅婚事期间',place='大梁',note='得之大梁疑叠字，依上下句理解得赴大梁，底本不改；并非孔循取得大梁领土。')
E=ev('kongxun_courts_wangdefei_party_asks_stay','孔循厚结王德妃之党，请求留在大梁',45,'厚结','乞留。',[('循','结党求留者')],when='928年十一月婚事期间',place='大梁',note='厚结主语承孔循，厚不是李从厚姓名截断；王德妃党无名，不造某个党人或正式联盟关系。')
claim('event',E,'description','本段的王德妃沿用李嗣源妃王德妃主体。',45,'厚结王德妃之党，','按当前后唐宫廷婚事定位，区别吴太后王氏；只识别党名，不推王本人在场或参与请求。')
E=ev('anzhonghui_reports_opposes_kongxun','安重诲上奏孔循求留之事，极力排拒',45,'安重诲','力排之，',[('重诲','具奏排拒者'),('循','被排拒求留者')],when='928年十一月婚事期间',place='后唐朝廷',note='之承孔循求留案，不能把礼毕归镇对象理解为新妃或李从厚。')
E=ev('kongxun_urged_return_after_marriage','婚礼结束后，孔循被催促返回藩镇',45,'礼毕',None,[('循','礼毕被催归镇者')],when='928年十一月婚礼毕后',place='大梁至孔循任镇',note='原促令是催命，不独立证明立即已经抵镇；未按新传跨年外任概述指定本日全部改职。')
E=event('wangjianli_interim_qingzhou','旧明宗纪补朝廷诏王建立暂掌青州军州事',46,'詔宰臣王建立權知青州軍州事。',[('王建立','权知青州军州事者')],source=ann,when='928年十一月霍彦威讣报后、甲午正式任命前；确日未独载',place='青州',note='权知临时与甲午平卢正式任命分开，不据前己丑项强确定本条独日。')
E=ev('wangjianli_pinglu_jiedushi','王建立以同平章事充平卢节度使',46,'甲午',None,[('王建立','平卢节度使获任者')],when='928年十一月甲午',place='平卢、青州',note='原仍带同平章事荣衔，不能概括为所有平章称号被剥夺；主原中书侍郎与旧仆射并列保留。')
claim('event',E,'description','旧明宗纪同日记王建立为青州节度使、检校太尉、同平章事，原衔为尚书左仆射等。',46,'甲午，以尚書左僕射、同平章事、集賢殿大學士、判三司王建立為青州節度使、檢校太尉、同平章事。','青州为平卢治州；主原中书侍郎与旧原尚书左仆射衔有异，不改底本，未再造第二同人。',source=ann,relation='conflicts')
E=ev('emperor_zhaofeng_iron_certificate_question','李嗣源询问赐铁券之意，赵凤答为立誓使子孙长享爵禄',47,'丙申','爵禄耳。”',[('上','询问赐铁券之意者'),('赵凤','解释铁券誓意者')],when='928年十一月丙申',place='后唐朝廷',note='赵凤对制度誓意的解释，不据此承诺所有后裔事实上永远免死或爵禄必不失。')
E=ev('emperor_recalls_three_iron_certificate_recipients','李嗣源回忆先朝三名铁券受赐者中郭崇韬、李继麟族灭，自身仅幸免，并久叹',47,'上曰','因叹息久之。',[('上','回忆先朝及自身危境者'),('崇韬','帝言回忆的已族灭受赐者'),('继麟','帝言回忆的已族灭受赐者')],when='928年十一月丙申谈论既往',place='后唐朝廷',note='让三人疑字由旧同案三受赐者补明，不改原话；郭朱是帝回忆对象，不当在场，族灭为先朝前事不重造928新死亡。')
claim('event',E,'description','旧明宗纪同日明列李嗣源、郭崇韬、李继麟三名先朝铁券受赐者。',47,'先朝所賜，惟朕與郭崇韜、李繼麟三人爾，崇韜、繼麟尋已族滅，朕之危疑，慮在旦夕。','李继麟沿朱友谦同人；主险脱毫厘与旧危疑旦夕话语分别保留，不把回忆改为928三人新受券事件。',source=ann,relation='corroborates')
E=ev('zhaofeng_good_faith_above_inscribed_metal','赵凤认为帝王心存大信，便不必刻之金石',47,'赵凤曰：“帝王心存',None,[('赵凤','发表守信意见者')],when='928年十一月丙申问答末',place='后唐朝廷',note='对话中的意见，不当已废铁券制度的正式诏令。')
review='卷276连续928年第41—47段、原73—79行。定州严守与诸将谋翻未果；帝催攻、王巡城论梯冲、建议三州租税爱民养兵待内溃及帝准分动作。王宴球疑字沿杜晏球主体不添正式别名，城溃是预测不提前929克。哀帝沿李祚，有司请与诏曹立庙分，位庙原字待核，诏非竣工。霍彦威卒主十一旧三年冬，奏日非卒日；旧57龄不倒生年，掩泣返宫、辍朝三日至月终无乐分别，追赠年null，旁注929葬敕不定追赠日，晋忠武公后谥回称。旧补子霍承训、弟霍彦珂，父与兄方向明确，不建反向重复。王雅忠州取归州无独立二十四史同案补证，分此前西方邺动作不猜中间得失。十一庚寅从厚实际纳孔女与此前议准分，新孔新愍补身份；孔氏限名、孔父、李丈夫边清楚。厚结主语孔循不误从厚，得之大梁疑字保存，王德妃沿明宗妃不混吴太后。安具奏排、礼毕促孔归镇分，催归非已抵镇。新传婚罢压缩不同纪时并列，不用十一婚解释早二月罢，新宋王后爵不提前928授。旧王建立权青与甲午正任平卢分，主中书侍郎旧左仆射异衔并列，仍同平章荣衔不称全罢。丙申铁券问答分，赵说为誓意非法律实际永远免死；主让三疑字由旧三名补，李继麟朱友谦同人，郭朱皆追忆对象非在场，族灭非928新死，帝险脱与旧危疑不同话语保留。赵存信不必刻为意见非已废制。展示简体，摘录及快照保留原字；纸本异文待核，未处理快照内后续段不算完成。'
contexts=[]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,48):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=928,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(41,48)],next_paragraph='zztj-v276-y0928-p048',next_volume=276,next_year=928,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷276连续928年第41—47段、原文件73—79行；定州待变、曹州哀帝庙令、霍彦威卒与追赠、王雅取归、孔氏婚及孔循求留、王建立任青、铁券问答。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(41,48)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
