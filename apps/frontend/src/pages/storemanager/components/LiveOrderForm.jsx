import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../../lib/api';

// Order only canonical products. Presentation-only catalogues must never supply API IDs.
export default function LiveOrderForm() {
  const [outlet, setOutlet] = useState(null);
  const [products, setProducts] = useState([]);
  const [quantities, setQuantities] = useState({});
  const [date, setDate] = useState('');
  const [temperature, setTemperature] = useState('ambient');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const shop = await apiFetch('/store-manager/outlet');
        const catalog = await apiFetch(`/store-manager/products?brand=${encodeURIComponent(shop.brand)}`);
        if (active) { setOutlet(shop); setProducts(catalog); }
      } catch (e) { if (active) setMessage(e.message); }
    })();
    return () => { active = false; };
  }, []);
  const available = products.filter(p => p.temp_req === temperature);
  async function submit(event) {
    event.preventDefault();
    setBusy(true); setMessage('');
    try {
      const items = available.filter(p => Number(quantities[p.product_id]) > 0)
        .map(p => ({ product_id: p.product_id, quantity: Number(quantities[p.product_id]) }));
      if (!items.length) throw new Error('Select at least one product.');
      const draft = await apiFetch('/store-manager/orders', { method: 'POST', body: JSON.stringify({
        outlet_id: outlet.outlet_id, brand: outlet.brand, temp_req: temperature, order_date: date, items,
      }) });
      const confirmed = await apiFetch(`/store-manager/orders/${encodeURIComponent(draft.order_id)}/confirm`, { method: 'POST' });
      setQuantities({}); setMessage(`Order ${confirmed.order_id} confirmed. Awaiting allocation.`);
    } catch (e) { setMessage(e.message); }
    finally { setBusy(false); }
  }
  return <form onSubmit={submit} className="p-5 space-y-4 overflow-y-auto h-full">
    <h2 className="text-xl font-bold">Place order {outlet ? `— ${outlet.name}` : ''}</h2>
    <p>Orders close at 16:00 Sri Lanka time on the previous day. Submit ambient and chilled goods separately.</p>
    <label className="block">Delivery date <input aria-label="Delivery date" required type="date" value={date} onChange={e => setDate(e.target.value)} className="border rounded p-2" /></label>
    <label className="block">Temperature <select aria-label="Temperature" value={temperature} onChange={e => setTemperature(e.target.value)} className="border rounded p-2"><option value="ambient">Ambient</option><option value="chilled">Chilled</option></select></label>
    {available.map(p => <label key={p.product_id} className="flex items-center justify-between gap-3 border rounded p-3">
      <span>{p.name} · {p.unit} · {p.unit_wt_kg ?? '—'} kg</span>
      <input aria-label={`Quantity for ${p.name}`} type="number" min="0" step="1" value={quantities[p.product_id] || ''} onChange={e => setQuantities(q => ({...q, [p.product_id]: e.target.value}))} className="border rounded p-2 w-24" />
    </label>)}
    {outlet && !available.length && <p>No active products for this temperature.</p>}
    <button disabled={busy || !outlet} className="bg-emerald-700 text-white rounded px-4 py-2 disabled:opacity-50">{busy ? 'Saving…' : 'Confirm order'}</button>
    {message && <p role="status">{message}</p>}
  </form>;
}
