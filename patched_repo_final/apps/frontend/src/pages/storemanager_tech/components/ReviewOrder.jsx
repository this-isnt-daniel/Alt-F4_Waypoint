import React, { useState } from 'react';
import { ArrowLeft, Check, Snowflake, Edit3, AlertCircle, Calendar as CalendarIcon, X } from 'lucide-react';
import { CATEGORIES, formatQuantity } from '../data/catalogue';
import QuantityStepper from './QuantityStepper';
import { ORDER_CUTOFF } from '../data/orders';
import DeliveryDateSelector from './DeliveryDateSelector';

export default function ReviewOrder({ basket, onBack, onConfirm, onNavigateToProduct, onChangeQty, orderDate, setOrderDate }) {
  const [showDatePickerModal, setShowDatePickerModal] = useState(false);
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
  const isValid = basket.length > 0 && !hasInvalidQty && !!orderDate;

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
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[12px] font-bold text-slate-400 uppercase tracking-wider">Delivery Details</h2>
              <button
                type="button"
                onClick={() => setShowDatePickerModal(true)}
                className="text-[12px] font-bold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100 px-2.5 py-1 rounded transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <CalendarIcon size={14} />
                <span>{orderDate ? 'Change Date' : 'Select Date'}</span>
              </button>
            </div>
            <div className="text-[13px] text-slate-900 space-y-2">
              <p className="font-semibold text-slate-800">Destination · Nugegoda Outlet</p>
              
              <div 
                onClick={() => setShowDatePickerModal(true)}
                className="p-3 rounded-lg border border-slate-200 hover:border-brand-500 bg-slate-50/80 hover:bg-brand-50/30 cursor-pointer transition-all flex items-center justify-between group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-md bg-brand-100 text-brand-600 flex items-center justify-center shrink-0">
                    <CalendarIcon size={16} />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide block">Scheduled Date</span>
                    <span className="font-bold text-[14px] text-slate-900">
                      {orderDate || 'Select Delivery Date'}
                    </span>
                  </div>
                </div>
                <span className="text-[12px] font-semibold text-brand-600 group-hover:underline">
                  {orderDate ? 'Change' : 'Choose Date'}
                </span>
              </div>

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
              <li className={`flex items-center gap-2 ${orderDate ? 'text-brand-700' : 'text-amber-600'}`}>
                {orderDate ? <Check size={16} /> : <AlertCircle size={16} />}
                {orderDate ? `Delivery date set (${orderDate})` : 'Delivery date selection required'}
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

      {/* Date Picker Modal Popup */}
      {showDatePickerModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in-95 duration-200">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2 text-slate-800">
                <CalendarIcon size={18} className="text-brand-600" />
                <h3 className="text-[15px] font-bold">Select Delivery Date</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowDatePickerModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            <div className="p-4">
              <DeliveryDateSelector
                orderDate={orderDate}
                setOrderDate={setOrderDate}
                onDateSelected={() => setShowDatePickerModal(false)}
                hideHeader={true}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
