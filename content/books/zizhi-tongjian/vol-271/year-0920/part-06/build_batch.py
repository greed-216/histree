"""Curate consecutive Tongjian volume 271, year 920, paragraphs 22–25."""
import hashlib
import json
import os
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = next(x for x in P.parents if (x / 'scripts/validate-content-batch.py').exists())
YEAR = P.parent
ledger = json.loads((YEAR / 'paragraphs.json').read_text())
Q = {int(row['id'][-3:]): row for row in ledger}
assert list(Q) == list(range(1, 27))
specs = [
    ('tongjian-271-920-yearend', P / 'sources/library/tongjian-271-920-yearend', '505908a2', '司马光等'),
]
sources = {key: path for key, path, _, _ in specs}
main_sources = [key for key, _, _, _ in specs[:1]]
B = {'format_version': 1, 'batch_key': 'zztj-v271-y0920-p022-p025',
     **{k: [] for k in ('people', 'events', 'person_events', 'person_relationships', 'sources', 'claims', 'topics')}}
manifest = []
for key, path, commit, author in specs:
    record = json.loads((path / 'paragraph.json').read_text())
    url = 'https://github.com/greed-216/histree/blob/' + commit + '/' + str((path / 'source.txt').relative_to(ROOT))
    B['sources'].append(dict(key=key, title=record['book'] + '·' + record['section_title'],
                             source_type='primary', author=author, edition='选定TXT逐字导出；电子本，纸本及异文待核。',
                             url=url, note=record['citation']))
    manifest.append(dict(key=key, file=os.path.relpath(path / 'source.txt', P / 'sources'),
                         sha256=hashlib.sha256((path / 'source.txt').read_bytes()).hexdigest(),
                         url=url, paragraph_id=record['id'], upstream_locator=record['locator'],
                         transformation='CLI逐字导出TXT，保留底本原字；繁简仅用于实体匹配。'))
