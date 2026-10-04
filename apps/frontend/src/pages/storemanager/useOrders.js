import { useState, useEffect } from 'react';
import { apiFetch } from '../../lib/api';

export function useOrders() {
  const [orders, setOrders] = useState([]);
  const [deferrals, setDeferrals] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchOrders = async () => {
    try {
      const data = await apiFetch('/store-manager/orders');
      const defs = await apiFetch('/store-manager/deferrals').catch(()=>[]);
      
      const todayStr = new Date().toISOString().split('T')[0];
      
      const mappedOrders = data.map(o => ({
        id: o.order_id,
        status: o.status,
        deliveryDate: o.order_date === todayStr ? 'today' : o.order_date,
        type: o.temp_req,
        expectedArrival: o.window_open ? `${o.window_open} - ${o.window_close}` : 'TBD',
        eta: o.exp_arrival || null,
        totalProducts: o.order_units || 0,
        ...o
      }));

      setOrders(mappedOrders);
      setDeferrals(defs);
    } catch (err) {
      console.error("Failed to fetch orders", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  return { orders, deferrals, loading, refetch: fetchOrders };
}
