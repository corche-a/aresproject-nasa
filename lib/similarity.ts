import type { BasinRecord, MetricKey, ScoredRecord, Target } from "./types";

export const metricKeys: MetricKey[] = ["aridity", "thermal", "dust", "slope", "mineral", "latitude", "elevation", "platform", "weather"];
const addedWeights: Record<MetricKey, number> = { aridity: 0, thermal: 0, dust: 0, slope: 0, mineral: 0, latitude: 0.08, elevation: 0.04, platform: 0.1, weather: 0.08 };
const addedIdeal: Record<MetricKey, number> = { aridity: 0, thermal: 0, dust: 0, slope: 0, mineral: 0, latitude: 0.7, elevation: 0.5, platform: 1, weather: 0.85 };
function mineralMatch(profile: string, expected: string): number {
  return profile.toLowerCase().includes(expected.toLowerCase().replace(/s$/, "")) ? 1 : 0;
}
const clamp = (value: number) => Math.min(1, Math.max(0, value));
export function targetWeights(target: Target): Record<MetricKey, number> {
  const legacy = target.weights;
  const legacySum = ["aridity", "thermal", "dust", "slope", "mineral"].reduce((sum, key) => sum + (legacy[key as MetricKey] ?? 0), 0);
  const scale = legacySum ? 0.7 / legacySum : 0.7;
  return metricKeys.reduce((result, key) => {
    result[key] = key in addedWeights && addedWeights[key] ? addedWeights[key] : (legacy[key] ?? 0) * scale;
    return result;
  }, {} as Record<MetricKey, number>);
}
export function targetIdeal(target: Target, key: MetricKey): number {
  if (key === "latitude") return target.body === "Moon" ? 0.9 : 0.75;
  if (key === "elevation") return target.body === "Moon" ? 0.45 : 0.55;
  if (key === "platform") return 1;
  if (key === "weather") return target.body === "Moon" ? 0.9 : 0.82;
  return target.ideal[key] ?? addedIdeal[key];
}
export function scoreRecord(record: BasinRecord, target: Target, weights = target.weights): number {
  const values = featureValues(record, target);
  const effectiveWeights = Object.keys(weights).length > 5 ? weights as Record<MetricKey, number> : weights as Record<MetricKey, number>;
  const scoredKeys = Object.keys(effectiveWeights) as MetricKey[];
  const distance = Math.sqrt(scoredKeys.reduce((sum, key) => sum + effectiveWeights[key] * (values[key] - targetIdeal(target, key)) ** 2, 0));
  return Math.max(0, 1 - distance);
}
export function featureValues(record: BasinRecord, target: Target): Record<MetricKey, number> {
  return {
    aridity: record.aridity_norm, thermal: record.thermal_norm, dust: record.dust_norm,
    slope: record.slope_norm, mineral: mineralMatch(record.mineral_profile, target.expected_mineral),
    latitude: target.body === "Moon" ? clamp(1 - Math.abs(Math.abs(record.lat) - 85) / 85) : clamp(1 - Math.abs(record.lat) / 45),
    elevation: clamp(1 - record.elevation_m / 5000),
    platform: clamp(1 - record.slope_deg / 5),
    weather: clamp(1 - (0.45 * record.wind_ms / 15 + 0.3 * record.rh_pct / 100 + 0.25 * record.precip_mm / 250)),
  };
}
export function scoreBreakdown(record: BasinRecord, target: Target, weights = target.weights) {
  const values = featureValues(record, target);
  const effectiveWeights = Object.keys(weights).length > 5 ? weights as Record<MetricKey, number> : weights as Record<MetricKey, number>;
  const scoredKeys = Object.keys(effectiveWeights) as MetricKey[];
  return scoredKeys.map((key) => ({
    key, value: values[key], target: targetIdeal(target, key),
    contribution: effectiveWeights[key] * (values[key] - targetIdeal(target, key)) ** 2,
  }));
}
export function rankRecords(records: BasinRecord[], target: Target, weights = targetWeights(target)): ScoredRecord[] {
  return records.map((record) => ({ ...record, score: scoreRecord(record, target, weights), best_month: record.month_name }))
    .sort((a, b) => b.score - a.score);
}
export function weightsSum(weights: Record<MetricKey, number>): number { return metricKeys.reduce((sum, key) => sum + (weights[key] ?? 0), 0); }
