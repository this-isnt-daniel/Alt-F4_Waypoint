export const DRIVER = {
  name: "Nimal Perera",
  date: "Saturday · 26 September",
  shift: "05:10–14:22",
} as const;

export const VEHICLE = {
  id: "VEH014",
  type: "van",
  temp: "reefer",
  depot: "Kandy hub",
  kmPerL: 9.4,
  weeklyFuelQuotaL: 42,
  startRemainingFuelL: 42,
} as const;

export const REASSIGN_VEHICLE = {
  id: "VEH021",
  type: "truck",
  temp: "reefer",
  depot: "Kandy hub",
} as const;

export const LOADER = {
  name: "S. Fernando",
  depot: "Kandy hub",
} as const;

export type Brand = "Fresh" | "Style";
export type District = "Kandy";
export type Depot = "Kandy hub";
export type DockType = "Rear dock" | "Street" | "Mall bay";
export type ParkingConstraint = "Normal" | "Van only" | "Mall dock";
export type TempRequirement = "Chilled" | "Ambient" | "Chilled + ambient";
export type StopOutcome = "delivered" | "partial" | "failed";

export interface DriverStop {
  seq: number;
  outletId: string;
  name: string;
  address: string;
  window: string;
  mallWindow?: string;
  dock: DockType;
  dockDetail?: string;
  parking: ParkingConstraint;
  temp: TempRequirement;
  units: number;
  deliverableUnits: number;
  returnUnits: number;
  returnCrate?: string;
  manager: string;
  phoneMasked: string;
  serviceMin: number;
  instructions?: string;
  outcome: StopOutcome;
  brand?: Brand;
  district?: District;
  depot?: Depot;
}

export const TRIP_1_STOPS: DriverStop[] = [
  {
    seq: 1,
    outletId: "OUT042",
    name: "Waypoint Fresh Gampola",
    address: "Main Street, Gampola",
    window: "05:30–06:30",
    dock: "Street",
    parking: "Van only",
    temp: "Chilled + ambient",
    units: 120,
    deliverableUnits: 120,
    returnUnits: 0,
    manager: "K. Bandara",
    phoneMasked: "+94 7• ••• ••18",
    serviceMin: 16,
    outcome: "delivered",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 2,
    outletId: "OUT047",
    name: "Waypoint Fresh Kandy Town",
    address: "Dalada Veediya · beside Clock Tower, Kandy",
    window: "05:45–07:01",
    dock: "Rear dock",
    dockDetail: "bay B",
    parking: "Van only",
    temp: "Chilled",
    units: 25,
    deliverableUnits: 25,
    returnUnits: 0,
    manager: "Anjali Silva",
    phoneMasked: "+94 7• ••• ••42",
    serviceMin: 15,
    instructions:
      "Use service lane. Ask for manager Anjali Silva. Keep chilled crates sealed until handover.",
    outcome: "delivered",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 3,
    outletId: "OUT049",
    name: "Waypoint Fresh Kandy Fort",
    address: "Fort Road, Kandy",
    window: "06:00–07:30",
    dock: "Street",
    parking: "Normal",
    temp: "Ambient",
    units: 18,
    deliverableUnits: 18,
    returnUnits: 0,
    manager: "P. Jayasuriya",
    phoneMasked: "+94 7• ••• ••21",
    serviceMin: 14,
    outcome: "delivered",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 4,
    outletId: "OUT052",
    name: "Waypoint Fresh Kandy City Centre",
    address: "Kandy City Centre, loading bay level",
    window: "05:45–07:30",
    mallWindow: "05:30–07:00",
    dock: "Mall bay",
    parking: "Mall dock",
    temp: "Chilled + ambient",
    units: 160,
    deliverableUnits: 160,
    returnUnits: 0,
    manager: "M. Fernando",
    phoneMasked: "+94 7• ••• ••63",
    serviceMin: 18,
    outcome: "delivered",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 5,
    outletId: "OUT055",
    name: "Waypoint Fresh Kandy East",
    address: "Kandy East, Peradeniya Road",
    window: "06:15–07:45",
    dock: "Rear dock",
    parking: "Normal",
    temp: "Ambient",
    units: 8,
    deliverableUnits: 8,
    returnUnits: 0,
    manager: "R. Gunawardena",
    phoneMasked: "+94 7• ••• ••09",
    serviceMin: 12,
    outcome: "delivered",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 6,
    outletId: "OUT058",
    name: "Waypoint Fresh Kandy Hills",
    address: "Kandy Hills, Baddegama Road",
    window: "06:45–08:00",
    dock: "Rear dock",
    parking: "Normal",
    temp: "Chilled",
    units: 12,
    deliverableUnits: 10,
    returnUnits: 2,
    returnCrate: "R-04",
    manager: "S. Silva",
    phoneMasked: "+94 7• ••• ••77",
    serviceMin: 15,
    instructions:
      "Two frozen items are sealed in return crate R-04. Do not hand them over.",
    outcome: "partial",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 7,
    outletId: "OUT061",
    name: "Waypoint Fresh Peradeniya",
    address: "Peradeniya, Kandy",
    window: "06:45–08:00",
    dock: "Rear dock",
    parking: "Normal",
    temp: "Chilled + ambient",
    units: 210,
    deliverableUnits: 210,
    returnUnits: 0,
    manager: "D. Perera",
    phoneMasked: "+94 7• ••• ••34",
    serviceMin: 17,
    outcome: "delivered",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 8,
    outletId: "OUT064",
    name: "Waypoint Fresh Nawalapitiya",
    address: "Nawalapitiya, Kandy district",
    window: "07:00–08:00",
    dock: "Street",
    parking: "Normal",
    temp: "Ambient",
    units: 687,
    deliverableUnits: 687,
    returnUnits: 0,
    manager: "T. Rosa",
    phoneMasked: "+94 7• ••• ••55",
    serviceMin: 20,
    outcome: "delivered",
    brand: "Fresh",
    district: "Kandy",
    depot: "Kandy hub",
  },
];

