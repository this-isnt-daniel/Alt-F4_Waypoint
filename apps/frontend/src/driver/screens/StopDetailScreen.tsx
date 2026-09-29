import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { AppIcon, type AppIconName } from "@/driver/components/AppIcon";
import { useDriverState } from "@/driver/state/useDriverState";
import { TRIP_1_STOPS, type DriverStop } from "@/driver/data/driverContent";
import { Lock, AlertCircle, CheckCircle } from "lucide-react";

export function StopDetailScreen() {
  const { push, route } = useNavigator();
  const {
    currentStopIndex,
    currentTripStops,
    currentTripSequence,
    completedStopIds,
    failedStopIds,
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

  const isDelivered = completedStopIds.includes(stop.outletId);
  const isFailed = failedStopIds.includes(stop.outletId);

  const tempIcon: AppIconName = stop.temp.includes("Chilled") ? "snowflake" : "package";
  const dockIcon: AppIconName = stop.dock === "Mall bay" ? "building" : "package";

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      {/* Sequential status notice banner */}
      {isUpcoming && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 flex items-start gap-2.5 text-xs text-amber-900">
          <Lock size={16} className="text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block">Upcoming Stop (Locked)</span>
            <span>
              Route stops must be completed sequentially. Complete Stop {currentStopIndex + 1} before arriving at {stop.outletId}.
            </span>
          </div>
        </div>
      )}

      {isPast && (
        <div className="rounded-xl border border-slate-200 bg-slate-100 p-3 flex items-start gap-2.5 text-xs text-slate-700">
          {isFailed ? (
            <AlertCircle size={16} className="text-rose-600 shrink-0 mt-0.5" />
          ) : (
            <CheckCircle size={16} className="text-emerald-600 shrink-0 mt-0.5" />
          )}
          <div>
            <span className="font-bold block">
              {isFailed ? "Stop Marked as Failed / Returned" : "Stop Already Delivered"}
            </span>
            <span>This stop has already been processed for this trip.</span>
          </div>
        </div>
      )}

      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-bold text-slate-900">{stop.outletId}</h1>
          {isCurrent && (
            <span className="text-[11px] font-bold text-green bg-green-fill px-2 py-0.5 rounded-full border border-green/20">
              Current Stop
            </span>
          )}
        </div>
        <p className="text-[14px] font-medium text-slate-700">{stop.name}</p>
        <p className="text-[13px] text-slate-500 mt-0.5">{stop.address}</p>
      </div>

      <Card variant="surface" className="space-y-3">
        <div className="flex items-center justify-between text-[13px]">
          <span className="text-slate-500">Window</span>
          <span className="font-semibold text-slate-900">{stop.window}</span>
        </div>
        {stop.dockDetail && (
          <div className="flex items-center justify-between text-[13px]">
            <span className="text-slate-500">Dock</span>
            <span className="font-medium text-slate-900">{stop.dock} · {stop.dockDetail}</span>
          </div>
        )}
        <div className="flex items-center justify-between text-[13px]">
          <span className="text-slate-500">Units</span>
          <span className="font-medium text-slate-900">{stop.units}</span>
        </div>
        <div className="flex items-center justify-between text-[13px]">
          <span className="text-slate-500">Service time</span>
          <span className="font-medium text-slate-900">{stop.serviceMin} min</span>
        </div>
      </Card>

      {/* Chips */}
      <div className="flex flex-wrap gap-1.5">
        <Chip kind="restriction" category="temperature" label={stop.temp} icon={tempIcon} />
        <Chip kind="restriction" category="dock" label={stop.dock} icon={dockIcon} />
        {stop.parking !== "Normal" && (
          <Chip kind="restriction" category="access" label={stop.parking} icon="truck" />
        )}
      </div>

      {stop.instructions && (
        <Card variant="raised">
          <p className="text-[13px] text-slate-600">{stop.instructions}</p>
        </Card>
      )}

      <div className="space-y-2 pt-2">
        {isCurrent ? (
          <Button
            variant="primary"
            size="lg"
            onClick={() => push("mark-arrived", { seq: String(seq) })}
          >
            Mark arrived
          </Button>
        ) : isUpcoming ? (
          <Button variant="secondary" size="lg" disabled className="opacity-60 cursor-not-allowed">
            <Lock size={15} className="mr-1.5" /> Locked · Complete Stop {currentStopIndex + 1} first
          </Button>
        ) : (
          <Button variant="secondary" size="lg" disabled className="opacity-60">
            {isFailed ? "Delivery Failed / In Return Crate" : "Delivered"}
          </Button>
        )}

        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="md"
            fullWidth={false}
            className="flex-1"
            onClick={() => push("chat", { outletId: stop.outletId })}
          >
            <AppIcon name="message" size={16} className="mr-1" /> Store Chat
          </Button>
          <Button
            variant="secondary"
            size="md"
            fullWidth={false}
            className="flex-1"
            onClick={() => push("call-overlay", { outletId: stop.outletId })}
          >
            <AppIcon name="phone" size={16} className="mr-1" /> Store Call
          </Button>
          <Button
            variant="secondary"
            size="md"
            fullWidth={false}
            className="flex-1 text-green border-green/30"
            onClick={() => push("contact-dispatch")}
          >
            <AppIcon name="phone" size={16} className="mr-1 text-green" /> Dispatch
          </Button>
        </div>

        <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={() => push("active-trip")}>
            <AppIcon name="arrow-left" size={16} className="mr-2" /> Back to route
          </Button>

          {isCurrent && (
            <button
              type="button"
              onClick={() =>
                push("failed-reason", { outletId: stop.outletId, seq: String(stop.seq) })
              }
              className="text-xs font-semibold text-rose-600 hover:text-rose-700 hover:underline py-1.5 px-2 cursor-pointer"
            >
              Report stop failure
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
