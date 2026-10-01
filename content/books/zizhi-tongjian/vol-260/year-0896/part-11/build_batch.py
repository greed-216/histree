"""Curate consecutive Tongjian volume 260, year 896 paragraphs 41–48."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p041-p048', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-260-896-library-end'
fixed_commit='72b0336'
manifest=[]
source_specs=[(source,'资治通鉴·卷260·乾宁三年年末连续段落','司马光等'),('jiuwudaishi-026-896-weizhou','旧五代史·卷26·武皇白龙潭战','薛居正等'),('jiuwudaishi-135-896-liu-yin','旧五代史·卷135·刘隐迎知柔','薛居正等'),('xintangshu-010-896-li-shiyue','新唐书·卷10·李师悦卒','欧阳修、宋祁等')]
for sk,title,author in source_specs:
    if sk==source:
        records=[json.loads((P/'sources/library'/part/'paragraph.json').read_text()) for part in ['tongjian-end-a','tongjian-end-b']]
        filename='tongjian-260-896-end.txt'; citation='《资治通鉴》卷260乾宁三年；原TXT连续段落 '+ '、'.join(r['id'] for r in records)
    else:
        records=[json.loads((P/'sources/library'/sk/'paragraph.json').read_text())];filename='library/'+sk+'/source.txt';citation=records[0]['citation']
    snapshot=P/'sources'/filename;url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str(snapshot.relative_to(ROOT))
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；电子本，纸本及异文待核。',url=url,note=citation))
    manifest.append(dict(key=sk,file=filename,sha256=hashlib.sha256(snapshot.read_bytes()).hexdigest(),url=url,paragraph_ids=[r['id'] for r in records],upstream_locators=[r['locator'] for r in records],transformation='主书两份相邻导出TXT原字节拼接，其他书保导出原TXT；不改疑字。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in range(41,49):assert Q[n]['text'] in (P/'sources/tongjian-260-896-end.txt').read_text()
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'王熔':'王镕','国弘信':'罗弘信','硃友裕':'朱友裕','赫连鐸':'赫连铎','硃崇节':'朱崇节','杨儒':'王宗儒','李晔':'李杰','李顺节':'杨守立','胡弘立':'杨守立','唐昭宗':'李杰','硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖','张廷范':'张延范','王鐸':'王铎','雷鄴':'雷邺','陈建瑄':'陈敬瑄','时浦':'时溥'}
people, used, reused = {}, {}, set()
alias.update({'硃朴':'朱朴','韩健':'韩建','嗣覃王嗣周':'李嗣周','覃王嗣周':'李嗣周','李钅岁':'李鐬','李彦威':'朱友恭','硃友恭':'朱友恭','硃友裕':'朱友裕','张夫人':'张氏（朱温妻）','李抱真':'李抱真（李匡威判官）','郑渥':'王宗渥','华洪':'王宗涤','李简':'李简（王建将）','王宗阮':'文武坚','王宗本':'谢从本'})

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_260_0896_11_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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

def e(code,title,n,q,actors=(),when=None,place=None,note=None,description=None):
    return event(code,title,n,when or '896年本段条；确日未载',place,description or title+'。',actors,quote=q,note=note)
e('qian_orders_east_petition','钱镠令两浙吏民表请兼浙东',41,'钱镠令两浙吏民上表，请以镠兼领浙东',[('钱镠','令表请者')],when='896年十月条；确日未载',place='两浙',note='吏民上表由钱镠下令，非据此认定全部民众自发拥护。')
e('wang_tuan_restored_court','王抟复吏部尚书同平章事',41,'朝廷不得已，复以王抟为吏部尚书、同平章事',[('王抟','复朝职者')],when='896年十月条；确日未载')
e('qian_two_governorships','钱镠领镇海威胜两军',41,'以镠为镇海、威胜两军度使。',[('钱镠','受两军者')],when='896年十月条；确日未载',note='度使为底本缺字，按两军节度使释读，原摘录保留。')
e('weisheng_renamed_zhendong','威胜军更名镇东军',41,'丙子，更名威胜曰镇东军。',when='896年十月丙子',place='威胜军')
e('li_keyong_bailongtan_guanyin','李克用败魏兵于白龙潭，追至观音门',42,'李克用自将攻魏州，败魏兵于白龙潭，追至观音门。',[('李克用','亲征胜者')],when='896年十月条；确日未载',place='魏州、白龙潭、观音门',note='追至门不写魏州城已陷。')
e('zhu_ge_huanshui_rescue_li_retreat','朱温遣葛从周屯洹水救魏并继大军，李克用还',42,'硃全忠复遣葛从周救之，屯于洹水，全忠以大军继之。克用乃还。',[('朱温','遣军继援者'),('葛从周','援军屯驻者'),('李克用','还军者')],when='896年十月白龙潭战后；确日未载',place='洹水')
e('wang_ke_added_pingzhang','王珂加同平章事',43,'加河中节度使王珂同平章事。',[('王珂','受加官者')],when='896年十月条；确日未载',place='河中')
e('zhu_returns_daliang_november','朱温还大梁',44,'十一月，硃全忠还大梁',[('朱温','还镇者')],when='896年十一月；确日未载',place='大梁')
e('ge_pang_attack_yun_november','葛从周东会庞师古攻郓州',44,'复遣葛从周东会庞师古，攻郓州。',[('朱温','遣将者'),('葛从周','东会攻者'),('庞师古','会军攻者')],when='896年十一月朱温还大梁后；确日未载',place='郓州',note='攻城不写郓州已经陷落；接下年围攻段。')
e('li_shiyue_requests_banner','李师悦求旌节',45,'湖州刺史李师悦求旌节',[('李师悦','请求者')],when='896年十一月条；确日未载',place='湖州')
e('zhongguo_established_li_appointed','湖州置忠国军，李师悦受节度使',45,'诏置忠国军于湖州，以师悦为节度使。',[('李师悦','受节度使者')],when='896年十一月条；确日未载',place='湖州',note='诏命与旌节实际送达区分，未写受节现场仪式。')
e('li_shiyue_dies_before_documents','李师悦卒，告身旌节使者尚未入境',45,'赐告身旌节者未入境，戊子，师悦卒。',[('李师悦','卒者')],when='896年十一月戊子',place='湖州',note='人物已有稳定主体，复用人物记录；本批新增死亡事实引用，不覆盖旧人物行。')
claim('person',people['李师悦'],'death_year','李师悦卒于乾宁三年十一月戊子（896）；赐告身旌节者尚未入境。',45,quote='赐告身旌节者未入境，戊子，师悦卒。')
e('yang_petitions_li_yanhui_huzhou','杨行密表李师悦之子彦徽知湖州事',45,'杨行密表师悦子前绵州刺史彦徽知州事。',[('杨行密','上表者'),('李彦徽（湖州）','被表知州者')],when='896年十一月李师悦卒后；确日未载',place='湖州',note='主书称彦徽，按李师悦之子用姓氏及湖州消歧；新唐书作继徽且自称留后，暂不并入其他李继徽人物。前绵州官有本句，不补生年。')
a=people['李师悦'];b=people['李彦徽（湖州）'];rk=f'relationship_{a}_{b}_父亲'
B['person_relationships'].append(dict(key=rk,person_a_key=a,person_b_key=b,relation_type='父亲',description='李师悦是湖州彦徽的父亲。',status='draft'))
claim('person_relationship',rk,'description','李师悦是湖州彦徽的父亲。',45,quote='杨行密表师悦子前绵州刺史彦徽知州事。',note='父亲方向明示；彦徽与补书记继徽异名待核，不合并异地李继徽。')
e('an_renyi_attacks_wuzhou','安仁义攻婺州',46,'淮南将安仁义攻婺州。',[('安仁义','进攻者')],when='896年十一月条；确日未载',place='婺州',note='仅记攻，不补陷城、胜负或钱镠亲自参战。')
e('dongchuan_burns_han_mei_zi_jian','东川兵焚掠汉眉资简境',47,'十二月，东川兵焚掠汉、眉、资简之境。',when='896年十二月；确日未载',place='汉、眉、资简之境',note='原段未名将领，不凭东川所属替具体人建参与边；未记各州城均陷。')
e('guangzhou_officers_reject_zhirou','卢琚与谭弘拒李知柔，令谭弘守端州',48,'清海节度使薛王知柔行至湖南，广州牙将卢琚、谭弘据境拒之，使弘守端州。',[('李知柔','赴镇被拒者'),('卢琚','据境拒命者'),('谭弘（末字待考）','拒命守端州者')],when='896年十二月条；确日未载',place='湖南、广州、端州',note='谭弘末字私用字保原文，以末字待考显示；旧五代史作谭玘，姓名对应待核，不将私用字猜成确定汉字。')
e('tan_proposes_daughter_liu_feigns','谭弘许女给刘隐，刘隐佯许托亲迎',48,'弘结封州刺史刘隐，许妻以女。隐伪许之，托言亲迎',[('谭弘（末字待考）','许女结交者'),('刘隐','佯许者')],when='896年十二月端州袭击前；确日未载',note='妻以女是提议，伪许是计谋；不建实际婚姻或岳父关系，不新建无名女儿。')
e('liu_night_duanzhou_kills_tan','刘隐伏甲舟中夜入端州，斩谭弘',48,'伏甲舟中，夜入端州，斩弘',[('刘隐','伏甲夜袭者'),('谭弘（末字待考）','被斩者')],when='896年十二月夜；确日未载',place='端州')
e('liu_attacks_guangzhou_kills_lu','刘隐袭广州斩卢琚',48,'遂袭广州，斩琚',[('刘隐','袭城者'),('卢琚','被斩者')],when='896年十二月端州袭击后；确日未载',place='广州')
e('liu_welcomes_zhirou','刘隐具军容迎李知柔入视事',48,'具军容迎知柔入视事',[('刘隐','迎镇者'),('李知柔','入视事者')],when='896年十二月袭广州后；确日未载',place='广州')
e('zhirou_petitions_liu_sima','李知柔表刘隐为行军司马',48,'知柔表隐为行军司马。',[('李知柔','上表者'),('刘隐','被表者')],when='896年十二月入视事后；确日未载',place='广州',note='主书表为与补书辟为分录书证，不推得中央批准日期。')
supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
    record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_260_0896_11_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiuwudaishi-026-896-weizhou','event','event_zztj_260_0896_li_keyong_bailongtan_guanyin','description','《旧五代史》记十月武皇败魏军于白龙潭，追至观音门。','十月，武皇敗魏軍於白龍潭，追擊至觀音門，汴軍救至，乃退。',42,'卷26武皇纪上下文乾宁三年；不将十一月征兵迎驾并作本月实际入华。','corroborates')
extra('xintangshu-010-896-li-shiyue','event','event_zztj_260_0896_li_shiyue_dies_before_documents','description','《新唐书》亦记十一月戊子忠国军节度使李师悦卒。','十一月戊子，忠國軍節度使李師悅卒，其子繼徽自稱留後。',45,'卷10昭宗乾宁三年条；死亡日对应，儿子名号和接职方式异文另列。','corroborates')
extra('xintangshu-010-896-li-shiyue','person',people['李彦徽（湖州）'],'description','《新唐书》本次湖州接职记李师悦之子继徽自称留后；通鉴称彦徽、杨行密表知州事。','十一月戊子，忠國軍節度使李師悅卒，其子繼徽自稱留後。',45,'同父同地接职对应保留两书记法，异名待校，不设确定改名别名，不与静难李继徽合并。','conflicts')
extra('jiuwudaishi-135-896-liu-yin','person',people['刘隐'],'description','《旧五代史》记刘隐为封州刺史，诛拒命牙将后受辟行军司马、委兵赋。','俄奏兼封州刺史，用法清肅，威望頗振。',48,'卷135僭伪刘氏传叙事；任封州身份补证，不把幼年、父母和梁封爵都定896。','corroborates')
extra('jiuwudaishi-135-896-liu-yin','person',people['谭弘（末字待考）'],'description','《旧五代史》相关清海拒命记牙将谭玘；通鉴作谭弘加私用字。','有府之牙將盧琚、譚玘謀不稟朝命',48,'同卢琚拒命事件对应保留异文；源文谭玘不当已核定通鉴末字或正式别名。','conflicts')
extra('jiuwudaishi-135-896-liu-yin','event','event_zztj_260_0896_zhirou_petitions_liu_sima','description','《旧五代史》记知柔到任后辟刘隐行军司马，委以兵赋。','知柔至，深德之，辟為行軍司馬，委以兵賦。',48,'该传不具本句年月，独立补任职方式和事务；不推已具中央批复。','adds')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(41,49):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='年末八段连续校核；奏请与授命、进攻与陷城、佯婚与实婚分清。旧五代史白龙潭和刘隐、新唐书师悦之子独立补证；彦徽/继徽和谭弘私用字/谭玘保异文待核。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(41,49)],next_paragraph='zztj-v261-y0897-p001',coverage='第41—48段连续整理，全年是否完成以所有批次发布读回及跨卷检查为准。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
