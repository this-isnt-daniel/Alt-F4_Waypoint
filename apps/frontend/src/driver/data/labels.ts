// Single home for driver-facing vocabulary. Components must NOT hardcode these words.
// Booklet order_units = "Number of items or cases"; the driver physically counts cases/crates,
// so "cases" is the honest plain word (OUT047's 25 cases == 8 dairy + 5 frozen + 12 dry).
export const UNIT_WORD = "cases";
export const UNIT_WORD_TITLE = "Cases";

// Real superscript glyph. NEVER write the six characters backslash-u-0-0-b-3 in a string.
export const VOLUME_UNIT = "m³";

// Load-confirmation row states (exception-first: nothing starts as "Matches").
export const LOAD_STATE = {
  unconfirmed: "To check",
  matches: "Matches",
  flagged: "Flagged",
} as const;
export type LoadState = keyof typeof LOAD_STATE;

// Reasons a *loaded* group can be wrong at the depot (distinct from handover reasons).
export const LOADING_REASONS = [
  "Short at loading",
  "Extra loaded",
  "Damaged in staging",
  "Wrong item",
  "Other",
] as const;
export type LoadingReason = (typeof LOADING_REASONS)[number];
