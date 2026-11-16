"use client";

import { useEffect, useState } from "react";
import type { BasinRecord } from "../lib/types";

interface Coverage { available: boolean; source: string; period?: string; cloudAttenuationPct?: number; allSkySolar?: number; clearSkySolar?: number; }
export default function NasaCoverage({ record }: { record: BasinRecord }) {
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  useEffect(() => {
    fetch(`/api/nasa-coverage?lat=${record.lat}&lon=${record.lon}&month=${record.month}`)
      .then((response) => response.ok ? response.json() as Promise<Coverage> : Promise.reject(new Error("NASA POWER coverage failed")))
      .then(setCoverage)
      .catch((error) => { console.error(error); setCoverage({ available: false, source: "NASA POWER" }); });
  }, [record.lat, record.lon, record.month]);
  return <div className="nasa-coverage"><div className="label">Live NASA POWER coverage</div>{coverage?.available ? <><div className="coverage-value">{coverage.cloudAttenuationPct}% <span>cloud attenuation proxy</span></div><p className="muted">{coverage.period} · All-sky {coverage.allSkySolar?.toFixed(2)} vs clear-sky {coverage.clearSkySolar?.toFixed(2)} kWh/m²/day.</p></> : <p className="muted">{coverage ? "NASA POWER coverage is unavailable for this window." : "Loading NASA POWER coverage..."}</p>}<small className="muted">Derived from NASA POWER all-sky and clear-sky surface solar radiation.</small></div>;
}
