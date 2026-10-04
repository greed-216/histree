# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 281, year 937 paragraphs 29–34."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,60))
specs=[(d.name,d,'c90e9012','司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-281-937-wuyue','jiuwudaishi-095-wu-luan','xinwudaishi-029-wu-luan']:
 prior=next(x for f in (ROOT/'content').rglob('content-batch.json') for x in json.loads(f.read_text())['sources'] if x['key']==key)
 commit,relative=prior['url'].split('/blob/')[1].split('/',1)
 specs.append((key,(ROOT/relative).parent,commit,prior['author']))

# Reuse already published source identities, including the earlier Zhou Gui biography.
prior_source_registry={x['key']:x for f in sorted((ROOT/'content').rglob('content-batch.json')) if f.parent != P for x in json.loads(f.read_text())['sources']}
normalized=[]
for key,path,commit,author in specs:
 if key in prior_source_registry:
  archived=prior_source_registry[key]['url'].split('/blob/',1)[1];commit,relative=archived.split('/',1);old_path=(ROOT/relative).parent
  assert (old_path/'source.txt').read_bytes()==(path/'source.txt').read_bytes(),key
  path=old_path
 normalized.append((key,path,commit,author))
specs=normalized

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-281-937-wuyue','tongjian-281-937-rebellion']
B = {'format_version': 1, 'batch_key': 'zztj-v281-y0937-p029-p034',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'jiuwudaishi-076-937-june':'卷76·晋高祖纪·天福二年六月','jiuwudaishi-076-li-xia-background':'卷76·晋高祖纪·天福二年八月追记李遐遇害','jiuwudaishi-109-du-chongwei':'卷109·杜重威传','xinwudaishi-051-fan-rebellion':'卷51·范延光传','xinwudaishi-068-chen-jiu':'卷68·闽世家'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=('维基文库固定修订1769092；wikitext连续摘录，纸本及版本字形待核。' if key.endswith('-collation') else '选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/281.txt').read_text().splitlines()
for n in range(29, 35):
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
for name,extra in [('荝剌',['荝刺']),('耶律倍',['李赞华','李贊華'])]:
    if name in registry:registry[name]=dict(registry[name],aliases=list(dict.fromkeys(registry[name]['aliases']+extra)))
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
    labels={'jiuwudaishi-076-937-june':'卷76·晋高祖纪·天福二年六月','jiuwudaishi-076-li-xia-background':'卷76·晋高祖纪·天福二年八月追记李遐遇害','jiuwudaishi-109-du-chongwei':'卷109·杜重威传','xinwudaishi-051-fan-rebellion':'卷51·范延光传','xinwudaishi-068-chen-jiu':'卷68·闽世家'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '六月条下'
        citation = f'卷281·后晋天福二年（937；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_281_0937_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={
'孙锐':'范延光的元随左都押牙。范延光把军府事务交给他处理。937年与冯晖共同劝逼范延光起兵，随后担任兵马都监。',
'白奉进':'云州人，后晋将领。937年以侍卫马军都指挥使、昭信节度使身份，奉命率一千五百骑兵驻守白马津。',
'张言':'后晋六宅使。937年出使魏州返回，向石敬瑭报告范延光反叛。',
'杜重威':'朔州人，后晋将领，妻子是石敬瑭的妹妹乐平长公主。937年以护圣都指挥使身份率军驻卫州。',
'乐平长公主（杜重威妻）':'石敬瑭的妹妹、杜重威的妻子。937年的记载称她为乐平长公主。',
'张谊':'襄邑人，曾任耀州团练推官。937年致书和凝，劝他接待宾客以了解各地情况，随后经推荐被任命为左拾遗。',
'石重信':'石敬瑭的儿子，任河阳节度使。937年张从宾反叛时被杀。',
'石重乂':'石敬瑭的儿子，代理东都留守。937年张从宾进入洛阳时被杀。',
'张延播':'后晋官员，任东都副留守、都巡检使。937年张从宾反叛后让他主持河南府事务。',
'李遐':'后晋东都留守判官。937年拒绝把库中的钱帛交给张从宾的叛军，遭军士杀害。',
'蔡守蒙':'闽国官员，任吏部侍郎并负责三司事务。937年在王继鹏逼迫下接受收取贿赂、登记上缴的任官办法。史书称他是候官人，地名写法待核。',
'陈究':'闽国医工。937年奉王继鹏命，持未填官员姓名的任官文书到外地卖官。'}
NEW_ALIASES={n:[] for n in NEW_DESCRIPTIONS}
NEW_ALIASES.update({'孙锐':['孫銳'],'白奉进':['白奉進'],'杜重威':[],'乐平长公主（杜重威妻）':['乐平长公主'],'张谊':['張誼'],'石重信':['重信'],'石重乂':['重乂'],'张延播':['張延播']})
ALIASES.update({'景通':'李璟','徐知诰':'李昪','徐诰':'李昪','元瓘':'钱传瓘','钱元瓘':'钱传瓘','闽主':'王继鹏','蜀主':'孟昶','汉主':'刘岩','梁均王':'朱友贞'})



ALIASES.update({'张彦琦':'张彦琪','张彦琪':'张彦琪','曹太后':'曹氏（李嗣源后）','刘皇后':'刘氏（李从珂后）','太相温':'太相温（契丹将）','大相温':'太相温（契丹将）','汉主':'刘岩','吴主':'杨溥','杨光远':'杨檀','景岩':'刘景岩','刘延郎':'刘延朗','李赞华':'耶律倍','李懿':'李懿（后唐亲将）'})

# Follow already verified merges so hidden legacy entities are never revived.
registry_by_key={r['key']:r for r in registry.values()}
for plan_file in sorted((ROOT/'content/revisions').glob('*/plan.json')):
 audit_file=plan_file.parent/'publication.json'
 if not audit_file.exists():continue
 plan=json.loads(plan_file.read_text());audit=json.loads(audit_file.read_text())
 if not (audit.get('verified') and audit.get('canonical_person_id') and audit.get('hidden_duplicate_person_id')):continue
 canonical=registry_by_key.get(plan.get('canonical_key'));duplicate=registry_by_key.get(plan.get('duplicate_key'))
 if canonical and duplicate:
  canonical=dict(canonical,aliases=list(dict.fromkeys(canonical.get('aliases',[])+plan.get('aliases_to_add',[]))))
  registry[canonical['name']]=canonical
  for alias in [duplicate['name']]+duplicate.get('aliases',[]):ALIASES[alias]=canonical['name']

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=937 if name in ['石重信','石重乂','李遐'] else None,description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=937, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='937年六月'+'，具体日期未记载'
    key = 'event_zztj_281_0937_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=description or title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='采用史书记载的地点名称，地理坐标尚未核实。', status='draft')
    if stable_key:
        matches = [x for path in (ROOT/'content').rglob('content-batch.json') if path.resolve()!=(P/'content-batch.json').resolve() for x in json.loads(path.read_text())['events'] if x['key']==stable_key]
        assert matches, stable_key
        row=dict(matches[0],status='draft'); key=stable_key; reused.add(key)
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。',source=source)
    claim('event', key, 'time_original', when, n, quote,
          '按主书及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_281_0937_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'与{a}存在原文明示的亲属关系',quote,source=source)
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
        row=dict(key=f'relationship_zztj_281_0937_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)




E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=ev(code,title,n,start,end,actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
def source_span(source,start,end):
 t=(sources[source]/'source.txt').read_text();a=t.index(start);b=t.index(end,a)+len(end);return t[a:b]

# Curated opening paragraphs.
ALIASES.update({'张昭远':'张昭（五代宋初）','契丹主':'耶律德光'})
ALIASES.update({'乐平长公主':'乐平长公主（杜重威妻）','重信':'石重信','重乂':'石重乂'})
# 29: existing military administration, decision to rebel, reports and deployments.
add('sun_controls_fan_office','范延光将军府事务交给孙锐处理，孙锐当面撕毁不合心意的文书',29,'范延光素以','手裂之。',[('范延光','长期把军府事务交给孙锐'),('孙锐','处理军府事务，当面撕毁不合心意的文书')],year=None,when='范延光起兵前的军府事务，起始年份未明确',place='魏州',note='“素”表示先前长期情况，不将全部经历强定为937年。孙锐恃恩专横是史书记述。')
add('sun_feng_press_fan','孙锐与冯晖劝逼范延光起兵，范延光接受',29,'会延光病经旬','遂从之。',[('孙锐','秘密召冯晖商议，劝逼范延光起兵'),('冯晖','与孙锐共同劝逼范延光起兵'),('范延光','患病十天后接受起兵建议')],place='魏州',description='范延光患病十天。孙锐秘密召来澶州刺史冯晖，二人合谋劝逼范延光反叛。范延光想到此前张生的说法，最终同意。',note='“经旬”说明病程，不据此推算发病日；没有把范延光写成完全被动或无意起兵。张生是此前已录术士，不另建同名人。')
sup('sun_feng_press_fan',29,'xinwudaishi-051-fan-rebellion','天福二年六月，延光遂反，','《新五代史》也记范延光在天福二年六月起兵。','新史没有在这句交代孙锐、冯晖劝逼过程，补证只确认起兵月份。')
add('zhang_yan_reports_fan','张言出使魏州返回，报告范延光反叛',29,'甲午，','言延光反状；',[('张言','从魏州返回，报告范延光反叛'),('帝','收到张言关于范延光的报告')],when='937年六月甲午报告',place='魏州至朝廷')
sup('zhang_yan_reports_fan',29,'jiuwudaishi-076-937-june','甲午，六宅使張言自魏府回，奏範延光叛命。','《旧五代史》也记张言于甲午从魏府返回并奏报范延光反叛。','甲午是返回及报告日期，不直接认定为最初起兵日。')
add('fu_reports_river_arson','符彦饶报告范延光派兵渡河焚烧草市',29,'义成节度使','焚草市；',[('符彦饶','报告范延光派兵渡河焚烧草市'),('范延光','被报告派兵渡河焚烧草市')],place='黄河沿岸草市',note='保存奏报所述行动，没有明确的渡河、焚烧日期，不将前句甲午自动作为行动日。')
add('bai_defends_baima','石敬瑭命白奉进率一千五百骑兵驻守白马津',29,'诏侍卫马军','奉进，云州人也。',[('帝','命白奉进率骑兵设防'),('白奉进','率一千五百骑兵驻守白马津')],place='白马津')
sup('bai_defends_baima',29,'jiuwudaishi-076-937-june','尋命護聖都指揮使白奉進領騎士一千五百赴白馬渡巡檢。','《旧五代史》记白奉进率一千五百骑兵到白马渡巡检，官衔记为护圣都指挥使。','兵数相同，官衔与主书侍卫马军都指挥使、昭信节度使分别保留，不用相同人数消除职衔差异。',relation='adds')
add('zhang_southwest_command','石敬瑭任命张从宾为魏府西南面都部署',29,'丁酉，','西南面都部署。',[('帝','任命张从宾为魏府西南面都部署'),('张从宾','从东都巡检使被任命为魏府西南面都部署')],when='937年六月丁酉')
sup('zhang_southwest_command',29,'jiuwudaishi-076-937-june','以東都巡檢使張從賓充魏府四南面都部署；','《旧五代史》电子本此处写“魏府四南面都部署”。','与《通鉴》“西南面”异文并列。“四南面”疑有文字问题，纸本未核，不悄悄改动摘录。',relation='conflicts')
add('yang_ten_thousand_hua','石敬瑭派杨光远率一万步骑兵驻滑州',29,'戊戌，','屯滑州。',[('帝','派杨光远率一万步骑兵驻滑州'),('杨光远','率一万步骑兵驻滑州')],when='937年六月戊戌',place='滑州',note='杨光远复用杨檀主体，一万是步兵与骑兵合计，不各记一万。')
sup('yang_ten_thousand_hua',29,'jiuwudaishi-076-937-june',source_span('jiuwudaishi-076-937-june','丁酉，遣內班','領步騎一萬赴滑州。'),'《旧五代史》在丁酉条下记派杨光远率一万步骑兵赴滑州。','主书记戊戌；日期差异分别保存，不改既有主书纪日。',relation='conflicts',field='time_original')
add('du_stations_wei','石敬瑭派杜重威率军驻守卫州',29,'己亥，','尚帝妹乐平长公主。',[('帝','派杜重威率军驻卫州'),('杜重威','以护圣都指挥使身份率军驻卫州')],when='937年六月己亥',place='卫州')
relationship('帝','乐平长公主','兄长',29,span(29,'重威，朔州人也，','尚帝妹乐平长公主。'),'原文明示公主为石敬瑭的妹妹，方向为石敬瑭是公主的兄长。')
relationship('杜重威','乐平长公主','丈夫',29,span(29,'重威，朔州人也，','尚帝妹乐平长公主。'),'“尚”在这里指娶公主，不改变双方性别、身份或关系方向。')
claim('person',people['杜重威'],'description','《旧五代史》记杜重威祖籍朔州，家族后来迁居太原。其妻是晋高祖石敬瑭的妹妹，后来多次受封，称宋国大长公主。',29,source_span('jiuwudaishi-109-du-chongwei','杜重威，其先朔州人','累封宋國大長公主。'),'这里只补家世、婚姻身份；不把传记后来宋国大长公主的称号提前作为937年称号。',source='jiuwudaishi-109-du-chongwei')
add('fan_feng_sun_liyang','范延光任命冯晖、孙锐率两万步骑兵抵达黎阳口',29,'范延光以冯晖','抵黎阳口。',[('范延光','任命冯晖、孙锐并派军进至黎阳口'),('冯晖','以都部署身份统率出征军队'),('孙锐','以兵马都监身份随军出征')],place='黎阳口',description='范延光任命冯晖为都部署、孙锐为兵马都监。二人统率共两万步骑兵，沿黄河向西抵达黎阳口。')
sup('fan_feng_sun_liyang',29,'xinwudaishi-051-fan-rebellion','遣其牙將孫銳、澶州刺史馮暉，以兵二萬距黎陽，掠滑、衞。','《新五代史》也记范延光派孙锐、冯晖率两万人到黎阳，并侵掠滑州、卫州。','两万是同一支军队的人数，未按两个将领各计两万；后文渡河败战留待主书对应段落处理。',relation='adds')
add('yang_reports_huliang_crossing','杨光远奏报率军渡过胡梁渡',29,'辛丑，',None,[('杨光远','奏报率军渡过胡梁渡'),('帝','收到渡河奏报')],when='937年六月辛丑奏报',place='胡梁渡',note='辛丑明确是奏报纪日，渡河发生日没有独立列出。')
# 30: communication and policy proposals, not proof of implementation.
add('he_appointed_duanming','和凝被任命为端明殿学士',30,'以翰林学士','为端明殿学士。',[('和凝','由翰林学士、礼部侍郎被任命为端明殿学士')])
sup('he_appointed_duanming',30,'jiuwudaishi-076-937-june','翰林學士、禮部侍郎和凝改端明殿學士。','《旧五代史》也记和凝改任端明殿学士。','本纪这句未单列日干支，不外推成前后相邻日期。')
add('zhang_yi_writes_he','张谊致书和凝，劝他接待宾客以了解各地情况',30,'凝署其门','如负国何！”',[('和凝','在门上张贴告示，不接待宾客'),('张谊','致书劝和凝了解各地利弊')],description='和凝在门上张贴告示，不接待宾客。曾任耀州团练推官的襄邑人张谊致书，认为近臣承担皇帝耳目之责，应接触宾客以了解各地利弊，不能只求自己方便。',note='这是张谊提出的劝告，不据此判定和凝已经造成具体国家损失。')
add('he_recommends_zhang_yi','和凝向桑维翰推荐张谊',30,'凝奇之，','荐于桑维翰，',[('和凝','赏识张谊并向桑维翰推荐'),('张谊','被和凝推荐'),('桑维翰','收到和凝的推荐')])
add('zhang_yi_appointed_shiyi','张谊经推荐后被任命为左拾遗',30,'凝奇之，','除左拾遗。',[('张谊','经和凝推荐后被任命为左拾遗')],year=None,when='和凝推荐之后不久，任命日期未明确',note='“未几”表示后续不久，原文没有单列任命日，暂不强定为六月。')
add('zhang_yi_border_advice','张谊建议对契丹保持友好，同时谨慎防备边境',30,'谊上言：',None,[('张谊','建议对契丹保持友好，同时加强边境防备'),('帝','赞同张谊的建议')],year=None,when='张谊任左拾遗之后上言，具体日期未记载',description='张谊认为契丹曾帮助石敬瑭即位，建议对外保持友好，对内谨慎防备边境，不可安逸自满。石敬瑭表示赞同。',note='“深然之”是认可建议，没有直接说明随后实施了哪项边防措施。')
# 31: reused siege/relief; newly attested steps remain separate.
add('yunzhou_siege_recap','契丹围攻云州半年而未能攻下',31,'契丹攻云州，','半岁不能下。',[('吴峦','守卫云州')],place='云州',stable_key='event_zztj_281_0937_khitan_fails_yunzhou',note='复用二月段中已经建立的同一围城事件，新增半年未下的引用；六月条为回顾叙述，不改旧档案为另一场围攻。')
claim('event',E['yunzhou_siege_recap'],'description','《资治通鉴》在六月条下回顾契丹攻云州，围攻半年未能攻下。',31,'契丹攻云州，半岁不能下。','半年是主书概述的围攻时长，不从此推算精确开始、结束日。')
add('wu_sends_relief_request','吴峦派使者经隐蔽路线向石敬瑭求援',31,'吴峦遣使','奉表求救，',[('吴峦','派使者携表求援'),('帝','吴峦的求援对象')],place='云州至后晋朝廷',year=None,when='云州围城期间，具体求救日期未记载；主书六月条下回顾')
add('yunzhou_relief_recap','石敬瑭致书耶律德光请求云州解围',31,'帝为之致书','解围去。',[('帝','致书耶律德光请求解围'),('契丹主','命翟璋解除云州包围'),('翟璋','奉命解除云州包围')],place='云州',stable_key='event_zztj_281_0937_shi_requests_yunzhou_relief',note='复用此前由新旧五代史建立的解围事件，补主书当前段落引用；该事件旧档案未定具体年，当前纪时作为独立事实保留。')
claim('event',E['yunzhou_relief_recap'],'description','石敬瑭为吴峦致书耶律德光，请求解围；耶律德光随后命翟璋解除包围离去。',31,span(31,'帝为之致书','解围去。'),'这段明确请求、下令及解围的先后关系，不另造第二次解围。')
add('wu_summoned_wuning_deputy','石敬瑭召吴峦回朝，任命他为武宁节度副使',31,'帝召峦归，',None,[('帝','召吴峦回朝并任命为武宁节度副使'),('吴峦','回朝后被任命为武宁节度副使')],place='后晋朝廷',year=None,when='云州解围之后，召回和任命日期未单列；主书六月条下回顾')
sup('wu_summoned_wuning_deputy',31,'xinwudaishi-029-wu-luan','高祖召巒，以為武寧軍節度副使、諫議大夫、復州防禦使。','《新五代史》记吴峦被召回后任武宁军节度副使，随后又任谏议大夫、复州防御使。','当前段只录副使任命；传记串列的后续职务不全部定在六月。')
sup('wu_summoned_wuning_deputy',31,'jiuwudaishi-095-wu-luan','召巒歸闕，授徐州節度使，','《旧五代史》记吴峦被召回后授徐州节度使。','武宁军治所在徐州，但节度使与节度副使的职级仍不同，保留记载差异，不据地名相同消除官职差异。',relation='conflicts')
# 32: command assignments and Guo Wei's own assessment.
add('yang_four_sides_command','杨光远被任命为魏府四面都部署',32,'丁未，','魏府四面都部署，',[('杨光远','以侍卫使身份被任命为魏府四面都部署')],when='937年六月丁未')
sup('yang_four_sides_command',32,'jiuwudaishi-076-937-june','丁未，詔侍衛使楊光遠充魏府四面都部署；','《旧五代史》也记丁未任命杨光远为魏府四面都部署。','复用杨檀主体，当前四面部署任命与前段领军驻滑州分开。')
add('zhang_deputy_command','张从宾被任命为副部署兼诸军都虞侯',32,'张从宾为','兼诸军都虞侯，',[('张从宾','被任命为副部署兼诸军都虞侯')],when='937年六月丁未')
add('gao_stations_xiang','高行周率本军驻相州，担任魏府西面都部署',32,'昭义节度使', '西面都部署。',[('高行周','率本军驻相州，担任魏府西面都部署')],when='937年六月丁未',place='相州')
sup('gao_stations_xiang',32,'jiuwudaishi-076-937-june','昭義節度使高行周充魏府西面都部署。','《旧五代史》也记高行周担任魏府西面都部署。','本纪未在此句记驻相州，补证只确认部署职务。')
add('guo_asks_remain_liu','郭威请求留在刘知远部下，不随杨光远北征',32,'军士郭威',None,[('郭威','请求留在刘知远部下，表示刘知远更能用自己'),('刘知远','收到郭威请求留任'),('杨光远','原拟带郭威北征，被郭威评论')],description='原属刘知远的军士郭威本应随杨光远北征，却向刘知远请求留下。被问及原因时，他认为杨光远不能发挥自己的能力，而刘知远能够用他。',note='对杨光远“有奸诈之才，无英雄之气”的话是郭威的评价，不写成网站客观定论；原文未明确刘知远是否批准。')
# 33: rebellion in Henan, murders, appointments and response.
add('zhang_ordered_against_fan','石敬瑭命张从宾调河南数千兵讨伐范延光',33,'诏张从宾','击范延光。',[('帝','命张从宾调河南兵讨伐范延光'),('张从宾','受命调动河南数千兵'),('范延光','朝廷命令讨伐的对象')],place='河南至魏州',note='“数千”不补成精确人数，朝廷命令不等于张从宾真正出战。')
add('fan_recruits_zhang_rebellion','范延光派人招引张从宾，张从宾随即一同反叛',33,'延光使人诱','遂与之同反，',[('范延光','派人招引张从宾'),('张从宾','接受招引，一同反叛')],place='河南',note='招引使者未具名；不因联合反叛而新增无证亲属或长期私人关系。')
sup('fan_recruits_zhang_rebellion',33,'jiuwudaishi-076-937-june','是日，張從賓亦叛，與範延光葉謀，害皇子河陽節度使重信、皇子東都留守重乂。','《旧五代史》在丁未条下记张从宾与范延光合谋反叛，并杀两位皇子。','这是旧史给出的日期补证，主书本段未单列干支，不将之前任部署纪日自动转作所有后续行动日。',relation='adds',field='time_original')
add('zhang_kills_chongxin','张从宾杀死河阳节度使石重信',33,'杀皇子河阳','重信，',[('张从宾','反叛后杀死石重信'),('重信','以河阳节度使身份被杀')],place='河阳')
relationship('帝','重信','父亲',33,'杀皇子河阳节度使重信，','皇子称谓结合本年皇帝石敬瑭确认父子，方向为石敬瑭是石重信的父亲。')
add('zhang_jizuo_heyang','张从宾让张继祚主持河阳留后事务',33,'使上将军','继祚，全义之子也。',[('张从宾','让张继祚主持河阳留后事务'),('张继祚','以原上将军身份主持河阳留后事务')],place='河阳',note='这是叛军安排的职位，不写成石敬瑭的朝廷正式任命。')
relationship('张全义','张继祚','父亲',33,'继祚，全义之子也。','原文明示张继祚是张全义之子，复用已存同向关系，不新增反向重复边。')
add('zhang_enters_luoyang_kills_chongyi','张从宾率兵进入洛阳，杀死代理东都留守石重乂',33,'从宾又引兵','权东都留守重乂，',[('张从宾','率兵进入洛阳并杀死石重乂'),('重乂','以代理东都留守身份被杀')],place='洛阳')
relationship('帝','重乂','父亲',33,'杀皇子权东都留守重乂，','皇子身份明确，权字表示代理职务，父亲边不把张从宾误作父亲。')
add('zhang_yanbo_henan','张从宾让张延播主持河南府事务',33,'以东都副留守','知河南府事。',[('张从宾','让张延播主持河南府事务'),('张延播','以东都副留守、都巡检使身份主持河南府事务')],place='洛阳',note='这是反叛后的职务安排，不认作石敬瑭同意。')
add('zhang_treasury_li_xia_killed','李遐拒给张从宾军队库钱，遭军士杀害',33,'从宾取内库','兵众杀之。',[('张从宾','取库中钱帛赏赐部下'),('李遐','拒绝交出库钱，被军士杀害')],place='洛阳',description='张从宾要取内库钱帛赏赐部下，东都留守判官李遐拒绝交出，遭军士杀害。',note='杀人主体是军士，原文未说张从宾亲手杀人。')
sup('zhang_treasury_li_xia_killed',33,'jiuwudaishi-076-li-xia-background','先是，遐監左藏庫於洛陽，會張從賓叛，令強取錢帛，遐拒而不與，因而遇害，故有是命。','《旧五代史》补记李遐在洛阳监管左藏库，因拒绝张从宾强取钱帛而被杀。','八月条中的“先是”回顾此次遇害，不将李遐死日定为八月；追赠及母亲待遇留待对应主书时段补录。',relation='adds')
add('zhang_blocks_sishui','张从宾向东扼守汜水关，准备威胁汴州',33,'从宾引兵东扼','将逼汴州。',[('张从宾','率军向东扼守汜水关，准备威胁汴州')],place='汜水关',note='扼守关口为已发生行动，逼近汴州为计划，不写成已经攻下汴州。')
add('hou_du_ordered_zhang','石敬瑭命侯益率五千援兵与杜重威会合讨伐张从宾',33,'诏奉国都指挥使','讨张从宾；',[('帝','命侯益率援兵会合杜重威讨伐'),('侯益','受命率五千援兵'),('杜重威','被命与侯益会合讨伐'),('张从宾','讨伐对象')],place='汜水关方向',note='主书“五千”在侯益所率援兵句中，不自行加总为杜、侯各五千或推两军总兵数。')
sup('hou_du_ordered_zhang',33,'jiuwudaishi-076-937-june','己酉，以奉國都指揮使侯益、護聖都指揮使杜重威領步騎五千往屯汜水關，備從賓之亂也。','《旧五代史》记己酉命侯益、杜重威率共五千步骑兵屯汜水关，防备张从宾。','旧史人数范围为杜、侯共同所率步骑，主书写侯益率五千援兵会合杜重威；保持口径差异，不强合成同一总数。',relation='adds')
add('liu_churang_divides_force','石敬瑭命刘处让从黎阳分兵讨伐张从宾',33,'又诏宣徽使','分兵讨之。',[('帝','命刘处让从黎阳分兵讨伐'),('刘处让','受命从黎阳分兵'),('张从宾','讨伐对象')],place='黎阳')
add('sang_calms_court','桑维翰从容安排军事，史书记载官员因此稍感安定',33,'时羽檄纵横，',None,[('桑维翰','从容安排军事并照常接待宾客')],place='大梁',description='军情文书不断往来，留在大梁的随行官员惊惧。史书记载桑维翰从容安排军事，照常接待宾客，众人因而稍感安定。',note='恐惧、从容和众心稍安是史书记述，不额外推断全部官员或长期心理状态。')
# 34: belief reported as such, explicit orders distinguished from consequences.
add('min_white_dragon_temple','王继鹏听方士称螺峰出现白龙，修建白龙寺',34,'方士言于闽主','闽主作白龙寺。',[('闽主','听取方士说法，修建白龙寺')],place='螺峰、白龙寺',description='方士向王继鹏声称螺峰夜里出现白龙，王继鹏据此修建白龙寺。',note='出现白龙只是方士的说法，不作为实际自然现象确证。')
add('min_orders_bribe_appointments','王继鹏命蔡守蒙收取任官贿赂并登记上缴',34,'时百役繁兴，','籍而献之。”',[('闽主','要求蔡守蒙收取任官贿赂并登记上缴'),('蔡守蒙','负责吏部、三司事务，收到收贿任官命令')],place='闽',description='工程众多、费用不足。王继鹏询问蔡守蒙官员任命中是否有受贿现象，蔡守蒙说传言不足信。王继鹏称自己早已知情，命蔡守蒙在选贤任官之外，对不称职或冒名求官者也不要拒绝，只须收取贿赂、登记上缴。',note='命令没有普遍废除选贤要求，但明确放行不称职或冒名者收贿求官；不压成所有职位均只卖官的单一诏令。')
add('cai_compelled_bribery','蔡守蒙反对收贿任官，因王继鹏发怒而接受',34,'守蒙素廉，','守蒙惧而从之。',[('蔡守蒙','反对收贿任官，惧怕王继鹏而接受'),('闽主','因蔡守蒙反对而发怒')],place='闽',note='廉洁是史书评价，接受命令与自发赞成区分。')
add('min_bribes_rank_offices','史书记载闽国此后任官只按贿赂多少定高下',34,'自是除官','为差。',[('闽主','收贿任官命令之后的闽国统治者')],place='闽',note='这是主书对随后任官结果的概括，与上段诏令原话分别录；没有具体贿赂金额。')
add('chen_jiu_sells_offices','王继鹏派医工陈究持空白任官文书到外地卖官',34,'闽主又以空名','无有盈厌。',[('闽主','派陈究持空白任官文书卖官'),('陈究','以医工身份到外地卖官')],place='闽各地',description='王继鹏把未填官员姓名的任官文书交给医工陈究，让他到外地卖官。史书记载王继鹏不断聚敛财富，没有满足。',note='空名堂牒为未填受任者姓名的任官文书，不按现代商业合同理解；聚敛无厌为史家概述。')
sup('chen_jiu_sells_offices',34,'xinwudaishi-068-chen-jiu','又遣醫人陳究以空名堂牒賣官。','《新五代史》也记王昶派医人陈究持空名堂牒卖官。','卷68闽世家本段昶即王继鹏，非后蜀孟昶；陈究医人、医工为同一身份，不因字形另建人物。')
add('min_population_penalties','王继鹏下令重罚隐瞒年龄、人口和逃亡的民众',34,'又诏民有隐年','逃亡者族。',[('闽主','下令处罚隐瞒年龄、人口与逃亡者')],place='闽',description='王继鹏下令：隐瞒年龄者杖打背部，隐瞒人口者处死，逃亡者连同族人处死。',note='保存严厉惩罚命令，不据此断言每种处罚均实际执行。“族”在此表示族诛，即牵连家族的死刑，具体族人范围未明。')
add('min_heavy_produce_taxes','闽国对果菜和鸡猪等征收重税',34,'果菜鸡豚，',None,[('闽主','统治期间对果菜和鸡猪等征收重税')],place='闽',note='豚按猪解释，原文没有税率，不补具体数额。')
# Profiles and death years are justified separately; reused archive rows are not rewritten.
profiles={
'孙锐':(29,'范延光素以','将步骑二万循河西抵黎阳口。'),
'白奉进':(29,'诏侍卫马军','奉进，云州人也。'),
'张言':(29,'甲午，','言延光反状；'),
'杜重威':(29,'己亥，','尚帝妹乐平长公主。'),
'乐平长公主（杜重威妻）':(29,'重威，朔州人也，','尚帝妹乐平长公主。'),
'张谊':(30,'前耀州','除左拾遗。'),
'石重信':(33,'杀皇子河阳','重信，'),
'石重乂':(33,'从宾又引兵','权东都留守重乂，'),
'张延播':(33,'以东都副留守','知河南府事。'),
'李遐':(33,'从宾取内库','兵众杀之。'),
'蔡守蒙':(34,'闽主谓吏部','守蒙惧而从之。'),
'陈究':(34,'闽主又以空名','无有盈厌。')}
for name,(n,start,end) in profiles.items():
 claim('person',people[name],'description',NEW_DESCRIPTIONS[name],n,span(n,start,end),'身份、任官与行动来自所引原文；不补未记生年、家世和时间。杜重威后来参与讨伐另见本批第33段。')
for name in ['石重信','石重乂','李遐']:
 n,start,end=profiles[name];claim('person',people[name],'death_year',f'{name}于937年张从宾反叛期间被杀。',n,span(n,start,end),'当前六月叛乱段明示被杀，死年937；具体公历日期未换算。')
reviews={29:'旧军府事务年份未定；范起兵决定、奏报及调兵分开。杜、公主婚姻和兄妹方向明示。两万为共同军队，一万步骑不分别计数。旧史部署方位、杨调兵纪日及白官衔差异保留。',30:'和凝任职、拒宾、张谊来书、推荐、任官和边防建议分开；未几及后续上言日期不强定，皇帝认可不等于措施已执行。',31:'复用云州围攻与解围主体；主书半年、新史七个月时长已有独立引证，当前补求救和副使任命。旧徐州节度使与新、主武宁副使职级差异保留。',32:'丁未三部署任命分录，郭威请求不自动写成获准；对杨评价归郭威言辞，不当作网站定论。',33:'诏讨与张实际反叛分开；皇子被杀、叛军职务安排、李拒交库钱被军士杀、军事调度分别录。数千不填精确数，旧侯杜五千与主侯五千保留口径。',34:'方士称白龙为传言；蔡收贿命令、拒绝受迫、后续按贿任官区分；陈空名堂牒新史独立补证。惩罚为诏令，不假定所有处分已实施，税率不造数。'}
assert not (P/'publication.json').exists()
for n in range(29,35):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
(P/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=281,year=937,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(29,35)],next_paragraph=Q[35]['id'],next_volume=281,next_year=937,supplements=supplements,source_contexts=[],excluded_non_body=[],coverage='连续第29—34段，原第34—39行；范延光起兵、朝廷调兵、和凝与张谊、云州解围、张从宾反叛及闽国卖官征税。937年尚未完成。',source_issues_review='逐字核对主书原TXT及固定快照；本范围未见私用字。旧本纪四南面异文保持；旧杜传传主与新范传、闽世家上下文已核；旁注转引通鉴不作为独立证明。新导出主书快照含第35—36段仅供后续引用，本批不计入录入范围。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(29,35)],plain_language_review='首次整理逐条检查新增标题、简介、事件正文、参与角色、关系方向与事实、核对说明，使用现代白话；引用原字不改。复用档案不重写，当前补充事实独立可回溯；不另设发布后二次文案审阅。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
