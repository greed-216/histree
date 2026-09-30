"""Curate consecutive Tongjian volume 258, year 891 paragraphs 35–40."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 41))
B = {'format_version': 1, 'batch_key': 'zztj-v258-y0891-p035-p040', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-258-891'
B['sources'] = [dict(key=source,title='资治通鉴·卷258',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/4d35696319726b523bd624f2370cb2cf7faa6b43/resources/derived/tongjian/258.txt',note='卷258大顺二年条；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/258.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/258.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
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
alias['郑渥']='王宗渥'
alias['李简']='李简（王建将）'
alias['华洪']='王宗涤'

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_258_0891_05_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷258·大顺二年（891）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['华洪'] if name=='王宗涤' else ['郑渥'] if name=='王宗渥' else ['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else ['杨儒'] if name=='王宗儒' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷258大顺二年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=891,note=None,quote=None):
    key='event_zztj_258_0891_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_258_0891_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

supplements=[]
def relation(a,b,t,n,description,quote=None):
    key=f'relationship_{people[a]}_{people[b]}_{t}'
    rows=[r for f in (ROOT/'content').rglob('content-batch.json') if f.resolve()!=(P/'content-batch.json').resolve() for r in json.loads(f.read_text())['person_relationships'] if r['key']==key]
    if rows:
        assert all(r==rows[0] for r in rows);row=dict(rows[0]);reused.add(key)
    else:row=dict(key=key,person_a_key=people[a],person_b_key=people[b],relation_type=t,description=description,status='draft')
    B['person_relationships'].append(row);claim('person_relationship',key,'description',description,n,quote=quote)
    return key

event('jinxiang_zhu_jin_defeat','丁会张归霸金乡大破朱瑾',35,'891年十二月乙酉','金乡',
      '汴将丁会、张归霸与朱瑾在金乡交战，大败朱瑾，书载杀获殆尽，朱瑾单骑逃脱。',
      [('丁会','汴军获胜将领'),('张归霸','汴军获胜将领'),('朱瑾','败逃将领')],note='殆尽为书中战果措辞，未载精确数；与十一月朱瑾攻单州分开，不写朱瑾阵亡。')
event('shunjie_guards_background','李顺节带兵出入，刘景宣西门君遂奏疑',36,'十二月戊子被杀前；确年日未载','京师',
      '《通鉴》述天威都将李顺节恃宠骄横、出入带兵。两军中尉刘景宣、西门君遂厌恶，上报皇帝担心其作乱。',
      [('杨守立','以李顺节名义被奏疑者'),('刘景宣','奏疑者'),('西门君遂','奏疑者'),('李杰','以唐昭宗身份受奏者')],year=None,note='概括背景年份留空；恐作乱是担心，不等于谋反已证实。')
event('shunjie_killed','李顺节银台门被召，似先知斩首',36,'891年十二月戊子','银台门、仗舍',
      '刘景宣、西门君遂以诏召李顺节。李顺节入银台门后被邀至仗舍坐谈，供奉官似先知从后斩首，其随从喧噪而出。',
      [('刘景宣','召入与邀谈者'),('西门君遂','召入与邀谈者'),('似先知','斩首者'),('杨守立','以李顺节名义被杀者')],note='似先知按底本完整姓名，不当作知道一词；李顺节杨守立同人，不新建重复人物。')
event('three_units_loot_yongning','三都军士劫掠永宁坊至暮才定',36,'891年十二月戊子；李顺节被杀后','永宁坊',
      '李顺节被杀后，天威、捧日、登封三都大掠永宁坊，直到傍晚才平定，百官上表称贺。',note='底本捧日照存，胡注电子本作奉日，部队名称待校；三都与百官不是具名人物，不造个人参与边。')
event('sun_ru_suchang_qian_suzhou','孙儒焚苏常逼宣，钱镠复据苏州',37,'891年十二月条；具体日未载','苏州、常州、宣州',
      '孙儒焚掠苏州常州，率军逼宣州；钱镠再次遣兵占据苏州。',[('孙儒','焚掠进逼者'),('钱镠','遣军复据者')],note='焚掠不推城市完全无人；据苏州不画全吴越疆界。')
event('qian_aids_yang','杨行密受孙儒屡破，钱镠以兵食援助',37,'891年十二月条；具体日未载','宣州、两浙',
      '孙儒屡败杨行密军，书载旌旗辎重绵延百余里。杨行密向钱镠求救，钱镠以兵与粮食援助。',[('孙儒','屡破对手者'),('杨行密','求援者'),('钱镠','兵食援助者')],note='百余里为队伍规模书载，不作地图路线测量；援助限定本次，非终身同盟。')
event('gu_yanhui_formal','顾彦晖获东川节度使，宋道弼奉节',38,'891年十二月条；具体日未载','东川',
      '朝廷任顾彦晖为东川节度使，遣中使宋道弼赐旌节。',[('顾彦晖','正式受任者'),('宋道弼','奉旌节使者')],note='与九月军推知留后分事。')
event('song_daobi_captured','杨守厚囚宋道弼夺节攻梓州',38,'891年十二月条；赐节途中','梓州、绵州',
      '杨守亮令杨守厚囚宋道弼、夺其旌节，并发兵攻梓州。',[('杨守亮','命囚攻者'),('杨守厚','执行囚夺进攻者'),('宋道弼','被囚使者')],note='囚使地点未直书，梓州为进攻目标，不标为囚押确点。')
event('gu_wang_relief_plot','顾彦晖求援，王建遣四将并密谋擒顾',38,'891年十二月癸卯、甲辰','东川、梓州',
      '癸卯顾彦晖向王建求救，甲辰王建遣华洪、李简、王宗侃、王宗弼救东川；王建密令破敌后趁顾彦晖报宴将其拘执。',
      [('顾彦晖','求援对象及密谋目标'),('王建','遣援及密令者'),('王宗涤','以华洪旧名出援将领'),('李简','王建麾下出援将领'),('王宗侃','出援将领'),('王宗弼','出援将领')],note='华洪身份由十国春秋对应传补证，稳定key王宗涤；李简按所属主将暂消歧，与广德杨行密将李简不直接合并。密谋不记已绑架顾彦晖。')
event('zongkan_breaks_yang_hou','王宗侃破七砦，杨守厚退绵州',38,'891年十二月甲辰后','东川七砦、绵州',
      '王宗侃攻破杨守厚七砦，杨守厚逃归绵州。',[('王宗侃','破砦者'),('杨守厚','败退者')],note='七砦是书载，不补具体每寨名称与坐标。')
event('zongbi_warns_gu','王宗弼泄露王建谋，顾彦晖辞宴',38,'891年十二月条；破七砦后','东川',
      '顾彦晖备犒礼，诸将回请宴饮；王宗弼告知王建密谋，顾彦晖以病推辞。',[('顾彦晖','辞宴者'),('王宗弼','告密谋者'),('王建','密谋原发起者')],note='称病为推辞，不确认其真患病；未实际赴宴被擒。')
event('feng_seizes_jin_background','冯行袭取李继臻所据金州',39,'初；确年日未载','金州、均州',
      '《通鉴》追述李茂贞养子继臻据金州，均州刺史冯行袭攻取，朝廷任冯为昭信防御使，治金州。',[('李茂贞','养父及所据一方主将'),('李继臻','据金州养子'),('冯行袭','攻取与受任者')],year=None,note='初为追叙，年未定；继臻按养父同氏省称补李，未追填后名。')
relation('李茂贞','李继臻','养父',39,'《通鉴》称继臻为李茂贞养子；李茂贞是李继臻的养父。',quote='李茂贞养子继臻据金州')
event('feng_blocks_yang_shouliang','冯行袭阻击杨守亮由金商袭京之谋',39,'段内初后的记事；确年日未定','金州、商州、京师',
      '杨守亮计划自金州、商州袭京师，冯行袭迎击，大败其军。',[('杨守亮','谋袭京者'),('冯行袭','迎击获胜者')],year=None,note='同段以初起，后句年界未明确，暂留年份空；欲袭京不记已经攻到京师。')
event('jingyuan_zhangyi','泾原获彰义军号增领渭武',40,'891年；具体月日未载','泾原、渭州、武州',
      '朝廷赐泾原军号彰义，增加所领渭州、武州。',note='是岁为年范围，无具体日；无可据兵数与现代界线。')
event('chen_yan_summons_wang_dies','陈岩病召王潮未至而去世',40,'891年；具体月日未载','福建、泉州',
      '福建观察使陈岩患病，遣使以书召泉州刺史王潮，想授军政，王潮尚未到而陈岩去世。',[('陈岩','病召及去世者'),('王潮','被召未至者')],note='欲授不等于交接已完成；通鉴与新五代史死亡年有差别，另附异说，不改主书891年。')
event('fan_hui_claims_office','范晖促军推留后并发兵拒王潮',40,'891年；陈岩去世后','福建',
      '《通鉴》称陈岩妻弟、都将范晖劝将士推己为留后，发兵抵抗王潮。《新五代史》称范晖为陈岩之婿，亲属记载不同。',[('范晖','促推留后与拒兵者'),('王潮','被拒者'),('陈岩','前任及亲属异说所指')],note='讽将士为促请，自推不写朝廷正式授；亲属异说并列，不把妻弟擅改女婿。')
rk=relation('范晖','陈岩','妻弟',40,'《通鉴》本段称范晖为陈岩妻弟；《新五代史》称婿。此边据通鉴，关系异说见引用，尚未裁定。',quote='岩妻弟都将范晖讽将士推己为留后')
# Corresponding independent histories and identity excerpts; no future careers are selected.
sk='xinwudaishi-068-891-chen-yan-fan-hui'
full=ROOT/'resources/derived/twenty-four-histories/19新五代史.jsonl';page=next(json.loads(l) for l in full.read_text().splitlines() if json.loads(l)['pdf_page']==1476)
data=page['text'].encode();local=sk+'.txt';(P/'sources'/local).write_bytes(data)
url='https://github.com/greed-216/histree/blob/17a0b9a305d40d6371bbdd66d1827c8f2f7321fa/resources/derived/twenty-four-histories/19%E6%96%B0%E4%BA%94%E4%BB%A3%E5%8F%B2.jsonl#L1476'
B['sources'].append(dict(key=sk,title='新五代史·卷68·闽世家·陈岩范晖段',source_type='primary',author='欧阳修',edition='仓库PDF逐页电子提取文本；摘取PDF第1476页原text，不改字，未核纸本。',url=url,note='原PDF页1476，对应卷68闽世家；仅补当前主段的身份与纪年异说。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk,file=local,sha256=hashlib.sha256(data).hexdigest(),url=url,upstream=str(full.relative_to(ROOT)),transformation='JSONL按pdf_page=1476提取text字段，保留原换行与字形。'));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
def extra(table,key,field,value,n,sourcekey,quote,citation,note,book,kind):
    ck=f'claim_zztj_258_0891_05_{len(B["claims"])+1:04d}'
    assert quote in (P/'sources'/next(x['file'] for x in json.loads((P/'sources/manifest.json').read_text()) if x['key']==sourcekey)).read_text()
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=value,source_key=sourcekey,citation=citation,note='原文：'+quote+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,primary_paragraph_id=Q[n]['id'],subject_key=key,source_book=book,relation=kind))
extra('event','event_zztj_258_0891_chen_yan_summons_wang_dies','start_year','《新五代史》记陈岩卒于景福元年（892），与通鉴891年条不同。',40,sk,'景福元年岩卒','卷68·闽世家·原PDF第1476页','两书纪年并列，不以新五代史覆盖通鉴事件年；当前主线年仍891。','新五代史','conflicts')
extra('person_relationship',rk,'description','《新五代史》称范晖为陈岩之婿，与通鉴妻弟说不同。',40,sk,'其婿范\n晖自称留后。','卷68·闽世家·原PDF第1476页','逐字保留提取换行；婿与妻弟说并列，不另建一个未经裁定的女婿边。','新五代史','conflicts')
# The name 华洪 is explicit in the current paragraph; the later name is corroborated at this locus.
sk2='shiguochunqiu-039-891-names'
# Add the existing fixed snapshot, then a separately archived identity excerpt when available.
identity_path=ROOT/'resources/derived/shiguochunqiu/039-hua-hong-excerpt.txt'
assert identity_path.exists()
meta=json.loads((ROOT/'resources/derived/shiguochunqiu/039-hua-hong-manifest.json').read_text())
data=identity_path.read_bytes();local='shiguochunqiu-039-891-hua-hong.txt';(P/'sources'/local).write_bytes(data)
sk2='shiguochunqiu-039-891-hua-hong';url='https://github.com/greed-216/histree/blob/'+'32fe43f3d1dfa38344bf53b23870638f899f3e99'+'/resources/derived/shiguochunqiu/039-hua-hong-excerpt.txt'
B['sources'].append(dict(key=sk2,title='十国春秋·卷39·王宗涤姓名摘录',source_type='primary',author='吴任臣',edition='维基文库电子文本逐字摘录，未核纸本，不是整卷快照。',url=url,note='只补对应华洪身份，不提前录其后来事迹。'))
mf=json.loads((P/'sources/manifest.json').read_text());mf.append(dict(key=sk2,file=local,sha256=hashlib.sha256(data).hexdigest(),url=url,upstream=meta['upstream'],transformation=meta['transformation']));(P/'sources/manifest.json').write_text(json.dumps(mf,ensure_ascii=False,indent=2)+'\n')
extra('person',people['王宗涤'],'aliases','《十国春秋》称王宗涤本姓华名洪；本段以华洪旧名所见为同一人。',38,sk2,'王宗滌，本姓華，名洪，潁川人也。','卷39·王宗涤传·姓名摘录第3行','清代汇编仅校核对应同人身份，改名确日未明，不提前构建改名事件。','十国春秋','adds')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
reviews={35:'乙酉金乡大战，朱瑾逃免，杀获殆尽无确数。',36:'李顺节前事评述年份空，戊子诏召斩首与三都劫掠分录，李顺节杨守立同人；捧日异本奉日待考。',37:'孙儒焚苏常钱镠复据、杨行密求援钱镠兵食助分录；不转终身同盟。',38:'正式授东川、囚使夺节、癸卯求援甲辰出援与密谋、破七砦、告谋辞宴分录；华洪王宗涤同人补证；李简按王建将消歧。',39:'初为追叙，金州攻取授职与杨守亮谋袭京被阻年份暂空，李继臻养父关系据原文。',40:'彰义建制与陈岩病召去世、范晖促推拒潮分录；新五代史卒年892与婿异說独立引用，不改主书。'}
for n in range(35,41):
    assert used.get(n)
    ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key'];ledger[n-1]['review']=reviews[n]
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(35,41):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=258,year=891,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(35,41)],next_paragraph='zztj-v259-y0892-p001',coverage='卷258大顺二年第35—40段连续录入，至卷末；整年完成须五批发布验证均通过。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
