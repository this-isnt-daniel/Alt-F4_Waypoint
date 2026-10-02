import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { CloudOff, RefreshCcw, CheckCircle2, ArrowLeft } from "lucide-react";

export function SyncCentreScreen() {
  const { push } = useNavigator();
  const { connection, setConnection, syncRecords } = useDriverState();
  const isOnline = connection === "online";
  
  const pendingCount = syncRecords.filter(r => r.state === "pending").length;
  const syncedRecords = syncRecords.filter(r => r.state === "synced");
  const lastSynced = syncedRecords[0]?.createdAt ?? "Never";

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-slate-50 px-5 py-6">
      <div className="flex items-center gap-3 mb-8">
        <button type="button" onClick={() => push("active-trip")} className="p-1.5 -ml-1.5 rounded-full text-slate-500 hover:bg-slate-200 transition-colors">
          <ArrowLeft size={22} />
        </button>
        <h1 className="text-[24px] font-bold text-slate-900">SYNC</h1>
      </div>

      <div className="mb-8">
        <div className="flex justify-between items-baseline border-b border-slate-200 pb-4 mb-4">
          <span className="text-[14px] text-slate-500">Connection</span>
          <span className="text-[14px] font-semibold text-slate-900 flex items-center gap-1.5">
            {!isOnline ? <><CloudOff size={16} className="text-amber-500" /> Offline</> : <><CheckCircle2 size={16} className="text-emerald-500" /> Online</>}
          </span>
        </div>
        
        <div className="flex justify-between items-baseline border-b border-slate-200 pb-4 mb-4">
          <span className="text-[14px] text-slate-500">Pending actions</span>
          <span className="text-[14px] font-semibold text-slate-900">{pendingCount}</span>
        </div>
        
        <div className="flex justify-between items-baseline pb-4">
          <span className="text-[14px] text-slate-500">Last synced</span>
          <span className="text-[14px] font-semibold text-slate-900">{lastSynced}</span>
        </div>
      </div>

      {!isOnline && (
        <button
          type="button"
          onClick={() => setConnection("online")}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] mb-8"
        >
          SYNC NOW
        </button>
      )}

      <div className="flex-1">
        <h2 className="text-[12px] font-bold text-slate-400 uppercase tracking-wider mb-4">Sync history</h2>
        
        {syncRecords.length === 0 ? (
          <p className="text-[14px] text-slate-500">No recent sync activity.</p>
        ) : (
          <div className="space-y-4">
            {syncRecords.map((record) => (
              <div key={record.id} className="flex justify-between items-start">
                <div>
                  <p className="text-[14px] font-semibold text-slate-900">
                    {record.state === 'synced' ? 'Uploaded' : record.state === 'failed' ? 'Failed to sync' : 'Pending'} {record.type}
                  </p>
                  <p className="text-[13px] text-slate-500">{record.outletId}</p>
                </div>
                <span className="text-[13px] text-slate-500">{record.createdAt}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
