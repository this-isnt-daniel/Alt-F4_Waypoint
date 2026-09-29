import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { RECORD_SENT } from "@/driver/data/driverContent";

export function RecordSentScreen() {
  const { push } = useNavigator();
  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center">
      <div className="pt-6">
        <div className="w-16 h-16 rounded-full bg-green-fill mx-auto flex items-center justify-center mb-3">
          <AppIcon name="send" size={28} className="text-green" />
        </div>
        <h1 className="text-lg font-bold text-slate-900">{RECORD_SENT.title}</h1>
        <p className="text-[13px] text-slate-500">{RECORD_SENT.subtitle}</p>
      </div>
      <p className="text-[13px] text-slate-500">{RECORD_SENT.body}</p>
      <p className="text-[13px] text-slate-500">{RECORD_SENT.continueLine}</p>
      <div className="space-y-2 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("active-trip")}>{RECORD_SENT.primary}</Button>
        <Button variant="ghost" size="md" onClick={() => push("sync-centre")}>{RECORD_SENT.secondary}</Button>
      </div>
    </div>
  );
}
