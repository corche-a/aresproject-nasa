"use client";

import Link from "next/link";
import { useMemo, useState, type FormEvent } from "react";
import AresMap from "./AresMap";
import { metricKeys, rankRecords, targetWeights, weightsSum } from "../lib/similarity";
import { targetDescription } from "../lib/presentation";
import { GIBS_LAYERS, type GibsLayer } from "../lib/gibs";
import type { AnalogsData, MetricKey } from "../lib/types";

const metricLabels: Record<MetricKey, string> = {
  aridity: "Aridity / dryness",
  thermal: "Thermal contrast",
  dust: "Dust / aeolian",
  slope: "Topography / slope",
  mineral: "Mineral affinity",
  latitude: "Latitude / orbital geometry",
  elevation: "Elevation / datum",
  platform: "Platform stability",
  weather: "Weather window",
};
const metricGroups = [
  { title: "A · Analog fidelity", keys: ["slope", "mineral", "thermal", "aridity", "dust"] as MetricKey[] },
  { title: "B · Base and launch operations", keys: ["latitude", "elevation", "platform", "weather"] as MetricKey[] },
];
interface AskResponse {
  answer: string;
  fallback?: boolean;
  label: string;
  model?: string;
}

export default function ExplorerClient({ data }: { data: AnalogsData }) {
  const [targetId, setTargetId] = useState(data.targets[0].id);
  const [month, setMonth] = useState(1);
  const [layer, setLayer] = useState<GibsLayer>("blue_marble");
  const [selectedBasinId, setSelectedBasinId] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [question, setQuestion] = useState("");
  const [aiResponse, setAiResponse] = useState<AskResponse | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const target = data.targets.find((item) => item.id === targetId) ?? data.targets[0];
  const [draftWeights, setDraftWeights] = useState<Record<MetricKey, number>>(targetWeights(target));
  const [applied, setApplied] = useState({ targetId: target.id, month: 1, weights: targetWeights(target) });
  const appliedTarget = data.targets.find((item) => item.id === applied.targetId) ?? target;
  const ranked = useMemo(() => {
    const monthRows = data.records.filter((record) => record.month === applied.month);
    return rankRecords(monthRows, appliedTarget, applied.weights)
      .filter((record) => record.score >= 0.6)
      .filter((record, index, all) => all.findIndex((item) => item.basin_id === record.basin_id) === index);
  }, [applied, appliedTarget, data.records]);
  const visibleRanked = showAll ? ranked : ranked.slice(0, 10);
  const sum = weightsSum(draftWeights);
  const updateTarget = (id: string) => {
    const next = data.targets.find((item) => item.id === id) ?? data.targets[0];
    setTargetId(next.id);
    setDraftWeights(targetWeights(next));
  };
  const recompute = () => {
    if (Math.abs(sum - 1) > 0.001) return;
    setApplied({ targetId, month, weights: { ...draftWeights } });
    setSelectedBasinId(null);
    setShowAll(false);
  };
  const askQuestion = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isAsking) return;
    setIsAsking(true);
    setAiResponse(null);
    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          question: trimmedQuestion,
          context: { month: applied.month, target: appliedTarget.name, weights: applied.weights },
        }),
      });
      const result = await response.json() as AskResponse;
      if (!response.ok) throw new Error(result.answer || "ARES could not answer the question.");
      setAiResponse(result);
    } catch (error) {
      setAiResponse({ answer: error instanceof Error ? error.message : "ARES could not answer the question.", label: "Request error" });
    } finally {
      setIsAsking(false);
    }
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
        {Array.from({ length: 12 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1} · {data.records.find((record) => record.month === index + 1)?.month_name} climatology</option>)}
      </select>
      <p className="muted target-description">NASA POWER long-term climatology, not a forecast for the next calendar year.</p>
      <div className="label">Similarity weights</div>
      <p className="muted target-description">NASA-derived and transparent proxy signals. Missing resources data is not scored.</p>
      {metricGroups.map((group) => <section className="weight-group" key={group.title}><div className="weight-group-title">{group.title}</div>{group.keys.map((key) => <label className="weight-control" key={key}><span>{metricLabels[key]} <b>{Math.round(draftWeights[key] * 100)}%</b></span><input suppressHydrationWarning aria-label={`${metricLabels[key]} weight`} type="range" min="0" max="100" value={Math.round(draftWeights[key] * 100)} onChange={(event) => setDraftWeights({ ...draftWeights, [key]: Number(event.target.value) / 100 })} /></label>)}</section>)}
      <div className={Math.abs(sum - 1) <= 0.001 ? "weights-ok" : "weights-error"}>Total: {Math.round(sum * 100)}% {Math.abs(sum - 1) <= 0.001 ? "✓" : "— must equal 100%"}</div>
      <button suppressHydrationWarning className="button" onClick={recompute} disabled={Math.abs(sum - 1) > 0.001}>Recompute</button>
    </aside>
    <section className="map" aria-label={`NASA GIBS basin map using ${GIBS_LAYERS[layer].sensor}`}><AresMap records={ranked} layer={layer} selectedBasinId={selectedBasinId} onSelect={setSelectedBasinId} /></section>
    <aside className="card">
      <div className="ranking-heading"><div className="label">Select a location</div><span className="ranking-context">{data.records.find((record) => record.month === applied.month)?.month_name} climatology · {appliedTarget.name} · {ranked.length} locations above 60%</span></div>
      {visibleRanked.map((record, index) => <div aria-pressed={record.basin_id === selectedBasinId} className={`rank rank-button ${record.basin_id === selectedBasinId ? "rank-selected" : ""}`} onClick={() => setSelectedBasinId(record.basin_id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") setSelectedBasinId(record.basin_id); }} role="button" tabIndex={0} key={record.basin_id}><div className="rank-main"><span><b>{index + 1}.</b> {record.basin_name}<br /><small className="muted">{record.lat}, {record.lon}</small></span>{record.basin_id === selectedBasinId && <Link className="rank-details-button" href={`/basin/${record.basin_id}`} onClick={(event) => event.stopPropagation()}>View all information <span aria-hidden="true">→</span></Link>}</div><span className="score">{(record.score * 100).toFixed(1)}%</span></div>)}
      {ranked.length > 10 && <button className="show-more-button" onClick={() => setShowAll((current) => !current)}>{showAll ? "Show less" : `Show more (${ranked.length - 10} more)`}</button>}
      <div className="card" style={{ marginTop: 16 }}><div className="label">Ask ARES</div><p className="muted">Google AI Studio is optional. Add <code>GOOGLE_AI_API_KEY</code> to enable Gemini answers; local fallback remains available.</p><form onSubmit={askQuestion}><input suppressHydrationWarning value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about a basin or month" aria-label="Ask ARES question" maxLength={500} /><button className="button" type="submit" disabled={isAsking || question.trim().length === 0}>{isAsking ? "Asking…" : "Ask"}</button></form>{aiResponse && <div className="muted" role="status" style={{ marginTop: 12 }}><strong>{aiResponse.label}</strong><p>{aiResponse.answer}</p></div>}</div>
    </aside>
  </div>;
}
