import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { Button } from "@/driver/components/Button";
import { Card } from "@/driver/components/Card";
import { DRIVER, VEHICLE } from "@/driver/data/driverContent";
import { maskPin } from "@/lib/security";

export function SignInScreen() {
  const { push } = useNavigator();
  const [pin, setPin] = useState<string>("1234");

  const handleSignIn = () => {
    push("start-day");
  };

  return (
    <div className="p-4 space-y-5 max-w-[430px] mx-auto pt-8">
      <div className="text-center space-y-1">
        <span className="text-xs font-bold text-green tracking-wider uppercase">
          Waypoint Group
        </span>
        <h1 className="text-xl font-extrabold text-ink">Driver sign-in</h1>
        <p className="text-xs text-ink-muted">
          Secure access for today’s assigned route.
        </p>
      </div>

      <Card variant="surface" className="space-y-4">
        <div>
          <label htmlFor="driver-id" className="block text-2xs font-bold text-ink-muted uppercase mb-1">
            Driver ID
          </label>
          <input
            id="driver-id"
            type="text"
            readOnly
            value={DRIVER.name}
            className="w-full p-3 bg-raised border border-line rounded-btn font-semibold text-ink text-sm"
          />
        </div>

        <div>
          <label htmlFor="secure-pin" className="block text-2xs font-bold text-ink-muted uppercase mb-1">
            Secure PIN
          </label>
          <input
            id="secure-pin"
            type="password"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="••••"
            maxLength={4}
            className="w-full p-3 bg-raised border border-line rounded-btn font-semibold text-ink text-sm tracking-widest text-center"
          />
        </div>

        <div className="text-2xs text-ink-muted text-center pt-1">
          Device verified · {VEHICLE.depot} depot
        </div>
      </Card>

      <div className="space-y-2.5 pt-2">
        <Button variant="primary" size="lg" onClick={handleSignIn}>
          Sign in
        </Button>
        <Button
          variant="ghost"
          size="md"
          onClick={() => push("contact-dispatch")}
        >
          Need help? Call depot support
        </Button>
      </div>
    </div>
  );
}
