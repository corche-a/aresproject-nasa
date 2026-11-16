"use client";

import { useEffect, useState } from "react";
import type { BasinRecord } from "../lib/types";
import LocationMap from "./LocationMap";

interface LocationResponse { country: string; address: string; photos: string[]; }
export default function LocationDetails({ record }: { record: BasinRecord }) {
  const [details, setDetails] = useState<LocationResponse | null>(null);
  useEffect(() => {
    fetch(`/api/location?lat=${record.lat}&lon=${record.lon}&name=${encodeURIComponent(record.basin_name)}`)
      .then((response) => response.ok ? response.json() as Promise<LocationResponse> : Promise.reject(new Error("Location lookup failed")))
      .then(setDetails)
      .catch((error) => { console.error(error); setDetails({ country: "Country unavailable", address: "Address unavailable", photos: [] }); });
  }, [record.basin_name, record.lat, record.lon]);
  return <section className="location-details card">
    <div><div className="label">Location context</div><h2>{record.basin_name}</h2><p><strong>Country:</strong> {details?.country ?? "Loading country..."}</p><p className="muted">{details?.address ?? "Resolving location..."}</p></div>
    <div className="location-map-wrap"><div className="label">Location map</div><div className="location-map-placeholder"><LocationMap record={record} /></div></div>
    <div className="photo-panel"><div className="label">Location photos</div>{details?.photos.length ? <div className="photo-carousel">{details.photos.map((photo) => <img key={photo} src={`/api/location/photo?name=${encodeURIComponent(photo)}`} alt={`${record.basin_name} location`} />)}</div> : <div className="photo-unavailable">{details ? "Photos unavailable for this location." : "Checking photo availability..."}</div>}<small className="muted">Google Places photos are optional and require GOOGLE_MAPS_API_KEY.</small></div>
  </section>;
}
