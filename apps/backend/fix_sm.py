import os
import re

# Paths
SM_DIR = r"c:\Users\shami\OneDrive\Documents\GitHub\Alt-F4_Waypoint\apps\frontend\src\pages\storemanager"
OVERVIEW_TAB = os.path.join(SM_DIR, "components", "OverviewTab.jsx")
ORDERS_TAB = os.path.join(SM_DIR, "components", "OrdersTab.jsx")
PLACE_ORDER_TAB = os.path.join(SM_DIR, "components", "PlaceOrderTab.jsx")

def patch_overview_tab():
    with open(OVERVIEW_TAB, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace imports
    content = content.replace("import { ACTIVE_ORDERS, DEFERRED_ORDERS } from '../data/orders';", "import { useOrders } from '../useOrders';")
    
    # Inject hook inside component
    target = "export default function OverviewTab({ onNavigate, isConfirmed, setIsConfirmed, deliveryArrived = true, onOpenOtpModal }) {"
    if target in content:
        replacement = target + "\n  const { orders: ACTIVE_ORDERS, deferrals: DEFERRED_ORDERS, loading } = useOrders();\n  if (loading) return <div className=\"p-8\">Loading...</div>;"
        content = content.replace(target, replacement)
        
    target2 = "export default function OverviewTab({ onNavigate, isConfirmed, setIsConfirmed, basket, onSetQty, deliveryArrived, onOpenOtpModal }) {"
    if target2 in content:
        replacement = target2 + "\n  const { orders: ACTIVE_ORDERS, deferrals: DEFERRED_ORDERS, loading } = useOrders();\n  if (loading) return <div className=\"p-8\">Loading...</div>;"
        content = content.replace(target2, replacement)
    
    with open(OVERVIEW_TAB, "w", encoding="utf-8") as f:
        f.write(content)

def patch_orders_tab():
    with open(ORDERS_TAB, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("import { ACTIVE_ORDERS, DEFERRED_ORDERS, ORDER_STAGES, getStageIndex } from '../data/orders';", "import { ORDER_STAGES, getStageIndex } from '../data/orders';\nimport { useOrders } from '../useOrders';")
    
    target = "export default function OrdersTab({ selectedOrderId }) {"
    if target in content:
        replacement = target + "\n  const { orders: ACTIVE_ORDERS, deferrals: DEFERRED_ORDERS, loading } = useOrders();\n  if (loading) return <div className=\"p-8\">Loading...</div>;"
        content = content.replace(target, replacement)
        
    with open(ORDERS_TAB, "w", encoding="utf-8") as f:
        f.write(content)

def patch_place_order_tab():
    with open(PLACE_ORDER_TAB, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "import { apiFetch } from '../../lib/api';" not in content:
        content = content.replace("import React, { useState, useEffect, useRef } from 'react';", "import React, { useState, useEffect, useRef } from 'react';\nimport { apiFetch } from '../../lib/api';")
    
    # Update handleConfirmOrder to make API calls
    old_handle_confirm = """  const handleConfirmOrder = () => {
    onClearBasket();
    setView('success');
  };"""
    
    new_handle_confirm = """  const handleConfirmOrder = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const selectedDateStr = orderDate && orderDate.includes('Oct') ? `2026-10-${orderDate.split('Oct ')[1]}` : (orderDate && orderDate.includes('Sep') ? `2026-09-${orderDate.split('Sep ')[1]}` : today); // crude mock to date
      
      const payload = {
        outlet_id: 'OUT-0043',
        brand: 'fresh',
        temp_req: basket.some(b => ['chilled', 'frozen'].includes(b.tempRequired || '')) ? 'chilled' : 'dry',
        order_date: selectedDateStr,
        items: basket.map(b => ({
          product_id: b.productId,
          quantity: b.qty
        }))
      };
      
      const res = await apiFetch('/store_manager/orders', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      
      await apiFetch(`/store_manager/orders/${res.order_id}/confirm`, {
        method: 'POST'
      });
      
      onClearBasket();
      setView('success');
    } catch (e) {
      console.error(e);
      alert("Failed to confirm order: " + e.message);
    }
  };"""
    
    content = content.replace(old_handle_confirm, new_handle_confirm)

    with open(PLACE_ORDER_TAB, "w", encoding="utf-8") as f:
        f.write(content)

print("Patching Store Manager components...")
patch_overview_tab()
patch_orders_tab()
patch_place_order_tab()
print("Done.")
