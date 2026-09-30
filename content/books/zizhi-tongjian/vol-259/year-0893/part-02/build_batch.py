"""Curate consecutive Tongjian volume 259, year 893 paragraphs 8–13."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 39))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0893-p008-p013', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-893'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/259.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/259.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, {source}
alias.update({'李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0893_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福二年（893）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=893,note=None,quote=None):
    key='event_zztj_259_0893_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0893_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

event('zhu_yougong_accuses_youyu','朱友恭谮朱友裕，朱全忠命庞师古代将',8,'893年二月条；具体日未载','彭城',
      '朱友裕围彭城，时溥多次出兵，友裕闭壁不战；朱瑾夜逃，友裕没有追击。都虞候朱友恭写信向朱全忠谮友裕，朱全忠发怒，驿书命庞师古替代领军并调查。',[('朱友裕','围城及被谮将领'),('时溥','被围且屡出兵者'),('朱瑾','夜逃者'),('朱友恭','书谮者'),('朱温','以朱全忠名义命代将者'),('庞师古','奉命代将按事者')],note='谮是史书用词，不把指控当证实异志；闭壁不追与函令各自因果依段述，不补未载书信全文。')
event('zhu_youyu_flees_dangshan','误收父亲驿书，朱友裕逃砀山藏伯父处',8,'误得驿书后；具体日未载','山中、砀山',
      '本送庞师古的驿书误到朱友裕处，友裕害怕，率二千骑逃入山中，再潜到砀山藏在伯父朱全昱家。',[('朱友裕','误收书及逃藏者'),('朱全昱','藏身所在伯父'),('朱温','以朱全忠名义驿书发出者')],note='二千为书载逃时兵数，不推全数一起到砀山；藏于所不写伯父亲自策划逃走。')
person('张氏（朱温妻）',8,'张夫人，劝友裕归父并护救者')
event('zhang_saves_zhu_youyu','张夫人使朱友裕归汴，抱救免死',8,'朱友裕潜砀山之后；具体日未载','砀山、汴州',
      '张夫人听闻后使朱友裕单骑去汴州见朱全忠。友裕伏地哭拜，朱全忠命左右抓按将杀他；张夫人赶来抱住，哭称其弃兵束身归罪足见无异志。朱全忠醒悟放过他，使其权知许州。',[('张氏（朱温妻）','劝返及抱救者'),('朱友裕','归罪获免者'),('朱温','以朱全忠名义将杀后赦使权知者')],note='无异志为张氏劝说，不作为独立内心测量；权知许州暂摄，不推即日抵任。')
event('yougong_childhood_adoption','朱友恭原名李彦威，幼为家僮后被收养',8,'幼时；确切年日未载','寿春（籍贯）',
      '《通鉴》记朱友恭是寿春人李彦威，幼年为朱全忠家僮，被朱全忠养为子。',[('朱友恭','幼时家僮被养为子者'),('朱温','以朱全忠名义收养者')],year=None,note='追叙身份与旧名，不记收养发生893年；寿春为籍贯，不推收养地。')
next(p for p in B['people'] if p['key']==people['朱友恭'])['aliases']=['李彦威','硃友恭']
claim('person',people['朱友恭'],'aliases','朱友恭原名李彦威。',8,quote='友恭，寿春人李彦威也',note='同段明示姓名对应，不另建李彦威。')
relation('朱温','朱友恭','养父',8,'朱全忠养李彦威为子，李彦威后来名朱友恭；朱温是朱友恭的养父。',quote='友恭，寿春人李彦威也，幼为全忠家僮，全忠养以为子。')
relation('张氏（朱温妻）','朱温','妻子',8,'原文明示全忠夫人张氏；张氏是朱温的妻子，不据此推她为朱友裕生母。',quote='全忠夫人张氏闻之')
relation('朱全昱','朱友裕','伯父',8,'《通鉴》称全昱为友裕伯父；朱全昱是朱友裕的伯父。',quote='匿于伯父全昱之所')
claim('person',people['张氏（朱温妻）'],'biography','张氏，砀山人；《通鉴》称其多智略，朱全忠敬惮她，有时与她商议军府事务。',8,quote='张夫人，砀山人，多智略，全忠敬惮之，虽军府事，时与之谋议',note='史书品评与总述不推具体单次会议年日；妻子身份不自动作所有朱氏子女生母。')
event('zhang_recalls_zhu_campaign','张夫人遣使召返出征的朱全忠之总述',8,'或将兵出中途；各次确年未载','',
      '《通鉴》述朱全忠有时领兵出发，张夫人认为不可，派一人召回，朱全忠立即返回。',[('张氏（朱温妻）','遣使召返者'),('朱温','以朱全忠名义领兵后返者')],year=None,note='或为往事总述，不补出征目标、日期或具体战役。')
event('pang_takes_foshan_camp','庞师古攻拔佛山寨，徐兵不再出',9,'893年二月条；具体日未载','佛山寨、徐州',
      '庞师古攻佛山寨，攻下后徐州军不再敢出战。',[('庞师古','攻拔者'),('时溥','徐军所属主将')],note='底本拨疑拔，快照不改；与前段石佛山野战分阶段。')
event('li_kuangwei_assaults_brothers_wife','李匡威出援前酒醉侵害弟妻',10,'将发幽州救王镕时；具体日未载','幽州',
      '李匡威将从幽州出发援救王镕，家人聚会送别；他酒醉侵害其弟李匡筹的妻子。',[('李匡威','侵害者'),('李匡筹','受侵害妻子的丈夫'),('王镕','当次出兵援救对象')],note='与前段本年救镕相承，出发具体日未载；弟妻未名，不捏造姓名。')
event('li_kuangchou_seizes_lulong','李匡筹据军府自称留后、召还行营兵',10,'893年二月；匡威自镇州还至博野时','幽州、博野、深州',
      '李匡威从镇州返回至博野时，李匡筹占军府自称留后，用符召还行营兵。李匡威部众散归，只同亲近者留深州，无处进退。',[('李匡威','失去军府与部众者'),('李匡筹','据府自称并召兵者')],note='自称不作正式诏任；博野为匡威到处，军府在幽州，未混同。')
relation('李匡威','李匡筹','兄长',10,'《通鉴》称匡筹为李匡威之弟；李匡威是李匡筹的兄长。',quote='弟匡筹之妻美')
event('li_baozhen_petitions_capital_return','李匡威遣判官李抱真请归京师，引坊市恐慌',10,'失军府后；具体日未载','深州、京师',
      '李匡威派判官李抱真上奏请归京师。京师经历多次大乱，听说他要来，坊市恐慌，称金头王来图社稷，部分士民逃入山谷。',[('李匡威','请归者'),('李抱真（李匡威判官）','奉遣上奏者')],note='判官李抱真暂辨稳定key，与早唐同名名将不合并；金头王图社稷为坊市传言，不写确有篡位计划或已到京师。')
event('wang_hosts_li_kuangwei','王镕迎李匡威镇州筑第，父礼相待',10,'李匡威请归京后条；具体日未载','镇州',
      '王镕感念李匡威因援救自己而失地，迎他到镇州，筑住宅，以父亲之礼对待。',[('王镕','迎居筑第者'),('李匡威','受迎礼者')],note='父事之为尊奉方式，不建立生父或养父关系；感念理由归于史书。')
event('liu_pin_luzhou_office','柳玭由渝州刺史转泸州刺史',11,'893年二月条；具体日未载','渝州、泸州',
      '朝廷以渝州刺史柳玭为泸州刺史。',[('柳玭','转任者')],note='同段玼字按上下文暂指玭，化绰及膏梁疑字保留快照不改；不造柳化绰人物。')
claim('person',people['柳玭'],'biography','《通鉴》述柳氏世以孝悌礼法为士大夫所宗；柳玭曾任御史大夫，皇帝欲用为相，宦官厌恶他，故长期谪居外任。',11,note='品評及外任原因归于史书；曾任与欲任不记893首次发生，未补具体贬谪年。')
event('liu_pin_admonishes_family','柳玭告诫子弟门第可畏不可恃',11,'戒其子弟时；确年未载','',
      '柳玭告诫子弟：门第高既要敬畏又不可倚仗；自己有失，责罚比他人重；门高易骄，族盛易招嫉，才行未获信而小失易被指摘，故应更勤学、更谨慎行事。',[('柳玭','告诫子弟者')],year=None,note='训诫保留主要论点，不把常理讲话转换成已发生族人犯罪；子弟未名不造人。')
event('wang_jian_seeks_killing_denied','王建屡请杀陈敬瑄田令孜，朝廷不许',12,'屡请；具体起止未载','',
      '王建多次请杀陈敬瑄与田令孜，朝廷不批准。',[('王建','请求者'),('陈敬瑄','所请杀者'),('田令孜','所请杀者')],year=None,note='屡请为既往背景，不反算首次请求日期或诏令署名者。')
event('chen_jingxuan_accused_killed','王建使告陈敬瑄作乱，杀于新津',12,'893年夏四月乙亥','新津',
      '王建派人告发陈敬瑄谋作乱，在新津将其杀死。',[('王建','使告与杀者'),('陈敬瑄','被告被杀者')],note='谋乱是所告罪名，不当已独立证实的实际阴谋。')
event('tian_lingzi_accused_imprisoned_dies','王建使告田令孜通凤翔书，下狱死',12,'893年四月乙亥条后；死亡具体日未载','',
      '王建又派人告发田令孜与凤翔通信，田令孜下狱后死亡。',[('王建','使告者'),('田令孜','被告下狱死者')],note='通信为所告，未见书信不确认罪名真实；下狱死未明方式，不补勒死或同日死。')
event('feng_juan_drafts_explanation','冯涓为王建草奏，辩解专杀先机',12,'陈田遇害后奏报；具体日未载','西川',
      '王建命节度判官冯涓草拟奏表。奏中用开匣出虎孔子不责他人、当路斩蛇孙叔敖非为己利的典故，为军外专杀与先机制乱辩解。',[('王建','命草奏者'),('冯涓','节度判官草表者')],note='典故为奏章论证，不建孔子孙叔敖在晚唐参与事件；专杀必要性为奏表主张，不作本项目结论。')
claim('person',people['冯涓'],'biography','《通鉴》称冯涓为宿之孙。',12,quote='涓，宿之孙也。',note='仅保留书载祖孙信息；本段宿未全名，不新建未核身份祖父。')
event('zhang_tao_inauspicious_letter','张涛称进军日不吉，敬翔劝勿懈攻',13,'汴军攻徐累月时；具体日未载','徐州',
      '汴军攻徐州数月未下，通事官张涛写信向朱全忠说进军日期不吉故无功，朱认为有理。敬翔指出攻城耗费已多、徐人已困，若军士听到这种说法会松懈，朱全忠便烧信。',[('张涛','称进军日不吉写信者'),('朱温','以朱全忠名义收信后焚者'),('敬翔','劝勿传播以防懈怠者')],note='时日非良为张涛迷信归因，不作攻城失败的客观原因；累月不反算起围日，敬翔判断徐困不作现代估测。')
event('zhu_goes_xuzhou','朱全忠亲自赴徐州',13,'893年四月癸未','徐州',
      '朱全忠亲自率军前往徐州。',[('朱温','以朱全忠名义亲赴者')],note='如徐为前往，不补同日入城。')
event('pang_takes_pengcheng_shi_dies','庞师古拔彭城，时溥举族自焚',13,'893年四月戊子','彭城、燕子楼',
      '庞师古攻下彭城，时溥带全族登燕子楼自焚而死。',[('庞师古','攻拔者'),('时溥','举族自焚者')],note='底本拨疑拔保留；全族未列姓名，不补逐人死亡信息；死亡形式与其他书异说另设出处。')
event('zhu_enters_pengcheng_zhang_acting','朱全忠入彭城，张廷范知感化留后',13,'893年四月己丑','彭城、感化',
      '朱全忠进入彭城，以宋州刺史张廷范知感化留后，上奏请求朝廷任文臣为节度使。',[('朱温','以朱全忠名义入城授暂职奏请者'),('张延范','以张廷范名知感化留后者')],note='知留后暂摄，与请求文臣节度分开；张廷范按已归档异名书证复用张延范。')

# Cross-book evidence from already committed PDF-derived JSONL snapshots.
from urllib.parse import quote as urlquote
supplements=[]
for sk,title,author,path,page in [
 ('xinwudaishi-043-893-yougong','新五代史·卷43·李彦威传·身份摘录','欧阳修','resources/derived/twenty-four-histories/19新五代史.jsonl',797),
 ('jiuwudaishi-001-893-pengcheng','旧五代史·卷1·梁太祖纪·彭门段','薛居正等','resources/derived/twenty-four-histories/18旧五代史.jsonl',24)]:
    raw=next(json.loads(x)['text'].encode() for x in (ROOT/path).read_text().splitlines() if json.loads(x)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='仓库PDF派生电子文本；逐字及换行保留，未核纸本。',url=url,note=f'原PDF第{page}页，只补当前主线段落。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,text,n,sk,quote,citation,note,book,kind):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_259_0893_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=citation,note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=ck,source_book=book,primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('person',people['朱友恭'],'aliases','《新五代史》记李彦威受梁太祖收养，冒姓朱氏，名友恭。',8,'xinwudaishi-043-893-yougong','太祖怜\n之，养以为子，冒姓硃氏，名友恭。','卷43·杂传第三十一·李彦威传·原PDF第797页','印证旧名对应及收养；新书寿州与主书寿春分层保留，不抽录后续弑君。','新五代史','corroborates')
extra('event','event_zztj_259_0893_pang_takes_pengcheng_shi_dies','time_original','《旧五代史》记景福二年四月丁丑庞师古下彭门；与《通鉴》四月戊子日不同。',13,'jiuwudaishi-001-893-pengcheng','二年四月丁丑，庞师古下彭门，\n枭时溥首以献。','卷1·梁书·太祖纪一·原PDF第24页','两书记日与死后叙述差别并列，不覆盖主书戊子自焚；旧书枭首不自动否定先自焚。','旧五代史','conflicts')
extra('event','event_zztj_259_0893_pang_takes_pengcheng_shi_dies','description','《旧五代史》另记庞师古下彭门后枭时溥首献上。',13,'jiuwudaishi-001-893-pengcheng','庞师古下彭门，\n枭时溥首以献。','卷1·梁书·太祖纪一·原PDF第24页','补旧书枭首献首记载，区别通鉴所记举族自焚，不推自焚与枭首的准确先后。','旧五代史','adds')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={8:'朱友恭谮、友裕逃藏、张抱救、幼时收养及妻干预军务总述分录；新史旧名印证；伯父养父妻子有据，不推生母。',9:'佛山寨攻拔与先前石佛山野战分阶段，拨疑字保留。',10:'侵弟妻、弟据府散兵、判官请归与恐慌、王镕父礼相待分开；父事非父子；抱真判官暂辨。',11:'柳玭授职与曾职外谪书评、门第训诫分层；玼化绰膏梁疑字保留，不造祖人。',12:'屡请不许、告陈谋乱杀、告田通信下狱死、冯草奏分录；所告非已证实；典故不造晚唐参与。',13:'不吉日书说焚信、癸未赴徐、戊子攻拔自焚、己丑入城知留后分录；旧史丁丑及枭首别说独立出处。'}
for n in range(8,14):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(8,14):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=893,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(8,14)],next_paragraph='zztj-v259-y0893-p014',coverage='卷259景福二年第8—13段连续录入；本年38段尚未完。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
