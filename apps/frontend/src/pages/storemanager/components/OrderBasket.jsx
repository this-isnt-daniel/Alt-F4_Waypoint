import React, { useState } from 'react';
import { X, ChevronRight, ChevronLeft } from 'lucide-react';
import { CATEGORIES, formatQuantity } from '../data/catalogue';
import QuantityStepper from './QuantityStepper';
import { addSavedTemplate } from '../data/templates';

export default function OrderBasket({
  basket,
  onRemoveItem,
  onChangeQty,
  onReview,
  mobileExpanded,
  setMobileExpanded,
  isEditingTemplate,
  orderDate,
  isCollapsed,
  onToggleCollapse
}) {
  const [isSavingTemplate, setIsSavingTemplate] = useState(false);
  const [templateName, setTemplateName] = useState('');

  const handleSaveTemplate = () => {
    if (templateName.trim()) {
      addSavedTemplate(templateName.trim(), basket);
      setIsSavingTemplate(false);
      setTemplateName('');
      // Optionally notify user here, but inline UI change works
    }
  };

  const activeBasket = basket.filter(item => item.qty > 0);
  const totalItems = activeBasket.length;
  const isEmpty = totalItems === 0;

  // Group by category
  const grouped = activeBasket.reduce((acc, item) => {
    const key = item.categoryId;
    if (!acc[key]) acc[key] = { name: item.categoryName, items: [] };
    acc[key].items.push(item);
    return acc;
  }, {});

  // Temperature grouping
  const dryItems = activeBasket.filter(item => {
    const cat = CATEGORIES.find(c => c.id === item.categoryId);
    return !cat?.tempRequired;
  });
  const tempItems = activeBasket.filter(item => {
    const cat = CATEGORIES.find(c => c.id === item.categoryId);
    return cat?.tempRequired;
  });
  const numOrders = (dryItems.length > 0 ? 1 : 0) + (tempItems.length > 0 ? 1 : 0);

  return (
    <>
      {/* ── Desktop Order Summary ── */}
      {isCollapsed ? (
        <aside 
          className="hidden md:flex flex-col w-[52px] shrink-0 bg-white border-l border-slate-200 h-full items-center py-4 cursor-pointer hover:bg-slate-50 transition-colors"
          onClick={onToggleCollapse}
          aria-label="Expand order summary"
          role="button"
          tabIndex={0}
        >
          <button className="w-8 h-8 flex items-center justify-center rounded-md text-slate-500 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 transition-colors mb-6" aria-hidden="true" tabIndex={-1}>
            <ChevronLeft size={16} />
          </button>
          
          <div className="flex flex-col items-center opacity-80 mt-2 gap-4">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
              Order
            </span>
            <span className="w-6 h-6 rounded-full bg-slate-100 border border-slate-200 text-slate-600 flex items-center justify-center text-[11px] font-bold">
              {totalItems}
            </span>
          </div>
        </aside>
      ) : (
        <aside className="hidden md:flex flex-col w-72 lg:w-80 shrink-0 bg-white border-l border-slate-200 h-full">
          <div className="flex flex-col h-full max-h-full bg-white">
            {/* Header */}
            <div className="p-4 border-b border-slate-200">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-[13px] font-bold text-slate-800 uppercase tracking-wider">Order Summary</h2>
                <button
                  onClick={onToggleCollapse}
                  className="p-1 -mr-1 text-slate-400 hover:text-slate-700 bg-slate-50 hover:bg-slate-100 rounded transition-colors"
                  aria-label="Collapse order summary"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
              <div className="text-[13px] text-slate-900 space-y-0.5 mb-3">
                <p className="font-bold">Delivery</p>
                <p>{orderDate || 'Tomorrow · 30 Sep'}</p>
              </div>
              {!isEmpty && (
                <div className="pt-3 border-t border-slate-100">
                  <p className="text-[12px] font-semibold text-slate-600">{totalItems} products</p>
                </div>
              )}
            </div>

          {/* Table Body */}
          <div className="flex-1 overflow-y-auto p-1">
            {isEmpty ? (
              <div className="p-4 text-center text-slate-400 text-[12px]">No items added</div>
            ) : (
              <div className="space-y-4 py-2">
                {Object.values(grouped).map((group) => (
                  <div key={group.name} className="px-1">
                    <div className="px-2 py-1 mb-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      {group.name}
                    </div>
                    <div className="divide-y divide-slate-100">
                      {group.items.map((item) => {
                        const step = item.quantityType === 'weight' ? 0.5 : 1;
                        return (
                          <SummaryRow
                            key={item.key}
                            item={item}
                            onChange={(newQty) => onChangeQty(item.key, newQty)}
                            onDecrement={() => onChangeQty(item.key, Math.max(0, item.qty - step))}
                            onIncrement={() => onChangeQty(item.key, item.qty + step)}
                          />
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer Action */}
          {!isEmpty && (
            <div className="p-4 border-t border-slate-200 bg-slate-50">
              {numOrders > 1 && (
                <div className="mb-4">
                  <p className="text-[13px] font-bold text-slate-800 mb-1">{numOrders} orders</p>
                  <p className="text-[12px] text-slate-500">Dry · {dryItems.length} items</p>
                  <p className="text-[12px] text-slate-500">Chilled/Frozen · {tempItems.length} items</p>
                </div>
              )}
              {isSavingTemplate ? (
                <div className="bg-white p-3 rounded-md border border-brand-200 shadow-sm mb-2">
                  <p className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">Save as Template</p>
                  <input
                    type="text"
                    value={templateName}
                    onChange={(e) => setTemplateName(e.target.value)}
                    placeholder="e.g. Weekend Restock"
                    className="w-full text-[13px] border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent mb-3"
                    autoFocus
                  />
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setIsSavingTemplate(false)}
                      className="flex-1 py-1.5 text-[12px] font-semibold text-slate-600 hover:bg-slate-100 rounded transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveTemplate}
                      disabled={!templateName.trim()}
                      className="flex-1 py-1.5 text-[12px] font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded transition-colors disabled:opacity-50"
                    >
                      Save
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  <button
                    type="button"
                    onClick={onReview}
                    className="w-full py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-[13px] font-semibold rounded-md transition-colors"
                  >
                    Review & Confirm
                  </button>
                  {!isEditingTemplate && (
                    <button
                      type="button"
                      onClick={() => { setTemplateName(''); setIsSavingTemplate(true); }}
                      className="w-full py-1.5 bg-transparent hover:bg-slate-200 text-slate-600 text-[12px] font-medium rounded-md transition-colors"
                    >
                      Save as Template
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </aside>
      )}

      {/* ── Mobile Sticky Bottom Tray ── */}
      {!isEmpty && (
        <div className="md:hidden fixed bottom-[56px] left-0 right-0 z-40 px-2 pb-2 pointer-events-none">
          {/* We offset bottom by 56px to sit right above the SMLayout bottom nav bar.
              Wait, the bottom nav bar is part of normal flow in SMLayout? 
              Actually, the mobile header in SMLayout is at the TOP (sticky top-0), 
              there is NO bottom nav bar in SMLayout! So bottom-0 is correct. */}
        </div>
      )}

      {/* Actual Mobile Tray */}
      {!isEmpty && (
        <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-100 border-t border-slate-300 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)]">
          {mobileExpanded && (
            <div className="bg-white border-b border-slate-200 flex flex-col max-h-[70vh]">
              <div className="p-4 border-b border-slate-200 flex items-start justify-between bg-slate-50">
                <div>
                  <h2 className="text-[13px] font-bold text-slate-800 uppercase tracking-wider mb-3">Order Summary</h2>
                  <div className="text-[13px] text-slate-900 space-y-0.5 mb-3">
                    <p className="font-bold">Delivery</p>
                    <p>{orderDate || 'Tomorrow · 30 Sep'}</p>
                  </div>
                  <div className="pt-3 border-t border-slate-200 w-full">
                    <p className="text-[12px] font-semibold text-slate-600">{totalItems} products</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setMobileExpanded(false)}
                  className="p-1 -mr-2 text-slate-400 hover:text-slate-600"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="overflow-y-auto flex-1 p-1">
                <div className="space-y-4 py-2">
                  {Object.values(grouped).map((group) => (
                    <div key={group.name} className="px-2">
                      <div className="px-2 py-1 mb-1 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                        {group.name}
                      </div>
                      <div className="divide-y divide-slate-100">
                        {group.items.map((item) => {
                          const step = item.quantityType === 'weight' ? 0.5 : 1;
                          return (
                            <SummaryRow
                              key={item.key}
                              item={item}
                              onChange={(newQty) => onChangeQty(item.key, newQty)}
                              onDecrement={() => onChangeQty(item.key, Math.max(0, item.qty - step))}
                              onIncrement={() => onChangeQty(item.key, item.qty + step)}
                            />
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tray handle / collapsed view */}
          <div className="p-3 bg-white border-t border-slate-200">
            {!mobileExpanded ? (
              <button
                type="button"
                onClick={() => setMobileExpanded(true)}
                className="w-full bg-slate-900 text-white rounded-md px-4 py-3 flex items-center justify-between text-[14px] font-semibold shadow-sm"
              >
                <span>{totalItems} items</span>
                <span className="text-brand-300">View Order</span>
              </button>
            ) : (
              <div className="flex flex-col gap-2">
                {numOrders > 1 && (
                  <div className="mb-2 px-1">
                    <p className="text-[13px] font-bold text-slate-800 mb-1">{numOrders} orders</p>
                    <p className="text-[12px] text-slate-500">Dry · {dryItems.length} items</p>
                    <p className="text-[12px] text-slate-500">Chilled/Frozen · {tempItems.length} items</p>
                  </div>
                )}
                {isSavingTemplate ? (
                  <div className="bg-white p-3 rounded-md border border-brand-200 shadow-sm">
                    <p className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">Save as Template</p>
                    <input
                      type="text"
                      value={templateName}
                      onChange={(e) => setTemplateName(e.target.value)}
                      placeholder="e.g. Weekend Restock"
                      className="w-full text-[13px] border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent mb-3"
                    />
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setIsSavingTemplate(false)}
                        className="flex-1 py-1.5 text-[12px] font-semibold text-slate-600 hover:bg-slate-100 rounded transition-colors"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleSaveTemplate}
                        disabled={!templateName.trim()}
                        className="flex-1 py-1.5 text-[12px] font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded transition-colors disabled:opacity-50"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      onClick={() => { setMobileExpanded(false); onReview(); }}
                      className="w-full bg-brand-600 text-white rounded-md px-4 py-3 flex items-center justify-center text-[14px] font-semibold shadow-sm"
                    >
                      Review & Confirm
                    </button>
                    {!isEditingTemplate && (
                      <button
                        type="button"
                        onClick={() => { setTemplateName(''); setIsSavingTemplate(true); }}
                        className="w-full bg-transparent hover:bg-slate-100 text-slate-600 rounded-md px-4 py-2 flex items-center justify-center text-[13px] font-medium transition-colors"
                      >
                        Save as Template
                      </button>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function SummaryRow({ item, onChange, onDecrement, onIncrement }) {
  return (
    <div className="flex items-start justify-between px-2 md:px-3 py-2 hover:bg-slate-50 transition-colors">
      <div className="flex-1 min-w-0 pr-2 pt-0.5">
        <p className="text-[12px] font-medium text-slate-900 truncate">
          {item.productName}{item.variant ? ` · ${item.variant}` : ''}
        </p>
      </div>
      <div className="shrink-0">
        <QuantityStepper
          qty={item.qty}
          quantityType={item.quantityType}
          unit={item.unit}
          onChange={onChange}
          onDecrement={onDecrement}
          onIncrement={onIncrement}
          size="sm"
        />
      </div>
    </div>
  );
}
