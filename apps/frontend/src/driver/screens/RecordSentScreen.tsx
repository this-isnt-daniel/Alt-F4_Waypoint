import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { Chip } from "@/driver/components/Chip";
import { KeyValueRow } from "@/driver/components/KeyValueRow";
import { RECORD_SENT } from "@/driver/data/driverContent";

export function RecordSentScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8 pt-4">
      <div className="flex items-center justify-between">
        <span className="text-2xs font-extrabold text-offline tracking-wider uppercase">
          Evidence Forwarded
        </span>
        <Chip kind="sync" tone="forwarded" label="FORWARDED" />
      </div>

      <div className="space-y-1">
        <h1 className="text-xl font-extrabold text-ink">{RECORD_SENT.title}</h1>
        <p className="text-xs font-semibold text-ink-muted">{RECORD_SENT.subtitle}</p>
      </div>

      <Card variant="surface" className="space-y-3">
        <p className="text-xs text-ink leading-relaxed">{RECORD_SENT.body}</p>

        <div className="p-3 bg-raised rounded-btn space-y-1.5 text-xs">
          <span className="font-bold text-ink block">{RECORD_SENT.preservedTitle}</span>
          <p className="text-ink-muted">{RECORD_SENT.preservedBody}</p>
        </div>

        <KeyValueRow label="Delivery photo" value="Captured 07:13 · attached" />
        <KeyValueRow label="Manager PIN" value="Field confirmation · protected" emphasis="strong" />
      </Card>

      <Card variant="raised" className="text-xs text-ink-muted leading-relaxed">
        <span className="font-bold text-ink block mb-0.5">Route Continuity:</span>
        {RECORD_SENT.continueLine}
      </Card>

      {/* Board annotation outside phone frame styling */}
      <div className="p-3 border-2 border-dashed border-line rounded-card text-2xs text-ink-muted leading-tight bg-raised/50">
        <span className="font-bold text-ink block mb-0.5">[BOARD ANNOTATION]</span>
        Resolution controls — accept reassignment / keep driver record / contact store — live on the DISPATCHER and STORE-MANAGER surfaces. The driver surface only preserves and forwards field evidence.
      </div>

      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("active-trip")}>
          {RECORD_SENT.primary}
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("sync-centre")}>
          {RECORD_SENT.secondary}
        </Button>
      </div>
    </div>
  );
}
