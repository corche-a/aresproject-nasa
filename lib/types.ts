export type MetricKey = "aridity" | "thermal" | "dust" | "slope" | "mineral" | "latitude" | "elevation" | "platform" | "weather";
export type RecordValue = number | string;
export interface BasinRecord {
  basin_id: string; basin_name: string; lat: number; lon: number; month: number; month_name: string;
  elevation_m: number; slope_deg: number; temp_max_c: number; temp_min_c: number;
  diurnal_temp_range_c: number; precip_mm: number; wind_ms: number; rh_pct: number;
  solar_kwh_m2_day: number; aridity_norm: number; thermal_norm: number; dust_norm: number;
  slope_norm: number; mineral_profile: string;
}
export interface Target {
  id: string; name: string; body: "Mars" | "Moon"; description: string; expected_mineral: string;
  ideal: Record<MetricKey, number>; weights: Record<MetricKey, number>;
}
export interface AnalogsData { metadata: { basins_count: number; total_windows: number; emit_integrated: boolean }; targets: Target[]; records: BasinRecord[]; }
export interface ScoredRecord extends BasinRecord { score: number; best_month: string; }
