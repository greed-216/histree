"""Curate consecutive Tongjian volume 260, year 895 paragraphs 25–28."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p025-p028', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-895'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/260.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/260.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0895_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=895,note=None,quote=None):
    key='event_zztj_260_0895_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0895_'+code+'_'+pk
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

alias.update({'李溪':'李磎','李谿':'李磎','李存审':'符存审','吉王保':'李保'})
event('shi_yan_chengsi_rush_yun','史俨李承嗣以万骑驰援郓州',25,'895年五月诏讨董以前；确日未载','郓州',
      '河东派史俨、李承嗣领万骑驰入郓州。',[('史俨','领骑驰援者'),('李承嗣','领骑驰援者')],quote='河东遣其将史俨、李承嗣以万骑驰入于郓',note='原文河东遣，不自动把李克用加为亲自驰援者；万骑为书载数。')
event('yougong_retreats_bian','朱友恭退回汴州',25,'895年河东骑入郓后；确日未载','汴州、郓州',
      '朱友恭退回汴州。',[('朱友恭','退归者')],quote='硃友恭退归于汴。',note='退归不增具体战败、追击或伤亡。')
event('dong_stripped_qian_ordered_campaign','朝廷削董昌官爵，委钱镠讨之',25,'895年五月；具体日未载','朝廷、浙东',
      '朝廷下诏剥夺董昌官爵，委钱镠讨伐。',[('唐昭宗','下讨诏者'),('董昌','被削官爵及诏讨者'),('钱镠','受委讨伐者')],quote='五月，诏削董昌官爵，委钱镠讨之。',note='与四月释罪及钱请不可赦分录；五月讨诏非已擒董。')
event('xingyu_resent_shangshuling_denial','王行瑜因未获尚书令怨朝廷',26,'初；五月入京以前，确年待考',None,
      '王行瑜曾求尚书令未得，因此怨朝廷。',[('王行瑜','求官不获而怨者')],year=None,quote='初，王行瑜求尚书令不获，由是怨朝廷。',note='背景初不强定895；沿原文动机，不另补求官日期。')
event('han_xingyu_seek_imperial_garrisons','韩建王行瑜求取禁军两镇，宦官拒之',26,'五月入京以前；确年待考','郃阳、良原、华州、邠州',
      '畿内八镇兵隶左右军，韩建求取近华州的郃阳镇，王行瑜求取近邠州的良原镇。宦官以其为天子禁军，拒绝。',[('韩建','求郃阳镇者'),('王行瑜','求良原镇者')],year=None,quote='畿内有八镇兵，隶左右军。郃阳镇近华州，韩建求之；良原镇近邠州，王行瑜求之。宦官曰：“此天子禁军，何可得也！”',note='求之对象为禁军镇兵控制，不写已割辖地；未具名宦官不补人。')
event('warlords_shame_hezhong_failure','三帅为王珙请河中不得而耻',26,'895年五月以前河中争位期间；确日未载','河中、朝廷',
      '王行瑜、韩建、李茂贞为王珙请求河中未得，感到耻辱。',[('王行瑜','为珙请不得者'),('韩建','为珙请不得者'),('李茂贞','为珙请不得者'),('王珙','被代请者')],quote='王珂、王珙争河中，行瑜、建及李茂贞皆为珙请，不能得，耻之。')
event('wang_gong_urges_attack_ke','王珙遣人劝三帅讨王珂',26,'895年五月入京以前；确日未载','河中',
      '王珙遣人向三帅声称王珂不受代且与河东联姻，必对三帅不利，请求讨伐王珂。',[('王珙','遣人劝讨者'),('王珂','被请讨者'),('王行瑜','受说三帅之一'),('李茂贞','受说三帅之一'),('韩建','受说三帅之一')],quote='珙使人语三帅曰：“珂不受代而与河东昏姻，必为诸公不利，请讨之。”',note='必为不利为王珙判断；婚姻有前段婿句，但不推共同反叛计划。')
event('xingyue_attacks_hezhong_ke_seeks_aid','王行约攻河中，王珂求救李克用',26,'895年五月三帅入京以前；确日未载','河中',
      '王行瑜命弟、匡国节度使王行约攻河中，王珂向李克用求救。',[('王行瑜','命弟出兵者'),('王行约','匡国节度使攻城者'),('王珂','求救者'),('李克用','被求救者')],quote='行瑜使其弟匡国节度使行约攻河中，珂求救于李克用。',note='攻不作已克，求救不作本段已援到。')
relation('王行瑜','王行约','兄长',26,'王行瑜是王行约的兄长。',quote='行瑜使其弟匡国节度使行约')
event('three_warlords_enter_capital','三帅各领精兵数千入京，坊市民窜匿',26,'895年五月甲子','京师、坊市',
      '王行瑜、李茂贞、韩建各领精兵数千入朝，甲子抵京师，坊市居民窜匿。',[('王行瑜','领兵入京者'),('李茂贞','领兵入京者'),('韩建','领兵入京者')],quote='行瑜乃与茂贞、建各将精兵数千入朝，甲子，至京师，坊市民皆窜匿。',note='各数千为概数，不加总成已知总军数；入朝是原文名义，不将其合法性当书外结论。')
event('emperor_confronts_three_warlords','唐昭宗临安福门亲诘三帅称兵入京',26,'895年五月甲子','安福门',
      '唐昭宗御安福门，三帅盛陈甲兵、拜伏舞蹈。皇帝责其未奏请候报而称兵入京；王行瑜、李茂贞流汗失语，韩建略述原因。',[('唐昭宗','临门诘问者'),('王行瑜','受诘失语者'),('李茂贞','受诘失语者'),('韩建','略述原因者')],quote='上御安福门以待之，三帅盛陈甲兵，拜伏舞蹈于门下。上临轩，亲诘之曰：“卿辈不奏请俟报，辄称兵入京城，其志欲何为乎？若不能事朕，今日请避贤路！”行瑜、茂贞流汗不能言，独韩建粗述入朝之由。',note='避贤路为责问言辞，皇帝没有因此实际退位。')
event('warlords_request_execute_chancellors','三帅宴中请诛韦昭度李磎，皇帝未许',26,'895年五月甲子','京师、宴席',
      '皇帝宴三帅，三帅称南北司结党乱政、韦昭度讨西川失策、李磎不合众心，请诛二人，皇帝尚未准许。',[('唐昭宗','未许诛相者'),('王行瑜','宴中请诛者'),('李茂贞','宴中请诛者'),('韩建','宴中请诛者'),('韦昭度','被请诛者'),('李磎','以李溪名被请诛者')],quote='上与三帅宴，三帅奏称：“南、北司互有朋党，堕紊朝政。韦昭度讨西川失策，李溪作相，不合众心，请诛之。”上未之许。',note='结党失策等为三帅奏称，不当已证罪状；未许与下文实际杀害分开。')
event('warlords_kill_wei_li_kang','王行瑜等杀韦昭度李磎康尚弼',26,'895年五月甲子','都亭驿、京师',
      '王行瑜等当日杀韦昭度、李磎于都亭驿，又杀枢密使康尚弼及宦官数人。',[('王行瑜','等杀人者'),('韦昭度','被杀者'),('李磎','以李溪名被杀者'),('康尚弼','被杀枢密使')],quote='是日，行瑜等杀昭度、溪于都亭驿，又杀枢密使康尚弼及宦官数人。',note='行瑜等未逐名确认另二帅亲手行凶；都亭驿明确二相处，康与宦官地点不强定同一刑场；不补未具名宦官。')
event('warlords_secure_hezhong_reassignments','三帅请王珙领河中并徙行约王珂，皇帝许',26,'895年五月甲子','河中、陕州、同州、朝廷',
      '三帅称王珂、王珙嫡庶不分，请王珙领河中、王行约改陕州、王珂改同州，皇帝均许。',[('王行瑜','等请求改镇者'),('唐昭宗','准许者'),('王珙','被许河中者'),('王行约','被许陕州者'),('王珂','被许同州者')],quote='又言：“王珂、王珙嫡庶不分，请除王珙河中，徙王行约于陕，王珂于同州。”上皆许之。',note='嫡庶不分为三帅说辞；帝许不代表三人已实际换镇，与旧史人名调镇异说另引。')
event('three_warlords_plan_depose_emperor','三帅谋废唐昭宗立吉王李保',26,'始；895年五月入京前后，谋议确日未载',None,
      '三帅曾谋废唐昭宗，立吉王李保。',[('王行瑜','谋废立三帅之一'),('李茂贞','谋废立三帅之一'),('韩建','谋废立三帅之一'),('唐昭宗','拟被废者'),('李保','拟被立吉王')],year=None,quote='始，三帅谋废上，立吉王保',note='始为追述，未实际废立，李保沿888年吉王身份复用；不当已即位。')
event('warlords_leave_garrisons_depart','闻李克用起兵，行瑜茂贞留兵后辞还镇',26,'895年五月甲子入京事后；确日未另载','京师、河东',
      '三帅闻李克用已起兵于河东，王行瑜、李茂贞各留二千兵宿卫京师，与韩建均辞还镇。',[('王行瑜','留兵还镇者'),('李茂贞','留兵还镇者'),('韩建','辞还镇者'),('李克用','被闻已起兵者')],quote='至是，闻李克用已起兵于河东，行瑜、茂贞各留兵二千人宿卫京师，与建皆辞还镇。',note='宿卫按原文，不当皇帝自愿欢迎或主帅留居京师；韩建未明确同样留二千人。')
event('yang_kan_demoted_yazhou','杨堪贬雅州刺史',26,'895年五月三帅入京事后；确日未载','雅州、朝廷',
      '户部尚书杨堪被贬为雅州刺史。',[('杨堪','被贬者')],quote='贬户部尚书杨堪为雅州刺史。',note='未载明确发诏主体及理由，不补皇帝主动以朋党罪贬。')
person('虞卿（杨堪父）',26,'原文称虞卿，杨堪之父')
relation('虞卿（杨堪父）','杨堪','父亲',26,'原文所称虞卿是杨堪之父。',quote='堪，虞卿之子')
relation('杨堪','韦昭度','舅父',26,'杨堪是韦昭度之舅。',quote='昭度之舅也。')
event('xue_court_agent_recommends_liu','河东进奏官薛志勤扬言刘崇望更合李克用',27,'初；崔胤除河中帅时，确年待考','朝廷、河中',
      '崔胤被任河中节度使时，河东进奏官薛志勤称，与其以崔胤代王珂，不如与李克用更厚的光德刘公。光德刘公为太常卿刘崇望。',[('薛志勤（河东进奏官）','扬言进奏官'),('崔胤','被比较的河中帅'),('王珂','拟被代者'),('刘崇望','所荐光德刘公'),('李克用','言中我公')],year=None,quote='初，崔胤除河中节度使，河东进奏官薛志勤扬言曰：“崔公虽重德，以之代王珂，不若光德刘公于我公厚也。”光德刘公者，太常卿刘崇望也。',note='背景初不强定日期；进奏官与已录昭义节度使薛志勤未有可靠任职连接，先以职位消歧，不认定二者必为异人；于我公厚为薛言。')
event('liu_chongwang_demoted_zhaozhou','三帅闻薛言，贬刘崇望昭州司马',27,'895年五月三帅入京时；确日未另载','昭州、京师',
      '三帅入朝听到薛志勤之言，将刘崇望贬为昭州司马。',[('王行瑜','入朝三帅之一'),('李茂贞','入朝三帅之一'),('韩建','入朝三帅之一'),('刘崇望','被贬者')],quote='及三帅入朝，闻志勤之言，贬崇望昭州司马。',note='沿主书动作链，不补实际赴任日、犯罪或帝亲自贬命。')
event('keyong_dispatches_thirteen_mobilizers','李克用遣十三辈使发北部兵，约次月入关',27,'895年五月闻犯阙即日；预期来月','河东、北部、关中',
      '李克用闻三镇兵犯阙，当日遣使十三辈征发北部兵，约定次月渡河入关。',[('李克用','遣使征兵者')],quote='李克用闻三镇兵犯阙，即日遣使十三辈发北部兵，期以来月渡河入关。',note='十三辈是使者批次，不自动作十三个人；期为约定，实际渡河后段再录。')
event('qian_zhedong_commission','钱镠授浙东招讨使',28,'895年六月庚寅','浙东、朝廷',
      '朝廷以钱镠为浙东招讨使。',[('钱镠','受浙东招讨使者')],quote='六月，庚寅，以钱镠为浙东招讨使')
event('qian_again_attacks_dong','钱镠复发兵击董昌',28,'895年六月授招讨使条；确日未另载','浙东',
      '钱镠再次出兵攻击董昌。',[('钱镠','再次出兵者'),('董昌','被攻者')],quote='镠复发兵击董昌。',note='与先前城下劝改退军分开，不作本段已擒董。')

from urllib.parse import quote as urlquote
supplements=[]
sk='jiuwudaishi-026-895-three-warlords'
path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==595)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L595'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·三帅犯阙',source_type='primary',author='薛居正等',edition='仓库PDF派生文本；换行原字保留，未核纸本。',url=url,note='原PDF第595页，乾宁二年六月条内追述前事；与主书调镇人名异说并存。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=595的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(code,text,quote,note,kind):
    assert quote in raw.decode()
    ck=f'claim_zztj_260_0895_06_{len(B["claims"])+1:04d}';key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path='description',claim_text=text,source_key=sk,citation='卷26·唐书二·武皇纪下·乾宁二年六月条追述·原PDF第595页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[26]['id'],subject_key=key,relation=kind))
extra('warlords_kill_wei_li_kang','《旧五代史》也记三帅称兵向阙、杀害宰辅。','先是，三帅称兵向\n阙，同弱王室，杀害宰辅。','先是追述不将杀相日改为六月；这里只印证宰辅被害，不补康尚弼或具体亲手凶手。','corroborates')
extra('warlords_secure_hezhong_reassignments','《旧五代史》记三帅请授王珂同州、王瑶河中；主书请王珙河中及王行约陕州，调授人名不同。','三帅遂以兵入觐，大掠京师，请\n授王珂同州节度使，王瑶河中节度\n使，天子亦许之。','保存王瑶与主书王珙差别，不默改为同一字或据此称王瑶已经到河中；两书实际经过另有后段核对。','conflicts')
reviews={
 25:'河东万骑入郓与友恭退汴、五月削董诏讨分录；退不增会战，诏不作董已被擒。',
 26:'初与禁军两镇背景无确年；争位、攻河中求救、甲子至京与帝诘、宴请未许与杀害、调镇许令、谋废未行、留兵还镇、贬杨逐阶段。各千概数不编总军，康刑场不强定驿；王约兄长、虞卿父、杨舅有句，虞卿先保短名。旧史王瑶主书王珙河中异说独存。',
 27:'进奏官薛志勤先职位消歧，与旧录昭义帅未获身份链，不武断合并；初背景无确年。刘贬与李十三辈使约次月分录，辈非人数。',
 28:'六月庚寅授浙东招讨使与复出兵分录，不提前董昌灭亡。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(25,29):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(25,29)],next_paragraph=Q[29]['id'],coverage='第25—28段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
