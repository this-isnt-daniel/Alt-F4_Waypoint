/**
 * Waypoint Store Manager (Style) — Mock Orders & History Data
 */

export const ACTIVE_ORDERS = [
  {
    id: 'STY-2091',
    deliveryDate: 'today',
    placedAt: '2026-09-28T07:30:00',
    type: 'Apparel Restock',
    tempClass: 'ambient',
    status: 'out-for-delivery',
    activeStage: 3,
    vehicle: 'VH-30302',
    driver: { name: 'Rohan Wickramasinghe', phone: '+94 71 890 1234' },
    expectedArrival: '8:45 AM',
    eta: '8:40 AM',
    totalUnits: 45,
    items: [
      { name: 'Classic Oxford Cotton Button-Down (M · White)', qty: 15, unit: 'pc' },
      { name: 'Smart Stretch Slim Chinos (32 · Khaki)',        qty: 12, unit: 'pc' },
      { name: 'Silk-Touch Collared Blouse (S · Ivory)',        qty: 10, unit: 'pc' },
      { name: 'Minimalist White Leather Sneaker (EU 42)',      qty: 8,  unit: 'pc' },
    ],
  },
  {
    id: 'STY-2088',
    deliveryDate: 'today',
    placedAt: '2026-09-28T06:15:00',
    type: 'Footwear & Accessories',
    tempClass: 'ambient',
    status: 'loaded',
    activeStage: 2,
    vehicle: 'VH-30301',
    driver: { name: 'Kamal Perera', phone: '+94 77 234 5678' },
    expectedArrival: '9:30 AM',
    eta: null,
    totalUnits: 36,
    items: [
      { name: 'Minimalist White Leather Sneaker (EU 41)', qty: 10, unit: 'pc' },
      { name: 'Full-Grain Italian Leather Belt (34)',     qty: 12, unit: 'pc' },
      { name: 'Organic Cotton Crew Socks 3-Pack',        qty: 14, unit: 'pack' },
    ],
  },
  {
    id: 'STY-2104',
    deliveryDate: 'Tomorrow · Oct 1',
    placedAt: '2026-09-29T10:00:00',
    type: "Women's Collection Autumn",
    tempClass: 'ambient',
    status: 'confirmed',
    activeStage: 0,
    vehicle: null,
    driver: null,
    expectedArrival: '8:45 AM',
    eta: null,
    totalUnits: 32,
    totalProducts: 8,
    items: [],
  },
  {
    id: 'STY-2110',
    deliveryDate: 'Oct 2',
    placedAt: '2026-09-29T11:30:00',
    type: 'Outerwear & Coats',
    tempClass: 'ambient',
    status: 'planned',
    activeStage: 1,
    vehicle: null,
    driver: null,
    expectedArrival: '9:15 AM',
    eta: null,
    totalUnits: 20,
    totalProducts: 5,
    items: [],
  }
];

export const DEFERRED_ORDERS = [
  {
    id: 'STY-2075',
    type: 'Outerwear & Coats',
    originalDate: 'Thu, Oct 1',
    newDate: 'Fri, Oct 2',
    reason: 'Garment bag protective packaging shortage',
    reasonDetail: 'Hanging garment carrier boxes required for structured trench coats were allocated to flagship store first. Dispatched on Friday route.',
    deferralCount: 1,
    items: [
      { name: 'Double-Breasted Heritage Trench Coat', ordered: 6, unit: 'pc' },
    ],
  },
];

export const ORDER_STAGES = [
  { key: 'confirmed',        label: 'Confirmed'        },
  { key: 'planned',          label: 'Planned'          },
  { key: 'loaded',           label: 'Loaded'           },
  { key: 'out-for-delivery', label: 'Out for delivery' },
  { key: 'delivered',        label: 'Delivered'        },
];

export function getStageIndex(status) {
  return ORDER_STAGES.findIndex((s) => s.key === status);
}

export const ORDER_HISTORY = [
  {
    id: 'STY-2060',
    date: 'Sep 27',
    displayDate: 'Saturday, Sep 27',
    type: "Men's Collection",
    status: 'delivered',
    totalOrdered: 28,
    totalReceived: 28,
    receipt: 'confirmed',
    issues: [],
  },
  {
    id: 'STY-2052',
    date: 'Sep 25',
    displayDate: 'Thursday, Sep 25',
    type: 'Dresses & Blouses',
    status: 'delivered',
    totalOrdered: 24,
    totalReceived: 23,
    receipt: 'partial',
    issues: [
      {
        item: 'Elegance Midi Wrap Dress (M · Emerald)',
        ordered: 8,
        received: 7,
        type: 'short',
        loaderNote: '1 garment tag damaged in distribution hanger sorting — replaced in upcoming batch',
      },
    ],
  },
  {
    id: 'STY-2041',
    date: 'Sep 24',
    displayDate: 'Wednesday, Sep 24',
    type: 'Basics & Essentials',
    status: 'delivered',
    totalOrdered: 40,
    totalReceived: 40,
    receipt: 'confirmed',
    note: 'Weekend promo stock replenishment',
    issues: [],
  },
];

export const ORDER_CUTOFF = {
  hour: 16,
  minute: 0,
  label: '4:00 PM',
  nextDelivery: 'Tomorrow · 8:45 AM',
};
