import { useState } from "react";
import { useNavigator } from "@/router/navigator";
import { PhotoTile, type PhotoState } from "@/driver/components/PhotoTile";

export function PodPhotoScreen() {
  const { push, route } = useNavigator();

  // Allow seeding photoState via query param (e.g. &photoState=captured)
  const initialPhotoState =
    (route.params.photoState as PhotoState) || "empty";

  const [state, setState] = useState<PhotoState>(initialPhotoState);
  const [previewUrl, setPreviewUrl] = useState<string | undefined>(
    initialPhotoState !== "empty"
      ? "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'><rect width='400' height='300' fill='%23e2e8f0'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%2364748b' font-family='sans-serif' font-size='16'>Delivery Crates Staged</text></svg>"
      : undefined,
  );

  const handleCapture = () => {
    setState("capturing");
    setTimeout(() => {
      setPreviewUrl(
        "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='300' viewBox='0 0 400 300'><rect width='400' height='300' fill='%23e2e8f0'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%2364748b' font-family='sans-serif' font-size='16'>Delivery Crates Staged</text></svg>",
      );
      setState("captured");
    }, 600);
  };

  const handleUse = () => {
    push("pod-pin");
  };

  const handleRetake = () => {
    setPreviewUrl(undefined);
    setState("empty");
  };

  const handleRetry = () => {
    setState("pending-upload");
    setTimeout(() => {
      setState("captured");
    }, 800);
  };

  const handleCannotCapture = () => {
    push("camera-denied");
  };

  return (
    <div className="p-4 space-y-4 max-w-[430px] mx-auto pb-8">
      {/* Stepper with single source of truth */}
      <div className="flex items-center justify-between border-b border-line pb-2">
        <span className="text-[12px] font-semibold text-slate-500">
          Step 1 of 2
        </span>
        <span className="text-[12px] font-bold text-slate-900">Photo</span>
      </div>

      <div>
        <h1 className="text-lg font-bold text-slate-900">
          Photograph the handover
        </h1>
      </div>

      <PhotoTile
        state={state}
        previewUrl={previewUrl}
        onCapture={handleCapture}
        onUse={handleUse}
        onRetake={handleRetake}
        onRetry={handleRetry}
        onCannotCapture={handleCannotCapture}
      />
    </div>
  );
}