export const TRIP_2_STOPS: DriverStop[] = [
  {
    seq: 1,
    outletId: "OUT070",
    name: "Waypoint Style Kandy City",
    address: "Kandy City Centre, Style unit",
    window: "10:00–12:00",
    mallWindow: "10:00–12:00",
    dock: "Mall bay",
    parking: "Mall dock",
    temp: "Ambient",
    units: 220,
    deliverableUnits: 220,
    returnUnits: 0,
    manager: "A. Silva",
    phoneMasked: "+94 7• ••• ••80",
    serviceMin: 18,
    outcome: "delivered",
    brand: "Style",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 2,
    outletId: "OUT071",
    name: "Waypoint Style Gampola",
    address: "Main Street, Gampola",
    window: "10:30–12:30",
    dock: "Street",
    parking: "Normal",
    temp: "Ambient",
    units: 160,
    deliverableUnits: 160,
    returnUnits: 0,
    manager: "J. Fernando",
    phoneMasked: "+94 7• ••• ••81",
    serviceMin: 15,
    outcome: "delivered",
    brand: "Style",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 3,
    outletId: "OUT072",
    name: "Waypoint Style Kandy Fort",
    address: "Fort Road, Kandy",
    window: "11:00–13:00",
    dock: "Rear dock",
    parking: "Normal",
    temp: "Ambient",
    units: 180,
    deliverableUnits: 180,
    returnUnits: 0,
    manager: "K. Silva",
    phoneMasked: "+94 7• ••• ••82",
    serviceMin: 16,
    outcome: "delivered",
    brand: "Style",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 4,
    outletId: "OUT073",
    name: "Waypoint Style Peradeniya",
    address: "Peradeniya, Kandy",
    window: "11:30–13:30",
    dock: "Street",
    parking: "Normal",
    temp: "Ambient",
    units: 150,
    deliverableUnits: 150,
    returnUnits: 0,
    manager: "L. Perera",
    phoneMasked: "+94 7• ••• ••83",
    serviceMin: 14,
    outcome: "delivered",
    brand: "Style",
    district: "Kandy",
    depot: "Kandy hub",
  },
  {
    seq: 5,
    outletId: "OUT074",
    name: "Waypoint Style Nawalapitiya",
    address: "Nawalapitiya, Kandy district",
    window: "12:00–14:00",
    dock: "Rear dock",
    parking: "Normal",
    temp: "Ambient",
    units: 150,
    deliverableUnits: 150,
    returnUnits: 0,
    manager: "M. Rosa",
    phoneMasked: "+94 7• ••• ••84",
    serviceMin: 14,
    outcome: "delivered",
    brand: "Style",
    district: "Kandy",
    depot: "Kandy hub",
  },
];

