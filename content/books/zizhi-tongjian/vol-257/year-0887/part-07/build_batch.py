"""Curate consecutive Tongjian volume 257, year 887 paragraphs 49–59."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
Q = {int(p['id'][-3:]): p for p in json.loads((YEAR / 'paragraphs.json').read_text())}
assert list(Q) == list(range(1, 60))
B = {'format_version': 1, 'batch_key': 'zztj-v257-y0887-p049-p059', **{k: [] for k in ['people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics']}}
source = 'tongjian-257-887'
B['sources'] = [dict(key=source,title='资治通鉴·卷257',source_type='primary',author='司马光等',edition='仓库电子文本；未核纸本。疑似转录讹字保留并单独注明。',url='https://github.com/greed-216/histree/blob/5911e959ccc6b7efae3e673a6f8bcb612a9748a0/resources/derived/tongjian/257.txt',note='卷257光启三年起；书、卷、年、段落及行号见批次账本。')]
raw = (ROOT / 'resources/derived/tongjian/257.txt').read_bytes()
(P / 'sources').mkdir(parents=True, exist_ok=True)
(P / 'sources' / (source + '.txt')).write_bytes(raw)
(P / 'sources/manifest.json').write_text(json.dumps([dict(key=source, file=source + '.txt', sha256=hashlib.sha256(raw).hexdigest(), url=B['sources'][0]['url'], upstream='resources/derived/tongjian/257.txt', transformation='none')], ensure_ascii=False, indent=2) + '\n')
registry = {}
for f in sorted((ROOT / 'content').rglob('content-batch.json')):
    if f.resolve() == (P / 'content-batch.json').resolve() or ('books' in f.parts and str(f) > str(P / 'content-batch.json')):
        continue
    for row in json.loads(f.read_text())['people']:
        if row['name'] in registry:
            assert registry[row['name']]['key'] == row['key'], (f, row['name'])
        registry[row['name']] = row
alias = {'硃全忠':'朱温','硃敬玫':'朱敬玫','硃玫':'朱玫','硃政':'朱政','嗣襄王煴':'李煴','襄王煴':'李煴','郭禹':'成汭','硃瑄':'朱瑄','硃裕':'朱裕','硃珍':'朱珍','冯弘鐸':'冯弘铎','毕师鐸':'毕师铎','师鐸':'毕师铎','张神剑':'张神剑（高邮）','宋兗':'宋兖'}
people, used, reused = {}, {}, {source}

def claim(table, key, field, value, n, quote=None, note=None):
    q = quote or Q[n]['text']
    assert q in Q[n]['text']
    B['claims'].append(dict(key=f'claim_zztj_257_0887_07_{len(B["claims"])+1:04d}', subject_table=table, subject_key=key, field_path=field, claim_text=value, source_key=source, citation=f'卷257·光启三年（887）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行', note=f'原文：{q}；核对说明：{note or "按本段原文整理，不补写未载的月日、地点或人物完整生平。"}', status='draft'))

def person(name,n,role):
    name=alias.get(name,name)
    if name in people:return people[name]
    if name in registry:
        row=dict(registry[name],status='draft');reused.add(row['key'])
    else:
        row=dict(key='person_'+name,name=name,aliases=(['郭禹'] if name=='成汭' else ['嗣襄王煴'] if name=='李煴' else ['訾亮'] if name=='杨守亮' else ['张神剑'] if name=='张神剑（高邮）' else []),era='晚唐',birth_year=None,death_year=None,description=f'《资治通鉴》卷257光启三年条所见人物：{name}。',biography=None,status='draft')
    B['people'].append(row);people[name]=row['key']
    claim('person',row['key'],'description',f'本段记{name}：{role}。',n)
    return row['key']

def event(code,title,n,when,place,description,actors=(),year=887,note=None,quote=None):
    key='event_zztj_257_0887_'+code
    B['events'].append(dict(key=key,title=title,start_year=year,end_year=year,time_original=when,dynasty='唐',description=description,phases=[],location_name=place,location_modern_name=None,location_lat=None,location_lng=None,location_precision='unknown',location_note='仅保留史载地名；未核坐标。' if place else '原文未给单一地点。',status='draft'))
    used.setdefault(n,[]).append(key)
    claim('event',key,'description',description,n,quote,note)
    claim('event',key,'time_original',when,n,quote,note or ('段内追叙，确年待考。' if year is None else '干支日未换算公历日。'))
    for name,role in actors:
        pk=person(name,n,role);edge='participation_zztj_257_0887_'+code+'_'+pk
        B['person_events'].append(dict(key=edge,person_key=pk,event_key=key,role=role,status='draft'))
        claim('person_event',edge,'role',f'{name}：{role}。',n,quote)
    return key

event('zhu_huainan_command','朝廷命朱全忠兼淮南节度使',49,'光启三年闰月；具体日未载','淮南',
      '朝廷因淮南久乱，任朱全忠兼淮南节度使、东南面招讨使。',
      [('朱温','以朱全忠名义受任者')],
      note='闰月照原文，不自行断定闰几月；授官不代表已经实控淮南。')
event('chen_tian_summon_wang','陈敬瑄与田令孜召王建',50,'光启三年闰月前后；具体日未载','西川、梓州',
      '陈敬瑄忧顾彦朗与王建合兵图己，与田令孜商议后遣使召王建；王建赴梓州见顾彦朗，留家于梓州，率部西行。',
      [('陈敬瑄','商议及遣召者'),('田令孜','建议召王建者'),('王建','受召及西行者'),('顾彦朗','王建赴见者')],
      note='陈敬瑄“恐其合兵图己”是其担忧，不作为顾彦朗、王建已结盟进攻的事实。')
event('wang_jian_sons_march','王建率从子假子西行',50,'受召后；具体日未载','梓州至鹿头关',
      '王建率亲兵与从子、假子西行；原文具名王宗瑶、王宗弼、王宗侃、王宗弁等。',
      [('王建','率军者'),('王宗瑶','随行假子'),('王宗弼','随行假子'),('王宗侃','随行假子'),('王宗弁','随行假子')],
      note='另一从子名在电子底本作“宗钅岁”，字形待校，不据残字创稳定人物。兵数“二千”为原文数字。')
for current,old in [('王宗瑶','姜郅'),('王宗弼','魏弘夫'),('王宗侃','田师侃'),('王宗弁','鹿弁')]:
    row=next(x for x in B['people'] if x['key']==people[current])
    if old not in row['aliases']:row['aliases'].append(old)
    claim('person',row['key'],'aliases',f'{current}原名{old}。',50,
          note='原文列假子改名及旧名；不据此推断其受养的具体年份。')
event('chen_revokes_invitation','陈敬瑄拒王建过鹿头关',50,'王建抵鹿头关后；具体日未载','鹿头关',
      '一名西川参谋劝陈敬瑄勿引王建入境；陈敬瑄遣人阻止，并加强关防。王建因此愤怒。',
      [('陈敬瑄','收回邀请及设防者'),('王建','被拒者')],
      note='底本作“参谋乂李”，另一电子文本也有字序疑点；姓名未核定，暂不建具名人物。')
event('wang_jian_takes_hanzhou','王建破关取汉州德阳',50,'被拒鹿头关后；具体日未载','鹿头关、绵竹、汉州、蚕北、德阳',
      '王建破鹿头关，败汉州刺史张顼于绵竹，取汉州；进军学射山，又败西川将句惟立于蚕北，取德阳。',
      [('王建','进军及攻取者'),('张顼','被击败者'),('句惟立','被击败者')],
      note='连战先后据原文，不擅配具体干支日。')
event('wang_jian_chengdu_attempt','王建与顾彦朗攻成都未克',50,'王建取德阳后；具体日未载','成都、汉州',
      '田令孜劝慰王建未果；顾彦朗任其弟顾彦晖为汉州刺史，并发兵助王建攻成都。三日未克，王建军退屯汉州。',
      [('田令孜','劝慰者'),('王建','攻城及退屯者'),('顾彦朗','遣援军及任弟者'),('顾彦晖','受任汉州刺史者'),('陈敬瑄','成都守方主将')],
      note='田令孜为劝慰者，不把他的言辞推作议和成功。')
event('court_seeks_sichuan_peace','朝廷遣使调解西川冲突',50,'王建攻成都不克后；具体日未载','成都、汉州',
      '陈敬瑄向朝廷告急，朝廷遣使调解，并命人致书劝谕，但冲突双方未从。',
      [('陈敬瑄','告急者'),('王建','劝谕对象')],
      note='底本“节茂贞”疑讹，不据此直接归责李茂贞为致书者；调解结果依原文“不从”。')
event('yang_kills_gao_ba','杨行密杀高霸丁从实余绕山',51,'光启三年闰月己酉','广陵',
      '杨行密听袁袭关于高霸恐反复的进言后，伏兵拘杀高霸、丁从实、余绕山，又袭杀法云寺中高霸部众。高暀出逃，次日被捕杀。',
      [('袁袭','进言者'),('杨行密','下令者'),('高霸','被杀者'),('丁从实','被杀者'),('余绕山','被杀者'),('高暀','次日被杀者')],
      note='袁袭所言高霸将叛是其判断，不当作高霸已叛事实；“数千人”为原文死者概数。')
event('lv_yongzhi_executed','杨行密处死吕用之及族党',52,'光启三年闰月庚戌','广陵',
      '杨行密以吕用之承诺给军士的银子未兑现为由将其拘禁，命田頵讯问，随后将吕用之腰斩，并诛其族党。',
      [('杨行密','拘捕及处置者'),('吕用之','被处死者'),('田頵','讯问者')],
      note='吕用之此前所许埋银未获证实；“桐入”疑底本讹字，原文保留。')
event('lv_interrogation_claim','吕用之讯问中出现谋杀高骈说法',52,'光启三年闰月庚戌','广陵',
      '《通鉴》记田頵讯问吕用之时，有郑杞、董瑾拟借斋会杀高骈、推吕用之为节度使的说法。',
      [('田頵','讯问者'),('吕用之','被讯问者')],
      note='原文“云”未明交代供词来源，且出现在刑讯语境；仅登记为审讯中出现的说法，不当作已实施谋杀。')
event('yang_sends_forces_away','杨行密遣兵与辎重返和庐',53,'光启三年闰月甲寅至乙卯','广陵、和州、庐州',
      '袁袭因广陵饥弊、蔡军将至而建议避敌。杨行密遣延陵宗率部返和州，又命蔡俦率兵及辎重返庐州。',
      [('袁袭','建议者'),('杨行密','遣返者'),('延陵宗','率部返和州者'),('蔡俦','率兵返庐州者')],
      note='袁袭“民必重困”是预测；兵数与辎重车数均照书载。')
event('zhang_xiong_takes_shangyuan','张雄攻取上元，赵晖被部下杀',53,'光启三年闰月戊午','上元、当涂',
      '赵晖据上元，与东塘张雄不通问并以兵堵江；张雄攻下上元。赵晖奔当涂途中被部下杀死。',
      [('张雄','攻取者'),('赵晖','被逐及被杀者')],
      note='赵晖部下未具名，不将杀赵晖直接归责张雄。')
event('zhang_xiong_kills_surrendered','张雄坑杀赵晖降众',53,'上元被攻后；具体日未载','上元',
      '赵晖余众投降张雄，张雄将其全部坑杀。',
      [('张雄','坑杀者'),('赵晖','被杀降众原统领')],
      note='人数未载，不作估算。')
event('zhu_sends_li_fan_huainan','朱全忠遣李璠赴淮南',54,'光启三年闰月后；具体日未载','淮南、泗州',
      '朱全忠遣张延范传达朝命，拟授杨行密淮南节度副使、李璠淮南留后，并遣郭言率军护送李璠。',
      [('朱温','以朱全忠名义遣使者'),('张延范','传命者'),('杨行密','拟受副使者'),('李璠','拟赴淮南留后者'),('郭言','护送者')],
      note='仅记朝命及赴任尝试，不能推为李璠已在淮南视事。')
event('shi_pu_blocks_li_fan','时溥袭李璠，徐汴交恶',54,'李璠至泗州时；具体日未载','泗州',
      '时溥不许朱全忠军借道，在李璠抵泗州时发兵袭击；郭言力战得免而返，此后徐、汴交恶。',
      [('时溥','拒借道及袭击者'),('李璠','被袭者'),('郭言','护送及突围者'),('朱温','以朱全忠名义请求借道者')],
      note='时溥官位与先后资历是其怨望背景，不视为合法控制淮南的既成事实。')
event('zhao_deyin_takes_jingnan','赵德諲陷荆南杀张瑰',55,'光启三年十二月癸巳','荆南',
      '秦宗权所署赵德諲攻陷荆南，杀节度使张瑰，留部将王建肇守城后离开。',
      [('秦宗权','署任者'),('赵德諲','攻陷及杀人者'),('张瑰','被杀者'),('王建肇','留守者')],
      note='“遗民才数百家”为书载战后概数；王建肇与本批西川王建是不同人物。')
event('chen_ru_takes_quzhou','陈儒陷衢州',56,'光启三年十二月；具体日未载','衢州',
      '饶州刺史陈儒攻陷衢州。',
      [('陈儒','攻城者')])
event('feng_jingzhang_takes_qizhou','冯敬章陷蕲州',57,'光启三年十二月；具体日未载','蕲州',
      '上蔡军首领冯敬章攻陷蕲州。',
      [('冯敬章','攻城者')])
event('zhou_bao_dies','周宝卒于杭州',58,'光启三年十二月乙未','杭州',
      '周宝在杭州去世。',
      [('周宝','去世者')])
event('qian_duleng_changzhou','钱镠任杜稜常州制置使',59,'光启三年十二月；具体日未载','常州',
      '钱镠任杜稜为常州制置使。',
      [('钱镠','任命者'),('杜稜','受任者')])
event('qian_takes_runzhou','钱镠军攻取润州擒薛朗',59,'光启三年十二月丙申','润州',
      '钱镠命阮结等攻润州，丙申取城；刘浩逃走，薛朗被擒。',
      [('钱镠','遣军者'),('阮结','攻城将领'),('刘浩','出逃者'),('薛朗','被擒者')],
      note='“等”不据此推定具体每名将领参战。')

ledger=json.loads((YEAR/'paragraphs.json').read_text())
for n in range(49,60):
    assert used.get(n)
    ledger[n-1]['status']='reviewed';ledger[n-1]['event_keys']=used[n];ledger[n-1]['batch_key']=B['batch_key']
for n,note in {49:'闰月未注明闰几月，不自行补。',50:'“宗钅岁”“参谋乂李”“节茂贞”疑电子讹字，暂不据此创确定人物；田令孜所疑非已发生事实。',51:'袁袭对高霸反复的判断不作已叛事实；高暀次日被杀。',52:'审讯中的谋杀说法不作已实施事件；“桐入”疑讹。',53:'赵晖被无名部下杀，不归责张雄；降众遭张雄坑杀另记。',54:'李璠赴任受阻，不记为已实控淮南。',55:'王建肇与西川王建不混同。',59:'刘浩逃走、薛朗被擒，未见二人死亡。'}.items():ledger[n-1]['review']=note
payload=json.dumps(B,ensure_ascii=False,indent=2)+'\n'
audit=json.loads((P/'publication.json').read_text()) if (P/'publication.json').exists() else {}
status='published_verified' if audit.get('verified') and audit.get('batch_sha256')==hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(49,60):ledger[n-1]['status']=status
(P/'content-batch.json').write_text(payload)
(P/'reused-keys.json').write_text(json.dumps(sorted(reused),ensure_ascii=False,indent=2)+'\n')
(YEAR/'paragraphs.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
(P/'coverage.json').write_text(json.dumps(dict(book='资治通鉴',volume=257,year=887,primary_source_key=source,paragraphs=[Q[n]['id'] for n in range(49,60)],next_paragraph='zztj-v257-y0888-p001',coverage='卷257光启三年条第49—59段；本年与本卷本年条结束。',supplements=[],status=status),ensure_ascii=False,indent=2)+'\n')
print({k:len(v) for k,v in B.items() if isinstance(v,list)})
