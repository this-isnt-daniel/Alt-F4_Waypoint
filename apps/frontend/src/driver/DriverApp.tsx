import { useState, type ComponentType } from "react";
import { NavigatorProvider, useNavigator, type ScreenId } from "@/router/navigator";
import { DriverStateProvider } from "@/driver/state/DriverStateProvider";
import { PreTripBar, ActiveTripBar } from "@/driver/components/TopBar";
import { useDemoMode } from "@/driver/state/useDemoMode";
import { ScenarioPanel } from "@/driver/components/ScenarioPanel";
import { ListChecks } from "lucide-react";

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
  "stop-detail": StopDetailScreen,
  "mark-arrived": MarkArrivedScreen,
  checklist: ChecklistScreen,
  "not-handed-over": NotHandedOverReasonScreen,
  "pod-photo": PodPhotoScreen,
  "pod-pin": PodPinScreen,
  "delivery-complete": DeliveryCompleteScreen,
  "partial-summary": PartialSummaryScreen,
  "failed-reason": FailedReasonScreen,
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

const PRE_TRIP_SCREENS: ScreenId[] = [
  "signin",
  "start-day",
  "today-trips",
  "trip-briefing",
  "load-confirm",
  "trip-complete",
  "day-summary",
  "no-trips",
];

function DriverContent() {
  const { route } = useNavigator();
  const demo = useDemoMode();
  const [scenOpen, setScenOpen] = useState(false);

  const Screen = SCREEN_MAP[route.id] ?? SignInScreen;
  const isPreTrip = PRE_TRIP_SCREENS.includes(route.id);

  return (
    <div className="min-h-screen bg-canvas text-ink selection:bg-green-fill selection:text-green-ink">
      <a
        href="#driver-main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-3 focus:bg-surface focus:text-green"
      >
        Skip to main content
      </a>

      {/* Container wrapper */}
      <div className="max-w-[430px] mx-auto min-h-screen bg-canvas flex flex-col shadow-2 relative">
        {/* Demo mode quick button if ?demo=1 */}
        {demo && (
          <div className="bg-slate-900 text-white px-4 py-1.5 flex items-center justify-between text-xs">
            <span className="font-semibold text-emerald-400">Judge / Demo Mode</span>
            <button
              type="button"
              onClick={() => setScenOpen(true)}
              className="flex items-center gap-1 bg-white/20 hover:bg-white/30 px-2 py-0.5 rounded text-white font-medium"
            >
              <ListChecks size={13} />
              <span>Scenarios</span>
            </button>
          </div>
        )}

        {isPreTrip ? (
          <PreTripBar />
        ) : (
          <ActiveTripBar tripLabel="Trip 1 · Fresh" stopLabel="Stop 2 of 8" />
        )}

        <main id="driver-main" className="flex-1">
          <Screen />
        </main>

        {demo && (
          <ScenarioPanel open={scenOpen} onClose={() => setScenOpen(false)} />
        )}
      </div>
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
