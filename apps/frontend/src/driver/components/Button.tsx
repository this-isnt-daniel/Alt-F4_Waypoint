import { type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { AppIcon } from "./AppIcon";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "locked";
  size?: "md" | "lg";
  fullWidth?: boolean;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "lg",
  fullWidth = true,
  className,
  children,
  disabled,
  type = "button",
  ...props
}: ButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center font-semibold rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-green focus-visible:outline-offset-2";

  const sizeStyles = {
    md: "min-h-[48px] px-4 text-[13px]",
    lg: "min-h-[56px] px-6 text-[13px]",
  };

  const variantStyles = {
    primary: "bg-green text-white hover:opacity-95",
    secondary: "bg-raised text-ink border border-line hover:bg-surface",
    ghost: "bg-transparent text-green hover:bg-raised",
    danger: "bg-danger-fill text-danger border border-danger/20 hover:opacity-95",
    locked: "bg-raised text-ink-muted border border-line cursor-not-allowed opacity-80",
  };

  const isLocked = variant === "locked" || disabled;

  return (
    <button
      type={type}
      disabled={isLocked}
      className={cn(
        baseStyles,
        sizeStyles[size],
        variantStyles[variant],
        fullWidth && "w-full",
        isLocked && "opacity-70 cursor-not-allowed",
        className,
      )}
      {...props}
    >
      {variant === "locked" && (
        <AppIcon name="lock" size={14} className="mr-2 opacity-70" />
      )}
      {children}
    </button>
  );
}
