/**
 * Waypoint Store Manager — Product Catalogue
 * Hierarchy: Category → Subcategory → Product (→ Variants)
 *
 * quantityType: 'weight' (variable weight, step 0.5kg) | 'count' (fixed integer quantities)
 */

export const CATEGORIES = [
  {
    id: 'fresh-produce',
    name: 'Fresh Produce',
    description: 'Vegetables, fruits & herbs',
    icon: 'Leaf',
    subcategories: [
      {
        id: 'fruits',
        name: 'Fruits',
        showImages: true,
        products: [
          { id: 'FRT-001', name: 'Apple',      quantityType: 'weight', unit: 'kg', variants: ['Red', 'Green'] },
          { id: 'FRT-002', name: 'Banana',     quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'FRT-003', name: 'Orange',     quantityType: 'weight', unit: 'kg', variants: ['Navel', 'Valencia'] },
          { id: 'FRT-004', name: 'Papaya',     quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'FRT-005', name: 'Watermelon', quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'FRT-006', name: 'Pineapple',  quantityType: 'count',  unit: 'pc', variants: [], packSize: 1 },
          { id: 'FRT-007', name: 'Mango',      quantityType: 'weight', unit: 'kg', variants: ['Local', 'Imported'] },
          { id: 'FRT-008', name: 'Grapes',     quantityType: 'weight', unit: 'kg', variants: ['Red', 'Green'] },
        ],
      },
      {
        id: 'vegetables',
        name: 'Vegetables',
        showImages: true,
        products: [
          { id: 'VEG-001', name: 'Tomato',       quantityType: 'weight', unit: 'kg', variants: ['Local', 'Hybrid'] },
          { id: 'VEG-002', name: 'Carrot',       quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'VEG-003', name: 'Cabbage',      quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'VEG-004', name: 'Brinjal',      quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'VEG-005', name: 'Onion',        quantityType: 'weight', unit: 'kg', variants: ['Local', 'Imported'] },
          { id: 'VEG-006', name: 'Potato',       quantityType: 'weight', unit: 'kg', variants: ['Local', 'Imported'] },
          { id: 'VEG-007', name: 'Green Beans',  quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'VEG-008', name: 'Pumpkin',      quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'VEG-009', name: 'Green Chilli', quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'VEG-010', name: 'Garlic',       quantityType: 'weight', unit: 'kg', variants: ['Local', 'Imported'] },
          { id: 'VEG-011', name: 'Ginger',       quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'VEG-012', name: 'Leeks',        quantityType: 'weight', unit: 'kg', variants: [] },
        ],
      },
      {
        id: 'herbs',
        name: 'Herbs & Greens',
        showImages: false,
        products: [
          { id: 'HRB-001', name: 'Curry Leaves', quantityType: 'count', unit: 'bunch', variants: [], packSize: 1 },
          { id: 'HRB-002', name: 'Coriander',    quantityType: 'count', unit: 'bunch', variants: [], packSize: 1 },
          { id: 'HRB-003', name: 'Rampe',        quantityType: 'count', unit: 'bunch', variants: [], packSize: 1 },
          { id: 'HRB-004', name: 'Lemongrass',   quantityType: 'count', unit: 'bunch', variants: [], packSize: 1 },
        ],
      },
    ],
  },

  {
    id: 'rice-grains',
    name: 'Rice & Grains',
    description: 'Rice, flour & dry staples',
    icon: 'Wheat',
    subcategories: [
      {
        id: 'rice',
        name: 'Rice',
        showImages: false,
        products: [
          { id: 'RCE-001', name: 'Rice', quantityType: 'weight', unit: 'kg', variants: ['Nadu', 'Samba', 'Red Rice', 'Basmati', 'Keeri Samba'] },
        ],
      },
      {
        id: 'flour',
        name: 'Flour',
        showImages: false,
        products: [
          { id: 'FLR-001', name: 'Wheat Flour', quantityType: 'weight', unit: 'kg', variants: ['Plain', 'Self-Raising'] },
          { id: 'FLR-002', name: 'Rice Flour',  quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'FLR-003', name: 'Corn Flour',  quantityType: 'weight', unit: 'kg', variants: [] },
        ],
      },
      {
        id: 'cereals',
        name: 'Cereals & Oats',
        showImages: false,
        products: [
          { id: 'CRL-001', name: 'Oats',        quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Rolled', 'Instant'] },
          { id: 'CRL-002', name: 'Corn Flakes', quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'sugar-baking',
    name: 'Sugar & Baking',
    description: 'Sugar, salt & baking',
    icon: 'Cookie',
    subcategories: [
      {
        id: 'sweeteners',
        name: 'Sugar & Sweeteners',
        showImages: false,
        products: [
          { id: 'SGR-001', name: 'White Sugar', quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'SGR-002', name: 'Brown Sugar', quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'SGR-003', name: 'Jaggery',     quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'SGR-004', name: 'Honey',       quantityType: 'count',  unit: 'bottle', packSize: 1, variants: ['Local', 'Imported'] },
        ],
      },
      {
        id: 'salt-seasoning',
        name: 'Salt',
        showImages: false,
        products: [
          { id: 'SLT-001', name: 'Salt', quantityType: 'weight', unit: 'kg', variants: ['Iodised', 'Sea Salt', 'Rock Salt'] },
        ],
      },
      {
        id: 'baking',
        name: 'Baking',
        showImages: false,
        products: [
          { id: 'BKG-001', name: 'Baking Powder', quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'BKG-002', name: 'Yeast',         quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'BKG-003', name: 'Vanilla Essence', quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'cooking-essentials',
    name: 'Cooking Essentials',
    description: 'Oils, sauces & condiments',
    icon: 'Flame',
    subcategories: [
      {
        id: 'oils',
        name: 'Cooking Oils',
        showImages: false,
        products: [
          { id: 'OIL-001', name: 'Cooking Oil', quantityType: 'count', unit: 'bottle', packSize: 1, variants: ['Vegetable', 'Coconut', 'Sunflower'] },
        ],
      },
      {
        id: 'sauces',
        name: 'Sauces & Condiments',
        showImages: false,
        products: [
          { id: 'SOS-001', name: 'Soy Sauce',      quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'SOS-002', name: 'Chilli Sauce',   quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'SOS-003', name: 'Tomato Ketchup', quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'SOS-004', name: 'Coconut Milk',   quantityType: 'count', unit: 'can',    packSize: 1, variants: [] },
          { id: 'SOS-005', name: 'Vinegar',        quantityType: 'count', unit: 'bottle', packSize: 1, variants: ['White', 'Apple Cider'] },
        ],
      },
    ],
  },

  {
    id: 'pulses',
    name: 'Pulses & Dry Goods',
    description: 'Lentils, pulses & canned goods',
    icon: 'Circle',
    subcategories: [
      {
        id: 'lentils',
        name: 'Lentils & Pulses',
        showImages: false,
        products: [
          { id: 'PLS-001', name: 'Red Lentils',     quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'PLS-002', name: 'Green Gram',      quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'PLS-003', name: 'Chickpeas',       quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'PLS-004', name: 'Black-eyed Peas', quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'PLS-005', name: 'Parippu',         quantityType: 'weight', unit: 'kg', variants: [] },
        ],
      },
      {
        id: 'canned',
        name: 'Canned Goods',
        showImages: false,
        products: [
          { id: 'CAN-001', name: 'Canned Fish',     quantityType: 'count', unit: 'can', packSize: 1, variants: ['Tuna', 'Mackerel', 'Sardine'] },
          { id: 'CAN-002', name: 'Canned Tomatoes', quantityType: 'count', unit: 'can', packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'tea-beverages',
    name: 'Tea, Coffee & Beverages',
    description: 'Tea, coffee & drinks',
    icon: 'Coffee',
    subcategories: [
      {
        id: 'tea',
        name: 'Tea',
        showImages: false,
        products: [
          { id: 'TEA-001', name: 'Ceylon Black Tea', quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'TEA-002', name: 'Green Tea',        quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'TEA-003', name: 'Herbal Tea',       quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Ginger', 'Chamomile'] },
        ],
      },
      {
        id: 'coffee',
        name: 'Coffee',
        showImages: false,
        products: [
          { id: 'COF-001', name: 'Instant Coffee',  quantityType: 'count', unit: 'jar', packSize: 1, variants: ['Regular', 'Decaf'] },
          { id: 'COF-002', name: 'Ground Coffee',   quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
        ],
      },
      {
        id: 'drinks',
        name: 'Soft Drinks & Juices',
        showImages: false,
        products: [
          { id: 'DRK-001', name: 'Soft Drink', quantityType: 'count', unit: 'bottle', packSize: 1, variants: ['Cola', 'Orange', 'Cream Soda'] },
          { id: 'DRK-002', name: 'Water',      quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'DRK-003', name: 'Juice',      quantityType: 'count', unit: 'carton', packSize: 1, variants: ['Orange', 'Mango', 'Pineapple'] },
        ],
      },
    ],
  },

  {
    id: 'chilled-dairy',
    name: 'Chilled & Dairy',
    description: 'Milk, yoghurt, butter & cheese',
    icon: 'Milk',
    tempRequired: 'chilled',
    subcategories: [
      {
        id: 'milk',
        name: 'Milk',
        showImages: false,
        products: [
          { id: 'MLK-001', name: 'Fresh Milk',  quantityType: 'count', unit: 'bottle', packSize: 1, variants: ['Full Cream', 'Low Fat', 'Chocolate'] },
          { id: 'MLK-002', name: 'Milk Powder', quantityType: 'count', unit: 'pack',   packSize: 1, variants: ['Full Cream', 'Low Fat'] },
        ],
      },
      {
        id: 'dairy',
        name: 'Dairy Products',
        showImages: false,
        products: [
          { id: 'DRY-001', name: 'Butter',    quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Salted', 'Unsalted'] },
          { id: 'DRY-002', name: 'Yoghurt',   quantityType: 'count', unit: 'cup',  packSize: 1, variants: ['Plain', 'Strawberry', 'Mango'] },
          { id: 'DRY-003', name: 'Curd',      quantityType: 'count', unit: 'pot',  packSize: 1, variants: [] },
          { id: 'DRY-004', name: 'Cheese',    quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Cheddar', 'Processed'] },
          { id: 'DRY-005', name: 'Margarine', quantityType: 'count', unit: 'tub',  packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'meat-eggs',
    name: 'Meat & Eggs',
    description: 'Chicken, meat & eggs',
    icon: 'UtensilsCrossed',
    tempRequired: 'chilled',
    subcategories: [
      {
        id: 'chicken',
        name: 'Chicken',
        showImages: true,
        products: [
          { id: 'CHK-001', name: 'Whole Chicken',      quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'CHK-002', name: 'Chicken Breast',     quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'CHK-003', name: 'Chicken Drumsticks', quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'CHK-004', name: 'Sausages',           quantityType: 'count',  unit: 'pack', packSize: 1, variants: ['Chicken', 'Beef'] },
        ],
      },
      {
        id: 'eggs',
        name: 'Eggs',
        showImages: false,
        products: [
          { id: 'EGG-001', name: 'Eggs', quantityType: 'count', unit: 'tray', packSize: 30, variants: ['Large', 'Medium'] },
        ],
      },
    ],
  },

  {
    id: 'frozen',
    name: 'Frozen Foods',
    description: 'Frozen food & seafood',
    icon: 'Snowflake',
    tempRequired: 'frozen',
    subcategories: [
      {
        id: 'seafood',
        name: 'Seafood',
        showImages: false,
        products: [
          { id: 'SEA-001', name: 'Frozen Fish',   quantityType: 'weight', unit: 'kg', variants: ['Tuna', 'Tilapia', 'Salmon'] },
          { id: 'SEA-002', name: 'Frozen Prawns', quantityType: 'weight', unit: 'kg', variants: ['Small', 'Large'] },
          { id: 'SEA-003', name: 'Squid',         quantityType: 'weight', unit: 'kg', variants: [] },
        ],
      },
      {
        id: 'frozen-veg',
        name: 'Frozen Vegetables',
        showImages: false,
        products: [
          { id: 'FRZ-001', name: 'Mixed Vegetables', quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'FRZ-002', name: 'Frozen Peas',      quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'FRZ-003', name: 'Frozen Corn',      quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'bread-bakery',
    name: 'Bread & Bakery',
    description: 'Bread, rolls & baked goods',
    icon: 'ShoppingBag',
    subcategories: [
      {
        id: 'bread',
        name: 'Bread',
        showImages: false,
        products: [
          { id: 'BRD-001', name: 'Sliced Bread', quantityType: 'count', unit: 'loaf', packSize: 1, variants: ['White', 'Wholemeal'] },
          { id: 'BRD-002', name: 'Bread Rolls',  quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'BRD-003', name: 'Pita Bread',   quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'snacks',
    name: 'Snacks & Confectionery',
    description: 'Biscuits, chocolate & snacks',
    icon: 'Star',
    subcategories: [
      {
        id: 'biscuits',
        name: 'Biscuits',
        showImages: false,
        products: [
          { id: 'BSC-001', name: 'Cream Cracker',      quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Munchee', 'Maliban'] },
          { id: 'BSC-002', name: 'Chocolate Biscuits', quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'BSC-003', name: 'Marie Biscuits',     quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
        ],
      },
      {
        id: 'confectionery',
        name: 'Confectionery',
        showImages: false,
        products: [
          { id: 'CNF-001', name: 'Chocolate', quantityType: 'count', unit: 'bar', packSize: 1, variants: ['Milk', 'Dark', 'White'] },
          { id: 'CNF-002', name: 'Chips',     quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Plain', 'Cheese', 'BBQ'] },
          { id: 'CNF-003', name: 'Candy',     quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'spices',
    name: 'Spices & Seasonings',
    description: 'Spices, curry powders & pastes',
    icon: 'Zap',
    subcategories: [
      {
        id: 'curry-powders',
        name: 'Curry Powders',
        showImages: false,
        products: [
          { id: 'SPZ-001', name: 'Curry Powder',     quantityType: 'weight', unit: 'kg', variants: ['Mild', 'Hot'] },
          { id: 'SPZ-002', name: 'Turmeric',         quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'SPZ-003', name: 'Cumin',            quantityType: 'weight', unit: 'kg', variants: ['Whole', 'Ground'] },
          { id: 'SPZ-004', name: 'Coriander Powder', quantityType: 'weight', unit: 'kg', variants: [] },
          { id: 'SPZ-005', name: 'Chilli Powder',    quantityType: 'weight', unit: 'kg', variants: [] },
        ],
      },
    ],
  },

  {
    id: 'cleaning',
    name: 'Cleaning Essentials',
    description: 'Laundry, dishwashing & cleaning',
    icon: 'Sparkles',
    subcategories: [
      {
        id: 'dishwashing',
        name: 'Dishwashing',
        showImages: false,
        products: [
          { id: 'DWS-001', name: 'Dishwashing Liquid', quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'DWS-002', name: 'Dishwasher Pods',    quantityType: 'count', unit: 'pack',   packSize: 1, variants: [] },
        ],
      },
      {
        id: 'laundry',
        name: 'Laundry',
        showImages: false,
        products: [
          { id: 'LND-001', name: 'Laundry Detergent', quantityType: 'count', unit: 'pack',   packSize: 1, variants: ['Powder', 'Liquid'] },
          { id: 'LND-002', name: 'Fabric Softener',   quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'LND-003', name: 'Stain Remover',     quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
        ],
      },
      {
        id: 'household-cleaning',
        name: 'Household Cleaning',
        showImages: false,
        products: [
          { id: 'HHC-001', name: 'Floor Cleaner',   quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'HHC-002', name: 'Toilet Cleaner',  quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'HHC-003', name: 'Bleach',          quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'HHC-004', name: 'Garbage Bags',    quantityType: 'count', unit: 'pack',   packSize: 1, variants: [] },
          { id: 'HHC-005', name: 'Sponges',         quantityType: 'count', unit: 'pack',   packSize: 1, variants: [] },
          { id: 'HHC-006', name: 'Cleaning Cloths', quantityType: 'count', unit: 'pack',   packSize: 1, variants: [] },
        ],
      },
    ],
  },

  {
    id: 'personal-care',
    name: 'Personal Care',
    description: 'Toiletries & personal care',
    icon: 'User',
    subcategories: [
      {
        id: 'hair',
        name: 'Hair Care',
        showImages: false,
        products: [
          { id: 'HRC-001', name: 'Shampoo',     quantityType: 'count', unit: 'bottle', packSize: 1, variants: ['Normal', 'Dry', 'Anti-Dandruff'] },
          { id: 'HRC-002', name: 'Conditioner', quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
        ],
      },
      {
        id: 'body',
        name: 'Body Care',
        showImages: false,
        products: [
          { id: 'BDY-001', name: 'Bathing Soap', quantityType: 'count', unit: 'bar',    packSize: 1, variants: [] },
          { id: 'BDY-002', name: 'Hand Wash',    quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
          { id: 'BDY-003', name: 'Deodorant',    quantityType: 'count', unit: 'bottle', packSize: 1, variants: ['Roll-on', 'Spray'] },
          { id: 'BDY-004', name: 'Face Wash',    quantityType: 'count', unit: 'tube',   packSize: 1, variants: [] },
        ],
      },
      {
        id: 'oral',
        name: 'Oral Care',
        showImages: false,
        products: [
          { id: 'ORL-001', name: 'Toothpaste',  quantityType: 'count', unit: 'tube', packSize: 1, variants: ['Regular', 'Whitening', 'Sensitive'] },
          { id: 'ORL-002', name: 'Toothbrush',  quantityType: 'count', unit: 'pc',   packSize: 1, variants: ['Soft', 'Medium', 'Hard'] },
          { id: 'ORL-003', name: 'Mouthwash',   quantityType: 'count', unit: 'bottle', packSize: 1, variants: [] },
        ],
      },
      {
        id: 'feminine',
        name: 'Feminine & Baby Care',
        showImages: false,
        products: [
          { id: 'FMN-001', name: 'Sanitary Pads', quantityType: 'count', unit: 'pack', packSize: 1, variants: ['Regular', 'Night'] },
          { id: 'FMN-002', name: 'Baby Diapers',  quantityType: 'count', unit: 'pack', packSize: 1, variants: ['S', 'M', 'L'] },
        ],
      },
    ],
  },

  {
    id: 'household',
    name: 'Household Essentials',
    description: 'Tissues, paper & household items',
    icon: 'Home',
    subcategories: [
      {
        id: 'paper',
        name: 'Paper Products',
        showImages: false,
        products: [
          { id: 'PPR-001', name: 'Tissues',      quantityType: 'count', unit: 'box',  packSize: 1, variants: [] },
          { id: 'PPR-002', name: 'Toilet Paper', quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
          { id: 'PPR-003', name: 'Kitchen Roll', quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
        ],
      },
      {
        id: 'wrap',
        name: 'Wrap & Storage',
        showImages: false,
        products: [
          { id: 'WRP-001', name: 'Cling Wrap',      quantityType: 'count', unit: 'roll', packSize: 1, variants: [] },
          { id: 'WRP-002', name: 'Aluminium Foil',  quantityType: 'count', unit: 'roll', packSize: 1, variants: [] },
          { id: 'WRP-003', name: 'Zip-lock Bags',   quantityType: 'count', unit: 'pack', packSize: 1, variants: [] },
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

      if (p.variants.length > 0) {
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
 * If count -> "4 packs", "2 trays"
 * If weight -> "2.5 kg", "479 g"
 */
export function formatQuantity(qty, quantityType, unit) {
  if (!qty) return '';
  
  if (quantityType === 'weight') {
    // qty is stored in kg
    if (qty < 1 && qty > 0) {
      return `${Math.round(qty * 1000)} g`;
    }
    return `${qty} kg`;
  }
  
  // count
  const isPlural = qty !== 1;
  let displayUnit = unit;
  if (isPlural) {
    if (unit === 'box') displayUnit = 'boxes';
    else if (unit === 'loaf') displayUnit = 'loaves';
    else if (unit === 'pc') displayUnit = 'pcs';
    else displayUnit = unit + 's';
  }
  
  return `${qty} ${displayUnit}`;
}
