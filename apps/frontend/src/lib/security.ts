const PORTAL_ALLOWLIST = ["store-manager", "dispatcher", "loader", "driver"] as const;
export type Portal = (typeof PORTAL_ALLOWLIST)[number];

export function resolvePortal(search: string): Portal | null {
  const raw = new URLSearchParams(search).get("portal");
  if (!raw) return null;
  return (PORTAL_ALLOWLIST as readonly string[]).includes(raw) ? (raw as Portal) : null;
}

export function sanitizeText(input: string): string {
  return input.replace(/[\u0000-\u001F\u007F<>]/g, "").slice(0, 2000);
}

export function maskPin(pin: string): string {
  return "•".repeat(Math.max(0, Math.min(4, pin.length)));
}

export function isSafeExternalHref(href: string): boolean {
  try {
    if (href.startsWith("tel:")) return true;
    const origin = typeof window !== "undefined" && window.location ? window.location.origin : "http://localhost:5173";
    const url = new URL(href, origin);
    return url.protocol === "tel:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

const NAMESPACE = "waypoint.driver.";

export const safeStorage = {
  get(key: string): string | null {
    try {
      return localStorage.getItem(NAMESPACE + key);
    } catch {
      return null;
    }
  },
  set(key: string, value: string): void {
    try {
      localStorage.setItem(NAMESPACE + key, value);
    } catch {
      // Private mode or storage disabled. Theme/state degrade gracefully.
    }
  },
  remove(key: string): void {
    try {
      localStorage.removeItem(NAMESPACE + key);
    } catch {
      // Ignore.
    }
  },
};
