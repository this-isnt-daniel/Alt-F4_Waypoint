import React, { useState } from 'react';
import { FileText, Clock, Edit2, Play, Save } from 'lucide-react';
import { RECENT_ORDERS, SAVED_TEMPLATES, renameSavedTemplate } from '../data/templates';

export default function MyTemplates({ onUseTemplate, onEditTemplate }) {
  const [renamingId, setRenamingId] = useState(null);
  const [renameValue, setRenameValue] = useState('');

  const startRenaming = (id, currentName) => {
    setRenamingId(id);
    setRenameValue(currentName);
  };

  const handleRename = () => {
    if (renameValue.trim()) {
      renameSavedTemplate(renamingId, renameValue.trim());
    }
    setRenamingId(null);
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4 pb-24 md:pb-10 min-h-0 bg-white dark:bg-[#0B0F17]">
      <div className="max-w-screen-md mx-auto space-y-8">

        {/* ── Recent Orders ── */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Clock size={16} className="text-slate-400 dark:text-slate-500" />
            <h2 className="text-[12px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Recent Orders (Last 10 days)
            </h2>
          </div>

          {RECENT_ORDERS.length === 0 ? (
            <div className="bg-slate-50 dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-lg p-5 text-center">
              <p className="text-[13px] font-medium text-slate-600 dark:text-slate-300">No recent orders found.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {RECENT_ORDERS.map((order) => (
                <div key={order.id} className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[13px] font-semibold text-slate-900 dark:text-[#F8FAFC]">{order.date}</span>
                      <span className="text-[12px] font-medium text-slate-500 dark:text-slate-400">· {order.id}</span>
                    </div>
                    <p className="text-[13px] text-slate-700 dark:text-slate-300 mb-0.5 font-medium">{order.items.length} products</p>
                    <p className="text-[12px] text-slate-500 dark:text-slate-400">{order.categories}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onUseTemplate(order.items, 'order')}
                    className="shrink-0 self-start md:self-auto px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-[13px] font-semibold rounded-md transition-colors flex items-center gap-1.5 cursor-pointer"
                  >
                    <Play size={14} /> Use Order
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* ── Saved Templates ── */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <FileText size={16} className="text-slate-400 dark:text-slate-500" />
            <h2 className="text-[12px] font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Saved Templates
            </h2>
          </div>

          {SAVED_TEMPLATES.length === 0 ? (
            <div className="bg-slate-50 dark:bg-[#111827] border border-slate-100 dark:border-slate-800 rounded-lg p-5 text-center">
              <p className="text-[13px] font-medium text-slate-600 dark:text-slate-300 mb-2">No templates saved yet.</p>
              <p className="text-[12px] text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
                Build an order in the catalogue and save it as a template for faster future ordering.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {SAVED_TEMPLATES.map((template) => (
                <div key={template.id} className="bg-white dark:bg-[#111827] border border-slate-200 dark:border-slate-800 rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm group">
                  <div className="flex-1 min-w-0">
                    {renamingId === template.id ? (
                      <div className="flex items-center gap-2 mb-1">
                        <input
                          type="text"
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleRename()}
                          autoFocus
                          className="text-[14px] font-bold text-slate-900 dark:text-[#F8FAFC] border border-brand-300 dark:border-emerald-600 bg-brand-50 dark:bg-emerald-950/40 rounded px-1.5 py-0.5 outline-none focus:ring-2 focus:ring-brand-500 dark:focus:ring-emerald-500 w-full max-w-[200px]"
                        />
                        <button onClick={handleRename} className="text-brand-600 dark:text-emerald-400 p-1 hover:bg-brand-50 dark:hover:bg-emerald-950/50 rounded cursor-pointer"><Save size={14} /></button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[14px] font-bold text-slate-900 dark:text-[#F8FAFC] truncate">{template.name}</span>
                        <button
                          onClick={() => startRenaming(template.id, template.name)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 dark:text-slate-500 hover:text-brand-600 dark:hover:text-emerald-400 p-1 cursor-pointer"
                          aria-label="Rename template"
                        >
                          <Edit2 size={13} />
                        </button>
                      </div>
                    )}
                    <p className="text-[13px] text-slate-700 dark:text-slate-300 mb-0.5 font-medium">{template.items.length} products</p>
                    <p className="text-[12px] text-slate-500 dark:text-slate-400">{template.lastUsedText}</p>
                  </div>
                  
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => onEditTemplate(template)}
                      className="px-4 py-2 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-[13px] font-semibold rounded-md transition-colors cursor-pointer"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => onUseTemplate(template.items, 'template')}
                      className="px-4 py-2 bg-brand-50 dark:bg-emerald-950/40 border border-brand-200 dark:border-emerald-800 hover:bg-brand-100 dark:hover:bg-emerald-900/40 text-brand-700 dark:text-emerald-300 text-[13px] font-semibold rounded-md transition-colors flex items-center gap-1.5 cursor-pointer"
                    >
                      <Play size={14} /> Use Template
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

      </div>
    </div>
  );
}
