"use client";

import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import { divIcon } from "leaflet";
import { useEffect } from "react";
import type { ScoredRecord } from "../lib/types";
import { GIBS_LAYERS, type GibsLayer } from "../lib/gibs";

function MapFocus({ record }: { record?: ScoredRecord }) {
  const map = useMap();
  useEffect(() => { if (record) map.flyTo([record.lat, record.lon], Math.max(map.getZoom(), 4), { duration: 0.8 }); }, [map, record]);
  return null;
}

function pinIcon(selected: boolean) {
  return divIcon({
    className: "custom-pin-icon",
    html: `<span class="map-pin${selected ? " map-pin-selected" : ""}"><span class="map-pin-core"></span></span>`,
    iconSize: [30, 40],
    iconAnchor: [15, 40],
    popupAnchor: [0, -36],
  });
}

export default function LeafletMap({ records, layer, selectedBasinId, onSelect }: { records: ScoredRecord[]; layer: GibsLayer; selectedBasinId: string | null; onSelect: (id: string) => void }) {
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
      <MapFocus record={records.find((record) => record.basin_id === selectedBasinId)} />
      {records.map((record) => (
        <Marker
          position={[record.lat, record.lon]}
          key={record.basin_id}
          icon={pinIcon(record.basin_id === selectedBasinId)}
          eventHandlers={{ click: () => onSelect(record.basin_id) }}
        >
          <Popup>
            <strong>{record.basin_name}</strong><br />
            Score: {(record.score * 100).toFixed(1)}%<br />
            {record.lat}, {record.lon}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
