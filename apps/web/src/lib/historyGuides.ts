import data from "../data/history-guides.json";
const selected: Record<number, string[]> = {
  951: ["event_zztj_290_0951_guo_accession_chongyuan"],
  954: [
    "event_zztj_291_0954_chairong_accession",
    "event_zztj_291_0954_zhou_captures_gaoping_spoils",
    "event_zztj_292_0954_chairong_orders_troop_selection",
  ],
  955: [
    "event_zztj_292_0955_wangpu_presents_strategy",
    "event_zztj_292_0955_fengzhou_captured",
    "event_zztj_292_0955_temple_consolidation",
  ],
  958: [
    "event_zztj_294_0958_jiangbei_territory_summary",
    "event_zztj_294_0958_lijing_renames_and_reduces_titles",
    "event_zztj_294_0958_aiying_tax_equalization",
  ],
  959: [
    "event_zztj_294_0959_liuchuxin_mozhou_surrender",
    "event_zztj_294_0959_chairong_dies",
    "event_zztj_294_0959_zongxun_accession",
  ],
};
const events = new Map(
  data.zhou.chapters.flatMap((c) => c.events).map((e) => [e.key, e]),
);
export function guideHighlights(year: number) {
  return (selected[year] ?? []).flatMap((key) => {
    const event = events.get(key);
    return event && event.year === year
      ? [{ id: event.id, title: event.title }]
      : [];
  });
}

export function hasGuideForNode(id: string) {
  return data.zhou.chapters.some(
    (c) =>
      c.people.some((p) => p.id === id) || c.events.some((e) => e.id === id),
  );
}
