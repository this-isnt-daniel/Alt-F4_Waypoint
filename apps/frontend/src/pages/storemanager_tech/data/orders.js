/**
 * Waypoint Store Manager (Tech) — Mock Orders & History Data
 */

export const ACTIVE_ORDERS = [
  {
    id: 'TECH-8401',
    deliveryDate: 'today',
    placedAt: '2026-09-28T07:15:00',
    type: 'High-Value Electronics',
    tempClass: 'ambient',
    status: 'out-for-delivery',
    activeStage: 3,
    vehicle: 'VH-30302',
    driver: { name: 'Rohan Wickramasinghe', phone: '+94 71 890 1234' },
    expectedArrival: '10:30 AM',
    eta: '10:24 AM',
    totalUnits: 38,
    items: [
      { name: 'Rugged USB 3.2 External SSD (1TB)', qty: 15, unit: 'pc' },
      { name: 'GaN Fast Wall Charger 65W (Black)',  qty: 15, unit: 'pc' },
      { name: 'SilencePro ANC Over-Ear Headphones', qty: 8,  unit: 'pc' },
    ],
  },
  {
    id: 'TECH-8395',
    deliveryDate: 'today',
    placedAt: '2026-09-28T06:00:00',
    type: 'Peripherals & Cables',
    tempClass: 'ambient',
    status: 'loaded',
    activeStage: 2,
    vehicle: 'VH-30301',
    driver: { name: 'Kamal Perera', phone: '+94 77 234 5678' },
    expectedArrival: '11:15 AM',
    eta: null,
    totalUnits: 42,
    items: [
      { name: 'Braided USB-C to USB-C 100W 2m Cable', qty: 25, unit: 'pack' },
      { name: 'Mechanical Wireless Keyboard TKL RGB',  qty: 10, unit: 'pc'   },
      { name: 'Ergonomic Vertical Wireless Mouse',     qty: 7,  unit: 'pc'   },
    ],
  },
  {
    id: 'TECH-8412',
    deliveryDate: 'Tomorrow · Oct 1',
    placedAt: '2026-09-29T09:30:00',
    type: 'Laptops & Displays',
    tempClass: 'ambient',
    status: 'confirmed',
    activeStage: 0,
    vehicle: null,
    driver: null,
    expectedArrival: '8:45 AM',
    eta: null,
    totalUnits: 20,
    totalProducts: 6,
    items: [],
  },
  {
    id: 'TECH-8420',
    deliveryDate: 'Oct 2',
    placedAt: '2026-09-29T11:00:00',
    type: 'Smart Home & Audio',
    tempClass: 'ambient',
    status: 'planned',
    activeStage: 1,
    vehicle: null,
    driver: null,
    expectedArrival: '9:30 AM',
    eta: null,
    totalUnits: 18,
    totalProducts: 5,
    items: [],
  }
];

export const DEFERRED_ORDERS = [
  {
    id: 'TECH-8380',
    type: 'High-Value Electronics',
    originalDate: 'Thu, Oct 1',
    newDate: 'Fri, Oct 2',
    reason: 'Security cage capacity reached',
    reasonDetail: 'High-value locked cargo cage reached capacity on morning dispatch route. Scheduled for primary cage slot on tomorrow morning flight dispatch.',
    deferralCount: 1,
    items: [
      { name: 'ProBook Studio 16" (M3 Pro)', ordered: 5, unit: 'pc' },
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
    id: 'TECH-8370',
    date: 'Sep 27',
    displayDate: 'Saturday, Sep 27',
    type: 'Displays & Storage',
    status: 'delivered',
    totalOrdered: 24,
    totalReceived: 24,
    receipt: 'confirmed',
    issues: [],
  },
  {
    id: 'TECH-8355',
    date: 'Sep 25',
    displayDate: 'Thursday, Sep 25',
    type: 'Audio & Accessories',
    status: 'delivered',
    totalOrdered: 30,
    totalReceived: 29,
    receipt: 'partial',
    issues: [
      {
        item: 'True Wireless ANC Earbuds Pro',
        ordered: 10,
        received: 9,
        type: 'short',
        loaderNote: 'Factory seal compromised on 1 retail box — withheld at DC hub for QC inspection',
      },
    ],
  },
  {
    id: 'TECH-8340',
    date: 'Sep 24',
    displayDate: 'Wednesday, Sep 24',
    type: 'Cables & Power',
    status: 'delivered',
    totalOrdered: 50,
    totalReceived: 50,
    receipt: 'confirmed',
    note: 'Fast tracked restock',
    issues: [],
  },
];

export const ORDER_CUTOFF = {
  hour: 16,
  minute: 0,
  label: '4:00 PM',
  nextDelivery: 'Tomorrow · 8:45 AM',
};
