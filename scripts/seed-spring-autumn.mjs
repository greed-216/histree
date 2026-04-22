import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(new URL('../apps/api/package.json', import.meta.url));
const { createClient } = require('@supabase/supabase-js');

function loadEnv(path) {
  const env = {};
  const raw = readFileSync(path, 'utf8');

  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const index = trimmed.indexOf('=');
    if (index === -1) continue;
    env[trimmed.slice(0, index)] = trimmed.slice(index + 1);
  }

  return env;
}

const env = {
  ...loadEnv('apps/api/.env'),
  ...process.env,
};

const supabaseUrl = env.SUPABASE_URL;
const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !serviceRoleKey) {
  throw new Error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY.');
}

const supabase = createClient(supabaseUrl, serviceRoleKey, {
  auth: { persistSession: false },
});

const people = [
  { id: '11111111-1111-1111-1111-111111111001', name: '管仲', era: '春秋', birth_year: -723, death_year: -645, description: '齐国名相，辅佐齐桓公推行改革，使齐国成为春秋首霸。' },
  { id: '11111111-1111-1111-1111-111111111002', name: '齐桓公', era: '春秋', death_year: -643, description: '姜姓齐国君主，任用管仲改革内政，打出尊王攘夷旗号，会盟诸侯。' },
  { id: '11111111-1111-1111-1111-111111111003', name: '晋文公', era: '春秋', birth_year: -697, death_year: -628, description: '晋国君主，流亡十九年后归国即位，在城濮之战后成为春秋霸主之一。' },
  { id: '11111111-1111-1111-1111-111111111004', name: '楚庄王', era: '春秋', death_year: -591, description: '楚国君主，励精图治，问鼎中原，是春秋时期南方强国崛起的代表人物。' },
  { id: '11111111-1111-1111-1111-111111111005', name: '伍子胥', era: '春秋', death_year: -484, description: '楚人入吴，辅佐吴王阖闾强吴伐楚，是吴楚争霸中的关键人物。' },
  { id: '11111111-1111-1111-1111-111111111006', name: '孙武', era: '春秋', description: '兵家代表人物，相传著有《孙子兵法》，曾助吴国训练军队。' },
  { id: '11111111-1111-1111-1111-111111111007', name: '勾践', era: '春秋', death_year: -465, description: '越国君主，卧薪尝胆，最终灭吴，成为春秋末期霸主之一。' },
  { id: '11111111-1111-1111-1111-111111111008', name: '商鞅', era: '战国', birth_year: -390, death_year: -338, description: '法家重要人物，在秦国主持变法，奠定秦国强盛基础。' },
  { id: '11111111-1111-1111-1111-111111111009', name: '秦孝公', era: '战国', birth_year: -381, death_year: -338, description: '秦国君主，任用商鞅变法，使秦国迅速崛起。' },
  { id: '11111111-1111-1111-1111-111111111010', name: '苏秦', era: '战国', death_year: -284, description: '纵横家代表人物，以合纵策略游说六国抗秦。' },
  { id: '11111111-1111-1111-1111-111111111011', name: '张仪', era: '战国', death_year: -309, description: '纵横家代表人物，服务秦国，以连横策略瓦解合纵。' },
  { id: '11111111-1111-1111-1111-111111111012', name: '廉颇', era: '战国', death_year: -243, description: '赵国名将，长平之战前曾坚守防线，与蔺相如并称。' },
  { id: '11111111-1111-1111-1111-111111111013', name: '蔺相如', era: '战国', description: '赵国政治家，以完璧归赵、渑池会见闻名，与廉颇将相和。' },
  { id: '11111111-1111-1111-1111-111111111014', name: '白起', era: '战国', death_year: -257, description: '秦国名将，战国后期秦军扩张中的核心军事人物。' },
];

