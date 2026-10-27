/** Navigation groups for editorial era labels. These are not new dates or identity claims. */
export const personEraPeriods = [
  { key: "pre-qin", label: "先秦" },
  { key: "qin-han", label: "秦汉" },
  { key: "three-kingdoms", label: "三国" },
  { key: "jin-sixteen-kingdoms", label: "两晋十六国" },
  { key: "southern-northern", label: "南北朝" },
  { key: "sui-tang", label: "隋唐" },
  { key: "five-dynasties", label: "五代十国" },
  { key: "song-liao-jin-xia", label: "宋辽金夏" },
  { key: "mongol-yuan", label: "蒙古与元" },
  { key: "ming", label: "明" },
  { key: "qing", label: "清" },
  { key: "uncertain", label: "时代待考" },
  { key: "unclassified", label: "其他／待归类" },
] as const;
export type PersonEraPeriodKey = (typeof personEraPeriods)[number]["key"];
export interface PersonEraPeriodFacet {
  key: PersonEraPeriodKey;
  label: string;
  count: number;
}
export interface PersonDirectoryFacets {
  periods: PersonEraPeriodFacet[];
  /** Exact raw labels retained for old API consumers, not the directory dropdown. */
  eras: string[];
  factions: string[];
  books: Array<{ book_key: string; title: string }>;
}

const aliases: Partial<Record<PersonEraPeriodKey, readonly string[]>> = {
  "pre-qin": [
    "先秦",
    "上古",
    "神话时代",
    "五帝叙事",
    "五帝",
    "夏",
    "商",
    "周",
    "西周",
    "东周",
    "春秋",
    "战国",
    "战国初期",
    "商末周初",
    "战国末至秦末",
  ],
  "qin-han": [
    "秦汉",
    "秦",
    "汉",
    "西汉",
    "西汉初年",
    "东汉",
    "两汉之际",
    "秦末",
    "秦末汉初",
    "战国末至秦末",
  ],
  "three-kingdoms": ["三国"],
  "jin-sixteen-kingdoms": [
    "两晋十六国",
    "两晋",
    "晋",
    "西晋",
    "东晋",
    "十六国",
  ],
  "southern-northern": [
    "南北朝",
    "南朝",
    "北朝",
    "南朝宋",
    "刘宋",
    "南齐",
    "北齐",
    "北魏",
    "东魏",
    "西魏",
    "北周",
    "南朝梁",
    "南朝陈",
    "北周至唐",
  ],
  "sui-tang": [
    "隋唐",
    "隋",
    "唐",
    "晚唐",
    "隋末唐初",
    "北周至唐",
    "唐末五代十国",
    "晚唐至五代",
  ],
  "five-dynasties": [
    "五代",
    "五代十国",
    "唐末五代十国",
    "晚唐至五代",
    "五代至北宋初",
  ],
  "song-liao-jin-xia": [
    "宋辽金夏",
    "五代至北宋初",
    "宋",
    "北宋",
    "南宋",
    "北宋末至南宋初",
    "北宋至南宋",
    "辽",
    "契丹",
    "金",
    "女真",
    "西夏",
    "西夏至北宋",
    "西辽",
    "东夏",
    "金齐",
    "伪齐",
    "宋金",
    "宋金之际",
    "宋及同时诸政权",
    "宋夏之间",
    "宋至金",
    "宋西南诸部",
    "南宋边部",
    "南宋至金齐",
    "金齐至南宋",
    "金至南宋",
    "金末南宋",
    "金末辽",
    "金末东夏",
    "辽宋金",
    "辽至宋",
    "辽至金",
    "北宋末至金",
    "金宋国别待考",
    "宋蒙",
    "宋蒙古",
    "宋金蒙",
    "金末蒙古",
    "辽末蒙古",
    "南宋元",
    "南宋至元",
    "宋元",
    "宋至元",
  ],
  "mongol-yuan": [
    "蒙古与元",
    "蒙古",
    "元",
    "元末",
    "蒙古元",
    "蒙古诸部",
    "蒙古吐蕃",
    "蒙古高丽",
    "元高丽",
    "宋蒙",
    "宋蒙古",
    "宋金蒙",
    "金末蒙古",
    "辽末蒙古",
    "南宋元",
    "南宋至元",
    "宋元",
    "宋至元",
    "元末明初",
    "高丽至元",
  ],
  ming: ["明", "明初", "元末明初", "明清", "明末清初"],
  qing: ["清", "清末", "明清", "明末清初"],
  uncertain: [
    "",
    "待考",
    "时代待考",
    "时代未详",
    "年代待考",
    "年代未详",
    "赵国，具体年代待核",
  ],
};
const membership = new Map<string, PersonEraPeriodKey[]>();
for (const period of personEraPeriods) {
  for (const alias of aliases[period.key] ?? []) {
    const groups = membership.get(alias) ?? [];
    if (!groups.includes(period.key)) groups.push(period.key);
    membership.set(alias, groups);
  }
}
/** Exact reviewed spellings only: a bare polity (e.g. 齐、高丽) must not acquire guessed dates. */
export function classifyPersonEra(
  raw?: string | null,
): readonly PersonEraPeriodKey[] {
  return membership.get((raw ?? "").trim()) ?? ["unclassified"];
}
export function isPersonEraPeriod(value: string): value is PersonEraPeriodKey {
  return personEraPeriods.some((period) => period.key === value);
}
