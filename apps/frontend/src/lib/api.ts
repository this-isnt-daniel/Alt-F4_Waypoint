import { safeStorage } from "./security";

const API_BASE = import.meta.env.VITE_API_URL || "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = safeStorage.get("token");
  
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "An error occurred";
    try {
      const data = await response.json();
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((d: any) => d.msg || (typeof d === 'string' ? d : JSON.stringify(d))).join(", ");
      } else if (data.detail && typeof data.detail === "object") {
        message = data.detail.message || JSON.stringify(data.detail);
      } else if (data.message) {
        message = typeof data.message === "string" ? data.message : JSON.stringify(data.message);
      }
    } catch {
      // Ignored
    }
    throw new ApiError(response.status, message);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as any;
  }

  return response.json();
}
