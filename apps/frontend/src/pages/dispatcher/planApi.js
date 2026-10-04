import { apiFetch } from '../../lib/api';

// Persist exactly the whole-order placements shown on the board; let the backend
// recalculate every hard constraint. Unplaced orders are explicit deferrals.
export async function confirmBoard(rows, tray, targetDate, note) {
  const plan = await apiFetch('/dispatcher/plans/draft', {
    method: 'POST', body: JSON.stringify({target_date: targetDate}),
  });
  const deferred = new Set((plan.deferred_orders || []).map(o => o.order_ref));
  const actions = [];
  for (const row of rows) {
    for (const orderRef of new Set(row.cards.map(card => card.orderId))) {
      actions.push({action_type: deferred.has(orderRef) ? 'reinstate_whole_order' : 'move_whole_order',
        order_ref: orderRef, target_vehicle_id: row.vehicleId, target_trip_number: 1});
    }
  }
  for (const orderRef of new Set(tray.map(card => card.orderId))) {
    if (!deferred.has(orderRef)) actions.push({action_type: 'defer_whole_order', order_ref: orderRef,
      reason: 'MANUAL_DISPATCHER_DEFERRAL', detail: note || 'Deferred in allocation board'});
  }
  await apiFetch(`/dispatcher/plans/${plan.plan_id}/edit`, {method: 'POST', body: JSON.stringify({actions})});
  // The approval API independently checks validation and refuses stale fleet/order state.
  return apiFetch(`/dispatcher/plans/${plan.plan_id}/approve`, {method:'POST', body:JSON.stringify({client_op_id:crypto.randomUUID()})});
}
