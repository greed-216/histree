"""Curated Zhu Wen background batch. Rebuilds local artifacts; never writes to the database."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
B={'format_version':1,'batch_key':'late-tang-zhu-wen-852-883',**{k:[] for k in ['people','events','person_events','person_relationships','sources','claims','topics']}}
texts={}; manifest=[]
# The immutable upstream files were already committed before this batch.
revision='d6cb65361c67ab0cb766ab888a30011542c24510'
def source(key,title,path,author,text=None):
 raw=path.read_text() if text is None else text
 (OUT/'sources'/f'{key}.txt').write_text(raw)
 texts[key]=raw
 url=f'https://github.com/greed-216/histree/blob/{revision}/{path.relative_to(ROOT)}'
 B['sources'].append(dict(key=key,title=title,source_type='primary',author=author,edition='仓库电子文本；未核纸本。引文保留底本文字，PDF抽取文本仅合并排版空白。',url=url,note='摘录与校核范围见本批 README；电子文本可能有转录讹误。'))
 manifest.append(dict(key=key,file=f'{key}.txt',sha256=hashlib.sha256(raw.encode()).hexdigest(),url=url,upstream_file=str(path.relative_to(ROOT)),transformation='原文快照' if text is None else 'PDF第1—3页派生文本：移除页眉、页码和排版空白，按页保留分隔'))
source('jiuwudaishi-1','旧五代史·卷一·梁书太祖纪一',ROOT/'content/later-liang-907-923/sources/jiuwudaishi-1.txt','薛居正等；清代辑佚')
p=ROOT/'resources/derived/twenty-four-histories/19新五代史.jsonl'
new=[]
for line in p.read_text().splitlines()[:3]:
 row=json.loads(line);t=re.sub(r'新五代史\s*\d+/1627','',row['text']);new.append(f"【PDF第{row['pdf_page']}页】\n"+re.sub(r'\s+','',t))
source('xinwudaishi-1-early','新五代史·卷一·梁本纪第一（朱温早年）',p,'欧阳修','\n'.join(new)+'\n')
for n in [254,255]:source(f'tongjian-{n}-late-tang',f'资治通鉴·卷{n}',ROOT/f'resources/derived/tongjian/{n}.txt','司马光等')
O='jiuwudaishi-1';N='xinwudaishi-1-early';T='tongjian-254-late-tang';U='tongjian-255-late-tang'
def quote(src,start,end=None):
 t=texts[src];a=t.index(start);return t[a:a+len(start)] if end is None else t[a:t.index(end,a)+len(end)]
def claim(table,key,field,text,src,q,note='按原文陈述，不补入原文未载的日期或细节。'):
 assert q in texts[src],q
 B['claims'].append(dict(key=f'claim_early_{len(B["claims"])+1:03}',subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=src,citation={'jiuwudaishi-1':'卷一·梁太祖纪一',N:'卷一·梁本纪第一；PDF第1—3页',T:'卷二百五十四·唐纪七十',U:'卷二百五十五·唐纪七十一'}[src],note=f'原文：{q}；核对说明：{note}',status='draft'))
family=quote(N,'太祖神武','而温尤凶悍。')
birth=quote(O,'以唐大中六年','生于碭山縣午溝里。')
join=quote(N,'唐僖宗乾符四年','存、温亡入贼中。')
surrender=quote(U,'黄巢所署同州防御使','瞳，福州人也。')
keys={}
def person(name,key,desc,src,q,aliases=None,birth_year=None,death_year=None):
 keys[name]=key;B['people'].append(dict(key=key,name=name,aliases=aliases or [],era='晚唐',birth_year=birth_year,death_year=death_year,description=desc,biography=desc,status='draft'));claim('person',key,'biography',desc,src,q)
person('朱温','person_zhu_wen','朱温，后赐名朱全忠，又名朱晃，后梁建立者。籍贯宋州砀山午沟里；父亲朱诚以《五经》教授乡里，父亡后家贫，与母亲、兄长在萧县刘崇家佣食。877年随兄朱存加入黄巢军，882年归唐并获赐名全忠，883年入镇汴州。907年称帝，912年在宫廷政变中被杀。',N,family,['朱全忠','朱晃','梁太祖'],852,912)
# Existing 907/912 claims remain attached; this batch adds field-level evidence below.
B['claims'][-1]['claim_text']='朱温籍贯宋州砀山午沟里；父朱诚教授《五经》，父亡后家贫，随母兄在刘崇家佣食。'
claim('person','person_zhu_wen','birth_year','朱温生于852年，原纪年为唐大中六年十月二十一日。',O,birth,'年号换算为852年；十月二十一日保留为传统历日，不换算公历月日。旧五代史此卷为清代辑佚本。')
person('朱诚','person_朱诚','朱温、朱全昱、朱存之父，以《五经》教授乡里。',N,family)
person('王氏（朱温母）','person_王氏_朱温母','朱温之母，姓王氏；丈夫去世后携子寄居萧县刘崇家。',O,quote(O,'帝卽誠之第三子','母曰文惠王皇后。'),['文惠王皇后'])
claim('person',keys['王氏（朱温母）'],'biography','王氏丧夫后携子寄居刘崇家。',T,quote(T,'温少孤贫','依萧县刘崇家，'))
person('朱全昱','person_朱全昱','朱诚长子、朱温兄长，早年与母亲、兄弟在刘崇家佣食。',N,family)
person('朱存','person_朱存','朱温兄长，877年与朱温一同加入黄巢军。',N,join)
claim('person',keys['朱存'],'biography','朱存是朱诚之子、朱温兄长。',N,family)
person('刘崇','person_刘崇_萧县','萧县人。朱温父亲去世后，朱温一家在其家佣食。',N,family)
person('黄巢','person_黄巢','晚唐起兵者。朱温早年在其军中，曾受命驻守东渭桥并招降诸葛爽。',T,quote(T,'诸葛爽以','爽遂降于巢。'))
person('王重荣','person_王重荣','晚唐河中节度使；882年朱温举同州归附，王重荣接纳并上奏。',O,quote(O,'時河中節度使王重榮','重榮卽日飛章上奏，'))
person('胡真','person_胡真','朱温亲将，882年与谢瞳劝朱温归唐。',U,surrender)
person('谢瞳','person_谢瞳','福州人，朱温亲将；882年劝朱温归唐，后奉表赴唐帝行在。',U,surrender)
def relationship(a,b,kind,desc,src,q):
 key=f'rel_early_{a}_{b}_{kind}';B['person_relationships'].append(dict(key=key,person_a_key=keys[a],person_b_key=keys[b],relation_type=kind,description=desc,status='draft'));claim('person_relationship',key,'description',desc,src,q)
relationship('朱诚','朱温','父亲','朱诚为朱温之父。',N,family)
relationship('王氏（朱温母）','朱温','母亲','王氏为朱温之母，史书称文惠王皇后。',O,quote(O,'帝卽誠之第三子','母曰文惠王皇后。'))
for a in ['朱全昱','朱存']:relationship(a,'朱温','兄长',f'{a}为朱温兄长。',N,family)
relationship('黄巢','朱温','统属','朱温早年为黄巢部将；此关系限于归唐前，不表示终身效忠。',T,quote(T,'诸葛爽以','爽遂降于巢。'))
def event(slug,title,year,time,desc,place,src,q,participants,note=None):
 key='event_early_'+slug
 B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=time,dynasty='唐',description=desc,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='保留史载地名，未做坐标校准。',status='draft'))
 claim('event',key,'description',desc,src,q,note or '按所属年条定位；原历月日未换算为公历。')
 for name,role in participants:
  pk=f'pe_early_{slug}_{name}';B['person_events'].append(dict(key=pk,person_key=keys[name],event_key=key,role=role,status='draft'));claim('person_event',pk,'role',f'{name}：{role}。',src,q)
 return key
event('852_birth','朱温出生于砀山午沟里',852,'唐大中六年十月二十一日','《旧五代史》记朱温生于唐大中六年（852）十月二十一日，出生地为砀山县午沟里。','砀山县午沟里',O,birth,[('朱温','出生')])
event('877_join','朱温与兄朱存加入黄巢军',877,'唐乾符四年','《新五代史》记乾符四年（877），朱存、朱温加入黄巢军。该年是本批采用的入军纪年，不据该段认定黄巢也在877年才起兵。',None,N,join,[('朱温','加入黄巢军'),('朱存','加入黄巢军'),('黄巢','军队首领')],'入军年采用新五代史乾符四年；旧五代史仅记乾符中，不能作为877年的独立确认。曹、濮是段中黄巢起兵背景地，非确定入军地点。')
event('880_bridge','朱温屯东渭桥并招降诸葛爽',880,'唐广明元年十二月','黄巢命朱温屯东渭桥，并令其劝降诸葛爽，诸葛爽随后归降黄巢。','东渭桥',O,quote(O,'唐廣明元年十二月甲申','爽遂降于巢。'),[('朱温','驻军并招降'),('黄巢','下令')])
event('881_nanyang','朱温任先锋使进攻南阳',881,'唐中和元年二月','黄巢任朱温为东南面行营先锋使，令其攻取南阳；《旧五代史》记其攻下南阳。','南阳',O,quote(O,'中和元年二月','下之。'),[('朱温','领兵进攻'),('黄巢','任命并下令')])
event('882_tongzhou','朱温攻占同州',882,'唐中和二年二月','黄巢命朱温自行攻取同州。二月，同州刺史米诚奔河中，朱温占据同州。','同州',T,quote(T,'黄巢以硃温为同州刺史','温遂据之。'),[('朱温','攻占同州'),('黄巢','下令')],'通鉴称同州刺史，旧五代史称同州防御使；标题与叙述只取攻占事实，不消除官名异文。')
event('882_surrender','朱温举同州归唐',882,'唐中和二年九月丙戌','朱温求援受阻，见黄巢势衰；胡真、谢瞳劝其归唐。朱温杀监军严实，举同州归降王重荣，谢瞳随后奉表赴行在。','同州',U,surrender,[('朱温','举州归唐'),('王重荣','受降'),('胡真','劝归唐'),('谢瞳','劝归唐并奉表')],'采用通鉴九月丙戌；旧五代史辑注记旧唐书作八月庚子。温以舅事重荣是政治尊事，不据此建立血缘舅甥关系。')
grant=quote(U,'以硃温为右金吾大将军','赐名全忠。')
event('882_name','唐廷赐朱温名全忠',882,'唐中和二年冬十月条','唐廷授朱温河中行营招讨副使等官职，赐名全忠。朱温与朱全忠为同一人。',None,U,grant,[('朱温','受官赐名')],'通鉴置于冬十月条；新旧五代史承归降叙述。金吾官名通鉴作右，新旧五代史作左，正文不强行裁定。')
claim('person','person_zhu_wen','aliases','朱温获唐廷赐名全忠。',U,grant)
event('883_appointment','朱全忠获任宣武节度使',883,'唐中和三年三月己丑','唐廷任朱全忠为宣武节度使，令其待收复长安后赴镇。',None,U,quote(U,'己丑，以河中行营招讨副使','令赴镇。'),[('朱温','受任宣武节度使')])
event('883_bian','朱全忠入镇汴州',883,'唐中和三年秋七月丁卯','朱全忠率所部数百人赴镇，于七月丁卯到达汴州。当时汴、宋饥荒，公私困乏，军队难制且受外敌威胁。','汴州',U,quote(U,'宣武节度使硃全忠帅所部','而全忠勇气益振。'),[('朱温','入镇')])
for slug,src,q in [('877_join',N,join),('882_surrender',U,surrender),('883_bian',U,quote(U,'宣武节度使硃全忠帅所部','而全忠勇气益振。'))]:
 ev=next(e for e in B['events'] if e['key']=='event_early_'+slug)
 claim('person','person_zhu_wen','biography',ev['description'],src,q)
B['people'][0]['era']='晚唐至五代'
# Retain prior published biographical evidence and content for the reused elder brother.
previous=json.loads((ROOT/'content/year-0907/content-batch.json').read_text())
existing=next(p for p in previous['people'] if p['key']=='person_朱全昱')
B['people'][3]=dict(existing,status='draft')
for i,r in enumerate(B['person_relationships']):
 if r['person_a_key']=='person_朱全昱':
  old_key=r['key'];existing_rel=next(x for x in previous['person_relationships'] if x['person_a_key']=='person_朱全昱' and x['person_b_key']=='person_zhu_wen' and x['relation_type']=='兄长')
  B['person_relationships'][i]=dict(existing_rel,status='draft')
  for c in B['claims']:
   if c['subject_key']==old_key:c['subject_key']=existing_rel['key']
(OUT/'content-batch.json').write_text(json.dumps(B,ensure_ascii=False,indent=2)+'\n')
(OUT/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
