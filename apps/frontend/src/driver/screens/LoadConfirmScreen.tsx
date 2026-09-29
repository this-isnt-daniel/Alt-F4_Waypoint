import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { HeroBand } from "@/driver/components/HeroBand";
import { ListRow } from "@/driver/components/ListRow";
import { Toast } from "@/driver/components/Toast";
import {
  LOAD_REVIEW_GROUPS,
  LOAD_SUMMARY,
  LOADER,
  TRIP_1,
} from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";
import { formatNumber } from "@/lib/derive";

export function LoadConfirmScreen() {
  const { push } = useNavigator();
  const { connection, addSyncRecord, startTrip1 } = useDriverState();
  const [toastVisible, setToastVisible] = useState<boolean>(false);

  const handleConfirmDepart = () => {
    startTrip1();
    addSyncRecord({
      type: "load-confirmation",
      state: connection === "online" ? "synced" : "pending",
      hasPhoto: false,
      pinVerified: false,
    });

    setToastVisible(true);
    setTimeout(() => {
      push("active-trip");
    }, 1200);
  };

  return (
    <div className="pb-8 max-w-[430px] mx-auto">
      <HeroBand
        label="BEFORE YOU LEAVE"
        title="Load confirmation"
        subline={`Trip 1 · Fresh · Kandy · ${TRIP_1.stopCount} stops · ${formatNumber(LOAD_SUMMARY.manifestUnits)} units · loader ${LOADER.name}`}
      />

      <div className="px-4 space-y-4">
        <div className="p-3 bg-raised rounded-card border border-line text-xs text-ink-muted leading-relaxed">
          <span className="font-bold text-ink block mb-0.5">Manifest Reconcile:</span>
          Match the van to the manifest. Flag anything short, extra, or damaged — dispatch sees it now, not at the outlet.
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs font-extrabold uppercase text-ink-muted px-1">
            <span>Count against manifest</span>
            <span>{LOAD_SUMMARY.groupCount} groups · {LOAD_SUMMARY.flaggedCount} flagged</span>
          </div>

          {LOAD_REVIEW_GROUPS.map((group) => {
            const isFlagged = group.status === "flagged";

            return (
              <ListRow
                key={group.id}
                title={group.label}
                subtitle={`${group.manifestUnits} manifest units`}
                status={isFlagged ? "flagged" : "matches"}
                statusLabel={isFlagged ? "Flagged" : "Matches"}
                expandable={isFlagged}
                expandedContent={
                  isFlagged && group.lineItem ? (
                    <div className="space-y-2 text-xs">
                      <div className="font-bold text-ink">{group.lineItem.name}</div>
                      <div className="grid grid-cols-3 gap-2 bg-surface p-2 rounded-btn border border-line">
                        <div>
                          <span className="text-ink-muted block">Manifest</span>
                          <span className="font-bold text-ink">{group.lineItem.manifestQuantity}</span>
                        </div>
                        <div>
                          <span className="text-ink-muted block">Deliverable</span>
                          <span className="font-bold text-ink">{group.lineItem.deliverableQuantity}</span>
                        </div>
                        <div>
                          <span className="text-ink-muted block">Return</span>
                          <span className="font-bold text-warning">{group.lineItem.returnQuantity}</span>
                        </div>
                      </div>
                      <div>
                        <span className="text-ink-muted">Reason: </span>
                        <span className="font-medium text-ink">{group.lineItem.reason}</span>
                      </div>
                      <div>
                        <span className="text-ink-muted">Return Crate: </span>
                        <span className="font-bold text-ink">{group.lineItem.returnCrate}</span>
                      </div>
                      {group.loaderNote && (
                        <div className="p-2 bg-warning-fill text-warning rounded-btn font-medium">
                          {group.loaderNote}
                        </div>
                      )}
                    </div>
                  ) : undefined
                }
              />
            );
          })}
        </div>

        {/* Footer Summary */}
        <div className="p-3 bg-surface rounded-card border border-line text-xs font-semibold text-ink text-center">
          {TRIP_1.stopCount} stops · manifest {formatNumber(LOAD_SUMMARY.manifestUnits)} units · deliverable {formatNumber(LOAD_SUMMARY.deliverableUnits)} · return {LOAD_SUMMARY.returnUnits} · 1 discrepancy
        </div>

        {connection === "offline" && (
          <div className="text-2xs text-ink-muted text-center italic">
            Saved on this phone. Dispatch notification is queued.
          </div>
        )}

        <Button variant="primary" size="lg" onClick={handleConfirmDepart}>
          {connection === "online"
            ? "Confirm & depart"
            : "Confirm & depart · saved offline"}
        </Button>
      </div>

      <Toast
        message="Dispatch notified · 2 return items at OUT058"
        visible={toastVisible}
        onClose={() => setToastVisible(false)}
      />
    </div>
  );
}
