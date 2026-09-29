import { ALL_PRODUCTS } from './catalogue';

// Helper to quickly build items
function buildItem(productId, variant, qty) {
  const product = ALL_PRODUCTS.find(p => p.id === productId && (p.variant === variant || (!p.variant && !variant)));
  if (!product) return null;
  
  return {
    key: `${product.id}-${variant ?? ''}`,
    productId: product.id,
    productName: product.name,
    variant: variant ?? null,
    packSize: product.packSize,
    unit: product.unit,
    qty,
    categoryId: product.categoryId,
    categoryName: product.categoryName,
    subcategoryId: product.subcategoryId,
    quantityType: product.quantityType,
  };
}

export const RECENT_ORDERS = [
  {
    id: 'ORD-10482',
    date: 'Yesterday',
    productCount: 4,
    categories: 'Fresh Produce · Chilled · Staples',
    items: [
      buildItem('RCE-001', 'Nadu', 5),
      buildItem('VEG-002', null, 3),
      buildItem('DRY-001', 'Salted', 4),
      buildItem('FRT-001', 'Red', 2.5),
    ].filter(Boolean)
  },
  {
    id: 'ORD-10441',
    date: '3 days ago',
    productCount: 3,
    categories: 'Fresh Produce · Staples',
    items: [
      buildItem('RCE-001', 'Samba', 10),
      buildItem('VEG-005', 'Local', 5),
      buildItem('VEG-006', 'Local', 5),
    ].filter(Boolean)
  },
  {
    id: 'ORD-10391',
    date: '6 days ago',
    productCount: 5,
    categories: 'Meat · Produce · Bakery',
    items: [
      buildItem('CHK-001', null, 10),
      buildItem('EGG-001', 'Large', 5),
      buildItem('BRD-001', 'White', 20),
      buildItem('FRT-002', null, 10),
      buildItem('VEG-001', 'Local', 5),
    ].filter(Boolean)
  }
];

export let SAVED_TEMPLATES = [
  {
    id: 'tpl-1',
    name: 'Weekly Grocery',
    lastUsedText: 'Last used 2 days ago',
    items: [
      buildItem('RCE-001', 'Nadu', 5),
      buildItem('VEG-002', null, 3),
      buildItem('FRT-001', 'Red', 2.5),
      buildItem('DRY-001', 'Salted', 4),
      buildItem('MLK-001', 'Full Cream', 10),
      buildItem('CHK-001', null, 5),
    ].filter(Boolean)
  },
  {
    id: 'tpl-2',
    name: 'Weekend Restock',
    lastUsedText: 'Last used Friday',
    items: [
      buildItem('BRD-001', 'White', 10),
      buildItem('BRD-002', null, 5),
      buildItem('DRY-004', 'Processed', 3),
      buildItem('DRK-001', 'Cola', 12),
      buildItem('BSC-002', null, 8),
    ].filter(Boolean)
  },
  {
    id: 'tpl-3',
    name: 'Cleaning Supplies',
    lastUsedText: 'Last used 1 month ago',
    items: [
      buildItem('DWS-001', null, 12),
      buildItem('LND-001', 'Powder', 8),
      buildItem('HHC-001', null, 6),
      buildItem('HHC-002', null, 6),
    ].filter(Boolean)
  }
];

export function addSavedTemplate(name, items) {
  const newTemplate = {
    id: `tpl-${Date.now()}`,
    name,
    lastUsedText: 'Just created',
    items: [...items],
  };
  SAVED_TEMPLATES = [newTemplate, ...SAVED_TEMPLATES];
  return newTemplate;
}

export function renameSavedTemplate(id, newName) {
  SAVED_TEMPLATES = SAVED_TEMPLATES.map(t => t.id === id ? { ...t, name: newName } : t);
}

export function updateSavedTemplate(id, items) {
  SAVED_TEMPLATES = SAVED_TEMPLATES.map(t => t.id === id ? { ...t, items: [...items] } : t);
}
