"use client";

import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import type { ScoredRecord } from "../lib/types";
import { GIBS_LAYERS, type GibsLayer } from "../lib/gibs";

export default function LeafletMap({ records, layer }: { records: ScoredRecord[]; layer: GibsLayer }) {
  const selectedLayer = GIBS_LAYERS[layer];
  const tileUrl = selectedLayer.date
    ? `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${selectedLayer.layer}/default/${selectedLayer.date}/${selectedLayer.matrix}/{z}/{y}/{x}.${selectedLayer.extension}`
    : `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${selectedLayer.layer}/default/${selectedLayer.matrix}/{z}/{y}/{x}.${selectedLayer.extension}`;
  return (
    <MapContainer className="ares-map" center={[20, -35]} zoom={2} scrollWheelZoom>
      <TileLayer
        attribution="NASA GIBS"
        url={tileUrl}
        maxZoom={9}
      />
      {records.map((record) => (
        <CircleMarker
          center={[record.lat, record.lon]}
          key={record.basin_id}
          radius={7}
          pathOptions={{ color: "#38bdf8", fillColor: "#38bdf8", fillOpacity: 0.8 }}
        >
          <Popup>
            <strong>{record.basin_name}</strong><br />
            Score: {(record.score * 100).toFixed(1)}%<br />
            {record.lat}, {record.lon}
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
