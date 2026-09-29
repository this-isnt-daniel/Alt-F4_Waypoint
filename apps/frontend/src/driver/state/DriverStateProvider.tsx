import {
  createContext,
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { type ConnectionState } from "./connection";
import { type SyncRecord } from "./syncQueue";

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
  routeUpdateAccepted: boolean;
  acceptRouteUpdate: () => void;
  syncReviewForwarded: boolean;
  forwardSyncReview: () => void;
}

export const DriverStateContext = createContext<DriverStateContextValue | null>(null);

export function DriverStateProvider({ children }: { children: ReactNode }) {
  const [connection, setConnectionState] = useState<ConnectionState>("online");
  const [syncRecords, setSyncRecords] = useState<SyncRecord[]>([]);
  const [trip1Started, setTrip1Started] = useState<boolean>(false);
  const [trip2Unlocked, setTrip2Unlocked] = useState<boolean>(false);
  const [currentStopSeq, setCurrentStopSeq] = useState<number>(2);
  const [routeUpdateAccepted, setRouteUpdateAccepted] = useState<boolean>(false);
  const [syncReviewForwarded, setSyncReviewForwarded] = useState<boolean>(false);

  const setConnection = useCallback((next: ConnectionState) => {
    setConnectionState(next);
  }, []);

  const addSyncRecord = useCallback((record: Omit<SyncRecord, "id" | "createdAt">) => {
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
  }, []);

  const updateSyncRecord = useCallback((id: string, patch: Partial<SyncRecord>) => {
    setSyncRecords((prev) =>
      prev.map((item) => (item.id === id ? { ...item, ...patch } : item)),
    );
  }, []);

  const startTrip1 = useCallback(() => {
    setTrip1Started(true);
  }, []);

  const completeTrip1 = useCallback(() => {
    setTrip2Unlocked(true);
  }, []);

  const acceptRouteUpdate = useCallback(() => {
    setRouteUpdateAccepted(true);
  }, []);

  const forwardSyncReview = useCallback(() => {
    setSyncReviewForwarded(true);
  }, []);

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
      routeUpdateAccepted,
      acceptRouteUpdate,
      syncReviewForwarded,
      forwardSyncReview,
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
      routeUpdateAccepted,
      acceptRouteUpdate,
      syncReviewForwarded,
      forwardSyncReview,
    ],
  );

  return (
    <DriverStateContext.Provider value={value}>
      {children}
    </DriverStateContext.Provider>
  );
}
