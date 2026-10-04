# -*- coding: utf-8 -*-
"""Curate consecutive Tongjian volume 279, year 935 paragraphs 12–20."""
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
 specs.append((directory.name,directory,'0a39d9d7','司马光、胡三省（注）' if directory.name.endswith('-collation') else '司马光等' if directory.name.startswith('tongjian') else '薛居正等' if directory.name.startswith('jiuwudaishi') else '脱脱等' if directory.name.startswith('songshi') else '欧阳修'))

specs += [
 ('tongjian-279-934-year-end',YEAR.parent/'year-0934/part-10/sources/library/tongjian-279-934-year-end','82c9d42c','司马光等'),
 ('xinwudaishi-061-jinling-fire',YEAR.parent/'year-0934/part-01/sources/library/xinwudaishi-061-jinling-fire','570df7a6','欧阳修'),
 ('jiuwudaishi-047-935-february',YEAR/'part-01/sources/library/jiuwudaishi-047-935-february','104a22bf','薛居正等')]

sources = {key: path for key, path, _, _ in specs}
main_sources = ['tongjian-279-934-year-end','tongjian-279-935-middle']
B = {'format_version': 1, 'batch_key': 'zztj-v279-y0935-p012-p020',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    labels={'xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
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
for n in range(12, 21):
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
for name,extra in [('杨檀',['杨光远','楊光遠']),('刘延朗',['刘延郎','劉延郎'])]:
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
    labels={'xinwudaishi-016-liu-yanhao':'卷16·废帝皇后刘氏传附刘延皓','songshi-269-yang-zhaojian-family':'卷269·杨昭俭传','xinwudaishi-015-cao-princess':'卷15·明宗家人传·曹氏'}
    if source in labels:record=dict(record,citation='《'+record['book']+'》'+labels[source]+'，段落 '+record['id']+'；已核上下文及传主，纸本及异文待核。')
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        month = '三月条下' if n<=13 else '四月条下' if n==14 else '五月条下' if n<=16 else '六月条下及附载追叙'
        citation = f'卷279·清泰二年（935；{month}）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_279_0935_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

ALIASES={'帝':'李从珂','吴主':'杨溥','徐知诰':'李昪','景迁':'徐景迁','宋子嵩':'宋齐丘','皇后':'刘氏（李从珂后）','刘延郎':'刘延朗','曹太后':'曹氏（李嗣源后）','晋国长公主':'永宁公主（石敬瑭妻）','王振':'王振（吴史官）','李晖':'李晖（挟马都将）'}
NEW_ALIASES={'史在德':[],'刘涛':['劉濤'],'杨昭俭':['楊昭儉'],'杨嗣复':['楊嗣復'],'毋昭裔':[],'刘延皓':['劉延皓'],'王振（吴史官）':['王振（吳史官）'],'赵延乂':['趙延乂'],'段希尧':['段希堯'],'李晖（挟马都将）':['李暉（挾馬都將）','李晖（忻州挟马都将）']}

def person(name,n,role,quote,source=None):
    name=ALIASES.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        assert name in NEW_ALIASES,('unreviewed new identity',name)
        row=dict(key='person_'+name,name=name,aliases=NEW_ALIASES[name],era='唐' if name=='杨嗣复' else '五代十国',birth_year=None,death_year=None,description=f'本批《资治通鉴》与二十四史所见人物：{name}，{role}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n,quote,'核对同名、职务及行动后识别主体；展示简体，摘录保留原字。',source=source)
    return row['key']

def event(code, title, n, quote, actors, when=None, note='', year=935, place='五代十国', source=None, stable_key=None):
    assert quote in (sources[source]/'source.txt').read_text() if source else quote in Q[n]['text'], (n, quote)
    if when is None:when='935年'+('三月' if n<=13 else '四月' if n==14 else '五月' if n<=16 else '六月')+'条下；确日未独载'
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
E['petition']=ev('shi_zaide_petitions_examinations','史在德上书批评文武官员，建议逐一考核并按能力黜陟',12,'太常丞史在德，','黜陟能否。',[('史在德','太常丞、提出考核与黜陟建议者')],note='狂狷及历诋为史家叙述，上书所称官员无能不能当全体官员的已证事实；建议不是已经举行考试。')
E['punish_request']=ev('lu_liu_yang_seek_shi_punishment','卢文纪、刘涛、杨昭俭等请求处罚史在德',12,'执政及朝士大怒，','皆请加罪。',[('卢文纪','请加罪者'),('刘涛','补阙、请加罪者'),('杨昭俭','补阙、请加罪者')],note='请求不等于已执行刑罚；主列三人和等，未名余官不造主体。旧记请辨可否宣行与中书驳奏另保过程。')
E['ma_draft']=ev('congke_asks_ma_draft_edict','李从珂以开放言路为由，命马胤孙草诏表明意见',12,'帝谓学士马胤孙','宣朕意。”',[('帝','主张开言路、命草诏者'),('马胤孙','学士、受命草诏者')],note='记录帝所述理由与委派，不能以一句即断所有言论自由制度已实施；马胤孙沿马裔孙等已有别名。')
E['edict']=ev('congke_edict_does_not_punish_shi','李从珂下诏援引魏征旧事，表示不应因史在德进言加罪',12,'乃下诏，','安可责也！”',[('帝','发布诏令者'),('史在德','诏中被宽免责罚者')],note='魏征、皇甫德参为诏令所引唐旧典，本批不把旧典改为935事件或新建二人参与本诏；引诏为政治表达，不断言疏中所有批评属实。')
claim('event',E['petition'],'description','旧末帝纪保存上疏大意：武人考试武艺与权谋，文官由宰臣面试，能者进用、无才者降职。',12,'居下位有將才者便拔為大將，居上位無將略者移之下軍。其東班臣僚，請內出策題，下中書令宰臣麵試。如下位有大才者便拔居大位，處大位無大才者即移之下僚。','旧以其略、大约标明摘要，不是完整疏全文；建议中的等级调整不当已经执行的任免。',source='jiuwudaishi-047-shi-zaide-petition',relation='corroborates')
claim('event',E['ma_draft'],'description','旧末帝纪也记帝召马裔孙，命代草诏勿加史在德之罪。',12,'帝召學士馬裔孫謂曰：「史在德語太凶，其實難容。朕初臨天下，須開言路，若朝士以言獲罪，誰敢言者！爾代朕作詔，勿加在德之罪。」','马裔孙沿已核马胤孙；旧帝先评语太凶与主省略分别保，未当史在德罪已执行。',source='jiuwudaishi-047-shi-zaide-petition',relation='corroborates')
claim('event',E['punish_request'],'description','旧纪称刘涛、杨昭俭等请出疏辨可否宣行，中书又驳其错误。',12,'故諫官劉濤、楊昭儉等上疏，請出在德疏，辨可否宣行，中書覆奏亦駁其錯誤。','与主请加罪的概括层次不同，保具体奏议动作，不称旧句逐字就是处罚申请。',source='jiuwudaishi-047-shi-zaide-petition')
claim('event',E['edict'],'description','旧纪所载诏书说明已宽史在德之罪并停止相关处分的宣行。',12,'因覽文貞之言，遂寬在德之罪，已令停寢，不遣宣行。','文贞为魏征；停止处分与已经刑罚后赦免不同，不把旧诏先前罪措辞自动当执行。',source='jiuwudaishi-047-shi-zaide-edict',relation='corroborates')
relationship('杨嗣复','杨昭俭','曾祖父',12,'昭俭，嗣复之曾孙也。','父系曾祖孙依明确曾孙，补杨姓据杨昭俭及宋传家系；A是B曾祖父，不拆出未知中间两代。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','宋杨昭俭传也记其曾祖嗣复曾任唐门下侍郎、平章事、吏部尚书。',12,'曾祖嗣復，唐門下侍郎、平章事、吏部尚書。','宋家系承杨昭俭传首，印证曾祖关系，官职不当935新任。',source='songshi-269-yang-zhaojian-family',relation='corroborates')
claim('person',people['杨昭俭'],'description','宋杨昭俭传记其字仲宝，京兆长安人。',12,'楊昭儉，字仲寶，京兆長安人。','新人物以原传首核同人；籍贯不当出生坐标，未扩录以后各朝历官。',source='songshi-269-yang-zhaojian-family')
E['qian_office']=ev('xu_jingqian_chancellor_left_right_armies','吴加徐景迁同平章事、知左右军事',13,'吴加徐景迁','知左右军事；',[('景迁','同平章事知左右军事获加者'),('吴主','吴主、加职者')],place='吴',note='承三月条，吴主沿杨溥；与934左仆射参政事另一期命，不合为934已加同平章事。')
claim('event',E['qian_office'],'time_original','新吴世家把景迁太保、平章事与王令谋等执政记在天祚六年一段。',13,'以其子景遷為太保、平章事，與令謀等執政。','新压缩时序与主934十一月、935三月分次记不同，沿既有争议并列原文，不当本次三月的独立确日。',source='xinwudaishi-061-jinling-fire',relation='conflicts')
ev('xu_orders_chen_jue_assist_jingqian','徐知诰命尚书郎陈觉辅佐徐景迁',13,'徐知诰令尚书郎','辅之，',[('徐知诰','命辅佐者'),('陈觉','尚书郎、受命辅佐者'),('景迁','受辅佐者')],place='吴',note='职掌命令本段明示；不编陈具体到任日或长期主属关系。')
ev('xu_recalls_disagreements_with_song','徐知诰向陈觉回忆年轻时与宋齐丘反复争论、挽留其出走的往事',13,'谓觉曰：','止之。',[('徐知诰','向陈觉叙旧者'),('陈觉','听叙者')],when='935年三月命辅佐景迁时的谈话；所述争论属未具年往事',place='吴',note='事件年是当前谈话，所叙与宋子嵩争论及秦淮门出走不能按935实际发生；宋是谈话中被提及者，不建在场参与边。')
claim('person',person('宋子嵩',13,'被徐知诰在谈话中回忆者',span(13,'吾少时','止之。')),'description','徐知诰在本段谈话中回忆与宋齐丘年轻时相互辩难。',13,span(13,'吾少时','止之。'),'宋子嵩沿既有宋齐丘，姓名字同人已有史证；只是被述者，不表示此次在陈觉面前参与谈话。')
ev('xu_explains_guidance_for_young_jingqian','徐知诰称自己尚未通晓时事，因景迁年少，请陈觉教导',13,'吾今老矣，','诲之耳。”',[('徐知诰','说明安排辅佐缘由者'),('陈觉','被请教导者')],place='吴',note='吾子为礼貌称呼陈觉，不建父子关系；景迁年少未给岁数，不填生年。')
E['wu']=ev('wu_zhaoyi_shu_chancellor','四月庚午毋昭裔由御史中丞任蜀中书侍郎、同平章事',14,'夏，四月，庚午，','同平章事。',[('毋昭裔','龙门人、原御史中丞、获任宰辅者')],when='935年四月庚午',place='蜀',note='龙门为史载籍贯不填现代县或坐标；毋姓不转为母姓，蜀主孟昶身份已知但本句无个人下令动作不强造参与。')
E['han']=ev('han_zhaoyin_chancellor_appointment','四月癸未韩昭胤加中书侍郎、同平章事',14,'癸未，','中书侍郎、同平章事。',[('韩昭胤','枢密使刑部尚书、获加宰辅衔者'),('帝','加职者')],when='935年四月癸未',note='主既刑部尚书、旧新兼兵部尚书的官衔写法分列，不把旧裔字当不同人。')
claim('event',E['han'],'description','旧末帝纪四月条记韩昭裔任中书侍郎兼兵部尚书、平章事。',14,'以樞密使韓昭裔為中書侍郎兼兵部尚書、平章事。','旧本日条承癸未；韩昭裔沿已应用韩昭胤别名。主原刑部身份、旧兼兵部的新衔分别保，不涂改。',source='jiuwudaishi-047-935-april',relation='corroborates')
E['yanhao']=ev('liu_yanhao_shumi_justice','四月辛卯刘延皓任刑部尚书并充枢密使',14,'辛卯。','充枢密使。',[('刘延皓','宣徽南院使、刑部尚书枢密使获任者'),('帝','任命者')],when='935年四月辛卯',note='主辛卯后的句号仍是同一任命，不跳句；新五月辛卯同人同职月份异说，不另建两次任命。')
claim('event',E['yanhao'],'description','旧末帝纪四月辛卯同记刘延皓由宣徽南院使任刑部尚书、枢密使。',14,'辛卯，以宣徽南院使劉延皓為刑部尚書，充樞密使；','支持主四月日与官；不把新另一月直接覆主。',source='jiuwudaishi-047-935-april',relation='corroborates')
claim('event',E['yanhao'],'time_original','新废帝纪把刘延皓任枢密使记为夏五月辛卯。',14,'夏五月辛卯，宣徽南院使劉延皓為樞密使。','主与旧四月、新五月月份不同，同职同人作为异说，不自行校改月份或换算公历。',source='xinwudaishi-007-935-liu-appointment',relation='conflicts')
relationship('皇后','刘延皓','姐姐',14,'延皓，皇后之弟也。','皇后为既有李从珂刘后，弟字明示长幼；A是B姐姐，不反建弟弟重复边；不能由刘延郎同姓推其也是皇后弟。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新废帝刘皇后传也明示刘延皓为其弟。',14,'其弟延皓，少事廢帝為牙將，','其承上一段废帝皇后刘氏，传首上下文作为context核；只取姐弟，不把后面的936乱事提前录入。',source='xinwudaishi-016-liu-yanhao',relation='corroborates')
claim('event',E['yanhao'],'description','新刘皇后传附记刘延皓清泰二年任枢密使、天雄军节度使。',14,'清泰二年，為樞密使、天雄軍節度使。','新将本年两期职务压缩，当前只支持枢密年，本年七月天雄尚未轮到录入；不能说四月同时两官。',source='xinwudaishi-016-liu-yanhao',relation='corroborates')
E['yanlang']=ev('liu_yanlang_north_xuanhui_shumi_deputy','四月癸巳刘延朗任左领军卫上将军、宣徽北院使兼枢密副使',14,'癸巳，','兼枢密副使。',[('刘延郎','原左领军卫大将军、新本卫上将军与宣徽北院使兼枢密副使者'),('帝','任命者')],when='935年四月癸巳',note='主延郎沿已有刘延朗，旧同一组官命写延朗；郎朗异写原保，不能因同姓新推皇后亲属。')
claim('event',E['yanlang'],'description','旧末帝纪也记刘延朗为左领军上将军、宣徽北院使兼枢密副使。',14,'以樞密副使劉延朗為左領軍上將軍，充宣徽北院使兼樞密副使。','旧这命在四月辛卯所列条中而无另具癸巳，主明确癸巳，分保编次，不硬断旧也具相同日。',source='jiuwudaishi-047-935-april',relation='corroborates')
claim('person',people['刘延朗'],'aliases','本段刘延郎与旧同职官命所写刘延朗沿同一主体。',14,'以左领军卫大将军刘延郎为本卫上将军，充宣徽北院使，兼枢密副使。','不是繁简字，依同年同官命及既有枢密副使身份核对异写；保刘延郎检索别名，不另建重复人。')
E['raid_may']=ev('khitan_raids_xinzhou_zhenwu_may','五月丙申契丹侵袭新州及振武',15,'五月，','振武。',[],when='935年五月丙申',place='新州、振武',note='主记寇事，旧丙申是两地奏报，两书层次不同；不指定契丹统帅或假定同一战场。')
claim('event',E['raid_may'],'description','旧末帝纪记五月丙申新州、振武奏契丹寇境。',15,'五月丙申，新州、振武奏，契丹寇境。','旧明确奏报日，不自动变成各处战斗开始日；支持同月受侵消息。',source='jiuwudaishi-047-935-may',relation='corroborates')
E['name']=ev('yang_tan_granted_guangyuan_name','五月庚戌赐杨檀名光远',16,'庚戌，','名光远。',[('杨檀','获赐名光远者'),('帝','赐名者')],when='935年五月庚戌',note='保持 person_杨檀稳定key，补杨光远、楊光遠别名；不另建杨光远主体。主振武旧定州现职不同，原衔各保。')
claim('person',people['杨檀'],'aliases','杨檀于本段获赐名光远，后可称杨光远。',16,'赐振武节度使杨檀名光远。','姓名变更事件与检索别名关联，同UUID，当前规范名沿原库。')
claim('event',E['name'],'description','旧末帝纪记避庙讳提议中，皇帝只改杨檀名光远，其余地名仍旧。',16,'偏旁文字，音韻懸殊，止避正呼，不宜全改。楊檀賜名光遠，餘依舊。','独立补赐名背景，原庚戌条不编应避哪个讳字；不同现镇衔在两书保留待考。',source='jiuwudaishi-047-935-may',relation='corroborates')
event('yang_tan_moves_dingzhou','二月庚午杨檀由振武移镇定州，兼北面行营马步都虞候',16,'二月庚午，定州節度使兗王從溫移鎮兗州；振武軍節度使楊檀移鎮定州，兼北面行營馬步都虞候。',[('杨檀','振武移镇定州并兼北面行营马步都虞候者')],source='jiuwudaishi-047-935-february',when='935年二月庚午；旧纪补录与五月赐名当前职衔有关的前任命',place='定州',note='旧同年二月已经记杨檀移定州，解释五月旧称定州的前文；主五月仍称振武的旧衔写法原保，不修改主。引文前半从温只是定位上下文，不为他另录无关任官。')
E['chai_death']=ev('chai_zaiyong_dies','六月吴德胜节度使兼中书令柴再用去世',17,'六月，','柴再用卒。',[('柴再用','德胜节度使兼中书令、去世者')],when='935年六月；确日未载',place='吴',note='主当月卒明示，其他书目前未找到本次死日独证，不假称旧战功记述就是死亡佐证。')
claim('person',people['柴再用'],'death_year','柴再用于935年六月去世。',17,'六月，吴德胜节度使兼中书令柴再用卒。','主所载死亡年与月，不补生年、享年或死因。')
ev('wang_zhen_asks_chai_for_merits_background','追记吴史官王振曾询问柴再用战功',17,'先是，','其战功，',[('王振','史官、询问者'),('柴再用','被问战功者')],year=None,when='柴再用去世前的往事；询问年份未载',place='吴',note='先是不可强设935六月；王振限定吴史官，不混后世同名宦官，不编王官履历。')
ev('chai_declines_merit_credit_background','柴再用将微功归于社稷之灵，最终不报战功',17,'再用曰：','竟不报。',[('柴再用','答问并未报战功者'),('王振','受答的史官')],year=None,when='前述询问战功的往事；年份未载',place='吴',note='回答为自谦言辞，不把鹰犬解释成实际猎鹰猎犬事；不报限定本次史官询功，非一生没有奏报战役。')
E['ying']=ev('khitan_raids_yingzhou_june','六月契丹侵袭应州',18,'契丹','寇应州。',[],place='应州',note='本段承六月，无独日和统帅兵数；不与五月两地消息合成一次战斗。')
claim('event',E['ying'],'description','旧末帝纪六月条也记契丹寇应州。',18,'契丹寇應州。','本条无日，不能借相邻壬申给侵袭硬定日。',source='jiuwudaishi-047-935-june',relation='corroborates')
ev('shi_contemplates_self_preservation','主书叙石敬瑭回镇后暗作自全之计',19,'河东节度使、','阴为自全之计。',[('石敬瑭','河东节度使北面总管、被叙有自全计划者')],year=None,when='回镇之后、本年六月军政段所附背景；筹划始年未独载',place='河东',note='阴为自全是主作者判断，不等于936反叛此时已经实施；既还镇只是背景，不新造本年第二次回镇事件。')
ev('congke_rotating_night_consultations','李从珂常召李专美、李崧、吕琦、薛文遇、赵延乂轮值谈事至夜',19,'帝好咨访外事，','与语或至夜分。',[('帝','命轮值并咨询者'),('李专美','端明殿学士、轮值者'),('李崧','翰林学士、轮值者'),('吕琦','知制诰、轮值者'),('薛文遇','轮值议事者'),('赵延乂','翰林天文、轮值者')],year=None,when='李从珂在位时常行的咨询；起止年份和各次日期未载',place='中兴殿庭',note='常行做法不硬记935首次，知制诰是否兼辖薛文遇职称原句可能并列，未明确不单独定薛官衔；更直是轮值，不说五人每夜全在场。')
claim('person',people['石敬瑭'],'description','本段称石敬瑭有两个儿子任内使，但没有具名。',19,'时敬瑭二子为内使，','只保二子任职事实，不猜石重英、重裔等名或新建未名重复主体，也不造两子就是本次侦谋执行者。')
relationship('曹太后','晋国长公主','母亲',19,'曹太后则晋国长公主之母也。','本次明确曹氏为公主生母；公主沿已应用永宁公主（石敬瑭妻）晋国长公主别名，非曹氏李存勖母，A是B母亲。')
claim('person_relationship',B['person_relationships'][-1]['key'],'description','新明宗家人传也明确和武宪皇后曹氏生晋国公主。',19,'和武憲皇后曹氏生晉國公主；','明确生育关系独证，与前几年只载异母信息不同；未载生年，不把935首次认母。',source='xinwudaishi-015-cao-princess',relation='corroborates')
ev('shi_bribes_empress_dowager_attendants','石敬瑭贿赂曹太后身边人，令窥探李从珂密谋',19,'敬瑭赂太后左右，','事无巨细皆知之。',[('石敬瑭','贿赂并令侦探者')],when='935年六月条所附密谋背景；具体起始年月未载',year=None,note='太后左右未具名，不把曹本人写成收贿者或肯定亲自侦探；事无巨细是史述概括非可核统计。')
ev('shi_claims_weakness_before_guests','石敬瑭多向宾客自称羸弱不堪为帅，希望朝廷不忌',19,'敬瑭多于宾客前','冀朝廷不之忌。',[('石敬瑭','向宾客自称身体弱者')],year=None,when='本段所附多次自称的背景；起始年日未载',note='底本赢瘠字疑羸瘠，保摘录字样；自称和冀望为书述，不诊断疾病或反断一定装病。')
ev('shi_zhao_request_troops_grain','契丹屡寇时石敬瑭、赵德钧不断请增兵运粮',19,'时契丹屡寇北边，','朝夕相继。',[('石敬瑭','请求增兵运粮者'),('赵德钧','请求增兵运粮者')],when='935年六月甲申等诏之前；具体各次奏日未载',note='朝夕相继只说明频繁，未列次数不统计；主禁军多幽并不等于全部驻此。')
E['borrow']=ev('order_borrow_hedong_grain','六月甲申诏向河东有积蓄人户借菽粟',19,'甲申，','菽粟。',[('帝','发布借粮诏者')],when='935年六月甲申',place='河东',note='借令与实际借多少分，没有偿还记录不称无偿征没；菽粟不一律换成现代大米。')
E['silk']=ev('zhenzhou_fifty_thousand_silk_grain','六月乙酉诏镇州输绢五万匹到总管府以籴军粮',19,'乙酉，','籴军粮，',[('帝','下输绢籴粮诏者')],when='935年六月乙酉',place='镇州、总管府',note='五万匹是绢额，不换成粮食五万石；诏令不等于资金和粮食已全部到达。')
E['carts']=ev('zhen_ji_fifteen_hundred_carts','六月乙酉征调镇冀人车一千五百乘运粮至代州',19,'率镇冀人车','运粮于代州；',[('帝','命征调运粮者')],when='935年六月乙酉',place='镇州、冀州、代州',note='1500为车乘，不当1500名人或1500石；只录命令未记所有车抵达。')
ev('weibo_grain_purchase_order','六月乙酉又诏魏博市籴粮食',19,'又诏魏博','市籴。',[('帝','诏魏博籴粮者')],when='935年六月乙酉条下',place='魏博',note='未具购量及价，不编供粮成效。')
E['hardship']=ev('disaster_hunger_urgent_grain_migration','水旱民饥时石敬瑭遣使严督粮运，山东民众流散',19,'时水旱民饥，','乱始兆矣。',[('石敬瑭','遣使严急督运者')],when='935年六月粮运叙事条下；各地灾起及迁徙日未载',place='山东',note='山东为史载地理范围不当现代山东省；乱始兆矣为主作者因果判断，展示只列灾饥督运流散，不预设后唐灭亡唯一原因。')
for key,quote,note in [('borrow','朝廷以邊儲不給，詔河東戶民積粟處，量事抄借，','旧补因边储不够借积粟，未具甲申，不称主借令已完全执行。'),('silk','仍於鎮州支絹五萬匹，送河東充博采之直。','旧送河东采粮钱，与主总管府购粮金额同，单位匹不改。'),('carts','是月，北面轉運副使劉福配鎮州百姓車子一千五百乘，運糧至代州。','旧明确执行分配官刘福及镇州范围，主镇冀两州不同，保范围不称旧也具冀州。'),('hardship','時水旱民饑，河北諸州困於飛挽，逃潰者甚眾，軍前使者繼至，督促糧運，由是生靈谘怨。','独立记水旱饥、运粮和逃流，地域河北诸州与主山东各保；独立说明相关困苦，不补人数。')]:
 claim('event',E[key],'description','旧末帝纪六月条补证借粮、输绢、征车或灾饥督运的记载。',19,quote,note,source='jiuwudaishi-047-935-june',relation='corroborates')
ev('shi_garrison_xinzhou','石敬瑭率大军屯忻州',19,'敬瑭将大军','屯忻州，',[('石敬瑭','率军驻忻州者')],place='忻州',note='大军无数量不补人数，主没有确出屯日；与回镇背景不矛盾，不把太原作为当前此屯处。')
ev('court_summer_clothes_message','朝廷派使到石敬瑭军中赐夏衣并传诏抚谕',19,'朝廷遣使赐军士','传诏抚谕，',[('帝','朝廷赐衣传诏的君主')],place='忻州',note='使者未名不造人物；朝廷行为主体按后唐帝，未证亲临军营；衣数和诏全文未载。')
E['cheer']=ev('soldiers_shout_wansui_xinzhou','忻州军士数次高呼万岁',19,'军士呼万岁者','数四。',[],place='忻州',note='数四为史载概数或反复，不改成精确独立统计；呼喊对象原句未具，不直接把全体军士当已拥石称帝。')
ev('duan_requests_killing_cheer_leaders','石敬瑭惊惧，段希尧请求处死首先呼喊者',19,'敬瑭惧，','其唱首者，',[('石敬瑭','惊惧的主帅'),('段希尧','河内幕僚、请诛唱首者')],place='忻州',note='惧为书述，请求不同执行；河内为地理标注与后怀州籍贯各保，未名唱首不编完整名单。')
claim('person',people['段希尧'],'description','段希尧是怀州人。',19,'希尧，怀州人也。','本句明籍贯，怀州不凭字面认现代县或出生坐标。')
E['kill']=ev('liu_zhiyuan_executes_li_hui_thirtysix','石敬瑭命刘知远斩挟马都将李晖等三十六人示众',19,'敬瑭命都押衙','三十六人以徇。',[('石敬瑭','下处死命者'),('刘知远','都押衙、奉命执行者'),('李晖','挟马都将、被斩者')],when='935年六月叙事条下；旧七月丙申报斩，实际斩日未独列',place='忻州',note='李晖独立限定挟马都将，不与902年同名军将无证合并。三十六含李晖等总数，未名其余不造人物；旧七月奏日不是主明具的斩日。')
claim('person',people['李晖（挟马都将）'],'death_year','挟马都将李晖于935年忻州军中被斩。',19,'斩挟马都将李晖等三十六人以徇。','两书本年同事、死亡年可定，实际处死日未载，不等于旧七月丙申奏报日。')
claim('event',E['kill'],'time_original','旧末帝纪记七月丙申石敬瑭奏报斩李晖等三十六人，以谋乱为由。',19,'秋七月丙申，石敬瑭奏，斬挾馬都指揮使李暉等三十六人，以謀亂故也。','旧奏报时间晚于主六月编次，可能报告与执行层次差异，均保；谋乱故为奏中理由，不当已独证反叛。挟马都指挥使与主都将是职名差别。',source='jiuwudaishi-047-xinzhou-report',relation='conflicts')
claim('event',E['cheer'],'description','旧纪正文也记石敬瑭军屯忻州，士兵喧噪呼万岁，随后斩李晖等。',19,'時敬瑭以兵屯忻州，一日，軍士喧噪，遽呼萬歲，乃斬暉等以止之。','引用旧正文作独立书证；其附注《契丹国志》与主高度同文，有依赖性，不将附注重复算第二份独证或本批专书录入。',source='jiuwudaishi-047-xinzhou-report',relation='corroborates')
ev('congke_more_suspicious_shi','李从珂闻忻州处死军士后更加怀疑石敬瑭',19,'帝闻之，','益疑敬瑭。',[('帝','闻事后益疑者'),('石敬瑭','被加怀疑者')],when='935年忻州事件之后；闻讯日未独载',note='怀疑为主叙心理，不等于此时已经诏讨反叛或移镇；不把936事件提前。')
ev('harsh_theft_arson_robbery_edict','六月壬辰诏窃盗不计赃数，与纵火强盗一并行极法',20,'壬辰，','并行极法。”',[('帝','发布严刑诏令者')],when='935年六月壬辰',note='记录历史刑令不代表本站赞同；极法保史义为最重刑罚，不造具体处刑人数、实际执行和案件。')
reviews={12:'上疏请求考核、朝臣求罪、帝命马草诏、公布诏意分；旧上疏摘要及停处分互核，诏所引魏征旧典不建935参与。杨昭俭曾祖关系主宋同，字籍贯宋传独补；不编中间两代。',13:'景迁当年加相与934辅政分，新六年压缩官衔异说保；陈辅命、徐对陈叙年轻时与宋争执、解释请教分。宋只谈话提及不在场参与，吾子敬称陈不造父子。',14:'蜀毋任相、唐韩加职、刘延皓枢密、刘延郎北院副使四命分。主旧刘四月、新五月辛卯月异；韩旧兵部新衔、主原刑部不覆。后刘是延皓姐姐，新传其弟上下文核卷16；不由同姓推延朗后弟。主癸巳与旧辛卯条未独日分别保。',15:'主五月丙申寇、旧丙申两地奏报层次分，不指定统帅或合成一个战场。',16:'杨檀赐名光远同UUID，旧避讳背景独补；旧补同年二月庚午杨檀由振武移定州，主五月仍称振武的衔差保，不猜改名应避哪字；别名另安全修订。',17:'柴六月卒与先是问功自谦不报追叙分，问答年null；吴史官王振与后世同名区别，无旁证死日不假装多书确证。',18:'六月应州寇主旧同，无独日不借前壬申定日。',19:'既回镇自全、常轮值咨事、二未名子内使、贿曹左右、宾前自称背景分；未知起年null，不诊断羸弱。曹晋公主母子主新明，公主沿永宁已应用别名。求兵粮、甲申借、乙酉绢匹车乘与魏博籴、旱饥流散、屯忻赐衣万岁、段请、刘奉命斩36、帝益疑分。旧六月粮运地域、七月丙申奏斩与主六月编次各保，谋乱是奏理由；旧附契丹国志依赖不独证、不新增专书；李晖独立限名不合902同名，山东不当现代省。',20:'壬辰严刑命记史义，极法不编已执行名单数量。'}
context_path=YEAR.parent/'year-0934/part-08/sources/library/xinwudaishi-016-liu-empress/source.txt'
contexts=[dict(file=os.path.relpath(context_path,P/'sources'),sha256=hashlib.sha256(context_path.read_bytes()).hexdigest(),paragraph_id='xin-wudaishi-b08f244b9241-p000546',purpose='核卷16废帝刘皇后传首，定位下一段其弟延皓所承主体；不扩录他段',url='https://github.com/greed-216/histree/blob/5f4233fa/'+str(context_path.relative_to(ROOT)))]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(12,21):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],status=status,review=reviews[n])
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=279,year=935,primary_source_key=main_sources[0],primary_source_keys=main_sources,paragraphs=[Q[n]['id'] for n in range(12,21)],next_paragraph='zztj-v279-y0935-p021',next_volume=279,next_year=935,supplements=supplements,source_contexts=contexts,excluded_non_body=[],coverage='卷279连续935年第12—20正文段，原96—104行；史在德言事、吴景迁加职陈觉辅政、唐蜀任官、五月边寇杨赐名、柴死及问功、六月应州寇、河东军政粮运与忻州诛军、严刑诏。后17段待录，全年未完成。',reviewed_questions=[dict(paragraph_id=Q[n]['id'],note=reviews[n]) for n in range(12,21)]),ensure_ascii=False,indent=2)+'\n')
assert {x['key'] for x in B['sources']}=={x['source_key'] for x in B['claims']}
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
