import { isSafeExternalHref } from "@/lib/security";
import type { GeoPoint } from "@/driver/data/driverContent";

export function osmDirectionsUrl(from: GeoPoint, to: GeoPoint): string {
  const origin = `${from.lat},${from.lng}`;
  const destination = `${to.lat},${to.lng}`;
  return `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${encodeURIComponent(origin)}%3B${encodeURIComponent(destination)}`;
}

export function openExternalMap(url: string): void {
  if (!isSafeExternalHref(url)) return;
  window.open(url, "_blank", "noopener,noreferrer");
}
