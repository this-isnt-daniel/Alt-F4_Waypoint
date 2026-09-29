import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";

export function CallOverlayScreen() {
  const { route, back } = useNavigator();
  const outletId = route.params.outletId ?? "OUT047";

  return (
    <div className="p-4 max-w-[430px] mx-auto min-h-[80vh] flex flex-col items-center justify-center">
      <Card variant="raised" className="w-full text-center space-y-4 p-6">
        <div className="w-16 h-16 rounded-full bg-slate-100 mx-auto flex items-center justify-center">
          <AppIcon name="phone" size={32} className="text-slate-600" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Call Anjali Silva?</h1>
          <p className="text-[13px] text-slate-500">Store manager · {outletId}</p>
        </div>
        <div className="text-[15px] font-mono text-slate-900 bg-slate-50 py-2 rounded-lg border border-slate-100 tracking-wider">
          +94 77 ••• ••42
        </div>
        <p className="text-[12px] text-slate-400 leading-tight">Your personal number stays hidden. Standard call rates may apply.</p>
        <div className="flex gap-2 pt-2">
          <Button variant="secondary" size="md" fullWidth={false} className="flex-1" onClick={back}>Cancel</Button>
          <Button variant="primary" size="md" fullWidth={false} className="flex-1" onClick={back}>Call</Button>
        </div>
      </Card>
    </div>
  );
}