function sumNumbers(values: number[]): number {
  return values.reduce((total, value) => total + value, 0);
}

function countByOutcome(stops: DriverStop[], outcome: StopOutcome): number {
  return stops.filter((stop) => stop.outcome === outcome).length;
}

export const TRIP_1 = {
  id: 1,
  brand: "Fresh" as Brand,
  district: "Kandy" as District,
  depot: "Kandy hub" as Depot,
  status: "active" as const,
  capability: "CHILLED REEFER" as const,
  stops: TRIP_1_STOPS,
  stopCount: TRIP_1_STOPS.length,
  weightKg: 890,
  volumeM3: 4.2,
  manifestUnits: sumNumbers(TRIP_1_STOPS.map((stop) => stop.units)),
  deliverableUnits: sumNumbers(TRIP_1_STOPS.map((stop) => stop.deliverableUnits)),
  returnUnits: sumNumbers(TRIP_1_STOPS.map((stop) => stop.returnUnits)),
  deliveredCount: countByOutcome(TRIP_1_STOPS, "delivered"),
  partialCount: countByOutcome(TRIP_1_STOPS, "partial"),
  failedCount: countByOutcome(TRIP_1_STOPS, "failed"),
  depart: "05:45 AM",
  etaReturn: "09:30 AM",
  distanceKm: 126,
  driveTime: "3h 40m",
  startRemainingFuelL: 42,
  finishTime: "09:54",
  completedDistanceKm: 128,
  completedDuration: "3h 42m",
  fuelUsedL: 13.6,
  remainingFuelAfterTripL: 28.4,
};

export const TRIP_2 = {
  id: 2,
  brand: "Style" as Brand,
  district: "Kandy" as District,
  depot: "Kandy hub" as Depot,
  status: "locked" as const,
  capability: "AMBIENT" as const,
  stops: TRIP_2_STOPS,
  stopCount: TRIP_2_STOPS.length,
  weightKg: 540,
  volumeM3: 2.8,
  manifestUnits: sumNumbers(TRIP_2_STOPS.map((stop) => stop.units)),
  deliverableUnits: sumNumbers(TRIP_2_STOPS.map((stop) => stop.deliverableUnits)),
  returnUnits: sumNumbers(TRIP_2_STOPS.map((stop) => stop.returnUnits)),
  deliveredCount: countByOutcome(TRIP_2_STOPS, "delivered"),
  partialCount: countByOutcome(TRIP_2_STOPS, "partial"),
  failedCount: countByOutcome(TRIP_2_STOPS, "failed"),
  depart: "After Trip 1 + depot check",
  etaReturn: "02:22 PM",
  distanceKm: 54,
  driveTime: "1h 55m",
  remainingFuelAfterTrip1L: 28.4,
};

export const TRIPS = [TRIP_1, TRIP_2];

