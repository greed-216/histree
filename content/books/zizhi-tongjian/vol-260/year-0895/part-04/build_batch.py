"""Curate consecutive Tongjian volume 260, year 895 paragraphs 11–18."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p011-p018', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

alias.update({'李溪':'李磎','李谿':'李磎','李存审':'符存审','刘廉':'刘谦','徐知诰':'李昪'})
event('gao_brothers_youzhou_commands','李克用以高思继兄弟为都将分掌幽州兵',11,'李克用定幽州以后；本段背景，确年待考','幽州、妫州',
      '妫州人高思继兄弟为燕人所服，李克用以其为都将，分掌幽州兵；其部下多山北豪强，刘仁恭忌惮他们。',[('高思继','与兄弟分掌幽州兵者'),('李克用','授都将者'),('刘仁恭','忌惮高氏者')],year=None,quote='妫州人高思继兄弟，在武干，为燕人所服，克用皆以为都将，分掌幽州兵；部下士卒，皆山北之豪也，仁恭惮之。',note='在武干疑有武干，底本保留；不由背景顺序强定任命发生895，也不编两兄弟姓名。')
event('gao_brothers_punish_garrison','高思继兄弟依法裁治暴横的河东戍兵',11,'久之；幽州高氏掌兵以后，确年待考','幽州',
      '河东戍幽州兵暴横，高思继兄弟依法裁治，诛杀多人。',[('高思继','与兄弟裁治戍兵者')],year=None,quote='久之，河东兵戍幽州者暴横，思继兄弟以法裁之，所诛杀甚多。',note='久之无确年；甚多不转换具体人数，依法裁治为史书叙述而非现代司法结论。')
event('keyong_kills_gao_brothers','李克用责刘仁恭后杀高思继兄弟',11,'高氏裁治戍兵以后；确年待考','幽州',
      '李克用怒责刘仁恭，刘仁恭称系高氏兄弟所为，李克用杀高思继兄弟。',[('李克用','责问并命杀者'),('刘仁恭','归责高氏者'),('高思继','与兄弟被杀者')],year=None,quote='克用怒，以让仁恭，仁恭诉称高氏兄弟所为，克用俱杀之。',note='让是责让而非让位；不据所在年条填写确定死亡年。')
event('rengong_receives_gao_sons','刘仁恭收高氏诸子于帐下厚抚',11,'高氏兄弟被杀以后；确年待考','幽州、帐下',
      '刘仁恭为收燕人之心，将高氏兄弟诸子置于帐下，厚加抚恤。',[('刘仁恭','收诸子厚抚者')],year=None,quote='仁恭欲收燕人心，复引其诸子置帐下，厚抚之。',note='厚抚不等同收为养子；主书未列子名，补书另引。')
event('cui_informs_warlords','崔昭纬向李茂贞王行瑜告朝廷机事',12,'895年三月罢李磎以前；往来起点未载',None,
      '崔昭纬与李茂贞、王行瑜深相结，将所知天子过失及朝廷机事告给二人。',[('崔昭纬','通告朝廷机事者'),('李茂贞','受告者'),('王行瑜','受告者')],year=None,quote='崔昭纬与李茂贞、王行瑜深相结，得天子过失，朝廷机事，悉以告之。',note='关系往来为背景，不反算开始年；所称过失未列内容，不补具体罪行。')
event('cui_chan_conveys_accusation','崔昭纬使崔鋋向王行瑜诋毁韦昭度李磎',12,'895年李磎再入相后；确日未载',None,
      '李磎再次入相后，崔昭纬让同族、邠宁节度副使崔鋋向王行瑜指称韦昭度阻其尚书令任命，并与李磎相共惑主。',[('崔昭纬','指使传话者'),('崔鋋','传话邠宁副使'),('王行瑜','受话者'),('韦昭度','被诋者'),('李磎','以李溪名被诋者')],quote='邠宁节度副使崔鋋，昭纬之族也，李溪再入相，昭纬使鋋告行瑜曰：“向者尚书令之命已行矣，而韦昭度沮之，今又引李溪为同列，相与荧惑圣听，恐复有杜太慰之事。”',note='杜太慰疑杜太尉，原字保留；这是崔氏说辞，杜故事不当本年参与者；同族不推父子叔侄。')
claim('person',people['崔鋋'],'biography','崔鋋是崔昭纬同族，时为邠宁节度副使。',12,quote='邠宁节度副使崔鋋，昭纬之族也。' if '邠宁节度副使崔鋋，昭纬之族也。' in Q[12]['text'] else '邠宁节度副使崔鋋，昭纬之族也',note='仅族，不推具体辈分或亲属称谓。')
event('warlords_petition_remove_chancellors','王行瑜李茂贞表请罢李磎韦昭度',12,'895年三月以前；确日未载',None,
      '王行瑜与李茂贞上表称李磎奸邪、韦昭度无相业，请求罢为散秩。',[('王行瑜','联表请罢者'),('李茂贞','联表请罢者'),('李磎','以李溪名被请罢者'),('韦昭度','被请罢者')],quote='行瑜乃与茂贞表称溪奸邪，昭度无相业，宜罢居散秩。',note='奸邪无相业为奏表指控，不录为客观人物评价。')
event('emperor_defends_chancellor_choice','唐昭宗答命相当出朕怀',12,'895年三月以前；确日未载','朝廷',
      '唐昭宗回复王行瑜等，称军旅可与藩镇议，任命宰相应出皇帝之意。',[('唐昭宗','回复拒藩镇干预命相者'),('王行瑜','受答者')],quote='上报曰：“军旅之事，联则与籓镇图之；至于命相，当出朕怀。”',note='联疑朕、籓为底本字形，照引不改；本段回复不写争论已结束。')
event('li_xi_again_removed_895','李磎再罢相为太子少师',12,'895年三月；具体日未载','朝廷',
      '王行瑜等不断论列，三月李磎再次罢相，为太子少师。',[('李磎','以李溪名再罢相者'),('王行瑜','持续论列者')],quote='行瑜等论列不已，三月，溪复罢为太子少师。')
event('wangs_request_hezhong_commander','王珙王瑶请朝廷命河中帅',13,'895年三月条；确日未载','河中、朝廷',
      '王珙、王瑶请求朝廷任命河中统帅。',[('王珙','请命河中帅者'),('王瑶','请命河中帅者')],quote='王珙、王瑶请朝廷命河中帅')
event('cui_yin_huguo_appointment','崔胤兼同平章事充护国节度使',13,'895年三月条；确日未载','护国、朝廷',
      '朝廷命中书侍郎、同平章事崔胤兼同平章事，充护国节度使。',[('崔胤','受命护国节度使者')],quote='诏以中书侍郎、同平章事崔胤同平章事，充护国节度使',note='原书同平章事复见，保底本，不推已赴河中到任。')
event('wang_tuan_chancellor','王抟授中书侍郎同平章事',13,'895年三月条；确日未载','朝廷',
      '朝廷以户部侍郎、判户部王抟为中书侍郎、同平章事。',[('王抟','授相者')],quote='以户部侍郎、判户部王抟为中书侍郎、同平章事。')
person('李克用',14,'王珂岳父、为珂求节钺者');person('王珂',14,'李克用之婿')
relation('李克用','王珂','岳父',14,'李克用是王珂岳父；原书称王珂为其婿。',quote='王珂，李克用之婿也。')
event('keyong_petitions_wang_ke_commission','李克用表请赐王珂节钺',14,'895年河中继立争议期间；确日未载','朝廷、河中',
      '李克用上表称王重荣有功于国，请赐其子王珂节钺。',[('李克用','表请授节钺者'),('王珂','被请授节钺者'),('王重荣','奏中已故有功者')],quote='克用表重荣有功于国，请赐其子珂节钺。',note='其子承前段养子，不误生父；重荣为奏中提及，不作895年现场人物。')
event('wang_gong_petitions_exchange_posts','王珙结三帅，再表请交换珂珙辖镇',14,'895年河中继立争议期间；确日未载','陕州、河中、朝廷',
      '王珙厚结王行瑜、李茂贞、韩建，重申王珂非王氏子，要求王珂去陕州、自己领河中。',[('王珙','结帅再表争河中者'),('王行瑜','所结三帅之一'),('李茂贞','所结三帅之一'),('韩建','所结三帅之一'),('王珂','被要求改陕州者')],quote='王珙厚结王行瑜、李茂贞、韩建三帅，更上表称珂非王氏子，请以珂为陕州、珙为河中。',note='非王氏子保争嗣指控，不覆盖父养关系；请交换非已换镇，不作终身同盟。')
event('emperor_rejects_wang_gong_exchange','唐昭宗以已允李克用所奏拒王珙请求',14,'895年王珙再表以后；确日未载','朝廷',
      '唐昭宗告谕王珙等，称先已允李克用所奏，不许交换王珂、王珙辖镇。',[('唐昭宗','拒交换请求者'),('王珙','请求被拒者'),('李克用','先奏已允者')],quote='上谕以先已允克用之秦，不许。',note='秦疑奏，原字保留；已允所奏未另具诏日，不倒推前段请授即已就任。')
event('wang_rong_shizhong','王镕加兼侍中',15,'895年三月条；确日未载',None,
      '王镕加兼侍中。',[('王镕','加官者')])
event('yang_visits_sizhou_tai_display','杨行密至泗州，不悦台濛盛饰供帐',16,'895年攻濠围寿之前；确日未载','淮河、泗州',
      '杨行密沿淮至泗州，防御使台濛盛饰供帐，杨行密不悦。',[('杨行密','至泗州不悦供帐者'),('台濛','盛饰供帐者')],quote='杨行密浮淮至泗州，防御使台濛盛饰供帐，行密不悦。')
event('tai_returns_patched_clothes','台濛使归补绽衣，杨行密言不忘本',16,'895年离泗州以后；确日未载','泗州、卧内',
      '杨行密离开后，台濛在卧内得补绽衣，使人追还。杨行密笑称幼年贫贱、不敢忘本，台濛惭。',[('台濛','发现衣并遣归者'),('杨行密','述不忘本者')],quote='既行，濛于卧内得补绽衣，驰使归之。行密笑曰：“吾少贫贱，不敢忘本。”濛甚惭。',note='贫贱为杨自己回忆，不推生年、贫困年限。')
event('yang_takes_haozhou_zhang_sui','杨行密攻取濠州，执张璲',16,'895年围寿以前；确日未载','濠州',
      '杨行密攻下濠州，俘获刺史张璲。',[('杨行密','攻取者'),('张璲','被执濠州刺史')],quote='行密攻濠州，拨之，执刺史张璲。',note='拨疑拔，保底本；执不作杀，濠州不与濠寿两城合并。')
event('yang_adopts_li_child','杨行密收养军士掠得的徐州李氏八岁子',16,'攻濠条内追述幼年；确年待考','徐州、濠州',
      '杨行密军士掠得徐州李氏八岁之子，杨行密将其收为养子，长子杨渥憎之。',[('杨行密','初收养者'),('李昪','幼年被掠收养者'),('杨渥','憎新养子者')],year=None,quote='行密军士掠得徐州人李氏之子，生八年矣，行密养以为子，行密长子渥憎之',note='掠儿段连及其后成长，确年未另载；八岁不反算生年，李昪同人据新史南唐世家名知诰链补证，徐州系籍贯不作已核被掠地点。')
for row in B['people']:
    if row['key']==people['李昪']:row['aliases']=['徐知诰','知诰']
relation('杨行密','李昪','养父',16,'杨行密是李昪初时养父，后将其交徐温为子。',quote='行密养以为子')
relation('杨行密','杨渥','父亲',16,'杨行密是杨渥父亲，杨渥为其长子。',quote='行密长子渥')
event('yang_gives_child_xu_wen','杨行密将所养李氏子交徐温，徐温名知诰',16,'收养后；确年待考',None,
      '杨行密认为杨渥不能容新养子，将孩子赐给徐温为子；徐温为其取名知诰。',[('杨行密','交养子者'),('徐温','收养并取名者'),('李昪','被交徐温后名知诰者')],year=None,quote='行密谓其将徐温曰：“此儿质状性识，颇异于人，吾度渥必不能容，今赐汝为子。”温名之曰知诰。',note='度渥必不能容为杨判断，非杨渥未来行为已发生；知诰姓徐由补书冒姓徐明证。')
relation('徐温','李昪','养父',16,'徐温是李昪养父，接收杨行密所养子，取名知诰。',quote='今赐汝为子。”温名之曰知诰。')
event('xu_zhi_gao_filial_return','徐知诰受笞逐后迎拜，徐温益爱之',16,'徐温养知诰以后；尝，确年待考',None,
      '知诰勤孝，曾因得罪徐温被笞逐，却仍在门迎拜，表示子不能离父母。徐温因此愈爱之。',[('李昪','以知诰名被逐仍迎拜者'),('徐温','笞逐而后益爱者')],year=None,quote='知诰事温，勤孝过于诸子。尝得罪于温，温笞而逐之；及归，知诰迎拜于门。温问：“何故犹在此？”知诰泣对曰：“人子舍父母将何之！父怒而归母，人情之常也。”温以是益爱之',note='尝为追述，不定895；母仅引语泛称，不由此建具体养母。')
event('xu_zhi_gao_manages_household','徐温使知诰掌家事',16,'笞逐迎拜以后；确年待考',None,
      '徐温让知诰管理家事，家人无违言。',[('徐温','命掌家事者'),('李昪','以知诰名掌家事者')],year=None,quote='使掌家事，家人无违言。')
event('yang_praises_grown_zhi_gao','知诰长成，杨行密称其俊杰',16,'及长；幼年以后，确年待考',None,
      '知诰长大后喜书善射，史书称其识度英伟。杨行密常向徐温称赞知诰俊杰、诸将子不及。',[('李昪','长成被赞者'),('杨行密','称赞者'),('徐温','受言者')],year=None,quote='及长，喜书善射，识度英伟。行密常谓温曰：“知诰俊杰，诸将子皆不及也。”',note='及长跨度不能定为895；诸将子不及为杨评价，不作统计能力结论。')
event('yang_besieges_shouzhou','杨行密围寿州',16,'895年三月丁亥','寿州',
      '杨行密包围寿州。',[('杨行密','围城者')],quote='丁亥，行密围寿州。',note='本段明确当年围寿；不把前面及长等追述也定为当日，未载攻克。')
event('emperor_plans_princely_patrols','唐昭宗拟宗室巡警并抚慰藩镇',17,'895年四月罢诏以前；确日未载','郊畿、宫、陵寝',
      '因郊畿盗贼甚至入宫、犯陵寝，唐昭宗拟让宗室诸王领兵巡警，并派往四方抚慰藩镇。',[('唐昭宗','提出巡警抚慰者')],quote='上以郊畿多盗，至有逾垣入宫或侵犯陵寝者，欲令宗室诸王将兵巡警，又欲使之四方抚慰籓镇。',note='欲令为计划，不补已经出兵诸王或盗贼姓名。')
event('court_opposes_princely_plan','南北司用事臣交章反对宗室领兵',17,'895年四月以前；确日未载','朝廷',
      '南北司用事之臣担心宗室领兵不利于己，交章谏阻。',[('唐昭宗','所提计划受阻者')],quote='南北司用事之臣恐其不利于己，交章论谏。',note='群臣未具名，不凭官职套已有宦官、宰相参与；担忧为史书归因。')
event('emperor_cancels_princely_plan','唐昭宗诏罢宗室巡警抚慰计划',17,'895年夏四月；具体日未载','朝廷',
      '唐昭宗不得已，下诏取消诸王领兵巡警及抚慰藩镇的计划。',[('唐昭宗','下罢诏者')],quote='上不得已，夏，四月，下诏悉罢之。')
event('court_pardons_dong_to_farms','朝廷释董昌罪，纵归田里',18,'895年四月条；具体日未载','朝廷',
      '朝廷以董昌曾勤于贡输，并认为其当下行为似患心疾，下诏释罪，允许其归田里。',[('唐昭宗','朝廷释罪诏令者'),('董昌','诏释罪归田者')],note='类得心疾是诏令理由的比拟，不作医学诊断；纵归田里不表示已经实际卸权归田，后文继续录。')

from urllib.parse import quote as urlquote
supplements=[]
for sk,title,page in [('xinwudaishi-048-895-gao-brothers','新五代史·卷48·高行周传·高氏兄弟',939),('xinwudaishi-062-895-li-bian','新五代史·卷62·南唐世家第二·徐知诰收养',1306)]:
    path='resources/derived/twenty-four-histories/19新五代史.jsonl'
    raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==page)
    url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+f'#L{page}'
    (P/'sources'/(sk+'.txt')).write_bytes(raw)
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author='欧阳修',edition='仓库PDF派生电子文本；未核纸本，换行原字保留。',url=url,note=f'原PDF第{page}页；补主线本段，后世身份不当895年现职。'))
    mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation=f'提取JSONL pdf_page={page}的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,text,n,sk,quote,where,note,kind='corroborates'):
    assert quote in (P/'sources'/(sk+'.txt')).read_text()
    ck=f'claim_zztj_260_0895_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=where,note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='新五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('event','event_zztj_260_0895_keyong_kills_gao_brothers','description','《新五代史》同记思继等多诛犯法律的晋兵，仁恭被责后以高氏为诉，晋诛思继兄弟。',11,'xinwudaishi-048-895-gao-brothers','而晋兵多犯\n法，思继等数诛杀之。克用以责仁\n恭，仁恭以高氏为诉，由是晋尽诛思\n继兄弟。','卷48·杂传第三十六·高行周传·原PDF第939页','两书行动链相应；补书未列该事确年，不据史传顺序推死年。')
extra('event','event_zztj_260_0895_rengong_receives_gao_sons','description','《新五代史》记刘仁恭以高思继兄之子行珪为牙将，将思继子行周收于帐下。',11,'xinwudaishi-048-895-gao-brothers','仁恭以其兄某之子行珪为牙将，\n而思继子行周年十馀岁，亦收之帐\n下，稍长，补以军职。','卷48·杂传第三十六·高行周传·原PDF第939页','诸子名为补书补充，不把高行珪误记为思继亲子；稍长补职亦未定895。','adds')
extra('person',people['李昪'],'aliases','《新五代史》南唐世家称李昪，记杨行密收养后交徐温，冒姓徐氏名知诰。',16,'xinwudaishi-062-895-li-bian','李昪，'+(P/'sources/xinwudaishi-062-895-li-bian.txt').read_text().split('李昪，',1)[1].split('及壮，',1)[0],'卷62·南唐世家第二·原PDF第1306页','本名与知诰同人据同页收养改姓名链；李昪称谓作全站稳定名，不把后来的帝号放到幼年。','adds')
extra('person_relationship',f"relationship_{people['杨行密']}_{people['李昪']}_养父",'description','《新五代史》同记杨行密攻濠得李昪，奇其状貌，养为子。',16,'xinwudaishi-062-895-li-bian','杨行\n密攻濠州，得之，奇其状貌，养以为\n子。','卷62·南唐世家第二·原PDF第1306页','主书军士掠得与补书攻濠得之相应；不反算八岁生日。')
extra('person_relationship',f"relationship_{people['徐温']}_{people['李昪']}_养父",'description','《新五代史》记杨氏诸子不容，行密将所养子交徐温，冒姓徐氏名知诰。',16,'xinwudaishi-062-895-li-bian','而杨氏诸子不能容，行密以乞徐\n温，乃冒姓徐氏，名知诰。','卷62·南唐世家第二·原PDF第1306页','主书具体长子渥与补书诸子表述各存；改姓名可证徐知诰检索别名，不新建第二人。')

reviews={
 11:'背景授都将与久之裁戍兵、李杀、仁恭收诸子分录无确年；在武干疑字留底本，不编兄弟名；新史补高行珪为思继兄子、行周为思继子。',
 12:'通机事背景无起年；崔族传言、两帅指控表、帝回复、三月再罢相分录；杜太慰与联疑字保，不将奏中奸邪当事实，崔族不推辈分。',
 13:'王氏请命河中帅、崔胤诏授与王抟任相分录；崔重复同平章事保底本，不作已赴护国。',
 14:'婿关系明确；李请节钺与王结三帅再请换镇、帝拒分录，指控非事实；已允克用之秦疑奏，保字不定批准日。',
 15:'加王镕兼侍中，不补下诏日。',
 16:'泗州供帐衣服、攻濠执璲、幼年李氏子初养交养与笞逐掌家及长、丁亥围寿逐项；幼年至成年无确年，八岁不反算生年，两养父明示，李昪知诰同人由新史改姓名链补证。',
 17:'宗室巡警抚慰均计划，未具名群臣不补人；交章与四月悉罢分录，未实际巡警。',
 18:'心疾为朝廷判断不作确诊；释罪纵归田里为诏令不作董已卸权。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text())
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,19):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(11,19)],next_paragraph=Q[19]['id'],coverage='第11—18段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
