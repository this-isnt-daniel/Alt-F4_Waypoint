import React from 'react';
import { ArrowLeft, Check, Snowflake, Edit3, AlertCircle } from 'lucide-react';
import { CATEGORIES, formatQuantity } from '../data/catalogue';
import QuantityStepper from './QuantityStepper';
import { ORDER_CUTOFF } from '../data/orders';

export default function ReviewOrder({ basket, onBack, onConfirm, onNavigateToProduct, onChangeQty, orderDate }) {
  const totalItems = basket.length;
  const totalWeight = basket
    .filter(b => b.quantityType === 'weight')
    .reduce((sum, b) => sum + b.qty, 0);

  // Does the order contain any chilled/frozen items?
  const hasTempControlled = basket.some((item) => {
    const cat = CATEGORIES.find((c) => c.id === item.categoryId);
    return cat?.tempRequired;
  });

  // Validation
  const hasInvalidQty = basket.some(b => !b.qty || isNaN(b.qty) || b.qty <= 0);
  const isValid = basket.length > 0 && !hasInvalidQty;

  // Group by category for review sections
  const grouped = basket.reduce((acc, item) => {
    const key = item.categoryId;
    if (!acc[key]) {
      const cat = CATEGORIES.find((c) => c.id === key);
      acc[key] = {
        name: item.categoryName,
        tempRequired: cat?.tempRequired,
        items: [],
      };
    }
    acc[key].items.push(item);
    return acc;
  }, {});

  return (
    <div className="h-full flex flex-col bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onBack}
            className="w-8 h-8 rounded-md border border-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft size={16} strokeWidth={2} />
          </button>
          <div>
            <h1 className="text-[15px] font-bold text-slate-900 uppercase tracking-wide">Review Order</h1>
            <p className="text-[12px] text-slate-500">
              {totalItems} {totalItems === 1 ? 'product' : 'products'}
              {totalWeight > 0 ? ` · ${formatQuantity(totalWeight, 'weight', 'kg')} total weight` : ''}
            </p>
          </div>
        </div>
      </div>

      {/* Review Content */}
      <div className="flex-1 overflow-y-auto px-4 py-5 max-w-screen-md mx-auto w-full pb-24 md:pb-10">
        
        {hasTempControlled && (
          <div className="mb-5 bg-sky-50 border border-sky-200 rounded-md px-4 py-3 flex gap-3">
            <Snowflake size={16} className="text-sky-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-[13px] font-semibold text-sky-800">Separate dispatch required</p>
              <p className="text-[12px] text-sky-700 mt-0.5">
                This order contains temperature-controlled items. They will be packed and delivered in a specialised freezer truck, separate from dry goods.
              </p>
            </div>
          </div>
        )}

        <div className="space-y-6">
          {Object.values(grouped).map((group) => (
            <section key={group.name} className="bg-white border border-slate-200 rounded-md overflow-hidden">
              <div className="px-4 py-2 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
                <h2 className="text-[12px] font-bold text-slate-700 uppercase tracking-wider">
                  {group.name}
                </h2>
                {group.tempRequired && (
                  <span className="text-[10px] font-bold text-sky-600 bg-sky-50 px-1.5 py-0.5 rounded border border-sky-100">
                    {group.tempRequired === 'chilled' ? 'Chilled' : 'Frozen'}
                  </span>
                )}
              </div>
              <div className="divide-y divide-slate-100">
                {group.items.map((item) => {
                  const step = item.quantityType === 'weight' ? 0.5 : 1;
                  return (
                    <div key={item.key} className="px-4 py-3 flex items-center justify-between hover:bg-slate-50 transition-colors">
                      <div 
                        className="cursor-pointer group flex-1 min-w-0 pr-4" 
                        onClick={() => onNavigateToProduct(item)}
                      >
                        <p className="text-[14px] font-medium text-slate-900 group-hover:text-brand-600 transition-colors truncate flex items-center gap-2">
                          {item.productName}{item.variant ? ` · ${item.variant}` : ''}
                          <Edit3 size={12} className="text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </p>
                        {(!item.qty || isNaN(item.qty) || item.qty <= 0) && (
                          <p className="text-[11px] text-red-500 font-semibold mt-0.5 flex items-center gap-1">
                            <AlertCircle size={12} /> Quantity required
                          </p>
                        )}
                      </div>
                      <div className="shrink-0">
                        <QuantityStepper
                          qty={item.qty}
                          quantityType={item.quantityType}
                          unit={item.unit}
                          onChange={(newQty) => onChangeQty(item.key, newQty)}
                          onDecrement={() => onChangeQty(item.key, Math.max(0, item.qty - step))}
                          onIncrement={() => onChangeQty(item.key, item.qty + step)}
                          size="md"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          ))}

          {/* Delivery Info */}
          <section className="bg-white border border-slate-200 rounded-md p-4">
            <h2 className="text-[12px] font-bold text-slate-400 uppercase tracking-wider mb-3">Delivery</h2>
            <div className="text-[13px] text-slate-900 space-y-1">
              <p className="font-semibold">Nugegoda</p>
              <p>{orderDate || 'Tomorrow · 30 Sep'}</p>
              <p>Expected arrival · <span className="font-medium text-slate-700">{ORDER_CUTOFF.nextDelivery.split(' · ')[1]}</span></p>
              
              {orderDate?.includes('Tomorrow') && (
                <p className="text-[12px] text-slate-500 mt-2 border-t border-slate-100 pt-2">
                  Order closes today · {ORDER_CUTOFF.label}
                </p>
              )}
            </div>
          </section>

          {/* Order Check */}
          <section className="bg-slate-100 border border-slate-200 rounded-md p-4">
            <h2 className="text-[12px] font-bold text-slate-500 uppercase tracking-wider mb-3">Order Check</h2>
            <ul className="text-[13px] font-medium space-y-2">
              <li className={`flex items-center gap-2 ${basket.length > 0 ? 'text-brand-700' : 'text-red-500'}`}>
                {basket.length > 0 ? <Check size={16} /> : <AlertCircle size={16} />}
                {basket.length > 0 ? 'Products added' : 'No products in order'}
              </li>
              <li className={`flex items-center gap-2 ${!hasInvalidQty ? 'text-brand-700' : 'text-red-500'}`}>
                {!hasInvalidQty ? <Check size={16} /> : <AlertCircle size={16} />}
                {!hasInvalidQty ? 'All quantities entered' : 'Some quantities need attention'}
              </li>
              <li className="flex items-center gap-2 text-brand-700">
                <Check size={16} /> Delivery date set
              </li>
              <li className={`flex items-center gap-2 ${isValid ? 'text-brand-700' : 'text-slate-400'}`}>
                {isValid ? <Check size={16} /> : <Check size={16} className="opacity-50" />}
                {isValid ? 'Order ready for confirmation' : 'Order not ready'}
              </li>
            </ul>
          </section>
        </div>
      </div>

      {/* Footer Action */}
      <div className="bg-white border-t border-slate-200 p-4 shrink-0 flex gap-3 justify-end items-center max-w-screen-md mx-auto w-full">
        <button
          type="button"
          onClick={onBack}
          className="px-5 py-2.5 text-[14px] font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-md transition-colors"
        >
          Edit Order
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={!isValid}
          className="px-6 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold text-[14px] rounded-md transition-colors flex items-center justify-center gap-2"
        >
          <Check size={18} strokeWidth={2.5} /> Confirm Order
        </button>
      </div>
    </div>
  );
}
