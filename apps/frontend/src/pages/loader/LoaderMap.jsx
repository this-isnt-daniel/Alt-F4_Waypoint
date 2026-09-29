import React, { useEffect, useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet marker icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom icon for selected vehicle
const selectedIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Custom icon for unselected vehicles
const defaultIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Component to dynamically adjust map bounds
function MapBounds({ vehicles, selectedVehicleId }) {
  const map = useMap();

  useEffect(() => {
    if (!vehicles || vehicles.length === 0) return;

    if (selectedVehicleId) {
      const selected = vehicles.find(v => v.id === selectedVehicleId);
      if (selected?.location) {
        map.setView([selected.location.lat, selected.location.lng], 12, { animate: true });
      }
    } else {
      const bounds = L.latLngBounds(vehicles.filter(v => v.location).map(v => [v.location.lat, v.location.lng]));
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [30, 30] });
      }
    }
  }, [vehicles, selectedVehicleId, map]);

  return null;
}

// Component to render individual vehicle route using OSRM
function VehicleRoute({ vehicle, isSelected }) {
  const [routeGeometry, setRouteGeometry] = useState(null);

  useEffect(() => {
    if (!vehicle.routeCoords || vehicle.routeCoords.length < 2) return;

    const fetchRoute = async () => {
      try {
        // OSRM expects coordinates in lng,lat format
        const coords = vehicle.routeCoords.map(c => `${c.lng},${c.lat}`).join(';');
        const res = await fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`);
        const data = await res.json();
        
        if (data.code === 'Ok' && data.routes && data.routes[0]) {
          // Convert GeoJSON [lng, lat] to Leaflet [lat, lng]
          const latLngs = data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
          setRouteGeometry(latLngs);
        }
      } catch (err) {
        console.error('Failed to fetch route for', vehicle.id, err);
      }
    };

    fetchRoute();
  }, [vehicle.routeCoords]);

  if (!routeGeometry) return null;

  return (
    <Polyline 
      positions={routeGeometry} 
      pathOptions={{ 
        color: isSelected ? '#059669' : '#94a3b8', 
        weight: isSelected ? 4 : 2,
        opacity: isSelected ? 0.8 : 0.4
      }} 
    />
  );
}

export default function LoaderMap({ vehicles, selectedVehicleId, onSelectVehicle }) {
  const markerRefs = useRef({});

  // Auto-open popup when a vehicle is selected from outside the map
  useEffect(() => {
    if (selectedVehicleId && markerRefs.current[selectedVehicleId]) {
      const marker = markerRefs.current[selectedVehicleId];
      // Leaflet markers have an openPopup method
      if (marker && marker.openPopup) {
        marker.openPopup();
      }
    }
  }, [selectedVehicleId, vehicles]);

  // Default center somewhere in Sri Lanka
  const defaultCenter = [7.8731, 80.7718];

  return (
    <div className="w-full h-full border border-slate-200 rounded overflow-hidden shadow-sm relative z-0">
      <MapContainer center={defaultCenter} zoom={7} className="w-full h-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapBounds vehicles={vehicles} selectedVehicleId={selectedVehicleId} />

        <MarkerClusterGroup chunkedLoading maxClusterRadius={40}>
          {vehicles.map(veh => {
            const isSelected = selectedVehicleId === veh.id;
            
            return (
              <React.Fragment key={veh.id}>
                {/* Marker */}
                {veh.location && (
                  <Marker 
                    ref={(ref) => {
                      if (ref) markerRefs.current[veh.id] = ref;
                    }}
                    position={[veh.location.lat, veh.location.lng]}
                    icon={isSelected ? selectedIcon : defaultIcon}
                    eventHandlers={{
                      click: () => onSelectVehicle(veh.id)
                    }}
                  >
                    <Popup>
                      <div className="font-sans">
                        <div className="font-bold text-slate-900">{veh.id}</div>
                        <div className="text-sm font-semibold text-brand-600 mb-1">{veh.status}</div>
                        <div className="text-sm text-slate-600">{veh.route}</div>
                        {veh.eta && <div className="text-xs text-slate-500 mt-1">{veh.eta}</div>}
                      </div>
                    </Popup>
                  </Marker>
                )}
              </React.Fragment>
            );
          })}
        </MarkerClusterGroup>
        
        {/* Render selected route outside of cluster group to avoid issues */}
        {vehicles.map(veh => {
          if (selectedVehicleId !== veh.id) return null;
          return <VehicleRoute key={`route-${veh.id}`} vehicle={veh} isSelected={true} />;
        })}
      </MapContainer>
    </div>
  );
}
