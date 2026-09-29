import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { ListRow } from "@/driver/components/ListRow";
import { OUT047_CHECKLIST_ITEMS, TRIP_1_STOPS } from "@/driver/data/driverContent";

export function ChecklistScreen() {
  const { route, push } = useNavigator();
  const outletId = route.params.outletId ?? "OUT047";
  const stop = TRIP_1_STOPS.find((s) => s.outletId === outletId) ?? TRIP_1_STOPS[1]!;

  const [itemStates, setItemStates] = useState<Record<string, "pending" | "delivered" | "flagged">>(
    () => Object.fromEntries(OUT047_CHECKLIST_ITEMS.map((item) => [item.id, "pending"])),
  );

  const toggleDelivered = (id: string) => {
    setItemStates((prev) => ({
      ...prev,
      [id]: prev[id] === "delivered" ? "pending" : "delivered",
    }));
  };

  const handleFlag = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setItemStates((prev) => ({ ...prev, [id]: "flagged" }));
    push("not-handed-over", { itemId: id, outletId: stop.outletId });
  };

  const allHandled = Object.values(itemStates).every((st) => st !== "pending");
  const hasFlagged = Object.values(itemStates).some((st) => st === "flagged");

  const handleMarkAllDelivered = () => {
    setItemStates(
      Object.fromEntries(OUT047_CHECKLIST_ITEMS.map((item) => [item.id, "delivered"])),
    );
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-green tracking-wider uppercase">
          Unloading Checklist
        </span>
        <h1 className="text-xl font-extrabold text-ink">{stop.name}</h1>
        <p className="text-xs text-ink-muted">
          {stop.outletId} · arrived 06:18 · Receiver: {stop.manager}
        </p>
      </div>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-0.5">Instruction:</span>
        Check every item. Mark delivered or flag what was not handed over.
      </Card>

      <div className="space-y-2">
        {OUT047_CHECKLIST_ITEMS.map((item) => {
          const state = itemStates[item.id] ?? "pending";
          const isDelivered = state === "delivered";
          const isFlagged = state === "flagged";

          return (
            <ListRow
              key={item.id}
              title={`${item.name} ×${item.quantity}`}
              subtitle={item.temp}
              status={isDelivered ? "delivered" : isFlagged ? "flagged" : "pending"}
              statusLabel={isDelivered ? "Handed over" : isFlagged ? "Flagged" : "Pending"}
              onClick={() => toggleDelivered(item.id)}
              trailing={
                !isDelivered && (
                  <button
                    type="button"
                    onClick={(e) => handleFlag(item.id, e)}
                    className="text-2xs font-bold text-warning border border-warning/30 px-2 py-1 rounded-pill bg-warning-fill hover:opacity-80"
                  >
                    Flag issue
                  </button>
                )
              }
            />
          );
        })}
      </div>

      {!allHandled && (
        <Button variant="secondary" size="md" onClick={handleMarkAllDelivered}>
          Mark all items delivered
        </Button>
      )}

      <div className="pt-2">
        <Button
          variant={allHandled ? "primary" : "secondary"}
          size="lg"
          disabled={!allHandled}
          onClick={() => push(hasFlagged ? "partial-summary" : "pod-photo", { outletId: stop.outletId })}
        >
          {hasFlagged ? "Review partial handover" : "Continue to proof"}
        </Button>
      </div>
    </div>
  );
}
