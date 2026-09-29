"""Reviewed copy edits. Preserve quotations, IDs, URLs and historical uncertainty."""
import re,json,sys
from pathlib import Path
GENERIC_NOTES={
'按指定电子文本逐段整理；907年条中的前事与泛论不据此强行断年；2026-09-29由项目助手核读；单源内容按书中记载发布，不视为独立证实。',
'已对照所保存电子文本；尚待人工复核，不视为纸本校勘结论。',
'按PDF文字层提取核对；版式断行保留，未作纸本校勘。',
'本项目核读电子文本；文字层不是原刻影印，未作纸本校勘。'}
REPLACE={
'本批仅整理相关史事，生卒与完整履历待补。':'',
'本批“蜀王”对应前蜀王建；':'“蜀王”指前蜀王建；',
'本批“岐王”对应李茂贞；':'“岐王”指李茂贞；',
'本批采用907年的名字高季昌；':'907年时名高季昌；',
'高季兴作为检索异名。':'后名高季兴。',
'本批依据907年改名与封王记载。':'见907年改名与封王记载。',
'关系范围限于本批任职记载。':'此处为907年的任职关系。',
'本批只记录907年前后的依附关系。':'此处为907年前后的依附关系。',
'本批记录908年作战指挥及923年后唐君臣关系':'记载涉及908年作战指挥及923年后唐君臣关系',
'用户TXT中“王镕宁太师”有疑字，王镕具体官衔暂不订正。':'所据文本“王镕宁太师”有疑字，具体官衔待考。',
'兵力与伤亡数字暂不结构化。':'',
'；盗贼减少比例不结构化。':'。',
'本项目用“前蜀”区分后来的后蜀。':'史称前蜀。',
'人名按本次所用《通鉴》文本保留，异名待查。':'人名沿用《通鉴》记载，异名待考。',
'江陵恢复的过程不压缩为任命当天完成。':'江陵的恢复并非一日完成。',
'本段后续契丹沿革和会盟叙事另列待核，未并入此次使行。':'契丹沿革及此前会盟不属于此次使行。',
'段首所述诛杀三将等前事另列待核，不全部断为当日。':'诛杀三将等前事的具体日期未详。',
'已记录原文地名；古今对应及WGS84坐标尚未完成核验，不落点。':'历史地名与今地的对应尚待考证。',
'原文历史地名；未核定古城址、今地与坐标。':'历史地名与今地的对应尚待考证。',
'原文未直接确定单一地点，待核。':'具体地点未详。',
'本事件是追尊行为，不据此新增先人的在世活动。':'追尊发生于先人去世之后。',
'本事件只记录书信提议，不据此建立已成形的军事同盟。':'此为书信提议，不能据此认定双方已结成军事同盟。',
'这里记录诏令，不断言各地全部执行。':'诏令在各地的实际执行情况未详。',
'不推算人数，也不扩写后续生活。':'人数及此后去向未详。',
'本批依据':'依据', '本批只记录':'此处记载',
}
def prose(s):
 for a,b in REPLACE.items():s=s.replace(a,b)
 s=re.sub(r'《资治通鉴》907年条所记人物。在“(.+?)”中为(.+?)。',r'据《资治通鉴》，907年在“\1”中为\2。',s)
 s=re.sub(r'卷266·开平元年条·tj266-907-p(\d+)',lambda m:'卷266·开平元年·'+('年次题记' if int(m[1])==0 else f'第{int(m[1])}段'),s)
 return s

def clean(table,row):
 r=dict(row)
 if table=='source':
  r['title']=re.sub(r'（(?:用户提供TXT|GitHub电子排印本|Kanripo电子本)）','',r['title']).replace('/卷','·卷')
  if '用户提供' in row.get('edition',''):
   r['edition']='电子文本，底本未详';r['note']='按卷次、年次与段落定位。部分文字可能存在转录讹误，疑字随引文注明。'
  elif 'grimoire-kindle' in row.get('edition',''):
   r['edition']='电子排印本，底本待考';r['note']='页码为电子文件页码，非古籍原叶码。'
   if '旧五代史' in r['title']:r['note']+='此书辑本含他书引文，须区分本书叙述与引文。'
  elif '维基文库' in row.get('edition',''):
   r['edition']='维基文库电子本，未与纸本校勘'
   r['note']='保留异体字、疑字与编年标题。' if '资治通鉴' in r['title'] else '电子本含辑佚说明、校注与引书；转引《通鉴》的文字不作为独立证据。'
  elif row.get('edition','').startswith(('SBCK','WYG')):
   r['edition']='电子文本；所标版本尚未逐叶核验';r['note']='保留原文页标与异体字，无法识读的字暂存原标记。'
  return r
 for k,v in r.items():
  if k=='note' and table=='fact_claim' and isinstance(v,str) and '；核对说明：' in v:
   quote,review=v.split('；核对说明：',1)
   r[k]=quote+'；核对说明：'+('' if review in GENERIC_NOTES else prose(review))
  elif k in ['description','biography','claim_text','citation','time_original','location_note'] and isinstance(v,str):r[k]=prose(v)
 return r

if __name__=='__main__':
 mode,path=sys.argv[1:3];p=Path(path);data=json.loads(p.read_text())
 if mode=='--batch':
  groups={'people':'person','events':'event','person_relationships':'person_relationship','claims':'fact_claim','sources':'source'}
  for g,t in groups.items():data[g]=[clean(t,x) for x in data[g]]
  p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 elif mode=='--snapshot':
  out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True);snapshot=data['rows'][0]['snapshot'];changes=[];sql=['BEGIN;','SET LOCAL standard_conforming_strings = on;']
  def lit(x):return "'"+json.dumps(x,ensure_ascii=False).replace("'","''")+"'::jsonb"
  for t,rows in snapshot.items():
   for r in rows:
    z=clean(t,r);fields=[k for k in r if r[k]!=z[k]]
    if not fields:continue
    a={k:r[k] for k in fields};b={k:z[k] for k in fields};id=r['id'];changes.append(dict(table=t,id=id,before=a,after=b))
    sql.append(f"DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM public.{t} t WHERE id='{id}' AND (to_jsonb(t) @> {lit(a)} OR to_jsonb(t) @> {lit(b)})) THEN RAISE EXCEPTION 'Copy edit conflict: {id}'; END IF; END $$;")
    sql.append(f'UPDATE public.{t} SET '+','.join(f'{k}=v.{k}' for k in fields)+f" FROM jsonb_populate_record(NULL::public.{t}, {lit(b)}) v WHERE {t}.id='{id}';")
  sql.append('COMMIT;');(out/'apply.sql').write_text('\n'.join(sql)+'\n');(out/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
  from collections import Counter
  print(dict(Counter(x['table'] for x in changes)))
