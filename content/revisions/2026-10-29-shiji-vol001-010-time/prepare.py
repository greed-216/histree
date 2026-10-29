# coding: utf-8
"""Prepare a bounded, source-scoped time revision. Read-only database access."""
import json,sys,uuid,hashlib,gzip,subprocess,os,urllib.request
from pathlib import Path
import pymysql
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'scripts'))
from mysql_content_store import MysqlContentStore
N=uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/greed-216/histree/content');sid=lambda k:str(uuid.uuid5(N,k));sha=lambda b:hashlib.sha256(b).hexdigest()
cur=json.loads((D/'curation.json').read_text());DEC={r['key']:r for r in cur['events']};INV=json.loads((R/'content/books/shiji/runs/2026-10-29-vol-001-010/time-review/inventory.json').read_text());OWN={e['key']:e for v in INV['volumes'] for e in v['new_event_details']}
PARAS={p['id']:p for p in map(json.loads,gzip.open(R/'resources/derived/history-library/shiji/paragraphs.jsonl.gz','rt'))}
s=MysqlContentStore(R/'.env.migration.local');protected={};source_meta={};curitems={};people={};own_persons=set();stock_ids=set()
for v in range(1,11):
 B=R/f'content/books/shiji/vol-{v:03}/from-start/part-01';b=json.loads((B/'content-batch.json').read_text());c=json.loads((B/'curation.json').read_text());reuse=set(json.loads((B/'reused-keys.json').read_text()))
 for file in ['content-batch.json','curation.json','packet.json','publication-mysql.json']:protected[str((B/file).relative_to(R))]=sha((B/file).read_bytes())
 for p in b['people']:people[p['name']]=p['key'];own_persons.update([p['key']] if p['key'] not in reuse else [])
 for it in c['items']:
  if it['group']=='events':curitems.setdefault(it['row']['key'],it)
 for m in json.loads((B/'sources/manifest.json').read_text()):source_meta.setdefault(m['paragraph_id'],dict(id=sid(m['key']),url=m['url'],key=m['key'],raw_path=str((B/'sources'/m['file']).relative_to(R)),sha256=m['sha256']))
 for e in b['events']:
  if e['key'] not in OWN:stock_ids.add(sid(e['key']))
