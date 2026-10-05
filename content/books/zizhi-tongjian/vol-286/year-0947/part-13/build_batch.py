# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 286, year 947 paragraphs 69–75."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q)==list(range(1,93))
COMMIT='df264aefc4373c3f610c2f0bb525ac26f65cd07c'
specs=[(d.name,d,COMMIT,'司马光等' if d.name.startswith('tongjian') else '薛居正等' if d.name.startswith('jiuwudaishi') else '脱脱等' if d.name.startswith('liaoshi') else '脱脱等' if d.name.startswith('songshi') else '欧阳修') for d in sorted((P/'sources/library').iterdir()) if d.name!='songshi-484-li-jun-name']
for key in ['tongjian-286-947-return-april','jiuwudaishi-099-april-appointments']:
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
main_sources = ['tongjian-286-947-return-april']
B = {'format_version': 1, 'batch_key': 'zztj-v286-y0947-p069-p075',
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
lines = (ROOT / 'resources/derived/tongjian/286.txt').read_text().splitlines()
for n in range(69, 76):
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
        citation = f'卷286·天福十二年（947年四月及追述）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_286_0947_13_{len(B["claims"])+1:04d}'
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

def event(code, title, n, quote, actors, when=None, note='', year=947, place='五代十国', source=None, stable_key=None, description=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='947年，具体月日未载'
    when=when.replace('主书','《资治通鉴》').replace('旧本纪','《旧五代史》本纪').replace('新本纪','《新五代史》本纪').replace('新史','《新五代史》').replace('旧史','《旧五代史》')
    key = 'event_zztj_286_0947_' + code
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
        edge = 'participation_zztj_286_0947_' + code + '_' + pk
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
        row=dict(key=f'relationship_zztj_286_0947_{pa}_{kind}_{pb}',person_a_key=pa,person_b_key=pb,
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
ALIASES.update({'帝':'刘知远','契丹主':'耶律德光','魏国夫人李氏':'李氏（刘知远妻）','燕王':'赵延寿','折从阮':'折从远','谦':'郑廉'})
NEW_ALIASES={'苏逢吉':['蘇逢吉'],'苏禹珪':['蘇禹珪'],'刘铢':['劉銖'],'郑廉':['鄭廉','郑谦','鄭謙'],'阎万进':['閻萬進'],'武行德':[],'武行友':[]}
NEW_DESCRIPTIONS={
'苏逢吉':'长安人，任河东节度判官。947年刘知远任命他为中书侍郎、同平章事。具体生卒年尚未录入。',
'苏禹珪':'密州人，任河东观察判官。947年刘知远任命他为中书侍郎、同平章事。具体生卒年尚未录入。',
'刘铢':'陕地人，任河东左都押牙。947年刘知远任命他为河阳节度使。具体生卒年尚未录入。',
'郑廉':'岢岚军使。947年获任忻州刺史，兼忻、代二州义军都部署。《旧五代史》同职同事作郑谦，《资治通鉴》后句也用谦字，保留异写；所领节度军号存在差异。生卒年未载。',
'阎万进':'并州人，任沿河巡检使。947年获任岚州刺史，兼岚、宪二州义军都制置使。所领节度军号各书有差异。生卒年未载。',
'武行德':'并州榆次人。947年受契丹命运送晋朝铠甲兵器，途中与军士夺取兵器、杀契丹监军，继而占据河阳。生卒年尚未录入。',
'武行友':'武行德的弟弟。947年受武行德派遣，携蜡封表章经小路前往晋阳。生卒年未载。'}
a='jiuwudaishi-099-april-appointments';j='jiuwudaishi-099-heyang-april';ss='songshi-252-wu-xingde-heyang';origin='songshi-252-wu-xingde-origin'
t='947年四月，具体日未载'
add('li_empress_established','刘知远立魏国夫人李氏为皇后',69,'癸亥，',None,[('帝','册立李氏为皇后'),('魏国夫人李氏','从魏国夫人获立为皇后')],when='947年四月癸亥',place='后汉朝廷',note='复用已录入的刘知远妻李氏，不与后唐、后晋同姓后妃合并。')
sup('li_empress_established',69,a,'癸亥，冊魏國夫人李氏為皇后。','《旧五代史》同在四月癸亥记册立魏国夫人李氏为皇后。','册立日期按原纪年，未自行换算公历。')
add('khitan_blames_zhao_and_zhang','耶律德光见沿途城邑荒废，指责赵延寿和张砺造成中原残破',70,'契丹主',None,[('契丹主','将中原残破归咎于赵延寿和张砺'),('燕王','被耶律德光指责为中原残破的责任者'),('张砺','被耶律德光当面指责也有责任')],when=t,place='契丹北归沿途，具体地点未载',note='这是耶律德光的归责言论，不是已核实的战争损失因果；燕王指赵延寿。',description='耶律德光看到所过城邑荒废，对群臣说中原变成这样全是燕王赵延寿的罪责，又对张砺说他也有责任。此处保留耶律德光的说法，不将其作为唯一历史解释。')
add('su_fengji_chancellor','刘知远任命苏逢吉为中书侍郎、同平章事',71,'甲子，','同平章事。',[('帝','任命苏逢吉为宰相'),('苏逢吉','从河东节度判官获任中书侍郎、同平章事')],when='947年四月甲子',place='后汉朝廷',note='原句并任二苏，各人授官分别记录；长安为苏逢吉籍贯。')
add('su_yugui_chancellor','刘知远任命苏禹珪为中书侍郎、同平章事',71,'甲子，',None,[('帝','任命苏禹珪为宰相'),('苏禹珪','从河东观察判官获任中书侍郎、同平章事')],when='947年四月甲子',place='后汉朝廷',note='密州为苏禹珪籍贯，不是这次授官所在地。')
sup('su_fengji_chancellor',71,a,'以河東節度判官蘇逢吉為中書侍郎、同平章事、集賢殿大學士','《旧五代史》同记苏逢吉任中书侍郎、同平章事，并兼集贤殿大学士。','补书甲子条下有大学士职衔，作为补充，不擅加至主书原文。',relation='adds')
sup('su_yugui_chancellor',71,a,'以河東觀察判官蘇禹珪為中書侍郎、同平章事。','《旧五代史》同记苏禹珪任中书侍郎、同平章事。','两书官职及原职相合。')
add('zhe_congyuan_visits_renames','折从远入朝，改名折从阮',72,'振武节度使','更名从阮，',[('折从远','以振武节度使、府州团练使身份入朝并改名')],when='947年四月甲子条下，具体日未载',place='府州至后汉朝廷',note='复用折从远已有主体及从阮别名，不新建两个人。')
add('fuzhou_yongan_established','刘知远在府州设永安军，任折从阮为节度使',72,'置永安军','以从阮为节度使。',[('帝','在府州设置永安军并任折从阮节度使'),('折从阮','获任永安军节度使')],when='947年四月甲子条下；《旧五代史》系甲子',place='府州',note='本段府州在北方，与此前福州救援战的福州分开。')
sup('fuzhou_yongan_established',72,a,'升府州為節鎮，加永安軍額。以振武節度使、府州團練使折從阮為永安軍節度使，行府州刺史、檢校太尉','《旧五代史》记升府州为节镇、加永安军号，任折从阮为永安军节度使。','补书同时列行府州刺史、检校太尉，保留独立引文。',relation='adds')
add('liu_zhu_heyang_appointment','刘知远任命刘铢为河阳节度使',72,'又以河东',None,[('帝','任命刘铢为河阳节度使'),('刘铢','从河东左都押牙获任河阳节度使')],when='947年四月甲子条下；《旧五代史》系甲子',place='后汉朝廷、河阳',note='任命不代表刘铢已经进驻河阳，不与同段后续武行德占城冲突。陕为籍贯。')
sup('liu_zhu_heyang_appointment',72,a,'以北京隨使、左都押衙劉銖為河陽節度使','《旧五代史》同记刘铢任河阳节度使。','补书北京随使与主书河东左都押牙职衔分别保留，不据此补其实际接管城池。')
add('geng_chongmei_plans_luzhou','耿崇美屯驻泽州，准备进攻潞州',73,'契丹昭义','将攻潞州。',[('耿崇美','以契丹昭义节度使身份屯泽州，准备攻潞州')],when='947年四月乙丑之前，具体日未载',place='泽州；潞州（拟攻）',note='将攻表示准备，不写成已经攻陷潞州。')
add('shi_hongzhao_ordered_to_relieve_luzhou','刘知远命史弘肇率步骑一万人救援潞州',73,'乙丑，',None,[('帝','下令救援潞州'),('史弘肇','奉命率一万步骑救援')],when='947年四月乙丑',place='后汉至潞州',note='一万人是本次奉命出援的规模，不是全后汉兵力；本句是命令。')
sup('shi_hongzhao_ordered_to_relieve_luzhou',73,a,'乙丑，遣史宏肇率兵一萬人趨潞州。','《旧五代史》同记乙丑遣史宏肇率一万人趋潞州。','弘、宏沿已知同一人物，遣兵不补本日已到达。')
add('wang_shouen_zhaoyi_appointment','刘知远任命王守恩为昭义节度使',74,'丙寅，','王守恩为昭义节度使，',[('帝','任命王守恩为昭义节度使'),('王守恩','获任昭义节度使')],when='947年四月丙寅',place='潞州昭义军',note='王守恩前批夺取潞州与本次正式授官分开。')
sup('wang_shouen_zhaoyi_appointment',74,a,'丙寅，以權知潞州軍州事、左驍衛大將軍王守恩為潞州節度使、檢校太保','《旧五代史》同在丙寅记王守恩任潞州节度使。','潞州州名与昭义军号保留各书表达。')
add('gao_yunquan_zhangwu_appointment','刘知远任命高允权为彰武节度使',74,'高允权','为彰武节度使，',[('帝','任命高允权为彰武节度使'),('高允权','获任彰武节度使')],when='947年四月丙寅',place='延州彰武军',note='延州归附与此处正式任命是不同动作。')
sup('gao_yunquan_zhangwu_appointment',74,a,'以權點檢延州軍州事高允權為延州節度使、檢校太保','《旧五代史》同记高允权任延州节度使。','同主语、原任职与州镇支持同一次授职。')
add('zheng_lian_xinzhou_appointment','刘知远任命郑廉为忻州刺史，领彰国节度使兼忻代义军都部署',74,'又以岢岚','忻、代二州义军都部署。',[('帝','任命郑廉管理忻州及忻代义军'),('郑廉','从岢岚军使任忻州刺史，并领节度职、义军都部署')],when='947年四月丙寅',place='岢岚、忻州、代州',note='主书前句郑廉、后句谦，旧史同职同事作郑谦，登记异写；彰国与补书应州节度职差异保留。')
sup('zheng_lian_xinzhou_appointment',74,a,'以岢嵐軍使鄭謙為忻州刺史，遙領應州節度使，充忻、代二州義軍都部署。','《旧五代史》记郑谦任忻州刺史、遥领应州节度使，充忻代义军都部署。','主书彰国、补书应州写法不同，姓名廉、谦异写并列保留，不能默改原字或军号。',relation='conflicts')
add('yan_wanjin_lanzhou_appointment','刘知远任命阎万进为岚州刺史，领振武节度使兼岚宪义军都制置使',74,'丁卯，','岚、宪二州义军都制置使。',[('帝','任命阎万进管理岚州及岚宪义军'),('阎万进','从沿河巡检使任岚州刺史，并领节度职、义军都制置使')],when='947年四月丁卯',place='岚州、宪州',note='阎万进为并州人；主书原职作缘河，补书沿河，原文保留字形。')
sup('yan_wanjin_lanzhou_appointment',74,j,'丁卯，以河東都巡館驛、沿河巡檢使閻萬進為嵐州刺史，領朔州節度使，充嵐、憲二州義軍都制置。','《旧五代史》同日记阎万进任岚州刺史，但所领节度职写作朔州节度使。','主书振武、补书朔州分别保留，未用地名替换来消除差异。',relation='conflicts')
add('liu_uses_north_south_deployments','刘知远得知契丹北归，安排史弘肇先行、郑廉与阎万进从北方分散契丹兵势',74,'帝闻契丹',None,[('帝','谋划经营河南，以南北部署分散契丹兵势'),('史弘肇','被安排作经略河南的前驱'),('谦','受遣往北方分散契丹兵势'),('阎万进','受遣往北方分散契丹兵势')],when='947年四月任官条后的形势说明，具体日未载',place='河南、北方（部署方向）',note='原文谦万进按前后文为郑谦、阎万进两人，谦对应前句郑廉异写。欲经略是意图，不表示整个河南已受控或分兵策略已成功。')
add('wu_xingde_ordered_transport_armor','契丹安排数十艘船运晋朝铠甲兵器，命武行德率千余军士护送北运',75,'契丹主','部送之。',[('契丹主','命武行德护送晋朝兵器北运'),('武行德','受命率千余军士护送')],when='947年契丹从大梁北归前后，具体日未载',place='汴州、汴河至北方（拟运路线）',note='将自汴溯河归其国为预定运输路线，不等于器械已到契丹；千余是护送士卒数。')
sup('wu_xingde_ordered_transport_armor',75,j,'初，契丹主將發東京，船載武庫兵仗，自汴浮河，欲置之於北地，遣奉國都虞候武行德部送，與軍士千餘人並家屬俱行。','《旧五代史》记武行德受命护送兵器，千余军士与家属同行，职衔作奉国都虞候。','主书宁国与补书奉国职衔差异保留；家属同行只据此引文，不把人数加算进千余军士。',relation='conflicts')
sup('wu_xingde_ordered_transport_armor',75,ss,'晉天福初，授奉國都頭，遷指揮使，改控鶴指揮使、寧國軍都虞候。','《宋史》武行德传列其先后任奉国、控鹤及宁国军职务。','传记先后职务有助回查两书宁国、奉国差异，但未据此认定同一时点兼任两职。',relation='adds')
pk=people['武行德']
claim('person',pk,'description','武行德是并州榆次人。',75,'武行德，幷州榆次人','《宋史》传首与主书榆次籍贯相合；未把传中早年相遇事件定到947年。',source=origin,relation='adds')
add('wu_proposes_defection_at_heyin','武行德在河阴劝军士摆脱契丹控制、共守河阳，等候局势明确再归附',75,'至河阴，','众以为然。',[('武行德','劝军士摆脱契丹控制、共守河阳')],when='947年北运途中到河阴时，具体日未载',place='河阴',note='虏势不能久留是武行德的判断，天命所归是等待归附对象的主张，不提前写成已向刘知远归附。')
add('wu_seizes_armor_kills_monitor','武行德将铠甲兵器交给军士，与他们杀死契丹监军使',75,'行德即','相与杀契丹监军使。',[('武行德','把兵器交军士，并与军士杀契丹监军')],when='947年河阴军士同意后，具体日未载',place='河阴',note='监军未名，不猜为契丹其他已知将领。')
sup('wu_seizes_armor_kills_monitor',75,ss,'行德即殺契丹監使，分授器甲','《宋史》同记武行德杀契丹监使并分发器甲。','两书叙述器甲分发与杀监使的顺序不同，不硬推精确先后时刻。')
add('cui_escorts_geng_luzhou','崔廷勋率兵护送耿崇美往潞州',75,'会契丹河阳','以兵送耿崇美之潞州，',[('崔廷勋','以河阳节度使身份率兵送耿崇美往潞州'),('耿崇美','受兵护送往潞州')],when='947年武行德抵河阳前后，具体日未载',place='河阳至潞州',note='会表示适逢，不将护送行动强定为此前乙丑的救援日。')
add('wu_takes_heyang','武行德乘河阳守军外出占城，被推为河阳都部署',75,'行德遂','众推行德为河阳都部署。',[('武行德','占据河阳并获军众推举为都部署')],when='947年四月，具体占城日未载',place='河阳',note='主书记乘虚入据；补书记与崔廷勋交战，各自保留，不能拼成同日无战且交战的确定经过。')
sup('wu_takes_heyang',75,j,'河陽偽命節度使崔廷勛率兵拒之，兵敗，行德等追躡之，廷勛棄城而遁，行德因據其城。','《旧五代史》记崔廷勋出兵抵抗、败退弃城，武行德追击后占河阳。','与主书乘虚占城的过程不同，登记异说，不新增重复占城事件。',relation='conflicts')
sup('wu_takes_heyang',75,ss,'契丹節度使崔廷勳出兵來拒，行德麾眾逆擊，自旦及午殊死戰，廷勳大敗，棄城走。行德遂據河陽','《宋史》也记武行德与崔廷勋交战，从早晨至午，崔廷勋败退后武行德占城。','该书与旧史同为交战说，不能因两书相同便断言已独立核实；与主书并列。',relation='conflicts')
add('wu_sends_brother_jinyang','武行德派弟弟武行友携蜡封表章，经小路前往晋阳',75,'行德遣弟',None,[('武行德','派弟弟携表章往晋阳'),('武行友','受派携蜡封表章经小路去晋阳')],when='947年四月占据河阳后，具体启程日未载',place='河阳至晋阳',note='本句是派遣启程，武行友抵达日期见后续戊辰段，本批不提前当作已经到达；表章具体全文未载。')
relationship('武行德','武行友','兄长',75,span(75,'行德遣弟',None),'弟明确长幼，方向表示武行德是武行友的兄长。')
reviews={69:'李氏复用刘知远妻，癸亥册立与前批劝谏身份分开。',70:'责赵延寿、张砺是耶律德光言论，不确认史实唯一因果。',71:'两位宰相分别授职，籍贯不作为任命地点；旧史大学士补证独立保留。',72:'折更名沿已有key；北方府州与福州不同；刘铢授河阳节度不证明已经入城。',73:'耿屯兵拟攻与乙丑救援诏令分清，万人是出援规模，未补攻取结果。',74:'郑廉与郑谦、原文谦万进经同职同事识别；军号与朔州、振武等写法分别保留；经略及分兵是意图。',75:'北运计划、河阴劝议、分兵器杀监军、崔送耿、占城、遣弟分录。主书乘虚与旧史宋史交战并列；人数不加家属；派弟不等于到达。'}
assert not (P/'publication.json').exists()
for n in range(69,76):
 assert ledger[n-1]['status'] in ('pending','reviewed')
 ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status='reviewed',review=reviews[n])
for path,data in [(P/'content-batch.json',B),(P/'reused-keys.json',sorted(reused)),(YEAR/'paragraphs.json',ledger)]:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
c=dict(book='资治通鉴',volume=286,year=947,primary_source_keys=main_sources,primary_source_key=main_sources[0],paragraphs=[Q[n]['id'] for n in range(69,76)],next_paragraph=Q[76]['id'],next_volume=286,next_year=947,supplements=supplements,excluded_non_body=[],coverage='卷286原74—80行连续七段，累计75/92，947年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(69,76)],source_issues_review='郑廉谦同事异写；地方军号与武行德军职差异并列；占河阳乘虚与交战说保留，宋史非单独确证；全书范围未完成。',plain_language_review='首次逐条核对全部人物、事件、参与、关系、出处和事实说明，明确主语、判断言论与行动，区分官任、实际入城、启程及到达，引用底本字形保留。')
(P/'coverage.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
assert len({x['key'] for x in B['person_events']})==len(B['person_events'])
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
