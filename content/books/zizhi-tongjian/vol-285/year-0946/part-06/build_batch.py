# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 285, year 946 paragraphs 39–44."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,57))
COMMIT='c7d707f140aeeb6d7f8cb666674b4e39a39263b6'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir())]
for key in ['tongjian-285-946-november-december']:
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
main_sources = ['tongjian-285-946-november-december','tongjian-285-946-surrender-camp','tongjian-285-946-surrender-capital']
B = {'format_version': 1, 'batch_key': 'zztj-v285-y0946-p039-p044',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if key in labels:record=dict(record,section_title=labels[key],citation='《'+record['book']+'》'+labels[key]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition=record.get('edition_note','选定TXT逐字导出；电子本，纸本及异文待核。'),
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation=('固定修订API wikitext连续摘录，原字及模板标记不改；仅用于同书版本、纪日、礼制、姓名及地理校读。' if key.endswith('-collation') else 'CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。')))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
# Reused source metadata remains exactly the already published record.
prior_sources=prior_source_registry
B['sources']=[dict(prior_sources[x['key']]) if x['key'] in prior_sources else x for x in B['sources']]
lines = (ROOT / 'resources/derived/tongjian/285.txt').read_text().splitlines()
for n in range(39, 45):
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
    for a,b in [('主書','《资治通鉴》'),('補','补'),('旧本纪','《旧五代史》本纪'),('新本纪','《新五代史》本纪'),('旧纪','《旧五代史》本纪'),('旧史','《旧五代史》'),('新史','《新五代史》'),('主书','《资治通鉴》'),('上批','此前的引用'),('寢','寝')]:
        note=note.replace(a,b)
    value = value.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    note = note.translate(str.maketrans({'記':'记','書':'书','約':'约','載':'载','壇':'坛','時':'时','數':'数','聞':'闻','實':'实','異':'异','財':'财','給':'给'}))
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    labels={'tongjian-283-943-autumn':'卷283·天福八年·八月至十一月及追述','jiuwudaishi-082-943-september':'卷82·晋少帝本纪·天福八年九月','jiuwudaishi-089-feng-yu':'卷89·冯玉传','xinwudaishi-017-feng-empress':'卷17·晋家人传·出帝冯皇后','xinwudaishi-017-shi-chongyin':'卷17·晋家人传·石重胤','xinwudaishi-062-zhang-defeat':'卷62·南唐世家·讨张遇贤'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷285·后晋开运三年（946年十二月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_285_0946_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'石敬瑭','唐主':'李从珂','徐知诰':'李昪','景通':'李璟','昶':'王继鹏','贤妃李氏':'李春燕','晋国长公主':'永宁公主（石敬瑭妻）','赞华':'耶律倍','契丹母':'述律平','荝刺':'荝剌'}
NEW_DESCRIPTIONS={'王威（王处直之子）':'《资治通鉴》与《旧五代史》记为王处直之子，因王都夺权逃往契丹。939年契丹要求后晋让他承袭父亲旧地，石敬瑭拒绝直接授节度使。生卒年未载。是否与早期记载的王郁有关，尚待校核，未作合并。'}
NEW_ALIASES={'王威（王处直之子）':['王威']}

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
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='五代十国',birth_year=None,death_year=globals().get('NEW_DEATH_YEARS',{}).get(name),description=NEW_DESCRIPTIONS[name],biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=946, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='946年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_285_0946_' + code
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
          '按《资治通鉴》及对应补证纪时；追叙或他书记载另作说明，不自行换算公历日期。',source=source)
    for name, role in actors:
        role = role.translate(str.maketrans({'\u805e':'\u95fb','\u5be6':'\u5b9e'}))
        pk = person(name, n, role, quote, source=source)
        edge = 'participation_zztj_285_0946_' + code + '_' + pk
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
    pa=person(a,n,f'是{b}的{kind}',quote,source=source); pb=person(b,n,f'是{a}的{kind}关系对象',quote,source=source)
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
        row=dict(key=f'relationship_zztj_285_0946_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
                 relation_type=kind,description=f'{a}是{b}的{kind}。',status='draft')
    B['person_relationships'].append(row)
    claim('person_relationship',row['key'],'description',f'{a}是{b}的{kind}。',n,quote,note,source=source)




