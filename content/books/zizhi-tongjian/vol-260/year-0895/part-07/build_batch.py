"""Curate consecutive Tongjian volume 260, year 895 paragraphs 29–32."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 75))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0895-p029-p032', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_260_0895_07_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁二年（895）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

alias.update({'李溪':'李磎','李谿':'李磎','李存审':'符存审','阎珪':'李继鹏'})
event('kong_zhang_taizi_binke','孔纬张浚授太子宾客',29,'895年六月辛卯','朝廷',
      '朝廷以前均州刺史孔纬、绣州司户张浚为太子宾客。',[('孔纬','复用授宾客者'),('张浚','复用授宾客者')],quote='辛卯，以前均州刺史孔纬、绣州司户张浚并为太子宾客。',note='绣州按底本，不悄改繡绣为秀；未取前官推二人此时仍治均绣。')
event('kong_returns_rank_libushangshu','孔纬授吏部尚书，恢复阶爵',29,'895年六月壬辰','朝廷',
      '孔纬授吏部尚书，恢复其阶爵。',[('孔纬','授尚书复阶爵者')],quote='壬辰，以纬为吏部尚书，复其阶爵；')
event('kong_reappointed_chancellor','孔纬授司空兼门下侍郎同平章事',29,'895年六月癸已；底本日字如此','朝廷',
      '孔纬授司空，兼门下侍郎、同平章事。',[('孔纬','再任相者')],quote='癸已，拜司空，兼门下侍郎、同平章事。',note='癸已疑癸巳，原字保留，不换算公历日。')
event('zhang_jun_bingbu_rent_commission','张浚授兵部尚书诸道租庸使',29,'895年六月复用条；确日未另载','朝廷',
      '张浚授兵部尚书、诸道租庸使。',[('张浚','受尚书租庸使者')],quote='以张浚为兵部尚书、诸道租庸使。',note='紧承癸已条但未另明确干支，不强写所有官都同日。')
event('emperor_recalls_staunch_kong_zhang','唐昭宗因朋党倾轧而骤用孔纬张浚',29,'895年六月再用时','华州、长水、朝廷',
      '孔纬时居华州，张浚居长水。唐昭宗因崔昭纬等外结藩镇、朋党相倾，想用骨鲠之士，迅速复用二人。',[('唐昭宗','骤用二人者'),('孔纬','华州居者'),('张浚','长水居者'),('崔昭纬','史书所述外结者')],quote='时纬居华州，浚居长水，上以崔昭纬等外交籓镇，朋党相倾，思得骨鲠之士，故骤用纬、浚。',note='动机依史书叙述，不另造幕后谈话；仅居所不补任官地点坐标。')
event('kong_ill_borne_to_capital_declines','孔纬患病扶舆入京，辞命未许',29,'895年六月受命后；确日未载','京师',
      '孔纬有病，扶舆到京师见皇帝，涕泣固辞，皇帝不许。',[('孔纬','患病入京辞命者'),('唐昭宗','不许辞者')],quote='纬以有疾，扶舆至京师，见上，涕泣固辞；上不许。',note='未载病名，不作具体诊断、痊愈或死亡；不许辞不表示已办理全部入署手续。')
event('keyong_south_army_petition','李克用大举蕃汉兵南下，表请讨三帅',30,'895年七月朔到河中以前；确日未载','河东、关中',
      '李克用大举蕃汉兵南下，上表指王行瑜、李茂贞、韩建称兵犯阙、杀害大臣，请求讨伐。',[('李克用','举军表请讨者'),('王行瑜','被请讨者'),('李茂贞','被请讨者'),('韩建','被请讨者')],quote='李克用大举蕃、汉兵南下，上表称王行瑜、李茂贞、韩建称兵犯阙，贼害大臣，请讨之',note='表称与主书前段杀害相照，但请讨不作已有正式总讨诏；蕃汉兵不编民族或军数。')
event('keyong_proclaims_three_towns','李克用移檄三镇，三帅惧',30,'895年南下时；确日未载','三镇',
      '李克用向三镇发檄，王行瑜等大惧。',[('李克用','移檄者'),('王行瑜','受檄三帅之一'),('李茂贞','受檄三帅之一'),('韩建','受檄三帅之一')],quote='又移檄三镇，行瑜等大惧。',note='檄未保存全文，不补完整檄文或特定罪条。')
event('keyong_attacks_jiangzhou','王瑶闭城拒李克用，绛州旬日被克',30,'895年南下途中；攻城旬日，确日未载','绛州',
      '李克用军到绛州，刺史王瑶闭城抵拒。李克用进攻，十日后攻下。',[('李克用','攻城者'),('王瑶','闭城抵拒者')],quote='克用军至绛州，刺史王瑶闭城拒之；克用进攻，旬日，拔之。',note='旬日作为原书时长，不反算围城开始与结束干支。')
event('keyong_executes_wang_yao_thousand','李克用斩王瑶，杀城中违拒者千余',30,'895年绛州攻克后；确日未载','绛州、军门',
      '李克用在军门斩王瑶，并杀城中抵拒者一千余人。',[('李克用','命诛者'),('王瑶','军门被斩者')],quote='斩瑶于军门，杀城中违拒者千馀人。',note='千余为概数；违拒者没有明确全是平民或全是军士，不擅分类。')
event('keyong_hezhong_wang_ke_greets','李克用至河中，王珂迎谒',30,'895年秋七月丙辰朔','河中、路',
      '李克用到河中，王珂在路迎谒。',[('李克用','至河中者'),('王珂','迎谒者')],quote='秋，七月，丙辰朔，克用至河中，王珂迎谒于路。')
event('xingyue_defeated_chaoyi','王行约败于朝邑',31,'895年七月戊午以前；确日未載','朝邑',
      '匡国节度使王行约在朝邑战败。',[('王行约','战败者')],quote='匡国节度使王行约败于朝邑',note='主书未明该战敌将，不自动补李克用亲自击败。')
event('xingyue_abandons_tongzhou','王行约弃同州逃京师',31,'895年七月戊午弃城；己未至京','同州、京师',
      '王行约戊午弃同州逃走，己未到京师。',[('王行约','弃城奔京者')],quote='戊午，行约弃同州走，己未，至京师。',note='保两个阶段日，不将旧史己未弃城覆盖主书。')
event('wang_brothers_plunder_west_market','王行实与王行约率众掠西市',31,'895年七月王行约至京以后；确日未另载','京师、西市',
      '王行约之弟、左军指挥使王行实率众与王行约大掠西市。',[('王行实','左军指挥使掠市者'),('王行约','共同掠市者')],quote='行约弟行实时为左军指挥使，帅众与行约大掠西市。')
relation('王行约','王行实','兄长',31,'王行约是王行实兄长。',quote='行约弟行实时为左军指挥使')
event('xing_shi_asks_flee_binzhou','王行实奏称同华已没，请帝幸邠州',31,'895年七月王氏掠西市后；确日未载','京师、邠州',
      '王行实上奏称同州、华州已经失守、沙陀将到，请皇帝去邠州。',[('王行实','以失守说请移驾者'),('唐昭宗','被请幸邠者')],quote='行实奏称同华已没，沙陀将至，请车驾幸邠州。',note='同华已没与沙陀将至为王奏说辞，不独据此录华州已失守或军已至京。')
event('luo_asks_flee_fengxiang','骆全瓘请帝幸凤翔',31,'895年七月庚申','京师、凤翔',
      '枢密使骆全瓘上奏请皇帝去凤翔。',[('骆全瓘','请幸凤翔者'),('唐昭宗','被请幸凤翔者')],quote='庚申，枢密使骆全瓘奏请车驾幸凤翔。')
event('emperor_refuses_panic_relocation','唐昭宗称李克用尚在河中，令各抚本军',31,'895年七月庚申条','京师、河中',
      '唐昭宗称已收到李克用表，其军尚驻河中，即使沙陀到来也自有应对；令诸臣安抚本军，不得摇动。',[('唐昭宗','拒仓促移驾并令安军者'),('李克用','表中河中驻军者')],quote='上曰：“朕得克用表，尚驻军河中。就使沙陀至此，朕自有以枝梧，卿等但各抚本军，勿令摇动。”',note='尚驻河中为皇帝转述表报；就使为假设，不写军已至京。')
person('李继鹏',32,'右军指挥使，李茂贞假子，本姓名阎珪')
for row in B['people']:
    if row['key']==people['李继鹏']:row['aliases']=['阎珪']
person('李茂贞',32,'李继鹏假父')
relation('李茂贞','李继鹏','养父',32,'李茂贞是李继鹏的养父；原书称其为假子。',quote='右军指挥使李继鹏，茂贞假子也，本姓名阎珪')
claim('person',people['李继鹏'],'aliases','李继鹏本姓名阎珪。',32,quote='本姓名阎珪')
event('right_army_plots_fengxiang_abduction','李继鹏骆全瓘谋劫帝去凤翔',32,'895年七月京师乱前；确日未另载','京师、凤翔',
      '右军指挥使李继鹏与骆全瓘谋劫皇帝去凤翔。',[('李继鹏','谋劫右军指挥使'),('骆全瓘','共谋劫者'),('唐昭宗','拟被劫者')],quote='与骆全瓘谋劫上幸凤翔。',note='谋劫与实际出幸区分；不是皇帝已答允凤翔。')
event('left_army_plots_binzhou_abduction','刘景宣王行实欲劫帝去邠州',32,'895年七月知右军谋劫以后；确日未另载','京师、邠州',
      '中尉刘景宣与王行实得知右军计划后，欲劫皇帝去邠州。',[('刘景宣','谋劫中尉'),('王行实','共谋劫者'),('唐昭宗','拟被劫者')],quote='中尉刘景宣与王行实知之，欲劫上幸邠州。')
event('kong_confronts_liu_palace_departure','孔纬面折刘景宣，不可轻离宫阙',32,'895年七月京师乱前；确日未另载','宫阙',
      '孔纬当面驳斥刘景宣，认为不可轻易离开宫阙。',[('孔纬','面折者'),('刘景宣','受驳者')],quote='孔纬面折景宣，以为不可轻离宫阙。')
event('jipeng_renewed_departure_petitions','李继鹏向晚连奏请帝出幸',32,'895年七月京师乱日向晚；确日未另载','京师',
      '李继鹏向晚接连上奏，请皇帝出幸。',[('李继鹏','连奏请幸者'),('唐昭宗','被请出幸者')],quote='向晚，继鹏连奏请车驾出幸',note='连奏非帝已行，向晚保相对时段不换成具体钟点。')
event('left_attacks_right_army','王行约引左军攻右军',32,'895年七月向晚请幸后；确日未另载','京师',
      '王行约率左军攻击右军。',[('王行约','引左军攻者'),('李继鹏','右军指挥使一方')],quote='于是王行约引左军攻右军，于楼前侍卫。',note='于楼前侍卫原句断句与修饰未定，不补某殿侍卫阵地或双方伤亡；补书同记两军相攻。')
event('jipeng_burns_palace_gate','李继鹏纵火焚宫门',32,'895年七月两军相攻时；确日未另载','宫门、京师',
      '李继鹏纵火焚烧宫门，烟焰蔽天。',[('李继鹏','纵火者')],quote='继鹏复纵火焚宫门，烟炎蔽天。')
event('emperor_summons_yanzhou_six_units','唐昭宗召盐州六都兵入卫',32,'895年七月两军相攻时；确日未另载','京师',
      '盐州六都兵原驻京师，为两军所惮；皇帝急召入卫。',[('唐昭宗','召六都兵入卫者')],quote='时有盐州六都兵屯京师，素为两军所惮，上急召令入卫',note='六都是军队单位，不写为六名士兵、六千兵或由盐州新赶到京师。')
event('two_armies_retreat_to_towns','六都兵至，两军退归邠州凤翔',32,'895年七月盐州兵入卫后；确日未另载','京师、邠州、凤翔',
      '盐州六都兵到来后，两军退走，分别归邠州和凤翔。',[('唐昭宗','所召兵入卫后的皇帝')],quote='既至，两军退走，各归邠州及凤翔。',note='两军退走不作主帅王行瑜、李茂贞亲自都在京或已永久放弃宫廷干预。')
event('emperor_flees_to_li_jun_camp','京师乱，唐昭宗与诸王亲近幸李筠营',32,'895年七月两军退走后；确日未另载','京师、李筠营',
      '城中大乱、互相抢掠，唐昭宗与诸王及亲近之人去李筠军营。',[('唐昭宗','避乱幸军营者'),('李筠','所幸军营所属者')],quote='城中大乱，互相剽掠，上与诸王及亲近幸李筠营',note='诸王未具名不自动补所有宗室；本段目的地是李筠营，不改写成已幸邠凤或后段石门。')
event('li_jushi_protective_followup','护跸都头李居实率众继至',32,'895年七月帝幸李筠营后；确日未另载','李筠营',
      '护跸都头李居实率众随后到来。',[('李居实','护跸都头率众者'),('唐昭宗','护驾对象')],quote='护跸都头李居实帅众继至。',note='李居实与王行实为不同姓名官职，未混同；未载军数不补。')

from urllib.parse import quote as urlquote
sk='jiuwudaishi-026-895-capital-army-clash';path='resources/derived/twenty-four-histories/18旧五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==596)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L596'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='旧五代史·卷26·武皇纪下·绛州与京师兵乱',source_type='primary',author='薛居正等',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第596页，乾宁二年六月、七月段。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=596的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(table,key,field,text,n,quote,note,kind='corroborates'):
    assert quote in raw.decode()
    ck=f'claim_zztj_260_0895_07_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation='卷26·唐书二·武皇纪下·乾宁二年段·原PDF第596页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='旧五代史',primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('event','event_zztj_260_0895_keyong_executes_wang_yao_thousand','description','《旧五代史》同记攻绛州旬日克、斩王瑶军门、诛其党千余。',30,'皇攻之，旬日而拔，斩王瑶于军门，\n诛其党千余人。','主书城中违拒者与补书其党各保对象表述，不自行认全为平民。')
extra('event','event_zztj_260_0895_xingyue_abandons_tongzhou','time_original','《旧五代史》记己未王行约弃城奔京，主书记戊午弃城、己未至京。',31,'己未，同州节度使王行约弃城奔\n京师','日与动作范围不全同，不将主书记日改成己未；官称同州与主书匡国对应，不据补书抹去五月调镇请求。','conflicts')
extra('person',people['李继鹏'],'aliases','《旧五代史》同记李继鹏为茂贞假子，本姓阎名珪。',32,'右军指挥使李继鹏，茂贞假子\n也，本姓阎，名珪','独立印证本名与养亲，不与另一假子杨崇本李继徽混同。')
extra('event','event_zztj_260_0895_left_attacks_right_army','description','《旧五代史》记两军相攻，纵火烧内门，烟火蔽天。',32,'两军相攻，纵火烧内门，烟火蔽天。','补书未具体归纵火于李继鹏；主书指名与补书概述独立保留，不扩推其二人亲自各烧一门。')
reviews={
 29:'辛卯宾客、壬辰复阶授吏部、癸已司空相与张浚兵部租庸逐步；癸已疑巳保字；居所、帝用意、孔病固辞不许分录，不补病名。',
 30:'南下表请与檄、绛城闭拒旬日克、军门斩王瑶并杀违拒千余、丙辰朔河中迎谒分录；奏有说话人，未明伤亡分类不补。',
 31:'朝邑败敌未名；戊午弃己未至、兄弟掠市、行实奏同华没请邠与庚申骆请凤、帝拒动分别；虚报内容不独当城陷事实。旧史己未弃城另引异说。',
 32:'继鹏阎珪假子身份有句和旧史独证；左右军谋劫未执行、孔面折、向晚连奏、行约攻右与火、六都召卫、两军退、帝幸李筠营和李居实继至各录；楼前侍卫断句不补殿名，六都非人数，三李两王不混。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(29,33):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=895,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(29,33)],next_paragraph=Q[33]['id'],coverage='第29—32段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
