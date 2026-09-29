"""Curate consecutive Tongjian volume 256, year 885 paragraphs 11–20."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 31))
B = {'format_version': 1, 'batch_key': 'zztj-v256-y0885-p011-p020', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','郭禹':'成汭'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_256_0885_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷256·光启元年（885）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=['郭禹'] if name=='成汭' else [],era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷256光启元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=885,note=None,quote=None):
    key='event_zztj_256_0885_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_256_0885_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

# 河北诸镇与河东、义武之争。联姻仅照原文叙述，不另造亲属姓名。
event('hebei_alliance','李可举与王镕谋攻王处存',11,'光启元年三月后条；具体日未载','易州、无极',
      '李可举、王镕约定合攻王处存并分其地，又说赫连铎攻李克用后方。李可举遣李全忠攻易州，王镕遣兵攻无极；王处存向李克用求援，李克用遣康君立等援救。',
      [('李可举','谋攻及遣兵者'),('王镕','谋攻及遣兵者'),('王处存','被攻及求援者'),('赫连铎','受邀攻河东者'),('李全忠','领兵攻易州者'),('李克用','遣兵援义武者'),('康君立','领兵援义武者')],
      note='李可举、王镕意图与约定据本段叙述；未把王处存与李克用“亲善”推成永久盟约。')
event('qin_zongyan_jingnan','秦宗权遣弟秦宗言攻荆南',12,'光启元年闰月','荆南',
      '秦宗权遣弟秦宗言侵犯荆南。',[('秦宗权','遣兵者'),('秦宗言','领兵者')])
event('tian_army_background','田令孜在蜀募新军',12,'在蜀期间；确年待考','蜀',
      '《通鉴》追叙田令孜在蜀募新军五十四都，分隶两神策军，由十军统辖。',[('田令孜','募军者')],year=None,
      note='原文“初”追叙在蜀旧事；五十四都、每都千人的数字照书载，不用其推定实际总人数。')
event('court_fiscal_strain','朝廷因藩镇截留税收难给军赏',12,'光启元年闰月后条；具体月日未载',None,
      '《通鉴》记藩镇各专租税，朝廷主要收京畿及同、华、凤翔等州租税，难以按时发军赏，士卒有怨言。',
      [('田令孜','为军费发愁者')],note='此为史书的时局总述；不据此量化所有州的实际税额。')
event('salt_ownership_background','王重荣在中和以来控制两池盐利',12,'中和以来；具体起年待考','安邑、解县两池',
      '安邑、解县两池先前由盐铁官榷；中和以来王重荣控制其利，每年献盐三千车供国用。',[('王重荣','控制盐利者')],year=None,
      note='原文“先是”“中和以来”表背景沿革，不把取得盐利定为885年。')
event('tian_salt_office','田令孜兼两池榷盐使，引发王重荣争论',12,'光启元年夏四月','安邑、解县两池',
      '田令孜奏请两池盐利复归盐铁管辖，并于四月兼任两池榷盐使，以盐利供军；王重荣接连上章反对，中使劝谕未果。',
      [('田令孜','奏请及兼使者'),('王重荣','反对者')])
event('kuangyou_dispute','匡祐出使河中，与王重荣部生冲突',12,'光启元年五月前；具体日未载','河中',
      '田令孜养子匡祐出使河中，王重荣厚待而匡祐骄傲，军中不满；王重荣责备其无礼，监军调解，匡祐返回后劝田令孜对付王重荣。',
      [('匡祐','出使及劝田令孜者'),('田令孜','匡祐养父'),('王重荣','接待及责备者')],
      note='原文仅称“令孜养子匡祐”；不补其姓氏。')
rel='relationship_'+people['田令孜']+'_'+people['匡祐']+'_养父'
B['person_relationships'].append(dict(key=rel,person_a_key=people['田令孜'],person_b_key=people['匡祐'],relation_type='养父',description='《通鉴》卷256称匡祐为田令孜养子；收养发生年未据此段确定。',status='draft'))
claim('person_relationship',rel,'description','匡祐为田令孜养子。',12,'令孜养子匡祐使河中',note='只据“养子”录收养关系，发生年份不明。')
event('may_transfers','田令孜五月奏调王重荣、齐克让、王处存',12,'光启元年五月','泰宁、义武、河中',
      '田令孜调王重荣为泰宁节度使、齐克让为义武节度使、王处存为河中节度使，并诏李克用援王处存赴镇；这是一组任命诏令，王重荣随后未依令赴任。',
      [('田令孜','主导调任者'),('王重荣','被调泰宁者'),('齐克让','被调义武者'),('王处存','被调河中者'),('李克用','奉诏援王处存者')],
      note='“徙”“诏”是朝廷命令；王重荣是否到任须与后续段落分辨。')
event('li_keju_yizhou','刘仁恭穴地攻入易州',13,'光启元年五月后条；具体日未载','易州',
      '卢龙军攻易州，刘仁恭掘地道入城并夺取易州。',[('刘仁恭','掘地道攻城者'),('李全忠','前段所记攻易州卢龙军统领')],
      note='李全忠统领攻易州见前段；本段具体掘地入城者为刘仁恭。')
event('li_keyong_wuji','李克用在无极、新城击败成德军',13,'光启元年五月后条；具体日未载','无极、新城、九门',
      '李克用亲率军援无极，败成德军，再攻新城并追至九门；斩首数字依《通鉴》记述。',[('李克用','领兵者'),('王镕','成德节度使；前段遣兵者')],
      note='“万馀级”为本书战报式记数，不据此推算战死总人数。')
event('wang_chucun_yizhou','王处存夜袭收复易州',13,'李克用援无极之际；具体日未载','易州',
      '王处存命士卒披羊皮接近易州城，趁卢龙军出城掠取时攻击，收复易州，李全忠逃走。',
      [('王处存','收复易州者'),('李全忠','败走者')])
event('wang_chongying_office','王重盈加同平章事',14,'光启元年五月后条；具体日未载',None,
      '陕虢节度使王重盈加同平章事。',[('王重盈','受加官者')])
event('li_quanzhong_yuzhou','李全忠败后袭幽州，李可举自焚',15,'光启元年六月','幽州',
      '李全忠败于易州后恐获罪，率残军返袭幽州。六月李可举陷入困境，举族登楼自焚，李全忠自称留后。',
      [('李全忠','袭幽州及自称留后者'),('李可举','自焚者')])
event('luoyang_fall','李罕之弃东都，秦宗权部陷城',16,'光启元年六月后条；相拒数月起点未载','东都、渑池',
      '李罕之与秦宗权将孙儒对峙数月，因兵少粮尽弃东都，西退渑池；《通鉴》记秦宗权军陷东都。',
      [('李罕之','弃城退守者'),('秦宗权','攻城方统领'),('孙儒','秦宗权部将')],
      note='“相拒数月”不据此逆推具体开战月。')
event('li_quanzhong_appointed','李全忠获任卢龙留后',17,'光启元年七月',None,
      '朝廷以李全忠为卢龙留后。',[('李全忠','受任者')])
event('chang_jun_memorial','常浚上疏批评朝廷姑息藩镇',18,'光启元年七月乙巳',None,
      '右补阙常浚上疏，认为朝廷过于姑息藩镇，请整饬刑典。',[('常浚','上疏者')],
      note='奏疏内容是常浚的政见，不作为藩镇行为的独立事实证据。')
event('chang_jun_punished','常浚被贬万州，后获赐死',18,'七月庚戌贬；赐死在其后、确日未载','万州',
      '田令孜党人称常浚奏疏会激怒藩镇；常浚于庚戌被贬万州司户，不久被赐死。',
      [('常浚','被贬及被赐死者'),('田令孜','其党人提出反对意见')],
      note='赐死时间只记“寻”，不可定为七月庚戌同日。')
event('cangzhou_mutiny','沧州军逐杨全玫，推卢彦威留后',19,'光启元年七月后条；具体日未载','沧州、幽州',
      '沧州军变，逐节度使杨全玫，推牙将卢彦威为留后；杨全玫逃往幽州。',
      [('杨全玫','被驱逐者'),('卢彦威','被推留后者')])
event('yichang_dezhou_offices','朝廷任曹诚义昌、卢彦威德州',19,'沧州军变后；具体日未载','义昌、德州',
      '朝廷任保銮都将曹诚为义昌节度使，任卢彦威为德州刺史；原文仅记任命，不说明二人是否赴任。',
      [('曹诚','获任义昌节度使者'),('卢彦威','获任德州刺史者')])
event('sun_ru_burns_luoyang','孙儒焚掠东都后撤走',20,'据东都月余后；确月日未载','东都',
      '孙儒占东都一个多月后焚烧宫室、官寺、民居并大肆劫掠，随后离去。',
      [('孙儒','焚掠及撤走者')],note='“月馀”是占据时长，不能用于倒推入城日。')
event('li_hanzhi_returns','李罕之返回东都',20,'孙儒撤离后；确月日未载','东都',
      '孙儒撤走后，李罕之率众返回东都，于市西筑垒居住。',[('李罕之','返回并筑垒者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(11,21):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {11:'各镇约定合攻义武、王处存求援；亲善与联姻不推为永久盟友。',12:'闰月、四月、五月及追叙旧制分录；任命不等于到任。',13:'卢龙占易州、李克用救无极、王处存收复易州分录。',16:'相拒数月不倒推开战日。',18:'常浚奏疏为政见；庚戌贬与后续赐死不同日。',20:'“月馀”不倒推具体入城日期。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(11,21):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=256,year=885,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(11,21)],next_paragraph='zztj-v256-y0885-p021',coverage='卷256光启元年条第11—20段；本年尚未完成。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
