import { describe, it, expect } from "vitest";
import {
  sanitizeText,
  maskPin,
  isSafeExternalHref,
} from "@/lib/security";

describe("Security utilities", () => {
  it("sanitizes text input", () => {
    expect(sanitizeText("Hello <script>alert(1)</script>")).toBe("Hello scriptalert(1)/script");
  });

  it("masks PIN properly", () => {
    expect(maskPin("1234")).toBe("••••");
    expect(maskPin("12")).toBe("••");
  });

  it("validates external hrefs strictly", () => {
    expect(isSafeExternalHref("tel:+94771234567")).toBe(true);
    expect(isSafeExternalHref("https://example.com")).toBe(true);
    expect(isSafeExternalHref("javascript:alert(1)")).toBe(false);
    expect(isSafeExternalHref("data:text/html")).toBe(false);
  });
});
