"""Curate consecutive Tongjian volume 256, year 886 paragraphs 21–30."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 57))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0886-p021-p030', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-256-884'
prior = json.loads((ROOT / 'content/books/zizhi-tongjian/vol-256/year-0884/part-01/content-batch.json').read_text())
B['sources'] = [next(s for s in prior['sources'] if s['key'] == source)]
raw = (ROOT / 'resources/derived/tongjian/256.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/256.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0886_03_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启二年（886）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启二年条所见人物：{name}。',biography=None,status='draft')
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

event('zhu_mei_appointments','朱玫在襄王煴名下大行封拜',21,'光启二年五月','京师及诸镇',
      '朱玫把萧遘改任太子太保，自加侍中及盐铁、转运等职，并安排裴澈、郑昌图、高骈、吕用之等人职务，以争取诸藩镇。',
      [('朱玫','主导封拜者'),('萧遘','改任太子太保者'),('裴澈','判度支者'),('郑昌图','判户部者'),('高骈','兼中书令者'),('吕用之','获授岭南东道节度使者')],
      note='这是朱玫拥立的襄王煴方面的封拜；不把任命视为各人实际到镇。')
event('zhu_mei_envoys','朱玫遣使宣谕河北、江淮',21,'光启二年五月','河北、江淮',
      '朱玫遣夏侯潭赴河北、杨陟赴江淮宣谕；《通鉴》记不少藩镇受其命，高骈又上笺劝进。',
      [('朱玫','遣使者'),('夏侯潭','赴河北者'),('杨陟','赴江淮者'),('高骈','上笺劝进者')],
      note='“什六七”为本书的概括性比例，不换算为确定的藩镇数量。')
event('lv_yongzhi_power','吕用之在淮南自建幕府并扩张权力',22,'光启二年五月后条；确日未载','淮南',
      '吕用之建牙开幕，逼高骈亲信和能任事将校归从自己，行事不再请示高骈；高骈暗中想夺其权而未能。',
      [('吕用之','扩权者'),('高骈','被架空者')])
event('lv_secret_letter','郑杞、董瑾为吕用之作密信',22,'前事次日；确月日未载','淮南',
      '吕用之因高骈疑忌而询问郑杞、董瑾；次日二人写密信交给吕用之，信中内容原文未载。',
      [('吕用之','求策及受信者'),('郑杞','作信者'),('董瑾','作信者')],
      note='《通鉴》明称“其语秘，人莫有知者”，不得编造密信内容。')
event('xiao_gu_yongle','萧遘称病归永乐',23,'光启二年五月后条；具体日未载','永乐',
      '萧遘称病，返回永乐。',[('萧遘','称病归去者')])
event('li_changfu_break','李昌符与朱玫分裂，向兴元通表',24,'光启二年五月后条；具体日未载','凤翔、兴元',
      '李昌符原与朱玫共同谋立襄王煴，后因朱玫专权不满，不受其官，转向兴元上表；朝廷加李昌符检校司徒。',
      [('李昌符','转向兴元者'),('朱玫','与其分裂者'),('李煴','先前谋立对象')],
      note='本段以“初”追述原先合作；改向兴元为当前叙事，合作起年未据此定为886年。')
event('wang_xingyu_pursuit','王行瑜奉朱玫命追车驾，占凤州',24,'光启二年五月后条；具体日未载','散关、凤州',
      '朱玫遣王行瑜率军追车驾。杨晟数次战斗后弃散关，王行瑜进屯凤州。',
      [('朱玫','遣兵者'),('王行瑜','追击者'),('杨晟','退守者')],
      note='“五万”为本书所记出兵数字，不据此推定实到人数。')
event('xingyuan_shortage','贡赋多往长安，兴元行在粮食不足',25,'光启二年五月后条；具体日未载','兴元、长安',
      '《通鉴》记诸道贡赋多送长安而非兴元，随驾官员和卫士缺粮。',
      note='时局总述仅录原文所称供给方向与缺粮，不推算财政总额。')
event('liu_chongwang_hezhong','刘崇望赴河中劝王重荣归顺',25,'光启二年五月后条；具体日未载','兴元、河中',
      '杜让能建议遣使劝王重荣归朝；皇帝遣刘崇望赍诏往河中。王重荣听命，上表称献绢十万匹并请求讨朱玫。',
      [('杜让能','建言者'),('刘崇望','奉诏出使者'),('王重荣','听命及上表者'),('朱玫','王重荣请讨对象')],
      note='十万匹为王重荣表称献绢数，未核实际交付；杜让能关于人际关系的判断保留为其建言。')
event('li_yun_false_notice','襄王煴使者向李克用谎称僖宗驾崩',26,'光启二年戊戌；月份本段未明','晋阳',
      '襄王煴遣使赐李克用诏，诏中声称皇帝途中驾崩、自己已受册；这是襄王方面的说辞。朱玫也致书李克用。',
      [('李煴','遣诏者'),('李克用','受诏者'),('朱玫','致书者')],
      note='诏书的“晏驾”说法与僖宗仍在兴元的叙事冲突，不能当作僖宗已死。')
event('li_keyong_rejects_yun','李克用拒襄王煴，声讨朱玫',26,'收到诏书之后；具体日未载','晋阳',
      '盖寓劝李克用讨朱玫、黜襄王煴；李克用焚诏、拘使，并向邻道发檄声讨朱玫。',
      [('盖寓','劝谏者'),('李克用','焚诏及发檄者'),('朱玫','被声讨者'),('李煴','被拒斥者')],
      note='李克用檄文中“三万兵”等为其宣告，不据此核定实际出兵量。')
event('qin_xian_weishi','朱全忠在尉氏南击败秦贤',27,'光启二年五月后条；具体日未载','尉氏南',
      '秦贤攻宋、汴，朱全忠在尉氏南击败秦贤部。',
      [('秦贤','进攻者'),('朱温','以朱全忠名义获胜者')])
event('guo_yan_caizhou','朱全忠遣郭言攻蔡州',27,'光启二年癸巳；月份本段未明','蔡州',
      '朱全忠遣都将郭言率步骑军攻蔡州。',
      [('朱温','遣兵者'),('郭言','领兵者')],
      note='三万为本书所记军数，不推为确实出动人数。')
event('yang_shouliang_jinshang','杨守亮受命为金商节度使并讨朱玫',28,'光启二年六月','金州、金商',
      '朝廷任杨守亮为金商节度、京畿制置使，令其出金州与王重荣、李克用共讨朱玫。',
      [('杨守亮','受命领兵者'),('王重荣','共同讨朱玫者'),('李克用','共同讨朱玫者'),('朱玫','讨伐对象')],
      note='“兵二万”为诏命叙述中的数字；三方合兵及结果待后文，不先写成已完成会战。')
person('杨守信',28,'杨守亮之弟、杨复光假子')
person('杨复光',28,'杨守亮与杨守信假父')
for child in ['杨守亮','杨守信']:
    rel='relationship_'+people['杨复光']+'_'+people[child]+'_假父'
    B['person_relationships'].append(dict(key=rel,person_a_key=people['杨复光'],person_b_key=people[child],relation_type='假父',description=f'《通鉴》卷256称{child}为杨复光假子；收养年未定。',status='draft'))
    claim('person_relationship',rel,'description',f'{child}为杨复光假子。',28,'与弟信皆为杨复光假子')
rel='relationship_'+people['杨守亮']+'_'+people['杨守信']+'_兄弟'
B['person_relationships'].append(dict(key=rel,person_a_key=people['杨守亮'],person_b_key=people['杨守信'],relation_type='兄弟',description='《通鉴》卷256记杨守信为杨守亮之弟。',status='draft'))
claim('person_relationship',rel,'description','杨守信为杨守亮之弟。',28,'与弟信皆为杨复光假子')
claim('person',people['杨守亮'],'aliases','杨守亮本姓訾，原名亮。',28,'守亮本姓訾，名亮')
event('li_keyong_june_memorial','李克用上表请合力讨朱玫',29,'光启二年六月条；具体日未载',None,
      '李克用遣使上表，称将渡河除逆、迎回车驾，并请朝廷令诸道协力；皇帝把表章示从官和山南诸镇。',
      [('李克用','上表者'),('朱玫','拟讨伐对象')],
      note='“方发兵济河”是李克用表章中的计划，不等于已经渡河。')
event('court_delays_zhu','朝廷劝李克用暂缓对付朱全忠',29,'收到李克用表章后；具体日未载',None,
      '李克用表章仍提朱全忠；朝廷遣杨复恭致书，表示待三辅平定后另有安排。',
      [('李克用','被劝谕者'),('杨复恭','致书者'),('朱温','以朱全忠名义被表章所指者')],
      note='后续安排未明，不推定朝廷已经决定讨伐朱全忠。')
event('tanzhou_battle','周岳攻取潭州，黄皓杀闵勖后亦被杀',30,'光启二年六月条；具体日未载','潭州',
      '衡州刺史周岳攻潭州。钦化节度使闵勖邀黄皓入城共守，黄皓杀闵勖；周岳攻下城，擒杀黄皓。',
      [('周岳','攻城及擒杀黄皓者'),('闵勖','邀援及被杀者'),('黄皓','杀闵勖后被杀者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(21,31):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {21:'朱玫政权的封拜与实际赴任分开；什六七不换算定数。',22:'密信内容原文明确不详，不补写。',24:'“初”追叙李昌符先前共谋；当前记录改向兴元及追驾。',26:'襄王诏称僖宗“晏驾”是虚假宣称，不当事实。',28:'杨守亮、杨守信原名及假父关系分录；二万兵为书载数。',29:'李克用渡河是上表计划，未记成已行动。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(21,31):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=886,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(21,31)],next_paragraph='zztj-v256-y0886-p031',coverage='卷256光启二年条第21至30段；本年尚未完成。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
