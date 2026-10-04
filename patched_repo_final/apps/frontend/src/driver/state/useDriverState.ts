import { useContext } from "react";
import { DriverStateContext } from "./DriverStateProvider";

export function useDriverState() {
  const ctx = useContext(DriverStateContext);
  if (!ctx) throw new Error("useDriverState must be used inside DriverStateProvider");
  return ctx;
}
