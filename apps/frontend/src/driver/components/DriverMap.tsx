import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { KANDY_HUB_COORDS, STOP_COORDS, type GeoPoint } from "@/driver/data/driverContent";
import { buildRoadGeometry, centroid } from "@/driver/lib/roadGeometry";
import { useTheme } from "@/theme/useTheme";
import { cn } from "@/lib/cn";
import './DriverMap.css';

export type MapStopState = 'upcoming' | 'current' | 'completed' | 'flagged' | 'failed';

export interface DriverMapProps {
  stopIds: string[];
  currentStopId?: string;
  completedStopIds?: string[];
  flaggedStopIds?: string[];
  failedStopIds?: string[];
  onStopClick?: (outletId: string) => void;
  selectedStopId?: string;
  recenterTrigger?: number;
  className?: string;
}

// Resilient coordinate getter with automatic centroid fallback
function getStopCoords(outletId: string): GeoPoint {
  const coords = STOP_COORDS[outletId];
  if (coords) return coords;
  const [lat, lng] = centroid(outletId);
  return { lat, lng };
}

export function DriverMap({
  stopIds,
  currentStopId,
  completedStopIds = [],
  flaggedStopIds = [],
  failedStopIds = [],
  onStopClick,
  selectedStopId,
  recenterTrigger,
  className
}: DriverMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const tileLayerRef = useRef<L.TileLayer | null>(null);
  const polylineRef = useRef<L.Polyline | null>(null);
  const markersRef = useRef<L.Marker[]>([]);
  const { theme } = useTheme();
  const isDark = theme === "dark";

  // Initialize map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = L.map(mapContainerRef.current, {
      zoomControl: false,
      attributionControl: true,
    });
    
    // Humanitarian OpenStreetMap tiles: free, reliable, no API key or watermark required
    const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
      subdomains: ['a', 'b'],
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/">HOT</a>'
    }).addTo(map);

    tileLayerRef.current = tileLayer;
    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
      tileLayerRef.current = null;
    };
  }, []);

  // Update markers, road polyline and bounds
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    let isCancelled = false;

    // Clear old markers and polyline
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];
    if (polylineRef.current) {
      polylineRef.current.remove();
    }

    const waypoints: L.LatLngExpression[] = [];

    // Add Depot marker
    const depotIcon = L.divIcon({
      className: 'driver-map-div-icon',
      html: `<div class="map-depot" title="Kandy Hub Depot"></div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
    const depotMarker = L.marker([KANDY_HUB_COORDS.lat, KANDY_HUB_COORDS.lng], { icon: depotIcon })
      .addTo(map);
    markersRef.current.push(depotMarker);
    waypoints.push([KANDY_HUB_COORDS.lat, KANDY_HUB_COORDS.lng]);

    // Add Stop markers
    stopIds.forEach((stopId, index) => {
      try {
        const coords = getStopCoords(stopId);
        const currentIdx = stopIds.indexOf(currentStopId ?? "");
        let state: MapStopState = 'upcoming';
        
        if (index > currentIdx && currentIdx >= 0) {
          // Strictly upcoming stop - temporal logic: cannot be failed or completed before visit!
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

        const stopIcon = L.divIcon({
          className: 'driver-map-div-icon',
          html: `<div class="map-pin map-pin--${state}">${index + 1}</div>`,
          iconSize: [34, 34],
          iconAnchor: [17, 17],
        });

        const stopMarker = L.marker([coords.lat, coords.lng], { icon: stopIcon })
          .addTo(map);
        
        if (onStopClick) {
          // Allow clicks on current and past stops; upcoming stops are sequential
          stopMarker.on('click', () => {
            if (index <= currentIdx || currentIdx < 0) {
              onStopClick(stopId);
            }
          });
        }
        
        markersRef.current.push(stopMarker);
        waypoints.push([coords.lat, coords.lng]);
      } catch (err) {
        console.warn(`Could not get coords for stop ${stopId}`, err);
      }
    });

    // Add Polyline with solid green line as requested
    if (waypoints.length > 1) {
      const polyline = L.polyline(waypoints, {
        color: '#059669', // Emerald solid green line
        weight: 5,
        opacity: 0.9,
      }).addTo(map);
      polylineRef.current = polyline;
      
      // Fit bounds to direct waypoints initially
      const initialBounds = L.latLngBounds(waypoints);
      map.fitBounds(initialBounds, { padding: [36, 36], maxZoom: 16 });

      // Fetch and apply high-fidelity street road geometry
      const sequence = ['DEPOT:KANDY_HUB', ...stopIds];
      buildRoadGeometry(sequence)
        .then((roadCoords) => {
          if (isCancelled || !polylineRef.current) return;
          if (roadCoords.length > 1) {
            const latLngs: L.LatLngExpression[] = roadCoords.map(([lat, lng]) => [lat, lng]);
            polylineRef.current.setLatLngs(latLngs);
            if (map) {
              const bounds = L.latLngBounds(latLngs);
              map.fitBounds(bounds, { padding: [36, 36], maxZoom: 16 });
            }
          }
        })
        .catch((err) => {
          console.warn("Could not load full road geometry:", err);
        });
    } else if (waypoints.length === 1 && waypoints[0]) {
      map.setView(waypoints[0], 15);
    }

    return () => {
      isCancelled = true;
    };
  }, [stopIds, currentStopId, completedStopIds, flaggedStopIds, failedStopIds, onStopClick]);

  useEffect(() => {
    if (!mapRef.current) return;
    if (selectedStopId) {
      try {
        const coords = getStopCoords(selectedStopId);
        mapRef.current.setView([coords.lat, coords.lng], 16, { animate: true });
      } catch (e) {
        // ignore
      }
    }
  }, [selectedStopId]);

  useEffect(() => {
    if (!mapRef.current || !recenterTrigger) return;
    let vehicleCoords: [number, number] = [KANDY_HUB_COORDS.lat, KANDY_HUB_COORDS.lng];
    if (completedStopIds.length > 0) {
      const lastCompletedId = completedStopIds[completedStopIds.length - 1];
      if (lastCompletedId) {
        try {
          const coords = getStopCoords(lastCompletedId);
          vehicleCoords = [coords.lat, coords.lng];
        } catch (e) {}
      }
    }
    mapRef.current.setView(vehicleCoords, 16, { animate: true });
  }, [recenterTrigger, completedStopIds]);

  return (
    <div
      ref={mapContainerRef}
      className={cn(
        "driver-map",
        isDark && "driver-map--dark",
        className
      )}
      aria-label="Route map showing stops and depot"
      role="region"
    />
  );
}
