/**
 * Waypoint Store Manager (Tech) — Product Catalogue
 * Hierarchy: Category → Subcategory → Product (→ Variants)
 *
 * quantityType: 'count' (fixed integer quantities)
 */

export const CATEGORIES = [
  {
    id: 'laptops-computers',
    name: 'Laptops & Computers',
    description: 'Ultrabooks, workstations & displays',
    icon: 'Laptop',
    subcategories: [
      {
        id: 'laptops',
        name: 'Laptops & Notebooks',
        showImages: true,
        products: [
          { id: 'LPT-001', name: 'Waypoint SlimBook 14"', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Core i5 · 16GB / 512GB', 'Core i7 · 32GB / 1TB'] },
          { id: 'LPT-002', name: 'ProBook Studio 16"',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['M3 Pro · 18GB / 512GB', 'M3 Max · 36GB / 1TB'] },
          { id: 'LPT-003', name: 'Apex Gaming Laptop 15.6"', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['RTX 4060 · 16GB / 1TB', 'RTX 4070 · 32GB / 1TB'] },
          { id: 'LPT-004', name: 'CloudBook Go 11.6"',     quantityType: 'count', unit: 'pc', packSize: 1, variants: ['64GB eMMC', '128GB SSD'] },
        ],
      },
      {
        id: 'monitors-desktops',
        name: 'Monitors & Displays',
        showImages: true,
        products: [
          { id: 'MON-001', name: 'UltraFine 27" 4K IPS Monitor', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Matte Black', 'Silver Stand'] },
          { id: 'MON-002', name: 'Curved Gaming 34" WQHD 165Hz',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Standard HDR400'] },
          { id: 'MON-003', name: 'Compact Office 24" FHD 100Hz',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Black'] },
          { id: 'DSK-001', name: 'Waypoint Mini Desktop PC',     quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Ryzen 5 · 16GB / 512GB', 'Ryzen 7 · 32GB / 1TB'] },
        ],
      },
    ],
  },

  {
    id: 'mobile-tablets',
    name: 'Smartphones & Tablets',
    description: 'Phones, tablets, wearables & accessories',
    icon: 'Smartphone',
    subcategories: [
      {
        id: 'smartphones',
        name: 'Smartphones',
        showImages: true,
        products: [
          { id: 'PHN-001', name: 'Waypoint Phone 15 Pro', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Titanium Gray · 256GB', 'Titanium Black · 512GB', 'Titanium White · 256GB'] },
          { id: 'PHN-002', name: 'Waypoint Phone 15',     quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Midnight · 128GB', 'Starlight · 128GB', 'Blue · 256GB'] },
          { id: 'PHN-003', name: 'Nexus Lite 5G',          quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Charcoal · 128GB', 'Sage Green · 128GB'] },
        ],
      },
      {
        id: 'tablets-wearables',
        name: 'Tablets & Wearables',
        showImages: false,
        products: [
          { id: 'TAB-001', name: 'Waypoint Tab 11" OLED',   quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Wi-Fi · 128GB', 'Wi-Fi + 5G · 256GB'] },
          { id: 'TAB-002', name: 'Active Stylus Pen Gen 2', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['White', 'Matte Black'] },
          { id: 'WAT-001', name: 'Pro Watch Ultra 49mm',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Titanium / Orange Loop', 'Titanium / Midnight Band'] },
          { id: 'WAT-002', name: 'Pulse Smart Fitness Band',quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Black Strap', 'Navy Strap'] },
        ],
      },
    ],
  },

  {
    id: 'audio-sound',
    name: 'Audio & Acoustics',
    description: 'Headphones, ANC earbuds & speakers',
    icon: 'Headphones',
    subcategories: [
      {
        id: 'headphones',
        name: 'Headphones',
        showImages: true,
        products: [
          { id: 'AUD-001', name: 'SilencePro ANC Over-Ear Headphones', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Matte Black', 'Silver Sand', 'Midnight Blue'] },
          { id: 'AUD-002', name: 'Studio Monitor Reference Headphones',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['32 Ohm', '80 Ohm'] },
          { id: 'AUD-003', name: 'Wireless Casual On-Ear Headset',       quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Black', 'Cream White'] },
        ],
      },
      {
        id: 'earbuds-speakers',
        name: 'Earbuds & Speakers',
        showImages: false,
        products: [
          { id: 'EBD-001', name: 'True Wireless ANC Earbuds Pro',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Glossy White', 'Matte Carbon'] },
          { id: 'EBD-002', name: 'Sport Fit Water-Resistant Buds', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Neon Coral', 'Graphite'] },
          { id: 'SPK-001', name: 'Boom360 Portable Waterproof Speaker', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Black', 'Forest Green', 'Ocean Blue'] },
          { id: 'SPK-002', name: 'Desktop Hi-Fi Stereo Soundbar',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Charcoal Gray'] },
        ],
      },
    ],
  },

  {
    id: 'storage-memory',
    name: 'Storage & Drives',
    description: 'External SSDs, NVMe drives & flash memory',
    icon: 'HardDrive',
    subcategories: [
      {
        id: 'portable-ssds',
        name: 'Portable SSDs & Flash Drives',
        showImages: false,
        products: [
          { id: 'SSD-001', name: 'Rugged USB 3.2 External SSD', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['1TB', '2TB', '4TB'] },
          { id: 'SSD-002', name: 'Pocket Slim USB-C Solid State Drive', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['500GB', '1TB'] },
          { id: 'FSH-001', name: 'Dual USB-A / Type-C Flash Drive', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['64GB', '128GB', '256GB'] },
          { id: 'MSD-001', name: 'High Endurance MicroSDXC Class 10', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['128GB', '256GB', '512GB'] },
        ],
      },
      {
        id: 'internal-storage',
        name: 'Internal Storage & Components',
        showImages: false,
        products: [
          { id: 'M2S-001', name: 'PCIe 4.0 NVMe M.2 SSD 7000MB/s', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['1TB', '2TB'] },
          { id: 'RAM-001', name: 'DDR5 5600MHz Desktop Memory Kit', quantityType: 'count', unit: 'pack', packSize: 1, variants: ['32GB (2x16GB)', '64GB (2x32GB)'] },
          { id: 'HDD-001', name: 'Enterprise 3.5" SATA NAS Hard Drive', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['4TB', '8TB', '12TB'] },
        ],
      },
    ],
  },

  {
    id: 'cables-power',
    name: 'Cables & Power',
    description: 'GaN chargers, power banks & fast cables',
    icon: 'Cable',
    subcategories: [
      {
        id: 'power-chargers',
        name: 'Fast Chargers & Banks',
        showImages: false,
        products: [
          { id: 'CHG-001', name: 'GaN Fast Wall Charger 65W Dual-Port', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['White', 'Black'] },
          { id: 'CHG-002', name: 'GaN Desktop Power Station 120W Quad', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Space Gray'] },
          { id: 'PBK-001', name: 'MagSafe Wireless Power Bank 10000mAh', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['White', 'Navy', 'Titanium'] },
          { id: 'PBK-002', name: 'High Capacity Power Bank 20000mAh 65W PD', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Black'] },
        ],
      },
      {
        id: 'cables-adapters',
        name: 'Cables & Adapters',
        showImages: false,
        products: [
          { id: 'CBL-001', name: 'Braided USB-C to USB-C 100W 2m Cable', quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Black', 'Silver Gray'] },
          { id: 'CBL-002', name: 'Thunderbolt 4 / USB4 40Gbps 1m Cable',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Black'] },
          { id: 'CBL-003', name: 'Ultra High Speed HDMI 2.1 8K/60Hz 2m',   quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Braided Black'] },
          { id: 'ADP-001', name: 'USB-C to HDMI 4K@60Hz Adapter Dongle',   quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Aluminum Shell'] },
        ],
      },
    ],
  },

  {
    id: 'peripherals-accessories',
    name: 'Peripherals & Docks',
    description: 'Keyboards, ergonomic mice & docking hubs',
    icon: 'Cpu',
    subcategories: [
      {
        id: 'input-devices',
        name: 'Keyboards & Mice',
        showImages: false,
        products: [
          { id: 'KBD-001', name: 'Mechanical Wireless Keyboard TKL RGB', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Linear Red Switch', 'Tactile Brown Switch'] },
          { id: 'KBD-002', name: 'Ultra-Slim Multi-Device Bluetooth Board', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Space Gray', 'Pale Gray'] },
          { id: 'MSE-001', name: 'Ergonomic Vertical Wireless Mouse',     quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Graphite', 'Off-White'] },
          { id: 'MSE-002', name: 'Precision Wireless Scroll Mouse',       quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Matte Black', 'Silver'] },
        ],
      },
      {
        id: 'docks-stands',
        name: 'Docks, Hubs & Stands',
        showImages: false,
        products: [
          { id: 'DCK-001', name: 'USB-C 8-in-1 Dual Display Hub Dock', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Space Gray Aluminum'] },
          { id: 'DCK-002', name: 'Thunderbolt 4 Pro Dock Station 14-Port', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Silver Aluminum'] },
          { id: 'STN-001', name: 'Adjustable Aluminum Laptop Riser Stand', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Silver', 'Space Gray'] },
        ],
      },
    ],
  },

  {
    id: 'networking-smart',
    name: 'Networking & Smart Home',
    description: 'Routers, mesh nodes & IoT security',
    icon: 'Wifi',
    subcategories: [
      {
        id: 'networking',
        name: 'Routers & Switches',
        showImages: false,
        products: [
          { id: 'NET-001', name: 'Wi-Fi 6 AX3000 Dual-Band Gigabit Router', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Black 4-Antenna'] },
          { id: 'NET-002', name: 'Whole-Home Tri-Band Mesh System 2-Pack', quantityType: 'count', unit: 'pack', packSize: 1, variants: ['White Node'] },
          { id: 'NET-003', name: 'Gigabit 8-Port Unmanaged Desktop Switch', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Metal Casing'] },
        ],
      },
      {
        id: 'smart-devices',
        name: 'Smart Home & Security',
        showImages: false,
        products: [
          { id: 'CAM-001', name: '2K Pan-Tilt Indoor Security Wi-Fi Cam', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['White'] },
          { id: 'PLG-001', name: 'Smart Wi-Fi Plug with Power Monitor', quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Single Pack', '2-Pack Kit'] },
        ],
      },
    ],
  },
];

// ── Flatten helpers ──────────────────────────────────────

export const ALL_PRODUCTS = CATEGORIES.flatMap((cat) =>
  cat.subcategories.flatMap((sub) =>
    sub.products.flatMap((p) => {
      const baseProduct = {
        ...p,
        categoryId: cat.id,
        categoryName: cat.name,
        subcategoryId: sub.id,
        subcategoryName: sub.name,
      };

      if (p.variants && p.variants.length > 0) {
        return p.variants.map((v) => ({
          ...baseProduct,
          variant: v,
          searchKey: `${baseProduct.id} ${baseProduct.name} ${v} ${cat.name} ${sub.name}`.toLowerCase(),
        }));
      }

      return [{
        ...baseProduct,
        variant: null,
        searchKey: `${baseProduct.id} ${baseProduct.name} ${cat.name} ${sub.name}`.toLowerCase(),
      }];
    })
  )
);

export function searchProducts(query) {
  const q = query.toLowerCase().trim();
  if (!q) return [];
  return ALL_PRODUCTS.filter((p) => p.searchKey.includes(q));
}

/** 
 * formatQuantity
 */
export function formatQuantity(qty, quantityType, unit) {
  if (!qty) return '';
  const isPlural = qty !== 1;
  let displayUnit = unit;
  if (isPlural) {
    if (unit === 'box') displayUnit = 'boxes';
    else if (unit === 'pc') displayUnit = 'pcs';
    else displayUnit = unit + 's';
  }
  return `${qty} ${displayUnit}`;
}
