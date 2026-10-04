import React, { useState } from 'react';
import SMLayout from './components/SMLayout';
import OverviewTab from './components/OverviewTab';
import PlaceOrderTab from './components/PlaceOrderTab';
import OrdersTab from './components/OrdersTab';
import ReceiptsTab from './components/ReceiptsTab';
import ReceiptsHistoryTab from './components/ReceiptsHistoryTab';

/**
 * StoreManagerOverview
 * Root of the Store Manager portal.
 * Holds global state (active tab, basket, receipt confirmation).
 */
export default function StoreManagerOverview({ onLogout, user, outlet }) {
  const [activeTab, setActiveTab]     = useState('overview');
  const [activeTabParams, setActiveTabParams] = useState(null);
  const [basket, setBasket]           = useState([]);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [orderDate, setOrderDate]     = useState('2026-09-30');

  // Delivery arrival & OTP state
  const [deliveryArrived, setDeliveryArrived] = useState(true);
  const [deliveryOtp, setDeliveryOtp]         = useState('482 910');
  const [showOtpModal, setShowOtpModal]       = useState(false);

  const navigate = (tab, params = null) => {
    setActiveTab(tab);
    setActiveTabParams(params);
  };

  const handleConfirmDelivery = () => {
    setDeliveryArrived(false);
    setIsConfirmed(true);
    setShowOtpModal(false);
    navigate('receipts');
  };

  // ── Basket operations hoisted for global search access ──
  const setQty = (product, variant, qty) => {
    const key = `${product.id}-${variant ?? ''}`;
    setBasket((prev) => {
      const existing = prev.findIndex((b) => b.key === key);
      if (qty <= 0) {
        return prev.filter((b) => b.key !== key);
      }
      const item = {
        key,
        productId:    product.id,
        productName:  product.name,
        variant:      variant ?? null,
        packSize:     product.packSize,
        unit:         product.unit,
        qty,
        categoryId:   product.categoryId,
        categoryName: product.categoryName,
        subcategoryId: product.subcategoryId,
        quantityType: product.quantityType,
      };
      if (existing >= 0) {
        const next = [...prev];
        next[existing] = item;
        return next;
      }
      return [...prev, item];
    });
  };

  const removeItem = (key) => setBasket((prev) => prev.filter((b) => b.key !== key));

  const changeQty = (key, qty) => {
    if (qty <= 0) return removeItem(key);
    setBasket((prev) => prev.map((b) => (b.key === key ? { ...b, qty } : b)));
  };

  const clearBasket = () => setBasket([]);
  const replaceBasket = (items) => setBasket([...items]);

  return (
    <SMLayout
      activeTab={activeTab}
      setActiveTab={(tab) => navigate(tab, null)}
      onLogout={onLogout}
      basketCount={basket.length}
      user={user}
      outlet={outlet}
      deliveryArrived={deliveryArrived}
      deliveryOtp={deliveryOtp}
      showOtpModal={showOtpModal}
      setShowOtpModal={setShowOtpModal}
      onConfirmDelivery={handleConfirmDelivery}
    >
      <div className="h-full w-full overflow-hidden">
        {activeTab === 'overview' && (
          <OverviewTab
            onNavigate={navigate}
            isConfirmed={isConfirmed}
            setIsConfirmed={setIsConfirmed}
            basket={basket}
            onSetQty={setQty}
            deliveryArrived={deliveryArrived}
            onOpenOtpModal={() => setShowOtpModal(true)}
          />
        )}

        {activeTab === 'order' && (
          <PlaceOrderTab
            basket={basket}
            onSetQty={setQty}
            onRemoveItem={removeItem}
            onChangeQty={changeQty}
            onClearBasket={clearBasket}
            onReplaceBasket={replaceBasket}
            orderDate={orderDate}
            setOrderDate={setOrderDate}
            outlet={outlet}
          />
        )}

        {activeTab === 'progress' && <OrdersTab selectedOrderId={activeTabParams} />}

        {activeTab === 'receipts' && <ReceiptsTab isConfirmed={isConfirmed} onNavigate={navigate} />}

        {activeTab.startsWith('history-') && (
          <ReceiptsHistoryTab
            type={activeTab.replace('history-', '')}
            onNavigate={navigate}
          />
        )}
      </div>
    </SMLayout>
  );
}
