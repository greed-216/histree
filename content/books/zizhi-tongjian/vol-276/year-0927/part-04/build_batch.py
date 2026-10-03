# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 276, year 927, paragraphs 14–18."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 26))
specs=[
 ('tongjian-276-july-opening',YEAR/'part-01/sources/library/tongjian-276-july-opening','e38f4580','司马光等'),
 ('tongjian-276-late-927-opening',P/'sources/library/tongjian-276-late-927-opening','e00f3e22','司马光等'),
 ('xinwudaishi-061-wu-accession',P/'sources/library/xinwudaishi-061-wu-accession','755ad621','欧阳修'),
 ('jiuwudaishi-092-zhangjun-inquiry',P/'sources/library/jiuwudaishi-092-zhangjun-inquiry','755ad621','薛居正等'),
 ('jiuwudaishi-038-late-october',P/'sources/library/jiuwudaishi-038-late-october','755ad621','薛居正等'),
 ('jiuwudaishi-134-xuwen-family',P/'sources/library/jiuwudaishi-134-xuwen-family','755ad621','薛居正等'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-276-july-opening','tongjian-276-late-927-opening']
B = {'format_version': 1, 'batch_key': 'zztj-v276-y0927-p014-p018',
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
        citation = f'卷276·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_276_0927_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'知诰':'李昪','知询':'徐知询','陈夫人':'陈夫人（徐温家属）','苻彦琳':'符彦琳','吴王':'杨溥','吴主':'杨溥','孙晨':'孙晟','徐知诰':'李昪','硃守殷':'朱守殷','李彦超':'符彦超','李鐸':'李铎','楚王殷':'马殷','王晏球':'杜晏球','帝':'李嗣源','仁赞':'孟昶','琼华':'琼华长公主','李从严':'李继曮','楚王殷':'马殷','高季兴':'高季昌'}
NEW_ALIASES={'陈夫人（徐温家属）':[],'符彦琳':['符彥琳']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷276天成二年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='927年十月本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_276_0927_' + code
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
        edge = 'participation_zztj_276_0927_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_276_0927_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
wu='xinwudaishi-061-wu-accession';zhang='jiuwudaishi-092-zhangjun-inquiry';old='jiuwudaishi-038-late-october'
E=ev('xuwen_dies','吴大丞相徐温去世',14,'辛丑','徐温卒。',[('徐温','吴大丞相、东海王、去世者')],when='927年十月辛丑',place='吴，卒地本句未载',note='本句官衔概录，大丞相都督中外诸军事诸道都统镇海宁国节度使中书令东海王皆为卒时衔，未据此新建七次任命。')
claim('event',E,'description','新吴世家记大丞相徐温率文武劝进，杨溥未许而徐温病卒。',14,'七年，大丞相徐溫率吳文、武上表勸溥即皇帝位，溥未許而溫病卒。','新记病卒和劝进未许先后，未具死亡日；主辛丑据主，不补现代疾病诊断。',source=wu,relation='adds')
relationship('徐温','知询','父亲',14,'初，温子行军司马、忠义节度使、同平章事知询以其兄知诰非徐氏子，','温子知询明确，复用既有父亲key，区分918已死知训。')
relationship('徐温','知诰','养父',14,'李昪，本海州人。偽吳大丞相徐溫之養子也。','旧正文明确养父关系，与主非徐氏子及家中养之相合，沿已有养父key不改原叙述。',source='jiuwudaishi-134-xuwen-family')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','旧传述李昪幼时被徐温掳得并育为己子，与既有新史杨行密转交徐温的养育经过不同。',14,'昪時幼稚，為溫所擄，溫愛其慧黠，遂育為己子，名曰知誥。','养父关系一致，养育经过异说并存，不覆盖先前新史来源或重造收养事件。',source='jiuwudaishi-134-xuwen-family',relation='conflicts')
relationship('知诰','知询','兄长',14,'知询以其兄知诰非徐氏子，','明确其兄与非徐氏子，养家中的长幼关系，不作同父亲生兄弟。')
B['person_relationships'][-1]['description']='李昪是徐知询养家中的兄长，非徐氏亲生子。'
E=ev('xuzhixun_repeatedly_requests_replace_libian','徐知询以徐知诰非徐氏子为由，多次请求取代其执掌吴政',14,'初，温子','执吴政，',[('知询','行军司马、忠义节度使、请求代政者'),('知诰','拟被替代者')],year=None,when='徐温死前追叙，反复请求确年日未载',place='吴',note='多次请求不是已成功交权；非徐氏子是养育身份，不据此否定养父关系。')
E=ev('xuwen_refuses_sons_replace_libian','徐温称诸子皆不及徐知诰，未同意换人',14,'温曰','汝曹皆不如也。”',[('徐温','评价并拒更换者'),('知询','被比较者')],year=None,when='徐温死前追叙，确年日未载',place='吴',note='皆不如为徐温的评价，不作为能力客观排名。')
E=ev('yankeqiu_xujie_recommend_xuzhixun','严可求、徐玠屡劝徐温以徐知询取代徐知诰',14,'严可求','不忍也。',[('严可求','劝换人者'),('徐玠','行军副使、劝换人者'),('徐温','不忍更换者'),('知询','被推荐者'),('知诰','拟被替代者')],year=None,when='徐温死前追叙，确年日未载',place='吴',note='孝谨、不忍为主书所述判断，不推已有正式任命或建议者亲属结盟关系。')
E=ev('chen_pleads_keep_adopted_libian','陈夫人以贫贱时养育徐知诰为由，反对富贵后弃之',14,'陈夫人曰','奈何富贵而弃之！”',[('陈夫人','徐温家中陈夫人、护养育者'),('知诰','被维护者')],year=None,when='徐温死前追叙，确年日未载',place='吴徐氏家中',note='我家养之为本人话语；此句未明妻子或养母称谓，限定人物但不建妻母关系。')
E=ev('xuwen_plans_wu_emperor_petition','徐温拟率诸藩镇入朝，劝吴王称帝',14,'可求等言之不已','将行，',[('徐温','拟率藩镇入朝劝进者')],year=None,when='徐温死前，原文欲、将行；确年日未载',place='吴藩镇至吴王朝廷',note='欲将行为计划，未录徐温本人已完成入朝。')
E=ev('xuwen_ill_sends_son_petition','徐温因病改遣徐知询奉表劝进，并计划留其取代徐知诰执政',14,'有疾','因留代知诰执政。',[('徐温','病中遣子者'),('知询','奉表劝进者、拟留执政'),('知诰','拟被替代者')],when='927年十月徐温卒前，遣子确日未载',place='吴',note='遣子为实际安排，留代为此行所拟；下一句赴洪草表和闻丧折返说明未据此断言知询已实际接掌广陵吴政。')
E=ev('libian_drafts_hongzhou_request','徐知诰草拟求任洪州节度使的表，准备次晨上奏',14,'知诰草表','俟旦上之，',[('知诰','拟外任、草表者')],when='927年十月徐温死讯到达当夕之前',place='吴',note='欲求且俟旦为草拟未提交，不建已获洪州节授或已离职。')
E=ev('libian_stops_request_after_xuwen_news','当晚徐温死讯传到，徐知诰停止上奏外任请求',14,'是夕','乃止。',[('知诰','停止求外任者'),('徐温','死讯所指者')],when='927年十月，死讯传到当夕；接讯确日未载',place='吴',note='接讯日不直接等于辛丑死亡日。')
E=ev('xuzhixun_returns_jinling','徐知询闻丧后急归金陵',14,'知询亟','归金陵。',[('知询','急归者')],when='927年十月闻徐温死讯后，确日未载',place='金陵',note='从后文父卒背景录闻丧返，不凭此句推新节度任命已经取得。')
E=ev('xuwen_posthumous_qiwang_zhongwu','吴主追赠徐温齐王，谥忠武',14,'吴主赠',None,[('吴主','追赠者'),('徐温','被追赠者')],when='927年十月徐温死后，赠谥确日未载',place='吴',note='东海王卒时衔、齐王追赠区别，未提前后续徐温追帝。')
E=ev('zhangjun_ill_refuses_officers','张筠久病，拒绝将佐求见',15,'山南西道','不许。',[('张筠','山南西道节度使、拒见者')],year=None,when='927年十月改任前久疾背景，确年日未载',place='山南西道、兴元',note='久疾不作现代病诊断，拒见不等死亡。')
E=ev('fuyanlin_requests_temporary_seals','副使符彦琳等怀疑张筠已死及左右有谋，请暂交符印',15,'副使','请权交符印；',[('苻彦琳','副使、求见后请暂交印者')],when='927年十月本段；确日未载',place='兴元',note='主苻与旧符同副使同案识符彦琳，疑字不注册正式别名；疑死奸谋是下属怀疑，不作为已死或已证阴谋。')
claim('event',E,'description','旧张筠传称副使符彦琳等面请问疾，未获见，故疑死、请权交牌印。',15,'副使符彥琳等面請問疾，筠又不諾，彥琳等疑其已死，慮左右有謀，遂請權交牌印，','同名同职同动作补证，符印/牌印原文名词并存。',source=zhang,relation='corroborates')
E=ev('zhangjun_imprisons_officers_false_revolt','张筠将符彦琳及判官都指挥使下狱，诬以谋反',15,'筠怒','诬以谋反。',[('张筠','下狱诬告者'),('苻彦琳','被拘副使')],place='兴元',note='按主诬以谋反，不当定罪；判官与都指挥使未具名，不虚构人物或确定标点人数。')
E=ev('court_summons_inquires_releases_fuyanlin','朝廷召符彦琳等到阙查问，查无实据而释放',15,'诏取','释之；',[('帝','召问释放所归者'),('苻彦琳','被召查问后释放者')],place='兴元至后唐朝廷',note='按之无状为主查问结果，不当已有判决原卷；地点据旧至洛補主诣阙，未具审案官姓名。')
claim('event',E,'description','旧张传记诏取符彦琳等至洛，释而不问。',15,'詔取彥琳等至洛，釋而不問，','主按之无状、旧释而不问叙法有别，并列不硬等完整司法审判程序。',source=zhang,relation='adds')
E=ev('zhangjun_western_capital_resident','张筠调任西都留守',15,'徙筠',None,[('张筠','西都留守获授者')],when='927年十月，主未具日；旧纪辛丑条后记',place='西都、长安',note='任命与以后到长安被拒不混；未提前录928回朝任职。')
claim('event',E,'description','旧明宗纪在辛丑诏后称张筠任西京留守、行京兆尹。',15,'以山南西道節度使張筠為西京留守，行京兆尹。','补京兆尹衔，旧句在辛丑项内但未另具日，未强主本句明确辛丑。',source=old,relation='adds')
claim('event',E,'description','旧张传称授西京留守是为诱其离兴元。',15,'因授筠西京留守，誘離興元。','诱离为旧传所述朝廷动机，不作为已到任或后续被拒同日证明。',source=zhang,relation='adds')
E=ev('shijingtang_xuanwu_guard_command','石敬瑭由保义节度使转宣武节度使，兼侍卫亲军马步都指挥使',16,'癸卯',None,[('石敬瑭','宣武节度使及亲军马步都指挥使获任者')],when='927年十月癸卯',place='保义至宣武、汴州',note='任官异于前批京水受派亲兵跟进，不重复作同一军事行动。')
claim('event',E,'description','旧明宗纪同日称石敬瑭由权知汴州、陕州节度使任汴州节度使、兼六军诸卫副使及亲军马步都指挥使。',16,'癸卯，以權知汴州事、陝州節度使石敬瑭為汴州節度使、兼六軍諸衛副使、侍衛親軍馬步都指揮使。','军名与州名是职衔记法差别，同一任命补六军诸卫副使，未强推所有兼职已罢。',source=old,relation='adds')
E=ev('yangpu_emperor_accession','吴王杨溥即皇帝位',17,'十一月','即皇帝位，',[('吴王','吴皇帝即位者')],when='927年十一月庚戌',place='吴',note='即位与其后甲子改元大赦分阶段。')
claim('event',E,'description','新吴世家同记杨溥十一月庚戌御文明殿即帝位。',17,'十一月庚戌，溥御文明殿即皇帝位，','补殿名，不新增具体殿址坐标。',source=wu,relation='corroborates')
for code,name,title,start,end,supp in [
 ('yangxingmi_posthumous_wuhuangdi','杨行密','武皇帝','追尊孝武王','武皇帝，','追尊行密武皇帝，'),
 ('yangwo_posthumous_jinghuangdi','杨渥','景皇帝','景王曰','景皇帝，','渥景皇帝，'),
 ('yanglongyan_posthumous_xuanhuangdi','杨隆演','宣皇帝','宣王曰','宣皇帝。','隆演宣皇帝。')
]:
 E=ev(code,'杨溥追尊'+name+'为'+title,17,start,end,[(name,'追尊为'+title+'者')],when='927年十一月庚戌即位段',place='吴',note='死后追尊不当本人新登位，也不重造死亡。')
 claim('event',E,'description','新吴世家明确追尊对象'+name+'、称号'+title+'。',17,supp,'补王号所指主体，沿全站key。',source=wu,relation='corroborates')
E=event('libian_wu_taiwei_shizhong','新吴世家记徐知诰获授太尉兼侍中',17,'以徐知誥為太尉兼侍中，',[('知诰','太尉兼侍中获授者')],source=wu,when='927年十一月吴即位段概叙，确日未另具',place='吴',note='新独補此衔，未把下一段加都督中外诸军事任命提前复制；不强同庚戌。')
E=event('xuzhixun_jinling_fuguo','新吴世家记徐知询任辅国大将军、金陵尹，治徐温旧镇',17,'拜溫子知詢輔國大將軍、金陵尹，治溫舊鎮。',[('知询','辅国大将军、金陵尹、旧镇获任者')],source=wu,when='927年十一月吴即位段概叙，确日未另具',place='金陵',note='金陵旧镇任官不等已在广陵替代徐知诰；下一段诸道副都统等衔待连录，不提前合为已处理。')
E=ev('anzhonghui_proposes_wu_attack','安重诲建议攻吴',17,'安重诲议','伐吴，',[('安重诲','提议攻吴者')],when='927年十一月吴称帝后本段，确日未载',place='后唐朝廷',note='议为提案，不作已经出兵。')
E=ev('siyuan_rejects_wu_attack','李嗣源未接受安重诲攻吴建议',17,'安重诲议',None,[('帝','不从攻吴议者'),('安重诲','建议未获接受者')],when='927年十一月本段，确日未载',place='后唐朝廷',note='不从此议不推永不交战的长期承诺。')
E=ev('wu_general_amnesty_qianzhen','吴宣布大赦',18,'甲子','吴大赦，',[('吴主','吴大赦所归者')],when='927年十一月甲子',place='吴',note='主未列赦罪范围，不虚构所有囚犯全部已释。')
claim('event',E,'description','新吴世家在即位条概叙改元、大赦境内。',18,'改元曰乾貞，大赦境內，','新将赦改元合于即位事项，不具甲子；主明甲子，新未明另日，不直接判异日。',source=wu,relation='adds')
E=ev('wu_changes_era_qianzhen','吴改元乾贞',18,'甲子',None,[('吴主','改元所归者')],when='927年十一月甲子',place='吴',note='改元命令日按主，前段庚戌即位不直接等改元日；原贞繁体新貞保持摘录。')
review='连续14—18段逐句校核。徐温卒辛丑官衔保留不造七任；新病卒但未具日不现代病诊断。父徐至知询、养父徐至李复用已存key；旧徐擄育与既有新杨行密转交养育经过异说存证。主其兄知诰非徐氏子明确养家长幼，新兄长说明非亲生，知询区别918知训。多次代政请求、徐温评价、严徐推荐、陈话语、拟率入朝都是前事追叙null；陈限定徐家语境但未明妻养母不建此边。徐病改遣子劝进实际安排，留代为拟，不强交权完成；李草求洪州未交未任，死讯阻止，接讯日不等卒日；知询急归不先授新职；齐王忠武是追赠非卒时东海衔或后帝追尊。张久病拒见、副疑死奸谋请交符印、拘诬、朝召问释及徙官分阶段。主苻/旧符同副同案识符，苻疑字不正式别名；疑死非已死、诬反非定罪，判官都指挥使匿名不定标点人数；主按无状/旧释不问不同叙法不强完整审判卷。张西都衔旧补京兆尹、诱离动机，任命不同928到长安被拒回朝。石癸卯主军名与旧州名、权知/正式同官，补六军诸卫副不重前京水遣军。吴庚戌登位殿名新补，追杨行密渥隆演分别死后帝号；新太尉侍中李、辅国金陵尹知询本段补授确日未另具，不提前下一段丙子官衔。安议攻、帝不从分提案与未采纳，不造战争。甲子赦改元两事，新合即位概叙不当明确同庚戌，不虚构赦范围。原字引用简体展示，纸本及异文待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(14,19):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=276,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(14,19)],next_paragraph='zztj-v276-y0927-p019',next_volume=276,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷276连续14—18段、原文件19—23行；徐温卒和继任争议、张筠案、石任官与吴即帝。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(14,19)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
