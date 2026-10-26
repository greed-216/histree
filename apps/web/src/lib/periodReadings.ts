import { historyScroll } from "./historyScroll";
const keys = [
  "western-zhou",
  "spring-autumn",
  "warring-states",
  "qin-han",
  "three-kingdoms",
  "jin-sixteen-kingdoms",
  "southern-northern",
  "sui-tang",
  "five-dynasties",
  "song",
  "yuan",
  "ming",
  "qing",
];
export const periodReadings = historyScroll.periods.map((p, index) => ({
  ...p,
  id: keys[index],
}));
