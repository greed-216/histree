"""Curate consecutive Tongjian volume 260, year 895 paragraph 6."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p006-p006', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

alias.update({'李溪':'李磎','李谿':'李磎','李存审':'符存审','刘廉':'刘谦'})
n=6
event('dong_consults_imperial_title','董昌议称帝，召将佐商议',n,'895年二月即帝以前；确日未载',None,
      '董昌准备称帝，召集将佐商议。',[('董昌','准备称帝召议者')],quote='董昌将称帝，集将佐议之。')
event('huang_jie_remonstrates','黄碣以受唐恩与灭族之危谏董昌',n,'895年二月即帝以前；确日未载',None,
      '节度副使黄碣劝董昌继续奉唐，指出其受朝廷厚恩、位至将相，并表示宁死为忠臣。',[('黄碣','反对称帝谏者'),('董昌','受谏者')],quote='节度副使黄碣曰：“今唐室虽微，天人未厌。齐桓、晋文皆翼戴周室以成霸业。大王兴于畎亩，受朝廷厚恩，位至将相，富贵极矣，奈何一旦忽为族灭之计乎！碣宁死为忠臣，不生为叛逆！”',note='黄碣复用884年婺州刺史人物；本段任副使。齐桓晋文为引述典故，不列本年在场人物；族灭之计为劝谏风险。')
event('dong_kills_huang_household','董昌杀黄碣及其家八十口',n,'895年称帝议论期间；确日未载',None,
      '董昌怒斥黄碣惑众，斩黄碣，将首级投厕；又杀其家八十口，同坑埋葬。',[('董昌','命杀者'),('黄碣','被斩并株连家属者')],quote='昌怒，以为惑众，斩之，投其首于厕中，骂之曰：“奴贼负我！好圣明时三公不能待，而先求死也！”并杀其家八十口，同坎瘗之。',note='八十口仅黄家；三公为董昌怒语，不当黄碣已有三公官职。')
event('wu_liao_remonstrates_killed','会稽令吴镣谏称帝，遭董昌族诛',n,'895年称帝以前；确日未载','会稽',
      '董昌询问会稽令吴镣，吴镣劝其保诸侯之位以传子孙，反对称帝；董昌族诛吴镣。',[('吴镣','谏言后遭族诛者'),('董昌','询问并族诛者')],quote='又问会稽令吴镣，对曰：“大王不为真诸侯以传子孙，乃欲假天子以取灭亡邪！”昌亦族诛之。',note='地点为任职县而非已知刑场；不写家属人数。')
event('zhang_xun_remonstrates_killed','张逊拒称帝之议，遭董昌杀害',n,'895年称帝以前；确日未载','山阴、浙东',
      '董昌许诺称帝后让山阴令张逊知御史台。张逊以浙东六州未必服从、李锜刘辟前例等劝谏，董昌杀之。',[('张逊','山阴令谏阻被杀者'),('董昌','许官而后杀谏者')],quote='又谓山阴令张逊曰：“汝有能政，吾深知之，俟吾为帝，命汝知御史台。”逊曰：“大王起石镜镇，建节浙东，荣贵近二十年，何苦效李锜、刘辟之所为乎！浙东僻处海隅，巡属虽有六州，大王若称帝，彼必不从，徒守孤城，为天下笑耳！”昌又杀之，谓人曰：“无此三人者，则人莫我违矣！”',note='知御史台是未兑现许诺；近二十年为张逊说辞，不反算董任节度年份；李锜刘辟为典故。')
event('dong_takes_imperial_title','董昌登子城门楼称帝，陈瑞物示众',n,'895年二月辛卯','子城门楼、庭',
      '董昌着礼服登子城门楼即皇帝位，将瑞物陈列于庭示众。',[('董昌','登楼称帝者')],quote='二月，辛卯，昌被兗冕登子城门楼，即皇帝位。悉陈瑞物于庭以示众。',note='兗冕疑衮冕，保留底本，不认瑞物为真实天命；未换算干支日。')
event('luoping_bird_rumor','吴越民间流传罗平天册鸟讹言',n,'咸通末；段内追叙，确年未载','吴、越',
      '《通鉴》追述咸通末吴越间流传山中四目三足鸟的讹言，民间绘像祭祀。',[('董昌','后来援此传言自称鸑鷟者')],year=None,quote='先是，咸通末，吴、越间讹言山中有大鸟，四目三足，声云“罗平天册”，见者有殃，民间多画像以祀之。及昌僭号，曰：“此吾鸑鷟也。”',note='明确讹言与追叙，不记为895年真实动物或祥瑞；董昌角色为后来的援引，不是咸通末造谣已证实。')
event('dong_sets_luoping_shuntian','董昌定大越罗平国号与顺天年号',n,'895年二月称帝后；确日未另载','天册之楼',
      '董昌自称大越罗平国，改元顺天，将城楼题为天册之楼，令群下称其圣人。',[('董昌','定国号年号称号者')],quote='乃自称大越罗平国，改元顺天，署城楼曰天册之楼，令群下谓己曰：“圣人”。')
event('dong_appoints_four_chancellors','董昌任李邈等四人为相',n,'895年称帝后；确日未另载',None,
      '董昌以前杭州刺史李邈、前婺州刺史蒋瑰、两浙盐铁副使杜郢、前屯田郎中李瑜为相。',[('董昌','任相者'),('李邈','前杭州刺史被任相者'),('蒋瑰','前婺州刺史被任相者'),('杜郢','两浙盐铁副使被任相者'),('李瑜','前屯田郎中被任相者')],quote='以前杭州刺史李邈、前婺州刺史蒋瑰、两浙盐铁副使杜郢、前屯田郎中李瑜为相。',note='前官非当年仍任；仅董政权授官，不作唐廷宰相。')
event('dong_appoints_scholars_generals','董昌以吴瑶等为翰林，李畅之等为大将军',n,'895年称帝后；确日未另载',None,
      '董昌以吴瑶等为翰林学士，李畅之等为大将军。',[('董昌','授官者'),('吴瑶','受翰林学士者'),('李畅之','受大将军者')],quote='又以吴瑶等皆为翰林学士、李畅之等皆为大将军。')
event('dong_writes_qian_appointment','董昌告钱镠即国位，称授都指挥使',n,'895年称帝后；确日未另载','两浙',
      '董昌移书钱镠，称权即罗平国位，并以钱镠为两浙都指挥使。',[('董昌','移书自报称帝授官者'),('钱镠','收书被称授官者')],quote='昌移书钱镠，告以权即罗平国位，以镠为两浙都指挥使。',note='董单方面授官，不写钱镠接受或转为其臣。')
event('qian_advises_dong_by_letter','钱镠书劝董昌悔改，董昌不听',n,'895年董昌称帝后；确日未另载',None,
      '钱镠致书劝董昌放弃称帝，保节度使之位并及时悔改；董昌不听。',[('钱镠','致书劝改者'),('董昌','不听书劝者')],quote='镠遗昌书曰：“与其闭门作天子，与九族、百姓俱陷涂炭，岂若开门作节度使，终身富贵邪！及今悛悔，尚可及也！”昌不听',note='九族百姓陷涂炭为警告，不新建已灭九族事件。')
event('qian_army_yingen_remonstrance','钱镠将兵三万至越州迎恩门再谏',n,'895年书劝不听后；确日未另载','越州城下、迎恩门',
      '钱镠将兵三万到越州城下，于迎恩门见董昌，再拜劝其改过，警告朝廷出师将累及乡里士民。',[('钱镠','领兵赴城再谏者'),('董昌','受城下劝谏者')],quote='镠乃将兵三万诣越州城下，至迎恩门见昌，再拜言曰：“大王位兼将相，奈何舍安就危！镠将兵此来，以俟大王改过耳。若天子命将出师，纵大王不自惜，乡里士民何罪，随大王族灭乎！”',note='三万为主书军数；朝廷出师属警告条件，不认本段已发生；不把来谏写成城已攻陷。')
event('dong_rewards_surrenders_instigators','董昌犒军，送吴瑶及巫觋请待罪',n,'895年钱镠城下劝谏后；确日未另载','越州城下',
      '董昌惧，送犒军钱二百万，将首谋者吴瑶与巫觋数人交给钱镠，并请求待罪于天子。',[('董昌','送犒钱交首谋请待罪者'),('吴瑶','被交付首谋者'),('钱镠','收犒军与所送者')],quote='昌惧，致犒军钱二百万，执首谋者吴瑶及巫觋数人送于镠，且请待罪天子。',note='巫觋未具名不编姓名；送钱不等于唐廷已赦，交付吴瑶不作本段已处死。')
event('qian_withdraws_reports_dong','钱镠引兵还，将董昌事上报',n,'895年董昌送犒请待罪后；确日未另载',None,
      '钱镠撤回军队，将董昌之事上报朝廷。',[('钱镠','撤兵具状上报者')],quote='镠引兵还，以状闻。',note='撤兵不表示董政权已灭或称帝已撤销；后续段落续录。')

sk='KR2i0019-001-895-dongchang'
path='resources/originals/kanripo/KR2i0019/KR2i0019_001.txt'
raw=(ROOT/path).read_bytes()
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+path
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='吴越备史·卷1·董昌称帝及谏者',source_type='primary',author='范坰、林禹',edition='Kanripo四部丛刊本电子转录；保留异体字与版页标记，未核纸本。',url=url,note='乾宁二年称帝段及乾宁三年平董昌段内追述；逐条注明追叙位置。'))
mf=json.loads((P/'sources/manifest.json').read_text())
mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='none'))
(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(code,field,text,quote,where,note,kind='corroborates'):
    assert quote in raw.decode()
    ck=f'claim_zztj_260_0895_02_{len(B["claims"])+1:04d}'
    key='event_zztj_260_0895_'+code
    B['claims'].append(dict(key=ck,subject_table='event',subject_key=key,field_path=field,claim_text=text,source_key=sk,citation='卷1·'+where,note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='吴越备史',primary_paragraph_id=Q[6]['id'],subject_key=key,relation=kind))
extra('dong_sets_luoping_shuntian','description','《吴越备史》乾宁二年条同记董昌称帝，国号罗平、改元顺天。','莭度使董昌僣稱皇帝建元順天國號羅平','乾宁二年·16a·原文件345行','该书称罗平，主书称大越罗平；本条用于年号印证，不补完整国号。')
extra('zhang_xun_remonstrates_killed','description','《吴越备史》称被杀山阴令为张遂，主书作张逊，姓名有异。','山陰令張遂曰浙東雖領六州¶\n　大王稱帝彼不從徒守孤城為天下笑昌又殺之','乾宁三年平董昌条追述·22b·原文件487—488行','同官、同谏语同被杀链相应；保存异名，不擅改主书姓名或认定正式更名。','conflicts')
extra('huang_jie_remonstrates','description','《吴越备史》追述黄碣谏董昌，称节度使；主书称节度副使。','莭度¶\n　使黄碣悪其惑亂屢諫','乾宁三年平董昌条追述·22b·原文件488—489行','官衔异文不覆盖主书；追述录为独立书证，不把谏发生年改到896。','conflicts')
extra('dong_rewards_surrenders_instigators','description','《吴越备史》记董昌送犒师钱二亿万，与主书二百万数额不同。','昌于是送犒師錢二億萬','乾宁二年·17a·原文件364行','二亿万按电子底本文字记录，不自行折算；保留数额差异。','conflicts')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger[5].update(event_keys=used[6],batch_key=B['batch_key'],review='董昌称帝长段拆15事件；谋议三谏及不同杀法、即帝授官、书劝出兵与送犒退兵逐项；咸通末鸟为讹言追叙无确年，黄家八十口不推广，张御史仅许诺。吴越备史张遂、黄官衔、犒钱异文独引。',status=status)
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[6]['id']],next_paragraph='zztj-v260-y0895-p007',coverage='第6段长段完整整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
