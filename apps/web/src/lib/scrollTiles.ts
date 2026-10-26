import manifest from "../data/history-scroll-tiles.json";
import { historyScroll, scrollPanels } from "./historyScroll";
export type ScrollPanel = (typeof scrollPanels)[number];
export type TilePanel = (typeof manifest.panels)[number];
export type ScrollTile = TilePanel['tiles'][number];
export const tilePanels = manifest.panels;
/** Chapter display positions and annual positions share drawing units, not calendar meaning. */
export function visibleScrollTiles(panel: ScrollPanel, from: number, to: number, next?: ScrollPanel) {
  const atlas = tilePanels.find(item=>item.id===panel.id)!;
  const nativePerPosition = historyScroll.pixels_per_elapsed_year * panel.crop.height / 720;
  const ownEnd = panel.from_position + panel.crop.width/nativePerPosition;
  // Once the following image is opaque, don't fetch the covered part of this image.
  const end = Math.min(ownEnd, next ? next.from_position+(next.fade_in_pixels??0)/historyScroll.pixels_per_elapsed_year : ownEnd);
  const left = Math.max(from,panel.from_position),right=Math.min(to,end);
  if(right<=left)return {atlas,visible:[],adjacent:[]};
  const sourceLeft=panel.crop.x+(left-panel.from_position)*nativePerPosition;
  const sourceRight=panel.crop.x+(right-panel.from_position)*nativePerPosition;
  const visible=atlas.tiles.filter(tile=>tile.content_x+tile.content_width>sourceLeft&&tile.content_x<sourceRight);
  const first=atlas.tiles.indexOf(visible[0]),last=atlas.tiles.indexOf(visible.at(-1)!);
  const adjacent=[atlas.tiles[first-1],atlas.tiles[last+1]].filter((tile):tile is ScrollTile=>!!tile&&tile.content_x<panel.crop.x+(end-panel.from_position)*nativePerPosition);
  return {atlas,visible,adjacent};
}
