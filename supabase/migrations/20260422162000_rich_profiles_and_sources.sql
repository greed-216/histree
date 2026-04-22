-- Add richer profile fields for the current person/event experience and lay
-- the source-aware foundation for future fact-level provenance.

ALTER TABLE public.person
  ADD COLUMN IF NOT EXISTS courtesy_name TEXT,
  ADD COLUMN IF NOT EXISTS aliases TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS faction TEXT,
  ADD COLUMN IF NOT EXISTS native_place TEXT,
  ADD COLUMN IF NOT EXISTS biography TEXT,
  ADD COLUMN IF NOT EXISTS historical_evaluation TEXT,
  ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS family JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS social_relations JSONB DEFAULT '[]'::jsonb;

ALTER TABLE public.event
  ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS phases JSONB DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS public.source (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('primary', 'reference', 'scholarship', 'digital', 'media')),
  author TEXT,
  edition TEXT,
  url TEXT,
  note TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.fact_claim (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_table TEXT NOT NULL,
  subject_id UUID NOT NULL,
  field_path TEXT NOT NULL,
  claim_text TEXT NOT NULL,
  source_id UUID REFERENCES public.source(id) ON DELETE SET NULL,
  citation TEXT,
  confidence NUMERIC(3, 2) CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  note TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_claim_subject ON public.fact_claim(subject_table, subject_id);
CREATE INDEX IF NOT EXISTS idx_fact_claim_source ON public.fact_claim(source_id);

ALTER TABLE public.source ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fact_claim ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read access on source" ON public.source;
DROP POLICY IF EXISTS "Allow admin write access on source" ON public.source;
CREATE POLICY "Allow public read access on source" ON public.source FOR SELECT USING (true);
CREATE POLICY "Allow admin write access on source" ON public.source FOR ALL USING (public.is_admin()) WITH CHECK (public.is_admin());

DROP POLICY IF EXISTS "Allow public read access on fact_claim" ON public.fact_claim;
DROP POLICY IF EXISTS "Allow admin write access on fact_claim" ON public.fact_claim;
CREATE POLICY "Allow public read access on fact_claim" ON public.fact_claim FOR SELECT USING (true);
CREATE POLICY "Allow admin write access on fact_claim" ON public.fact_claim FOR ALL USING (public.is_admin()) WITH CHECK (public.is_admin());

INSERT INTO public.source (id, title, source_type, author, edition, note)
VALUES
  ('66666666-6666-6666-6666-666666666001', '史记', 'primary', '司马迁', '中华书局点校本', '人物列传与世家为先秦人物、战国事件的重要基础来源。'),
  ('66666666-6666-6666-6666-666666666002', '左传', 'primary', NULL, '中华书局点校本', '春秋时期政治、战争、外交叙事的重要基础来源。'),
  ('66666666-6666-6666-6666-666666666003', '战国策', 'primary', NULL, '中华书局点校本', '战国纵横、外交、谋略叙事的重要基础来源。'),
  ('66666666-6666-6666-6666-666666666004', '资治通鉴', 'primary', '司马光', '中华书局点校本', '编年体通史，可作为事件时间线与因果链校核来源。')
ON CONFLICT (id) DO UPDATE SET
  title = EXCLUDED.title,
  source_type = EXCLUDED.source_type,
  author = EXCLUDED.author,
  edition = EXCLUDED.edition,
  note = EXCLUDED.note;

UPDATE public.person SET
  courtesy_name = NULL,
  aliases = ARRAY['管敬仲'],
  faction = '齐国',
  native_place = '颍上',
  biography = '管仲早年经商并从政，曾辅佐公子纠。齐桓公即位后，经鲍叔牙推荐重用管仲。管仲主持齐国改革，整顿行政、财政和军事，使齐国迅速增强国力，并协助齐桓公以尊王攘夷号召组织诸侯会盟。',
  historical_evaluation = '传统史学多将管仲视为春秋霸政与早期国家治理改革的代表人物。他的评价重点不只在个人谋略，更在制度整顿、财政组织和诸侯秩序建构。',
  tags = ARRAY['改革家', '齐国', '春秋霸政', '政治制度', '经济改革'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111002","name":"齐桓公","relation":"君臣","note":"辅佐齐桓公改革齐国并成就霸业。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111001';

UPDATE public.person SET
  aliases = ARRAY['小白'],
  faction = '齐国',
  native_place = '齐国',
  biography = '齐桓公名小白，齐国内乱后返国即位。他任用管仲整顿内政和军政，并以尊王攘夷为旗号会盟诸侯。葵丘会盟标志齐国霸业达到高峰，是春秋早期霸主政治的代表。',
  historical_evaluation = '齐桓公常被视为春秋五霸之首，其成就离不开管仲改革和齐国国力支撑。其政治影响在于以诸侯会盟重建周王室名义下的区域秩序。',
  tags = ARRAY['春秋五霸', '齐国', '霸主', '尊王攘夷'],
  family = '[{"name":"齐襄公","relation":"兄","note":"齐国内乱背景中的关键人物。"}]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111001","name":"管仲","relation":"君臣","note":"重用管仲主持改革。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111002';

UPDATE public.person SET
  aliases = ARRAY['重耳'],
  faction = '晋国',
  native_place = '晋国',
  biography = '晋文公名重耳，早年因晋国内乱长期流亡，周游列国。返晋即位后整顿内政，并在城濮之战中击败楚军，确立晋国在中原诸侯中的霸主地位。',
  historical_evaluation = '晋文公的历史形象结合了流亡经历、政治复归与军事胜利。其霸业代表春秋中期晋楚争霸格局的形成。',
  tags = ARRAY['春秋五霸', '晋国', '流亡', '晋楚争霸', '城濮之战'],
  family = '[]'::jsonb,
  social_relations = '[]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111003';

UPDATE public.person SET
  aliases = ARRAY['熊侣'],
  faction = '楚国',
  native_place = '楚国',
  biography = '楚庄王为楚国君主，早期隐忍观望，后励精图治，重整国政和军力。其北上问鼎象征楚国对中原秩序的挑战，也是楚国强盛的重要标志。',
  historical_evaluation = '楚庄王常被列入春秋霸主谱系。他的重要性在于展示南方强国进入中原政治结构后的冲击。',
  tags = ARRAY['楚国', '春秋五霸', '问鼎中原', '南方强国'],
  family = '[]'::jsonb,
  social_relations = '[]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111004';

UPDATE public.person SET
  faction = '吴国',
  native_place = '楚国',
  biography = '伍子胥本为楚人，因家族遭难出奔入吴，后辅佐吴国强盛。他参与吴国伐楚战略，吴破郢之战中扮演重要角色，成为春秋末期吴楚争霸的关键人物。',
  historical_evaluation = '伍子胥的形象兼具复仇叙事、亡命政治和军事谋略。他连接了楚国内部政治、吴国崛起与吴越争霸等多条历史线索。',
  tags = ARRAY['吴国', '楚国', '复仇', '军事', '吴楚争霸'],
  family = '[{"name":"伍奢","relation":"父","note":"楚国大夫，伍子胥出奔背景中的关键人物。"}]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111006","name":"孙武","relation":"同僚","note":"同为吴国军事行动的重要人物。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111005';

UPDATE public.person SET
  aliases = ARRAY['孙子'],
  faction = '吴国',
  native_place = '齐国',
  biography = '孙武相传出身齐国，后入吴，以兵法见用于吴王。传统叙事中，他与吴国军事改革、伐楚战争相联系，并被归为兵家代表人物。',
  historical_evaluation = '孙武的历史评价主要来自兵学传统。《孙子兵法》所体现的战略思想使其影响远超具体生平事迹。',
  tags = ARRAY['兵家', '吴国', '孙子兵法', '军事思想'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111005","name":"伍子胥","relation":"同僚","note":"传统叙事中共同服务吴国。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111006';

UPDATE public.person SET
  faction = '越国',
  native_place = '越国',
  biography = '勾践为越国君主。吴越争霸中越国一度失败，勾践长期蓄力、整顿国政，最终灭吴。其故事后来形成卧薪尝胆的强烈历史记忆。',
  historical_evaluation = '勾践常被作为忍辱复兴和长期战略的代表。其历史意义在于春秋末期吴越力量更替与区域霸权变化。',
  tags = ARRAY['越国', '吴越争霸', '卧薪尝胆', '霸主'],
  family = '[]'::jsonb,
  social_relations = '[]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111007';

UPDATE public.person SET
  aliases = ARRAY['公孙鞅', '卫鞅'],
  faction = '秦国',
  native_place = '卫国',
  biography = '商鞅本为卫人，入秦后得到秦孝公重用，主持两次变法。变法推行军功爵、县制、连坐、土地制度调整等措施，改变秦国社会组织和国家能力。',
  historical_evaluation = '商鞅是战国法家政治实践的代表人物。其评价长期存在张力：一方面被视为秦国强盛基础，另一方面也因严刑峻法受到批评。',
  tags = ARRAY['法家', '秦国', '变法', '军功爵', '县制'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111009","name":"秦孝公","relation":"君臣","note":"受秦孝公支持主持变法。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111008';

UPDATE public.person SET
  faction = '秦国',
  native_place = '秦国',
  biography = '秦孝公即位后求贤图强，任用商鞅推行变法。其统治时期是秦国由西方强国走向战国强权的重要转折。',
  historical_evaluation = '秦孝公的关键贡献在于为制度改革提供政治支持。秦国后续扩张与商鞅变法密不可分。',
  tags = ARRAY['秦国', '变法', '君主', '战国'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111008","name":"商鞅","relation":"君臣","note":"支持商鞅变法。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111009';

UPDATE public.person SET
  faction = '六国',
  native_place = '洛阳',
  biography = '苏秦为战国纵横家代表人物，传统叙事中以合纵策略游说六国抗秦。他的活动体现战国外交联盟和强秦压力下的多国博弈。',
  historical_evaluation = '苏秦形象代表纵横家以外交策略影响国际格局的一面。其事迹材料复杂，后续需要用来源和争议标记加以区分。',
  tags = ARRAY['纵横家', '合纵', '外交', '战国'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111011","name":"张仪","relation":"对手","note":"合纵与连横构成战国外交叙事中的对照。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111010';

UPDATE public.person SET
  faction = '秦国',
  native_place = '魏国',
  biography = '张仪为战国纵横家代表人物，服务秦国，以连横策略瓦解六国合纵。其活动体现秦国通过外交分化对手、扩大优势的政治手段。',
  historical_evaluation = '张仪常作为连横策略的代表，与苏秦合纵形成对照。其重要性在于展现战国外交与军事扩张之间的互动。',
  tags = ARRAY['纵横家', '连横', '秦国', '外交'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111010","name":"苏秦","relation":"对手","note":"合纵与连横构成战国外交叙事中的对照。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111011';

UPDATE public.person SET
  faction = '赵国',
  native_place = '赵国',
  biography = '廉颇为赵国名将，长期参与赵国军事防御。长平之战前期，廉颇采取坚守策略抵御秦军，后被赵括替换，战局发生重大变化。',
  historical_evaluation = '廉颇代表战国后期赵国军事力量和老成持重的防御策略。与蔺相如将相和的故事也使其成为政治伦理叙事中的重要人物。',
  tags = ARRAY['赵国', '名将', '长平之战', '将相和'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111013","name":"蔺相如","relation":"同僚","note":"将相和故事中的另一核心人物。"},{"person_id":"11111111-1111-1111-1111-111111111014","name":"白起","relation":"敌对阵营","note":"秦赵军事对抗中的两方代表。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111012';

UPDATE public.person SET
  faction = '赵国',
  native_place = '赵国',
  biography = '蔺相如为赵国政治人物，以完璧归赵和渑池会见等外交故事著称。传统叙事中，他能在强秦压力下维护赵国尊严，并与廉颇形成将相和关系。',
  historical_evaluation = '蔺相如代表战国外交场景中的机敏、胆识与礼制政治。他的形象常用于说明外交谈判与国内政治协调。',
  tags = ARRAY['赵国', '外交', '完璧归赵', '将相和'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111012","name":"廉颇","relation":"同僚","note":"将相和故事中的另一核心人物。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111013';

UPDATE public.person SET
  faction = '秦国',
  native_place = '秦国',
  biography = '白起为秦国名将，参与战国后期多次重大战争。长平之战中，白起指挥秦军击败赵军，使秦国在统一进程中取得决定性优势。',
  historical_evaluation = '白起通常被评价为战国最重要的军事统帅之一。他的功绩与战争残酷性并存，是秦国军事扩张能力的集中体现。',
  tags = ARRAY['秦国', '名将', '长平之战', '军事扩张'],
  family = '[]'::jsonb,
  social_relations = '[{"person_id":"11111111-1111-1111-1111-111111111012","name":"廉颇","relation":"敌对阵营","note":"秦赵军事对抗中的两方代表。"}]'::jsonb
WHERE id = '11111111-1111-1111-1111-111111111014';

UPDATE public.event SET
  tags = ARRAY['改革', '齐国', '春秋霸政', '制度'],
  phases = '[{"title":"任用管仲","description":"齐桓公重用管仲，为改革提供政治条件。"},{"title":"整顿内政与军政","description":"改革行政、经济和军事组织，增强齐国国力。"},{"title":"霸业形成","description":"改革成果支撑齐桓公会盟诸侯。"}]'::jsonb
WHERE id = '22222222-2222-2222-2222-222222222001';

UPDATE public.event SET
  tags = ARRAY['会盟', '齐国', '尊王攘夷', '诸侯秩序'],
  phases = '[{"title":"诸侯会盟","description":"齐桓公召集诸侯形成政治秩序。"},{"title":"霸业确认","description":"葵丘会盟标志齐国霸业成熟。"}]'::jsonb
WHERE id = '22222222-2222-2222-2222-222222222002';

UPDATE public.event SET
  tags = ARRAY['战争', '晋国', '楚国', '霸权', '晋楚争霸'],
  phases = '[{"title":"晋楚对峙","description":"晋楚在中原秩序中形成霸权竞争。"},{"title":"城濮决战","description":"晋军击败楚军。"},{"title":"晋国称霸","description":"晋文公霸主地位得到确认。"}]'::jsonb
WHERE id = '22222222-2222-2222-2222-222222222003';

INSERT INTO public.fact_claim (id, subject_table, subject_id, field_path, claim_text, source_id, citation, confidence, note)
VALUES
  ('77777777-7777-7777-7777-777777777001', 'person', '11111111-1111-1111-1111-111111111001', 'biography', '管仲辅佐齐桓公改革齐国并成就霸业。', '66666666-6666-6666-6666-666666666001', '史记·管晏列传', 0.90, 'MVP 阶段先记录篇目级引用，后续补页码和版本信息。'),
  ('77777777-7777-7777-7777-777777777002', 'person', '11111111-1111-1111-1111-111111111008', 'biography', '商鞅在秦孝公支持下主持秦国变法。', '66666666-6666-6666-6666-666666666001', '史记·商君列传', 0.90, NULL),
  ('77777777-7777-7777-7777-777777777003', 'event', '22222222-2222-2222-2222-222222222003', 'description', '城濮之战是晋楚争霸中的关键战役。', '66666666-6666-6666-6666-666666666002', '左传·僖公二十八年', 0.85, NULL),
  ('77777777-7777-7777-7777-777777777004', 'event', '22222222-2222-2222-2222-222222222008', 'description', '合纵连横体现战国诸国与秦国之间的外交博弈。', '66666666-6666-6666-6666-666666666003', '战国策', 0.75, '具体篇章和版本需要后续细化。')
ON CONFLICT (id) DO UPDATE SET
  subject_table = EXCLUDED.subject_table,
  subject_id = EXCLUDED.subject_id,
  field_path = EXCLUDED.field_path,
  claim_text = EXCLUDED.claim_text,
  source_id = EXCLUDED.source_id,
  citation = EXCLUDED.citation,
  confidence = EXCLUDED.confidence,
  note = EXCLUDED.note;
