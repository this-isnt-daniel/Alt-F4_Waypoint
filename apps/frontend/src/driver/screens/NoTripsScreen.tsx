import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { AppIcon } from "@/driver/components/AppIcon";

export function NoTripsScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center pt-12">
      <div className="w-16 h-16 rounded-full bg-slate-100 mx-auto flex items-center justify-center mb-4">
        <AppIcon name="package" size={32} className="text-slate-400" />
      </div>
      <h1 className="text-lg font-bold text-slate-900">No trips assigned</h1>
      <p className="text-[13px] text-slate-500 max-w-xs mx-auto">
        There are no trips scheduled for you right now. Refresh to check again or contact dispatch if you're expecting a route.
      </p>
      
      <div className="space-y-2 pt-6">
        <Button variant="primary" size="lg" onClick={() => push("today-trips")}>
          <AppIcon name="refresh" size={16} className="mr-2" /> Refresh trips
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("contact-dispatch")}>
          Call dispatch
        </Button>
      </div>
    </div>
  );
}
