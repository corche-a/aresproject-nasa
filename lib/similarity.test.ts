import { describe, expect, it } from "vitest";
import { scoreRecord, weightsSum } from "./similarity";
import type { BasinRecord, Target } from "./types";
const record = { aridity_norm:.904, thermal_norm:.935, dust_norm:.494, slope_norm:0, mineral_profile:"Sulfates / Halite-Gypsum (Lit. Prior)" } as BasinRecord;
const target = { expected_mineral:"Sulfates", ideal:{aridity:.95,thermal:.88,dust:.8,slope:.35,mineral:1}, weights:{aridity:.25,thermal:.2,dust:.25,slope:.1,mineral:.2} } as Target;
describe("ARES similarity", () => { it("uses weighted Euclidean distance", () => expect(scoreRecord(record,target)).toBeCloseTo(.808185,5)); it("checks normalized weights", () => expect(weightsSum(target.weights)).toBe(1)); });
