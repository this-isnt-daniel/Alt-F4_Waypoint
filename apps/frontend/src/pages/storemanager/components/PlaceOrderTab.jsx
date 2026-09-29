import React, { useState, useEffect, useRef } from 'react';
import { CATEGORIES } from '../data/catalogue';
import { updateSavedTemplate } from '../data/templates';
import CategoryBrowser from './CategoryBrowser';
import ProductFamily from './ProductFamily';
import OrderBasket from './OrderBasket';
import ReviewOrder from './ReviewOrder';
import GlobalSearch from './GlobalSearch';
import MyTemplates from './MyTemplates';
import DeliveryDateSelector from './DeliveryDateSelector';
import { Calendar as CalendarIcon, ChevronDown, X } from 'lucide-react';

/**
 * PlaceOrderTab
 * Orchestrates the Place Order workflow:
 *   date selection → categories → products → (review) → confirm
 *
 * Basket state is passed down from StoreManagerOverview so it persists
 * across tab switches.
 */
export default function PlaceOrderTab({ 
  basket, onSetQty, onRemoveItem, onChangeQty, onClearBasket, onReplaceBasket,
  orderDate, setOrderDate
}) {
  const [view, setView]               = useState('categories'); // 'categories' | 'products' | 'review' | 'success'
  const [activeTab, setActiveTab]     = useState('catalogue'); // 'catalogue' | 'templates'
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [activeSubcat, setActiveSubcat] = useState(null);
  const [mobileBasketExpanded, setMobileBasketExpanded] = useState(false);
  
  // Date modal popup state (calendar only appears as popup modal when requested)
  const [showDateModal, setShowDateModal] = useState(false);
  
  // Template editing state
  const [editingTemplate, setEditingTemplate] = useState(null); // The full template object if editing
  
  // Replace Confirmation Modal State
  const [pendingReplace, setPendingReplace] = useState(null);

  // Order Summary Collapse State
  const [isOrderSummaryCollapsed, setIsOrderSummaryCollapsed] = useState(basket.length === 0);
  const [hasManuallyCollapsed, setHasManuallyCollapsed] = useState(false);
  const previousBasketLength = useRef(basket.length);

  useEffect(() => {
    // When the first item is added, automatically expand the Order Summary
    if (basket.length > 0 && previousBasketLength.current === 0) {
      if (!hasManuallyCollapsed) {
        setIsOrderSummaryCollapsed(false);
      }
    }
    previousBasketLength.current = basket.length;
  }, [basket.length, hasManuallyCollapsed]);

  const toggleCollapse = () => {
    setIsOrderSummaryCollapsed(prev => {
      const next = !prev;
      if (next) setHasManuallyCollapsed(true);
      return next;
    });
  };

  const handleConfirmOrder = () => {
    onClearBasket();
    setView('success');
  };

  const handleSaveChanges = () => {
    if (editingTemplate) {
      updateSavedTemplate(editingTemplate.id, basket);
      setEditingTemplate(null);
      onClearBasket();
      setView('categories');
      setActiveTab('templates');
    }
  };

  const handleNavigateToProduct = (item) => {
    const cat = CATEGORIES.find(c => c.id === item.categoryId);
    setSelectedCategory(cat);
    setActiveSubcat(item.subcategoryId);
    setView('products');
  };

  const handleUseTemplate = (items, type) => {
    // If basket is empty, just replace it
    if (basket.length === 0) {
      onReplaceBasket(items);
      setActiveTab('catalogue');
      setView('categories');
    } else {
      // Ask for confirmation
      setPendingReplace({ items, type });
    }
  };

  const confirmReplaceBasket = () => {
    onReplaceBasket(pendingReplace.items);
    setPendingReplace(null);
    setActiveTab('catalogue');
    setView('categories');
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    onReplaceBasket(template.items);
    setActiveTab('catalogue');
    setView('categories');
  };

  const cancelEditMode = () => {
    setEditingTemplate(null);
    onClearBasket();
  };

  // ── Render ─────────────────────────────────────────────

  if (view === 'success') {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 bg-slate-50 text-center">
        <div className="w-16 h-16 bg-brand-100 text-brand-600 rounded-full flex items-center justify-center mb-6">
          <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-[20px] font-bold text-slate-900 mb-2">Order Confirmed!</h1>
        <p className="text-[14px] text-slate-500 max-w-[280px] mb-8">
          Your order has been placed successfully and will be delivered on {orderDate ? orderDate.split(' · ')[0].toLowerCase() : 'tomorrow'}.
        </p>
        <button
          onClick={() => setView('categories')}
          className="px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-bold text-[14px] rounded-lg transition-colors"
        >
          Start New Order
        </button>
      </div>
    );
  }

  if (view === 'review') {
    return (
      <div className="h-full overflow-hidden relative">
        <ReviewOrder
          basket={basket}
          onBack={() => setView('categories')}
          onConfirm={editingTemplate ? handleSaveChanges : handleConfirmOrder}
          onChangeQty={onChangeQty}
          onNavigateToProduct={handleNavigateToProduct}
          isEditingTemplate={!!editingTemplate}
          orderDate={orderDate}
          setOrderDate={setOrderDate}
        />
      </div>
    );
  }

  return (
    <div className="h-full flex overflow-hidden relative">
      {/* ── Replace Modal ── */}
      {pendingReplace && (
        <div className="absolute inset-0 z-50 bg-slate-900/40 flex items-center justify-center px-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="px-5 pt-5 pb-4">
              <h3 className="text-[16px] font-bold text-slate-900 mb-2">Replace current basket?</h3>
              <p className="text-[14px] text-slate-600">
                You already have items in your basket. Loading this {pendingReplace.type} will clear your current selections.
              </p>
            </div>
            <div className="px-5 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setPendingReplace(null)}
                className="px-4 py-2 text-[14px] font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-200/50 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmReplaceBasket}
                className="px-4 py-2 text-[14px] font-semibold text-white bg-brand-600 hover:bg-brand-700 rounded-lg transition-colors shadow-sm"
              >
                Replace Basket
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Main area (catalogue or templates) ── */}
      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        
        {/* Editing Template Mode Banner */}
        {editingTemplate && (
          <div className="px-4 md:px-6 py-2.5 bg-brand-50 border-b border-brand-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
              <span className="text-[13px] font-bold text-brand-800">
                Editing Template: {editingTemplate.name}
              </span>
            </div>
            <button
              onClick={cancelEditMode}
              className="text-[12px] font-semibold text-brand-600 hover:text-brand-800"
            >
              Cancel Edit
            </button>
          </div>
        )}

        {/* Not editing -> Persistent Delivery Date and Tabs */}
        {!editingTemplate && (
          <>
            <div className="px-4 md:px-6 py-2.5 bg-slate-50 dark:bg-[#111827] border-b border-slate-200 dark:border-slate-800 flex items-center justify-between transition-colors">
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-0.5">
                  Delivery Date
                </span>
                <div className="flex items-center gap-1.5">
                  <CalendarIcon size={14} className="text-brand-600 dark:text-emerald-400" />
                  <span className="text-[13px] font-bold text-slate-900 dark:text-[#F8FAFC]">{orderDate || 'Select Date'}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowDateModal(true)}
                className="text-[12px] font-semibold text-brand-600 dark:text-emerald-400 hover:text-brand-800 dark:hover:text-emerald-300 transition-colors cursor-pointer"
              >
                {orderDate ? 'Change' : 'Select'}
              </button>
            </div>

            {orderDate?.includes('Tomorrow') && (
              <div className="px-4 md:px-6 py-2 bg-emerald-500/10 dark:bg-emerald-950/30 border-b border-emerald-500/20 dark:border-emerald-800/30 flex items-center gap-2 transition-colors">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[11px] font-semibold text-emerald-800 dark:text-emerald-300 tracking-wide">
                  Order closes 4:00 PM today
                </span>
                <span className="text-[10px] font-medium text-emerald-600/80 dark:text-emerald-400/70 ml-auto hidden sm:inline">
                  Next-day dispatch active
                </span>
              </div>
            )}

            <div className="px-4 md:px-6 py-3 border-b border-slate-200 dark:border-slate-800 shrink-0">
              <div className="flex p-1 bg-slate-100 dark:bg-slate-800/80 rounded-lg">
                <button
                  type="button"
                  onClick={() => setActiveTab('catalogue')}
                  className={`flex-1 text-[13px] font-semibold py-1.5 rounded-md transition-all cursor-pointer ${
                    activeTab === 'catalogue'
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-[#F8FAFC] shadow-sm'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  Catalogue
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('templates')}
                  className={`flex-1 text-[13px] font-semibold py-1.5 rounded-md transition-all cursor-pointer ${
                    activeTab === 'templates'
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-[#F8FAFC] shadow-sm'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                  }`}
                >
                  My Templates
                </button>
              </div>
            </div>
          </>
        )}

        {/* Content based on tab */}
        {activeTab === 'templates' && !editingTemplate ? (
          <MyTemplates
            onUseTemplate={handleUseTemplate}
            onEditTemplate={handleEditTemplate}
          />
        ) : (
          <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
            {/* ── Global Search for Order page ── */}
            <div className="px-4 md:px-6 pt-4 pb-1 shrink-0 flex items-center justify-between gap-4">
              <div className="text-[12px] font-bold text-slate-500 uppercase tracking-wider shrink-0 hidden md:block">
                Order Items · {basket.length} Items
              </div>
              <GlobalSearch basket={basket} onSetQty={onSetQty} />
            </div>

            {view === 'categories' && (
              <CategoryBrowser
                categories={CATEGORIES}
                basket={basket}
                onSelectCategory={(cat) => {
                  setSelectedCategory(cat);
                  setActiveSubcat(null); // Reset subcat on new category
                  setView('products');
                }}
              />
            )}

            {view === 'products' && selectedCategory && (
              <ProductFamily
                category={selectedCategory}
                initialSubcat={activeSubcat}
                basket={basket}
                onBack={() => setView('categories')}
                onSetQty={(product, variant, qty) =>
                  onSetQty(
                    { 
                      ...product, 
                      categoryId: selectedCategory.id, 
                      categoryName: selectedCategory.name,
                      subcategoryId: activeSubcat
                    },
                    variant,
                    qty
                  )
                }
              />
            )}
          </div>
        )}
      </div>

      {/* ── Persistent Basket ── */}
      <OrderBasket
        basket={basket}
        onRemoveItem={onRemoveItem}
        onChangeQty={onChangeQty}
        onReview={() => setView('review')}
        mobileExpanded={mobileBasketExpanded}
        setMobileExpanded={setMobileBasketExpanded}
        isEditingTemplate={!!editingTemplate}
        orderDate={orderDate}
        isCollapsed={isOrderSummaryCollapsed}
        onToggleCollapse={toggleCollapse}
      />

      {/* ── Delivery Date Popup Modal ── */}
      {showDateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-[#111827] rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden border border-slate-100 dark:border-slate-800 animate-in fade-in zoom-in-95 duration-200">
            <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
              <div className="flex items-center gap-2 text-slate-800 dark:text-[#F8FAFC]">
                <CalendarIcon size={18} className="text-brand-600 dark:text-emerald-400" />
                <h3 className="text-[15px] font-bold">Select Delivery Date</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowDateModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              >
                <X size={18} />
              </button>
            </div>
            <div className="p-4">
              <DeliveryDateSelector
                orderDate={orderDate}
                setOrderDate={setOrderDate}
                onDateSelected={() => setShowDateModal(false)}
                hideHeader={true}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

