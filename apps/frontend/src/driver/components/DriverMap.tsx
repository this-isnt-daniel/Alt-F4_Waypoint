import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { KANDY_HUB_COORDS, STOP_COORDS, type GeoPoint } from "@/driver/data/driverContent";
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
  className?: string;
}

// Fallback for getting stop coords if getStopCoords is not exported
function getStopCoords(outletId: string): GeoPoint {
  const coords = STOP_COORDS[outletId];
  if (!coords) throw new Error(`Missing coords for ${outletId}`);
  return coords;
}

export function DriverMap({
  stopIds,
  currentStopId,
  completedStopIds = [],
  flaggedStopIds = [],
  failedStopIds = [],
  onStopClick,
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

  // Update markers, polyline and bounds
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

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
      html: `<div class="map-depot"></div>`,
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
        let state: MapStopState = 'upcoming';
        
        if (failedStopIds.includes(stopId)) state = 'failed';
        else if (flaggedStopIds.includes(stopId)) state = 'flagged';
        else if (completedStopIds.includes(stopId)) state = 'completed';
        else if (currentStopId === stopId) state = 'current';

        const stopIcon = L.divIcon({
          className: 'driver-map-div-icon',
          html: `<div class="map-pin map-pin--${state}">${index + 1}</div>`,
          iconSize: [34, 34],
          iconAnchor: [17, 17],
        });

        const stopMarker = L.marker([coords.lat, coords.lng], { icon: stopIcon })
          .addTo(map);
        
        if (onStopClick) {
          stopMarker.on('click', () => onStopClick(stopId));
        }
        
        markersRef.current.push(stopMarker);
        waypoints.push([coords.lat, coords.lng]);
      } catch (err) {
        console.warn(`Could not get coords for stop ${stopId}`, err);
      }
    });

    // Add Polyline
    if (waypoints.length > 1) {
      const polyline = L.polyline(waypoints, {
        color: '#64748b', // Using slate-500 since CSS vars might not work in SVG properties directly
        weight: 3,
        dashArray: '6, 6',
        opacity: 0.6
      }).addTo(map);
      polylineRef.current = polyline;
      
      // Fit bounds
      const bounds = L.latLngBounds(waypoints);
      map.fitBounds(bounds, { padding: [40, 40] });
    } else if (waypoints.length === 1 && waypoints[0]) {
      map.setView(waypoints[0], 14);
    }
  }, [stopIds, currentStopId, completedStopIds, flaggedStopIds, failedStopIds, onStopClick]);

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
