import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { HeroBand } from "@/driver/components/HeroBand";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { DAY_SUMMARY } from "@/driver/data/driverContent";

export function DaySummaryScreen() {
  const { push } = useNavigator();

  return (
    <div className="pb-8 max-w-[430px] mx-auto">
      <HeroBand
        label="DAY RECORD"
        title={DAY_SUMMARY.title}
        subline={DAY_SUMMARY.subtitle}
      />

      <div className="px-4 space-y-4">
        <Card variant="surface" className="space-y-2">
          <div className="text-2xs font-extrabold uppercase text-ink-muted tracking-wider pb-1">
            OPERATIONAL LOG SUMMARY
          </div>

          <KeyValueRow label="Driver" value={DAY_SUMMARY.driver} />
          <KeyValueRow label="Vehicle" value={DAY_SUMMARY.vehicle} />
          <KeyValueRow label="Home depot" value={DAY_SUMMARY.depot} />
          <KeyValueRow label="Shift duration" value={DAY_SUMMARY.shift} />
          <KeyValueRow label="Trips completed" value={DAY_SUMMARY.trips} />
          <KeyValueRow label="Stops visited" value={DAY_SUMMARY.stops} />
          <KeyValueRow label="Deliveries" value={DAY_SUMMARY.deliveries} />
          <KeyValueRow label="Return custody" value={DAY_SUMMARY.returns} />
          <KeyValueRow label="Sync status" value={DAY_SUMMARY.sync} emphasis="strong" />
        </Card>

        <Card variant="raised" className="text-xs text-ink-muted leading-relaxed text-center">
          {DAY_SUMMARY.closing}
        </Card>

        <div className="pt-2">
          <Button variant="primary" size="lg" onClick={() => push("signin")}>
            Finish day & sign out
          </Button>
        </div>
      </div>
    </div>
  );
}
