import { CircleMarker, MapContainer, TileLayer, Tooltip, useMapEvents } from 'react-leaflet';
import { LVIV_CENTER } from '../utils/format.js';

function ClickHandler({ onPick }) {
  useMapEvents({
    click(e) {
      onPick([e.latlng.lat, e.latlng.lng]);
    },
  });
  return null;
}

export default function LocationPicker({ value, onChange, restaurant }) {
  return (
    <MapContainer center={value || LVIV_CENTER} zoom={13} className="map map-small">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <ClickHandler onPick={onChange} />
      {restaurant && (
        <CircleMarker center={[restaurant.lat, restaurant.lng]} radius={9} pathOptions={{ color: '#ea580c', fillOpacity: 0.9 }}>
          <Tooltip>{restaurant.name}</Tooltip>
        </CircleMarker>
      )}
      {value && (
        <CircleMarker center={value} radius={10} pathOptions={{ color: '#16a34a', fillOpacity: 0.9 }}>
          <Tooltip permanent>Сюди доставити</Tooltip>
        </CircleMarker>
      )}
    </MapContainer>
  );
}
