import React, { useState } from 'react';
import { ArrowLeft, Search, ChevronLeft, ChevronRight } from 'lucide-react';

const mockData = {
  received: Array.from({ length: 45 }).map((_, i) => ({
    id: `ORD-${1000 + i}`,
    date: `Sep ${Math.max(1, 30 - Math.floor(i / 2))}`,
    status: i % 3 === 0 ? 'Received in full' : 'Received with exceptions',
    statusColor: i % 3 === 0 ? 'text-[#059669]' : 'text-[#b45309]'
  })),
  'missing-damaged': Array.from({ length: 45 }).map((_, i) => ({
    id: `ORD-${1000 + i}`,
    item: i % 2 === 0 ? 'Butter 200g Salted' : 'Cream Cracker 500g Munchee',
    issue: i % 2 === 0 ? '2 short' : '1 short',
    note: 'Damaged during loading — noted by loader',
  })),
  deferrals: Array.from({ length: 45 }).map((_, i) => ({
    id: `ORD-${1000 + i}`,
    type: 'Chilled',
    newDate: `Oct ${Math.max(1, Math.floor(i / 2))}`,
    note: 'Fleet capacity was short; Fresh outlets prioritized by order age.',
  }))
};

const PAGE_SIZE = 20;

export default function ReceiptsHistoryTab({ type, onNavigate }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  // Reset page when search changes
  const handleSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  let title = 'History';
  if (type === 'received') title = 'Received Orders — History';
  if (type === 'missing-damaged') title = 'Missing & Damaged Goods — History';
  if (type === 'deferrals') title = 'Deferrals — History';

  const data = mockData[type] || [];
  const filtered = data.filter(d => d.id.toLowerCase().includes(search.toLowerCase()));
  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));
  
  const startIdx = (page - 1) * PAGE_SIZE;
  const currentItems = filtered.slice(startIdx, startIdx + PAGE_SIZE);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-screen-md mx-auto px-4 md:px-6 py-5 space-y-6 pb-10">
        
        {/* Header & Back Link */}
        <div>
          <button 
            onClick={() => onNavigate('receipts')}
            className="flex items-center gap-1.5 text-[13px] font-semibold text-slate-500 hover:text-slate-800 transition-colors mb-3 cursor-pointer"
          >
            <ArrowLeft size={14} strokeWidth={2.5} />
            Back to Receipts &amp; Deferrals
          </button>
          <h2 className="text-[19px] font-bold text-slate-900">{title}</h2>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={handleSearchChange}
              placeholder="Search by order ID..."
              className="w-full h-10 pl-9 pr-3 border border-slate-200 rounded-xl text-[13px] focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="shrink-0">
            <select className="h-10 px-3 border border-slate-200 rounded-xl text-[13px] text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 cursor-pointer outline-none">
              <option>Last 7 days</option>
              <option>Last month</option>
              <option>Last 90 days</option>
            </select>
          </div>
        </div>

        {/* List */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm divide-y divide-slate-50 overflow-hidden">
          {currentItems.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-[13px]">No records found.</div>
          ) : (
            currentItems.map((item, idx) => {
              if (type === 'received') {
                return (
                  <div key={idx} className="px-5 py-4 flex items-center justify-between text-[14px]">
                    <span className="text-slate-700">{item.id} · {item.date}</span>
                    <span className={`font-semibold ${item.statusColor}`}>{item.status}</span>
                  </div>
                );
              }
              if (type === 'missing-damaged') {
                return (
                  <div key={idx} className="px-5 py-4 flex items-start justify-between">
                    <div>
                      <p className="text-[14px] font-bold text-slate-900">{item.item} · {item.issue}</p>
                      <p className="text-[12.5px] text-slate-400 mt-0.5">{item.note}</p>
                    </div>
                    <span className="text-[12.5px] text-slate-400">{item.id}</span>
                  </div>
                );
              }
              if (type === 'deferrals') {
                return (
                  <div key={idx} className="px-5 py-4">
                    <p className="text-[14px] font-bold text-slate-900">{item.id} · {item.type} <span className="font-normal text-slate-800">— moved to</span> {item.newDate}</p>
                    <p className="text-[12.5px] text-slate-400 mt-0.5">{item.note}</p>
                  </div>
                );
              }
              return null;
            })
          )}
        </div>

        {/* Pagination */}
        {totalPages > 0 && (
          <div className="flex items-center justify-between pt-2">
            <span className="text-[12px] font-medium text-slate-500">
              Showing {startIdx + 1}–{Math.min(startIdx + PAGE_SIZE, totalItems)} of {totalItems}
            </span>
            <div className="flex gap-2">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="h-8 px-3 rounded-lg border border-slate-200 text-[12px] font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 transition-colors"
              >
                <ChevronLeft size={14} /> Previous
              </button>
              <button 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="h-8 px-3 rounded-lg border border-slate-200 text-[12px] font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1 transition-colors"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
