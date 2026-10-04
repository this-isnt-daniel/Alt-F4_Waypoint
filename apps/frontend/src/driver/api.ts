import { apiFetch } from "@/lib/api";

// Fetch today's summary of trips (returns TodayTripsResponse)
export async function fetchTodayTrips() {
  return apiFetch<any>("/driver-platform/trips/today");
}

// Fetch details for a specific trip
export async function fetchTripDetail(tripId: string) {
  return apiFetch<any>(`/driver-platform/trips/${tripId}`);
}

// Post a driver event for syncing
export async function postDriverEvent(
  kind: string, 
  targetId: string, 
  payload: any, 
  clientEventId: string
) {
  return apiFetch<any>(`/driver-platform/events`, {
    method: "POST",
    body: JSON.stringify({
      kind,
      target_id: targetId,
      client_event_id: clientEventId,
      payload
    })
  });
}
