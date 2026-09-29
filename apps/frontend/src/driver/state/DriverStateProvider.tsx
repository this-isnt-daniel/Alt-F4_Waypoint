import {
  createContext,
  useCallback,
  useMemo,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { type ConnectionState } from "./connection";
import { type SyncRecord } from "./syncQueue";
import {
  SCENARIO_INITIAL,
  type ScenarioId,
  type ScenarioState,
} from "./scenarios";
import {
  ROUTE_UPDATED_SEQUENCE,
  TRIP_1_STOPS,
} from "@/driver/data/driverContent";

export interface DriverStateContextValue {
  connection: ConnectionState;
  setConnection: (next: ConnectionState) => void;
  syncRecords: SyncRecord[];
  addSyncRecord: (record: Omit<SyncRecord, "id" | "createdAt">) => void;
  updateSyncRecord: (id: string, patch: Partial<SyncRecord>) => void;
  trip1Started: boolean;
  trip2Unlocked: boolean;
  startTrip1: () => void;
  completeTrip1: () => void;
  currentStopSeq: number;
  setCurrentStopSeq: (seq: number) => void;
  currentStopIndex: number;
  trip1Sequence: string[];
  completedStopIds: string[];
  flaggedStopIds: string[];
  failedStopIds: string[];
  completeStop: (outletId: string, outcome: "delivered" | "partial" | "failed") => void;
  routeUpdateAccepted: boolean;
  acceptRouteUpdate: () => void;
  syncReviewForwarded: boolean;
  forwardSyncReview: () => void;
  applyScenario: (scenarioId: ScenarioId, params?: Record<string, string>) => void;
}

export const DriverStateContext = createContext<DriverStateContextValue | null>(
  null,
);

const DEFAULT_STOPS = TRIP_1_STOPS.map((s) => s.outletId);

function parseHashScenario(): {
  scenarioId?: ScenarioId;
  params: Record<string, string>;
} {
  try {
    const raw = window.location.hash.replace(/^#\/?/, "");
    const [, queryString] = raw.split("?");
    const params: Record<string, string> = {};
    if (queryString) {
      for (const [key, value] of new URLSearchParams(queryString)) {
        params[key] = value;
      }
    }
    const scenarioId = params.scenario as ScenarioId | undefined;
    return { scenarioId, params };
  } catch {
    return { params: {} };
  }
}

export function DriverStateProvider({ children }: { children: ReactNode }) {
  const initial = useMemo(() => {
    const { scenarioId, params } = parseHashScenario();
    const base =
      scenarioId && SCENARIO_INITIAL[scenarioId]
        ? SCENARIO_INITIAL[scenarioId]
        : SCENARIO_INITIAL.happy;

    if (params.outletId) {
      const idx = base.routeSequence.indexOf(params.outletId);
      return {
        ...base,
        currentStopId: params.outletId,
        currentStopIndex: idx >= 0 ? idx : base.currentStopIndex,
      };
    }
    return base;
  }, []);

  const [connection, setConnectionState] = useState<ConnectionState>(
    initial.connection,
  );
  const [syncRecords, setSyncRecords] = useState<SyncRecord[]>([]);
  const [trip1Started, setTrip1Started] = useState<boolean>(initial.tripStarted);
  const [trip2Unlocked, setTrip2Unlocked] = useState<boolean>(
    initial.trip2Unlocked ?? false,
  );
  const [trip1Sequence, setTrip1Sequence] = useState<string[]>(
    initial.routeSequence,
  );
  const [currentStopIndex, setCurrentStopIndex] = useState<number>(
    initial.currentStopIndex,
  );
  const [completedStopIds, setCompletedStopIds] = useState<string[]>(
    initial.completedStopIds,
  );
  const [flaggedStopIds, setFlaggedStopIds] = useState<string[]>(
    initial.flaggedStopIds,
  );
  const [failedStopIds, setFailedStopIds] = useState<string[]>(
    initial.failedStopIds,
  );
  const [routeUpdateAccepted, setRouteUpdateAccepted] = useState<boolean>(
    initial.routeUpdateAccepted,
  );
  const [syncReviewForwarded, setSyncReviewForwarded] = useState<boolean>(
    initial.syncReviewForwarded,
  );

  const applyScenario = useCallback(
    (scenarioId: ScenarioId, params: Record<string, string> = {}) => {
      const state: ScenarioState =
        SCENARIO_INITIAL[scenarioId] ?? SCENARIO_INITIAL.happy;

      setConnectionState(state.connection);
      setTrip1Started(state.tripStarted);
      setTrip2Unlocked(state.trip2Unlocked ?? false);
      setTrip1Sequence([...state.routeSequence]);
      setCompletedStopIds([...state.completedStopIds]);
      setFlaggedStopIds([...state.flaggedStopIds]);
      setFailedStopIds([...state.failedStopIds]);
      setRouteUpdateAccepted(state.routeUpdateAccepted);
      setSyncReviewForwarded(state.syncReviewForwarded);

      let targetIdx = state.currentStopIndex;
      if (params.outletId) {
        const found = state.routeSequence.indexOf(params.outletId);
        if (found >= 0) targetIdx = found;
      }
      setCurrentStopIndex(targetIdx);
    },
    [],
  );

  // Sync with hash changes
  useEffect(() => {
    function handleHashChange() {
      const { scenarioId, params } = parseHashScenario();
      if (scenarioId && SCENARIO_INITIAL[scenarioId]) {
        applyScenario(scenarioId, params);
      }
    }
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, [applyScenario]);

  const setConnection = useCallback((next: ConnectionState) => {
    setConnectionState(next);
  }, []);

  const addSyncRecord = useCallback(
    (record: Omit<SyncRecord, "id" | "createdAt">) => {
      const newRecord: SyncRecord = {
        ...record,
        id: `rec-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        createdAt: new Date().toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        }),
      };
      setSyncRecords((prev) => [newRecord, ...prev]);
    },
    [],
  );

  const updateSyncRecord = useCallback(
    (id: string, patch: Partial<SyncRecord>) => {
      setSyncRecords((prev) =>
        prev.map((item) => (item.id === id ? { ...item, ...patch } : item)),
      );
    },
    [],
  );

  const startTrip1 = useCallback(() => {
    setTrip1Started(true);
  }, []);

  const completeTrip1 = useCallback(() => {
    setTrip2Unlocked(true);
  }, []);

  const acceptRouteUpdate = useCallback(() => {
    setRouteUpdateAccepted(true);
    setTrip1Sequence([...ROUTE_UPDATED_SEQUENCE]);
  }, []);

  const forwardSyncReview = useCallback(() => {
    setSyncReviewForwarded(true);
  }, []);

  const completeStop = useCallback(
    (outletId: string, outcome: "delivered" | "partial" | "failed") => {
      if (outcome === "delivered") {
        setCompletedStopIds((prev) =>
          prev.includes(outletId) ? prev : [...prev, outletId],
        );
      } else if (outcome === "partial") {
        setFlaggedStopIds((prev) =>
          prev.includes(outletId) ? prev : [...prev, outletId],
        );
      } else if (outcome === "failed") {
        setFailedStopIds((prev) =>
          prev.includes(outletId) ? prev : [...prev, outletId],
        );
      }

      // Advance to next stop if available
      setCurrentStopIndex((prev) =>
        prev < trip1Sequence.length - 1 ? prev + 1 : prev,
      );
    },
    [trip1Sequence],
  );

  const currentStopSeq = currentStopIndex + 1;
  const setCurrentStopSeq = useCallback(
    (seq: number) => {
      setCurrentStopIndex(Math.max(0, seq - 1));
    },
    [],
  );

  const value = useMemo(
    () => ({
      connection,
      setConnection,
      syncRecords,
      addSyncRecord,
      updateSyncRecord,
      trip1Started,
      trip2Unlocked,
      startTrip1,
      completeTrip1,
      currentStopSeq,
      setCurrentStopSeq,
      currentStopIndex,
      trip1Sequence,
      completedStopIds,
      flaggedStopIds,
      failedStopIds,
      completeStop,
      routeUpdateAccepted,
      acceptRouteUpdate,
      syncReviewForwarded,
      forwardSyncReview,
      applyScenario,
    }),
    [
      connection,
      setConnection,
      syncRecords,
      addSyncRecord,
      updateSyncRecord,
      trip1Started,
      trip2Unlocked,
      startTrip1,
      completeTrip1,
      currentStopSeq,
      setCurrentStopSeq,
      currentStopIndex,
      trip1Sequence,
      completedStopIds,
      flaggedStopIds,
      failedStopIds,
      completeStop,
      routeUpdateAccepted,
      acceptRouteUpdate,
      syncReviewForwarded,
      forwardSyncReview,
      applyScenario,
    ],
  );

  return (
    <DriverStateContext.Provider value={value}>
      {children}
    </DriverStateContext.Provider>
  );
}
