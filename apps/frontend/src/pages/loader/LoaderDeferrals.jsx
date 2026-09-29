import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const MOCK_DEFERRALS = [
  {
    id: 'DEF-1042',
    orderId: 'ORD-1042',
    depot: 'peliyagoda',
    outlet: 'Kandana Express',
    originalDate: '29 Sep',
    newDate: '30 Sep',
    reason: 'Vehicle capacity',
    status: 'Removed from load',
    items: [
      { product: 'Fresh Whole Milk 1L', quantity: 20, unit: 'crates' },
      { product: 'Casual Dresses', quantity: 4, unit: 'cartons' }
    ],
    trip: 'TRIP-P01-04',
    vehicle: 'VEH011',
    note: 'Removed from current loading plan.'
  },
  {
    id: 'DEF-1045',
    orderId: 'ORD-1045',
    depot: 'peliyagoda',
    outlet: 'Ragama Tech Mart',
    originalDate: '29 Sep',
    newDate: '01 Oct',
    reason: 'Inventory shortage',
    status: 'Deferred',
    items: [
      { product: 'Samsung Microwave 23L', quantity: 2, unit: 'units' },
      { product: 'Laptop Accessories Kit', quantity: 5, unit: 'boxes' }
    ],
    trip: null,
    vehicle: null,
    note: 'Not staged for loading.'
  },
  {
    id: 'DEF-2011',
    orderId: 'ORD-2011',
    depot: 'kandy',
    outlet: 'Kandy City Mart',
    originalDate: '29 Sep',
    newDate: '30 Sep',
    reason: 'Vehicle breakdown',
    status: 'Scheduled for revised date',
    items: [
      { product: 'Premium Rice 5kg', quantity: 15, unit: 'bags' },
      { product: 'Cooking Oil 1L', quantity: 10, unit: 'bottles' }
    ],
    trip: 'TRIP-K03-02',
    vehicle: 'VEH-K02',
    note: 'Rescheduled to tomorrow morning dispatch.'
  }
];

export default function LoaderDeferrals({ user }) {
  const currentDepot = user?.depot || 'peliyagoda';
  const deferrals = MOCK_DEFERRALS.filter(d => d.depot === currentDepot);
  const [expandedId, setExpandedId] = useState(null);

  return (
    <div className="p-4 sm:p-6 bg-white min-h-full">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-slate-900">Deferrals</h2>
        <p className="text-sm text-slate-500">Deferred orders affecting this depot</p>
      </div>

      {deferrals.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-slate-900 font-bold mb-1">No deferred goods</p>
          <p className="text-slate-500 text-sm">Deferred loading records will appear here.</p>
        </div>
      ) : (
        <div className="border border-slate-200 rounded overflow-hidden">
          {/* Header */}
          <div className="hidden lg:grid grid-cols-[1fr_1.5fr_1fr_1fr_1fr_1.5fr_1.5fr] gap-4 px-4 py-3 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
            <div>Order</div>
            <div>Outlet</div>
            <div>Orig. Date</div>
            <div>New Date</div>
            <div>Goods</div>
            <div>Reason</div>
            <div>Status</div>
          </div>
          {/* List */}
          <div className="divide-y divide-slate-200">
            {deferrals.map(def => {
              const isExpanded = expandedId === def.id;
              
              return (
                <div key={def.id} className="bg-white">
                  <div 
                    onClick={() => setExpandedId(isExpanded ? null : def.id)}
                    className="p-4 lg:py-3 cursor-pointer hover:bg-slate-50 transition-colors"
                  >
                    <div className="lg:hidden space-y-2">
                      {/* Mobile/Tablet Layout */}
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-bold text-slate-900">{def.orderId}</div>
                          <div className="text-sm text-slate-600">{def.outlet}</div>
                        </div>
                        <div className="text-right flex flex-col items-end">
                          <div className="text-sm font-semibold text-slate-700">{def.items.length} items</div>
                        </div>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <div className="text-slate-500">{def.originalDate} → {def.newDate}</div>
                        <div className="flex items-center gap-1 text-slate-400">
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </div>
                      </div>
                      <div className="text-sm text-slate-700 font-medium">{def.status}</div>
                    </div>

                    {/* Desktop Layout */}
                    <div className="hidden lg:grid grid-cols-[1fr_1.5fr_1fr_1fr_1fr_1.5fr_1.5fr] gap-4 items-center">
                      <div className="font-bold text-slate-900 text-sm">{def.orderId}</div>
                      <div className="text-sm text-slate-700">{def.outlet}</div>
                      <div className="text-sm text-slate-600">{def.originalDate}</div>
                      <div className="text-sm text-slate-600">{def.newDate}</div>
                      <div className="text-sm text-slate-700">{def.items.length} items</div>
                      <div className="text-sm text-slate-700 truncate" title={def.reason}>{def.reason}</div>
                      <div className="text-sm text-slate-700 font-medium">{def.status}</div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div className="px-4 py-4 bg-[#f8faf9] border-t border-slate-100 text-sm">
                      <div className="grid sm:grid-cols-2 gap-6">
                        {/* Details */}
                        <div className="space-y-3">
                          <div className="grid grid-cols-[100px_1fr] gap-2">
                            <span className="text-slate-500">Order:</span>
                            <span className="font-bold text-slate-900">{def.orderId}</span>
                          </div>
                          <div className="grid grid-cols-[100px_1fr] gap-2">
                            <span className="text-slate-500">Outlet:</span>
                            <span className="text-slate-700">{def.outlet}</span>
                          </div>
                          <div className="grid grid-cols-[100px_1fr] gap-2">
                            <span className="text-slate-500">Delivery:</span>
                            <span className="text-slate-700">{def.originalDate} → {def.newDate}</span>
                          </div>
                          <div className="grid grid-cols-[100px_1fr] gap-2">
                            <span className="text-slate-500">Reason:</span>
                            <span className="text-slate-700">{def.reason}</span>
                          </div>
                          
                          {(def.trip || def.vehicle || def.note) && (
                            <div className="pt-3 mt-3 border-t border-slate-200 space-y-1.5">
                              {def.trip && (
                                <div className="grid grid-cols-[100px_1fr] gap-2">
                                  <span className="text-slate-500">Trip:</span>
                                  <span className="text-slate-700">{def.trip}</span>
                                </div>
                              )}
                              {def.vehicle && (
                                <div className="grid grid-cols-[100px_1fr] gap-2">
                                  <span className="text-slate-500">Vehicle:</span>
                                  <span className="text-slate-700">{def.vehicle}</span>
                                </div>
                              )}
                              {def.note && (
                                <div className="grid grid-cols-[100px_1fr] gap-2">
                                  <span className="text-slate-500">Operational note:</span>
                                  <span className="text-slate-700">{def.note}</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>

                        {/* Affected Goods */}
                        <div>
                          <div className="font-bold text-slate-900 mb-2">Affected goods</div>
                          <div className="border border-slate-200 rounded overflow-hidden bg-white">
                            <table className="w-full text-left">
                              <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                                <tr>
                                  <th className="px-3 py-2">Product</th>
                                  <th className="px-3 py-2 text-right">Quantity</th>
                                  <th className="px-3 py-2">Unit</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100">
                                {def.items.map((item, idx) => (
                                  <tr key={idx}>
                                    <td className="px-3 py-2 text-slate-700 font-medium">{item.product}</td>
                                    <td className="px-3 py-2 text-slate-900 font-bold text-right">{item.quantity}</td>
                                    <td className="px-3 py-2 text-slate-500">{item.unit}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
