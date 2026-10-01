"""Curate consecutive Tongjian volume 260, year 896 paragraphs 31–40."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 49))
B = {'format_version': 1, 'batch_key': 'zztj-v260-y0896-p031-p040', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source='tongjian-260-896-library-3097'
fixed_commit='64f09f6'
source_specs=[(source,'资治通鉴·卷260·乾宁三年连续段落','司马光等'),('jiutangshu-179-896-zhu-pu','旧唐书·卷179·朱朴附传','刘昫等'),('xinwudaishi-066-896-gao-yu','新五代史·卷66·马殷问高郁策','欧阳修')]
manifest=[]
for sk,title,author in source_specs:
    d=P/'sources/library'/sk; record=json.loads((d/'paragraph.json').read_text()); audit=json.loads((d/'manifest.json').read_text()); filename='library/'+sk+'/source.txt'
    url='https://github.com/greed-216/histree/blob/'+fixed_commit+'/'+str((P/'sources'/filename).relative_to(ROOT))
    B['sources'].append(dict(key=sk,title=title,source_type='primary',author=author,edition='选定TXT逐字导出；EPUB电子本，纸本及异文待核。',url=url,note=record['citation']))
    manifest.append(dict(key=sk,file=filename,sha256=audit['sha256'],url=url,paragraph_id=record['id'],upstream=record['locator']['source_file'],upstream_locator=record['locator'],transformation='按导出定位逐字截取TXT，保原换行空格。'))
(P/'sources/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
for n in range(31,41):assert Q[n]['text'] in (P/'sources/library'/source/'source.txt').read_text()
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
    B['claims'].append(dict(key=f'claim_zztj_260_0896_10_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷260·乾宁三年（896）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

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
e('qian_added_zhongshuling','钱镠加兼中书令',31,'加钱镠兼中书令。',[('钱镠','受加官者')],when='896年八月条；确日未载')
e('wang_jian_fengxiang_west_commander','王建为凤翔西面行营招讨使',32,'癸丑，以王建为凤翔西面行营招讨使。',[('王建','受招讨使者')],when='896年八月癸丑')
e('wang_tuan_weisheng_governor','王抟以同平章事充威胜节度使',33,'甲寅，以门下侍郎、同平章事王抟同平章事，充威胜节度使。',[('王抟','受威胜节度使者')],when='896年八月甲寅',place='威胜军')
e('zhu_pu_claims_month_peace','朱朴自称任相月余可致太平，帝信之',34,'上愤天下之乱，思得奇杰之士不次用之。国子博士硃朴自言：“得为宰相，月馀可致太平。”上以为然。',[('朱朴','自称者'),('唐昭宗','信其说者')],when='896年八月条；任朱朴相之前',note='月余可太平是朱自言，未记月余后天下实际太平。')
e('zhu_pu_appointed_chancellor','朱朴为左谏议大夫同平章事',34,'乙丑，以朴为左谏议大夫、同平章事。朴为人庸鄙迂僻，无它长。制出，中外大惊。',[('朱朴','受相职者')],when='896年八月乙丑',note='庸鄙迂僻和中外大惊是主书评价；不当作独立心理证据。')
e('han_jian_added_zhongshuling','韩建加兼中书令',34,'丙寅，加韩建兼中书令。',[('韩建','受加官者')],when='896年八月丙寅')
e('wang_chao_fujian_weiwu','福建升威武军，王潮为节度使',35,'九月，庚辰，升福建为威武军，以观察使王潮节度使。',[('王潮','受节度使者')],when='896年九月庚辰',place='福建',note='观察使到节度使为本段任职转换，不追溯写其先前已为节度使。')
e('ma_yin_administers_hunan','马殷判湖南军府事',36,'以湖南留后马殷判湖南军府事。',[('马殷','受判军府事者')],when='896年九月条；确日未载',place='湖南',note='本段仍湖南留后，不提前称正式节度使或楚王。')
e('ma_yin_uses_gao_yu','马殷以高郁为谋主',36,'殷以高郁为谋主。郁，扬州人也。',[('马殷','以为谋主者'),('高郁','谋主')],when='896年九月条；确日未载',note='高郁籍贯扬州有明句，未补现代行政地或生年。')
claim('person',people['高郁'],'description','高郁为扬州人，马殷以之为谋主。',36,quote='殷以高郁为谋主。郁，扬州人也。')
e('ma_considers_gifts_yang_cheng','马殷畏杨行密成汭，议以金帛结之',36,'殷畏杨行密、成汭之强，议以金帛结之',[('马殷','议送金帛者')],when='896年九月条；确日未载',note='议为打算，未作实际送财或结盟。')
e('gao_yu_advises_court_people_army','高郁劝奉天子抚士民训兵，马殷从之',36,'高郁曰：“成汭不足畏也，行密公之仇。虽以万金赂之，安肯为吾援乎！不若上奉天子，下抚士民，训卒厉兵，以修霸业，则谁与为敌矣。”殷从之。',[('高郁','劝说者'),('马殷','采纳者')],when='896年九月议金帛以后；确日未载',note='成汭不足畏及万金无援为高陈词，不写万金已经交付；采纳不等于全部政策已完成。')
e('cui_requests_zhu_build_luoyang','崔胤密向朱温求援，教营东都迎帝',37,'崔胤出镇湖南，韩建之志也。胤密求援于硃全忠，且教之营东都宫阙，表迎车驾',[('崔胤','密求援提出营宫者'),('朱温','受请求者')],when='896年九月条；确日未载',note='韩建之志归于主书；教营为建议，未记已营成宫阙。')
e('zhu_zhang_request_luoyang_twenty_thousand','朱温张全义表请帝迁洛阳，朱温请二万兵迎',37,'且全忠与河南尹张全义表请上廷都洛阳，全忠仍请以兵二万迎车驾，且言崔胤忠臣，不宜出外。',[('朱温','表请迎驾者'),('张全义','共同表请者')],when='896年九月条；确日未载',note='廷都保底本疑字，按迁都请求释读；二万为请带兵数，不作二万军已发，忠臣是朱陈词。',description='朱温与河南尹张全义表请唐昭宗迁都洛阳，底本作廷都；朱温又请以二万兵迎驾，称崔胤忠臣不宜出外。')
e('han_petitions_cui_return_zhu_stops','韩建奏召崔胤为相并劝朱温安静，朱温止',37,'韩建惧，复奏召胤为相，遣使谕全忠以且宜安静，全忠乃止。',[('韩建','奏召遣谕者'),('朱温','止迎议者')],when='896年九月迎驾奏后；确日未载',note='止承前请迎，不补取消全部军事行动或永久联盟。')
e('cui_yin_restored_chancellor','崔胤复中书侍郎同平章事',37,'乙未，复以胤为中书侍郎、同平章事。',[('崔胤','复相者')],when='896年九月乙未')
e('cui_yuan_appointed_chancellor','崔远以翰林承旨兵部侍郎入相',37,'以翰林学士承旨、兵部侍郎崔远同平章事。远，珙弟玙之孙也。',[('崔远','受相职者')],when='896年九月乙未条；确日未另载',note='珙弟玙之孙指崔玙是崔远祖父，不将崔珙写成祖父。')
e('lu_yi_demoted_cui_false_accusation','陆扆贬硖州，崔胤诬其党李茂贞',37,'丁酉，贬中书侍郎、同平章事陆扆为硖州刺史。崔胤恨扆代己，诬扆，云党于李茂贞而贬之。',[('陆扆','被贬者'),('崔胤','诬告者')],when='896年九月丁酉',place='硖州',note='诬党为主书明确归属，未增加陆扆与李茂贞同盟边。')
person('崔珙',37,'主书以崔远祖父崔玙之兄出现');person('崔玙',37,'崔珙之弟、崔远祖父')
for a,b,t,description in [('崔珙','崔玙','兄长','崔珙是崔玙的兄长。'),('崔玙','崔远','祖父','崔玙是崔远的祖父。')]:
 ka,kb=people[a],people[b];rk=f'relationship_{ka}_{kb}_{t}';B['person_relationships'].append(dict(key=rk,person_a_key=ka,person_b_key=kb,relation_type=t,description=description,status='draft'));claim('person_relationship',rk,'description',description,37,quote='远，珙弟玙之孙也。',note='方向按A是B的角色，未补崔远父名。')
e('zhu_pu_assigned_hubu_finances','朱朴兼判户部，帝委军旅财赋',38,'己亥，以硃朴兼判户部，凡军旅财赋之事，上一以委之。',[('朱朴','兼判受委者'),('唐昭宗','委事者')],when='896年九月己亥')
e('sun_wo_fengxiang_four_routes','孙偓为凤翔四面行营都统',38,'以孙偓为凤翔四面行营都统',[('孙偓','受都统者')],when='896年九月己亥条；确日未另载')
e('li_sijian_jingnan_deputy','李思谏任静难节度使兼副都统',38,'又以前定难节度使李思谏为静难节度使，兼副都统。',[('李思谏','受静难副都统者')],when='896年九月己亥条；确日未另载',note='定难为此前职，静难为本段新职，不混同两军。')
e('li_sijing_baoda_governor','保大留后李思敬为节度使',39,'以保大留后李思敬为节度使。',[('李思敬','受保大节度使者')],when='896年九月条；确日未载')
e('li_cunxin_wins_zongcheng','李存信攻临清，败葛从周于宗城北至魏北门',39,'河东将李存信攻临清，败汴将葛从周于宗城北，乘胜至魏州北门。',[('李存信','进攻胜者'),('葛从周','败将')],when='896年九月条；确日未载',place='临清、宗城北、魏州北门',note='至北门不作魏州已经陷落。')
e('sun_wo_added_campaign_posts','孙偓加行营节度招讨处置等使',40,'冬，十月，壬子，加孙偓行营节度、招讨、处置等使。',[('孙偓','受加官者')],when='896年十月壬子')
e('han_jian_acting_jingzhao','韩建权知京兆尹兼把截使',40,'丁已，以韩健权知京兆尹，兼把截使。',[('韩建','受权知者')],when='896年十月底本丁已',note='韩健按上下文复用韩建，保疑姓名原摘录；丁已不静改丁巳，未换公历。')
e('mao_petitions_repents_han_supports_no_army','李茂贞请罪献修宫钱，韩建佐助而未出师',40,'戊午，李茂贞上表请罪，愿得自新，仍献助修宫室钱；韩建复佐佑之，竟不出师。',[('李茂贞','表请献钱者'),('韩建','佐助者')],when='896年十月戊午',note='愿自新为茂贞表辞；未出师承前讨茂贞议，未作茂贞完全解除全部军队。')

supplements=[]
def extra(sk,table,key,field,text,q,n,note,kind='adds'):
    record=json.loads((P/'sources/library'/sk/'paragraph.json').read_text());assert q in (P/'sources/library'/sk/'source.txt').read_text();ck=f'claim_zztj_260_0896_10_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck,subject_table=table,subject_key=key,field_path=field,claim_text=text,source_key=sk,citation=record['citation'],note='原文：'+q+'；核对说明：'+note,status='draft'))
    supplements.append(dict(claim_key=ck,source_book=record['book'],primary_paragraph_id=Q[n]['id'],subject_key=key,relation=kind))
extra('jiutangshu-179-896-zhu-pu','person',people['朱朴'],'description','《旧唐书》朱朴附传记其乾宁中为国子博士。','朱朴者，乾寧中爲國子博士。',34,'卷179正文与选定TXT定位核对；人物复用，不把传中后事全部定在896。','corroborates')
extra('jiutangshu-179-896-zhu-pu','event','event_zztj_260_0896_zhu_pu_appointed_chancellor','description','《旧唐书》记昭宗召朱朴，因其以经义对答而悦，拜谏议大夫平章事。','昭宗召見，對以經義，甚悅，即日拜諫議大夫、平章事。',34,'该传未具本句年月和左右官称，不覆盖主书乙丑、左谏议；评价与后事未据此当确证。','adds')
extra('xinwudaishi-066-896-gao-yu','person',people['高郁'],'description','《新五代史》记马殷问策于其将高郁，高郁建议奉朝廷、修兵农。','殷初兵力尚寡，與楊行密、成汭、劉龑等為敵國，殷患之，問策於其將高郁',36,'该书背景未具年，刘龑等属更广时段，不能把所列全部敌国关系都定896。','adds')
extra('xinwudaishi-066-896-gao-yu','event','event_zztj_260_0896_gao_yu_advises_court_people_army','description','《新五代史》高郁建议内奉朝廷求封爵，退修兵农、畜力待时。','今宜內奉朝廷以求封爵而外誇隣敵，然後退脩兵農，畜力而有待爾。',36,'两书相关谋议各保陈词，未视为独立证实已经完成政策；该书后续茶税钱制本批未倒填896。','corroborates')
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n';audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(31,41):ledger[n-1].update(event_keys=used[n],batch_key=B['batch_key'],review='十段连续校核；任职、陈词、请求与实际行动分录，崔玙祖孙和崔珙兄弟方向明示。新选定TXT片段逐字导出，旧唐书朱朴、新五代史高郁独立補人物及事件依据，异字及后事不强定896。',status=status)
(P/'content-batch.json').write_text(payload);(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n');(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=260,year=896,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(31,41)],next_paragraph=Q[41]['id'],coverage='第31—40段连续整理；本年未完成。',supplements=supplements,status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
