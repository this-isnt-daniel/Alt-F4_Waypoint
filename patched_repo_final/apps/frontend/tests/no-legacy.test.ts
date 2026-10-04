import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import * as driverData from "@/driver/data/driverContent";

const FORBIDDEN_LEGACY_STRINGS = [
  "Peliyagoda",
  "Tech Kandy",
  "Colombo Mall",
  "Nugegoda",
  "yoghurt",
  "1,189",
  "1189",
  "4 items handed over",
  "Removed OUT",
  "Added next OUT",
  "7 Stops",
  "Skip photo",
  "Manifest Reconcile",
  "Photo Evidence",
];

const EMOJI_REGEX = /\p{Extended_Pictographic}/u;

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((entry: string) => {
    const full = path.join(dir, entry);
    return statSync(full).isDirectory() ? walk(full) : [full];
  });
}

describe("Legacy String Purge & Emoji Checks", () => {
  it("does not contain any forbidden legacy strings in canonical driver data", () => {
    const dataString = JSON.stringify(driverData);
    for (const forbidden of FORBIDDEN_LEGACY_STRINGS) {
      expect(dataString).not.toContain(forbidden);
    }
  });

  it("does not contain forbidden legacy strings in src/driver screens or components", () => {
    const driverDir = path.resolve(process.cwd(), "src/driver");
    const files = walk(driverDir).filter((file) => /\.(ts|tsx)$/.test(file));

    const violations: { file: string; match: string }[] = [];

    for (const file of files) {
      const content = readFileSync(file, "utf8");
      for (const forbidden of FORBIDDEN_LEGACY_STRINGS) {
        if (content.includes(forbidden)) {
          violations.push({ file: path.basename(file), match: forbidden });
        }
      }
    }

    expect(violations).toEqual([]);
  });

  it("does not contain emoji / pictographic characters in src/driver/ UI code", () => {
    const driverDir = path.resolve(process.cwd(), "src/driver");
    const files = walk(driverDir).filter((file) => /\.(ts|tsx)$/.test(file));

    const offenders: string[] = [];

    for (const file of files) {
      const content = readFileSync(file, "utf8");
      if (EMOJI_REGEX.test(content)) {
        offenders.push(path.basename(file));
      }
    }

    expect(offenders).toEqual([]);
  });
});
