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
      <div className="space-y-4">
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
          {previewUrl ? (
            <img
              src={previewUrl}
              alt="Captured handover"
              className="h-56 w-full object-cover"
            />
          ) : (
            <div className="grid h-56 place-items-center text-slate-400">
              <ImageUp size={28} />
            </div>
          )}
        </div>
        <div className="flex items-center justify-between text-[14px]">
          <span
            className={cn(
              state === "upload-failed" ? "text-rose-600 font-medium" : "text-slate-500",
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
            className="text-green font-semibold hover:underline cursor-pointer"
            style={{ color: "var(--c-green)" }}
          >
            Retake
          </button>
        </div>
        {state === "upload-failed" ? (
          <button
            type="button"
            onClick={onRetry}
            className="flex w-full py-4 items-center justify-center gap-2 rounded-lg bg-rose-50 text-rose-600 font-bold border border-rose-200 transition-colors cursor-pointer"
          >
            <RefreshCw size={18} />
            Retry upload
          </button>
        ) : (
          <button
            type="button"
            onClick={onUse}
            className="w-full py-4 rounded-lg bg-green text-white font-bold text-[16px] transition-colors active:scale-[0.98] cursor-pointer"
            style={{ backgroundColor: "var(--c-green)" }}
          >
            Use photo
          </button>
        )}
      </div>
    );
  }

  // empty / capturing: drop zone is the trigger; NO skip primary
  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={onCapture}
        disabled={state === "capturing"}
        className="grid h-56 w-full place-items-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 text-slate-400 hover:border-green hover:text-slate-600 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="flex flex-col items-center gap-2">
          <Camera size={32} strokeWidth={1.5} />
          <span className="font-bold text-slate-900 text-[15px]">
            {state === "capturing" ? "Capturing…" : "Take photo"}
          </span>
        </span>
      </button>
      <p className="text-[13px] text-slate-500 leading-relaxed text-center px-4">
        Include the delivered crates and receiving area. Avoid faces or unrelated documents.
      </p>
      <div className="pt-2 text-center">
        <button
          type="button"
          onClick={onCannotCapture}
          className="text-[14px] font-medium text-slate-400 hover:text-slate-700 cursor-pointer"
        >
          Can’t take a photo?
        </button>
      </div>
    </div>
  );
}
