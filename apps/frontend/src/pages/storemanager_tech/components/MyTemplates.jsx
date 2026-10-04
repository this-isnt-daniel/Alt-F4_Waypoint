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
    <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4 pb-24 md:pb-10 min-h-0 bg-white">
      <div className="max-w-screen-md mx-auto space-y-8">

        {/* ── Recent Orders ── */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Clock size={16} className="text-slate-400" />
            <h2 className="text-[12px] font-bold text-slate-700 uppercase tracking-wider">
              Recent Orders (Last 10 days)
            </h2>
          </div>

          {RECENT_ORDERS.length === 0 ? (
            <div className="bg-slate-50 border border-slate-100 rounded-lg p-5 text-center">
              <p className="text-[13px] font-medium text-slate-600">No recent orders found.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {RECENT_ORDERS.map((order) => (
                <div key={order.id} className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[13px] font-semibold text-slate-900">{order.date}</span>
                      <span className="text-[12px] font-medium text-slate-500">· {order.id}</span>
                    </div>
                    <p className="text-[13px] text-slate-700 mb-0.5 font-medium">{order.items.length} products</p>
                    <p className="text-[12px] text-slate-500">{order.categories}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onUseTemplate(order.items, 'order')}
                    className="shrink-0 self-start md:self-auto px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-[13px] font-semibold rounded-md transition-colors flex items-center gap-1.5"
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
            <FileText size={16} className="text-slate-400" />
            <h2 className="text-[12px] font-bold text-slate-700 uppercase tracking-wider">
              Saved Templates
            </h2>
          </div>

          {SAVED_TEMPLATES.length === 0 ? (
            <div className="bg-slate-50 border border-slate-100 rounded-lg p-5 text-center">
              <p className="text-[13px] font-medium text-slate-600 mb-2">No templates saved yet.</p>
              <p className="text-[12px] text-slate-500 max-w-sm mx-auto">
                Build an order in the catalogue and save it as a template for faster future ordering.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {SAVED_TEMPLATES.map((template) => (
                <div key={template.id} className="bg-white border border-slate-200 rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm group">
                  <div className="flex-1 min-w-0">
                    {renamingId === template.id ? (
                      <div className="flex items-center gap-2 mb-1">
                        <input
                          type="text"
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleRename()}
                          autoFocus
                          className="text-[14px] font-bold text-slate-900 border border-brand-300 bg-brand-50 rounded px-1.5 py-0.5 outline-none focus:ring-2 focus:ring-brand-500 w-full max-w-[200px]"
                        />
                        <button onClick={handleRename} className="text-brand-600 p-1 hover:bg-brand-50 rounded"><Save size={14} /></button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[14px] font-bold text-slate-900 truncate">{template.name}</span>
                        <button
                          onClick={() => startRenaming(template.id, template.name)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-brand-600 p-1"
                          aria-label="Rename template"
                        >
                          <Edit2 size={13} />
                        </button>
                      </div>
                    )}
                    <p className="text-[13px] text-slate-700 mb-0.5 font-medium">{template.items.length} products</p>
                    <p className="text-[12px] text-slate-500">{template.lastUsedText}</p>
                  </div>
                  
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => onEditTemplate(template)}
                      className="px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-[13px] font-semibold rounded-md transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => onUseTemplate(template.items, 'template')}
                      className="px-4 py-2 bg-brand-50 border border-brand-200 hover:bg-brand-100 text-brand-700 text-[13px] font-semibold rounded-md transition-colors flex items-center gap-1.5"
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
