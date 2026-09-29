import { useTheme } from "./useTheme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const next = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={`Switch to ${next} mode`}
      title={`${next} mode`}
      className="grid h-11 w-11 place-items-center rounded-pill border border-line bg-surface text-ink-muted transition hover:text-ink"
    >
      <span aria-hidden="true">{theme === "dark" ? "☀" : "☾"}</span>
      <span className="sr-only">{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
