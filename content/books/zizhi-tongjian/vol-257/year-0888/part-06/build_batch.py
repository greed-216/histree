"""Curate consecutive Tongjian volume 257, year 888 paragraphs 41–49."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 50))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0888-p041-p049', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-257-888'
B['sources'] = [dict(key=source,title='资治通鉴·卷257',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/f3d1c3c15ff4df6cf15204307c37f81ca1275a8a/resources/derived/tongjian/257.txt',note='卷257文德元年起；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/257.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/257.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0888_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·文德元年（888）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷257文德元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=888,note=None,quote=None):
    key='event_zztj_257_0888_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_257_0888_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('xizong_buried','僖宗葬靖陵并定庙号',41,'888年十月辛卯','靖陵',
      '朝廷将惠圣恭定孝皇帝葬于靖陵，定庙号僖宗。',
      [('唐僖宗','安葬及定庙号者')],
      note='本段是葬礼与庙号，不重复记为僖宗此日去世。')
event('chen_tian_prepare_sichuan','陈敬瑄田令孜备兵拒韦昭度',42,'888年十月后；具体日未载','成都、西川',
      '陈敬瑄、田令孜闻韦昭度将至，整军修城以拒。',
      [('陈敬瑄','备战者'),('田令孜','备战者'),('韦昭度','被拒对象')],
      note='“闻将至”不证明韦昭度已抵成都。')
event('shi_pu_wukang_defeat','朱珍败时溥于吴康镇',43,'888年十一月','吴康镇',
      '时溥亲率步骑屯吴康镇，与朱珍军交战，被朱珍击败。',
      [('时溥','败方统领'),('朱珍','胜方将领')],
      note='“七万”为书载兵数，不作实点。')
event('zhang_you_surrenders_su','张友以宿州降朱全忠',43,'888年十一月；具体日未载','宿州',
      '朱全忠另遣军攻宿州，刺史张友投降。',
      [('朱温','以朱全忠名义遣军者'),('张友','投降者')],
      note='攻宿州者未具名，不把朱珍视为该路直接将领。')
event('cai_takes_xuzhou','秦宗权别将陷许州执王蕴',44,'888年十一月丙申','许州',
      '秦宗权部将攻陷许州，拘获忠武留后王蕴；《通鉴》记其重新夺取许州。',
      [('秦宗权','别将所属主将'),('王蕴','被执者')],
      note='攻城别将未具名，不创人物；王蕴只是被执，不推定遇害。')
event('shen_cong_seizes_qin','申丛拘秦宗权归朱全忠',45,'888年十二月','蔡州',
      '蔡州将领申丛拘禁秦宗权，将其折足后归降朱全忠。',
      [('申丛','拘禁及归降者'),('秦宗权','被拘禁者'),('朱温','以朱全忠名义受降者')],
      note='此段未记秦宗权死亡，不提前记处决。')
event('zhu_petitions_shen','朱全忠表申丛蔡州留后',45,'888年十二月；申丛归降后','蔡州',
      '朱全忠上表请任申丛为蔡州留后。',
      [('朱温','以朱全忠名义上表者'),('申丛','被举荐者')],
      note='原文“表”是奏请，不推为诏命已下。')
event('yang_sheng_retreats_four','杨晟昔失兴凤后据文龙成茂',46,'此前；具体年未载','兴州、凤州、文州、龙州、成州、茂州',
      '《通鉴》追叙杨晟失兴、凤后退据文、龙、成、茂四州。',
      [('杨晟','退据四州者')],year=None,
      note='“初”“既失”均为往事回叙，不能记作888年新失州。')
event('tian_lingzi_yang_sheng','田令孜署杨晟威戎军节度使守彭州',46,'王建攻西川后；具体日未载','彭州',
      '田令孜因杨晟为其旧将，假其威戎军节度使之号，令守彭州。',
      [('田令孜','署任者'),('杨晟','受署守彭州者')],
      note='“假”表明田令孜授予权宜职号，不当作朝廷正式任命。')
event('wang_attacks_peng_again','王建攻彭州，山行章屯新繁救援',46,'888年十二月前后；具体日未载','彭州、新繁',
      '王建进攻彭州，陈敬瑄遣眉州刺史山行章率军屯新繁救援。',
      [('王建','攻城者'),('陈建瑄','遣救兵者'),('山行章','眉州刺史及援军将领'),('杨晟','彭州守方')],
      note='底本“陈建瑄”与前后陈敬瑄同一战局且异本文字作“陈敬瑄”，暂归陈敬瑄同人；原文底本不改。“后兵五万”疑转录讹字，兵额不核为实数。')
event('wei_zhaodu_campaign','韦昭度任行营招讨使，王建领永平军',47,'888年十二月丁亥','西川、邛州',
      '朝廷命韦昭度为行营招讨使、杨守亮为副、顾彦朗为行军司马；割邛、蜀、黎、雅置永平军，授王建节度使，治邛州并充诸军都指挥使。',
      [('韦昭度','行营招讨使受任者'),('杨守亮','副使受任者'),('顾彦朗','行军司马受任者'),('王建','永平军节度使受任者')],
      note='官职与分镇分别照原文，不推为四州当日均已受王建实控。')
event('chen_jingxuan_stripped','朝廷削陈敬瑄官爵',48,'888年十二月戊子','',
      '朝廷削去陈敬瑄官爵。',
      [('陈敬瑄','被削官爵者')])
event('yang_shouhou_takes_kuizhou','杨守厚攻陷夔州',49,'888年十二月；具体日未载','夔州',
      '山南西道节度使杨守厚攻陷夔州。',
      [('杨守厚','攻城者')])

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(41,50):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {41:'葬礼不重记为死亡。',42:'韦昭度“将至”不推为已到成都。',43:'时溥与朱珍交战、张友降宿州分录；宿州攻将未具名。',44:'王蕴被执未见死亡。',45:'秦宗权被囚未死；申丛任留后为朱全忠表请。',46:'杨晟失兴凤为追叙；“假”职不等于朝廷任命；“陈建瑄”“后兵”疑讹并保留底本。',47:'官职任命不推为已实控所割四州。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(41,50):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=888,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(41,50)],next_paragraph='zztj-v258-y0889-p001',coverage='卷257文德元年条第41—49段；本年与本卷此年条结束。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
