import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet';
import { KANDY_HUB_COORDS, STOP_COORDS, VEHICLE, type GeoPoint } from "@/driver/data/driverContent";
import { buildRoadGeometry } from "@/driver/lib/roadGeometry";
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useTheme } from "@/theme/useTheme";
import { cn } from "@/lib/cn";
import './DriverMap.css';

// Fix for default Leaflet icon paths in Vite/Webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export type MapStopState = 'upcoming' | 'current' | 'completed' | 'flagged' | 'failed';

export interface DriverMapProps {
  stopIds: string[];
  currentStopId?: string;
  selectedStopId?: string;
  recenterTrigger?: number;
  completedStopIds?: string[];
  flaggedStopIds?: string[];
  failedStopIds?: string[];
  onStopClick?: (outletId: string) => void;
  className?: string;
}

// Fallback for getting stop coords if getStopCoords is not exported
function getStopCoords(outletId: string): GeoPoint {
  const coords = STOP_COORDS[outletId as keyof typeof STOP_COORDS];
  if (!coords) throw new Error(`Missing coords for ${outletId}`);
  return coords;
}

function FitBounds({ bounds, selectedStopId }: { bounds: L.LatLngBounds | null, selectedStopId?: string }) {
  const map = useMap();
  useEffect(() => {
    if (bounds && bounds.isValid() && !selectedStopId) {
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [map, bounds, selectedStopId]);
  
  useEffect(() => {
    if (selectedStopId) {
      try {
        const coords = getStopCoords(selectedStopId);
        map.flyTo([coords.lat, coords.lng], 16, { duration: 0.5 });
      } catch (e) {}
    }
  }, [map, selectedStopId]);
  return null;
}

function RecenterMap({ trigger, coords }: { trigger?: number, coords: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    if (trigger && trigger > 0) {
      map.flyTo(coords, 16, { duration: 0.5 });
    }
  }, [map, trigger, coords]);
  return null;
}

const depotIcon = L.divIcon({
  className: 'bg-transparent border-none',
  html: `
    <div class="flex items-center justify-center w-7 h-7 rounded-lg border-2 border-slate-200 bg-white shadow-sm">
      <div class="w-2.5 h-2.5 rounded-[3px] bg-[#059669]"></div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const createVehicleIcon = (id: string) => L.divIcon({
  className: 'bg-transparent border-none',
  html: `
    <div class="relative flex flex-col items-center">
      <div class="w-[18px] h-[18px] rounded-full bg-[#059669] border-[3px] border-white shadow-sm"></div>
      <div class="mt-2 bg-white px-1.5 py-0.5 rounded shadow-sm border border-slate-200 text-[9px] font-bold text-slate-700 whitespace-nowrap uppercase tracking-wider">${id}</div>
    </div>
  `,
  iconSize: [60, 40],
  iconAnchor: [30, 9],
});

export function DriverMap({
  stopIds,
  currentStopId,
  selectedStopId,
  recenterTrigger,
  completedStopIds = [],
  flaggedStopIds = [],
  failedStopIds = [],
  onStopClick,
  className
}: DriverMapProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [routeLine, setRouteLine] = useState<[number, number][] | null>(null);

  // Prepare waypoints
  const waypoints = stopIds.map(id => getStopCoords(id));
  const depotCoords: [number, number] = [KANDY_HUB_COORDS.lat, KANDY_HUB_COORDS.lng];
  const markerPositions = [depotCoords, ...waypoints.map(w => [w.lat, w.lng] as [number, number])];

  // Determine bounds
  const bounds = L.latLngBounds(routeLine ?? markerPositions);

  // Build and stitch road geometry from DB / cache
  useEffect(() => {
    let cancelled = false;
    const sequence = ['DEPOT:KANDY_HUB', ...stopIds];
    buildRoadGeometry(sequence)
      .then(latLngs => {
        if (!cancelled) {
          if (latLngs && latLngs.length > 0) {
            setRouteLine(latLngs);
          } else {
            setRouteLine(null);
          }
        }
      })
      .catch(err => {
        console.error('Failed to build road geometry for driver map', err);
        if (!cancelled) setRouteLine(null);
      });
    return () => {
      cancelled = true;
    };
  }, [stopIds]); // Re-fetch only if route stops change

  // Determine vehicle position
  let vehicleCoords: [number, number] = [KANDY_HUB_COORDS.lat, KANDY_HUB_COORDS.lng];
  if (completedStopIds.length > 0) {
    const lastCompletedId = completedStopIds[completedStopIds.length - 1];
    if (lastCompletedId) {
      try {
        const coords = getStopCoords(lastCompletedId);
        vehicleCoords = [coords.lat, coords.lng];
      } catch (e) {
        // fallback
      }
    }
  }

  return (
    <div
      className={cn(
        "driver-map",
        isDark && "driver-map--dark",
        className
      )}
      aria-label="Route map showing stops and depot"
      role="region"
    >
      <MapContainer
        bounds={bounds}
        zoomControl={false}
        attributionControl={true}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Route Line */}
        <Polyline
          positions={routeLine ?? markerPositions}
          pathOptions={routeLine
            ? { color: '#64748b', weight: 3, opacity: 0.6, dashArray: '6, 6' }
            : { color: '#64748b', weight: 3, dashArray: '6, 6', opacity: 0.6 }
          }
        />

        {/* Depot Marker */}
        <Marker position={depotCoords} icon={depotIcon} />

        {/* Stop Markers */}
        {stopIds.map((stopId, index) => {
          const coords = getStopCoords(stopId);
          const currentIdx = stopIds.indexOf(currentStopId ?? "");
          let state: MapStopState = 'upcoming';

          if (index > currentIdx && currentIdx >= 0) {
            state = 'upcoming';
          } else if (currentStopId === stopId) {
            state = 'current';
          } else if (failedStopIds.includes(stopId)) {
            state = 'failed';
          } else if (flaggedStopIds.includes(stopId)) {
            state = 'flagged';
          } else if (completedStopIds.includes(stopId)) {
            state = 'completed';
          }

          let innerHtml = '';
          if (state === 'current') {
            innerHtml = `<div class="flex items-center justify-center w-[34px] h-[34px] rounded-full border-2 border-[#059669] bg-[#d1fae5] text-[#059669] font-bold text-[14px] shadow-sm">${index + 1}</div>`;
          } else if (state === 'completed') {
            innerHtml = `<div class="flex items-center justify-center w-[34px] h-[34px] rounded-full border-2 border-slate-200 bg-slate-100 text-slate-400 font-bold text-[14px] opacity-60">${index + 1}</div>`;
          } else if (state === 'flagged') {
            innerHtml = `<div class="flex items-center justify-center w-[34px] h-[34px] rounded-full border-2 border-[#D97706] bg-[#FEF3C7] text-[#D97706] font-bold text-[14px] shadow-sm">${index + 1}</div>`;
          } else if (state === 'failed') {
            innerHtml = `<div class="flex items-center justify-center w-[34px] h-[34px] rounded-full border-2 border-[#DC2626] bg-[#FEE2E2] text-[#DC2626] font-bold text-[14px] shadow-sm">${index + 1}</div>`;
          } else {
            // upcoming
            innerHtml = `<div class="flex items-center justify-center w-[34px] h-[34px] rounded-full border-2 border-slate-300 bg-white text-slate-700 font-bold text-[14px] shadow-sm">${index + 1}</div>`;
          }

          const stopIcon = L.divIcon({
            className: 'bg-transparent border-none',
            html: innerHtml,
            iconSize: [34, 34],
            iconAnchor: [17, 17],
          });

          return (
            <Marker
              key={stopId}
              position={[coords.lat, coords.lng]}
              icon={stopIcon}
              eventHandlers={{
                click: () => onStopClick?.(stopId)
              }}
            />
          );
        })}

        {/* Vehicle Marker */}
        <Marker
          position={vehicleCoords}
          icon={createVehicleIcon(VEHICLE.id)}
          zIndexOffset={1000}
        />

        <FitBounds bounds={bounds} selectedStopId={selectedStopId} />
        <RecenterMap trigger={recenterTrigger} coords={vehicleCoords} />
      </MapContainer>
    </div>
  );
}