export const RUN_TARGETS = {
  stopCount: sumNumbers(TRIPS.map((trip) => trip.stopCount)),
  unitCount: sumNumbers(TRIPS.map((trip) => trip.manifestUnits)),
};

export interface LoadReviewGroup {
  id: string;
  label: string;
  outletId?: string;
  manifestUnits: number;
  deliverableUnits: number;
  returnUnits: number;
  status: "matches" | "flagged";
  coveredOutletIds?: string[];
  lineItem?: {
    name: string;
    manifestQuantity: number;
    deliverableQuantity: number;
    returnQuantity: number;
    reason: string;
    returnCrate: string;
  };
  loaderNote?: string;
}

export const LOAD_REVIEW_GROUPS: LoadReviewGroup[] = [
  {
    id: "LG1",
    outletId: "OUT047",
    label: "OUT047 · 25 units",
    manifestUnits: 25,
    deliverableUnits: 25,
    returnUnits: 0,
    status: "matches",
  },
  {
    id: "LG2",
    outletId: "OUT049",
    label: "OUT049 · 18 units",
    manifestUnits: 18,
    deliverableUnits: 18,
    returnUnits: 0,
    status: "matches",
  },
  {
    id: "LG3",
    outletId: "OUT058",
    label: "OUT058 · 12 units",
    manifestUnits: 12,
    deliverableUnits: 10,
    returnUnits: 2,
    status: "flagged",
    lineItem: {
      name: "Frozen produce",
      manifestQuantity: 12,
      deliverableQuantity: 10,
      returnQuantity: 2,
      reason: "Damaged in staging",
      returnCrate: "R-04",
    },
    loaderNote:
      "S. Fernando: 2 damaged in staging. Sealed in return crate R-04.",
  },
  {
    id: "LG4",
    label: "Remaining stops · 1,185 units",
    manifestUnits: 1185,
    deliverableUnits: 1185,
    returnUnits: 0,
    status: "matches",
    coveredOutletIds: ["OUT042", "OUT052", "OUT055", "OUT061", "OUT064"],
  },
];

export const LOAD_SUMMARY = {
  groupCount: LOAD_REVIEW_GROUPS.length,
  flaggedCount: LOAD_REVIEW_GROUPS.filter((group) => group.status === "flagged").length,
  manifestUnits: sumNumbers(LOAD_REVIEW_GROUPS.map((group) => group.manifestUnits)),
  deliverableUnits: sumNumbers(LOAD_REVIEW_GROUPS.map((group) => group.deliverableUnits)),
  returnUnits: sumNumbers(LOAD_REVIEW_GROUPS.map((group) => group.returnUnits)),
};

export const OUT047_CHECKLIST_ITEMS = [
  {
    id: "OUT047-DAIRY",
    name: "Dairy crate",
    quantity: 8,
    temp: "Chilled · 2–5°C",
    defaultState: "pending" as const,
  },
  {
    id: "OUT047-FROZEN",
    name: "Frozen produce",
    quantity: 5,
    temp: "Keep sealed until handover",
    defaultState: "pending" as const,
  },
  {
    id: "OUT047-DRY",
    name: "Dry groceries",
    quantity: 12,
    temp: "Ambient",
    defaultState: "pending" as const,
  },
];

export const OUT058_PARTIAL = {
  outletId: "OUT058",
  outletName: "Waypoint Fresh Kandy Hills",
  handedOver: 10,
  manifest: 12,
  returnItems: [
    {
      name: "Frozen produce",
      quantity: 2,
      reason: "Damaged",
      returnCrate: "R-04",
    },
  ],
  arrivalTime: "07:12",
  finishTime: "07:55",
};

