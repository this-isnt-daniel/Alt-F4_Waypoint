import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";

export function CameraDeniedScreen() {
  const { push } = useNavigator();

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto text-center pt-8">
      <div className="w-16 h-16 rounded-full bg-amber-50 mx-auto flex items-center justify-center mb-3">
        <AppIcon name="camera" size={32} className="text-amber-500" />
      </div>
      <h1 className="text-lg font-bold text-slate-900">Camera access needed</h1>
      <p className="text-[13px] text-slate-500">
        Waypoint Driver needs the camera only to capture delivery and issue evidence.
      </p>
      
      <Card variant="surface" className="text-left mt-4">
        <div className="text-[13px] text-slate-500">• Used for POD and issue photos</div>
        <div className="text-[13px] text-slate-500">• Stored securely in Waypoint</div>
        <div className="text-[13px] text-slate-500">• Not used for background recording</div>
      </Card>

      <div className="space-y-2 pt-4">
        <Button variant="primary" size="lg" onClick={() => push("pod-photo")}>
          Allow camera access
        </Button>
        <Button variant="secondary" size="md" onClick={() => push("pod-pin")}>
          Save without photo
        </Button>
      </div>
    </div>
  );
}