(P / 'sources/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
lines = (ROOT / 'resources/derived/tongjian/271.txt').read_text().splitlines()
for n in range(22, 26):
    assert Q[n]['text'] == lines[Q[n]['source_line'] - 1]
registry = {}
for path in sorted((ROOT / 'content').rglob('content-batch.json')):
    if path.resolve() == (P / 'content-batch.json').resolve():
        continue
    for row in json.loads(path.read_text())['people']:
        old = registry.get(row['name'])
        if old:
            assert old['key'] == row['key'], (row['name'], path)
        registry[row['name']] = row
people, used, reused, supplements = {}, {}, set(), []

def choose_source(n, quote):
    for key in main_sources:
        if quote in (sources[key] / 'source.txt').read_text():
            return key
    raise AssertionError(('missing primary quote', n, quote))

def claim(table, key, field, value, n, quote, note, source=None, relation='adds'):
    source = source or choose_source(n, quote)
    record = json.loads((sources[source] / 'paragraph.json').read_text())
    assert quote in (sources[source] / 'source.txt').read_text(), (source, quote)
    if source in main_sources:
        assert quote in Q[n]['text'], (n, quote)
        citation = f'卷271·贞明六年（920）·{Q[n]["id"]}·原文件第{Q[n]["source_line"]}行'
    else:
        citation = record['citation']
    ck = f'claim_zztj_271_0920_06_{len(B["claims"])+1:04d}'
    B['claims'].append(dict(key=ck, subject_table=table, subject_key=key, field_path=field,
                            claim_text=value, source_key=source, citation=citation,
                            note=f'原文：{quote}；核对说明：{note}', status='draft'))
    if source not in main_sources:
        supplements.append(dict(claim_key=ck, source_book=record['book'], primary_paragraph_id=Q[n]['id'],
                                subject_key=key, relation=relation))

def person(name, n, role, quote):
    name = {'闽王审知':'王审知','审知':'王审知','延彬':'王延彬','楚王殷':'马殷','传琇':'钱传琇','王德明':'张文礼','德明':'张文礼','赵王镕':'王镕','越王镕':'王镕','镕':'王镕','李霭':'李蔼','李宏规':'李弘规','岐王':'李茂贞','昭祚':'王昭祚','守文':'刘守文','王建及':'李建及','温昭图':'温韬','溫昭圖':'温韬','蜀主':'王宗衍','硃友谦':'朱友谦','吴宣王':'杨隆演','梁帝':'朱友贞','汉主岩':'刘岩','晋王':'李存勖',
            '李存审':'符存审','存审':'符存审','宗播':'许存',
            '王宗播':'许存','太后':'徐贤妃','太妃':'徐淑妃',
            '吴越王镠':'钱镠','镠':'钱镠','传瓘':'钱传瓘','吴王':'杨隆演',
            '徐知诰':'李昪','徐知誥':'李昪','知诰':'李昪',
            '濛':'杨濛','溥':'杨溥','浔':'杨浔','澈':'杨澈','继明':'杨继明',
            '郑氏':'钱镠宠姬郑氏','王氏':'杨溥母王氏','全师朗':'王宗朗','王瓚':'王瓒','石敬塘':'石敬瑭','敬瑭':'石敬瑭','石敬瑭':'石敬瑭',
            '敬塘':'石敬瑭','李绍荣':'元行钦','李紹榮':'元行钦'}.get(name, name)
    if name in people:
        return people[name]
    if name in registry:
        row = dict(registry[name], status='draft')
        reused.add(row['key'])
    else:
        row = dict(key='person_' + name, name=name,
                   aliases={'隐彦谦':['隱彥謙'],'钱传琇':['錢傳琇']}.get(name, []), era='五代十国',
                   birth_year=None, death_year=None,
                   description=f'《资治通鉴》卷271贞明六年条所见人物：{name}。',
                   biography=None, status='draft')
    B['people'].append(row)
    people[name] = row['key']
    claim('person', row['key'], 'description', f'本段记{name}：{role}。', n, quote,
          '与既有规范名合并；繁简或异体仅用于实体匹配，引用保留原字。')
    return row['key']

def event(code, title, n, quote, actors, when='920年本段条；确日未载', note='', year=920, place='五代十国'):
    assert quote in Q[n]['text'], (n, quote)
    key = 'event_zztj_271_0920_' + code
    row = dict(key=key, title=title, start_year=year, end_year=year,
               time_original=when, dynasty='五代十国', description=title + '。', phases=[],
               location_name=place, location_modern_name=None, location_lat=None, location_lng=None,
               location_precision='unknown', location_note='仅保留史载地名；未核坐标。', status='draft')
    B['events'].append(row)
    used.setdefault(n, []).append(key)
    claim('event', key, 'description', row['description'], n, quote, note or '按原文动作分录；不外推原因与结果。')
    claim('event', key, 'time_original', when, n, quote,
          '按主书本段纪时；追叙或他书记载另作说明，不自行换算公历日期。')
    for name, role in actors:
        pk = person(name, n, role, quote)
        edge = 'participation_zztj_271_0920_' + code + '_' + pk
        B['person_events'].append(dict(key=edge, person_key=pk, event_key=key, role=role, status='draft'))
        claim('person_event', edge, 'role', f'{name}：{role}。', n, quote,
              '参与身份依据本句；人名沿用已有主体，原文不改字。')
    return key

event('jinling_city_completed','吴金陵城建成',22,
      '吴金陵城成，',[],when='920年年末本段；确月、日未载',place='金陵',
      note='“城成”记竣工，未反推开工年月或城垣规模。')
event('xu_wen_burns_jinling_accounts','隐彦谦呈金陵费用册籍，徐温焚之',22,
      '隐彦谦上费用册籍，徐温曰：“吾既任公，不复会计！”悉焚之。',
      [('隐彦谦','呈金陵工程费用册籍者'),('徐温','称信任隐彦谦而焚费用册籍者')],
      when='920年金陵城成后本段；确日未载',place='金陵',
      note='原文不说明隐彦谦具体官职或财务数额，不杜撰职衔、支出。')

event('wang_yanbin_given_pinglu_title','王审知承制加王延彬领平卢节度使',23,
      '初，闽王审知承制加其从子泉州刺史延彬领平卢节度使。',
      [('闽王审知','承制加从子领平卢节度使者'),('延彬','泉州刺史、加领平卢节度使的王审知从子')],
      when='闽王审知时期追叙；确年未载',year=None,place='泉州、平卢',
      note='“领”保留职衔，不据此说王延彬移赴山东平卢实治。')
nephew=person('延彬',23,'王审知之从子','初，闽王审知承制加其从子泉州刺史延彬领平卢节度使。')
uncle=person('王审知',23,'王延彬之叔伯','初，闽王审知承制加其从子泉州刺史延彬领平卢节度使。')
rk='relationship_zztj_271_0920_wang_yanbin_nephew_of_wang_shenzhi'
B['person_relationships'].append(dict(key=rk,person_a_key=nephew,person_b_key=uncle,
    relation_type='侄子',description='王延彬是王审知的侄子。',status='draft'))
claim('person_relationship',rk,'description','王延彬是王审知的侄子。',23,
      '其从子泉州刺史延彬','“从子”按侄子记录；未据此指定父亲姓名或叔伯长幼。')
claim('person','person_王延彬','description','王延彬治泉州十七年，主书称吏民安之。',23,
      '延彬治泉州十七年，吏民安之。',
      '十七年是主书记任治时长，未反推任职开始年份；吏民评价按原文。')
event('hao_yuan_calls_deer_and_fungus_royal_omens','僧浩源称白鹿紫芝为王者符，王延彬因之骄纵',23,
      '会得白鹿及紫芝，僧浩源以为王者之符，延彬由是骄纵，',
      [('浩源','将白鹿紫芝解释为王者符的僧人'),('延彬','听此解释而骄纵者')],
      when='闽王延彬治泉州时期追叙；确年未载',year=None,place='泉州',
      note='符瑞为浩源的解释，未作为可证的王者预兆；也未推白鹿紫芝现代鉴定。')
event('wang_yanbin_secretly_seeks_quanzhou_title','王延彬密遣海使入贡，请为泉州节度使',23,
      '密遣使浮海入贡，求为泉州节度使。',
      [('延彬','秘密遣使海路入贡并请泉州节度使者')],
      when='王延彬治泉州时期追叙；确年未载',year=None,place='泉州、海路',
      note='主书此句未点名入贡受方，保留入贡事实，不擅补梁廷授命或正式任官。')
event('wang_shenzhi_kills_hao_yuan_dismisses_yanbin','王审知诛浩源及其党，黜王延彬',23,
      '事觉，审知诛浩源及其党，黜延彬归私第。',
      [('王审知','事觉后诛浩源并黜从子者'),('浩源','事觉后被诛者'),('延彬','被黜归私第者')],
      when='王延彬密遣贡使事觉后；确年、月、日未载',year=None,place='闽、泉州',
      note='全段以初起追叙，后续无独立确年；未将浩源被诛与王延彬归私第误记同等刑罚。')

event('southern_han_sends_friendly_mission_to_shu','汉主刘岩遣使通好于蜀',24,
      '汉主岩遣使通好于蜀。',[('汉主岩','向蜀遣使通好的汉主')],
      when='920年年末本段；确月、日未载',place='汉、蜀',
      note='通好仅证使节往来，不推结盟条约或已订婚。')

event('qian_liu_seeks_chu_marriage_for_chuanxiu','钱镠为钱传琇向楚求婚，马殷允之',25,
      '吴越王镠遣使为其子传琇求婚于楚，楚王殷许之。',
      [('吴越王镠','为子钱传琇遣使向楚求婚者'),('传琇','求婚对象为楚的吴越王之子'),('楚王殷','允吴越求婚请求的楚王')],
      when='920年年末本段；确月、日未载',place='吴越、楚',
      note='“许之”是允请求，未见已迎娶或楚方女子姓名，不建已成婚配偶关系。')
father=person('钱镠',25,'钱传琇之父','吴越王镠遣使为其子传琇求婚于楚，楚王殷许之。')
son=person('传琇',25,'钱镠之子','吴越王镠遣使为其子传琇求婚于楚，楚王殷许之。')
rk='relationship_zztj_271_0920_qian_liu_father_of_qian_chuanxiu'
B['person_relationships'].append(dict(key=rk,person_a_key=father,person_b_key=son,
    relation_type='父亲',description='钱镠是钱传琇的父亲。',status='draft'))
claim('person_relationship',rk,'description','钱镠是钱传琇的父亲。',25,
      '吴越王镠遣使为其子传琇求婚于楚，','“其子”明确父子；未从求婚建立未名女方实体。')

payload = json.dumps(B, ensure_ascii=False, indent=2) + '\n'
audit = json.loads((P / 'publication.json').read_text()) if (P / 'publication.json').exists() else {}
status = 'published_verified' if audit.get('verified') and audit.get('batch_sha256') == hashlib.sha256(payload.encode()).hexdigest() else 'reviewed'
for n in range(22, 26):
    ledger[n-1].update(event_keys=used[n], batch_key=B['batch_key'], status=status,
                       review='卷271贞明六年第22—25正文段；金陵城成、闽王延彬追叙、汉蜀通好及吴越楚求婚。')
assert Q[26]['text']=='◎' and Q[26]['source_line']==41
ledger[25].update(kind='separator',event_keys=[],batch_key=None,
    status='excluded_non_body_verified' if status=='published_verified' else 'reviewed_non_body',
    review='原文件第41行为◎年界分隔符，后接第42行龙德元年标题；不是史事正文，不生成事件或事实引用。')
(P / 'content-batch.json').write_text(payload)
(P / 'reused-keys.json').write_text(json.dumps(sorted(reused), ensure_ascii=False, indent=2) + '\n')
(YEAR / 'paragraphs.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n')
(P / 'coverage.json').write_text(json.dumps(dict(book='资治通鉴', volume=271, year=920,
    primary_source_key=main_sources[0], primary_source_keys=main_sources,
    paragraphs=[Q[n]['id'] for n in range(22, 26)], next_paragraph='zztj-v271-y0921-p001',
    excluded_non_body=[dict(paragraph_id=Q[26]['id'],source_line=41,text='◎',reason='年界分隔符，非正文；保留稳定账本ID和原文定位。')],
    coverage='卷271贞明六年第22—25正文段；年末四段处理，原账本第26项仅为年界分隔符。',
    supplements=supplements, reviewed_questions=[
      {'paragraph_id':Q[22]['id'],'note':'金陵竣工及徐温焚费用册籍有原文；未记隐彦谦官职与具体费用。'},
      {'paragraph_id':Q[23]['id'],'note':'全段初起追叙、无独立确年，不硬定920；王延彬为王审知从子，长幼及父名未载。僧浩源符瑞解释是当事人主张。'},
      {'paragraph_id':Q[24]['id'],'note':'汉使通好蜀仅录外交往来，不推条约或联盟。'},
      {'paragraph_id':Q[25]['id'],'note':'楚许吴越求婚未说明完成婚礼或女方姓名；父子关系有其子明文。'},
      {'paragraph_id':Q[26]['id'],'note':'◎为年界分隔符；从正文范围排除但保留原账本ID，全年审计按25个正文段加1个结构项计算。'}
    ]),ensure_ascii=False,indent=2)+'\n')
print({k: len(v) for k, v in B.items() if isinstance(v, list)})
