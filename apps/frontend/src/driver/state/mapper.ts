import type { DriverStop } from "@/driver/data/driverContent";

export function mapBackendStopToDriverStop(dto: any): DriverStop {
  // Determine outcome
  let outcome: "delivered" | "partial" | "failed" | null = null;
  if (dto.status === "completed") {
    outcome = "delivered";
  } else if (dto.status === "failed") {
    outcome = "failed";
  }

  // Format window
  let window = "Anytime";
  if (dto.window_open && dto.window_close) {
    window = `${dto.window_open}-${dto.window_close}`;
  }

  return {
    seq: dto.seq,
    outletId: dto.outlet_id,
    name: dto.outlet_name || "Unknown Outlet",
    address: `${dto.district || ""} Area`.trim(),
    window,
    mallWindow: dto.mall_window,
    dock: (dto.dock_type || "Street") as any,
    parking: (dto.park_constraint || "Normal") as any,
    temp: (dto.temp_req || "Ambient") as any,
    units: dto.order_units || 0,
    deliverableUnits: dto.order_units || 0,
    returnUnits: 0, // Should be calculated if returns exist
    manager: "Store Manager",
    phoneMasked: "+94 77 ••• ••••",
    serviceMin: 15,
    outcome: outcome as any,
    district: dto.district as any,
    // Store original stop_id in depot field temporarily or extend DriverStop
    depot: dto.stop_id, 
  };
}
