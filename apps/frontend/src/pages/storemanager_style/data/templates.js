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
    id: 'STY-2091',
    date: 'Yesterday',
    productCount: 4,
    categories: "Men's Apparel · Women's · Footwear",
    items: [
      buildItem('MSH-001', 'M · White', 15),
      buildItem('MTR-001', '32 · Khaki', 12),
      buildItem('WBL-001', 'S · Ivory', 10),
      buildItem('FTW-001', 'EU 42 · Crisp White', 8),
    ].filter(Boolean)
  },
  {
    id: 'STY-2088',
    date: '3 days ago',
    productCount: 3,
    categories: 'Footwear · Leather · Basics',
    items: [
      buildItem('FTW-001', 'EU 41 · Crisp White', 10),
      buildItem('ACC-001', '34 · Dark Brown', 12),
      buildItem('BSC-001', 'White Pack', 14),
    ].filter(Boolean)
  },
];

export let SAVED_TEMPLATES = [
  {
    id: 'tpl-sty-1',
    name: "Men's Core Essentials Restock",
    lastUsedText: 'Last used 2 days ago',
    items: [
      buildItem('MSH-001', 'M · White', 12),
      buildItem('MSH-001', 'L · White', 12),
      buildItem('MSH-002', 'M · Navy', 10),
      buildItem('MTR-001', '32 · Khaki', 8),
      buildItem('MTR-002', '32 · Indigo', 8),
    ].filter(Boolean)
  },
  {
    id: 'tpl-sty-2',
    name: "Women's Weekend Capsule",
    lastUsedText: 'Last used Friday',
    items: [
      buildItem('WBL-001', 'M · Ivory', 8),
      buildItem('WBL-002', 'S · Oatmeal', 6),
      buildItem('WDR-001', 'M · Emerald', 6),
      buildItem('WTR-001', '28 · Sand', 8),
    ].filter(Boolean)
  },
  {
    id: 'tpl-sty-3',
    name: 'Footwear & Leather Goods',
    lastUsedText: 'Last used 1 week ago',
    items: [
      buildItem('FTW-001', 'EU 41 · Crisp White', 5),
      buildItem('FTW-001', 'EU 42 · Crisp White', 6),
      buildItem('ACC-001', '34 · Dark Brown', 8),
      buildItem('ACC-004', 'Natural Canvas', 10),
      buildItem('BSC-001', 'White Pack', 15),
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
