import { useMemo, useState } from "react";
import { resolvePortal } from "@/app/portal";
import { DriverApp } from "@/driver/DriverApp";

// Legacy portals
import DispatcherLogin from "./pages/dispatcher/DispatcherLogin";
import DispatcherRoster from "./pages/dispatcher/DispatcherRoster";
import StoreManagerLogin from "./pages/storemanager/StoreManagerLogin";
import StoreManagerOverview from "./pages/storemanager/StoreManagerOverview";

export default function App() {
  const portal = useMemo(() => resolvePortal(window.location.search), []);
  const [currentPage, setCurrentPage] = useState("login");

  if (portal === "driver") return <DriverApp />;

  if (portal === "store-manager") {
    if (currentPage === "overview") {
      return <StoreManagerOverview onLogout={() => setCurrentPage("login")} />;
    }
    return <StoreManagerLogin onLogin={() => setCurrentPage("overview")} />;
  }

  // Dispatcher Portal (Default fallback for unknown or absent portal)
  if (currentPage === "overview") {
    return <DispatcherRoster onLogout={() => setCurrentPage("login")} />;
  }

  return <DispatcherLogin onLogin={() => setCurrentPage("overview")} />;
}
