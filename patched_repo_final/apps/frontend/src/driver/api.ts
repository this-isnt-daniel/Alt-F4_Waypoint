import { apiFetch } from "@/lib/api";

// Fetch today's summary of trips (returns TodayTripsResponse)
export async function fetchTodayTrips() {
  return apiFetch<any>("/driver-platform/trips/today");
}

// Fetch details for a specific trip
export async function fetchTripDetail(tripId: string) {
  return apiFetch<any>(`/driver-platform/trips/${tripId}`);
}

const KIND_TARGET_MAP: Record<string, string> = {
  "trip.departed": "trip_id",
  "trip.completed": "trip_id",
  "stop.arrived": "stop_id",
  "checklist.submitted": "stop_id",
  "pod.photo.completed": "stop_id",
  "pod.submitted": "stop_id",
  "stop.outcome.submitted": "stop_id",
  "return.created": "stop_id",
  "depot_return.confirmed": "return_id",
  "route_change.acknowledged": "change_id",
};

// Post a driver event for syncing
export async function postDriverEvent(
  kind: string, 
  targetId: string, 
  payload: any, 
  clientEventId: string
) {
  const targetKey = KIND_TARGET_MAP[kind] || "target_id";
  const syncPayload = { ...payload, [targetKey]: targetId };

  const response = await apiFetch<any>(`/driver-platform/events/sync`, {
    method: "POST",
    body: JSON.stringify({
      events: [
        {
          kind,
          client_event_id: clientEventId,
          payload: syncPayload
        }
      ]
    })
  });
  const result = response.results?.find((item: any) => item.client_event_id === clientEventId);
  if (!result || !["applied", "already_applied"].includes(result.status)) {
    throw new Error(result?.error || `Driver event was not accepted: ${result?.status || "missing result"}`);
  }
  return result;
}
