import { X } from "lucide-react";
import { useNavigator } from "@/router/navigator";

export function AccountSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { push } = useNavigator();

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="absolute inset-0 z-[2000] bg-slate-900/20 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* Floating Panel (Top Right) */}
      <div className="absolute top-16 right-4 z-[2010] w-64 bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-4 border-b border-slate-100">
          <div>
            <h3 className="text-[16px] font-bold text-slate-900 leading-tight">Ayubowan, Daniru</h3>
            <p className="text-[13px] text-slate-500 mt-0.5">Driver · VEH014</p>
          </div>
          <button 
            type="button"
            onClick={onClose}
            className="p-1 -mr-1 -mt-1 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
          >
            <X size={18} />
          </button>
        </div>
        
        {/* Menu Items */}
        <div className="p-2 space-y-1">
          <button 
            type="button"
            className="w-full text-left px-3 py-2.5 rounded-lg text-[14px] font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Settings
          </button>
          <button 
            type="button"
            onClick={() => {
              onClose();
              push("signin");
            }}
            className="w-full text-left px-3 py-2.5 rounded-lg text-[14px] font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    </>
  );
}