const events = [
  { id: '22222222-2222-2222-2222-222222222001', title: '管仲改革', start_year: -685, end_year: -645, dynasty: '春秋', description: '管仲辅佐齐桓公整顿行政、发展经济、组织军政，使齐国获得争霸实力。', impact_level: 4, location_name: '临淄（今山东淄博）', location_lat: 36.82, location_lng: 118.30 },
  { id: '22222222-2222-2222-2222-222222222002', title: '葵丘会盟', start_year: -651, end_year: -651, dynasty: '春秋', description: '齐桓公召集诸侯会盟，尊王攘夷秩序达到高峰，标志齐国霸业成熟。', impact_level: 4, location_name: '葵丘（今河南民权附近）', location_lat: 34.65, location_lng: 115.13 },
  { id: '22222222-2222-2222-2222-222222222003', title: '城濮之战', start_year: -632, end_year: -632, dynasty: '春秋', description: '晋楚争霸中的关键战役，晋文公击败楚军，确立晋国霸主地位。', impact_level: 5, location_name: '城濮（今山东鄄城一带）', location_lat: 35.56, location_lng: 115.50 },
  { id: '22222222-2222-2222-2222-222222222004', title: '楚庄王问鼎', start_year: -606, end_year: -606, dynasty: '春秋', description: '楚庄王北上洛邑附近问周鼎轻重，象征楚国挑战中原秩序的野心。', impact_level: 3, location_name: '洛邑（今河南洛阳）', location_lat: 34.62, location_lng: 112.45 },
  { id: '22222222-2222-2222-2222-222222222005', title: '吴破郢之战', start_year: -506, end_year: -506, dynasty: '春秋', description: '吴国在伍子胥、孙武等人辅佐下攻入楚都郢，重创楚国。', impact_level: 5, location_name: '郢都（今湖北荆州一带）', location_lat: 30.35, location_lng: 112.19 },
  { id: '22222222-2222-2222-2222-222222222006', title: '越灭吴', start_year: -473, end_year: -473, dynasty: '春秋', description: '越王勾践长期蓄力后灭吴，春秋末期吴越争霸落幕。', impact_level: 5, location_name: '姑苏（今江苏苏州）', location_lat: 31.30, location_lng: 120.59 },
  { id: '22222222-2222-2222-2222-222222222007', title: '商鞅变法', start_year: -356, end_year: -350, dynasty: '战国', description: '商鞅在秦孝公支持下推行军功爵、县制、什伍连坐和土地制度改革，深刻改变秦国。', impact_level: 5, location_name: '栎阳/咸阳（今陕西一带）', location_lat: 34.34, location_lng: 108.94 },
  { id: '22222222-2222-2222-2222-222222222008', title: '合纵连横', start_year: -334, end_year: -318, dynasty: '战国', description: '苏秦合纵与张仪连横代表战国外交博弈，六国与秦国之间的联盟格局频繁变化。', impact_level: 4, location_name: '战国诸国', location_lat: 34.75, location_lng: 113.62 },
  { id: '22222222-2222-2222-2222-222222222009', title: '完璧归赵', start_year: -283, end_year: -283, dynasty: '战国', description: '蔺相如出使秦国，维护赵国利益，成为战国外交故事的代表。', impact_level: 3, location_name: '秦赵之间', location_lat: 34.34, location_lng: 108.94 },
  { id: '22222222-2222-2222-2222-222222222010', title: '长平之战', start_year: -260, end_year: -260, dynasty: '战国', description: '秦赵之间的大规模决战，赵军惨败，秦统一进程获得决定性优势。', impact_level: 5, location_name: '长平（今山西高平）', location_lat: 35.80, location_lng: 112.92 },
];

const relationships = [
  { id: '33333333-3333-3333-3333-333333333001', person_a: people[0].id, person_b: people[1].id, relation_type: 'minister', description: '管仲辅佐齐桓公完成齐国改革与霸业。' },
  { id: '33333333-3333-3333-3333-333333333002', person_a: people[4].id, person_b: people[5].id, relation_type: 'ally', description: '伍子胥与孙武共同服务吴国，是吴破楚的重要支撑。' },
  { id: '33333333-3333-3333-3333-333333333003', person_a: people[7].id, person_b: people[8].id, relation_type: 'minister', description: '商鞅受秦孝公重用，在秦国推行变法。' },
  { id: '33333333-3333-3333-3333-333333333004', person_a: people[9].id, person_b: people[10].id, relation_type: 'rival', description: '苏秦合纵与张仪连横代表相互对抗的外交路线。' },
  { id: '33333333-3333-3333-3333-333333333005', person_a: people[11].id, person_b: people[12].id, relation_type: 'ally', description: '廉颇与蔺相如由相争到相重，形成将相和。' },
  { id: '33333333-3333-3333-3333-333333333006', person_a: people[11].id, person_b: people[13].id, relation_type: 'enemy', description: '廉颇、白起分别代表赵秦军事集团，在秦赵对抗中处于敌对阵营。' },
];

