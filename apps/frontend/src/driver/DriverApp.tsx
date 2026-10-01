import { useState, type ComponentType } from "react";
import { NavigatorProvider, useNavigator, type ScreenId } from "@/router/navigator";
import { DriverStateProvider } from "@/driver/state/DriverStateProvider";
import { PreTripBar, ActiveTripBar } from "@/driver/components/TopBar";
import { useDemoMode } from "@/driver/state/useDemoMode";
import { ScenarioPanel } from "@/driver/components/ScenarioPanel";
import { useDriverState } from "@/driver/state/useDriverState";
import { ListChecks } from "lucide-react";
import { VehicleSheet } from "@/driver/components/VehicleSheet";
import { AccountSheet } from "@/driver/components/AccountSheet";

// Import all screens
import { SignInScreen } from "./screens/SignInScreen";
import { StartDayScreen } from "./screens/StartDayScreen";
import { TodayTripsScreen } from "./screens/TodayTripsScreen";
import { TripBriefingScreen } from "./screens/TripBriefingScreen";
import { LoadConfirmScreen } from "./screens/LoadConfirmScreen";
import { ActiveTripScreen } from "./screens/ActiveTripScreen";
import { StopDetailScreen } from "./screens/StopDetailScreen";
import { MarkArrivedScreen } from "./screens/MarkArrivedScreen";
import { ChecklistScreen } from "./screens/ChecklistScreen";
import { NotHandedOverReasonScreen } from "./screens/NotHandedOverReasonScreen";
import { PodPhotoScreen } from "./screens/PodPhotoScreen";
import { PodPinScreen } from "./screens/PodPinScreen";
import { DeliveryCompleteScreen } from "./screens/DeliveryCompleteScreen";
import { PartialSummaryScreen } from "./screens/PartialSummaryScreen";
import { FailedReasonScreen } from "./screens/FailedReasonScreen";
import { ReturnDepotScreen } from "./screens/ReturnDepotScreen";
import { DepotReturnScreen } from "./screens/DepotReturnScreen";
import { TripCompleteScreen } from "./screens/TripCompleteScreen";
import { DaySummaryScreen } from "./screens/DaySummaryScreen";
import { OfflineSavedScreen } from "./screens/OfflineSavedScreen";
import { SyncCentreScreen } from "./screens/SyncCentreScreen";
import { RouteChangedScreen } from "./screens/RouteChangedScreen";
import { OutletClosedScreen } from "./screens/OutletClosedScreen";
import { SyncReviewScreen } from "./screens/SyncReviewScreen";
import { RecordSentScreen } from "./screens/RecordSentScreen";
import { NoTripsScreen } from "./screens/NoTripsScreen";
import { CameraDeniedScreen } from "./screens/CameraDeniedScreen";
import { LocationDeniedScreen } from "./screens/LocationDeniedScreen";
import { SyncFailedScreen } from "./screens/SyncFailedScreen";
import { ChatScreen } from "./screens/ChatScreen";
import { CallOverlayScreen } from "./screens/CallOverlayScreen";
import { IssueWizardScreen } from "./screens/IssueWizardScreen";
import { ContactDispatchSheet } from "./screens/ContactDispatchSheet";

const SCREEN_MAP: Record<ScreenId, ComponentType> = {
  signin: SignInScreen,
  "start-day": StartDayScreen,
  "today-trips": TodayTripsScreen,
  "trip-briefing": TripBriefingScreen,
  "load-confirm": LoadConfirmScreen,
  "active-trip": ActiveTripScreen,
  
  // Phase 2 Unified Stop Workspace
  "stop-detail": StopDetailScreen,
  "mark-arrived": StopDetailScreen,
  "checklist": StopDetailScreen,
  "partial-summary": StopDetailScreen,
  "failed-reason": StopDetailScreen,
  "delivery-complete": StopDetailScreen,
  
  "not-handed-over": NotHandedOverReasonScreen,
  "pod-photo": PodPhotoScreen,
  "pod-pin": PodPinScreen,
  "return-depot": ReturnDepotScreen,
  "depot-return": DepotReturnScreen,
  "trip-complete": TripCompleteScreen,
  "day-summary": DaySummaryScreen,
  "offline-saved": OfflineSavedScreen,
  "sync-centre": SyncCentreScreen,
  "route-changed": RouteChangedScreen,
  "outlet-closed": OutletClosedScreen,
  "sync-review": SyncReviewScreen,
  "record-sent": RecordSentScreen,
  "no-trips": NoTripsScreen,
  "camera-denied": CameraDeniedScreen,
  "location-denied": LocationDeniedScreen,
  "sync-failed": SyncFailedScreen,
  chat: ChatScreen,
  "call-overlay": CallOverlayScreen,
  "issue-wizard": IssueWizardScreen,
  "contact-dispatch": ContactDispatchSheet,
};

