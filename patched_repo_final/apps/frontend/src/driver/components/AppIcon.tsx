import {
  AlertTriangle, ArrowLeft, Building2, Camera, Check, CheckCircle2,
  ChevronDown, ChevronUp, ChevronRight, CloudOff, Clock, Fuel,
  List, Map as MapIcon, MessageSquare, Moon, Navigation, Package,
  Phone, MapPin, RefreshCw, Route, Snowflake, Sun, Truck, Lock,
  MoreVertical, X, Eye, EyeOff, Shield, Send, CircleDot, Wifi, WifiOff, Save,
  type LucideIcon,
} from "lucide-react";

export type AppIconName =
  | "alert" | "arrow-left" | "building" | "camera" | "check" | "check-circle"
  | "chevron-down" | "chevron-up" | "chevron-right" | "cloud-off" | "clock"
  | "fuel" | "list" | "map" | "message" | "moon" | "navigate" | "package"
  | "phone" | "pin" | "refresh" | "route" | "snowflake" | "sun" | "truck"
  | "lock" | "more" | "x" | "eye" | "eye-off" | "shield" | "send"
  | "dot" | "wifi" | "wifi-off" | "save";

const ICONS: Record<AppIconName, LucideIcon> = {
  alert: AlertTriangle, "arrow-left": ArrowLeft, building: Building2,
  camera: Camera, check: Check, "check-circle": CheckCircle2,
  "chevron-down": ChevronDown, "chevron-up": ChevronUp, "chevron-right": ChevronRight,
  "cloud-off": CloudOff, clock: Clock, fuel: Fuel, list: List, map: MapIcon,
  message: MessageSquare, moon: Moon, navigate: Navigation, package: Package,
  phone: Phone, pin: MapPin, refresh: RefreshCw, route: Route,
  snowflake: Snowflake, sun: Sun, truck: Truck, lock: Lock,
  more: MoreVertical, x: X, eye: Eye, "eye-off": EyeOff,
  shield: Shield, send: Send, dot: CircleDot, wifi: Wifi, "wifi-off": WifiOff,
  save: Save,
};

export function AppIcon({
  name, size = 20, className, "aria-label": ariaLabel,
}: {
  name: AppIconName; size?: number; className?: string; "aria-label"?: string;
}) {
  const Icon = ICONS[name];
  return (
    <Icon
      size={size}
      className={className}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : true}
      focusable="false"
    />
  );
}
