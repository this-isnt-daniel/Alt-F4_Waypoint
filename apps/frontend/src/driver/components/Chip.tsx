import { cn } from "@/lib/cn";

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
      glyph: string;
      className?: string;
    }
  | {
      kind: "capability";
      label: "CHILLED REEFER" | "AMBIENT" | "VAN ONLY" | "LOCKED";
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
    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-pill text-xs font-medium tracking-wide uppercase";

  if (props.kind === "restriction") {
    return (
      <span
        className={cn(
          baseStyles,
          "text-restriction bg-restriction-fill border border-restriction-line",
          props.className,
        )}
      >
        <span aria-hidden="true">{props.glyph}</span>
        <span>{props.label}</span>
      </span>
    );
  }

  if (props.kind === "capability") {
    const isLocked = props.label === "LOCKED";
    return (
      <span
        className={cn(
          baseStyles,
          isLocked
            ? "bg-offline-fill text-offline border border-line"
            : "bg-green-fill text-green-ink border border-green/30 font-semibold",
          props.className,
        )}
      >
        <span aria-hidden="true">{isLocked ? "🔒" : "❄"}</span>
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
    let glyph = "✓";

    if (props.tone === "partial") {
      toneStyle = "bg-warning-fill text-warning border border-warning/30";
      glyph = "⚠";
    } else if (props.tone === "failed") {
      if (isFailedZero) {
        toneStyle = "bg-offline-fill text-offline border border-line";
        glyph = "•";
      } else {
        toneStyle = "bg-danger-fill text-danger border border-danger/30";
        glyph = "✕";
      }
    } else if (props.tone === "returned") {
      toneStyle = "bg-offline-fill text-offline border border-line";
      glyph = "↩";
    } else if (props.tone === "tripComplete" || props.tone === "complete") {
      toneStyle = "bg-success-fill text-success border border-success/30";
      glyph = "★";
    }

    return (
      <span className={cn(baseStyles, toneStyle, props.className)}>
        <span aria-hidden="true">{glyph}</span>
        <span>{props.label}</span>
      </span>
    );
  }

  if (props.kind === "sync") {
    const toneStyles: Record<string, string> = {
      online: "bg-success-fill text-success border border-success/30",
      offline: "bg-offline-fill text-offline border border-line",
      saving: "bg-warning-fill text-warning border border-warning/30",
      pending: "bg-offline-fill text-offline border border-line",
      syncing: "bg-offline-fill text-offline border border-line animate-pulse",
      success: "bg-success-fill text-success border border-success/30",
      failed: "bg-danger-fill text-danger border border-danger/30",
      inReview: "bg-warning-fill text-warning border border-warning/30",
      routeUpdated: "bg-warning-fill text-warning border border-warning/30",
      forwarded: "bg-offline-fill text-offline border border-line",
    };

    return (
      <span className={cn(baseStyles, toneStyles[props.tone] ?? toneStyles.offline, props.className)}>
        <span aria-hidden="true">●</span>
        <span>{props.label}</span>
      </span>
    );
  }

  return null;
}
