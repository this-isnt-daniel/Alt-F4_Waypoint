import React, { useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, RefreshCcw } from 'lucide-react';
import { fetchLoaderDeferrals } from './loaderApi';



export default function LoaderDeferrals({ user }) {
  const [deferrals, setDeferrals] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadDeferrals = async () => {
    setLoading(true);
    setError('');
    try {
      const rows = user?.token ? await fetchLoaderDeferrals(user.token) : [];
      setDeferrals(rows);
    } catch (err) {
      setError(err.message);
      setDeferrals([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDeferrals();
  }, [user?.token]);

  return (
    <div className="p-4 sm:p-6 bg-white min-h-full">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Deferrals</h2>
          <p className="text-sm text-slate-500">Deferred orders affecting this depot</p>
          {error && <p className="text-[12px] text-amber-700 mt-2">{error}</p>}
        </div>
        <button
          onClick={loadDeferrals}
          disabled={loading}
          className="text-[12px] font-bold text-brand-700 flex items-center gap-1 disabled:opacity-50"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          {loading ? 'Refreshing' : 'Refresh'}
        </button>
      </div>

      {deferrals.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-slate-900 font-bold mb-1">No deferred goods</p>
          <p className="text-slate-500 text-sm">Deferred loading records will appear here.</p>
        </div>
      ) : (
        <div className="border border-slate-200 rounded overflow-hidden">
          <div className="hidden lg:grid grid-cols-[1fr_1.5fr_1fr_1fr_1fr_1.5fr] gap-4 px-4 py-3 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
            <div>Order</div>
            <div>Outlet</div>
            <div>Original</div>
            <div>New</div>
            <div>Goods</div>
            <div>Reason</div>
          </div>
          <div className="divide-y divide-slate-200">
            {deferrals.map((deferral) => {
              const isExpanded = expandedId === deferral.deferral_id;
              return (
                <div key={deferral.deferral_id} className="bg-white">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : deferral.deferral_id)}
                    className="w-full p-4 lg:py-3 cursor-pointer hover:bg-slate-50 transition-colors text-left"
                  >
                    <div className="lg:hidden space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-bold text-slate-900">{deferral.order_id}</div>
                          <div className="text-sm text-slate-600">{deferral.outlet_name || deferral.outlet_id}</div>
                        </div>
                        <div className="text-sm font-semibold text-slate-700">{deferral.items.length} items</div>
                      </div>
                      <div className="flex justify-between items-center text-sm">
                        <div className="text-slate-500">{deferral.original_date} to {deferral.new_date}</div>
                        {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                      </div>
                    </div>

                    <div className="hidden lg:grid grid-cols-[1fr_1.5fr_1fr_1fr_1fr_1.5fr] gap-4 items-center">
                      <div className="font-bold text-slate-900 text-sm">{deferral.order_id}</div>
                      <div className="text-sm text-slate-700">{deferral.outlet_name || deferral.outlet_id}</div>
                      <div className="text-sm text-slate-600">{deferral.original_date}</div>
                      <div className="text-sm text-slate-600">{deferral.new_date}</div>
                      <div className="text-sm text-slate-700">{deferral.items.length} items</div>
                      <div className="text-sm text-slate-700 truncate" title={deferral.reason}>{deferral.reason || 'No reason'}</div>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="px-4 py-4 bg-[#f8faf9] border-t border-slate-100 text-sm">
                      <div className="grid sm:grid-cols-2 gap-6">
                        <div className="space-y-3">
                          <Info label="Deferral" value={deferral.deferral_id} />
                          <Info label="Order" value={deferral.order_id} />
                          <Info label="Outlet" value={deferral.outlet_name || deferral.outlet_id} />
                          <Info label="Delivery" value={`${deferral.original_date} to ${deferral.new_date}`} />
                          <Info label="Trip" value={deferral.trip_id || 'Not assigned'} />
                          <Info label="Reason" value={deferral.reason || 'No reason'} />
                        </div>

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
                                {deferral.items.map((item) => (
                                  <tr key={item.line_item_id}>
                                    <td className="px-3 py-2 text-slate-700 font-medium">{item.product_name || item.product_id}</td>
                                    <td className="px-3 py-2 text-slate-900 font-bold text-right">{item.assigned_qty}</td>
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

function Info({ label, value }) {
  return (
    <div className="grid grid-cols-[100px_1fr] gap-2">
      <span className="text-slate-500">{label}:</span>
      <span className="text-slate-700 font-medium">{value}</span>
    </div>
  );
}
