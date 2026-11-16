import { useEffect, useRef, useState } from 'react';
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from 'react-leaflet';
import { api } from '../api.js';

export default function TrackingMap({ orderId, active, onStatusChange }) {
  const [data, setData] = useState(null);
  const lastStatus = useRef(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const t = await api(`/orders/${orderId}/tracking`);
        if (!alive) return;
        if (lastStatus.current && lastStatus.current !== t.status && onStatusChange) onStatusChange(t.status);
        lastStatus.current = t.status;
        setData(t);
      } catch {
        /* ignore */
      }
    };
    load();
    const timer = active ? setInterval(load, 3000) : null;
    return () => { alive = false; if (timer) clearInterval(timer); };
  }, [orderId, active, onStatusChange]);

  if (!data) return <div className="map map-placeholder">Завантаження карти…</div>;
  if (!data.destination) return null;

  const start = [data.restaurant.lat, data.restaurant.lng];
  const end = [data.destination.lat, data.destination.lng];
  const center = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2];

  return (
    <div>
      <MapContainer center={center} zoom={14} className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={data.route} pathOptions={{ color: '#ea580c', weight: 5, opacity: 0.7, dashArray: '8 6' }} />
        <CircleMarker center={start} radius={10} pathOptions={{ color: '#ea580c', fillOpacity: 0.9 }}>
          <Tooltip>{data.restaurant.name}</Tooltip>
        </CircleMarker>
        <CircleMarker center={end} radius={10} pathOptions={{ color: '#16a34a', fillOpacity: 0.9 }}>
          <Tooltip>{data.destination.address}</Tooltip>
        </CircleMarker>
        {data.courier && (
          <CircleMarker
            center={[data.courier.lat, data.courier.lng]}
            radius={12}
            pathOptions={{ color: '#1d4ed8', fillColor: '#3b82f6', fillOpacity: 1 }}
          >
            <Tooltip permanent direction="top">Кур'єр</Tooltip>
          </CircleMarker>
        )}
      </MapContainer>
      <div className="tracking-info">
        <span>Відстань: <b>{data.distance_km} км</b></span>
        <span>Статус: <b>{data.status_title}</b></span>
        {data.eta_minutes !== null && data.status !== 'DELIVERED' && <span>Прибуде орієнтовно через <b>{data.eta_minutes} хв</b></span>}
        <div className="progress"><div style={{ width: `${Math.round(data.progress * 100)}%` }} /></div>
      </div>
    </div>
  );
}
