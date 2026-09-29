import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { ListRow } from "@/driver/components/ListRow";
import { ROUTE_UPDATE } from "@/driver/data/driverContent";
import { useDriverState } from "@/driver/state/useDriverState";

export function RouteChangedScreen() {
  const { push } = useNavigator();
  const { acceptRouteUpdate, setCurrentStopSeq } = useDriverState();

  const handleAccept = () => {
    acceptRouteUpdate();
    setCurrentStopSeq(7); // OUT061 is seq 7
    push("active-trip");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      <div className="space-y-1">
        <span className="text-2xs font-extrabold text-warning tracking-wider uppercase">
          Route Resequenced · {ROUTE_UPDATE.dispatcherTime}
        </span>
        <h1 className="text-xl font-extrabold text-ink">{ROUTE_UPDATE.headline}</h1>
        <p className="text-xs text-ink-muted leading-relaxed">{ROUTE_UPDATE.body}</p>
      </div>

      <Card variant="surface" className="space-y-2">
        <div className="text-2xs font-extrabold uppercase text-ink-muted tracking-wider pb-1">
          SEQUENCE CHANGES
        </div>

        {ROUTE_UPDATE.changes.map((change, idx) => (
          <ListRow
            key={idx}
            title={change.outletName}
            subtitle={`Sequence: stop #${change.fromSeq} → #${change.toSeq}`}
            status={change.type === "moved_next" ? "matches" : "returned"}
            statusLabel={change.type === "moved_next" ? "Moved next" : "Moved later"}
          />
        ))}

        <KeyValueRow label="New ETA" value={ROUTE_UPDATE.newEta} emphasis="strong" />
        <KeyValueRow label="Target Window" value={ROUTE_UPDATE.window} />
      </Card>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-0.5">Reassurance:</span>
        {ROUTE_UPDATE.reassurance}
      </Card>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={handleAccept}>
          {ROUTE_UPDATE.primary}
        </Button>
        <Button
          variant="secondary"
          size="md"
          onClick={() => push("call-overlay", { role: "dispatcher" })}
        >
          Call dispatcher
        </Button>
        <Button variant="ghost" size="md" onClick={() => push("active-trip")}>
          View map
        </Button>
      </div>
    </div>
  );
}
