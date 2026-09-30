"""Curate consecutive Tongjian volume 259, year 892 paragraphs 31–38."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 47))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0892-p031-p038', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-259-892'
B['sources'] = [dict(key=source,title='资治通鉴·卷259',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/tongjian/259.txt',note='卷259景福元年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/259.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/259.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias.update({'郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_259_0892_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福元年（892）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷259景福元年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=892,note=None,quote=None):
    key='event_zztj_259_0892_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_259_0892_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('li_maozhen_takes_feng','李茂贞克凤州，满存奔兴元',31,'892年七月己巳','凤州、兴元',
      '李茂贞攻克凤州，感义节度使满存逃奔兴元。',[('李茂贞','攻克者'),('满存','败走者')])
event('li_maozhen_takes_xing_yang','李茂贞又取兴洋，表子弟镇之',31,'892年七月己巳后条；逐次日未载','兴州、洋州',
      '李茂贞又取得兴州、洋州，上表请求由其子弟镇守。',[('李茂贞','取州与上表者')],note='子弟未具名，不补镇守人姓名与亲生关系；兴州与兴元不混同。')
event('yang_tian_an_offices','杨行密授淮南节度，田頵安仁义授职',32,'892年八月；具体日未载','淮南、宣州、润州',
      '朝廷任杨行密为淮南节度使、同平章事，以田頵知宣州留后，安仁义为润州刺史。',[('杨行密','受任淮南节度使者'),('田頵','知宣州留后者'),('安仁义','受任润州刺史者')],note='任命与七月表请分开；未载实际到任日。')
event('yang_black_cloud_corps','杨行密选孙儒降兵五千组成黑云都',33,'孙儒败降后；八月条所附；确切编组日未载','淮南',
      '孙儒降兵多为蔡人，杨行密从中选尤为勇健的五千人，厚给禀赐，以黑衣蒙甲，号黑云都。',[('杨行密','选编厚赐者'),('孙儒','降兵原所属主将')],note='本年败降后的编组，五千为书载编选数，不是所有孙儒降兵人数。')
event('black_cloud_later_battles','黑云都后来先登陷阵的总述',33,'编组之后；每战；各次确年日未载','',
      '《通鉴》总述杨行密后来每逢作战使黑云都先登陷阵，四邻畏惧。',[('杨行密','指挥者')],year=None,note='每战为后续概述，不造892单场战事或未载作战地点。')
event('gao_xu_trade_agriculture_advice','高勖劝杨行密以邻道贸易、劝农桑足用',34,'用度不足时；八月条所附；具体日未载','淮南、邻道',
      '杨行密因用度不足，想用茶盐换取居民布帛。掌书记高勖认为兵火后再向民取利恐致离叛，劝以本地所有换邻道所无供军，并任贤守令劝农桑；杨行密听从。田頵称赞贤者之言利远。',[('杨行密','拟议并接受建议者'),('高勖','掌书记献议者'),('田頵','闻议称赞者')],note='十室九空为高勖说辞，数年仓实是其预期，不作当时统计或已发生效果；原段后续恢复另录。')
claim('person',people['高勖'],'biography','高勖，舒城人，此段任杨行密掌书记。',34,quote='掌书记舒城高勖曰',note='舒城为明示籍贯，不据此造献议发生地。')
claim('person',people['杨行密'],'biography','《通鉴》评杨行密不长驰射武技，却宽简有智略，善于抚御将士、同甘苦，待人推心而无猜忌。',34,quote='行密驰射武伎，皆非所长，而宽简有智略，善抚御将士，与同甘苦，推心待物，无所猜忌。',note='人物品评归于史书，不作为独立测评结论或某年单次行为。')
event('yang_tolerates_stolen_tack','杨行密容忍从者盗马鞦金饰的轶事',34,'尝早出；它日；确年日未载','',
      '《通鉴》记杨行密一次早出，从者割断马鞦取金，杨行密知而不问，另日仍照常早出；书中说人们佩服其度量。',[('杨行密','知盗而不问者')],year=None,note='尝与它日轶事没有明确日期，从者未具名不推为某将；人服为史书评价。')
event('huainan_six_years_war','淮南受兵六年、杨行密初至给赐微薄',34,'受兵六年；杨行密初至；确切起止未载','淮南',
      '《通鉴》述淮南受兵六年，士民转徙几尽；杨行密初至，给将吏布帛不过数尺、钱不过数百，以勤俭足用，非公宴未举乐。',[('杨行密','初至给赐及勤俭者')],year=None,note='六年不反算起始，初至不贸然绑定本次七月归扬州；几尽为书述概括。')
event('yang_huainan_recovery','杨行密招流散、轻徭薄敛后淮南复富',34,'未及数年；具体起止未载','淮南',
      '杨行密招抚流散居民，轻徭薄敛；《通鉴》说不到数年公私富庶，接近承平旧况。',[('杨行密','招抚与轻徭薄敛者')],year=None,note='后续数年效果，不提前定为892年完成；富庶程度为史书评价。')
event('li_keyong_shendui_ambush','李克用北巡应云州之寇，神堆擒逻骑',35,'892年八月条；丙申之前','天宁军、新城、神堆、云州、晋阳',
      '李克用北巡至天宁军，闻李匡威与赫连铎率八万兵攻云州，派李君庆在晋阳发兵；李克用潜入新城，伏兵神堆，擒吐谷浑逻骑三百，李匡威等惊惧。',[('李克用','调兵伏击者'),('李匡威','来攻主将'),('赫连铎','来攻主将'),('李君庆','奉派发兵者')],note='八万与三百均书载；被擒逻骑非全军死亡。地名仅依底本，不补现代坐标。')
event('li_keyong_yunzhou_victory','李君庆援至，李克用云州大破来军',35,'892年八月丙申援至；丁酉出击','云州',
      '丙申李君庆率大军抵达，李克用进入云州；丁酉李克用出击李匡威等，大破之。',[('李君庆','率援军抵达者'),('李克用','进云州出击者'),('李匡威','被击来军主将'),('赫连铎','同段来军主将')])
event('yunzhou_army_retreat_pursuit','云州来军烧营退走，河东军追至天成',35,'892年八月己亥','云州、天成军',
      '己亥，底本所称天威等烧营而退，河东军追至天成军；《通鉴》称斩获不可胜计。',[('李克用','追军所属主将')],note='天威疑李匡威转录讹字，原文保留，不另建天威人物或悄改名；斩获包含杀与俘，不作纯死亡人数。')
event('li_maozhen_takes_xingyuan','李茂贞拔兴元，诸杨与满存奔阆州',36,'892年八月辛丑','兴元、阆州',
      '李茂贞攻下兴元，杨复恭、杨守亮、杨守信、杨守贞、杨守忠、满存逃奔阆州。',[('李茂贞','攻拔者'),('杨复恭','奔阆者'),('杨守亮','奔阆者'),('杨守信','奔阆者'),('杨守贞','奔阆者'),('杨守忠','奔阆者'),('满存','奔阆者')],note='不与七月取得兴州混为同地；此段明示守忠，891武定守忠守思异说继续保留既有备注。')
event('li_jimi_xingyuan_petition','李茂贞表李继密权知兴元府事',36,'892年八月辛丑条','兴元',
      '李茂贞上表以李继密权知兴元府事，《通鉴》称继密为其子。',[('李茂贞','上表者'),('李继密','被表权知者')],note='权知为暂摄，不补到任日；其子不补亲生或生母，关系身份须另书核实后再增。')
event('cheng_rui_chancellor_honor','成汭加同平章事',37,'892年九月','荆南',
      '荆南节度使成汭加同平章事。',[('成汭','受加官者')],note='节度使加同平章事不等于入京实际宰相任职。')
event('shi_pu_restored_zhu_objects','时溥复授感化，朱全忠请追回新命',38,'892年冬十月','感化、徐州',
      '时溥迫使监军奏称将士要留他，朝廷复以时溥为侍中、感化节度使。朱全忠奏请追回新命，朝廷诏谕劝解。',[('时溥','迫奏及复授者'),('朱温','以朱全忠名义请追新命者')],note='奏称留己不能当全体将士真实意愿；追命是朱的请求，未记朝廷已经撤销时溥任命。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={31:'凤州满存走与兴洋表子弟分录；未具名不造人。',32:'八月授职与七月表分开。',33:'编五千黑云都与后来每战先登概述分开。',34:'献议、盗金轶事、六年兵灾初至勤俭及数年恢复分录；舒城籍贯有据，预期与效果区别。',35:'神堆伏擒、丙申援至丁酉出击、己亥烧营追至分开；天威疑字保留不造人，斩获非纯阵亡。',36:'兴元非兴州；诸杨满存奔阆与继密权知表分开，子不推亲生。',37:'外镇加同平章事，不推实际入相。',38:'迫奏为奏称，追命为请求，未记撤命。'}
for n in range(31,39):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(31,39):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=892,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(31,39)],next_paragraph='zztj-v259-y0892-p039',coverage='卷259景福元年第31—38段连续录入；本年46段尚未完。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})

def relation(a,b,t,n,description,quote=None):
    ka,kb=people[a],people[b]
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['person_a_key']==ka and r['person_b_key']==kb and r['relation_type']==t]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);key=row['key'];reused.add(key)
    else:
        key=f'relationship_{ka}_{kb}_{t}';row=dict(key=key,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key
