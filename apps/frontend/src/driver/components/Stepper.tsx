import { cn } from "@/lib/cn";

export interface StepperProps {
  currentStep: number;
  totalSteps: number;
  label?: string;
  className?: string;
}

export function Stepper({
  currentStep,
  totalSteps,
  label,
  className,
}: StepperProps) {
  return (
    <div className={cn("mb-4", className)}>
      <div className="flex items-center justify-between text-xs font-bold text-ink-muted mb-2 tracking-wide uppercase">
        <span>
          Step {currentStep} of {totalSteps}
        </span>
        {label && <span>{label}</span>}
      </div>
      <div className="flex gap-1.5 h-1.5 w-full">
        {Array.from({ length: totalSteps }).map((_, index) => {
          const isActive = index + 1 <= currentStep;
          return (
            <div
              key={index}
              className={cn(
                "h-full flex-1 rounded-pill transition-colors",
                isActive ? "bg-green" : "bg-line",
              )}
            />
          );
        })}
      </div>
    </div>
  );
}