export const ROUTE_UPDATE = {
  dispatcherTime: "06:41",
  headline: "OUT061 is now next",
  body:
    "Dispatcher resequenced your remaining route to protect the delivery window. Your loaded goods and saved records are unchanged.",
  changes: [
    {
      type: "moved_next" as const,
      outletId: "OUT061",
      outletName: "Waypoint Fresh Peradeniya",
      fromSeq: 7,
      toSeq: 3,
    },
    {
      type: "moved_later" as const,
      outletId: "OUT052",
      outletName: "Waypoint Fresh Kandy City Centre",
      fromSeq: 4,
      toSeq: 6,
    },
  ],
  newEta: "06:55",
  window: "06:45–08:00",
  reassurance: "Saved deliveries remain safe. Only your remaining sequence changes.",
  primary: "Accept update",
};

export const SYNC_REVIEW = {
  outletId: "OUT058",
  outletName: "Waypoint Fresh Kandy Hills",
  status: "in review" as const,
  banner: "Your field record is preserved.",
  yourRecord: {
    label: "YOUR RECORD",
    sublabel: "Confirmed in the field",
    arrived: "07:12",
    items: "10 items handed over",
    proof: "Photo · manager PIN",
  },
  dispatcherView: {
    label: "DISPATCHER / STORE VIEW",
    sublabel: "For your context — not your decision",
    assignment: `Reassigned to ${REASSIGN_VEHICLE.id}`,
    storeReport: "Store reported not received",
  },
  body:
    "Your field evidence is preserved. We detected a difference between your delivery record and dispatch’s update. Send your record so dispatch can compare both versions.",
  primary: "My delivery stands — send for review",
  secondaryAdd: "Add note or photo",
  secondaryCall: "Call dispatcher",
  quietEscape: "I didn’t actually deliver this — correct my record",
};

export const RECORD_SENT = {
  outletId: "OUT058",
  title: "Record sent for review",
  subtitle: "OUT058 · evidence protected",
  body:
    "Your delivery record has been sent to dispatch for review. Its evidence remains attached and protected.",
  preservedTitle: "Evidence is preserved",
  preservedBody:
    "The photo and manager PIN stay attached to OUT058 while dispatch and the store manager compare records.",
  photoLine: "Delivery photo preserved · Captured 07:13 · attached to review",
  pinLine: "Manager PIN verified · Field confirmation · protected",
  continueLine:
    "You can continue your route — this won’t block your next stop.",
  primary: "Back to route",
  secondary: "View sync queue",
};

export const OUTLET_CLOSED = {
  outletId: "OUT052",
  outletName: "Waypoint Fresh Kandy City Centre",
  reason: "Mall bay unavailable",
  body: "The rear bay is closed and security cannot grant access.",
  affectedItems: [
    { name: "Dairy crate", quantity: 1, action: "Return to depot" },
    { name: "Frozen produce", quantity: 2, action: "Return to depot" },
  ],
  returnCrate: "R-07",
  destination: "Kandy hub depot",
  handover: "Returns desk · bay 3",
  result: "Return 3 items to depot",
};

export const RETURN_DEPOT = {
  sourceOutletId: "OUT058",
  sourceOutletName: "Waypoint Fresh Kandy Hills",
  reason: "Damaged",
  items: [
    {
      name: "Frozen produce",
      quantity: 2,
    },
  ],
  returnCrate: "R-04",
  destination: "Kandy hub depot",
  eta: "09:42",
  handover: "Returns desk · bay 3",
};

export const DEPOT_RETURN = {
  location: "Kandy hub · bay 3",
  officer: "S. Fernando",
  confirmedAt: "09:51",
  items: [
    {
      name: "Frozen produce",
      quantity: 2,
    },
  ],
  returnCrate: "R-04",
  condition: "Seal intact",
  officerPin: "Confirmed",
};

