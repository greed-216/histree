import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { divIcon } from 'leaflet';
import type { Event } from '@histree/shared-types';
import 'leaflet/dist/leaflet.css';

function hasCoordinates(event: Event) {
  return typeof event.location_lat === 'number' && Number.isFinite(event.location_lat) && Math.abs(event.location_lat) <= 90
    && typeof event.location_lng === 'number' && Number.isFinite(event.location_lng) && Math.abs(event.location_lng) <= 180;
}
function View({ events, selected }: { events: Event[]; selected?: Event }) {
  const map = useMap();
  const positions = events.map(e => [e.location_lat!, e.location_lng!] as [number, number]);
  const boundsKey = JSON.stringify(positions);
  useEffect(() => {
    const points = JSON.parse(boundsKey) as [number, number][];
    if (points.length) map.fitBounds(points, { padding: [35, 35], maxZoom: 8, animate: false });
  }, [map, boundsKey]);
  useEffect(() => {
    if (selected && hasCoordinates(selected)) map.setView([selected.location_lat!, selected.location_lng!], 8, { animate: false });
  }, [map, selected]);
  useEffect(() => {
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map]);
  return null;
}
export default function TopicMap({ events, selected, onSelect }: { events: Event[]; selected?: Event; onSelect: (id: string) => void }) {
  const [tileError, setTileError] = useState(false);
  const located = events.filter(hasCoordinates);
  const groups = new Map<string, Event[]>();
  for (const e of located) {
    const key = `${e.location_lat},${e.location_lng}`;
    groups.set(key, [...groups.get(key) ?? [], e]);
  }

  return <div className="min-w-0 space-y-2">
    {!located.length && <p role="status" className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900">当前事件尚无已核实坐标。下方显示方位参考底图；古地名可在事件列表中查看，核实坐标后才会出现标记。</p>}
    <p className="text-xs text-slate-500">现代底图仅用于方位参考；标记不表示历史疆界，概略位置不代表精确城址。</p>
    <div className="relative z-0 overflow-hidden rounded-xl" aria-label="专题事件地图">
      <MapContainer center={[35, 110]} zoom={4} scrollWheelZoom={false} style={{ height: 360, width: '100%' }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' eventHandlers={{ tileerror: () => setTileError(true), tileload: () => setTileError(false) }} />
        <View events={located} selected={selected} />
        {[...groups.values()].map((group, index) => {
          const active = group.some(e => e.id === selected?.id);
          return <Marker key={`${group[0].location_lat},${group[0].location_lng}`} position={[group[0].location_lat!, group[0].location_lng!]} title={`${group[0].location_name || '事件地点'} · ${group.length} 个事件`} icon={divIcon({ className: '', html: `<span class="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white shadow ${active ? 'bg-orange-700' : 'bg-teal-800'} text-white font-bold">${index + 1}</span>`, iconSize: [32, 32], iconAnchor: [16, 16] })} eventHandlers={{ click: () => onSelect(group[0].id) }}>
            <Popup><div className="space-y-2"><p className="font-semibold">{group[0].location_name || '事件地点'}</p>{group.map(e => <button key={e.id} className="block text-teal-800 underline" onClick={() => onSelect(e.id)}>{e.title}</button>)}</div></Popup>
          </Marker>;
        })}
      </MapContainer>
    </div>
    {tileError && <p role="status" className="text-sm text-slate-600">底图暂时无法加载，仍可通过事件列表查看地点和内容。</p>}
  </div>;
}
