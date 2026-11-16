"use client";

import { useEffect, useState } from "react";
import type { BasinRecord } from "../lib/types";
import LocationMap from "./LocationMap";
import NasaCoverage from "./NasaCoverage";

interface LocationResponse { country: string; countryEnglish: string; address: string; photos: string[]; }
export default function LocationDetails({ record }: { record: BasinRecord }) {
  const [details, setDetails] = useState<LocationResponse | null>(null);
  useEffect(() => {
    fetch(`/api/location?lat=${record.lat}&lon=${record.lon}&name=${encodeURIComponent(record.basin_name)}`)
      .then((response) => response.ok ? response.json() as Promise<LocationResponse> : Promise.reject(new Error("Location lookup failed")))
      .then(setDetails)
      .catch((error) => { console.error(error); setDetails({ country: "Country unavailable", countryEnglish: "Country unavailable", address: "Address unavailable", photos: [] }); });
  }, [record.basin_name, record.lat, record.lon]);
  const countryLabel = details && details.country !== details.countryEnglish ? `${details.country} / ${details.countryEnglish}` : details?.countryEnglish;
  return <section className="location-details card">
    <div><div className="label">Location context</div><h2>{record.basin_name}</h2><p><strong>Country:</strong> {countryLabel ?? "Loading country..."}</p><p className="muted">{details?.address ?? "Resolving location..."}</p></div>
    <div className="location-map-wrap"><div className="label">Location map</div><div className="location-map-placeholder"><LocationMap record={record} /></div></div>
    <NasaCoverage record={record} />
  </section>;
}
