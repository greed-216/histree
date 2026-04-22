ALTER TABLE public.person
  ADD COLUMN IF NOT EXISTS "references" JSONB DEFAULT '[]'::jsonb;

ALTER TABLE public.event
  ADD COLUMN IF NOT EXISTS "references" JSONB DEFAULT '[]'::jsonb;

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object(
    'title', '维基百科：管仲',
    'reference_type', 'encyclopedia',
    'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')
  ),
  jsonb_build_object(
    'title', '《史记·管晏列传》',
    'reference_type', 'primary',
    'note', '人物基础生平与评价的核心来源之一。'
  ),
  jsonb_build_object(
    'title', '《左传》相关篇目',
    'reference_type', 'primary',
    'note', '春秋齐国政治与会盟背景的重要来源。'
  )
) WHERE id = '11111111-1111-1111-1111-111111111001';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：齐桓公', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·齐太公世家》', 'reference_type', 'primary', 'note', '齐国君主谱系与霸业叙事的重要来源。'),
  jsonb_build_object('title', '《左传》相关篇目', 'reference_type', 'primary', 'note', '齐桓公会盟与尊王攘夷叙事的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111002';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：晋文公', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《左传》僖公相关篇目', 'reference_type', 'primary', 'note', '重耳流亡与城濮之战的重要来源。'),
  jsonb_build_object('title', '《史记·晋世家》', 'reference_type', 'primary', 'note', '晋国政治背景的重要参考。')
) WHERE id = '11111111-1111-1111-1111-111111111003';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：楚庄王', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《左传》宣公相关篇目', 'reference_type', 'primary', 'note', '楚庄王称霸、问鼎叙事的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111004';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：伍子胥', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·伍子胥列传》', 'reference_type', 'primary', 'note', '伍子胥生平与吴楚争霸的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111005';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：孙武', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·孙子吴起列传》', 'reference_type', 'primary', 'note', '孙武传统生平与兵学地位的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111006';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：勾践', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·越王勾践世家》', 'reference_type', 'primary', 'note', '吴越争霸与勾践复兴的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111007';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：商鞅', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·商君列传》', 'reference_type', 'primary', 'note', '商鞅生平与变法叙事的重要来源。'),
  jsonb_build_object('title', '维基百科：商鞅变法', 'reference_type', 'reference', 'url', 'https://zh.wikipedia.org/wiki/%E5%95%86%E9%9E%85%E5%8F%98%E6%B3%95')
) WHERE id = '11111111-1111-1111-1111-111111111008';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：秦孝公', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·秦本纪》', 'reference_type', 'primary', 'note', '秦孝公任用商鞅与秦国转折的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111009';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：苏秦', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·苏秦列传》', 'reference_type', 'primary', 'note', '合纵叙事的重要来源。'),
  jsonb_build_object('title', '《战国策》', 'reference_type', 'primary', 'note', '战国纵横活动的重要参考。')
) WHERE id = '11111111-1111-1111-1111-111111111010';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：张仪', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·张仪列传》', 'reference_type', 'primary', 'note', '连横叙事的重要来源。'),
  jsonb_build_object('title', '《战国策》', 'reference_type', 'primary', 'note', '战国外交活动的重要参考。')
) WHERE id = '11111111-1111-1111-1111-111111111011';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：廉颇', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·廉颇蔺相如列传》', 'reference_type', 'primary', 'note', '廉颇与蔺相如事迹的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111012';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：蔺相如', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·廉颇蔺相如列传》', 'reference_type', 'primary', 'note', '完璧归赵、渑池会等故事的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111013';

UPDATE public.person SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：白起', 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(name, ' ', '+')),
  jsonb_build_object('title', '《史记·白起王翦列传》', 'reference_type', 'primary', 'note', '白起战功与长平之战叙事的重要来源。')
) WHERE id = '11111111-1111-1111-1111-111111111014';

UPDATE public.event SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：' || title, 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(title, ' ', '+')),
  jsonb_build_object('title', '《左传》相关篇目', 'reference_type', 'primary', 'note', '春秋时期相关事件的重要原始叙事来源之一。'),
  jsonb_build_object('title', '《史记》相关列传/世家', 'reference_type', 'primary', 'note', '人物与事件背景的重要来源之一。')
) WHERE id IN (
  '22222222-2222-2222-2222-222222222001',
  '22222222-2222-2222-2222-222222222002',
  '22222222-2222-2222-2222-222222222003',
  '22222222-2222-2222-2222-222222222004',
  '22222222-2222-2222-2222-222222222005',
  '22222222-2222-2222-2222-222222222006'
);

UPDATE public.event SET "references" = jsonb_build_array(
  jsonb_build_object('title', '维基百科：' || title, 'reference_type', 'encyclopedia', 'url', 'https://zh.wikipedia.org/w/index.php?search=' || replace(title, ' ', '+')),
  jsonb_build_object('title', '《史记》相关列传/世家', 'reference_type', 'primary', 'note', '战国人物与事件背景的重要来源之一。'),
  jsonb_build_object('title', '《战国策》', 'reference_type', 'primary', 'note', '战国外交与政治叙事的重要参考。')
) WHERE id IN (
  '22222222-2222-2222-2222-222222222007',
  '22222222-2222-2222-2222-222222222008',
  '22222222-2222-2222-2222-222222222009',
  '22222222-2222-2222-2222-222222222010'
);
