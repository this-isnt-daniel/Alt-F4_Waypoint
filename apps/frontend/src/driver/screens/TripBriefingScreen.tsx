import { useNavigator } from "@/router/navigator";
import { useDriverState } from "@/driver/state/useDriverState";
import { TRIP_1, TRIP_2 } from "@/driver/data/driverContent";
import { Check, AlertTriangle, ChevronRight } from "lucide-react";

export function TripBriefingScreen() {
  const { route, push } = useNavigator();
  const { startTrip1, startTrip2 } = useDriverState();
  const isTrip2 = route.params.trip === "2";
  const trip = isTrip2 ? TRIP_2 : TRIP_1;
  const firstStop = trip.stops[0];

  const handleStart = () => {
    if (isTrip2) {
      startTrip2();
    } else {
      startTrip1();
    }
    push("active-trip");
  };

  return (
    <div className="flex flex-col flex-1 min-h-0 overflow-y-auto bg-white px-5 py-6">
      <h1 className="text-[24px] font-bold text-slate-900 mb-1 tracking-tight">
        Trip {trip.id} · {trip.brand}
      </h1>
      <p className="text-[16px] text-slate-500 mb-6">
        {trip.stopCount} stops · {trip.district} · Depart {trip.depart}
      </p>

      {/* Load verification status */}
      <section className="mb-6">
        <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-100 p-4 rounded-xl">
          <div className="bg-emerald-500 text-white rounded-full p-1.5 shrink-0">
            <Check size={16} strokeWidth={3} />
          </div>
          <div className="flex-1">
            <p className="text-[14px] font-bold text-emerald-800">Load verified</p>
            <p className="text-[13px] text-emerald-600/80">Loader Kasun Kalhara confirmed manifest matches van.</p>
          </div>
          {/* Allow inspecting load issues if needed */}
          <button 
            type="button" 
            className="text-emerald-700 p-1"
            onClick={() => push("load-confirm", { trip: isTrip2 ? "2" : "1" })}
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </section>

      {/* Key information */}
      <section className="mb-8">
        <h2 className="text-[12px] font-bold text-slate-400 uppercase tracking-wider mb-3">Key information</h2>
        
        <div className="space-y-4">
          <div>
            <p className="text-[13px] text-slate-500 mb-0.5">First stop</p>
            <p className="text-[15px] font-semibold text-slate-900">{firstStop?.name}</p>
          </div>
          
          <div>
            <p className="text-[13px] text-slate-500 mb-0.5">Delivery window</p>
            <p className="text-[15px] font-semibold text-slate-900">{firstStop?.window}</p>
          </div>
          
          <div>
            <p className="text-[13px] text-slate-500 mb-0.5">Vehicle requirements</p>
            <p className="text-[15px] font-semibold text-slate-900">{trip.capability}</p>
          </div>
        </div>
      </section>

      <div className="mt-auto">
        <button
          type="button"
          onClick={handleStart}
          className="w-full bg-green text-white font-bold text-[16px] py-4 rounded-lg transition-colors active:scale-[0.98] cursor-pointer"
          style={{ backgroundColor: "var(--c-green)" }}
        >
          Start Trip {trip.id}
        </button>
      </div>
    </div>
  );
}
