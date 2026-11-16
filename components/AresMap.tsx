"use client";

import dynamic from "next/dynamic";
import type { ScoredRecord } from "../lib/types";
import type { GibsLayer } from "../lib/gibs";

const LeafletMap = dynamic(() => import("./LeafletMap"), { ssr: false });
export default function AresMap({ records, layer, selectedBasinId, onSelect }: { records: ScoredRecord[]; layer: GibsLayer; selectedBasinId: string | null; onSelect: (id: string) => void }) {
  return <LeafletMap records={records} layer={layer} selectedBasinId={selectedBasinId} onSelect={onSelect} />;
}
