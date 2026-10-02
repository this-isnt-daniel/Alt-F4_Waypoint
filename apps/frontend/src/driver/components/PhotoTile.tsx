import { Camera, RefreshCw, ImageUp } from "lucide-react";
import { cn } from "@/lib/cn";

export type PhotoState =
  | "empty"
  | "capturing"
  | "captured"
  | "pending-upload"
  | "saved-offline"
  | "upload-failed";

export function PhotoTile({
  state,
  previewUrl,
  onCapture,
  onUse,
  onRetake,
  onRetry,
  onCannotCapture,
}: {
  state: PhotoState;
  previewUrl?: string;
  onCapture: () => void;
  onUse: () => void;
  onRetake: () => void;
  onRetry: () => void;
  onCannotCapture: () => void;
}) {
  if (
    state === "captured" ||
    state === "pending-upload" ||
    state === "saved-offline" ||
    state === "upload-failed"
  ) {
    return (
      <div className="space-y-3">
        <div className="overflow-hidden rounded-card border border-line bg-raised">
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Captured handover"
              className="h-56 w-full object-cover"
            />
          ) : (
            <div className="grid h-56 place-items-center text-ink-muted">
              <ImageUp size={28} />
            </div>
          )}
        </div>
        <div className="flex items-center justify-between text-sm">
          <span
            className={cn(
              state === "upload-failed" ? "text-danger font-medium" : "text-ink-muted",
            )}
          >
            {state === "captured" && "Photo captured"}
            {state === "pending-upload" && "Uploading…"}
            {state === "saved-offline" && "Saved offline"}
            {state === "upload-failed" && "Upload failed"}
          </span>
          <button
            type="button"
            onClick={onRetake}
            className="text-green font-medium hover:underline"
          >
            Retake
          </button>
        </div>
        {state === "upload-failed" ? (
          <button
            type="button"
            onClick={onRetry}
            className="flex w-full min-h-14 items-center justify-center gap-2 rounded-btn bg-danger-fill text-danger font-semibold border border-danger/30"
          >
            <RefreshCw size={18} />
            Retry upload
          </button>
        ) : (
          <button
            type="button"
            onClick={onUse}
            className="min-h-14 w-full rounded-btn bg-green font-semibold text-green-ink hover:opacity-95"
          >
            Use photo
          </button>
        )}
      </div>
    );
  }

  // empty / capturing: drop zone is the trigger; NO skip primary
  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={onCapture}
        disabled={state === "capturing"}
        className="grid h-56 w-full place-items-center rounded-card border-2 border-dashed border-line bg-raised text-ink-muted hover:border-green/40 transition-colors"
      >
        <span className="flex flex-col items-center gap-2">
          <Camera size={28} />
          <span className="font-semibold text-ink">
            {state === "capturing" ? "Capturing…" : "Take photo"}
          </span>
        </span>
      </button>
      <p className="text-sm text-ink-muted leading-relaxed">
        Include the delivered crates and receiving area. Avoid faces or unrelated documents.
      </p>
      <div className="pt-1">
        <button
          type="button"
          onClick={onCannotCapture}
          className="text-sm text-ink-muted underline-offset-4 hover:underline"
        >
          Can’t take a photo?
        </button>
      </div>
    </div>
  );
}
