/**
 * Waypoint Store Manager — Mock Orders & History Data
 */

export const ACTIVE_ORDERS = [
  {
    id: 'ORD-1042',
    deliveryDate: 'today',
    placedAt: '2026-09-28T06:00:00',
    type: 'Chilled',
    tempClass: 'chilled',
    status: 'out-for-delivery',
    activeStage: 3,
    vehicle: 'VH-30302',
    driver: { name: 'Rohan Wickramasinghe', phone: '+94 71 890 1234' },
    expectedArrival: '7:40 AM',
    eta: '7:36 AM',
    totalUnits: 62,
    items: [
      { name: 'Fresh Milk 1L Full Cream', qty: 30, unit: 'carton' },
      { name: 'Butter 200g Salted',       qty: 12, unit: 'block'  },
      { name: 'Yoghurt 200g Plain',       qty: 20, unit: 'cup'    },
    ],
  },
  {
    id: 'ORD-1041',
    deliveryDate: 'today',
    placedAt: '2026-09-28T05:45:00',
    type: 'Dry',
    tempClass: 'ambient',
    status: 'loaded',
    activeStage: 2,
    vehicle: 'VH-30301',
    driver: { name: 'Kamal Perera', phone: '+94 77 234 5678' },
    expectedArrival: '7:40 AM',
    eta: null,
    totalUnits: 34,
    items: [
      { name: 'Cream Cracker 500g Munchee', qty: 12, unit: 'pack' },
      { name: 'Ceylon Black Tea 100 bags',   qty: 10, unit: 'box'  },
      { name: 'Rice 5kg Samba',              qty: 12, unit: 'bag'  },
    ],
  },
  {
    id: 'ORD-1043',
    deliveryDate: 'Tomorrow · Oct 1',
    placedAt: '2026-09-29T10:00:00',
    type: 'Dry + Chilled',
    tempClass: 'mixed',
    status: 'confirmed',
    activeStage: 0,
    vehicle: null,
    driver: null,
    expectedArrival: '7:40 AM',
    eta: null,
    totalUnits: 45,
    totalProducts: 18,
    items: [],
  },
  {
    id: 'ORD-1046',
    deliveryDate: 'Oct 2',
    placedAt: '2026-09-29T11:00:00',
    type: 'Chilled',
    tempClass: 'chilled',
    status: 'planned',
    activeStage: 1,
    vehicle: null,
    driver: null,
    expectedArrival: '8:10 AM',
    eta: null,
    totalUnits: 25,
    totalProducts: 12,
    items: [],
  }
];

export const DEFERRED_ORDERS = [
  {
    id: 'ORD-1038',
    type: 'Chilled',
    originalDate: 'Thu, Oct 1',
    newDate: 'Fri, Oct 2',
    reason: 'Fleet capacity short',
    reasonDetail: 'Fleet capacity was short ahead of the holiday period — Fresh outlets prioritised by order age. Your order has been moved to the next available slot.',
    deferralCount: 1,
    items: [
      { name: 'Fresh Milk 1L Full Cream', ordered: 8, unit: 'crate' },
    ],
  },
];

// 5-step order milestones
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
    id: 'ORD-1035',
    date: 'Sep 27',
    displayDate: 'Saturday, Sep 27',
    type: 'Dry + Chilled',
    status: 'delivered',
    totalOrdered: 32,
    totalReceived: 32,
    receipt: 'confirmed',
    issues: [],
  },
  {
    id: 'ORD-1029',
    date: 'Sep 25',
    displayDate: 'Thursday, Sep 25',
    type: 'Chilled',
    status: 'delivered',
    totalOrdered: 25,
    totalReceived: 23,
    receipt: 'partial',
    issues: [
      {
        item: 'Butter 200g Salted',
        ordered: 25,
        received: 23,
        type: 'short',
        loaderNote: 'Damaged during loading — 2 crates removed pre-departure',
      },
    ],
  },
  {
    id: 'ORD-1022',
    date: 'Sep 24',
    displayDate: 'Wednesday, Sep 24',
    type: 'Dry',
    status: 'delivered',
    totalOrdered: 18,
    totalReceived: 18,
    receipt: 'confirmed',
    note: 'Originally deferred from Sep 23',
    issues: [],
  },
  {
    id: 'ORD-1018',
    date: 'Sep 22',
    displayDate: 'Monday, Sep 22',
    type: 'Dry + Chilled',
    status: 'delivered',
    totalOrdered: 40,
    totalReceived: 40,
    receipt: 'confirmed',
    issues: [],
  },
  {
    id: 'ORD-1011',
    date: 'Sep 19',
    displayDate: 'Friday, Sep 19',
    type: 'Dry',
    status: 'delivered',
    totalOrdered: 28,
    totalReceived: 27,
    receipt: 'partial',
    issues: [
      {
        item: 'Cream Cracker 500g Munchee',
        ordered: 12,
        received: 11,
        type: 'short',
        loaderNote: null,
      },
    ],
  },
];

/** Cutoff config */
export const ORDER_CUTOFF = {
  hour: 16,     // 4:00 PM
  minute: 0,
  label: '4:00 PM',
  nextDelivery: 'Tomorrow · 7:40 AM',
};
