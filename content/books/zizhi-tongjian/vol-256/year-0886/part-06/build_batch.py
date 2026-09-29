"""Curate consecutive Tongjian volume 256, year 886 paragraphs 49–56."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 57))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0886-p049-p056', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-256-884'
prior = json.loads((ROOT / 'content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json').read_text())
B['sources'] = [next(s for s in prior['sources'] if s['key'] == source)]
raw = (ROOT / 'resources/derived/tongjian/256.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/256.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
alt='tongjian-256-wikisource-803267'
alt_url='https://github.com/greed-216/histree/blob/8b1e06e4d8613a687e3f0af1d3578bd1f87a6470/resources/derived/tongjian/256-wikisource-803267.txt'
alt_raw=(ROOT/'resources/derived/tongjian/256-wikisource-803267.txt').read_bytes()
B['sources'].append(dict(key=alt,title='资治通鉴·卷256（维基文库固定版803267）',source_type='primary',author='司马光等',edition='维基文库固定修订版电子文本；未核纸本。',url=alt_url,note='用作卷256光启二年“李忠/李全忠”及“张环/张瑰”异文校核；同书异本文字，不算独立史书。'))
(P/'sources'/(alt+'.txt')).write_bytes(alt_raw)
manifest=json.loads((P/'sources/manifest.json').read_text())
manifest.append(dict(key=alt,file=alt+'.txt',sha256=hashlib.sha256(alt_raw).hexdigest(),url=alt_url,upstream='resources/derived/tongjian/256-wikisource-803267.txt',transformation='none'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','杨行密':'杨行愍','硃瑾':'朱瑾'}
people, used, reused = {}, {}, {source,alt}
supplements=[]

def alt_claim(table,key,field,value,n,quote,note):
    assert quote in alt_raw.decode()
    claim_key=f'claim_zztj_256_0886_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=claim_key,subject_table=table,subject_key=key,field_path=field,claim_text=value,source_key=alt,citation=f'卷256·光启二年（886）·{Q[n]["id"]}·维基文库固定版第231行',note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=claim_key,source_book='zizhi-tongjian-wikisource-803267',primary_paragraph_id=Q[n]['id'],subject_key=key,relation='adds'))

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0886_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启二年（886）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['宋文通'] if name=='李茂贞' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=886,note=None,quote=None):
    key='event_zztj_256_0886_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_256_0886_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('liu_hanhong_executed','刘汉宏在台州被捕送董昌后遭处决',49,'光启二年十二月条；具体日未载','台州、越州',
      '台州刺史杜雄诱捕刘汉宏，交给董昌；刘汉宏随后被斩。',
      [('杜雄','诱捕及解送者'),('刘汉宏','被斩者'),('董昌','接收刘汉宏者')],
      note='原文“执送董昌，斩之”未明确执刑者，不强指杜雄或董昌亲手杀人。')
event('dong_chang_yuezhou','董昌移镇越州，以钱镠知杭州事',49,'刘汉宏被斩后；具体日未载','越州、杭州',
      '董昌移镇越州，自称知浙东军府事，任钱镠知杭州事。',
      [('董昌','移镇及任命者'),('钱镠','知杭州事者')])
event('li_yun_head_sent','王重荣函送襄王煴首级至行在',50,'光启二年十二月条；具体日未载','河中、兴元行在',
      '王重荣把襄王煴首级函送皇帝行在；刑部建议公开献馘并由百官庆贺。',
      [('王重荣','送首者'),('李煴','首级被送者')],
      note='刑部所请是待审礼议，不在此事件中写成已行献馘礼。')
event('yin_yingsun_rites','殷盈孙建议废襄王煴为庶人、缓行献馘礼',50,'襄王煴首级送至行在后；具体日未载','兴元行在',
      '太常博士殷盈孙上议，主张将襄王煴废为庶人并葬其首，待朱玫首级送至再行献馘称贺；朝廷采纳。',
      [('殷盈孙','上议者'),('李煴','礼议所涉者'),('朱玫','其首级待送者')],
      note='其对李煴罪责与礼制的论断是殷盈孙议论，朝廷接受其处理建议。')
event('liu_jing_mianchi','刘经袭李罕之于渑池，败走洛阳',51,'光启二年十二月条；具体日未载','渑池、洛阳',
      '刘经惧李罕之难制，出兵袭渑池，被李罕之击败，弃洛阳逃走；李罕之追击。',
      [('刘经','进攻及败走者'),('李罕之','击败及追击者')])
event('zhang_quanyi_switch','张全义转与李罕之合兵攻河阳',51,'刘经在渑池战败后；具体日未载','河阳、怀州',
      '刘经先遣张全义阻李罕之渡河。张全义后来与李罕之合兵攻河阳，仍被刘经击败，二人退保怀州。',
      [('刘经','先遣张全义及后击败二人者'),('张全义','转而联李罕之者'),('李罕之','与张全义合兵者')],
      note='同段中张全义前后立场改变，不能把全段记成始终同一阵营。')
event('sun_ru_early','孙儒、刘建锋、马殷曾在蔡州抵黄巢',52,'“初”追叙黄巢时事；确年待考','蔡州',
      '《通鉴》追叙孙儒、刘建锋在蔡州戍守抗黄巢，马殷隶军中；秦宗权叛后几人转属其部。',
      [('孙儒','早年驻蔡州者'),('刘建锋','早年驻蔡州者'),('马殷','早年军中成员'),('黄巢','当时对抗对象'),('秦宗权','后来统领者')],year=None,
      note='段首“初”及“及秦宗权叛”跨越旧事，不能把全部归在886年。')
event('sun_ru_zhengzhou','孙儒攻陷郑州，李璠奔大梁',52,'光启二年岁末总述；具体月日未载','郑州、大梁',
      '秦宗权遣孙儒攻陷郑州，刺史李璠逃往大梁。',
      [('秦宗权','遣兵者'),('孙儒','攻城者'),('李璠','逃走者')],
      note='本段含旧事和岁末叙述，郑州陷落具体月日待其他史料核。')
event('sun_ru_heyang','孙儒取河阳并自称节度使',52,'郑州陷后；具体月日未载','河阳、怀州、泽州',
      '孙儒继而攻陷河阳，诸葛仲方逃往大梁；孙儒自称节度使，张全义据怀州、李罕之据泽州抵御。',
      [('孙儒','攻陷河阳及自称节度使者'),('诸葛仲方','逃往大梁者'),('张全义','据怀州抵御者'),('李罕之','据泽州抵御者')])
event('zhang_ji_liujianfeng','张佶与刘建锋在秦宗权幕下相善',52,'“初”追叙至秦宗权时期；确年待考','蔡州',
      '《通鉴》追叙张佶离开宣州，途经蔡州时被秦宗权留为行军司马；张佶向刘建锋表达对秦宗权的担忧，二人后来相善。',
      [('张佶','留幕及谈话者'),('秦彦','张佶原任职处观察使'),('秦宗权','留张佶者'),('刘建锋','谈话者')],year=None,
      note='张佶关于秦宗权将亡是其个人判断；“初”段起年不明。')
event('weichian_chucheng','杨行愍部在褚城败魏虔',53,'光启二年岁末条；具体月日未载','庐州、褚城',
      '张翱遣魏虔率军攻庐州，庐州刺史杨行愍遣田頵、李神福、张训抵御，于褚城败魏虔。',
      [('张翱','遣兵者'),('魏虔','进攻及战败者'),('杨行愍','遣将者'),('田頵','抵御者'),('李神福','抵御者'),('张训','抵御者')],
      note='“万人”为本书所记出兵规模，不推为实到人数。')
event('tao_ya_shuzhou','许勍袭舒州，陶雅奔庐州',53,'褚城战后条；具体月日未载','舒州、庐州',
      '滁州刺史许勍袭舒州，刺史陶雅逃往庐州。',
      [('许勍','袭城者'),('陶雅','逃走者')])
event('yang_xingmi_renamed','高骈命杨行愍更名杨行密',53,'光启二年岁末条；具体月日未载',None,
      '高骈命杨行愍更名为杨行密；这是同一人改名，不另建人物实体。',
      [('高骈','命名者'),('杨行愍','更名杨行密者')],
      note='人物在数据库现用旧名“杨行愍”作为稳定 key；本条以别名事实索引新名，后续段落继续复用同一 key。')
claim('person',people['杨行愍'],'aliases','杨行愍奉高骈命更名杨行密。',53,'高骈命行愍更名行密')
event('zhu_jin_taining','朱瑾以婚礼掩护袭泰宁治所，逐齐克让',54,'光启二年是岁；具体月日未载','衮州（底本文字待校）',
      '朱瑾以求婚及迎亲为掩护，将兵器暗藏车队，入城后发动伏兵，逐泰宁节度使齐克让，自称留后；朝廷随后任朱瑾为泰宁节度使。',
      [('朱瑾','袭取者及受任者'),('齐克让','被逐者')],
      note='底本作“衮州”，地名疑讹；婚事只是袭城安排，不据此建立已成立的姻亲关系。')
event('zhou_tong_ezhou','周通攻鄂州，路审中逃离',55,'光启二年是岁；具体月日未载','鄂州',
      '周通攻鄂州，路审中离开。',[('周通','攻城者'),('路审中','离城者')])
event('du_hong_wuchang','杜洪入鄂，自称武昌留后并获朝廷授任',55,'路审中离城后；具体月日未载','鄂州、武昌',
      '杜洪趁鄂州空虚进入，自称武昌留后，朝廷随后授任。',[('杜洪','入鄂及受任者')])
event('deng_jinsi_yuezhou','邓进思乘虚攻陷岳州',55,'杜洪离岳州后；具体月日未载','岳州',
      '邓进思趁岳州空虚攻陷该州。',[('邓进思','攻城者')])
event_key=event('qin_zongyan_jingnan_end','秦宗言久围荆南未克而撤',56,'至光启二年岁末；围城起点待考','荆南',
      '秦宗言围荆南历时约二年，守城将领原仓库底本作“张环”，固定异文作“张瑰”；城中粮食匮乏，秦宗言最终未克而去。',
      [('秦宗言','围城未克者')],
      note='“二年”只支持大致历时，不反推准确围城起日；张环/张瑰按同书异文并列，未核纸本。')
alt_quote='秦宗言圍荊南二年，張瑰嬰城自守，城中米斗直錢四十緡，食甲鼓皆盡，擊門扉以警夜，死者相枕。宗言竟不能克而去。'
alt_claim('event',event_key,'description','固定版作张瑰守荆南，秦宗言未能攻下而去。',56,alt_quote,'同书异文对照；仓库底本作“张环”，固定版作“张瑰”。')
pk=registry['张瑰']['key'];people['张瑰']=pk;B['people'].append(dict(registry['张瑰'],status='draft'));reused.add(pk)
alt_claim('person',pk,'description','固定版记张瑰婴荆南城自守。',56,alt_quote,'原底本作“张环”；张瑰为本卷前段已录人物，纸本待核。')
edge='participation_zztj_256_0886_qin_zongyan_jingnan_end_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=event_key,role='守城者',status='draft'))
alt_claim('person_event',edge,'role','张瑰：守城者。',56,alt_quote,'身份据固定异文；仓库底本保留“张环”。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(49,57):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {49:'原文“斩之”未明示执刑者。',50:'刑部建议与殷盈孙获采纳之礼议分录。',51:'张全义前后立场变化分录。',52:'两处“初”所述旧事确年不明。',53:'杨行愍更名杨行密，同一人物稳定 key。',54:'“衮州”疑讹；求婚为袭城安排，不建姻亲。',56:'底本张环，固定异文张瑰；保留两版，不据“二年”倒推起日。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(49,57):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=886,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(49,57)],next_paragraph='zztj-v256-y0887-p001',coverage='卷256光启二年条最后八段；该年共56段至此全部覆盖。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
