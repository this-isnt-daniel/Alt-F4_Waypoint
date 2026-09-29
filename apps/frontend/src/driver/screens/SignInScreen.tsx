import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { AppIcon } from "@/driver/components/AppIcon";
import { DRIVER, VEHICLE } from "@/driver/data/driverContent";

export function SignInScreen() {
  const { push } = useNavigator();
  const [pin, setPin] = useState<string>("");

  return (
    <div className="p-4 space-y-5 max-w-[430px] mx-auto pt-8">
      <div className="text-center space-y-1">
        <h1 className="text-xl font-bold text-slate-900">Driver sign-in</h1>
        <p className="text-[13px] text-slate-500">Sign in to start your route.</p>
      </div>

      <Card variant="surface" className="space-y-4">
        <div>
          <label htmlFor="driver-id" className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Driver ID
          </label>
          <input
            id="driver-id"
            type="text"
            readOnly
            value={DRIVER.name}
            className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg font-semibold text-slate-900 text-[14px]"
          />
        </div>

        <div>
          <label htmlFor="secure-pin" className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Secure PIN
          </label>
          <input
            id="secure-pin"
            type="password"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="••••"
            maxLength={4}
            className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg font-semibold text-slate-900 text-[14px] tracking-[0.3em] text-center"
          />
        </div>

        <div className="text-[11px] text-slate-400 text-center pt-1">
          {VEHICLE.depot} depot
        </div>
      </Card>

      <div className="space-y-2.5 pt-2">
        <Button variant="primary" size="lg" onClick={() => push("start-day")}>
          Sign in
        </Button>
        <Button
          variant="ghost"
          size="md"
          onClick={() => push("contact-dispatch")}
        >
          <AppIcon name="phone" size={16} className="mr-2" />
          Call depot support
        </Button>
      </div>
    </div>
  );
}
