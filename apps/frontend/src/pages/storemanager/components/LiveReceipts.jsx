import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../../lib/api';

export default function LiveReceipts() {
  const [orders, setOrders] = useState([]);
  const [message, setMessage] = useState('');
  const [selected, setSelected] = useState(null);
  const [details, setDetails] = useState(null);
  const [issue, setIssue] = useState({product_id: '', reason_code: 'missing', reported_qty: 1, note: ''});
  const [hasIssue, setHasIssue] = useState(false);
  const [busy, setBusy] = useState(false);
  const [operationId, setOperationId] = useState(null);
  useEffect(() => { apiFetch('/store-manager/orders').then(setOrders).catch(e => setMessage(e.message)); }, []);
  async function open(order) {
    setSelected(order); setDetails(null); setMessage(''); setHasIssue(false);
    setOperationId(crypto.randomUUID());
    setIssue({ product_id: order.items[0]?.product_id || '', reason_code: 'missing', reported_qty: 1, note: '' });
    try { setDetails(await apiFetch(`/store-manager/orders/${encodeURIComponent(order.order_id)}/receipt-details`)); }
    catch (e) { setMessage(e.message); }
  }
  async function confirm() {
    setBusy(true); setMessage('');
    try {
      const result = await apiFetch(`/store-manager/orders/${encodeURIComponent(selected.order_id)}/receipt`, {
        method: 'POST', body: JSON.stringify({client_op_id: operationId, pod_id: details.pod_id, items_ok: !hasIssue,
          discrepancies: hasIssue ? [{...issue, reported_qty: Number(issue.reported_qty)}] : []}),
      });
      setDetails(d => ({...d, confirm_id: result.confirm_id}));
      setMessage('Receipt saved.');
    } catch (e) { setMessage(e.message); }
    finally { setBusy(false); }
  }
  return <div className="p-5 space-y-4 overflow-y-auto h-full">
    <h2 className="text-xl font-bold">Receipts</h2>
    {orders.filter(o => ['delivered', 'out_for_delivery'].includes(o.status)).map(o => <button key={o.order_id} className="block border rounded p-3 w-full text-left" onClick={() => open(o)}>{o.order_id} · {o.status} · {o.order_date}</button>)}
    {selected && details && <section className="border rounded p-4 space-y-3">
      <h3 className="font-bold">{selected.order_id}</h3>
      {details.confirm_id ? <p>Receipt already recorded: {details.confirm_id}</p> : !details.pod_id ? <p>Waiting for the driver's proof of delivery.</p> : <>
        <label className="block"><input type="checkbox" checked={hasIssue} onChange={e => setHasIssue(e.target.checked)} /> Report a discrepancy</label>
        {hasIssue && <div className="space-y-2">
          <select aria-label="Product" value={issue.product_id} onChange={e => setIssue(i => ({...i, product_id:e.target.value}))}>{selected.items.map(i => <option key={i.line_item_id} value={i.product_id}>{i.product_id}</option>)}</select>
          <select aria-label="Reason" value={issue.reason_code} onChange={e => setIssue(i => ({...i, reason_code:e.target.value}))}>{['missing','damaged','wrong_item','short_qty','other'].map(r => <option key={r}>{r}</option>)}</select>
          <input aria-label="Affected quantity" type="number" min="1" step="1" value={issue.reported_qty} onChange={e => setIssue(i => ({...i, reported_qty:e.target.value}))} className="border p-2 w-24" />
          <input aria-label="Issue note" placeholder="Issue note" value={issue.note} onChange={e => setIssue(i => ({...i, note:e.target.value}))} className="border p-2" />
        </div>}
        <button disabled={busy} onClick={confirm} className="bg-emerald-700 text-white rounded px-4 py-2">{busy ? 'Saving…' : 'Confirm receipt'}</button>
      </>}
    </section>}
    {message && <p role="status">{message}</p>}
  </div>;
}
