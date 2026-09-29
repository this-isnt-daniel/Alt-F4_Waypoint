import { useTheme } from "./useTheme";
import { AppIcon } from "@/driver/components/AppIcon";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-raised transition-colors"
    >
      <AppIcon
        name={isDark ? "sun" : "moon"}
        size={16}
        className="text-slate-500"
      />
    </button>
  );
}
