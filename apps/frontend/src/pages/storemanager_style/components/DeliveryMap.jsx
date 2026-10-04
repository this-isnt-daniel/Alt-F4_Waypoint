import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet icon paths in Vite/Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const depotIcon = L.divIcon({
  className: 'bg-transparent border-none',
  html: `
    <div class="flex items-center justify-center w-7 h-7 rounded-lg border-2 border-slate-200 bg-white shadow-sm">
      <div class="w-2.5 h-2.5 rounded-[3px] bg-[#00A36C]"></div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const outletIcon = L.divIcon({
  className: 'bg-transparent border-none',
  html: `
    <div class="flex items-center justify-center w-[34px] h-[34px] rounded-full border-2 border-[#00A36C] bg-[#E5F6F0] text-[#00A36C] font-bold text-[13px] shadow-[0_0_0_4px_rgba(0,163,108,0.22)]">
      1
    </div>
  `,
  iconSize: [34, 34],
  iconAnchor: [17, 17],
});

const createVehicleIcon = (id) => L.divIcon({
  className: 'bg-transparent border-none',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-[18px] h-[18px] rounded-full bg-[#00A36C] border-[3px] border-white shadow-[0_0_0_4px_rgba(0,163,108,0.24)]"></div>
      <div class="mt-2 bg-white px-1.5 py-0.5 rounded shadow-sm border border-slate-200 text-[9px] font-bold text-slate-700 whitespace-nowrap uppercase tracking-wider">${id}</div>
    </div>
  `,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

// A component to automatically fit the map bounds to our markers
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [map, bounds]);
  return null;
}

export default function DeliveryMap({ order }) {
  // Mock Data Architecture - structured so real GPS can drop in later
  const deliveryTracking = {
    orderId: order.id,
    depot: { lat: 6.9610, lng: 79.8821, name: 'Peliyagoda Depot' },
    outlet: { lat: 6.8649, lng: 79.8997, name: 'Nugegoda Outlet' },
    vehicle: { lat: 6.9110, lng: 79.8720, id: order.vehicle || 'VH-UNKNOWN' },
    updatedAt: new Date().toISOString(),
  };

  // Mock a basic route from Depot -> Vehicle -> Outlet
  const routeCoords = [
    [deliveryTracking.depot.lat, deliveryTracking.depot.lng],
    [6.9450, 79.8750],
    [deliveryTracking.vehicle.lat, deliveryTracking.vehicle.lng],
    [6.8850, 79.8850],
    [deliveryTracking.outlet.lat, deliveryTracking.outlet.lng]
  ];

  const bounds = L.latLngBounds([
    [deliveryTracking.depot.lat, deliveryTracking.depot.lng],
    [deliveryTracking.outlet.lat, deliveryTracking.outlet.lng],
    [deliveryTracking.vehicle.lat, deliveryTracking.vehicle.lng],
  ]);

  return (
    <div className="w-full h-64 bg-slate-100 rounded-lg overflow-hidden border border-slate-200 shadow-inner relative z-0">
      <MapContainer 
        bounds={bounds} 
        zoomControl={false} // We will add it manually or keep it simple
        scrollWheelZoom={false}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/">HOT</a>'
          url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
        />
        
        {/* Route Line */}
        <Polyline 
          positions={routeCoords} 
          pathOptions={{ color: '#64748b', weight: 3, dashArray: '6, 6', opacity: 0.6 }} 
        />

        {/* Markers */}
        <Marker position={[deliveryTracking.depot.lat, deliveryTracking.depot.lng]} icon={depotIcon} />
        <Marker position={[deliveryTracking.outlet.lat, deliveryTracking.outlet.lng]} icon={outletIcon} />
        <Marker position={[deliveryTracking.vehicle.lat, deliveryTracking.vehicle.lng]} icon={createVehicleIcon(deliveryTracking.vehicle.id)} />
        
        <FitBounds bounds={bounds} />
      </MapContainer>
    </div>
  );
}
