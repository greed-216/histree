"""Curate consecutive Tongjian volume 259, year 892 paragraphs 39–46."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 47))
B = {'format_version': 1, 'batch_key': 'zztj-v259-y0892-p039-p046', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
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
    B['claims'].append(dict(key=f'claim_zztj_259_0892_06_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷259·景福元年（892）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

event('li_cunxiao_cunxin_rivalry','李存孝欲取镇冀立功，李存信从中阻挠',39,'初；具体年月未载','邢州、镇州、冀州',
      '《通鉴》追述李存孝与李存信俱为李克用假子，不相睦。李存信受李克用宠信；李存孝在邢州想立功超过李存信，建议取镇冀，李存信从中阻挠，使建议未及时获准。',[('李存孝','建议取镇冀者'),('李存信','受宠及阻挠者'),('李克用','二人所从者')],year=None,note='初追叙，年空；宠信、意图及不睦归于史书叙述，不据同时任将推盟友。')
for name in ['李存孝','李存信']:
    claim('person',people[name],'biography',f'《通鉴》本段称{name}为李克用假子。',39,quote='李存孝，与李存信俱为李克用假子',note='史载假子身份，保留与既有养父关系录法的出处层差异，不推生父或另造反向关系。')
event('yaoshan_relief_delay_background','李存孝救尧山不克，二将猜忌迟兵',39,'及王镕围尧山；具体日未载','尧山',
      '王镕围尧山时，李存孝救援未成功。李克用以李存信为蕃、马步都指挥使，与李存孝共同出击；二人互相猜忌，迟滞不进。',[('王镕','围攻者'),('李存孝','救援未克及迟兵者'),('李存信','受任共击及迟兵者'),('李克用','授职遣将者')],year=None,note='段内追叙不补具体日；随后李嗣勋击破与本年首第3段合并引用，不重复造同次胜利。')
prior=json.loads((YEAR/'part-01/content-batch.json').read_text())
won=next(e for e in prior['events'] if '李嗣勋' in e['title'])
B['events'].append(dict(won,status='draft'));reused.add(won['key']);used[39].append(won['key'])
claim('event',won['key'],'description','本段追述李存孝李存信迟兵后，李克用另遣李嗣勋等击破来军，与本年第3段尧山胜利对应。',39,quote='克用更遣李嗣勋等击破之。',note='同卷同年同地及同主将援军击破，对应第3段稳定事件，不新增重复胜利或重写原事件字段。')
event('li_cunxin_accuses_cunxiao','李存信指控李存孝无心击敌、有私约',39,'尧山战后；具体日未载','',
      '李存信返回后向李克用谮言李存孝无心击敌，并怀疑他与敌方有私约。李存孝闻后认为自己有功而信任不及李存信，愤怨且怕遭祸。',[('李存信','谮言指控者'),('李存孝','受指控且愤惧者'),('李克用','指控所向主将')],year=None,note='指控与怀疑不写成已证实私约；情绪判断依书述，未补所在城市。')
event('li_cunxiao_petitions_separate_command','李存孝结王镕朱全忠、上表求脱离河东',39,'892年冬十月条所附；具体日未载','邢州、洺州、磁州',
      '李存孝秘密联结王镕及朱全忠，上表请求邢洺磁三州直接归朝廷，请赐旌节并会诸道兵讨李克用。朝廷授其邢洺磁节度使，但不许会兵。',[('李存孝','联结上表及受任者'),('王镕','联结对象'),('朱温','以朱全忠名义联结对象'),('李克用','所请讨伐对象')],note='条首初追叙分开，此结尾回到编年条中的上表授职；所请会兵未获准，不记会兵已发生，不建终身同盟。')
event('zhang_sui_jian_join_zhu','张璲张谏以濠泗二州附朱全忠',40,'892年十一月','濠州、泗州',
      '时溥所属濠州刺史张璲、泗州刺史张谏，各以其州归附朱全忠。',[('时溥','原所属主将'),('张璲','以濠州归附者'),('张谏','以泗州归附者'),('朱温','以朱全忠名义受附者')],note='张谏复用既有人物，不推全部居民自愿归附。')
event('zhu_youyu_takes_pu','朱友裕率十万取濮州、执邵伦',41,'892年十一月乙未','濮州',
      '朱全忠派其子朱友裕率十万兵攻濮州，攻下城并捕获刺史邵伦。',[('朱温','以朱全忠名义遣兵者'),('朱友裕','率军攻拔者'),('邵伦','被执刺史')],note='十万为书载，不换算实际战力；执不写杀。父子关系此前已录，复用身份不重复新建。')
event('zhu_youyu_moves_against_shi','朱全忠令朱友裕移兵击时溥',41,'濮州被拔后；具体日未载','',
      '朱全忠随即命朱友裕移兵攻时溥。',[('朱温','以朱全忠名义下令者'),('朱友裕','奉命移兵者'),('时溥','进攻对象')],note='命令不补未载具体交战结果。')
event('wang_tan_takes_wu','孙儒将王坛陷婺州，蒋环出奔',42,'892年十一月条所附；具体日未载','婺州、赵州（底本，待考）',
      '底本称孙儒将王坛攻陷婺州，刺史蒋环逃奔赵州。',[('王坛（孙儒将）','底本王坛，攻陷者'),('蒋环','败走刺史'),('孙儒','该将原所属主将')],note='王坛暂按孙儒将身份立key，不因音形近合并王檀；赵州可能转录讹字，目的地待考，不配现代坐标。孙儒本人已死，不记其此次亲自出征。')
next(p for p in B['people'] if p['key']==people['王坛（孙儒将）'])['aliases']=['王坛']
event('cai_chou_desecrates_graves_seeks_help','蔡俦发杨氏祖父墓、联倪章求朱援',43,'892年十一月条所附；具体日未载','庐州、舒州',
      '庐州刺史蔡俦挖杨行密祖父墓，与舒州刺史倪章连兵，派使者向朱全忠送印求援。',[('蔡俦','发墓连兵求援者'),('杨行密','受侵害墓主的后人'),('倪章','连兵者'),('朱温','以朱全忠名义求援所向者')],note='祖父无姓名不造人物；连兵为此段行为，不自动推永久同盟。')
event('zhu_accepts_seal_no_rescue','朱全忠收蔡俦印不救、告杨行密',43,'蔡俦求援后；具体日未载','',
      '朱全忠嫌恶蔡俦反复，接受其印却不援救，并通牒告知杨行密，杨行密向朱全忠致谢。',[('朱温','以朱全忠名义受印拒援告知者'),('蔡俦','求援未获者'),('杨行密','收报致谢者')],note='嫌恶理由依史书；受印不等于派兵，不据谢建立终身同盟。')
event('li_shenfu_sent_against_cai','杨行密遣李神福讨蔡俦',43,'获朱全忠通报后；具体日未载','庐州',
      '杨行密派行营都指挥使李神福率兵讨蔡俦。',[('杨行密','遣军者'),('李神福','率兵者'),('蔡俦','被讨对象')],note='仅记录遣讨，不提前记攻克或蔡俦死亡。')
event('bian_gang_new_calendar','边冈献新历，定名景福崇玄历',44,'892年十二月','',
      '《宣明历》渐有偏差，太子少詹事边冈编成新历，十二月上献，命名《景福崇玄历》。',[('边冈','新历编成上献者')],note='不反算编历开工日或历法实施范围；偏差依书述不推具体误差数。')
event('hua_hong_defeats_yang_lang','华洪阆州击败杨守亮',45,'892年十二月壬午','阆州',
      '王建派华洪在阆州攻杨守亮，击败之。',[('王建','遣军者'),('王宗涤','以华洪旧名出击者'),('杨守亮','败方')],note='破不等于杀或擒，华洪复用王宗涤稳定key。')
event('zheng_xu_mission_to_zhu','郑顼使朱全忠，论剑阁之险',45,'892年十二月条；具体日未载','剑阁（谈论对象）',
      '王建派节度押牙郑顼出使朱全忠。朱全忠问剑阁，郑顼力言险峻；朱不信，郑称若不告知怕误其军机，朱大笑。',[('王建','遣使者'),('郑顼','出使陈说者'),('朱温','以朱全忠名义问话者')],note='延陵为郑顼籍贯，另记人物字段；剑阁为谈论对象，不推会见在剑阁或军队已经入蜀。')
claim('person',people['郑顼'],'biography','郑顼，延陵人，本段为王建节度押牙。',45,quote='建遣节度押牙延陵郑顼使于硃全忠',note='延陵按该书地望称谓记录，不补现代籍贯位置。')
event('zhong_wenji_dies_huang_claims','钟文季卒，黄晟自称明州刺史',46,'是岁；892年，具体月日未载','明州',
      '明州刺史钟文季去世，其将黄晟自称刺史。',[('钟文季','去世刺史'),('黄晟','自称刺史将领')],note='自称不写朝廷正式任命；黄晟与彭州杨晟是不同人物。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={39:'初追叙分录；谮与疑非证实，李嗣勋击破复用第3段事件；假子引用记人物，未多建养父重复关系。',40:'濠泗刺史以州归附，不泛化民意。',41:'濮州取执与移兵命令分开，十万书载，执不写杀。',42:'王坛孙儒将暂辨key；赵州疑讹待考，不配坐标，孙儒已死不记亲征。',43:'发墓连兵求援、收印拒援告知、遣神福讨三步分开；祖父未名不造人。',44:'历成十二月上献，不推开工与具体偏差。',45:'华洪旧名复用王宗涤，阆战与郑顼出使分开，剑阁为谈话对象；郑延陵籍贯。',46:'钟卒黄晟自称，不推正式授职，与杨晟分清。'}
for n in range(39,47):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(39,47):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=259,year=892,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(39,47)],next_paragraph='zztj-v259-y0893-p001',coverage='卷259景福元年第39—46段连续录入；本年段尾，整年完成须核对六批发布审计。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
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
