import { useEffect } from 'react';
import { MapContainer, ImageOverlay, useMap } from 'react-leaflet';
import { CRS, type LatLngBoundsExpression } from 'leaflet';
import type { Event } from '@histree/shared-types';
import 'leaflet/dist/leaflet.css';

const bounds: LatLngBoundsExpression = [[0, 0], [390, 576]];
const imageUrl = `${import.meta.env.BASE_URL}maps/shituguan-907.jpg`;
function FitImage() {
  const map = useMap();
  useEffect(() => {
    const fit = () => { map.invalidateSize(); map.fitBounds(bounds, { padding: [12, 12] }); };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map]);
  return <button type="button" className="absolute top-3 right-3 z-[500] rounded-lg bg-white px-3 py-2 text-sm shadow" onClick={fitToImage}>查看全图</button>;
  function fitToImage() { map.fitBounds(bounds, { padding: [12, 12] }); }
}
export default function HistoricalMap({ selected }: { selected?: Event }) {
  return <div className="space-y-3">
    <div>
      <h3 className="font-semibold">907 年形势参考图 · 史图馆</h3>
      <p className="text-sm text-slate-600 mt-1">拖动或使用 + / − 放大查看。底图固定为 907 年，切换事件不会改变图中疆域。</p>
      {selected?.start_year != null && selected.start_year !== 907 && <p className="text-sm text-amber-900 mt-2">所选事件发生于 {selected.start_year} 年；这张图用于对照五代开端的形势，不代表事件当年的疆域。</p>}
    </div>
    <div className="relative z-0 overflow-hidden rounded-xl border border-stone-200" aria-label="907年历史形势图">
      <MapContainer crs={CRS.Simple} bounds={bounds} minZoom={-2} maxZoom={3} scrollWheelZoom={false} style={{ height: 460, width: '100%', background: '#f0efe2' }}>
        <ImageOverlay url={imageUrl} bounds={bounds} alt="史图馆907年形势参考图，图片获取自注明作者的转载文章" attribution="地图原作者：史图馆" />
        <FitImage />
      </MapContainer>
    </div>
    <p className="text-xs leading-6 text-slate-500">地图原作者：史图馆。图片获取自 <a className="underline" href="https://www.sohu.com/a/545519368_120646375" target="_blank" rel="noreferrer">《图说五代十国》转载页</a>，年份依据该页图注。<a className="underline ml-1" href="https://www.bilibili.com/video/BV1uc411n7LN/" target="_blank" rel="noreferrer">观看史图馆《隋唐五代篇》</a>（相关作品，非本图片版本的确定出处）。本图保持原样，Histree 提供缩放与事件对照；图片像素不作为经纬度，暂未添加地点标记。</p>
    <a className="text-sm text-teal-700 underline" href={imageUrl} target="_blank" rel="noreferrer">打开完整图片 ↗</a>
  </div>;
}
