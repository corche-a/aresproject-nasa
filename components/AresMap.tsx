"use client";

import dynamic from "next/dynamic";
import type { ScoredRecord } from "../lib/types";
import type { GibsLayer } from "../lib/gibs";

const LeafletMap = dynamic(() => import("./LeafletMap"), { ssr: false });
export default function AresMap({ records, layer }: { records: ScoredRecord[]; layer: GibsLayer }) {
  return <LeafletMap records={records} layer={layer} />;
}