/** Screens where the header is hidden entirely */
const HIDDEN_HEADER_SCREENS: ScreenId[] = [
  "chat", 
  "call-overlay",
  "stop-detail",
  "mark-arrived",
  "checklist",
  "partial-summary",
  "failed-reason",
  "delivery-complete",
  "not-handed-over",
  "pod-photo",
  "pod-pin"
];

/** Screens that use the pre-trip bar variant */
const PRE_TRIP_SCREENS: ScreenId[] = [
  "signin",
  "start-day",
  "today-trips",
  "trip-briefing",
  "load-confirm",
  "trip-complete",
  "day-summary",
  "no-trips",
  "contact-dispatch",
  "issue-wizard",
];

function DriverContent() {
  const { route } = useNavigator();
  const demo = useDemoMode();
  const {
    activeTripId,
    trip1Started,
    trip2Started,
    currentStopIndex,
    currentTripSequence,
    vehicleBreakdown,
  } = useDriverState();
  const [scenOpen, setScenOpen] = useState(false);
  const [vehicleSheetOpen, setVehicleSheetOpen] = useState(false);
  const [accountSheetOpen, setAccountSheetOpen] = useState(false);

  const Screen = SCREEN_MAP[route.id] ?? SignInScreen;
  const hideTopBar = HIDDEN_HEADER_SCREENS.includes(route.id);
  const isTripActive = trip1Started || trip2Started;
  const isPreTrip = !isTripActive || PRE_TRIP_SCREENS.includes(route.id);
  const currentStopNum = currentStopIndex + 1;
  const totalStops = currentTripSequence.length || 8;
  const tripLabel = activeTripId === 2 ? "Trip 2 · Style" : "Trip 1 · Fresh";

  return (
    <div className="w-full h-dvh bg-white text-slate-900 overflow-hidden flex flex-col relative">
      {/* Skip link for accessibility */}
      <a
        href="#driver-main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-3 focus:bg-white focus:text-green"
      >
        Skip to main content
      </a>

      {/* ── DEMO MODE BAR ──────────────────────────────────────────
          Only rendered when ?demo=1 is in the URL.
          A real driver session never sees this.
      ───────────────────────────────────────────────────────────── */}
      {demo && (
        <div className="bg-slate-900 text-white px-4 py-1.5 flex items-center justify-between text-xs z-50 shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-emerald-400">Judge / Demo Mode</span>
            {vehicleBreakdown && (
              <span className="bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-bold px-1.5 py-0.5 rounded">
                Breakdown Active
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={() => setScenOpen(true)}
            className="flex items-center gap-1 bg-white/15 hover:bg-white/25 px-2 py-0.5 rounded text-white font-medium transition-colors cursor-pointer"
            aria-label="Open Scenario Panel"
          >
            <ListChecks size={13} />
            <span>Scenarios</span>
          </button>
        </div>
      )}

      {/* ── COMPACT MOBILE HEADER ───────────────────────────────── */}
      {!hideTopBar && (
        isPreTrip ? <PreTripBar /> : (
          <ActiveTripBar
            tripLabel={tripLabel}
            stopLabel={`Stop ${currentStopNum} of ${totalStops}`}
            onOpenVehicle={() => setVehicleSheetOpen(true)}
            onOpenAccount={() => setAccountSheetOpen(true)}
          />
        )
      )}

      {/* ── SCREEN CONTENT ─────────────────────────────────────── */}
      <main id="driver-main" className="flex-1 flex flex-col min-h-0 overflow-hidden relative z-0">
        <Screen />
      </main>

      {/* Overlays */}
      <VehicleSheet open={vehicleSheetOpen} onClose={() => setVehicleSheetOpen(false)} />
      <AccountSheet open={accountSheetOpen} onClose={() => setAccountSheetOpen(false)} />

      {/* Scenario Panel – demo only */}
      {demo && (
        <ScenarioPanel open={scenOpen} onClose={() => setScenOpen(false)} />
      )}
    </div>
  );
}

export function DriverApp() {
  return (
    <NavigatorProvider>
      <DriverStateProvider>
        <DriverContent />
      </DriverStateProvider>
    </NavigatorProvider>
  );
}
