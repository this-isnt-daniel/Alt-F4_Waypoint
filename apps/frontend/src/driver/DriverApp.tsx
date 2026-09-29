import { type ComponentType } from "react";
import { NavigatorProvider, useNavigator, type ScreenId } from "@/router/navigator";
import { DriverStateProvider } from "@/driver/state/DriverStateProvider";
import { useDriverState } from "@/driver/state/useDriverState";
import { PreTripBar, ActiveTripBar } from "@/driver/components/TopBar";

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
  const { currentStopSeq, trip2Unlocked, connection, syncRecords } = useDriverState();
  const Screen = SCREEN_MAP[route.id] ?? SignInScreen;
  const isPreTrip = PRE_TRIP_SCREENS.includes(route.id);

  const dynamicTripLabel = trip2Unlocked ? "Trip 2 · Style" : "Trip 1 · Fresh";
  const dynamicStopLabel = `Stop ${currentStopSeq || 2} of 8`;
  const dynamicSyncTone = connection === "offline" ? "pending" : (syncRecords.some(r => r.state === "pending") ? "pending" : "success");

  return (
    <div className="min-h-screen bg-slate-950/20 sm:py-6 flex justify-center items-center text-ink selection:bg-green-fill selection:text-green-ink font-sans">
      <a
        href="#driver-main"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-3 focus:bg-surface focus:text-green"
      >
        Skip to main content
      </a>

      {/* Realistic Mobile Viewport Device Frame */}
      <div className="w-full max-w-[430px] min-h-screen sm:min-h-[880px] sm:max-h-[92vh] bg-canvas flex flex-col shadow-2xl sm:rounded-[36px] sm:border-[8px] sm:border-slate-800 overflow-hidden relative">
        {isPreTrip ? (
          <PreTripBar />
        ) : (
          <ActiveTripBar tripLabel={dynamicTripLabel} stopLabel={dynamicStopLabel} syncTone={dynamicSyncTone} />
        )}

        <main id="driver-main" className="flex-1 overflow-y-auto">
          <Screen />
        </main>
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
