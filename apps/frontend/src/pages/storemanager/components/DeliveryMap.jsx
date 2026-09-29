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

// Create custom DivIcons for our 3 points
const depotIcon = L.divIcon({
  className: 'bg-transparent',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-4 h-4 rounded-full bg-slate-800 border-2 border-white shadow-md z-10"></div>
      <div class="mt-1 bg-white px-2 py-0.5 rounded shadow-sm border border-slate-200 text-[10px] font-bold text-slate-700 whitespace-nowrap">Peliyagoda Depot</div>
    </div>
  `,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const outletIcon = L.divIcon({
  className: 'bg-transparent',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-4 h-4 rounded-full bg-slate-800 border-2 border-white shadow-md z-10"></div>
      <div class="mt-1 bg-white px-2 py-0.5 rounded shadow-sm border border-slate-200 text-[10px] font-bold text-slate-700 whitespace-nowrap">Nugegoda Outlet</div>
    </div>
  `,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const createVehicleIcon = (id) => L.divIcon({
  className: 'bg-transparent',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-7 h-7 rounded-full bg-brand-600 border-2 border-white shadow-md flex items-center justify-center text-[12px] z-20">
        🚚
      </div>
      <div class="mt-1 bg-white px-2 py-0.5 rounded shadow-sm border border-slate-200 text-[10px] font-bold text-brand-700 whitespace-nowrap">${id}</div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
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
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Route Line */}
        <Polyline 
          positions={routeCoords} 
          pathOptions={{ color: '#0ea5e9', weight: 4, opacity: 0.8 }} // using a nice brand accent
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
