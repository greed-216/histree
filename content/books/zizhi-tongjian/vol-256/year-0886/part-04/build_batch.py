"""Curate consecutive Tongjian volume 256, year 886 paragraphs 31–40."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 57))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0886-p031-p040', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
B['sources'].append(dict(key=alt,title='资治通鉴·卷256（维基文库固定版803267）',source_type='primary',author='司马光等',edition='维基文库固定修订版电子文本；未核纸本。',url=alt_url,note='用作卷256光启二年“李忠/李全忠”异文校核；同书异本文字，不算独立史书。'))
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭'}
people, used, reused = {}, {}, {source}
supplements=[]

def alt_claim(table,key,field,value,n,quote,note):
    assert quote in alt_raw.decode()
    claim_key=f'claim_zztj_256_0886_04_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=claim_key,subject_table=table,subject_key=key,field_path=field,claim_text=value,source_key=alt,citation=f'卷256·光启二年（886）·{Q[n]["id"]}·维基文库固定版第189行',note=f'原文：{quote}；核对说明：{note}',status='draft'))
    supplements.append(dict(claim_key=claim_key,source_book='zizhi-tongjian-wikisource-803267',primary_paragraph_id=Q[n]['id'],subject_key=key,relation='adds'))

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0886_04_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启二年（886）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('zhou_bao_changzhou','周宝遣丁从实夺常州，张郁奔海陵',31,'光启二年六月后条；具体日未载','常州、海陵',
      '镇海节度使周宝遣丁从实袭常州，逐张郁；张郁投奔镇守海陵的高霸。',
      [('周宝','遣军者'),('丁从实','袭常州者'),('张郁','被逐者'),('高霸','收留者')])
event('lu_yanhong_xuzhou','秦宗权陷许州并杀鹿晏弘',32,'光启二年秋七月','许州',
      '秦宗权攻陷许州，杀时任节度使鹿晏弘。',[('秦宗权','攻城及杀人者'),('鹿晏弘','被杀者')])
event('wang_xingyu_xingzhou','王行瑜攻兴州，杨晟退往文州',33,'光启二年七月条；具体日未载','兴州、文州',
      '王行瑜进攻兴州，感义节度使杨晟弃镇往文州；朝廷命李鋋、李茂贞、陈佩屯大唐峰抵御。',
      [('王行瑜','攻兴州者'),('杨晟','撤往文州者'),('李鋋','屯大唐峰者'),('李茂贞','屯大唐峰者'),('陈佩','屯大唐峰者')])
claim('person',people['李茂贞'],'aliases','李茂贞本姓宋，原名文通。',33,'茂贞，博野人，本姓宋，名文通，以功赐姓名。')
event('wuan_name','钦化军改称武安，周岳任节度使',34,'光启二年七月条；具体日未载','武安军',
      '《通鉴》电子底本记钦化军改号武安，以衡州刺史周岳为节度使；原文首二字作“要命”，有疑字。',
      [('周岳','受任者')],
      note='原仓库底本与维基文库固定版均作“要命钦化军曰武安”，疑有转录讹字；暂不按疑字确定具体诏令用语。')
event_key=event('li_quanzhong_death','李全忠去世，李匡威为卢龙留后（底本缺字）',35,'光启二年八月','卢龙',
      '仓库电子底本作“李忠薨，以其子匡威为留后”；同卷固定版作“李全忠薨”，据前后任卢龙者接续为李全忠去世，子李匡威为留后。',
      [('李匡威','李全忠之子及受任留后者')],
      note='本批同时引用另一固定电子版本补足底本脱“全”字；纸本尚未核。')
pk=registry['李全忠']['key'];people['李全忠']=pk;B['people'].append(dict(registry['李全忠'],status='draft'));reused.add(pk)
alt_quote='八月，盧龍節度使李全忠薨，以其子匡威為留後。'
alt_claim('person',pk,'description','卷256固定版记李全忠去世。',35,alt_quote,'仓库底本脱“全”字；此处仅作同书异文校核。')
edge='participation_zztj_256_0886_li_quanzhong_death_'+pk
B['person_events'].append(dict(key=edge,person_key=pk,event_key=event_key,role='去世者',status='draft'))
alt_claim('person_event',edge,'role','李全忠：去世者。',35,alt_quote,'固定版具名李全忠；仓库底本作“李忠”。')
alt_claim('event',event_key,'description','固定版作李全忠薨，子匡威任留后。',35,alt_quote,'同书异文补足仓库底本脱字，未当作独立史书确证。')
rel='relationship_'+pk+'_'+people['李匡威']+'_父子'
B['person_relationships'].append(dict(key=rel,person_a_key=pk,person_b_key=people['李匡威'],relation_type='父子',description='卷256固定版称李匡威为李全忠之子。',status='draft'))
alt_claim('person_relationship',rel,'description','李匡威为李全忠之子。',35,alt_quote,'仓库底本省一字；固定版明确全名。')
event('wang_chao_quanzhou','王潮攻下泉州并杀廖彦若',36,'光启二年八月条；具体日未载','泉州',
      '王潮攻下泉州，杀刺史廖彦若。',[('王潮','攻城者'),('廖彦若','被杀者')])
event('wang_chao_chen_yan','王潮降陈岩并获泉州刺史任命',36,'泉州陷落之后；具体日未载','泉州、福建',
      '王潮未攻福州，遣使向福建观察使陈岩投降；陈岩上表任王潮为泉州刺史。',
      [('王潮','投降及受任者'),('陈岩','奏请任命者')])
event('wang_xu_suicide','王绪被王潮幽禁后自杀',36,'王潮据泉州之后；具体日未载','泉州',
      '王潮将王绪幽禁于别馆，王绪自杀。',[('王潮','幽禁王绪者'),('王绪','自杀者')],
      note='原文称“绪惭，自杀”；不据此确定具体自杀方式。')
event('datangfeng_battle','李鋋击退张行实于大唐峰',37,'光启二年九月','大唐峰',
      '朱玫部将张行实进攻大唐峰，李鋋等将其击退。',
      [('朱玫','张行实所从统领'),('张行实','进攻者'),('李鋋','击退者')])
event('man_cun_xingzhou','满存败邠军并收复兴州',37,'光启二年九月','兴州、万仞寨',
      '满存击败邠军、收复兴州，进守万仞寨。',[('满存','收复兴州者')])
event('li_kexiu_xingzhou','李克修攻孟方立并连取诸镇',38,'光启二年九月甲午及其前后','焦冈、邢州诸镇',
      '李克修攻孟方立，甲午于焦冈擒其将吕臻，攻取故镇、武安、临洺、邯郸、沙河，任安金俊为邢州刺史。',
      [('李克修','领兵及任将者'),('孟方立','被攻者'),('吕臻','被俘者'),('安金俊','受任者')],
      note='本段五地攻取不据此换算为同一公历日。')
event('li_yun_urged','长安百官劝襄王煴即位',39,'光启二年九月后、十月前','长安',
      '太子太师裴璩等长安百官劝襄王煴即皇帝位。',[('裴璩','劝进者'),('李煴','受劝进者')])
event('li_yun_enthroned','襄王煴即皇帝位，改元建贞',39,'光启二年冬十月','长安',
      '襄王煴在长安即皇帝位，改元建贞，遥尊在兴元的僖宗为太上元皇帝。',
      [('李煴','即位者')],
      note='此为朱玫拥立政权的即位与改元，与僖宗行在年号和政令并行；不误记僖宗已退位。')
event('dong_chang_offer','董昌许钱镠取越州后授杭州',40,'光启二年十月条；具体日未载','越州、杭州',
      '董昌向钱镠提出取越州后将杭州交给钱镠，钱镠同意并领兵出征。',
      [('董昌','提出条件者'),('钱镠','领兵者')],
      note='本段仅有承诺，杭州实际任命与交接待后文核实。')
event('qian_liu_fengshan','钱镠进兵丰山，鲍君福归降',40,'董昌建议后；具体月日未载','诸暨、平水、曹娥埭、丰山',
      '钱镠自诸暨进兵，经平水、曹娥埭；浙东将鲍君福率众降之。钱镠屡败浙东军，进屯丰山。',
      [('钱镠','进兵者'),('鲍君福','归降者')],
      note='“凿山开道五百里”为史书所记里数，未换算现代路程。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(31,41):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {34:'底本与固定版皆作“要命”，疑有讹字；不擅改。',35:'底本作“李忠”，固定版作“李全忠”；保留两版原文，人物接续李全忠。',36:'王潮攻泉州、向陈岩归降、王绪自杀分录。',39:'襄王煴政权改元建贞，与僖宗行在并行。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(31,41):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=886,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(31,41)],next_paragraph='zztj-v256-y0886-p041',coverage='卷256光启二年条第31至40段；本年尚未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
