import { useState, type ReactNode } from "react";
import { cn } from "@/lib/cn";
import { sanitizeText } from "@/lib/security";

export interface ChoiceOption {
  id: string;
  label: string;
  description?: string;
  icon?: ReactNode;
}

export interface ChoiceListProps {
  options: ChoiceOption[];
  selectedId: string | null;
  onSelect: (id: string, note?: string) => void;
  allowOtherNote?: boolean;
  otherPlaceholder?: string;
  className?: string;
}

export function ChoiceList({
  options,
  selectedId,
  onSelect,
  allowOtherNote = true,
  otherPlaceholder = "Add a short detail only if needed...",
  className,
}: ChoiceListProps) {
  const [note, setNote] = useState<string>("");

  const handleSelect = (id: string) => {
    onSelect(id, id === "Other" || id === "other" ? note : undefined);
  };

  const handleNoteChange = (val: string) => {
    const clean = sanitizeText(val);
    setNote(clean);
    if (selectedId === "Other" || selectedId === "other") {
      onSelect(selectedId, clean);
    }
  };

  const isOtherSelected = selectedId === "Other" || selectedId === "other";

  return (
    <div className={cn("space-y-2.5", className)} role="radiogroup">
      {options.map((option) => {
        const isSelected = selectedId === option.id;

        return (
          <div key={option.id} className="w-full">
            <button
              type="button"
              role="radio"
              aria-checked={isSelected}
              onClick={() => handleSelect(option.id)}
              className={cn(
                "w-full text-left p-4 rounded-btn border text-base font-medium transition-all flex items-center justify-between min-h-[56px]",
                isSelected
                  ? "border-green bg-green-fill text-ink ring-1 ring-green"
                  : "border-line bg-surface text-ink hover:bg-raised",
              )}
            >
              <div className="flex items-center gap-3">
                {option.icon && <span aria-hidden="true">{option.icon}</span>}
                <div>
                  <div className="font-semibold text-ink">{option.label}</div>
                  {option.description && (
                    <div className="text-xs text-ink-muted mt-0.5">{option.description}</div>
                  )}
                </div>
              </div>
              <div
                className={cn(
                  "grid h-6 w-6 place-items-center rounded-circle border transition-colors",
                  isSelected
                    ? "border-green bg-green text-green-ink"
                    : "border-line bg-surface",
                )}
                aria-hidden="true"
              >
                {isSelected && <span className="text-xs font-bold">✓</span>}
              </div>
            </button>
          </div>
        );
      })}

      {allowOtherNote && isOtherSelected && (
        <div className="mt-3 p-3 bg-raised rounded-btn border border-line">
          <label htmlFor="choice-other-note" className="block text-xs font-semibold text-ink-muted mb-1.5">
            Additional detail
          </label>
          <textarea
            id="choice-other-note"
            rows={3}
            value={note}
            onChange={(e) => handleNoteChange(e.target.value)}
            placeholder={otherPlaceholder}
            className="w-full p-2.5 bg-surface border border-line rounded-btn text-sm text-ink focus:outline-2 focus:outline-green"
          />
        </div>
      )}
    </div>
  );
}
