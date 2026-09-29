import { describe, it, expect } from "vitest";
import { resolvePortal } from "@/lib/security";

describe("Portal resolution", () => {
  it("resolves valid portals", () => {
    expect(resolvePortal("?portal=driver")).toBe("driver");
    expect(resolvePortal("?portal=store-manager")).toBe("store-manager");
    expect(resolvePortal("?portal=dispatcher")).toBe("dispatcher");
    expect(resolvePortal("?portal=loader")).toBe("loader");
  });

  it("returns null for missing or invalid portals", () => {
    expect(resolvePortal("?portal=admin")).toBe(null);
    expect(resolvePortal("")).toBe(null);
    expect(resolvePortal("?portal=%3Cscript%3E")).toBe(null);
  });
});