# Quote only a contiguous span in an exported original snapshot.
def span(n,start,end=None):
 t=Q[n]['text'];a=t.index(start);b=t.index(end,a)+len(end) if end else len(t);return t[a:b]
def ev(code,title,n,start,end,actors,**kw):return event(code,title,n,span(n,start,end),actors,**kw)

E={}
def add(code,title,n,start,end,actors,**kw):
 E[code]=event(code,title,n,span(n,start,end),actors,**kw);return E[code]
def sup(code,n,source,quote,text,note,relation='corroborates',field='description'):
 claim('event',E[code],field,text,n,quote,note,source=source,relation=relation)
ALIASES.update({'帝':'石重贵','契丹主':'耶律德光','杜威':'杜重威','高行舟':'高行周','李彦韬':'李彦韬（后晋宣徽使）','王晖':'王晖（后晋代州刺史）','傅住兒':'傅住儿'})
NEW_ALIASES={'关勋':['關勛'],'张祚':['張祚'],'高勋':['高勛'],'王晖（后晋代州刺史）':['王暉（後晉代州刺史）'],'郭璘':[],'耿崇美':[],'马崇祚':['馬崇祚'],'傅住儿':['傅住兒']}
NEW_DESCRIPTIONS={'关勋':'后晋军将。946年十二月丁巳朔，李谷让他快马送密奏，己未晚间到达朝廷。生卒年未载。与阁门使高勋姓名不同，不因勋字相同合并。','张祚':'杜重威的从者。946年十二月辛酉等奉派向朝廷告急，返回军中时被契丹俘获，随后朝廷与前线消息中断。生卒年未载。','高勋':'后晋阁门使。946年十二月丙寅，杜重威派他向契丹送降表，耶律德光赐诏接受。与军将关勋分别识别；生卒年本批未核。','王晖（后晋代州刺史）':'后晋代州刺史。946年十二月契丹派兵袭代州，他以城投降。与已录后蜀前陵州刺史王晖是否同人未证，暂分档；生卒年未载。','郭璘':'邢州人，后晋易州刺史。曾屡次坚守易州抵抗契丹；946年十二月杜重威投降后，契丹派耿崇美诱使易州守军投降，郭璘无法制止并被杀。出生年未载。','耿崇美':'契丹通事。946年十二月杜重威降后，奉命到易州诱说守军投降，并杀死刺史郭璘。生卒年未载。','马崇祚':'契丹客省副使。946年十二月各地晋将投降后，耶律德光让他暂掌恒州事务。生卒年未载。','傅住儿':'契丹通事。946年十二月耶律德光派张彦泽领二千骑先取大梁，让傅住儿任都监。姓名展示用简体儿，原文傅住兒保留；生卒年本批未核。'}
NEW_DEATH_YEARS={'郭璘':946}
dec='946年十二月';j='jiuwudaishi-085-946-december';nw='xinwudaishi-009-946';lz='liaoshi-076-zhang-li'
add('li_gu_secret_memorial','李谷密奏晋军危急，建议石重贵到滑州，并加强澶州、河阳防守',39,'十二月，','奔冲；',[('李谷','上密奏，建议皇帝移驻并加强防守'),('帝','被建议移驻滑州'),('高行舟','被建议护送皇帝'),('符彦卿','被建议护送皇帝')],when=dec+'丁巳朔',place='军前至后晋朝廷、滑州、澶州、河阳',note='请是建议，不写皇帝已赴滑州。高行舟据本段后文高行周及旧本纪对应官职识别为高行周，摘录保留。旧本纪本日密奏是据通鉴补文，未作独立证据。')
add('guan_xun_carries_secret_memorial','李谷派关勋快马向朝廷送密奏',39,'遣军将',None,[('李谷','派军将送密奏'),('关勋','快马送李谷奏书')],when=dec+'丁巳朔',place='军前至后晋朝廷')
add('shi_learns_zhongdu_camp','石重贵得知大军驻中度，关勋于当晚到达',40,'己未，','关勋至。',[('帝','得知大军驻中度'),('关勋','当晚到达朝廷')],when=dec+'己未',place='中度至后晋朝廷',note='帝始闻是收到消息日，不是大军到中度的实际日期。')
sup('shi_learns_zhongdu_camp',40,j,'己未，杜威奏，駐軍於中渡橋。','《旧五代史》记己未杜重威上奏驻军中渡桥。','奏报日与到达日分开，中度中渡不同字形按各底本保留。')
add('shi_sends_remaining_palace_guards','杜重威请求增兵，石重贵把剩余数百宫禁守卫发往前线',40,'庚申，','赴之。',[('杜威','上奏请增兵'),('帝','命数百宫禁守卫赴军前')],when=dec+'庚申',place='后晋宫廷至军前',note='数百是守禁所能再调人数，不是晋军全军仅数百人。')
add('shi_orders_emergency_fodder_grain','石重贵急令河北及滑孟泽潞调刍粮五十万，严催引发骚动',40,'又诏发','鼎沸。',[('帝','下令急调刍粮并严督')],when=dec+'庚申条下',place='河北、滑州、孟州、泽州、潞州至军前',note='五十万底本没有计量单位，不补为斛、斤或车；鼎沸解释为地方骚动，不虚造叛军。')
sup('shi_orders_emergency_fodder_grain',40,j,'辛酉，詔澤潞、鄴都、邢洺、河陽運糧赴中渡，','《旧五代史》另记辛酉命泽潞、邺都、邢洺、河阳运粮至中渡。','本纪日期和范围按原文并列，不覆盖通鉴庚申条下河北等调刍粮；可能为接续调度，不强认同一道命令。',relation='adds')
add('zhang_zuo_captured_returning','杜重威派张祚等向朝廷告急，他们返军时被契丹俘获，前后消息中断',40,'辛酉，','不相通。',[('杜威','派从者告急'),('张祚','告急后返程被俘')],when=dec+'辛酉派出，返程被俘具体日未载',place='中度军前至后晋朝廷',note='辛酉为派出或来告急记日，不强定被俘也同日；其他从者未名不造人物。')
add('capital_fears_empty_guards','宿卫兵集中于行营，京城人心恐惧，不知如何应对',40,'时宿卫兵','莫知为计。',[],when=dec+'消息中断后',place='后晋京城',note='军情恐惧是当时叙述，不列虚构群体心理人数。')
add('sang_denied_audience','桑维翰因国势危急求见，石重贵在苑中驯鹰而拒见',40,'开封尹桑维翰','辞不见。',[('桑维翰','以开封尹身份求见言事'),('帝','在苑中驯鹰并拒见桑维翰')],when=dec+'军前告急期间，具体日未载',place='后晋宫苑')
add('sang_warns_jin_end','桑维翰又向执政陈说危局，未获重视，退后叹后晋将亡',40,'又诣执政',None,[('桑维翰','向执政陈说后向亲近人叹晋将亡')],when=dec+'求见被拒后',place='后晋朝廷',note='不血食解释为晋政权将亡，是其判断，不写此刻皇帝已死；执政未指名，不全加李崧冯玉参与。')
add('li_yantao_stops_shi_personal_campaign','石重贵想亲自北征，李彦韬劝阻，计划停止',41,'帝欲','谏而止。',[('帝','想亲自北征后停止'),('李彦韬','劝止石重贵亲征')],when=dec,place='后晋朝廷',note='复用后晋宣徽使李彦韬，不误用已死温韬旧名。')
add('fu_retained_jingzhoukou','石重贵留下符彦卿，让他守荆州口',41,'时符彦卿','荆州口。',[('帝','留符彦卿于后方守口'),('符彦卿','虽有行营职，奉命守荆州口')],when=dec+'壬戌重新部署前',place='荆州口',note='此荆州口为原文地名，未凭名字定位为南方荆州；坐标不补。')
add('gao_fu_defend_chanzhou','石重贵任高行周为北面都部署、符彦卿为副，共守澶州',41,'壬戌，','共戍澶州；',[('帝','任命高符共守澶州'),('高行周','任北面都部署，守澶州'),('符彦卿','任副部署，守澶州')],when=dec+'壬戌',place='澶州')
sup('gao_fu_defend_chanzhou',41,j,'壬戌，又遣高行周屯澶州，景延廣守河陽。','《旧五代史》也记壬戌高行周驻澶州，并另记符彦卿庚申驻澶州。','本句印证高行周，不由此推符的庚申部署与壬戌任副是同一道命令。')
add('jing_defends_heyang','石重贵命西京留守景延广守河阳，以壮防御声势',41,'以西京留守','张形势。',[('帝','命景延广守河阳'),('景延广','以西京留守身份守河阳')],when=dec+'壬戌',place='河阳')
sup('jing_defends_heyang',41,j,'壬戌，又遣高行周屯澶州，景延廣守河陽。','《旧五代史》同记壬戌景延广守河阳。','守军任务不代表成功击退敌军。')
add('wang_qing_requests_bridge_assault','王清请率二千步卒夺桥开路，建议全军跟进到恒州',41,'奉国都指挥使','无忧矣。”',[('王清','以奉国都指挥使身份请求率步卒开路'),('杜威','收到请求')],when=dec+'壬戌条下',place='中度至恒州',note='二千是所请前锋人数，不据此算宋彦筠部人数；桥未具名，不强当早已焚桥的原桥形制。')
add('du_sends_wang_song_assault','杜重威同意，让王清、宋彦筠进攻；王清锐战迫契丹稍退',41,'威许诺，','势小却。',[('杜威','同意出击，派王清宋彦筠进兵'),('王清','奋力进攻，迫敌稍退'),('宋彦筠','与王清一同进军')],when=dec+'壬戌条下',place='滹沱河中度战区')
add('du_refuses_main_army_support','诸将请求全军跟进，杜重威拒绝',41,'诸将请','威不许。',[('杜威','拒绝派全军跟进')],when=dec+'王清进攻时',place='中度军营',note='未具名诸将不自动列入此前九位将领。')
add('song_escapes_by_swimming','宋彦筠战败，游泳到岸边脱险后退走',41,'彦筠为契丹','因退走。',[('宋彦筠','战败后游泳脱险并退走')],when=dec+'壬戌条下',place='滹沱河战区',note='逃到岸边不等于溺死，也不补哪岸坐标。')
add('wang_fights_without_rescue','王清在河水北岸独自率部苦战，屡请救援，杜重威始终不派兵',41,'清独帅','助之。',[('王清','率部在水北力战并多次求救'),('杜威','始终未派一骑援助')],when=dec+'壬戌条下',place='滹沱河水北',note='这是行动记载，不凭拒援提前写杜已签降表。')
add('wang_urges_death_for_country','王清认为统帅不救必有异志，劝部众死报国，士卒无人退却',41,'清谓其众','莫有退者。',[('王清','向部众表达怀疑并激励死战')],when=dec+'苦战时',place='滹沱河水北',note='异志是王清当时的判断，不能替为已经查明叛变动机。')
add('wang_qing_dies_with_troops','王清及部众战至傍晚，契丹增兵后全部战死，晋军士气受挫',41,'至暮，','皆夺气。',[('王清','率部苦战至暮后战死')],when=dec+'壬戌条下，战至暮',place='滹沱河战区',note='夺气解释士气受挫；不套全部晋军同时死亡。')
sup('wang_qing_dies_with_troops',41,j,'己巳，邢州方太奏，此月六日，契丹與王師戰於中渡，王師不利，奉國都指揮使王清戰死。','《旧五代史》记方太在己巳奏报：王清于十二月六日中渡战中战死。','己巳是奏报日；六日是战日，不能把死亡改为己巳。',field='time_original')
sup('wang_qing_dies_with_troops',41,nw,'壬戌，奉國都指揮使王清及契丹戰于滹沱，敗績，死之。','《新五代史》明确记王清于壬戌滹沱战败身亡。','原文死之直接印证死亡，后面的史例评议不当新事件。')
claim('person','person_王清','death_year','王清于946年十二月战死。',41,span(41,'至暮，','士众尽死。'),'新旧本纪分别补战日与奏报，复用人物death_year档案不直接覆写。')
claim('person','person_王清','birth_place','《资治通鉴》称王清为洺州人。',41,span(41,'清，',None),'此前记曲周人，曲周属于地区内县级籍贯可能相容；保留来源各自表述，不猜具体乡里。')
add('khitan_encircles_jin_camp','契丹远距离包围晋营，内外隔绝，军粮将尽',42,'甲子，','食且尽。',[],when=dec+'甲子',place='中度晋营',note='且尽是将尽，不写已经完全无粮。')
add('du_li_song_plan_surrender','杜重威、李守贞、宋彦筠商议投降契丹',42,'杜威与','谋降契丹。',[('杜威','参与商议降契丹'),('李守贞','参与商议投降'),('宋彦筠','参与商议投降')],when=dec+'甲子条下',place='中度晋营')
add('du_seeks_reward_from_khitan','杜重威暗派亲信到契丹牙帐，索求重赏',42,'威潜遣','邀求重赏。',[('杜威','派亲信索求重赏')],when=dec+'甲子条下',place='中度晋营至契丹牙帐',note='未具名腹心不造人物。')
add('khitan_dismisses_zhao_prestige','耶律德光在诱降话中说赵延寿威望不高，恐不能称帝',42,'契丹主绐之曰：','恐不能帝中国。',[('契丹主','以赵延寿威望不足为诱降理由'),('赵延寿','在诱降说辞中受到评价')],when=dec+'甲子条下',place='契丹牙帐',note='这是耶律德光的欺骗说辞，不作赵威望客观评级，也未给赵实际帝号。')
add('khitan_promises_du_emperor','耶律德光许诺杜重威投降便让其称帝，杜重威喜而决定投降',42,'汝果降者，','遂定降计。',[('契丹主','以称帝承诺诱降'),('杜威','接受许诺并决定投降')],when=dec+'甲子条下',place='契丹牙帐及晋营',note='承诺承接上文绐之，为欺骗诱降，不能写杜重威实际成为皇帝。')
add('du_forces_generals_sign_surrender','杜重威埋伏甲兵召将，出示降表令签名，诸将惊骇却不敢反对',42,'丙寅，','唯唯听命。',[('杜威','以伏兵威压诸将签降表')],when=dec+'丙寅',place='中度晋营',note='伏甲与诸将不敢反对按史载，未名将领不逐人推为主动拥护。')
add('gao_xun_delivers_surrender','高勋奉杜重威命送降表，耶律德光赐诏接受',42,'威遣阁门使','慰纳之。',[('杜威','派使送降表'),('高勋','以阁门使身份送降表'),('契丹主','赐诏接受投降')],when=dec+'丙寅',place='晋营至契丹牙帐')
add('du_orders_army_disarm','杜重威让士卒出营列阵，再宣布求生并命卸甲，士卒痛哭',42,'是日，','声振原野。',[('杜威','让士卒列阵后卸甲，宣布求生')],when=dec+'丙寅',place='中度晋营外',note='士卒起先以为将战与后卸甲分清；无从补全军精确兵数。')
sup('du_orders_army_disarm',42,j,'壬申，始聞杜威、李守貞等以此月十日率諸軍降於契丹。','《旧五代史》在壬申收到消息时记：杜重威、李守贞等于十二月十日率军投降。','十日是投降日，壬申是朝廷得讯日；未将两者合成同一天。',field='time_original')
sup('du_orders_army_disarm',42,nw,'杜威、李守貞、張彥澤以其軍叛降于契丹。','《新五代史》概述杜重威、李守贞、张彦泽率军降契丹。','张彦泽列入该书降军概述，主段没有在签表场景点名他，不据概述添他签名。')
add('du_li_blame_shi','杜重威、李守贞向士卒宣称石重贵失德、信奸并猜忌自己',42,'威、守贞仍','切齿。',[('杜威','把败局归咎皇帝失德猜忌'),('李守贞','共同宣称皇帝失德猜忌')],when=dec+'丙寅',place='晋营外',note='宣称是其辩解，不当皇帝失德的唯一客观结论；士卒切齿不明确只指恨皇帝，不补对象。')
add('zhao_in_red_robe_comforts_troops','耶律德光派赵延寿穿赭袍慰抚降兵，并说降兵都是他的',42,'契丹主遣赵延寿','汝物也。”',[('契丹主','派赵延寿慰抚，声称降兵归赵'),('赵延寿','着赭袍到晋营慰抚')],when=dec+'丙寅降军后',place='晋营',note='彼皆汝物是耶律说辞，未因此建永久隶属关系或赵帝位。')
add('du_welcomes_zhao_red_robe','杜重威等马前迎赵延寿，杜也着赭袍示众，史书记为戏弄',42,'杜威以下','皆戏之耳。',[('杜威','马前迎谒，也被穿赭袍示众'),('赵延寿','接受降将迎谒')],when=dec+'降军后',place='晋营',note='戏之是史书评语，不把赭袍当正式皇帝册命。')
add('du_li_receive_khitan_titles','耶律德光任杜重威为太傅、李守贞为司徒',42,'以威为太傅，','为司徒。',[('杜威','被任命为太傅'),('李守贞','被任命为司徒')],when=dec+'降军后',place='契丹牙帐及晋营')
add('du_persuades_wang_zhou_surrender','杜重威引耶律德光至恒州，并劝王周投降，王周出城归降',42,'威引契丹主','周亦出降。',[('杜威','以自身已降为由劝王周'),('契丹主','被引至恒州城下'),('王周','以顺国节度使身份出降')],when=dec+'戊辰入城前',place='恒州城下')
add('khitan_enters_hengzhou','耶律德光进入恒州',42,'戊辰，','入恒州。',[('契丹主','进恒州')],when=dec+'戊辰',place='恒州')
add('wang_hui_surrenders_daizhou','契丹派兵袭代州，刺史王晖以城投降',42,'遣兵袭代州，','以城降之。',[('王晖','以代州刺史身份以城投降')],when=dec+'恒州入城条下，具体日未载',place='代州',note='王晖限定为代州刺史，未与后蜀前陵州同名人合并；不硬定也是戊辰。')
add('guo_lin_prior_defense_yizhou','郭璘此前屡守易州抵抗契丹，耶律德光曾叹受其阻挡',42,'先是契丹','所扼！”',[('郭璘','此前屡次坚守易州'),('契丹主','因进军受阻而叹郭璘')],when='946年十二月易州降前的追述，具体年月未载',year=None,place='易州',note='先是所叙历次攻守不一律定在本年十二月；不得由叹语推已吞天下。')
add('geng_induces_yizhou_surrender_kills_guo','耿崇美诱使易州守军投降，郭璘无法制止而被杀',42,'及杜威既降，','崇美所杀。',[('契丹主','派耿崇美到易州诱说'),('耿崇美','诱军投降后杀郭璘'),('郭璘','无法制止守军投降，被杀')],when=dec+'杜重威投降后，具体日未载',place='易州')
claim('person','person_郭璘','birth_place','郭璘是邢州人。',42,span(42,'璘，',None),'原文明示籍贯，不推县乡和出生年。')
add('li_yin_fang_tai_surrender','李殷、方太向契丹投降',43,'义武节度使','降于契丹。',[('李殷','以义武节度使身份投降'),('方太','以安国留后身份投降')],when=dec+'晋军降后，具体日未载',place='义武军、安国军')
add('sun_fangjian_yiwu_appointment','耶律德光任孙方简为义武节度使',43,'契丹主以孙方简','义武节度使，',[('契丹主','任命孙方简'),('孙方简','被任命为义武节度使')],when=dec+'诸将降后',place='义武军')
add('mada_anguo_appointment','耶律德光任麻答为安国节度使',43,'麻答为','安国节度使，',[('麻答','被任命为安国节度使')],when=dec+'诸将降后',place='安国军')
add('ma_chongzuo_hengzhou_admin','耶律德光让客省副使马崇祚暂掌恒州',43,'以客省副使',None,[('马崇祚','以客省副使身份暂掌恒州事')],when=dec+'诸将降后',place='恒州')
add('zhang_li_recommends_local_officials','张砺建议耶律德光用中原人任将相，警告用亲近北人会失人心；意见未被采纳',44,'契丹翰林承旨','契丹主不从。',[('张砺','以翰林承旨、吏部尚书身份建议官员选择'),('契丹主','没有采纳建议')],when=dec+'恒州降后南行前',place='契丹朝廷',note='中国人按本段语境指中原人，不套现代国籍；建议和警告不是已任职名单或后来的失国结果。')
sup('zhang_li_recommends_local_officials',44,lz,'礪奏曰：「今大遼始得中國，宜以中國人治之，不可專用國人及左右近習。茍政令乖失，則人心不服，雖得之亦將失之。」上不聽。','《辽史》也记张砺提出应任用中原人并未被采纳的建议，但传记将其放在进入汴州后。','主书叙在南进大梁前，辽传入汴后；可能是反复谏议或叙次不同，保留时序疑问，不强称同日同一次发言。',relation='conflicts')
add('khitan_du_march_south','耶律德光由邢州、相州南行，杜重威率降兵随行',44,'引兵自邢','降兵以从。',[('契丹主','由邢相南行'),('杜威','率已降晋军跟随')],when=dec,place='邢州、相州南行')
add('zhang_yanze_sent_take_daliang','耶律德光派张彦泽率二千骑先取大梁，并要求安抚吏民',44,'遣张彦泽','抚安吏民，',[('张彦泽','奉命率二千骑先取大梁并安抚')],when=dec+'南行时',place='邢相军前至大梁',note='任务有安抚，但后续是否遵行须继续原文；此时尚不提前写已经破城。')
add('fu_zhu_er_campaign_monitor','契丹通事傅住儿任先取大梁部队的都监',44,'以通事',None,[('傅住兒','以通事身份任都监')],when=dec+'派张彦泽先取大梁时',place='先取大梁部队',note='傅住兒展示规范为傅住儿，保存原字及别名。')
reviews={39:'李谷密奏建议与关勋送奏分开；高行舟据同卷高行周及旧本纪校读。旧本纪本日据通鉴补的注文不是独立证据。',40:'己未帝得讯非驻军日，庚申再调数百卫兵不作全军人数。刍粮五十万无单位不补斛，旧辛酉调粮另事并列。张祚返被俘日未定；桑求见拒及向执政陈说不凭未名指代虚添。',41:'亲征提议受阻，荆州口不套南方荆州坐标。壬戌后方部署与前锋二千请求分别，王宋行动、杜拒全军救、宋游退、王苦战死亡按次序。旧己巳奏六日战、新壬戌战均为战报/战日分层；王籍洺州与此前曲周可为地区县层级，保留。',42:'甲子围粮断、降议索赏、称帝骗诺，丙寅伏兵迫签与释甲、赵杜赭袍非帝册、太傅司徒实职分开。戊辰入恒州后代州降未强同日。王晖代州与蜀陵州同名待核，郭前易州坚守日期未定和降后死分别。',43:'李殷方太降与孙麻马新任分别，沿已有主体，不按官位同名另造人。',44:'张砺建议主书南进前、辽传入汴后时序差保留；不提前录其后逼害死亡。二千骑先取大梁是部署、安抚是任务，不提前判实际战况。傅住兒简体展示及别名。'}
assert not (P/'publication.json').exists()
for n in range(39,45):
 assert ledger[n-1]['status']=='pending' or (ledger[n-1]['status']=='reviewed' and ledger[n-1]['batch_key']==B['batch_key'])
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for f,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
coverage=dict(book='资治通鉴',volume=285,year=946,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(39,45)],next_paragraph=Q[45]['id'],next_volume=285,next_year=946,supplements=supplements,excluded_non_body=[],coverage='卷285原69—74行连续六段，发布后946年累计44/56，余12段。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(39,45)],source_contexts=[dict(source_key=main_sources[0],note='续录39—42段开头，原自动片段结束在绐之话中；下面来源接续原字，不用不完整片段推完整含义。'),dict(source_key=main_sources[1],note='接42段后半，连续原文校核完整降营过程。'),dict(source_key=main_sources[2],note='只录43—44段，皇甫遇死、京城入兵与降表在下一批。'),dict(source_key=j,note='只用本纪正文補日期及部署，据通鉴注文不算独立证据；后续京城事实不提前。'),dict(source_key=lz,note='只补谏议及时间异说，后续逼害未提前。')],source_issues_review='王晖同名、荆州口定位、刍粮计量单位及张砺谏议时序保留待核；战日奏报日分清，帝位骗诺未当事实。',plain_language_review='首次逐条检查展示字段及事实说明，主体明确，时间和行动先后、书证依赖、建议执行及评价分别；原文摘录逐字保持。')
(P/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
