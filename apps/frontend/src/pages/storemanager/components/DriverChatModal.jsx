import React, { useState, useEffect } from 'react';
import { X, Send, Phone, Truck, CheckCircle2 } from 'lucide-react';
import { apiFetch } from '../../../lib/api';

const STORE_QUICK_REPLIES = [
  "Use Loading Bay B",
  "Main gate is open",
  "Dock staff is ready for unloading",
  "Please wait 5 mins at gate",
  "Check cold storage temperature on receipt"
];

export default function DriverChatModal({ isOpen, onClose, outlet }) {
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isCalling, setIsCalling] = useState(false);
  const [callStatus, setCallStatus] = useState(null);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;

    async function loadChatData() {
      try {
        const outletId = outlet?.id || 'OUT001';
        const [driversData, messagesData] = await Promise.all([
          apiFetch(`/chat/drivers?outlet_id=${outletId}`).catch(() => []),
          apiFetch(`/chat/messages?outlet_id=${outletId}`).catch(() => [])
        ]);

        if (!isMounted) return;

        if (Array.isArray(driversData) && driversData.length > 0) {
          setDrivers(driversData);
          if (!selectedDriver) setSelectedDriver(driversData[0]);
        }
        if (Array.isArray(messagesData)) {
          setMessages(messagesData);
        }
      } catch (err) {
        console.error("Error loading chat data:", err);
      }
    }

    loadChatData();
    const interval = setInterval(loadChatData, 5000); // Polling for new messages

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [isOpen, outlet]);

  const handleSend = async (text) => {
    const messageText = text || input;
    if (!messageText.trim()) return;

    const outletId = outlet?.id || 'OUT001';

    // Optimistic UI update
    const tempMsg = {
      id: `temp-${Date.now()}`,
      sender_role: 'store',
      sender_name: 'Store Manager',
      body: messageText,
      created_at: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages((prev) => [...prev, tempMsg]);
    setInput('');

    try {
      await apiFetch('/chat/messages', {
        method: 'POST',
        body: JSON.stringify({
          outlet_id: outletId,
          sender_role: 'store',
          sender_name: 'Store Manager',
          recipient_role: 'driver',
          body: messageText
        })
      });
    } catch (err) {
      console.error("Failed to send chat message:", err);
    }
  };

  const handleInitiateCall = async () => {
    setIsCalling(true);
    setCallStatus('Connecting audio call...');
    try {
      await apiFetch('/chat/call-intent', {
        method: 'POST',
        body: JSON.stringify({
          outlet_id: outlet?.id || 'OUT001',
          requested_by: 'store_manager'
        })
      });
      setCallStatus(`Connected to ${selectedDriver?.name || 'Driver'} (${selectedDriver?.phone || '+94770000004'})`);
      setTimeout(() => {
        setIsCalling(false);
        setCallStatus(null);
      }, 4000);
    } catch (err) {
      setCallStatus('Call failed');
      setTimeout(() => setIsCalling(false), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-[2px] flex items-center justify-center p-3 sm:p-5 animate-in fade-in duration-150">
      <div 
        className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-4xl h-[620px] max-h-[92vh] overflow-hidden flex flex-col md:flex-row animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Left Sidebar: Assigned Drivers */}
        <div className="w-full md:w-72 bg-slate-50 border-r border-slate-200 flex flex-col shrink-0 h-44 md:h-full">
          <div className="p-4 border-b border-slate-200 bg-white shrink-0">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Truck size={16} className="text-[#059669]" />
              Assigned Drivers
            </h2>
            <p className="text-[11px] text-slate-500 mt-0.5 truncate">
              Drivers delivering to {outlet?.name || 'Store'}
            </p>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {drivers.length === 0 ? (
              <div className="p-4 text-xs text-slate-400 text-center italic">
                No active delivery drivers assigned
              </div>
            ) : (
              drivers.map((drv) => {
                const isSelected = selectedDriver?.driver_id === drv.driver_id;
                return (
                  <button
                    key={drv.driver_id}
                    type="button"
                    onClick={() => setSelectedDriver(drv)}
                    className={`w-full text-left p-3.5 transition-colors cursor-pointer flex flex-col gap-1 ${
                      isSelected ? 'bg-[#EBF6F0] border-l-4 border-[#059669]' : 'hover:bg-slate-100'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-slate-900 truncate">{drv.name}</span>
                      <span className="text-[10px] font-semibold text-[#059669] bg-[#DCF0E5] px-2 py-0.5 rounded-full shrink-0">
                        {drv.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600 font-mono font-medium truncate">
                      {drv.vehicle_id} · {drv.vehicle_type}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1">
                      <span>ETA: {drv.eta}</span>
                      <span className="truncate max-w-[120px]">{drv.current_stop}</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Chat Area */}
        <div className="flex-1 min-w-0 flex flex-col bg-white overflow-hidden h-full">
          {/* Header */}
          <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-white shrink-0 gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 truncate">
                <span className="truncate">{selectedDriver?.name || 'Driver Chat'}</span>
                <span className="text-xs font-mono font-normal text-slate-500 shrink-0">
                  ({selectedDriver?.vehicle_id || 'VEH014'})
                </span>
              </h3>
              <p className="text-[11px] text-slate-500 truncate mt-0.5">
                Phone: {selectedDriver?.phone || '+94770000004'} · Direct Outlet Channel
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleInitiateCall}
                disabled={isCalling}
                className="px-3.5 py-1.5 rounded-xl bg-[#EBF6F0] border border-[#DCF0E5] text-[#059669] hover:bg-[#059669] hover:text-white text-xs font-bold transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50 shrink-0"
              >
                <Phone size={14} />
                <span className="hidden sm:inline">Call Driver</span>
                <span className="sm:hidden">Call</span>
              </button>

              <button
                type="button"
                onClick={onClose}
                className="text-slate-400 hover:text-slate-600 rounded-full p-1.5 hover:bg-slate-100 transition cursor-pointer shrink-0"
                title="Close chat"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* Call Status Toast Banner */}
          {callStatus && (
            <div className="px-4 py-2 bg-[#EBF6F0] border-b border-[#DCF0E5] text-[#059669] text-xs font-semibold flex items-center justify-between animate-in fade-in shrink-0">
              <span className="flex items-center gap-1.5 truncate">
                <CheckCircle2 size={14} className="shrink-0" /> {callStatus}
              </span>
            </div>
          )}

          {/* Messages Body */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-[#FAFBFA] min-h-0">
            {messages.map((m, idx) => {
              const isStore = m.sender_role === 'store';
              return (
                <div key={m.id || idx} className={`flex ${isStore ? 'justify-end' : 'justify-start'}`}>
                  <div 
                    className={`max-w-[85%] sm:max-w-[75%] p-3 rounded-2xl text-xs leading-relaxed shadow-2xs break-words ${
                      isStore
                        ? 'bg-[#059669] text-white rounded-tr-xs'
                        : 'bg-white border border-slate-200 text-slate-900 rounded-tl-xs'
                    }`}
                  >
                    <p className="font-semibold text-[11px] mb-0.5 opacity-90">
                      {m.sender_name || (isStore ? 'Store Manager' : 'Driver')}
                    </p>
                    <p className="whitespace-pre-wrap">{m.body}</p>
                    <span className={`block text-[9px] mt-1 text-right font-medium ${isStore ? 'text-emerald-100' : 'text-slate-400'}`}>
                      {m.created_at || 'Just now'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Replies & Input */}
          <div className="p-3 border-t border-slate-200 bg-white space-y-2 shrink-0">
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar w-full">
              {STORE_QUICK_REPLIES.map((reply, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => handleSend(reply)}
                  className="whitespace-nowrap px-3 py-1 rounded-full bg-slate-100 hover:bg-[#EBF6F0] hover:text-[#059669] text-[11px] text-slate-700 font-medium transition cursor-pointer border border-slate-200 shrink-0"
                >
                  {reply}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 w-full">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
                placeholder="Message assigned driver..."
                className="flex-1 min-w-0 px-3.5 py-2.5 bg-slate-100 border-none rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-[#059669]/50 outline-none"
              />
              <button
                type="button"
                onClick={() => handleSend(input)}
                disabled={!input.trim()}
                className="p-2.5 bg-[#059669] hover:bg-[#047857] text-white rounded-xl disabled:opacity-50 transition cursor-pointer flex items-center justify-center shrink-0"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
