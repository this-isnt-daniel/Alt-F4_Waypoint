import { useRef, useState, type ChangeEvent } from "react";
import { Button } from "./Button";
import { cn } from "@/lib/cn";

export interface PhotoTileProps {
  onPhotoCaptured?: (photoUrl: string) => void;
  savedOfflineNote?: boolean;
  className?: string;
}

export function PhotoTile({
  onPhotoCaptured,
  savedOfflineNote = false,
  className,
}: PhotoTileProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      if (onPhotoCaptured) {
        onPhotoCaptured(url);
      }
    }
  };

  const triggerCamera = () => {
    fileInputRef.current?.click();
  };

  const clearPhoto = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className={cn("space-y-3", className)}>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        className="hidden"
        aria-label="Capture delivery photo"
      />

      {previewUrl ? (
        <div className="relative rounded-card overflow-hidden border border-line bg-surface">
          <img
            src={previewUrl}
            alt="Delivery handover evidence"
            className="w-full h-56 object-cover"
          />
          <div className="absolute bottom-2 right-2 flex gap-2">
            <Button
              variant="secondary"
              size="md"
              fullWidth={false}
              onClick={clearPhoto}
            >
              Retake photo
            </Button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={triggerCamera}
          className="w-full h-48 border-2 border-dashed border-line rounded-card bg-raised hover:bg-surface flex flex-col items-center justify-center gap-2 transition-colors group p-4"
        >
          <div className="grid h-12 w-12 place-items-center rounded-circle bg-surface border border-line text-green group-hover:scale-105 transition-transform">
            📷
          </div>
          <span className="text-sm font-semibold text-ink">Tap to take photo</span>
          <span className="text-xs text-ink-muted">Uses camera or photo library</span>
        </button>
      )}

      <p className="text-xs text-ink-muted leading-relaxed">
        Include the delivered crates and receiving area. Avoid faces or unrelated documents.
      </p>

      {savedOfflineNote && (
        <div className="p-2.5 bg-offline-fill text-offline rounded-btn text-xs font-medium flex items-center gap-2">
          <span>ℹ</span>
          <span>Photo can be saved offline and uploads automatically when connected.</span>
        </div>
      )}
    </div>
  );
}