const personEvents = [
  ['44444444-4444-4444-4444-444444444001', 0, 0, 'reformer'],
  ['44444444-4444-4444-4444-444444444002', 1, 0, 'ruler'],
  ['44444444-4444-4444-4444-444444444003', 1, 1, 'hegemon'],
  ['44444444-4444-4444-4444-444444444004', 2, 2, 'commander'],
  ['44444444-4444-4444-4444-444444444005', 3, 3, 'ruler'],
  ['44444444-4444-4444-4444-444444444006', 4, 4, 'strategist'],
  ['44444444-4444-4444-4444-444444444007', 5, 4, 'strategist'],
  ['44444444-4444-4444-4444-444444444008', 6, 5, 'ruler'],
  ['44444444-4444-4444-4444-444444444009', 7, 6, 'reformer'],
  ['44444444-4444-4444-4444-444444444010', 8, 6, 'patron'],
  ['44444444-4444-4444-4444-444444444011', 9, 7, 'diplomat'],
  ['44444444-4444-4444-4444-444444444012', 10, 7, 'diplomat'],
  ['44444444-4444-4444-4444-444444444013', 12, 8, 'envoy'],
  ['44444444-4444-4444-4444-444444444014', 11, 9, 'defender'],
  ['44444444-4444-4444-4444-444444444015', 13, 9, 'commander'],
].map(([id, personIndex, eventIndex, role]) => ({
  id,
  person_id: people[personIndex].id,
  event_id: events[eventIndex].id,
  role,
}));

const causalities = [
  { id: '55555555-5555-5555-5555-555555555001', cause_event_id: events[0].id, effect_event_id: events[1].id, description: '齐国改革增强国力，推动齐桓公会盟诸侯。' },
  { id: '55555555-5555-5555-5555-555555555002', cause_event_id: events[1].id, effect_event_id: events[2].id, description: '齐国霸业之后，晋楚争霸成为中原秩序的核心矛盾。' },
  { id: '55555555-5555-5555-5555-555555555003', cause_event_id: events[4].id, effect_event_id: events[5].id, description: '吴国强盛并重创楚国后，也激化了吴越争霸，最终越灭吴。' },
  { id: '55555555-5555-5555-5555-555555555004', cause_event_id: events[6].id, effect_event_id: events[7].id, description: '秦国变法后实力增强，引发六国合纵与秦国连横的外交对抗。' },
  { id: '55555555-5555-5555-5555-555555555005', cause_event_id: events[7].id, effect_event_id: events[9].id, description: '合纵连横失败与秦赵力量变化，最终走向长平决战。' },
];

async function upsert(table, rows) {
  const { error } = await supabase.from(table).upsert(rows, { onConflict: 'id' });
  if (error) throw new Error(`${table}: ${error.message}`);
  console.log(`seeded ${rows.length} rows into ${table}`);
}

async function upsertEvents(rows) {
  const { error } = await supabase.from('event').upsert(rows, { onConflict: 'id' });

  if (!error) {
    console.log(`seeded ${rows.length} rows into event`);
    return;
  }

  if (!error.message.includes('location_')) {
    throw new Error(`event: ${error.message}`);
  }

  const compatibleRows = rows.map(({ location_name, location_lat, location_lng, ...row }) => row);
  const { error: retryError } = await supabase.from('event').upsert(compatibleRows, { onConflict: 'id' });
  if (retryError) throw new Error(`event: ${retryError.message}`);
  console.log(`seeded ${rows.length} rows into event without location columns`);
}

await upsert('person', people);
await upsertEvents(events);
await upsert('person_relationship', relationships);
await upsert('person_event', personEvents);
await upsert('event_causality', causalities);
