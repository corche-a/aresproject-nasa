"use client";

import dynamic from "next/dynamic";
import type { BasinRecord } from "../lib/types";

const LocationMapView = dynamic(() => import("./LocationMapView"), { ssr: false });
export default function LocationMap({ record }: { record: BasinRecord }) {
  return <LocationMapView record={record} />;
}
