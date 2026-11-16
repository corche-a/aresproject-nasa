"use client";

import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import type { BasinRecord } from "../lib/types";

export default function LocationMapView({ record }: { record: BasinRecord }) {
  return <MapContainer className="location-map" center={[record.lat, record.lon]} zoom={7} scrollWheelZoom>
    <TileLayer attribution="NASA GIBS" url="https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg" maxZoom={8} />
    <CircleMarker center={[record.lat, record.lon]} radius={10} pathOptions={{ color: "#d71920", fillColor: "#d71920", fillOpacity: 0.9 }}>
      <Popup><strong>{record.basin_name}</strong><br />{record.lat}, {record.lon}</Popup>
    </CircleMarker>
  </MapContainer>;
}
