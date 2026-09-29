import React from 'react';
import {
  Laptop, Smartphone, Headphones, HardDrive, Cable, Cpu, Wifi,
  Circle, Star, Zap, Sparkles, User, Home, ShoppingBag
} from 'lucide-react';

const ICON_MAP = {
  Laptop, Smartphone, Headphones, HardDrive, Cable, Cpu, Wifi,
  Circle, Star, Zap, Sparkles, User, Home, ShoppingBag
};

const TEMP_BADGE = {
  chilled: { label: 'Chilled', className: 'bg-sky-50 text-sky-700 border-sky-200' },
  frozen:  { label: 'Frozen',  className: 'bg-blue-50 text-blue-700 border-blue-200' },
};

/**
 * CategoryBrowser
 * Shows the category grid.
 */
export default function CategoryBrowser({
  categories,
  onSelectCategory,
  basket,
}) {
  const IconComponent = (name) => ICON_MAP[name] || Circle;

  return (
    <div className="flex flex-col flex-1 overflow-hidden min-h-0">
      {/* Category grid */}
      <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4 pb-24 md:pb-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
          {categories.map((cat) => {
            const Icon = IconComponent(cat.icon);
            // Count basket items in this category
            const basketItemsInCat = basket.filter((b) => b.categoryId === cat.id).length;

            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => onSelectCategory(cat)}
                className="group flex flex-col items-start p-4 bg-white border border-slate-200 rounded-xl hover:border-brand-300 hover:bg-brand-50/30 transition-all text-left relative"
              >
                {basketItemsInCat > 0 && (
                  <span className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full bg-brand-600 text-white text-[10px] font-bold flex items-center justify-center">
                    {basketItemsInCat}
                  </span>
                )}
                <div className="w-9 h-9 rounded-lg bg-slate-100 group-hover:bg-brand-100 flex items-center justify-center text-slate-500 group-hover:text-brand-700 mb-3 transition-colors">
                  <Icon size={18} strokeWidth={1.8} />
                </div>
                <p className="text-[13px] font-semibold text-slate-900 leading-snug">{cat.name}</p>
                {cat.tempRequired && (
                  <span className={`mt-1.5 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${TEMP_BADGE[cat.tempRequired]?.className}`}>
                    {TEMP_BADGE[cat.tempRequired]?.label}
                  </span>
                )}
                {!cat.tempRequired && (
                  <p className="text-[11px] text-slate-400 mt-1 leading-tight">{cat.description}</p>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
