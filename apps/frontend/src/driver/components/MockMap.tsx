import { useTheme } from "@/theme/useTheme";
import { cn } from "@/lib/cn";
import { TRIP_1_STOPS } from "@/driver/data/driverContent";

export interface MockMapProps {
  currentStopSeq?: number;
  onPinClick?: (seq: number) => void;
  className?: string;
}

export function MockMap({
  currentStopSeq = 2,
  onPinClick,
  className,
}: MockMapProps) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  // Coordinates normalized inside 400x300 SVG viewbox
  const stopCoordinates: Record<number, { x: number; y: number }> = {
    1: { x: 70, y: 220 },  // Gampola
    2: { x: 160, y: 150 }, // Kandy Town
    3: { x: 190, y: 120 }, // Kandy Fort
    4: { x: 220, y: 140 }, // KCC
    5: { x: 270, y: 170 }, // Kandy East
    6: { x: 300, y: 100 }, // Kandy Hills
    7: { x: 130, y: 240 }, // Peradeniya
    8: { x: 340, y: 250 }, // Nawalapitiya
  };

  const polylinePoints = TRIP_1_STOPS.map(
    (stop) => `${stopCoordinates[stop.seq]?.x ?? 100},${stopCoordinates[stop.seq]?.y ?? 100}`,
  ).join(" ");

  return (
    <div
      className={cn(
        "relative w-full h-[280px] overflow-hidden rounded-card border border-line transition-colors",
        isDark ? "bg-[#0B1713]" : "bg-[#E5EFEA]",
        className,
      )}
      aria-label="Route Map"
      role="region"
    >
      <svg
        viewBox="0 0 400 300"
        className="w-full h-full"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Background Grid Roads */}
        <path
          d="M 20 50 Q 150 80 200 150 T 380 280 M 50 280 L 350 40 M 100 20 L 120 280"
          stroke={isDark ? "#172A22" : "#D4E2DA"}
          strokeWidth="6"
          fill="none"
        />

        {/* Route Polyline */}
        <polyline
          points={polylinePoints}
          stroke="#3FB27F"
          strokeWidth="4"
          strokeDasharray="6 4"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Stop Pins */}
        {TRIP_1_STOPS.map((stop) => {
          const coord = stopCoordinates[stop.seq] ?? { x: 100, y: 100 };
          const isNext = stop.seq === currentStopSeq;
          const isPassed = stop.seq < currentStopSeq;

          return (
            <g
              key={stop.seq}
              transform={`translate(${coord.x}, ${coord.y})`}
              onClick={() => onPinClick?.(stop.seq)}
              className="cursor-pointer group"
              tabIndex={0}
              role="button"
              aria-label={`Stop ${stop.seq}: ${stop.name}`}
            >
              {/* Outer Pulse for Next Stop */}
              {isNext && (
                <circle
                  r="18"
                  className="fill-green/20 animate-ping origin-center"
                />
              )}

              {/* Pin Base */}
              <circle
                r={isNext ? "14" : "10"}
                fill={
                  isNext
                    ? "#3FB27F"
                    : isPassed
                      ? isDark
                        ? "#1C332A"
                        : "#C0D6CB"
                      : isDark
                        ? "#101D19"
                        : "#FFFFFF"
                }
                stroke={isNext ? "#0E3A26" : "#3FB27F"}
                strokeWidth={isNext ? "3" : "2"}
              />

              {/* Pin Label Number */}
              <text
                textAnchor="middle"
                dy="4"
                fontSize={isNext ? "12" : "10"}
                fontWeight="bold"
                fill={isNext ? "#0E3A26" : isDark ? "#F3F7F5" : "#14201A"}
              >
                {stop.seq}
              </text>
            </g>
          );
        })}

        {/* Current Vehicle Indicator */}
        <g transform={`translate(${stopCoordinates[currentStopSeq]?.x! - 20}, ${stopCoordinates[currentStopSeq]?.y! + 10})`}>
          <rect
            x="0"
            y="0"
            width="28"
            height="14"
            rx="4"
            fill="#14532D"
            stroke="#86D3A6"
            strokeWidth="1.5"
          />
          <text x="14" y="10" textAnchor="middle" fontSize="8" fill="#FFFFFF" fontWeight="bold">
            VAN
          </text>
        </g>
      </svg>

      {/* Overlay Badge */}
      <div className="absolute top-3 left-3 bg-surface/90 backdrop-blur border border-line px-2.5 py-1 rounded-pill text-xs font-semibold text-ink shadow-1 flex items-center gap-1.5">
        <span className="h-2 w-2 rounded-circle bg-green animate-pulse" />
        <span>GPS Active · Kandy Route</span>
      </div>
    </div>
  );
}
