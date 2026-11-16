import type { BasinRecord, MetricKey, ScoredRecord, Target } from "./types";

const keys: MetricKey[] = ["aridity", "thermal", "dust", "slope", "mineral"];
function mineralMatch(profile: string, expected: string): number {
  return profile.toLowerCase().includes(expected.toLowerCase().replace(/s$/, "")) ? 1 : 0;
}
export function scoreRecord(record: BasinRecord, target: Target, weights = target.weights): number {
  const values = featureValues(record, target);
  const distance = Math.sqrt(keys.reduce((sum, key) => sum + weights[key] * (values[key] - target.ideal[key]) ** 2, 0));
  return Math.max(0, 1 - distance);
}
export function featureValues(record: BasinRecord, target: Target): Record<MetricKey, number> {
  return {
    aridity: record.aridity_norm, thermal: record.thermal_norm, dust: record.dust_norm,
    slope: record.slope_norm, mineral: mineralMatch(record.mineral_profile, target.expected_mineral),
  };
}
export function scoreBreakdown(record: BasinRecord, target: Target, weights = target.weights) {
  const values = featureValues(record, target);
  return keys.map((key) => ({
    key, value: values[key], target: target.ideal[key],
    contribution: weights[key] * (values[key] - target.ideal[key]) ** 2,
  }));
}
export function rankRecords(records: BasinRecord[], target: Target, weights = target.weights): ScoredRecord[] {
  return records.map((record) => ({ ...record, score: scoreRecord(record, target, weights), best_month: record.month_name }))
    .sort((a, b) => b.score - a.score);
}
export function weightsSum(weights: Record<MetricKey, number>): number { return keys.reduce((sum, key) => sum + weights[key], 0); }
