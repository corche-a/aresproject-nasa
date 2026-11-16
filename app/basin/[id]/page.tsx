import { getBasin, getData } from "../../../lib/data";
import { limits } from "../../../lib/limits";
import { rankRecords, scoreBreakdown } from "../../../lib/similarity";
import Link from "next/link";
import { targetDescription } from "../../../lib/presentation";

const metricLabels = {
  aridity: "Aridity / dryness",
  thermal: "Thermal contrast",
  dust: "Dust / aeolian activity",
  slope: "Topography / slope",
  mineral: "Mineral affinity",
} as const;

function badge(label: "Measured" | "Derived" | "Reference") {
  return <span className={`data-badge ${label.toLowerCase()}`}>{label}</span>;
}

export async function generateStaticParams() {
  const data = await getData();
  return [...new Set(data.records.map((record) => record.basin_id))].map((id) => ({ id }));
}

export default async function Basin({ params }: { params: Promise<{ id: string }> }) {
  const data = await getData();
  const rows = await getBasin((await params).id);
  if (!rows.length) return <main className="shell"><h1>Basin not found</h1></main>;

  const candidates = data.targets.flatMap((target) =>
    rankRecords(rows, target).map((record) => ({ record, target })),
  ).sort((a, b) => b.record.score - a.record.score);
  const best = candidates[0];
  const breakdown = scoreBreakdown(best.record, best.target);
  const closeMetrics = breakdown.filter((item) => Math.abs(item.value - item.target) <= 0.15);
  const gapMetrics = breakdown.filter((item) => Math.abs(item.value - item.target) > 0.15);
  const parameters = [
    ["Latitude", `${best.record.lat.toFixed(4)}°`, "Basin coordinates / pipeline", "Measured"],
    ["Longitude", `${best.record.lon.toFixed(4)}°`, "Basin coordinates / pipeline", "Measured"],
    ["Elevation", `${best.record.elevation_m.toFixed(1)} m`, "Copernicus DEM", "Measured"],
    ["Slope", `${best.record.slope_deg.toFixed(2)}°`, "Copernicus DEM", "Measured"],
    ["Maximum temperature", `${best.record.temp_max_c.toFixed(2)} °C`, "NASA POWER", "Measured"],
    ["Minimum temperature", `${best.record.temp_min_c.toFixed(2)} °C`, "NASA POWER", "Measured"],
    ["Day-night temperature range", `${best.record.diurnal_temp_range_c.toFixed(2)} °C`, "NASA POWER", "Measured"],
    ["Precipitation", `${best.record.precip_mm.toFixed(2)} mm/month`, "NASA POWER PRECTOTCORR", "Measured"],
    ["Relative humidity", `${best.record.rh_pct.toFixed(2)} %`, "NASA POWER RH2M", "Measured"],
    ["Wind", `${best.record.wind_ms.toFixed(2)} m/s`, "NASA POWER WS10M", "Measured"],
    ["Solar radiation", `${best.record.solar_kwh_m2_day.toFixed(2)} kWh/m²/day`, "NASA POWER", "Measured"],
    ["Aridity index", best.record.aridity_norm.toFixed(3), "Derived from precipitation", "Derived"],
    ["Thermal index", best.record.thermal_norm.toFixed(3), "Derived from ΔT", "Derived"],
    ["Dust activity index", best.record.dust_norm.toFixed(3), "Derived from wind, aridity and humidity", "Derived"],
    ["Mineral profile", best.record.mineral_profile, "Literature prior", "Reference"],
  ] as const;

  return <main className="shell">
    <section className="hero">
      <Link href="/explorer" className="eyebrow">← Back to Explorer</Link>
      <h1>{best.record.basin_name}</h1>
      <p>{best.record.lat}, {best.record.lon} · Best stored window: {best.record.month_name} · Compared with {best.target.name}</p>
      <div className="verdict">
        <div className="verdict-label">Primary planetary analogue</div>
        <div className="verdict-target">{best.target.body === "Moon" ? "Moon analogue" : "Mars analogue"}</div>
        <div className="verdict-detail">{best.target.name} · {(best.record.score * 100).toFixed(1)}% similarity · {best.record.month_name} window</div>
      </div>
    </section>

    <section className="card analogy-card">
      <div className="label">Plain-language explanation</div>
      <h2>{best.target.name}</h2>
      <p>{targetDescription(best.target)}</p>
      <p><strong>Why it matches:</strong> this location is close in <strong>{closeMetrics.map((item) => metricLabels[item.key]).join(", ") || "the weighted combination of available indicators"}</strong>.</p>
      <p><strong>What does not match:</strong> the main differences are <strong>{gapMetrics.map((item) => metricLabels[item.key]).join(", ") || "within the configured tolerance"}</strong>.</p>
      <p className="muted">This is a specialized Earth analogue for the selected process, not a complete copy of {best.target.body}. Gravity, atmosphere, radiation and other planetary conditions remain different.</p>
    </section>

    <section className="card" style={{ marginTop: 16 }}>
      <div className="label">Location data</div>
      <div className="location-summary">
        <div><span className="summary-label">Coordinates</span><strong>{best.record.lat.toFixed(4)}°, {best.record.lon.toFixed(4)}°</strong></div>
        <div><span className="summary-label">Best month</span><strong>{best.record.month_name}</strong></div>
        <div><span className="summary-label">Elevation</span><strong>{best.record.elevation_m.toFixed(1)} m</strong></div>
        <div><span className="summary-label">Analogue target</span><strong>{best.target.body}</strong></div>
      </div>
      <div className="label" style={{ marginTop: 24 }}>Measured and derived parameters</div>
      <div className="parameter-grid">{parameters.map(([name, value, source, status]) =>
        <article className="parameter-card" key={name}><div className="parameter-name">{name}</div><div className="parameter-value">{value}</div><div className="parameter-source">{source}</div>{badge(status)}</article>,
      )}</div>
    </section>

    <section className="card" style={{ marginTop: 16 }}>
      <div className="label">Visual comparison</div>
      <p className="muted">Each bar is normalized from 0 to 100. Earth is the measured or derived basin value; target is the engine reference signature.</p>
      <div className="comparison-chart">{breakdown.map((item) => <div className="comparison-row" key={item.key}>
        <div className="comparison-title"><span>{metricLabels[item.key]}</span><span>{Math.round(item.value * 100)}% Earth / {Math.round(item.target * 100)}% target</span></div>
        <div className="bar-track"><div className="bar earth-bar" style={{ width: `${Math.min(100, Math.max(0, item.value * 100))}%` }} /></div>
        <div className="bar-track"><div className="bar target-bar" style={{ width: `${Math.min(100, Math.max(0, item.target * 100))}%` }} /></div>
      </div>)}</div>
      <div className="chart-legend"><span><i className="legend-earth" /> Earth location</span><span><i className="legend-target" /> {best.target.body} reference</span></div>
      <div className="label" style={{ marginTop: 24 }}>Detailed comparison</div>
      <table className="table"><thead><tr><th>Dimension</th><th>Earth value</th><th>Target signature</th><th>Weight</th><th>Interpretation</th></tr></thead><tbody>
        {breakdown.map((item) => <tr key={item.key}><td>{metricLabels[item.key]}</td><td>{item.value.toFixed(3)}</td><td>{item.target.toFixed(3)} {badge("Reference")}</td><td>{(best.target.weights[item.key] * 100).toFixed(0)}%</td><td className="muted">{Math.abs(item.value - item.target) <= 0.15 ? "Close match" : "Important difference"}</td></tr>)}
      </tbody></table>
      <p className="muted">Target signatures are reference values defined in the engine, not direct measurements of Mars or the Moon. The current dataset has no EMIT scenes, aerosol product, water time series, ice, caves, biology or radiation measurements.</p>
    </section>

    <section className="card" style={{ marginTop: 16 }}>
      <h2>Where the analogy breaks</h2>
      <table className="table"><tbody>{limits.map((limit) => <tr key={limit.name}><td>{limit.name}</td><td>{limit.earth}</td><td>{limit.mars}</td><td>{limit.source}</td></tr>)}</tbody></table>
    </section>
  </main>;
}
