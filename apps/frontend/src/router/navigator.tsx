import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export type ScreenId =
  | "signin"
  | "start-day"
  | "today-trips"
  | "trip-briefing"
  | "load-confirm"
  | "active-trip"
  | "stop-detail"
  | "mark-arrived"
  | "checklist"
  | "not-handed-over"
  | "pod-photo"
  | "pod-pin"
  | "delivery-complete"
  | "partial-summary"
  | "failed-reason"
  | "return-depot"
  | "depot-return"
  | "trip-complete"
  | "day-summary"
  | "offline-saved"
  | "sync-centre"
  | "route-changed"
  | "outlet-closed"
  | "sync-review"
  | "record-sent"
  | "no-trips"
  | "camera-denied"
  | "location-denied"
  | "sync-failed"
  | "chat"
  | "call-overlay"
  | "issue-wizard"
  | "contact-dispatch";

const ALL_SCREEN_IDS: ScreenId[] = [
  "signin",
  "start-day",
  "today-trips",
  "trip-briefing",
  "load-confirm",
  "active-trip",
  "stop-detail",
  "mark-arrived",
  "checklist",
  "not-handed-over",
  "pod-photo",
  "pod-pin",
  "delivery-complete",
  "partial-summary",
  "failed-reason",
  "return-depot",
  "depot-return",
  "trip-complete",
  "day-summary",
  "offline-saved",
  "sync-centre",
  "route-changed",
  "outlet-closed",
  "sync-review",
  "record-sent",
  "no-trips",
  "camera-denied",
  "location-denied",
  "sync-failed",
  "chat",
  "call-overlay",
  "issue-wizard",
  "contact-dispatch",
];

function isScreenId(value: string): value is ScreenId {
  return (ALL_SCREEN_IDS as string[]).includes(value);
}

type Params = Record<string, string>;
export type Route = { id: ScreenId; params: Params };

function parseHash(): Route {
  const raw = window.location.hash.replace(/^#\/?/, "");
  const [idRaw, queryString] = raw.split("?");
  const id: ScreenId = idRaw && isScreenId(idRaw) ? idRaw : "signin";
  const params: Params = {};

  if (queryString) {
    for (const [key, value] of new URLSearchParams(queryString)) {
      params[key] = value;
    }
  }

  return { id, params };
}

function serializeRoute(route: Route): string {
  const query = new URLSearchParams(route.params).toString();
  return `#/${route.id}${query ? `?${query}` : ""}`;
}

type NavigatorValue = {
  route: Route;
  push: (id: ScreenId, params?: Params) => void;
  replace: (id: ScreenId, params?: Params) => void;
  back: () => void;
};

const NavigatorContext = createContext<NavigatorValue | null>(null);

export function NavigatorProvider({ children }: { children: ReactNode }) {
  const [route, setRoute] = useState<Route>(() => parseHash());

  useEffect(() => {
    function onHashChange() {
      setRoute(parseHash());
    }

    window.addEventListener("hashchange", onHashChange);

    if (!window.location.hash) {
      window.location.replace(serializeRoute({ id: "signin", params: {} }));
    }

    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const push = useCallback((id: ScreenId, params: Params = {}) => {
    window.location.hash = serializeRoute({ id, params });
  }, []);

  const replace = useCallback((id: ScreenId, params: Params = {}) => {
    window.location.replace(serializeRoute({ id, params }));
  }, []);

  const back = useCallback(() => {
    window.history.back();
  }, []);

  const value = useMemo(
    () => ({ route, push, replace, back }),
    [route, push, replace, back],
  );

  return <NavigatorContext.Provider value={value}>{children}</NavigatorContext.Provider>;
}

export function useNavigator() {
  const ctx = useContext(NavigatorContext);
  if (!ctx) throw new Error("useNavigator must be used inside NavigatorProvider");
  return ctx;
}
