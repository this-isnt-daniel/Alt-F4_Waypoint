import React, { useState, useEffect } from 'react';
import { ArrowLeft, Snowflake } from 'lucide-react';
import QuantityStepper from './QuantityStepper';

/**
 * ProductFamily
 * Shows all products in a selected category.
 * Subcategory tabs filter the list.
 */
export default function ProductFamily({ category, initialSubcat, basket, onBack, onSetQty }) {
  const [activeSubcat, setActiveSubcat] = useState(initialSubcat ?? category.subcategories[0]?.id ?? null);

  useEffect(() => {
    if (initialSubcat) {
      setActiveSubcat(initialSubcat);
    }
  }, [initialSubcat, category]);

  const currentSubcat = category.subcategories.find((s) => s.id === activeSubcat);

  return (
    <div className="flex flex-col flex-1 overflow-hidden min-h-0">
      {/* Back + heading */}
      <div className="px-4 md:px-6 pt-4 pb-3 flex items-center gap-3">
        <button
          type="button"
          onClick={onBack}
          className="w-8 h-8 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 hover:border-slate-300 transition-colors shrink-0"
          aria-label="Back to categories"
        >
          <ArrowLeft size={16} strokeWidth={2} />
        </button>
        <div>
          <h2 className="text-[17px] font-bold text-slate-900 leading-tight">{category.name}</h2>
          {category.tempRequired && (
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-sky-600 mt-0.5">
              <Snowflake size={11} /> Temperature controlled
            </span>
          )}
        </div>
      </div>

      {/* Subcategory tabs — only if more than one */}
      {category.subcategories.length > 1 && (
        <div className="px-4 md:px-6 pb-3">
          <div className="flex gap-1.5 overflow-x-auto scrollbar-none">
            {category.subcategories.map((sub) => {
              const isActive = activeSubcat === sub.id;
              const itemsInBasket = basket.filter((b) =>
                sub.products.some((p) => p.id === b.productId)
              ).length;
              return (
                <button
                  key={sub.id}
                  type="button"
                  onClick={() => setActiveSubcat(sub.id)}
                  className={`shrink-0 px-3.5 py-1.5 rounded-full text-[13px] font-semibold transition-colors whitespace-nowrap flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-brand-600 text-white'
                      : 'bg-white border border-slate-200 text-slate-600 hover:border-brand-300 hover:text-brand-700'
                  }`}
                >
                  {sub.name}
                  {itemsInBasket > 0 && (
                    <span className={`inline-flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-bold ${isActive ? 'bg-white/20 text-white' : 'bg-brand-100 text-brand-700'}`}>
                      {itemsInBasket}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Product list */}
      <div className="flex-1 overflow-y-auto px-4 md:px-6 pb-24 md:pb-6">
        {currentSubcat ? (
          <ProductList
            subcategory={currentSubcat}
            basket={basket}
            onSetQty={onSetQty}
          />
        ) : (
          <p className="text-slate-400 text-[14px] py-12 text-center">No subcategory selected</p>
        )}
      </div>
    </div>
  );
}

function ProductList({ subcategory, basket, onSetQty }) {
  if (!subcategory.products.length) {
    return <p className="text-slate-400 text-[14px] py-12 text-center">No products in this category yet.</p>;
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      {/* Table header */}
      <div className="grid grid-cols-[1fr_auto] items-center px-4 py-2.5 border-b border-slate-100 bg-slate-50/60">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Product</span>
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-right">Quantity</span>
      </div>

      <div className="divide-y divide-slate-100">
        {subcategory.products.map((product) => (
          <ProductRow
            key={product.id}
            product={product}
            basket={basket}
            onSetQty={onSetQty}
          />
        ))}
      </div>
    </div>
  );
}

function ProductRow({ product, basket, onSetQty }) {
  const hasVariants = product.variants.length > 0;
  const step = product.quantityType === 'weight' ? 0.5 : 1;

  if (hasVariants) {
    return (
      <div className="px-4 py-3">
        {/* Product name header row */}
        <p className="text-[13px] font-semibold text-slate-700 mb-2.5">{product.name}</p>
        {/* One row per variant */}
        <div className="space-y-2 pl-2 border-l-2 border-slate-100">
          {product.variants.map((variant) => {
            const key = `${product.id}-${variant}`;
            const basketItem = basket.find((b) => b.key === key);
            const qty = basketItem?.qty ?? 0;
            return (
              <div key={variant} className="flex items-center justify-between">
                <div>
                  <p className="text-[14px] font-medium text-slate-900">{variant}</p>
                </div>
                <QuantityStepper
                  qty={qty}
                  quantityType={product.quantityType}
                  unit={product.unit}
                  onChange={(newQty) => onSetQty(product, variant, newQty)}
                  onDecrement={() => onSetQty(product, variant, Math.max(0, qty - step))}
                  onIncrement={() => onSetQty(product, variant, qty + step)}
                  size="sm"
                />
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // No variants — single row
  const key = `${product.id}-`;
  const basketItem = basket.find((b) => b.key === key);
  const qty = basketItem?.qty ?? 0;

  return (
    <div className="px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors">
      <div>
        <p className="text-[14px] font-medium text-slate-900">{product.name}</p>
      </div>
      <QuantityStepper
        qty={qty}
        quantityType={product.quantityType}
        unit={product.unit}
        onChange={(newQty) => onSetQty(product, null, newQty)}
        onDecrement={() => onSetQty(product, null, Math.max(0, qty - step))}
        onIncrement={() => onSetQty(product, null, qty + step)}
        size="sm"
      />
    </div>
  );
}
