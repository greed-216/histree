"""Curate consecutive Tongjian volume 260, year 896 paragraphs 4–7."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p004-p007', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-260-896'
B['sources'] = [dict(key=source,title='资治通鉴·卷260',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/260.txt',note='卷260乾宁三年条；书、卷、年、段落及行号见批次账本。')]
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
    B['claims'].append(dict(key=f'claim_zztj_260_0896_02_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷260乾宁三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=896,note=None,quote=None):
    key='event_zztj_260_0896_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_260_0896_'+code+'_'+pk
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

event('zhang_xiong_guozhou_surrenders','果州刺史张雄降王建',4,'896年闰月丁亥','果州',
      '果州刺史张雄降王建。',[('张雄（果州刺史）','降者'),('王建','受降者')],note='与前录江淮张雄按任职消歧，未经身份连接不合并，也不直接认定必为异人；果州为属地，不补受降地点。')
event('gu_xu_defeat_tang_shicheng','顾全武许再思石城败汤臼',5,'896年二月戊辰','石城',
      '顾全武、许再思在石城击败汤臼。',[('顾全武','胜者'),('许再思','胜者'),('汤臼','败者')],quote='二月，戊辰，顾全武、许再思败汤臼于石城。',note='汤臼复用上批原字人物，败将未明俘或死，不补。')
event('emperor_restores_dong_titles_qian_refuses','皇帝据杨行密请赦董昌复官爵，钱镠不从',5,'896年二月戊辰条；确日未另载','朝廷',
      '唐昭宗依杨行密请求，赦董昌并恢复官爵，钱镠不服从。',[('唐昭宗','赦复者'),('杨行密','奏请者'),('董昌','受赦复者'),('钱镠','不从者')],quote='上用杨行密之请，赦董昌，复其官爵；钱镠不从。',note='与895年请复分开，本段明确赦复；不从未补拒诏原话或永久反唐结论。')
event('li_zi_directs_palace_guard','通王李滋判侍卫诸将事',5,'896年二月条；确日未载','朝廷',
      '朝廷以通王李滋判侍卫诸将事。',[('李滋','受任通王')],quote='以通王滋判侍卫诸将事。',note='唐宗室通王滋按姓李为检索名，保通王滋别名；不补生卒母亲或确日。')
for row in B['people']:
    if row['key']==people['李滋']:row['aliases']=['通王滋']
event('zhu_wen_recommends_zhang_jun_chancellor','朱温荐张浚，皇帝欲复相',6,'896年二月条；确日未载','朝廷',
      '朱温推荐兵部尚书张浚，唐昭宗想让他再次任相。',[('朱温','推荐者'),('张浚','被荐兵部尚书'),('唐昭宗','欲复相者')],quote='硃全忠荐兵部尚书张浚，上欲复相之',note='欲复相不是已正式授任，旧时宰相经历按既录主体，不新造任命。')
event('keyong_opposes_zhang_jun_threatens','李克用请攻朱温，威言张浚朝相则夕至京',6,'896年二月复相议后条；确日未载','朝廷',
      '李克用上表请发兵攻朱温，并称张浚早晨为相，自己晚上便到京师。',[('李克用','上表反对威言者'),('朱温','被请讨者'),('张浚','被反对复相者')],quote='李克用表请发兵击全忠，且言“浚朝为相，臣则夕至阙庭！”',note='威胁与请讨不作已到京、已经攻击朱温，朝夕是条件威言非确切行军时长。')
event('emperor_edict_reconciles_zhang_dispute','京师震惧，皇帝下诏和解复相争议',6,'896年二月李克用表后；确日未载','京师',
      '京师震惧，唐昭宗下诏调解。',[('唐昭宗','下和解诏者')],quote='京师震惧，上下诏和解之。',note='下诏调解不等同所有矛盾已永久解决或本次已经重任张浚。')
alias['李继徽']='杨崇本'
event('li_jihui_tianxiong_governor','天雄留后李继徽正式授节度使',7,'896年三月；确日未载','天雄',
      '朝廷以天雄留后李继徽为节度使。',[('杨崇本','以李继徽名受节度使者')],note='依据主书保天雄，不自动等同魏博军；身份据新五代史杨崇本传补证。留后正式授节度与后书静难任职不作同次。')
for row in B['people']:
    if row['key']==people['杨崇本']:row['aliases']=['李继徽'];row['description']='《资治通鉴》卷260乾宁三年条所见天雄留后李继徽；《新五代史》杨崇本传记其姓名变更。'
person('李茂贞',7,'补书所记收养李继徽者')
# This person claim uses the explicit adoptive-parent evidence below, not the short primary paragraph.
B['claims'].pop()
row=dict(key='relationship_person_李茂贞_person_杨崇本_养父',person_a_key=people['李茂贞'],person_b_key=people['杨崇本'],relation_type='养父',description='李茂贞收养幼年事自己的杨崇本，令其冒姓李名继徽；关系起年未载。',status='draft')
B['person_relationships'].append(row)

from urllib.parse import quote as urlquote
sk='xinwudaishi-yangchongben-jihui-identity';path='resources/derived/twenty-four-histories/19新五代史.jsonl'
raw=next(json.loads(l)['text'].encode() for l in (ROOT/path).read_text().splitlines() if json.loads(l)['pdf_page']==741)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/'+urlquote(path,safe='/')+'#L741'
(P/'sources'/(sk+'.txt')).write_bytes(raw)
B['sources'].append(dict(key=sk,title='新五代史·杨崇本传·李继徽姓名与养亲',source_type='primary',author='欧阳修',edition='仓库PDF派生电子文本；原字换行保留，未核纸本。',url=url,note='原PDF第741页，杨崇本传起首；卷次待核，以固定文件页定位。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=sk+'.txt',sha256=hashlib.sha256(raw).hexdigest(),url=url,upstream=path,transformation='提取JSONL pdf_page=741的text字段，不改字。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
supplements=[]
def extra(table,key,field,text,quote,note):
    assert quote in raw.decode();ck=f'claim_zztj_260_0896_02_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation='杨崇本传起首·原PDF第741页',note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book='新五代史',primary_paragraph_id=Q[7]['id'],subject_key=key,relation='adds'))
q='杨崇本，幼事李茂贞，养以为\n子，冒姓李，名曰继徽'
extra('person',people['杨崇本'],'aliases','杨崇本曾冒姓李，名继徽，即主书李继徽。',q,'同一人物稳定key，未补改名确年；该书后续复杨赐崇本经过另待按史料时间补录。')
extra('person',people['李茂贞'],'biography','李茂贞收养幼事自己的杨崇本。',q,'养亲据补书明文，不借主书同姓继字推测。')
extra('person_relationship',row['key'],'description',row['description'],q,'养父方向茂贞→崇本，幼年起年不定为896，非血亲。')
reviews={
 4:'果州张雄按官职消歧，不凭同名合并江淮张雄。',
 5:'戊辰石城败将、帝赦复董钱不从、通王滋判侍卫分录，钱不从未推永久反唐。',
 6:'朱荐帝欲、李请攻威言、京惧下调解分录，欲相非已相，威言非李已到京。',
 7:'天雄留后李继徽正式节度，补新史杨崇本身份养亲，静难与天雄不混成同次授职，养年未定。',
}
ledger=json.loads((YEAR/'paragraphs.json').read_text());payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(4,8):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review=reviews[n],status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(4,8)],next_paragraph=Q[8]['id'],coverage='第4—7段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
