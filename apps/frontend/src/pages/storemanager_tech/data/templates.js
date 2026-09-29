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
    id: 'TECH-8401',
    date: 'Yesterday',
    productCount: 3,
    categories: 'Storage · Cables · Audio',
    items: [
      buildItem('SSD-001', '1TB', 10),
      buildItem('CHG-001', 'Black', 15),
      buildItem('CBL-001', 'Black', 20),
    ].filter(Boolean)
  },
  {
    id: 'TECH-8395',
    date: '3 days ago',
    productCount: 3,
    categories: 'Peripherals · Cables',
    items: [
      buildItem('KBD-001', 'Linear Red Switch', 5),
      buildItem('MSE-001', 'Graphite', 5),
      buildItem('CBL-003', 'Braided Black', 8),
    ].filter(Boolean)
  },
];

export let SAVED_TEMPLATES = [
  {
    id: 'tpl-tech-1',
    name: 'Fast-Moving Cables & Chargers',
    lastUsedText: 'Last used 2 days ago',
    items: [
      buildItem('CHG-001', 'Black', 10),
      buildItem('CHG-001', 'White', 10),
      buildItem('CBL-001', 'Black', 20),
      buildItem('PBK-001', 'Titanium', 8),
      buildItem('SSD-001', '1TB', 5),
    ].filter(Boolean)
  },
  {
    id: 'tpl-tech-2',
    name: 'Workstation Peripherals Kit',
    lastUsedText: 'Last used last week',
    items: [
      buildItem('MON-001', 'Matte Black', 3),
      buildItem('KBD-001', 'Tactile Brown Switch', 6),
      buildItem('MSE-001', 'Graphite', 6),
      buildItem('DCK-001', 'Space Gray Aluminum', 4),
    ].filter(Boolean)
  },
  {
    id: 'tpl-tech-3',
    name: 'Audio & Wearables Restock',
    lastUsedText: 'Last used 2 weeks ago',
    items: [
      buildItem('AUD-001', 'Matte Black', 5),
      buildItem('EBD-001', 'Glossy White', 8),
      buildItem('SPK-001', 'Black', 6),
      buildItem('WAT-001', 'Titanium / Midnight Band', 3),
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
