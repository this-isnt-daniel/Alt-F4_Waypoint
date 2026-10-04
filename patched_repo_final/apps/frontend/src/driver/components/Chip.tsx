import { cn } from "@/lib/cn";
import { AppIcon, type AppIconName } from "./AppIcon";

export type ChipProps =
  | {
      kind: "status";
      tone: "early" | "onTime" | "lateRisk" | "windowClosing" | "windowMissed";
      label: string;
      className?: string;
    }
  | {
      kind: "restriction";
      category: "temperature" | "access" | "dock";
      label: string;
      icon: AppIconName;
      className?: string;
    }
  | {
      kind: "capability";
      label:
        | "CHILLED REEFER"
        | "AMBIENT"
        | "VAN ONLY"
        | "LOCKED"
        | "COMPLETED"
        | "ACTIVE · AMBIENT";
      className?: string;
    }
  | {
      kind: "outcome";
      tone: "delivered" | "partial" | "failed" | "returned" | "complete" | "tripComplete";
      label: string;
      count?: number;
      className?: string;
    }
  | {
      kind: "sync";
      tone:
        | "online"
        | "offline"
        | "saving"
        | "pending"
        | "syncing"
        | "success"
        | "failed"
        | "inReview"
        | "routeUpdated"
        | "forwarded";
      label: string;
      className?: string;
    };

export function Chip(props: ChipProps) {
  const baseStyles =
    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium tracking-wide uppercase";

  if (props.kind === "restriction") {
    return (
      <span
        className={cn(
          baseStyles,
          "text-restriction bg-restriction-fill border border-restriction-line",
          props.className,
        )}
      >
        <AppIcon name={props.icon} size={12} />
        <span>{props.label}</span>
      </span>
    );
  }

  if (props.kind === "capability") {
    const isLocked = props.label === "LOCKED";
    const isCompleted = props.label === "COMPLETED";
    return (
      <span
        className={cn(
          baseStyles,
          isLocked
            ? "bg-raised text-ink-muted border border-line"
            : isCompleted
              ? "bg-slate-100 text-slate-600 border border-slate-200"
              : "bg-green-fill text-green border border-green/20 font-semibold",
          props.className,
        )}
      >
        <AppIcon
          name={isLocked ? "lock" : isCompleted ? "check" : "snowflake"}
          size={12}
        />
        <span>{props.label}</span>
      </span>
    );
  }

  if (props.kind === "status") {
    const toneStyles = {
      early: "bg-surface text-ink border border-line",
      onTime: "bg-success-fill text-success border border-success/30",
      lateRisk: "bg-warning-fill text-warning border border-warning/30",
      windowClosing: "bg-warning-fill text-warning border border-warning/30",
      windowMissed: "bg-danger-fill text-danger border border-danger/30",
    };
    return (
      <span className={cn(baseStyles, toneStyles[props.tone], props.className)}>
        <span>{props.label}</span>
      </span>
    );
  }

  if (props.kind === "outcome") {
    const isFailedZero = props.tone === "failed" && (props.count === 0 || props.count === undefined);

    let toneStyle = "bg-success-fill text-success border border-success/30";
    let iconName: AppIconName = "check";

    if (props.tone === "partial") {
      toneStyle = "bg-warning-fill text-warning border border-warning/30";
      iconName = "alert";
    } else if (props.tone === "failed") {
      if (isFailedZero) {
        toneStyle = "bg-raised text-ink-muted border border-line";
        iconName = "dot";
      } else {
        toneStyle = "bg-danger-fill text-danger border border-danger/30";
        iconName = "x";
      }
    } else if (props.tone === "returned") {
      toneStyle = "bg-raised text-ink-muted border border-line";
      iconName = "refresh";
    } else if (props.tone === "tripComplete" || props.tone === "complete") {
      toneStyle = "bg-success-fill text-success border border-success/30";
      iconName = "check-circle";
    }

    return (
      <span className={cn(baseStyles, toneStyle, props.className)}>
        <AppIcon name={iconName} size={12} />
        <span>{props.label}</span>
      </span>
    );
  }

  if (props.kind === "sync") {
    const toneStyles: Record<string, string> = {
      online: "bg-success-fill text-success border border-success/30",
      offline: "bg-raised text-ink-muted border border-line",
      saving: "bg-raised text-ink-muted border border-line",
      pending: "bg-raised text-ink-muted border border-line",
      syncing: "bg-raised text-ink-muted border border-line animate-pulse",
      success: "bg-success-fill text-success border border-success/30",
      failed: "bg-danger-fill text-danger border border-danger/30",
      inReview: "bg-warning-fill text-warning border border-warning/30",
      routeUpdated: "bg-raised text-ink-muted border border-line",
      forwarded: "bg-raised text-ink-muted border border-line",
    };

    const iconMap: Record<string, AppIconName> = {
      online: "wifi", offline: "wifi-off", saving: "refresh",
      pending: "clock", syncing: "refresh", success: "check",
      failed: "alert", inReview: "eye", routeUpdated: "route",
      forwarded: "send",
    };

    return (
      <span className={cn(baseStyles, toneStyles[props.tone] ?? toneStyles.offline, props.className)}>
        <AppIcon name={iconMap[props.tone] ?? "dot"} size={12} />
        <span>{props.label}</span>
      </span>
    );
  }

  return null;
}
