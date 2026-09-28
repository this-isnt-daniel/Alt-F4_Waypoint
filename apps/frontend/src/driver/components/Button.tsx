import { type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cn";

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
    "inline-flex items-center justify-center font-semibold rounded-btn transition-colors focus-visible:outline-2 focus-visible:outline-green focus-visible:outline-offset-2 active:scale-[0.99]";

  const sizeStyles = {
    md: "min-h-[48px] px-4 text-sm",
    lg: "min-h-[56px] px-6 text-base",
  };

  const variantStyles = {
    primary: "bg-green text-green-ink hover:opacity-95 shadow-1",
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
        isLocked && "opacity-70 cursor-not-allowed active:scale-100",
        className,
      )}
      {...props}
    >
      {variant === "locked" && <span className="mr-2" aria-hidden="true">🔒</span>}
      {children}
    </button>
  );
}