ids=sorted({sid(k) for k in OWN}|stock_ids);events={r['id']:r for r in s.request('event','id=in.('+','.join(ids)+')&limit=1000')};assert len(events)==len(ids)
new_sources={};archive=[]
needed={pid for d in DEC.values() for pid in d['anchors']}|{p['anchor'] for d in DEC.values() for p in d['phases']}|{'shiji-174f8dfa444c-p001048','shiji-174f8dfa444c-p001430','shiji-174f8dfa444c-p001809'}
# Old source excerpts remain immutable. Only newly consulted anchors need new archives.
for pid in sorted(needed):
 if pid in source_meta:continue
 p=PARAS[pid];loc=p['locator'];source=R/loc['source_file'];text=source.read_bytes().decode('utf-8');raw=text[loc['char_start']:loc['char_end']].encode();assert sha(raw)==loc['raw_excerpt_sha256'];folder=D/'sources'/pid;folder.mkdir(parents=True,exist_ok=True);(folder/'source.txt').write_bytes(raw);(folder/'paragraph.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
 sk='shiji-time-review-'+pid;source_meta[pid]=dict(id=sid(sk),key=sk,raw_path=str((folder/'source.txt').relative_to(R)),sha256=sha(raw),new=True)
 archive += [dict(path=str((folder/name).relative_to(R)),sha256=sha((folder/name).read_bytes()),bytes=(folder/name).stat().st_size) for name in ['source.txt','paragraph.json']]
(D/'source-upload-manifest.json').write_text(json.dumps(dict(files=archive,bytes=sum(f['bytes'] for f in archive),branch='codex/shiji-time-review-sources-20261029'),ensure_ascii=False,indent=2)+'\n')
commit_file=D/'source-commit.json'
if not commit_file.exists():print('SOURCE ARCHIVE READY',len(archive),'files',sum(f['bytes'] for f in archive),'bytes');s.connection.close();raise SystemExit(0)
commit=json.loads(commit_file.read_text())['commit'];assert len(commit)==40
for pid,m in source_meta.items():
 if not m.get('new'):continue
 p=PARAS[pid];path=m['raw_path'];m['url']=f'https://github.com/greed-216/histree/blob/{commit}/{path}'
 blob=subprocess.check_output(['git','show',commit+':'+path],cwd=R);assert sha(blob)==m['sha256']
 new_sources[m['id']]=dict(id=m['id'],title=f'史记电子版·卷{p["volume_candidate"]}·纪年对照·{pid}',source_type='secondary',author=None,edition='选定EPUB全文TXT逐字片段；年表公元前年列为现代对照信息，不冒充司马迁原有公元纪年。',url=m['url'],note=f'原文与定位见{pid}；同书年表必要校年补证，不推进连续录入进度。')
key_map={sid(k):k for k in set(curitems)|set(people.values())};key_map.update({m['id']:m['key'] for m in source_meta.values()});new_claims=[];datings=[];updates=[];phase_events=[];pes=[];relations=[];reviews=[];primary_sources=set();used_sources=set()
def make_claim(subject,table,field,value,pid,note,tag):
 m=source_meta[pid];raw=(R/m['raw_path']).read_bytes();assert sha(raw)==m['sha256'];quote=PARAS[pid]['text'];assert quote in raw.decode('utf-8-sig');p=PARAS[pid];logical_key='claim_shiji_time_20261029_'+tag+'_'+pid+'_'+field;cid=sid(logical_key);key_map[cid]=logical_key
 row=dict(id=cid,subject_table=table,subject_id=subject,field_path=field,claim_text=value,source_id=m['id'],citation=f'《史记》选定电子本卷{p["volume_candidate"]}·{pid}；时间修订依据',note='原文：'+quote+'；核对说明：'+note,status='published');assert not any(c['id']==cid for c in new_claims);new_claims.append(row);used_sources.add(m['id']);return row

def fingerprint(c):
 vals=[c[k] for k in ['subject_table','subject_id','claim_text','source_id','citation','note']]+[next(m['url'] for m in source_meta.values() if m['id']==c['source_id'])]
 return sha('|'.join(str(v or '').encode().hex().upper() for v in vals).encode())
def dating(event,c,d,tag):
 datings.append(dict(id=sid('dating_shiji_time_'+tag),event_id=event,claim_id=c['id'],claim_sha256=fingerprint(c),earliest_year=d['earliest'],latest_year=d['latest'],precision_kind=d['precision'],era_key=d['era'],basis=d['reason'],review_state='reviewed'))
def change(table,row,after,key):
 after={k:v for k,v in after.items() if row.get(k)!=v}
 if after:updates.append(dict(table=table,id=row['id'],key=key,before={k:row[k] for k in after},after=after,full_before=row))

for k,d in DEC.items():
 old=events[sid(k)];assert old['status']=='published' and old['start_year'] is None and old['end_year'] is None
 pid=OWN[k]['paragraphs'][0];oldtime=old.get('time_original') or '';reason=d['reason'];summary=reason
 after={};date_text=None
 if d['legacy']:
  after.update(start_year=d['earliest'],end_year=d['latest']);date_text=('公元前'+str(-d['earliest'])+'年') if d['earliest']==d['latest'] else f'公元前{-d["earliest"]}至{-d["latest"]}年'
  after['time_original']=oldtime+'；'+date_text+'（按史书记年对照，原月日保留）'
 elif d['decision']=='era' and ('具体公元年未核定' in oldtime or '五帝叙事；具体年代未定' in oldtime):after['time_original']=d['era']+'（传世叙事，未定绝对年代）'
 elif d['decision'] in ['multiple','conflicting','relative','range']:after['time_original']=oldtime+'；'+('含多个时点，分阶段记年' if d['decision']=='multiple' or d['phases'] else '仅定范围或先后，具体年份保留待考')
 if k.endswith('_wen_rong'):after['time_original']='秦文公十六年（公元前750年）'
 if k.endswith('_shifu'):after['time_original']='秦庄公时期；世父出战让位未单载年，末句四十四年为庄公卒年'
 # Keep the original narrative; append explicit stage dates to avoid representing separate actions as one duration.
 if d['phases']:
  phases='；'.join(f'公元前{-p["year"]}年：{p["title"]}' for p in d['phases'])
  after['description']=old['description']+'\n\n分阶段纪年：'+phases+'。总述涵盖不同动作，不表示其间持续发生。'
  if d['decision']=='relative':after['description']+='返归的具体年份仍待考。'
 change('event',old,after,k)
 field='start_year' if d['legacy'] else 'time_original';cl=make_claim(old['id'],'event',field,('本事件记为'+date_text+'。' if date_text else '时间处理：')+reason,pid,reason,k)
 dating(old['id'],cl,d,k)
 for apid in list(dict.fromkeys(d['anchors'])):
  if apid==pid:continue
  ac=make_claim(old['id'],'event',field,'纪年锚点及对照：'+reason,apid,'这是在位纪年与公元对照的支持资料；不把表中其他事件或现代公元列当成本事件原始叙事。'+reason,k+'_anchor')
  relations.append(dict(id=sid('rel_time_anchor_'+cl['id']+ac['id']),claim_id=cl['id'],related_claim_id=ac['id'],claim_sha256=fingerprint(cl),related_sha256=fingerprint(ac),relation_kind='corroborates',review_state='reviewed',note='同次时间校核的事件句与纪年对照分别保留；不是两个独立史源。'))
 reviews.append(dict(event_key=k,event_id=old['id'],decision=d['decision'],legacy_year_written=d['legacy'],claim_id=cl['id'],anchors=d['anchors'],reason=reason))
 for i,ph in enumerate(d['phases']):
  # One reviewed match already exists in the Tongjian; reuse it instead of a duplicate.
  reused=(k.endswith('_qin_awards') and i==0)
  eid='a6ecb7d4-3233-5dc2-ba84-79d772acf692' if reused else sid('event_shiji_time_stage_'+k+'_'+str(i))
  if not reused:
   key_map[eid]='event_shiji_time_stage_'+k+'_'+str(i)
   event={z:old[z] for z in ['dynasty','location_name','location_modern_name','location_lat','location_lng','location_precision','location_note']}
   # The parent location can cover unrelated stages; do not inherit an unverified coordinate.
   event.update(id=eid,title=ph['title'],description=f'《史记》卷{PARAS[pid]["volume_candidate"]}本段记载：{ph["title"]}。原记年为{ph["king"]}{ph["regnal"]}年，核同书年表对照为公元前{-ph["year"]}年。',start_year=ph['year'],end_year=ph['year'],time_original=f'{ph["king"]}{ph["regnal"]}年（公元前{-ph["year"]}年）',status='published',location_name=None,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note=None)
   phase_events.append(event)
  note='本阶段按本段明示的在位年单独换算，原总述和旧批次保留；'+('已有同一周王贺秦事件，复用旧稳定ID，不改其字段。' if reused else '不把父总述的整个范围当成本阶段时长。')
  pc=make_claim(eid,'event','start_year',f'{ph["title"]}，本阶段对应公元前{-ph["year"]}年。',pid,note,k+'_phase'+str(i))
  pd=dict(earliest=ph['year'],latest=ph['year'],precision='year',era=d['era'],reason=note);dating(eid,pc,pd,k+'_phase'+str(i))
  make_claim(eid,'event','start_year',f'{ph["king"]}{ph["regnal"]}年的公元纪年对照为前{-ph["year"]}年。',ph['anchor'],'现代公元对照列及本纪在位年相互校对；不独立证明本阶段全部事实。',k+'_phaseanchor'+str(i))
  if not reused:
   # Only explicitly named principal actors in the phase title get a new participation.
   name='周'+ph['king'] if ph['king'] in ['宣王','桓王','襄王','敬王','显王'] else ph['king']
   if '后子鍼' in ph['title']:name='后子鍼'
   if name in people and (name in ph['title'] or ph['king'] in ph['title']):
    personid=sid(people[name]);peid=sid('pe_shiji_time_stage_'+eid+'_'+personid);pe=dict(id=peid,person_id=personid,event_id=eid,role='原文明示的相关人物',status='published');pes.append(pe);key_map[peid]='pe_shiji_time_stage_'+eid+'_'+personid;make_claim(peid,'person_event','role',name+'是本阶段原文明示的相关人物。',pid,'根据本纪明示主语及上下文建参与，不由纪年王名自动推定所有行动。',k+'_pe'+str(i))
# One previously undated shared event is explicitly dated by the new Shiji source.
k='event_zztj_v008_zhaogao_deer';eid=sid(k);old=events[eid];assert old['start_year'] is None;d=dict(earliest=-207,latest=-207,precision='year',era='秦',reason='秦始皇本纪明示二世三年八月己亥；核二世元年对照前209年，三年为前207年。原月日保留，不换算公历日。')
change('event',old,dict(start_year=-207,end_year=-207,time_original='秦二世三年八月己亥（公元前207年）；原干支保留'),k);c=make_claim(eid,'event','start_year','指鹿为马按本纪二世三年对照为公元前207年。','shiji-174f8dfa444c-p000593',d['reason'],k);dating(eid,c,d,k);make_claim(eid,'event','start_year','二世元年对照为前209年，三年为前207年。','shiji-174f8dfa444c-p001698',d['reason'],k+'_anchor')
# Keep the old Chenggao year and add the different Shiji dating as an explicit source-scoped account.
k='event_zztj_v010_han_takes_zhao_army';eid=sid(k);old=events[eid];assert old['start_year']==-204
d=dict(earliest=-203,latest=-203,precision='year',era='西汉',reason='《项羽本纪》明记汉之四年围成皋、汉王逃出；依高祖元年前206年对照为前203年。旧《通鉴》对象仍保留前204年，两书记年有异说，未覆盖旧值。')
c=make_claim(eid,'event','start_year','按《项羽本纪》汉四年的记载，此事对照为公元前203年；与既有前204年的记录并列。','shiji-174f8dfa444c-p000689',d['reason'],k);dating(eid,c,d,k)
# Bound the remaining inherited undated accounts without manufacturing exact years.
stock=[r for r in json.loads((R/'content/books/shiji/runs/2026-10-29-vol-001-010/time-review/stock-events.json').read_text()) if r['start_year'] is None and r['id']!=sid('event_zztj_v008_zhaogao_deer')]
for old in stock:
 k=old['key'];it=curitems[k];pid=it['evidence'][0]['paragraph_id'];era=old.get('dynasty') or ('西汉' if 'v015' in k or 'hui_distress' in k else '秦汉之际');note='本次逐段核对仍是追叙、言论或生平概述，没有可独立核定的单一年份；保留旧年份为空和当前来源的相对语境，不借邻近年条强填。'
 d=dict(earliest=None,latest=None,precision='era',era=era,reason=note)
 if 'v015' in k:d.update(earliest=-179,latest=-157,precision='range',reason='本纪将此事作为文帝政事或生平概述，没有独立确年；只约束在文帝时期。文帝元年对照前179年，后元七年去世对照前157年，不表示连续持续22年。')
 c=make_claim(old['id'],'event','time_original',d['reason'],pid,d['reason'],k);dating(old['id'],c,d,k)

# Explicitly recorded deaths only; no births inferred from ages or participation.
person_dates=[]
deaths=[('周厉王','event_shiji_v004_gonghe',-828),('周宣王','event_shiji_v004_succession_周幽王',-782),('周幽王','event_shiji_v004_you_death',-771),('周平王','event_shiji_v004_huan_succeeds',-720),('周桓王','event_shiji_v004_succession_周庄王',-697),('周庄王','event_shiji_v004_succession_周釐王',-682),('周釐王','event_shiji_v004_succession_周惠王',-677),('周惠王','event_shiji_v004_succession_周襄王',-652),('周顷王','event_shiji_v004_succession_周匡王',-613),('周匡王','event_shiji_v004_succession_周定王（瑜）',-607),('周定王（瑜）','event_shiji_v004_succession_周简王',-586),('周简王','event_shiji_v004_succession_周灵王',-572),('周灵王','event_shiji_v004_succession_周景王',-545),('周元王','event_shiji_v004_succession_周定王（介）',-469),('周定王（介）','event_shiji_v004_ai_si_kao',-441),('周考王','event_shiji_v004_succession_周威烈王',-426),('秦武公','event_shiji_v005_wugong_death',-678),('秦穆公','event_shiji_v005_mu_death',-621),('秦宁公','event_shiji_v005_chuuzi',-704),('秦德公','event_shiji_v005_degong',-676),('秦庄公','event_shiji_v005_shifu',-778),('秦仲','event_shiji_v005_qinzhong',-822),('秦康公','event_shiji_v005_linghu',-609)]
for name,ek,year in deaths:
 pk=people.get(name)
 if not pk or pk not in own_persons:continue
 person=s.request('person','id=eq.'+sid(pk))[0]
 if person['status']!='published':continue
 assert person['death_year'] is None
 pid=OWN[ek]['paragraphs'][0];assert any(w in PARAS[pid]['text'] for w in ['崩','卒','死','殺'])
 note='本纪明示此人死亡，核对所载在位年与本书年表，对照为公元前'+str(-year)+'年；不由继任者元年或年龄单独倒推。'
 change('person',person,dict(death_year=year),pk);cl=make_claim(person['id'],'person','death_year',name+'据本篇死亡记年对照为公元前'+str(-year)+'年。',pid,note,pk)
 for apid in DEC[ek]['anchors']:make_claim(person['id'],'person','death_year',name+'的死亡纪年对照依据。',apid,note,pk+'_anchor')
 person_dates.append(dict(person_key=pk,year=year,kind='death_year',claim_id=cl['id'],basis_event=ek))


for ek,hpid in [('event_shiji_v004_gonghe','shiji-174f8dfa444c-p001048'),('event_shiji_v004_ai_si_kao','shiji-174f8dfa444c-p001430'),('event_shiji_v009_zhangbiqiang_plan','shiji-174f8dfa444c-p001809')]:
 make_claim(sid(ek),'event','time_original','本次年表对照使用此表头标明的公元前年列及相应国别栏。',hpid,'这是现代电子版对照列的表头说明，仅说明所用资料的列性质，不独立证明事件或声称公元列为司马迁原文。',ek+'_header')

# Protect pre-existing dated subjects, source bytes, and all original published batch files.
plan=dict(kind='source_scoped_time_revision',format_version=1,target_fingerprint=s.target_fingerprint,protected_paths=protected,protected_events=[events[i] for i in sorted(stock_ids) if events[i]['start_year'] is not None],updates=updates,new_events=phase_events,new_person_events=pes,new_claims=new_claims,event_dating=datings,claim_relations=relations,person_dates=person_dates,sources=list(new_sources.values()),source_metadata=source_meta,key_map=key_map,used_source_ids=sorted(used_sources),reviews=reviews,stage_existing_matches=[dict(parent='event_shiji_v004_qin_awards',stage=0,canonical_id='a6ecb7d4-3233-5dc2-ba84-79d772acf692',reason='同年同王向秦献公致贺，旧库保存黼黻细节；补独立出处而不新建。')],scope='Only reviewed date fields and phase clarification of current-run new events, plus one explicitly dated old undated record; old dated records and all original batches remain unchanged.')
(D/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');s.connection.close();print('READONLY PLAN',len(updates),'updates',len(phase_events),'new phases',len(new_claims),'claims',len(datings),'date records',len(new_sources),'new anchor sources')
