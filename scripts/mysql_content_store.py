"""Explicit MySQL backend for existing reviewed publishing/revision scripts.
Read-only unless the caller received --apply. No arbitrary SQL or unbounded updates.
"""
import json,decimal,re,hashlib,urllib.parse,urllib.request
from datetime import datetime
from pathlib import Path
import mysql_connection as _preflight
TABLES=('person','event','topic','source','fact_claim','person_relationship','person_event','event_causality')

def visible(table,alias='r'):
 if table=='source':return 'TRUE'
 base=f"{alias}.status='published'"
 pairs={'person_relationship':(('person','person_a'),('person','person_b')),'person_event':(('person','person_id'),('event','event_id')),'event_causality':(('event','cause_event_id'),('event','effect_event_id'))}
 if table in pairs:return base+' AND '+' AND '.join(f"EXISTS(SELECT 1 FROM `{t}` v WHERE v.id={alias}.`{c}` AND v.status='published')" for t,c in pairs[table])
 if table=='fact_claim':return base+' AND ('+' OR '.join(f"({alias}.subject_table='{t}' AND EXISTS(SELECT 1 FROM `{t}` s WHERE s.id={alias}.subject_id AND {visible(t,'s')}))" for t in ('person','event',*pairs))+')'
 return base

class MysqlContentStore:
 def __init__(self,env_path,writable=False,public_url=None):
  self.env=_preflight.read_env(Path(env_path));self.writable=writable;self.public=False;self.public_url=public_url
  self.target_fingerprint=hashlib.sha256(json.dumps([self.env['MYSQL_HOST'],int(self.env.get('MYSQL_PORT','3306')),self.env['MYSQL_DATABASE']],separators=(',',':')).encode()).hexdigest()
  self.connection=_preflight.connect_mysql(self.env,True);self.columns={};self.json_columns={}
  with self.connection.cursor() as cursor:
   if writable:
    cursor.execute("SELECT GET_LOCK('histree-content-publish',0)");assert cursor.fetchone()[0]==1, 'Another content publisher is active'
   cursor.execute("SET time_zone='+00:00'")
   cursor.execute('SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema=DATABASE()')
   for table,column,kind in cursor.fetchall():
    self.columns.setdefault(table,set()).add(column)
    if kind=='json':self.json_columns.setdefault(table,set()).add(column)
 def column(self,table,column):
  if column not in self.columns.get(table,set()):raise ValueError('Invalid column')
  return '`'+column+'`'
 def value(self,table,column,value):
  if column in self.json_columns.get(table,set()) and value is not None:return json.dumps(value,ensure_ascii=False,separators=(',',':'))
  return value
 def normalize(self,table,row):
  for column,value in row.items():
   if column in self.json_columns.get(table,set()) and isinstance(value,str):row[column]=json.loads(value)
   elif isinstance(value,datetime):row[column]=value.isoformat(timespec='microseconds')+'+00:00'
   elif isinstance(value,decimal.Decimal):row[column]=float(value)
  return row
 def read(self,table,where,params,selection,order,limit,offset):
  import pymysql
  select='r.*' if selection=='*' or selection=='*,source:source_id(*)' else ','.join('r.'+self.column(table,c) for c in selection.split(','))
  with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
   cursor.execute(f'SELECT {select} FROM `{table}` r WHERE {where} ORDER BY {order} LIMIT %s OFFSET %s',(*params,limit,offset))
   rows=[self.normalize(table,row) for row in cursor.fetchall()]
  if 'source:' in selection:
   for row in rows:
    sources=self.read('source','r.id=%s',[row['source_id']],'*','r.id',1,0);row['source']=sources[0] if sources else None
  return rows
 def request(self,table,query='',method='GET',body=None):
  if table not in TABLES:raise ValueError('Invalid table')
  options=urllib.parse.parse_qs(query,keep_blank_values=True)
  if any(len(v)!=1 for v in options.values()):raise ValueError('Duplicate query key')
  filters=[];params=[]
  for column,values in options.items():
   if column in ('select','order','limit','offset'):continue
   value=values[0]
   if column=='or':
    match=re.fullmatch(r'\(person_a\.eq\.([0-9a-f-]{36}),person_b\.eq\.([0-9a-f-]{36})\)',value)
    if table!='person_relationship' or not match or match[1]!=match[2]:raise ValueError('Unsupported relation filter')
    filters.append('(r.person_a=%s OR r.person_b=%s)');params.extend([match[1],match[2]]);continue
   sql='r.'+self.column(table,column)
   if value.startswith('eq.'):
    expected=value[3:]
    if column in self.json_columns.get(table,set()):
     # The alias revision script emits a PostgreSQL array guard; exact JSON preserves ordering.
     if expected.startswith('{') and expected.endswith('}'):expected=[] if expected=='{}' else expected[1:-1].split(',')
     else:expected=json.loads(expected)
     filters.append(f'{sql}=CAST(%s AS JSON)');params.append(self.value(table,column,expected))
    else:filters.append(f'{sql}=%s');params.append(expected)
   elif value.startswith('in.(') and value.endswith(')'):
    ids=value[4:-1].split(',');assert 0<len(ids)<=1000 and all(re.fullmatch(r'[0-9a-f-]{36}',x) for x in ids)
    filters.append(sql+' IN ('+','.join('%s' for _ in ids)+')');params.extend(ids)
   elif value=='is.null':filters.append(sql+' IS NULL')
   elif column=='id' and value.startswith('gt.'):
    filters.append(sql+' > %s');params.append(value[3:])
   else:raise ValueError('Unsupported filter')
  where=' AND '.join(filters) or 'TRUE'
  if self.public:
   if method!='GET':raise ValueError('Public writes forbidden')
   if not self.public_url:raise ValueError('Public API URL required for anonymous readback')
   # Actual HTTP anonymous contract; credentials never reach this request.
   ids=options.get('id',[''])[0]
   if ids.startswith('eq.'):ids=ids[3:]
   elif ids.startswith('in.('):ids=ids[4:-1]
   else:raise ValueError('Public readback requires exact ids')
   query=urllib.parse.urlencode({'ids':ids,'limit':50})
   result=[]
   for page in range(21):
    request=urllib.request.Request(self.public_url.rstrip('/')+f'/catalog/{table}?'+query+f'&page={page}')
    with urllib.request.urlopen(request,timeout=30) as response:data=json.load(response)
    for row in data['items']:
     if table in ('person','event'):
      detail=urllib.request.Request(self.public_url.rstrip('/')+'/entry/'+row['id'])
      with urllib.request.urlopen(detail,timeout=30) as response:row=json.load(response)
     elif table=='topic':
      detail=urllib.request.Request(self.public_url.rstrip('/')+'/topics/'+urllib.parse.quote(row['slug']))
      with urllib.request.urlopen(detail,timeout=30) as response:row=json.load(response)
     result.append(row)
    if not data['has_more']:return result
   raise RuntimeError('Public readback exceeded bound')
  selection=options.get('select',['*'])[0];ordering=options.get('order',['id'])[0].split(',')
  order=','.join('r.'+self.column(table,o.removesuffix('.asc').removesuffix('.desc'))+(' DESC' if o.endswith('.desc') else ' ASC') for o in ordering)
  limit=int(options.get('limit',['1000'])[0]);offset=int(options.get('offset',['0'])[0]);assert 1<=limit<=1000 and 0<=offset<=100000
  if method=='GET':return self.read(table,where,params,selection,order,limit,offset)
  if not self.writable:raise ValueError('Writes require --apply')
  import pymysql
  try:
   with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
    if method=='POST':
     assert isinstance(body,list) and body and len(body)<=1000
     for row in body:
      assert 'id' in row
      columns=list(row);names=','.join(self.column(table,c) for c in columns)
      cursor.execute(f'INSERT INTO `{table}` ({names}) VALUES('+','.join('%s' for _ in columns)+')',[self.value(table,c,row[c]) for c in columns])
     result=[]
     for row in body:result.extend(self.read(table,'r.id=%s',[row['id']],'*','r.id',1,0))
    elif method=='PATCH':
     assert 'id' in options and filters and isinstance(body,dict) and body and 'id' not in body
     columns=list(body);assign=','.join(self.column(table,c)+'=%s' for c in columns)
     before=self.read(table,where,params,'*','r.id',1000,0)
     cursor.execute(f'UPDATE `{table}` r SET {assign} WHERE {where}',(*[self.value(table,c,body[c]) for c in columns],*params))
     result=[]
     for row in before:result.extend(self.read(table,'r.id=%s',[row['id']],'*','r.id',1,0))
    else:raise ValueError('Unsupported mutation')
   self.connection.commit();return result
  except Exception:self.connection.rollback();raise
