# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 275, year 927, paragraphs 25–32."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 33))
specs=[
 ('jiuwudaishi-038-june-offices',P/'sources/library/jiuwudaishi-038-june-offices','0c15026c','薛居正等'),
 ('jiuwudaishi-038-july-reconquest',P/'sources/library/jiuwudaishi-038-july-reconquest','0c15026c','薛居正等'),
 ('jiuwudaishi-067-renhuan-vouchers',P/'sources/library/jiuwudaishi-067-renhuan-vouchers','0c15026c','薛居正等'),
 ('tongjian-275-chengdu-and-jingnan',YEAR/'part-04/sources/library/tongjian-275-chengdu-and-jingnan','69768554','司马光等'),
 ('jiuwudaishi-038-min-withdrawal',YEAR/'part-05/sources/library/jiuwudaishi-038-min-withdrawal','4b8f7b80','薛居正等'),
 ('xinwudaishi-006-927-opening',YEAR/'part-01/sources/library/xinwudaishi-006-927-opening','d50fed5c','欧阳修'),
]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-275-chengdu-and-jingnan']
B = {'format_version': 1, 'batch_key': 'zztj-v275-y0927-p025-p032',
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
lines = (ROOT / 'resources/derived/tongjian/275.txt').read_text().splitlines()
for n in range(25, 33):
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
        citation = f'卷275·天成二年（927）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_275_0927_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李嗣源','仁赞':'孟昶','琼华':'琼华长公主','李从严':'李继曮','楚王殷':'马殷','高季兴':'高季昌'}
NEW_ALIASES={'史光宪':['史光憲'],'孟鹄':['孟鵠'],'温辇':['溫輦']}
def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=None,description=f'《资治通鉴》卷275天成二年条所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when='927年五月至六月本段；确日未载', note='', year=927, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_275_0927_' + code
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
        edge = 'participation_zztj_275_0927_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_275_0927_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)
