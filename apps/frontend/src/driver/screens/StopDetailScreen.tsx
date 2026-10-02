import React, { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { DriverMap } from "@/driver/components/DriverMap";
import { useDriverState } from "@/driver/state/useDriverState";
import { TRIP_1_STOPS, type DriverStop } from "@/driver/data/driverContent";
import { Lock, AlertCircle, CheckCircle, Phone, MessageSquare, ChevronLeft, Check, Minus, Plus, X } from "lucide-react";
import { ChoiceList } from "@/driver/components/ChoiceList";

const ISSUE_REASONS = [
  "Customer rejected",
  "Nobody to receive",
  "No payment ready"
];

export function StopDetailScreen() {
  const { push, route, back } = useNavigator();
  const {
    currentStopIndex,
    currentTripStops,
    currentTripSequence,
    completedStopIds,
    flaggedStopIds,
    failedStopIds,
    completeStop,
  } = useDriverState();

  const seq = Number(route.params.seq) || currentStopIndex + 1;
  const fallbackStop: DriverStop = TRIP_1_STOPS[0]!;
  const stop: DriverStop =
    currentTripStops.find((s) => s.seq === seq) ??
    currentTripStops[currentStopIndex] ??
    fallbackStop;

  const stopIdx = currentTripSequence.indexOf(stop.outletId);
  const isCurrent = stopIdx === currentStopIndex;
  const isPast = stopIdx >= 0 && stopIdx < currentStopIndex;
  const isUpcoming = stopIdx > currentStopIndex;
  const isFailed = failedStopIds.includes(stop.outletId);
  
  const currentOutletId = currentTripSequence[currentStopIndex];

  // Local state for delivery workflow
  const [receivedQty, setReceivedQty] = useState(stop.units);
  const [outcome, setOutcome] = useState<"Complete" | "Partial" | "Unable to complete">("Complete");
  
  const [podPhoto, setPodPhoto] = useState(false);
  const [podSignature, setPodSignature] = useState(false);
  const [podNote, setPodNote] = useState("");

  const handleCompleteDelivery = () => {
    // If partial/unable, we'd normally require reasons. 
    // For now, just mark complete.
    if (outcome === "Unable to complete") {
      completeStop(stop.outletId, "failed");
    } else {
      completeStop(stop.outletId, "delivered");
    }
    push("active-trip");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-white">
      <div className="overflow-y-auto px-5 pb-8 pt-5 flex-1 flex flex-col">
        {/* Header area */}
        <div className="flex items-center justify-end mb-5 shrink-0">
          <button
            type="button"
            onClick={() => back()}
            className="flex items-center justify-center w-9 h-9 rounded-full bg-slate-50 text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X size={20} strokeWidth={2.5} />
          </button>
        </div>

        <div className="mb-8 shrink-0">
          <h1 className="text-[24px] font-bold text-slate-900 leading-tight mb-1">{stop.outletId}</h1>
          <p className="text-[15px] font-medium text-slate-700">{stop.name}</p>
          <p className="text-[13px] text-slate-500 mt-1">{stop.address}</p>
        </div>

        {/* ── INFO SECTION ── */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div>
            <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">Delivery Window</span>
            <span className="text-[14px] font-semibold text-slate-900">{stop.window}</span>
          </div>
          <div>
            <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">Expected</span>
            <span className="text-[14px] font-semibold text-slate-900">{stop.units} units</span>
          </div>
          <div>
            <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1">Service</span>
            <span className="text-[14px] font-semibold text-slate-900">{stop.serviceMin} min</span>
          </div>
        </div>

        <hr className="border-slate-100 mb-6" />

        {/* ── REQUIREMENTS ── */}
        <div className="mb-8">
          <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">Requirements</span>
          <div className="flex flex-wrap gap-2">
            {stop.temp && <span className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded text-[13px] font-medium text-slate-700">{stop.temp}</span>}
            {stop.dock && <span className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded text-[13px] font-medium text-slate-700">{stop.dock}</span>}
            {stop.parking !== "Normal" && <span className="bg-slate-50 border border-slate-200 px-2.5 py-1 rounded text-[13px] font-medium text-slate-700">{stop.parking}</span>}
          </div>
        </div>

        <hr className="border-slate-100 mb-6" />

        {/* ── DELIVERY QUANTITY ── */}
        <div className="mb-8">
          <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-4">Delivery</span>
          
          <div className="flex justify-between items-center mb-4">
            <span className="text-[14px] font-semibold text-slate-700">Expected</span>
            <span className="text-[15px] font-bold text-slate-900">{stop.units} units</span>
          </div>

          <div className="flex items-center justify-between mb-6">
            <span className="text-[14px] font-semibold text-slate-700">Received</span>
            <div className="flex items-center bg-slate-50 border border-slate-200 rounded-lg p-1">
              <button type="button" onClick={() => setReceivedQty(Math.max(0, receivedQty - 1))} className="w-10 h-10 flex items-center justify-center text-slate-500 bg-white rounded-md shadow-sm border border-slate-200 active:scale-95 transition-all"><Minus size={18} /></button>
              <span className="w-16 text-center text-[18px] font-bold text-slate-900">{receivedQty}</span>
              <button type="button" onClick={() => setReceivedQty(receivedQty + 1)} className="w-10 h-10 flex items-center justify-center text-slate-500 bg-white rounded-md shadow-sm border border-slate-200 active:scale-95 transition-all"><Plus size={18} /></button>
            </div>
          </div>

          <div className="space-y-2">
            {["Complete", "Partial", "Unable to complete"].map(opt => (
              <button
                key={opt}
                onClick={() => setOutcome(opt as any)}
                className={`w-full flex items-center justify-between p-3.5 rounded-lg border transition-colors ${outcome === opt ? 'border-[#059669] bg-[#059669]/5 text-[#059669]' : 'border-slate-200 bg-white text-slate-600'}`}
              >
                <span className="text-[14px] font-bold">{opt}</span>
                {outcome === opt && <Check size={18} />}
              </button>
            ))}
          </div>

          {outcome === "Partial" && (
            <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-[13px] text-amber-800 font-semibold mb-2">Short by {Math.max(0, stop.units - receivedQty)} units. Please add note.</p>
              <input type="text" placeholder="e.g. 5 damaged..." className="w-full px-3 py-2 border border-amber-200 rounded text-[13px] bg-white outline-none" />
            </div>
          )}

          {outcome === "Unable to complete" && (
            <div className="mt-3 p-3 bg-slate-50 border border-slate-200 rounded-lg">
              <ChoiceList
                options={ISSUE_REASONS.map(r => ({ id: r, label: r }))}
                selectedId={null}
                onSelect={() => {}}
                allowOtherNote={false}
              />
            </div>
          )}
        </div>

        <hr className="border-slate-100 mb-6" />

        {/* ── PROOF OF DELIVERY ── */}
        <div className="mb-8">
          <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-4">Proof of Delivery</span>
          <div className="space-y-3">
            <button onClick={() => setPodPhoto(true)} className="w-full flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
              <span className="text-[14px] font-semibold">Photo</span>
              {podPhoto ? <CheckCircle size={18} className="text-[#059669]" /> : <span className="text-[13px] text-slate-400">Capture</span>}
            </button>
            <button onClick={() => setPodSignature(true)} className="w-full flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50">
              <span className="text-[14px] font-semibold">Signature</span>
              {podSignature ? <CheckCircle size={18} className="text-[#059669]" /> : <span className="text-[13px] text-slate-400">Capture</span>}
            </button>
            <input 
              type="text" 
              placeholder="Notes (optional)" 
              value={podNote} 
              onChange={e => setPodNote(e.target.value)}
              className="w-full flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-white text-[14px] text-slate-900 placeholder-slate-400 outline-none focus:border-[#059669]"
            />
          </div>
        </div>

        <hr className="border-slate-100 mb-6" />

        {/* ── ISSUES & CONTACT ── */}
        <div className="mb-8 space-y-4">
          <div>
            <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">Issues</span>
            <button type="button" onClick={() => push("issue-wizard")} className="w-full py-3 border border-slate-200 rounded-lg text-[13px] font-bold text-slate-700 hover:bg-slate-50 flex justify-center items-center gap-2">
              <AlertCircle size={16} className="text-slate-400" />
              Report an issue
            </button>
          </div>
          <div>
            <span className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-3">Contact</span>
            <div className="flex gap-3">
              <button type="button" onClick={() => push("call-overlay", { outletId: stop.outletId })} className="flex-1 py-3 border border-slate-200 rounded-lg text-[13px] font-bold text-slate-700 hover:bg-slate-50 flex justify-center items-center gap-2">
                <Phone size={15} className="text-slate-400" /> Call
              </button>
              <button type="button" onClick={() => push("chat", { outletId: stop.outletId })} className="flex-1 py-3 border border-slate-200 rounded-lg text-[13px] font-bold text-slate-700 hover:bg-slate-50 flex justify-center items-center gap-2">
                <MessageSquare size={15} className="text-slate-400" /> Message
              </button>
              <button type="button" onClick={() => push("contact-dispatch")} className="flex-1 py-3 border border-slate-200 rounded-lg text-[13px] font-bold text-slate-700 hover:bg-slate-50 flex justify-center items-center gap-2">
                Dispatch
              </button>
            </div>
          </div>
        </div>

        {/* ── PRIMARY ACTION ── */}
        <div className="mt-4">
          <button
            type="button"
            onClick={handleCompleteDelivery}
            className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98]"
          >
            COMPLETE DELIVERY
          </button>
        </div>

      </div>
    </div>
  );
}
