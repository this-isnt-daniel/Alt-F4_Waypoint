import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";

export function TripCompleteScreen() {
  const { push } = useNavigator();
  const { completeTrip1, completeTrip2, completedStopIds, flaggedStopIds, failedStopIds, activeTripId, currentTripSequence } = useDriverState();

  const handleContinue = () => {
    if (activeTripId === 1) {
      completeTrip1();
      push("today-trips");
    } else {
      completeTrip2();
      push("day-summary");
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      <div className="flex-1 flex flex-col justify-center max-w-sm mx-auto w-full">
        <h1 className="text-[28px] font-bold text-slate-900 mb-1">
          TRIP COMPLETE
        </h1>
        <p className="text-[16px] text-slate-500 mb-8">
          Trip {activeTripId} · {activeTripId === 1 ? "Fresh" : "Style"}
        </p>
        
        <p className="text-[18px] font-bold text-slate-900 mb-6">
          {currentTripSequence.length} of {currentTripSequence.length} stops completed
        </p>

        <div className="space-y-4 mb-8">
          <div className="flex justify-between items-baseline border-b border-slate-100 pb-3">
            <span className="text-[15px] font-medium text-slate-600">Delivered</span>
            <span className="text-[18px] font-bold text-slate-900">{completedStopIds.length}</span>
          </div>
          
          <div className="flex justify-between items-baseline border-b border-slate-100 pb-3">
            <span className="text-[15px] font-medium text-slate-600">Partial</span>
            <span className="text-[18px] font-bold text-slate-900">{flaggedStopIds.length}</span>
          </div>
          
          <div className="flex justify-between items-baseline border-b border-slate-100 pb-3">
            <span className="text-[15px] font-medium text-slate-600">Not completed</span>
            <span className="text-[18px] font-bold text-slate-900">{failedStopIds.length}</span>
          </div>
        </div>
      </div>

      <div className="mt-auto pb-safe">
        <button
          type="button"
          onClick={handleContinue}
          className="w-full bg-[#059669] text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
        >
          CONTINUE
        </button>
      </div>
    </div>
  );
}