E=ev('ma_yin_shiguangxian_tribute','马殷遣中军使史光宪向后唐入贡',25,'楚王殷遣','入贡，',[('楚王殷','遣使入贡者'),('史光宪','中军使、贡使')],place='楚至后唐朝廷')
E=ev('shiguangxian_reward_horses_women','李嗣源赐骏马十匹、美女二人，由楚贡使携经江陵',25,'帝赐','美女二。',[('帝','赐物者'),('史光宪','楚贡使、赐物经江陵所涉者')],place='后唐朝廷',note='底本明确数量，赐之指代不强定史光宪个人受益；女子无姓名不虚构个体或婚姻关系。')
E=ev('gao_detains_chu_envoy_seizes_gifts','高季兴在江陵扣留史光宪并夺取赏赐',25,'过江陵','夺之，',[('高季兴','扣使夺物者'),('史光宪','被扣贡使')],place='江陵')
E=ev('gao_requests_wu_submission','高季兴请求举镇归附吴',25,'且请','自附于吴。',[('高季兴','请求归附者')],place='荆南至吴',note='请求不等吴已受臣或已册秦王；不提前后续接受与册封。')
E=ev('xuwen_explains_difficult_rescue','徐温以救援荆南困难为由，主张务实效而去虚名',25,'徐温曰','能无愧乎！”',[('徐温','提出政策理由者')],place='吴',note='此为徐温所陈形势及政策意见；唐袭、吴难救均假设，不建立实际战争事件。')
E=ev('wu_accepts_gifts_refuses_gao_vassalage','吴接受高季兴贡物，拒绝其称臣，允许其归附唐',25,'乃受',None,[('徐温','上文政策意见所归者'),('高季兴','称臣请求未被接受者')],place='吴与荆南',note='上下文归吴政策，未虚构吴主亲批细节；允许归附唐不等已完成唐方受纳。')
E=ev('renhuan_announced_voucher_dispute','任圜与安重诲在御前争论馆券应由户部还是内廷发出',26,'旧制','声色俱厉。',[('任圜','维护馆券出户部者'),('安重诲','请从内出者'),('帝','听奏者')],place='后唐朝廷',note='旧制为背景，争论日未明；争执不凭此建立终身仇敌关系。')
claim('event',E,'description','旧任圜传正文称使人食券原出户部，安重诲改为内出，任圜争于御前而被阻。',26,'先是，使人食券，皆出於戶部，重誨止之，俾須內出，爭於御前，往復數四，竟為所沮，','正文食券与主馆券并列；后附引通鉴的宫人叙述不算独立补证。',source='jiuwudaishi-067-renhuan-vouchers',relation='corroborates')
E=ev('palace_comment_on_renhuan_argument','宫人以宰相奏事激烈为轻视皇帝，李嗣源听后更加不悦',26,'上退朝','上愈不悦，',[('帝','听宫人议论者'),('任圜','宫人议论所指宰相')],place='后唐宫中',note='宫人匿名，所言长安经历和轻大家判断标为话语；不据此判断任圜真实动机。')
E=ev('siyuan_accepts_anzhonghui_voucher_plan','李嗣源最终采纳安重诲的馆券内出方案',26,'卒从','重诲议。',[('帝','采纳者'),('安重诲','方案提出者')],place='后唐朝廷')
E=ev('renhuan_requests_leave_finance','任圜请求辞去三司事务',26,'圜因','求罢三司，',[('任圜','请求辞三司者')],when='927年五月，旧明宗纪五月段记；主本段未具日',place='后唐朝廷',note='辞三司不是六月丙戌罢相，不提前七月致仕或十月被杀。')
claim('event',E,'description','旧明宗纪五月条亦记任圜上表辞三司事。',26,'宰臣任圜表辭三司事，','同一辞职请求，不重复创建事件；旧未另具日。',source='jiuwudaishi-038-min-withdrawal',relation='corroborates')
E=ev('menghu_deputy_finance_acting','枢密承旨孟鹄获命为三司副使、权判三司',26,'诏以','鹄，魏州人也。',[('帝','任命所归者'),('孟鹄','魏州人、枢密承旨转三司副使权判')],when='927年五月，旧明宗纪五月段记；主本段未具日',place='后唐朝廷',note='权判为暂掌事务，不等已获正式三司使；魏州籍贯不当任所。')
claim('event',E,'description','旧明宗纪称枢密院承旨孟鹄充三司副使权判。',26,'乃以樞密院承旨孟鵠充三司副使權判。','孟鵠繁简同一人；枢密承旨与枢密院承旨保留书证文字。',source='jiuwudaishi-038-min-withdrawal',relation='corroborates')
E=ev('wennian_proposes_crown_prince','太子詹事温辇请求册立太子',27,'六月',None,[('温辇','太子詹事、请立太子者')],when='927年六月庚辰',place='后唐朝廷',note='只录奏请；本句未记批准、册立或太子人选。')
E=ev('renhuan_removed_chancellor_shaobao','任圜罢门下侍郎、同平章事，守太子少保',28,'丙戌',None,[('任圜','罢相、守太子少保者')],when='927年六月丙戌',place='后唐朝廷',note='守太子少保不是已经致仕；与辞三司不同阶段。')
claim('event',E,'description','旧明宗纪同记六月丙戌任圜落平章事，守太子少保。',28,'丙戌，宰相任圜落平章事，守太子少保。','同日同事印证。',source='jiuwudaishi-038-june-offices',relation='corroborates')
claim('event',E,'time_original','新明宗纪亦记六月丙戌任圜罢。',28,'六月丙戌，任圜罷。','独立source正文；不提前同年十月被杀。',source='xinwudaishi-006-927-opening',relation='corroborates')
E=ev('zhangyanlang_heads_finance','宣徽北院使张延朗获命判三司',29,'己丑',None,[('张延朗','宣徽北院使、判三司获授者')],when='927年六月己丑',place='后唐朝廷')
claim('event',E,'description','旧明宗纪另列张延朗为右武卫大将军、判三司，依前宣徽使、检校司徒。',29,'以宣徽北院使張延朗為右武衛大將軍、判三司，依前宣徽使、檢校司徒。','补授衔；旧此句处丁亥事项后、辛卯前，未具己丑，不擅将旧任命强归丁亥。',source='jiuwudaishi-038-june-offices',relation='adds')
E=ev('liuxun_demoted_tanzhou','刘训贬为刺史：通鉴作檀州，旧五代史作澶州',30,'壬辰',None,[('刘训','受贬者')],when='927年六月壬辰',place='檀州〔主书〕／澶州〔旧史〕',note='两地不等同，底本文字保留，不强校地名或给坐标。')
claim('event',E,'description','旧明宗纪壬辰称刘训责授检校右仆射、守澶州刺史，并解释为南征无功。',30,'壬辰，南面招討使、知荊南行府事、襄州節度使、檢校太傅劉訓責授檢校右僕射、守澶州刺史。訓南征無功，故有是譴。','主檀州与旧澶州异文并存，南征无功为旧所记原因，不提前七月流濮州。',source='jiuwudaishi-038-june-offices',relation='conflicts')
E=ev('mayin_promoted_chu_kingdom_title','马殷由楚王进封楚国王',31,'丙申',None,[('楚王殷','楚国王获封者')],when='927年六月丙申',place='楚与后唐朝廷',note='保留楚王与楚国王具体称号差别，不据封号宣称此日始有楚政权。')
claim('event',E,'description','旧明宗纪同日称马殷守太师、尚书令，封楚国王。',31,'丙申，以天策上將軍、湖南節度使、開府儀同三司、檢校太師、守尚書令、楚王馬殷為守太師、尚書令，封楚國王。','补官衔，同日册命；七月竹册奏议留后续连续段落再处理。',source='jiuwudaishi-038-june-offices',relation='adds')
E=ev('xifangye_defeats_jingnan_recovers_three_prefectures','西方邺在峡中击败荆南军，收复夔、忠、万三州',32,'西方',None,[('西方邺','败荆南军、收复三州者')],when='927年六月段后叙述，战日未明；旧七月甲子段记奏报，新纪系七月甲子',place='峡中、夔州、忠州、万州',note='主原句败荆南水疑水军省字或讹缺，摘录保留；报告日不直接等于实战发生日。')
claim('event',E,'description','旧明宗纪在七月甲子段记夔州刺史西方邺奏，杀败荆南军、收峡内三州。',32,'夔州刺史西方鄴奏，殺敗荊南賊軍，收峽內三州。','奏报同战事；旧夔州刺史与新随州刺史职衔异文保留，不新建另一次收复。',source='jiuwudaishi-038-july-reconquest',relation='corroborates')
claim('event',E,'time_original','新明宗纪记秋七月甲子随州刺史西方邺取夔、忠、万州。',32,'秋七月甲子，隨州刺史西方鄴取夔、忠、萬州。','新系七月甲子，主六月后未另具日，旧甲子段记奏报，各标书证不强统战日。',source='xinwudaishi-006-927-opening',relation='conflicts')
review='连续25—32段逐句校核。楚遣史光宪入贡、后唐赐马女、荆南扣使夺物、请附吴、徐温难救理由与吴受贡拒臣分录；拒臣不提前后续受臣册王。馆券户部旧制、御前争执、宫人评论、采安议、任辞三司与孟副使权判分录；宫人匿名不建人物，其评价不当动机事实。旧任传正文食券为补证，注引通鉴不算独立。五月辞三司与六月丙戌罢相守少保不同阶段，不提前七月致仕或十月杀。温辇请立只是提议，不建已立太子或人选。张主己丑，旧在丁亥后辛卯前未具新日不硬定丁亥。刘主檀州/旧澶州异文不改，旧南征无功为史说，不提前濮州流。马楚王进楚国王与旧太师尚书令，称号差别不等新建国家，竹册后事暂留。西三州主六月后无明日、旧七月甲子段奏报、新七月甲子取州，报告不当实战日；旧夔刺史/新随刺史、主败荆南水缺字原样保留。展示简体，引用原字，纸本待核。'
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,33):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=review)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=275,year=927,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(25,33)],next_paragraph='zztj-v276-y0927-p001',next_volume=276,next_year=927,supplements=supplements,excluded_non_body=[],coverage='卷275连续25—32段、原文件99—106行；楚使、馆券、三司、朝廷任命及三州收复。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=review) for n in range(25,33)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
