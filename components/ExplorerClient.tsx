"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import AresMap from "./AresMap";
import { rankRecords, weightsSum } from "../lib/similarity";
import { targetDescription } from "../lib/presentation";
import { GIBS_LAYERS, type GibsLayer } from "../lib/gibs";
import type { AnalogsData, MetricKey } from "../lib/types";

const metricKeys: MetricKey[] = ["aridity", "thermal", "dust", "slope", "mineral"];
const metricLabels: Record<MetricKey, string> = {
  aridity: "Aridity / dryness",
  thermal: "Thermal contrast",
  dust: "Dust / aeolian",
  slope: "Topography / slope",
  mineral: "Mineral affinity",
};

export default function ExplorerClient({ data }: { data: AnalogsData }) {
  const [targetId, setTargetId] = useState(data.targets[0].id);
  const [month, setMonth] = useState(1);
  const [layer, setLayer] = useState<GibsLayer>("blue_marble");
  const target = data.targets.find((item) => item.id === targetId) ?? data.targets[0];
  const [draftWeights, setDraftWeights] = useState<Record<MetricKey, number>>(target.weights);
  const [applied, setApplied] = useState({ targetId: target.id, month: 1, weights: target.weights });
  const appliedTarget = data.targets.find((item) => item.id === applied.targetId) ?? target;
  const ranked = useMemo(() => {
    const monthRows = data.records.filter((record) => record.month === applied.month);
    return rankRecords(monthRows, appliedTarget, applied.weights)
      .filter((record, index, all) => all.findIndex((item) => item.basin_id === record.basin_id) === index)
      .slice(0, 10);
  }, [applied, appliedTarget, data.records]);
  const sum = weightsSum(draftWeights);
  const updateTarget = (id: string) => {
    const next = data.targets.find((item) => item.id === id) ?? data.targets[0];
    setTargetId(next.id);
    setDraftWeights(next.weights);
  };
  const recompute = () => {
    if (Math.abs(sum - 1) > 0.001) return;
    setApplied({ targetId, month, weights: { ...draftWeights } });
  };

  return <div className="explorer">
    <aside className="card controls">
      <div className="label">Target selector</div>
      <select suppressHydrationWarning value={targetId} onChange={(event) => updateTarget(event.target.value)}>
        {data.targets.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
      </select>
      <p className="muted target-description">{targetDescription(target)}</p>
      <div className="label">NASA satellite layer</div>
      <select suppressHydrationWarning value={layer} onChange={(event) => setLayer(event.target.value as GibsLayer)}>
        {Object.entries(GIBS_LAYERS).map(([key, item]) => <option key={key} value={key}>{item.label}</option>)}
      </select>
      <p className="muted target-description">Source: NASA GIBS · {GIBS_LAYERS[layer].sensor}. Public imagery, no API key required.</p>
      <div className="label">Month</div>
      <select suppressHydrationWarning value={month} onChange={(event) => setMonth(Number(event.target.value))}>
        {Array.from({ length: 12 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1} · {data.records.find((record) => record.month === index + 1)?.month_name}</option>)}
      </select>
      <div className="label">Similarity weights</div>
      {metricKeys.map((key) => <label className="weight-control" key={key}><span>{metricLabels[key]} <b>{Math.round(draftWeights[key] * 100)}%</b></span><input suppressHydrationWarning aria-label={`${metricLabels[key]} weight`} type="range" min="0" max="100" value={Math.round(draftWeights[key] * 100)} onChange={(event) => setDraftWeights({ ...draftWeights, [key]: Number(event.target.value) / 100 })} /></label>)}
      <div className={Math.abs(sum - 1) <= 0.001 ? "weights-ok" : "weights-error"}>Total: {Math.round(sum * 100)}% {Math.abs(sum - 1) <= 0.001 ? "✓" : "— must equal 100%"}</div>
      <button suppressHydrationWarning className="button" onClick={recompute} disabled={Math.abs(sum - 1) > 0.001}>Recompute</button>
    </aside>
    <section className="map" aria-label={`NASA GIBS basin map using ${GIBS_LAYERS[layer].sensor}`}><AresMap records={ranked} layer={layer} /></section>
    <aside className="card">
      <div className="label">{data.records.find((record) => record.month === applied.month)?.month_name} ranking · {appliedTarget.name}</div>
      {ranked.map((record, index) => <Link className="rank" href={`/basin/${record.basin_id}`} key={record.basin_id}><span><b>{index + 1}.</b> {record.basin_name}<br /><small className="muted">{record.lat}, {record.lon}</small></span><span className="score">{(record.score * 100).toFixed(1)}%</span></Link>)}
      <div className="card" style={{ marginTop: 16 }}><div className="label">Ask ARES</div><p className="muted">AI-generated summaries from NASA data. Endpoint is optional; deterministic briefs remain available.</p><input suppressHydrationWarning placeholder="Ask about a basin or month" aria-label="Ask ARES question" /></div>
    </aside>
  </div>;
}
