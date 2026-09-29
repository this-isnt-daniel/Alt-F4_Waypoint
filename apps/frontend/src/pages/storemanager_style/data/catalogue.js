/**
 * Waypoint Store Manager (Style) — Product Catalogue
 * Hierarchy: Category → Subcategory → Product (→ Variants)
 *
 * Clothes, apparel & fashion items.
 * quantityType: 'count' (fixed integer quantities)
 */

export const CATEGORIES = [
  {
    id: 'mens-collection',
    name: "Men's Apparel",
    description: 'Shirts, polos, trousers & denim',
    icon: 'Shirt',
    subcategories: [
      {
        id: 'shirts-polos',
        name: 'Shirts & Polos',
        showImages: true,
        products: [
          { id: 'MSH-001', name: 'Classic Oxford Cotton Button-Down', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · White', 'M · White', 'L · White', 'XL · White', 'M · Light Blue', 'L · Light Blue'] },
          { id: 'MSH-002', name: 'Premium Pique Polo Shirt',          quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Navy', 'M · Navy', 'L · Navy', 'M · Forest Green', 'L · Burgundy'] },
          { id: 'MSH-003', name: 'Relaxed Fit French Linen Shirt',   quantityType: 'count', unit: 'pc', packSize: 1, variants: ['M · Sand Beige', 'L · Sand Beige', 'M · Sage', 'L · White'] },
          { id: 'MSH-004', name: 'Heavyweight Cotton Crewneck Tee',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Black', 'M · Black', 'L · Black', 'M · White', 'L · Heather Gray'] },
        ],
      },
      {
        id: 'trousers-denim',
        name: 'Trousers & Denim',
        showImages: true,
        products: [
          { id: 'MTR-001', name: 'Smart Stretch Slim Chinos',        quantityType: 'count', unit: 'pc', packSize: 1, variants: ['30 · Khaki', '32 · Khaki', '34 · Khaki', '32 · Navy', '34 · Olive'] },
          { id: 'MTR-002', name: 'Selvedge Straight Leg Denim Jeans', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['30 · Indigo', '32 · Indigo', '34 · Indigo', '32 · Washed Black'] },
          { id: 'MTR-003', name: 'Pleated Formal Wool-Blend Trousers', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['32 · Charcoal', '34 · Charcoal', '32 · Navy'] },
          { id: 'MTR-004', name: 'Ripstop Utility Cargo Pants',       quantityType: 'count', unit: 'pc', packSize: 1, variants: ['M · Dark Olive', 'L · Dark Olive', 'M · Black'] },
        ],
      },
    ],
  },

  {
    id: 'womens-collection',
    name: "Women's Apparel",
    description: 'Blouses, dresses, knitwear & skirts',
    icon: 'ShoppingBag',
    subcategories: [
      {
        id: 'blouses-knitwear',
        name: 'Blouses & Knitwear',
        showImages: true,
        products: [
          { id: 'WBL-001', name: 'Silk-Touch Collared Blouse',        quantityType: 'count', unit: 'pc', packSize: 1, variants: ['XS · Ivory', 'S · Ivory', 'M · Ivory', 'S · Champagne', 'M · Midnight'] },
          { id: 'WBL-002', name: 'Breezy Linen Button-Front Top',     quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Oatmeal', 'M · Oatmeal', 'L · Terracotta'] },
          { id: 'WBL-003', name: 'Ribbed Fine Knit Long-Sleeve',      quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Black', 'M · Black', 'M · Camel', 'L · Cream'] },
          { id: 'WBL-004', name: 'Cashmere-Blend Crewneck Pullover',   quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Powder Blue', 'M · Oatmeal', 'L · Charcoal'] },
        ],
      },
      {
        id: 'dresses-skirts',
        name: 'Dresses & Skirts',
        showImages: true,
        products: [
          { id: 'WDR-001', name: 'Elegance Midi Wrap Dress',          quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Emerald', 'M · Emerald', 'L · Emerald', 'M · Navy Florals'] },
          { id: 'WDR-002', name: 'Tiered Linen Summer Sundress',      quantityType: 'count', unit: 'pc', packSize: 1, variants: ['XS · Soft Yellow', 'S · White', 'M · White'] },
          { id: 'WSK-001', name: 'High-Waist Pleated Satin Midi Skirt', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Bronze', 'M · Bronze', 'M · Rose Gold'] },
          { id: 'WTR-001', name: 'Wide-Leg Tailored Linen Trousers',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['26 · Sand', '28 · Sand', '30 · Sand', '28 · Black'] },
        ],
      },
    ],
  },

  {
    id: 'outerwear-jackets',
    name: 'Outerwear & Coats',
    description: 'Jackets, blazers, trench coats & bombers',
    icon: 'Scissors',
    subcategories: [
      {
        id: 'jackets-blazers',
        name: 'Jackets & Blazers',
        showImages: false,
        products: [
          { id: 'JKT-001', name: 'Classic Denim Trucker Jacket',      quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Vintage Blue', 'M · Vintage Blue', 'L · Vintage Blue', 'L · Washed Black'] },
          { id: 'JKT-002', name: 'Water-Repellent Windbreaker Jacket', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['M · Forest Green', 'L · Forest Green', 'M · Black'] },
          { id: 'JKT-003', name: 'Tailored Single-Breasted Blazer',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['38R · Navy', '40R · Navy', '42R · Charcoal'] },
          { id: 'JKT-004', name: 'Satin-Lined Reversible Bomber',     quantityType: 'count', unit: 'pc', packSize: 1, variants: ['M · Army Green', 'L · Army Green', 'L · Midnight Black'] },
        ],
      },
      {
        id: 'coats',
        name: 'Overcoats & Trench',
        showImages: false,
        products: [
          { id: 'COT-001', name: 'Double-Breasted Heritage Trench Coat', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['S · Honey Tan', 'M · Honey Tan', 'L · Honey Tan'] },
          { id: 'COT-002', name: 'Wool Blend Minimalist Overcoat',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['M · Camel', 'L · Camel', 'L · Black'] },
        ],
      },
    ],
  },

  {
    id: 'footwear',
    name: 'Footwear & Shoes',
    description: 'Sneakers, loafers, boots & dress shoes',
    icon: 'Footprints',
    subcategories: [
      {
        id: 'sneakers-loafers',
        name: 'Sneakers & Loafers',
        showImages: false,
        products: [
          { id: 'FTW-001', name: 'Minimalist White Leather Sneaker',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['EU 40 · Crisp White', 'EU 41 · Crisp White', 'EU 42 · Crisp White', 'EU 43 · Crisp White'] },
          { id: 'FTW-002', name: 'Handcrafted Penny Loafer Suede',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['EU 41 · Snuff Suede', 'EU 42 · Snuff Suede', 'EU 43 · Dark Brown'] },
          { id: 'FTW-003', name: 'Canvas Low-Top Everyday Sneaker',  quantityType: 'count', unit: 'pc', packSize: 1, variants: ['EU 40 · Black', 'EU 41 · Black', 'EU 42 · Natural White'] },
        ],
      },
      {
        id: 'boots-formal',
        name: 'Boots & Formal Shoes',
        showImages: false,
        products: [
          { id: 'FTW-004', name: 'Burnished Leather Chelsea Boots',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['EU 41 · Cognac', 'EU 42 · Cognac', 'EU 43 · Black'] },
          { id: 'FTW-005', name: 'Oxford Cap-Toe Leather Shoes',      quantityType: 'count', unit: 'pc', packSize: 1, variants: ['EU 41 · Black Box Calf', 'EU 42 · Black Box Calf'] },
        ],
      },
    ],
  },

  {
    id: 'accessories-leather',
    name: 'Accessories & Leather',
    description: 'Belts, bags, scarves & eyewear',
    icon: 'Tag',
    subcategories: [
      {
        id: 'leather-accessories',
        name: 'Leather Goods & Bags',
        showImages: false,
        products: [
          { id: 'ACC-001', name: 'Full-Grain Italian Leather Belt',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['32 · Dark Brown', '34 · Dark Brown', '36 · Black'] },
          { id: 'ACC-002', name: 'Slim Bifold Leather Card Wallet',    quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Caramel Tan', 'Midnight Black'] },
          { id: 'ACC-003', name: 'Heavy Canvas Overnight Weekend Duffle', quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Olive Drab / Leather Trim', 'Navy Blue / Tan Trim'] },
          { id: 'ACC-004', name: 'Everyday Minimalist Tote Bag',      quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Natural Canvas', 'Black Canvas'] },
        ],
      },
      {
        id: 'caps-scarves',
        name: 'Hats, Caps & Scarves',
        showImages: false,
        products: [
          { id: 'ACC-005', name: 'Washed Cotton Twill Dad Cap',       quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Khaki', 'Navy', 'Faded Green', 'Black'] },
          { id: 'ACC-006', name: 'Fine Merino Wool Ribbed Beanie',     quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Charcoal Gray', 'Oatmeal', 'Navy'] },
          { id: 'ACC-007', name: '100% Silk Printed Neck Scarf',      quantityType: 'count', unit: 'pc', packSize: 1, variants: ['Floral Navy', 'Geometric Gold'] },
        ],
      },
    ],
  },

  {
    id: 'basics-socks',
    name: 'Basics & Loungewear',
    description: 'Organic socks, tees & loungewear',
    icon: 'Sparkles',
    subcategories: [
      {
        id: 'socks-underwear',
        name: 'Socks & Essentials',
        showImages: false,
        products: [
          { id: 'BSC-001', name: 'Organic Combed Cotton Crew Socks 3-Pack', quantityType: 'count', unit: 'pack', packSize: 1, variants: ['White Pack', 'Black Pack', 'Assorted Earth Tones'] },
          { id: 'BSC-002', name: 'No-Show Invisible Loafer Socks 3-Pack',   quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Black / Gray', 'Natural Nude'] },
          { id: 'BSC-003', name: 'Breathable Modal Loungewear Shorts',       quantityType: 'count', unit: 'pc', packSize: 1, variants: ['M · Heather Gray', 'L · Heather Gray', 'M · Navy'] },
          { id: 'BSC-004', name: 'Supima Cotton Crew Undershirt 2-Pack',     quantityType: 'count', unit: 'pack', packSize: 1, variants: ['M · White', 'L · White', 'XL · White'] },
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