export const TRIP_COMPLETE = {
  tripLabel: "Trip 1 · Fresh · Kandy",
  title: "Trip 1 complete",
  subtitle: "All route records are synced and ready for depot review.",
  delivered: TRIP_1.deliveredCount,
  partial: TRIP_1.partialCount,
  failed: TRIP_1.failedCount,
  finishTime: "09:54",
  distance: "128 km",
  records: "All synced",
  totalTripTime: "3h 42m",
  budgetStatus: "UNDER BUDGET",
  fuelEconomy: "9.4 km/L",
  fuelUsed: "13.6 L",
  remainingFuel: "28.4 L",
  routeRecap: [
    {
      outletId: "OUT042",
      outletName: "Waypoint Fresh Gampola",
      outcome: "Delivered",
      time: "05:58",
    },
    {
      outletId: "OUT047",
      outletName: "Waypoint Fresh Kandy Town",
      outcome: "Delivered",
      time: "06:34",
    },
    {
      outletId: "OUT058",
      outletName: "Waypoint Fresh Kandy Hills",
      outcome: "Partial",
      time: "07:55",
      suffix: "2 return",
    },
  ],
  remainingRecapCount: 5,
  returnGuidance:
    "Next Step: Please proceed back to Kandy hub depot. Expected Return ETA: 09:42 AM.",
  forwardCta: "START TRIP 2 PREPARATION",
  forwardCaption: "Next: Trip 2 — Style Kandy, 5 stops",
};

export const DAY_SUMMARY = {
  title: "Day confirmed",
  subtitle: "A simple record of completed work—not a performance score.",
  driver: DRIVER.name,
  vehicle: VEHICLE.id,
  depot: VEHICLE.depot,
  shift: DRIVER.shift,
  trips: "2 completed",
  stops: "13 visited",
  deliveries: "12 complete · 1 partial",
  returns: "2 items confirmed",
  sync: "All records current",
  closing: "This record was saved to your driver file and sent to dispatch.",
};

export const CHAT_QUICK_REPLIES = [
  "On my way.",
  "5 minutes away.",
  "I’ve arrived.",
  "At the loading bay.",
  "Need access.",
  "Who can receive?",
] as const;

export const CONTACT_DISPATCH_PRESETS = [
  "Running late",
  "Load discrepancy",
  "Outlet inaccessible",
  "Vehicle issue",
] as const;

export interface GeoPoint {
  lat: number;
  lng: number;
}

export const KANDY_HUB_COORDS: GeoPoint = { lat: 7.2906, lng: 80.6337 };

export const STOP_COORDS: Record<string, GeoPoint> = {
  OUT042: { lat: 7.1666, lng: 80.5666 },
  OUT047: { lat: 7.2931, lng: 80.6350 },
  OUT049: { lat: 7.2936, lng: 80.6360 },
  OUT052: { lat: 7.2941, lng: 80.6380 },
  OUT055: { lat: 7.2880, lng: 80.6200 },
  OUT058: { lat: 7.2850, lng: 80.6250 },
  OUT061: { lat: 7.2667, lng: 80.6000 },
  OUT064: { lat: 7.0500, lng: 80.5333 },
  OUT070: { lat: 7.2941, lng: 80.6380 },
  OUT071: { lat: 7.1666, lng: 80.5666 },
  OUT072: { lat: 7.2936, lng: 80.6360 },
  OUT073: { lat: 7.2667, lng: 80.6000 },
  OUT074: { lat: 7.0500, lng: 80.5333 },
};

export function getStopCoords(outletId: string): GeoPoint {
  return STOP_COORDS[outletId] || KANDY_HUB_COORDS;
}

export const ROUTE_UPDATED_SEQUENCE = [
  "OUT042",
  "OUT047",
  "OUT061",
  "OUT049",
  "OUT055",
  "OUT052",
  "OUT058",
  "OUT064",
];

export const ISSUE_WIZARD_CATEGORIES = [
  { id: "delay", label: "Delay", icon: "clock" },
  { id: "load", label: "Load issue", icon: "package" },
  { id: "access", label: "Access", icon: "lock" },
  { id: "vehicle", label: "Vehicle", icon: "truck" },
  { id: "other", label: "Other", icon: "more" },
] as const;
